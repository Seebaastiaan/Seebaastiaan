"""Compose the profile README image; Python 3.10+, standard library only.

The page keeps the README's own shape (a masthead, then labelled sections
down the page) and borrows the portfolio's visual language: paper, one blue
ink, a red accent, Archivo for reading and IBM Plex Mono for labels.

Edit the content below, then run:

    python3 scripts/compose_readme.py
"""
from datetime import date
from html import escape
from pathlib import Path
import json
import re

from models import ACCENT, INK, MODELS, render, skyline
from typeset import Typesetter

ROOT = Path(__file__).resolve().parents[1]

# ── Content ───────────────────────────────────────────────────────────

NAME = 'Sebastian Jara'
ROLE = 'AI Engineer'
ISSUE = 'Issue №01'
PLACE = 'Mexico City · ESCOM / IPN'
STATUS = 'Open to work & collaborations'
TAGLINE = 'AI Engineer with an eye for interfaces and a curiosity for intelligence.'
STATEMENT = 'I build web experiences and explore how intelligence takes shape.'
MOTTO = 'Thoughtful interfaces. Curious engineering.'
CURRENTLY = [
    'Studying Artificial Intelligence Engineering at ESCOM, Instituto Politécnico Nacional (IPN).',
    'Building a neurodynamic engine to explore neural activity and stimulus propagation through '
    'simulated networks, while learning how to build AI from the ground up.',
]
# Each row is cut out as its own image so the README can wrap it in a link.
# (file slug, label, address as shown)
ELSEWHERE = [
    ('portfolio', 'Portfolio', 'portfolio-sebas-jara24.vercel.app'),
    ('linkedin', 'LinkedIn', 'linkedin.com/in/sebastianjara24'),
    ('email', 'Email', 'sebasjara1503@gmail.com'),
    ('x', 'X / Twitter', 'x.com/SeebastianJara'),
]
# (title, description, stack, drawing from models.MODELS)
PROJECTS = [
    ('LearnQuest', 'Gamified entrance exam preparation, with subject-based practice, XP, and progress tracking.',
     'Next.js · TypeScript · Supabase', 'steps'),
    ('MindfulSpace', 'A digital journal with an AI companion and mood tracking for personal reflection.',
     'Next.js · TypeScript · Firebase · Gemini API', 'journal'),
    ('Algoritmo Lanczos', 'Eigenvalue and eigenvector approximation for symmetric matrices, implemented in C.',
     'C · Linear algebra · Numerical methods', 'matrix'),
    ('RailSense', 'Interactive railway analytics powered by AI. I developed the entire user interface.',
     'Next.js · TypeScript · Tailwind CSS · Recharts', 'rail'),
]
CODE = [
    'profile = {',
    '    "role": "AI Engineer",',
    '    "education": "AI Engineering · ESCOM / IPN",',
    '    "interests": ["Interface design", "Web applications", "AI"],',
    '    "building": "A neurodynamic engine",',
    '    "learning": "How to build AI from the ground up",',
    '    "open_to": ["Job opportunities", "Project collaborations"],',
    '}',
]
TOOLKIT = [
    ('Languages', 'TypeScript · JavaScript · Python · C · SQL'),
    ('Web & platforms', 'React · Next.js · Tailwind CSS · Supabase · Firebase · Git'),
]
RECOGNITION = [
    ('Open Source Winner', ['Hackathon Mobility & AI · November 2025',
                            'RailSense — Developed the entire user interface.']),
    ('3rd Place · Software Development', ['Premio a los mejores Prototipos de Nivel Medio Superior, IPN',
                                          'June 2024 · Uxersii · Full stack developer']),
]
SKYLINE_NOTE = ('One block is one day. Height represents contributions from my public GitHub calendar, '
                'including activity beyond commits.')
LETS_BUILD = ("I'm looking for job opportunities and people to build projects with, especially around "
              'interfaces, web applications, and AI.')
FOOTER = 'written in this README'

# ── Page ──────────────────────────────────────────────────────────────

W = 1200
M = 64                    # outer margin
CX = 300                  # content column; section labels sit in the margin left of it
R = W - M
PAPER = '#f3f3ee'
SOFT = '#55629f'
ANNO, TRACK = 15, 0.08

