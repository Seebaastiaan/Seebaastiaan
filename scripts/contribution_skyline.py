"""Render a monochrome contribution skyline using GitHub's public calendar.
Python 3.10+, standard library only. No access token required.
"""
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import math
import re
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days, self.tips, self.tip = {}, {}, None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('data-date') and 'data-level' in attrs:
            self.days[attrs['id']] = attrs['data-date']
        if tag == 'tool-tip':
            self.tip = attrs.get('for')

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self.tip = None

    def handle_data(self, data):
        if self.tip:
            self.tips[self.tip] = self.tips.get(self.tip, '') + data


def parse_calendar(html):
    parser = CalendarParser()
    parser.feed(html)
    days = []
    for key, day in parser.days.items():
        tip = parser.tips.get(key, '').strip()
        match = re.match(r'([\d,]+) contributions?\b', tip)
        if match:
            count = int(match.group(1).replace(',', ''))
        elif tip.startswith('No contributions'):
            count = 0
        else:
            raise ValueError(f'Missing or unrecognized contribution count for {day}: {tip!r}')
        days.append({'date': day, 'count': count})
    days.sort(key=lambda day: day['date'])
    if len(days) < 350 or len({d['date'] for d in days}) != len(days):
        raise ValueError('Incomplete or duplicate calendar; existing outputs were not replaced.')
    for first, second in zip(days, days[1:]):
        if date.fromisoformat(second['date']) - date.fromisoformat(first['date']) != timedelta(days=1):
            raise ValueError('Non-contiguous calendar; existing outputs were not replaced.')
    return days


def render(days, username):
    total = sum(day['count'] for day in days)
    peak = max(day['count'] for day in days)
    streak = best = 0
    for day in days:
        streak = streak + 1 if day['count'] else 0
        best = max(best, streak)
    start = date.fromisoformat(days[0]['date'])
    start -= timedelta(days=(start.weekday() + 1) % 7)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="480" viewBox="0 0 1200 480" role="img" aria-labelledby="title desc">',
           f'<title id="title">{escape(username)} — contribution skyline</title>',
           f'<desc id="desc">{total} public-profile contributions from {days[0]["date"]} to {days[-1]["date"]}. Each block is one day. Height indicates contributions; peak {peak} in a day. Longest streak in this window: {best} days.</desc>',
           '<rect x="1" y="1" width="1198" height="478" rx="12" fill="#f2f0e9" stroke="#d8d3c8"/>',
           '<g font-family="Georgia, Times New Roman, serif" fill="#111110">',
           '<text x="42" y="65" font-size="32">Contribution skyline</text></g>',
           '<g font-family="monospace" fill="#827c70" font-size="11" letter-spacing="2">',
           f'<text x="44" y="93">{days[0]["date"]} — {days[-1]["date"]}</text>',
           '<text x="44" y="160">CONTRIBUTIONS PER DAY</text>',
           '<text x="44" y="258">TOTAL</text><text x="151" y="258">PEAK / DAY</text><text x="44" y="352">LONGEST STREAK</text></g>',
           '<path d="M44 119H300 M44 223H300" stroke="#d0cabf"/>',
           '<g font-family="Georgia, Times New Roman, serif" fill="#111110" font-size="36">',
           f'<text x="44" y="301">{total:,}</text><text x="151" y="301">{peak}</text><text x="44" y="393">{best} days</text></g>']
    tones = ['#ded9ce', '#bcb5a7', '#958b7b', '#686052', '#38352e']
    for i, color in enumerate(tones):
        svg.append(f'<rect x="{44 + i*36}" y="175" width="33" height="13" fill="{color}"/>')
    svg.extend(['<g font-family="monospace" fill="#827c70" font-size="11"><text x="44" y="207">0</text>',f'<text x="185" y="207">{peak} max</text></g>'])
    cubes=[]
    for item in days:
        delta=(date.fromisoformat(item['date'])-start).days
        week, weekday=divmod(delta,7)
        x=425 + week*11 + weekday*11
        y=220 + week*3.0 - weekday*7
        count=item['count']
        level=0 if not count else min(4, 1+int(3*math.log1p(count)/math.log1p(max(peak,1))))
        h=3 if not count else 8 + 115 * math.log1p(count)/math.log1p(max(peak,1))
        top=tones[level]
        label=escape(f"{item['date']}: {count} contributions")
        cubes.append((y, f'<g><title>{label}</title><path d="M{x},{y-h}l10,-5 10,5 -10,5Z" fill="{top}"/><path d="M{x},{y-h}l10,5v{h}l-10,-5Z" fill="{top}"/><path d="M{x},{y-h}l10,5v{h}l-10,-5Z" fill="#000" opacity=".14"/><path d="M{x+10},{y-h+5}l10,-5v{h}l-10,5Z" fill="{top}"/><path d="M{x+10},{y-h+5}l10,-5v{h}l-10,5Z" fill="#000" opacity=".28"/></g>'))
    svg.extend(cube for _,cube in sorted(cubes))
    svg.append('<g font-family="monospace" font-size="10" fill="#827c70" letter-spacing="1"><text x="425" y="422">ONE BLOCK = ONE DAY · HEIGHT = CONTRIBUTIONS</text><text x="44" y="454">GITHUB PUBLIC PROFILE · REFRESHED BY GITHUB ACTIONS</text></g></svg>')
    return ''.join(svg)


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else 'Seebaastiaan'
    if not re.fullmatch(r'[A-Za-z0-9-]+', username):
        raise ValueError('Invalid GitHub username')
    if len(sys.argv) > 2:
        html = Path(sys.argv[2]).read_text()
    else:
        request = Request(f'https://github.com/users/{username}/contributions', headers={'User-Agent': 'github-profile-skyline', 'Accept': 'text/html'})
        with urlopen(request, timeout=30) as response:
            html = response.read().decode('utf-8')
    days = parse_calendar(html)
    svg = render(days, username)
    (ROOT/'assets').mkdir(exist_ok=True)
    (ROOT/'assets/contribution-skyline.svg').write_text(svg)
    (ROOT/'assets/contributions.json').write_text(json.dumps({'username':username, 'source':f'https://github.com/users/{username}/contributions', 'days':days}, indent=2)+'\n')
    print(f'{len(days)} verified daily counts; {sum(day["count"] for day in days)} contributions.')

if __name__ == '__main__':
    main()
