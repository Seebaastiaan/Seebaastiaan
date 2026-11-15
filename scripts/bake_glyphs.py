"""Bake the profile's lettering into scripts/glyphs.json.

GitHub shows the profile as an image, and an image cannot load web fonts. So
the two typefaces of the portfolio (Archivo and IBM Plex Mono, both under the
SIL Open Font License) are traced once into outlines here, and the composer
sets every line of text from those outlines with the standard library alone.

Developer tool, not part of the daily workflow. Run it only to add characters
or faces:

    pip install fonttools
    python3 scripts/bake_glyphs.py            # downloads the fonts to a cache
    python3 scripts/bake_glyphs.py path/to/fonts   # or reads them from a folder
"""
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen
import json
import sys
import tempfile

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://raw.githubusercontent.com/google/fonts/main/ofl/'
FILES = {
    'Archivo.ttf': 'archivo/Archivo[wdth,wght].ttf',
    'PlexMono-Regular.ttf': 'ibmplexmono/IBMPlexMono-Regular.ttf',
    'PlexMono-Medium.ttf': 'ibmplexmono/IBMPlexMono-Medium.ttf',
}
# Face name → (file, variable-font instance). They mirror the portfolio's CSS.
FACES = {
    'display': ('Archivo.ttf', {'wdth': 125, 'wght': 300}),  # .name, .wide
    'title': ('Archivo.ttf', {'wdth': 118, 'wght': 400}),    # .title
    'text': ('Archivo.ttf', {'wdth': 100, 'wght': 400}),     # body copy
    'light': ('Archivo.ttf', {'wdth': 100, 'wght': 300}),    # .lead
    'mono': ('PlexMono-Regular.ttf', None),                  # .anno
    'monomed': ('PlexMono-Medium.ttf', None),                # .anno.font-medium
}
CHARS = ''.join(chr(c) for c in range(32, 127)) + 'áéíóúüñÁÉÍÓÚÜÑ¿¡—–·×°№’‘“”…→←↑↓↗↻©±≈'


def kerning(font, names):
    """Pair kerning for the baked characters, read from the GPOS 'kern' feature."""
    if 'GPOS' not in font:
        return {}
    table = font['GPOS'].table
    lookups = set()
    for record in table.FeatureList.FeatureRecord:
        if record.FeatureTag == 'kern':
            lookups.update(record.Feature.LookupListIndex)
    subtables = []
    for index in sorted(lookups):
        group = []
        for sub in table.LookupList.Lookup[index].SubTable:
            sub = getattr(sub, 'ExtSubTable', sub)
            if type(sub).__name__ == 'PairPos':
                group.append(sub)
        subtables.append(group)

    def adjust(left, right):
        total = 0
        for group in subtables:
            for sub in group:
                if left not in sub.Coverage.glyphs:
                    continue
                if sub.Format == 1:
                    pairs = sub.PairSet[sub.Coverage.glyphs.index(left)].PairValueRecord
                    hit = next((p for p in pairs if p.SecondGlyph == right), None)
                    if hit is None:
                        continue
                    value = hit.Value1
                else:
                    first = sub.ClassDef1.classDefs.get(left, 0)
                    second = sub.ClassDef2.classDefs.get(right, 0)
                    value = sub.Class1Record[first].Class2Record[second].Value1
                total += (getattr(value, 'XAdvance', 0) or 0) if value else 0
                break
        return total

    pairs = {}
    for a, left in names.items():
        for b, right in names.items():
            value = round(adjust(left, right))
            if value:
                pairs[a + b] = value
    return pairs


def bake(path, instance):
    font = TTFont(path)
    if instance:
        font = instantiateVariableFont(font, instance)
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    glyphs, names = {}, {}
    for char in CHARS:
        name = cmap.get(ord(char))
        if name is None:
            continue
        pen = SVGPathPen(glyph_set, ntos=lambda value: str(round(value)))
        # Flip to SVG's y-down so a line of text needs no mirrored transform.
        glyph_set[name].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
        glyphs[char] = [round(glyph_set[name].width), pen.getCommands()]
        names[char] = name
    return {'upm': font['head'].unitsPerEm, 'glyphs': glyphs, 'kern': kerning(font, names)}


def main():
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = Path(tempfile.gettempdir()) / 'profile-fonts'
        folder.mkdir(exist_ok=True)
        for name, remote in FILES.items():
            if not (folder / name).exists():
                with urlopen(SOURCE + quote(remote), timeout=60) as response:
                    (folder / name).write_bytes(response.read())
    faces = {}
    for face, (filename, instance) in FACES.items():
        faces[face] = bake(folder / filename, instance)
        print(f'{face}: {len(faces[face]["glyphs"])} glyphs, {len(faces[face]["kern"])} kerning pairs')
    out = ROOT / 'scripts/glyphs.json'
    out.write_text(json.dumps(faces, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f'Wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