T = Typesetter()
out = []          # lettering and drawings, in paint order
hair = []         # hairlines, as path fragments
styles = []       # CSS for the drawings' moving parts
defs = []         # clip paths
y = 0

# GitHub cannot put a link inside an image, so the page is cut into strips
# that the README stacks flush: plain strips, and one strip per link.
strips = []       # finished strips, top to bottom
strip = {'name': 'profile-top', 'top': 0, 'label': ''}


def cut(at, name, label=''):
    """End the current strip at `at` and start the next one there."""
    global out, hair, styles, defs, strip
    strips.append({**strip, 'bottom': at, 'out': out, 'hair': hair, 'styles': styles, 'defs': defs,
                   'glyphs': T.defs()})
    out, hair, styles, defs = [], [], [], []
    T.used = {}
    strip = {'name': name, 'top': at, 'label': label}


def anno(value, x, y, fill=INK, medium=False, anchor='start', size=ANNO):
    """Label lettering: mono, uppercase, tracked."""
    return T.line(value.upper(), x, y, 'monomed' if medium else 'mono', size, fill, TRACK, anchor)


def anno_width(value, size=ANNO):
    return T.width(value.upper(), 'mono', size, TRACK)


def copy(value, x, y, width, face='text', size=24, leading=36, fill=INK, track=0.0, balance=False):
    """A wrapped paragraph; returns the baseline of its last line."""
    for index, line in enumerate(T.wrap(value, face, size, width, track, balance)):
        if index:
            y += leading
        out.append(T.line(line, x, y, face, size, fill, track))
    return y


def rule(x0, x1, y):
    hair.append(f'M{x0} {y}H{x1}')


def section(label, ruled=True):
    """A hairline across the page and the section's label in the margin.

    Returns the baseline shared by the label and the section's first line.
    """
    if ruled:
        rule(M, R, y)
    line, lines = '', []
    for word in label.split():  # labels wrap inside the margin column
        if line and anno_width(f'{line} {word}') > CX - M - 24:
            lines.append(line)
            line = word
        else:
            line = f'{line} {word}'.strip()
    for index, text in enumerate(lines + [line]):
        out.append(anno(text, M, y + 50 + index * 22, medium=True))
    return y + 50


# ── Data ──────────────────────────────────────────────────────────────

days = json.loads((ROOT / 'assets/contributions.json').read_text())['days']
total = sum(day['count'] for day in days)
peak = max(day['count'] for day in days)
streak = best = 0
for day in days:
    streak = streak + 1 if day['count'] else 0
    best = max(best, streak)
updated = days[-1]['date']
year = updated[:4]
first_weekday = (date.fromisoformat(days[0]['date']).weekday() + 1) % 7  # Sunday = 0

# ── Masthead ──────────────────────────────────────────────────────────

out.append(anno(f'{ISSUE} · {year}', M, 68, SOFT))
status_x = R - anno_width(STATUS)
out.append(f'<rect x="{status_x - 19:.1f}" y="57.5" width="8" height="8" fill="{ACCENT}"/>' + anno(STATUS, status_x, 68))

name_size, name_track = 140, -0.035
while T.width(NAME, 'display', name_size, name_track) > R - M:
    name_size -= 1
out.append(T.line(NAME, M - name_size * 0.045, 68 + 44 + name_size * 0.78, 'display', name_size, INK, name_track))
y = 68 + 44 + name_size * 0.78 + 62
y = copy(TAGLINE, M, y, R - M, 'light', 32, 42, INK, -0.012, balance=True)
out.append(anno(PLACE, M, y + 46, SOFT))
y = round(y + 46 + 44)

# ── About ─────────────────────────────────────────────────────────────

base = section('About')
base = copy(STATEMENT, CX, base, R - CX, size=27, leading=38)
out.append(anno(MOTTO, CX, base + 38, SOFT))
y = base + 38 + 46

# ── Currently ─────────────────────────────────────────────────────────

base = section('Currently')
for index, paragraph in enumerate(CURRENTLY):
    base = copy(paragraph, CX, base + (52 if index else 0), R - CX)
y = base + 50

# ── Elsewhere ─────────────────────────────────────────────────────────
# Rows are tall on purpose: a strip shorter than a line of text would leave
# a gap under it on narrow screens.

