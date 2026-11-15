"""Read GitHub's public contribution calendar into assets/contributions.json.

The skyline itself is drawn by compose_readme.py, inside the profile image.
Python 3.10+, standard library only. No access token required.
"""
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
import json
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
    (ROOT/'assets').mkdir(exist_ok=True)
    (ROOT/'assets/contributions.json').write_text(json.dumps({'username':username, 'source':f'https://github.com/users/{username}/contributions', 'days':days}, indent=2)+'\n')
    print(f'{len(days)} verified daily counts; {sum(day["count"] for day in days)} contributions.')

if __name__ == '__main__':
    main()
