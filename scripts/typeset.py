"""Set text as outlines from scripts/glyphs.json; standard library only.

Each glyph used is defined once in <defs> and stamped with <use>, so the image
carries its own lettering and looks the same in every browser.
"""
from pathlib import Path
import json

PREFIX = {'display': 'd', 'title': 't', 'text': 'x', 'light': 'l', 'mono': 'm', 'monomed': 'n'}


class Typesetter:
    def __init__(self, path=Path(__file__).with_name('glyphs.json')):
        self.faces = json.loads(Path(path).read_text())
        self.used = {}

    def _advances(self, value, face, track):
        """Pen position of every character, in font units, and the total width."""
        data = self.faces[face]
        glyphs, kern, upm = data['glyphs'], data['kern'], data['upm']
        pen, positions, previous = 0, [], ''
        for char in value:
            if char not in glyphs:
                raise KeyError(f'{char!r} is not baked for {face!r}; add it to CHARS in scripts/bake_glyphs.py')
            pen += kern.get(previous + char, 0)
            positions.append(pen)
            pen += glyphs[char][0] + track * upm
            previous = char
        return positions, pen - (track * upm if value else 0)

    def width(self, value, face, size, track=0.0):
        return self._advances(value, face, track)[1] * size / self.faces[face]['upm']

    def line(self, value, x, y, face, size, fill, track=0.0, anchor='start', attrs=''):
        """One line of text with its baseline at (x, y)."""
        positions, total = self._advances(value, face, track)
        scale = size / self.faces[face]['upm']
        if anchor == 'end':
            x -= total * scale
        elif anchor == 'middle':
            x -= total * scale / 2
        uses = []
        for char, pen in zip(value, positions):
            if char == ' ':
                continue
            ref = f'{PREFIX[face]}{ord(char):x}'
            self.used[ref] = self.faces[face]['glyphs'][char][1]
            uses.append(f'<use href="#{ref}" x="{round(pen)}"/>' if pen else f'<use href="#{ref}"/>')
        return f'<g transform="translate({x:.1f} {y:.1f}) scale({scale:.5f})" fill="{fill}"{attrs}>{"".join(uses)}</g>'

    def wrap(self, value, face, size, width, track=0.0, balance=False):
        """Greedy word wrap to a measure; `balance` evens out the line lengths."""
        def greedy(measure):
            lines, current = [], ''
            for word in value.split():
                candidate = f'{current} {word}'.strip()
                if current and self.width(candidate, face, size, track) > measure:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            return lines + [current] if current else lines

        lines = greedy(width)
        if balance and len(lines) > 1:
            low, high = 0.0, width
            for _ in range(14):  # the narrowest measure that keeps the line count
                mid = (low + high) / 2
                if len(greedy(mid)) <= len(lines):
                    high = mid
                else:
                    low = mid
            lines = greedy(high)
        return lines

    def defs(self):
        return ''.join(f'<path id="{ref}" d="{d}"/>' for ref, d in sorted(self.used.items()))