ROW = 88
rule(M, R, y)
for index, (slug, label, address) in enumerate(ELSEWHERE):
    row_top = y + 1 + index * ROW
    cut(row_top, f'row-{slug}', f'{label}: {address}')
    if not index:
        section('Elsewhere', ruled=False)
    out.append(anno(label, CX, row_top + 49, SOFT))
    out.append(T.line(address, CX + 170, row_top + 53, 'text', 27, INK))
    out.append(T.line('↗', R, row_top + 52, 'mono', 20, INK, anchor='end'))
    rule(M if index == len(ELSEWHERE) - 1 else CX, R, row_top + ROW - 1)
y = y + len(ELSEWHERE) * ROW
cut(y + 1, 'profile-rest', 'Work, toolkit, recognition and contribution skyline')

# ── Work ──────────────────────────────────────────────────────────────

base = section('Work', ruled=False)
ART_W, ART_H = 250, 172
for number, (title, description, stack, model) in enumerate(PROJECTS, 1):
    top = base - 50
    out.append(anno(f'{number:02d}', CX, base, SOFT))
    out.append(T.line(title, CX + 52, base + 2, 'title', 33, INK, -0.02))
    line = copy(description, CX + 52, base + 46, R - CX - 52 - ART_W - 40, size=22.5, leading=33)
    out.append(anno(stack, CX + 52, line + 38, SOFT, size=14))
    bottom = max(line + 38, top + 28 + ART_H) + 40
    drawing = render(MODELS[model](), ART_W, ART_H, R - ART_W / 2, (top + bottom) / 2, f'c{number}_', stroke=1.15)
    out.append(drawing['svg'])
    defs.append(drawing['defs'])
    styles.append(drawing['css'])
    if number < len(PROJECTS):
        rule(CX, R, bottom)
    base = bottom + 50
y = bottom + 6

# ── About, in code ────────────────────────────────────────────────────

base = section('About, in code')
code_size = 18
advance = code_size * 0.6
box_top = base - 30
for index, source in enumerate(CODE):
    line = base + 8 + index * 31
    out.append(T.line(f'{index + 1}', CX + 40, line, 'mono', 13, SOFT, anchor='end'))
    x = CX + 64
    # Values in ink; keys, brackets and punctuation in the softer ink.
    for part in re.split(r'("[^"]*"(?!:))', source):
        if part.strip():
            lead = len(part) - len(part.lstrip())
            fill = INK if part.startswith('"') or '=' in part else SOFT
            out.append(T.line(part.strip(), x + lead * advance, line, 'mono', code_size, fill))
        x += len(part) * advance
box_bottom = base + 8 + (len(CODE) - 1) * 31 + 26
hair.append(f'M{CX} {box_top}H{R}V{box_bottom}H{CX}ZM{CX + 52} {box_top}V{box_bottom}')
y = box_bottom + 50

# ── Toolkit ───────────────────────────────────────────────────────────

base = section('Toolkit')
for index, (group, items) in enumerate(TOOLKIT):
    out.append(anno(group, CX, base, SOFT))
    base = copy(items, CX, base + 40, R - CX, size=25, leading=36)
    if index < len(TOOLKIT) - 1:
        base += 54
y = base + 50

# ── Recognition ───────────────────────────────────────────────────────

base = section('Recognition')
for index, (award, details) in enumerate(RECOGNITION):
    out.append(f'<rect x="{CX}" y="{base - 16}" width="9" height="9" fill="{ACCENT}"/>')
    out.append(T.line(award, CX + 26, base + 2, 'title', 30, INK, -0.02))
    line = base + 2
    for detail_index, detail in enumerate(details):
        line = copy(detail, CX + 26, line + (42 if not detail_index else 34), R - CX - 26, size=22.5, leading=33,
                    fill=SOFT if not detail_index else INK)
    base = line + 62
y = base - 62 + 50

# ── Contribution skyline ──────────────────────────────────────────────

base = section('Contribution skyline')
stat_y = base + 22 + 60
for label, value in (('Total', f'{total:,}'), ('Peak / day', str(peak)), ('Longest streak', f'{best} days')):
    out.append(anno(label, M, stat_y, SOFT, size=13))
    out.append(T.line(value, M, stat_y + 42, 'title', 34, INK, -0.02))
    stat_y += 96
SKY_H = 330
sky_top = base - 34
city = skyline(days, first_weekday, R - CX, SKY_H, (CX + R) / 2, sky_top + SKY_H / 2)
months = 'JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()
ticks = ''
for when, (mx, my) in city['months'][1:]:
    ticks += f'M{mx:.1f} {my + 5:.1f}v8'
    out.append(anno(months[int(when[5:7]) - 1], mx, my + 31, SOFT, anchor='middle', size=11.5))
out.append(f'<path d="{ticks}" stroke="{SOFT}"/>')
out.append(city['svg'])
(px, py), peak_day = city['peak']
label = f'Peak · {peak_day["count"]} · {peak_day["date"]}'
side = -1 if px + 36 + anno_width(label, 13.5) > R else 1  # letter towards the open side
out.append(f'<path d="M{px:.1f} {py - 6:.1f}V{sky_top + 14}h{14 * side}" fill="none" stroke="{ACCENT}" stroke-width="1.3"/>'
           f'<rect x="{px - 2.5:.1f}" y="{py - 8.5:.1f}" width="5" height="5" fill="{ACCENT}"/>')
out.append(anno(label, px + 22 * side, sky_top + 19, ACCENT, medium=True, size=13.5,
                anchor='end' if side < 0 else 'start'))
line = copy(SKYLINE_NOTE, CX, sky_top + SKY_H + 34, R - CX, size=21, leading=31, fill=SOFT)
out.append(anno(f'{days[0]["date"]} — {days[-1]["date"]} · refreshed daily by GitHub Actions', CX, line + 38,
                SOFT, size=13))
y = max(line + 38, stat_y - 54) + 50

# ── Let's build ───────────────────────────────────────────────────────

base = section("Let's build")
y = copy(LETS_BUILD, CX, base + 6, R - CX, 'light', 34, 46, INK, -0.012, balance=True) + 56

rule(M, R, y)
out.append(anno(f'{ISSUE} · {year} · {FOOTER}', M, y + 42, SOFT, size=13.5))
out.append(anno(f'Updated {updated}', R, y + 42, SOFT, anchor='end', size=13.5))
H = round(y + 78)

# ── Assembly ──────────────────────────────────────────────────────────

description = (
    f'{NAME} — {ROLE}. {TAGLINE} {STATEMENT} {MOTTO} Currently: {" ".join(CURRENTLY)} Work: '
    + ' '.join(f'{i}. {title} — {text} ({stack}).' for i, (title, text, stack, _) in enumerate(PROJECTS, 1))
    + ' Toolkit: ' + '; '.join(f'{group}: {items}' for group, items in TOOLKIT) + '. Recognition: '
    + ' '.join(f'{award} — {"; ".join(details)}' for award, details in RECOGNITION)
    + f' Contribution skyline: {total} contributions from {days[0]["date"]} to {days[-1]["date"]}, '
    f'peak {peak} in a day, longest streak {best} days. {LETS_BUILD}')

cut(H, '')
for index, part in enumerate(strips):
    top, height = part['top'], part['bottom'] - part['top']
    title = f'{NAME} — {ROLE}' if not index else part['label']
    desc = f'<desc>{escape(description)}</desc>' if not index else ''
    motion = ''.join(part['styles'])
    style = f'<style>@media (prefers-reduced-motion:no-preference){{{motion}}}</style>' if motion else ''
    (ROOT / f'assets/{part["name"]}.svg').write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 {top} {W} {height}" '
        f'role="img"><title>{escape(title)}</title>{desc}{style}'
        f'<defs>{"".join(part["defs"])}{part["glyphs"]}</defs>'
        # The page's paper and border, drawn whole and cropped by each strip.
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="{PAPER}" stroke="{INK}" stroke-opacity=".26"/>'
        f'<path d="M0 5H{W}" stroke="{INK}" stroke-width="10"/>'
        f'<path d="{"".join(part["hair"])}" fill="none" stroke="{INK}" stroke-opacity=".26"/>'
        + ''.join(part['out']) + '</svg>')

print(f'Composed profile: {W} × {H} in {len(strips)} strips, updated {updated}')
