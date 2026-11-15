"""Small line drawings for the profile, one per project, plus the skyline.

The portfolio draws each project as a little three.js model: paper-coloured
solids with ink edges, hidden lines removed, in an orthographic view. A README
cannot run WebGL, so this module builds the same kind of model from boxes and
cylinders and projects it to SVG. Standard library only.

Motion that survives the projection exactly is kept as CSS animation: bars
sink into the plate they stand on (a clipped vertical slide), the railcar
slides along its track, the speech bubble bobs.
"""
import math

INK = '#1b2b9b'
ACCENT = '#e2412b'
PAPER_RGB = (0xF3, 0xF3, 0xEE)
INK_RGB = (0x1B, 0x2B, 0x9B)
ELEVATION = 0.5
LIGHT = (-0.4, 0.8, 0.45)

STYLES = {
    'line': '',
    'thin': ' stroke-width=".8" stroke-opacity=".55"',
    'dash': ' stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-linecap="butt"',
    'accent': f' stroke="{ACCENT}" stroke-width="1.6"',
}


# ── Transforms (three.js conventions) ─────────────────────────────────

def move(x, y, z):
    return lambda p: (p[0] + x, p[1] + y, p[2] + z)


def turn_x(angle):
    c, s = math.cos(angle), math.sin(angle)
    return lambda p: (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def turn_y(angle):
    c, s = math.cos(angle), math.sin(angle)
    return lambda p: (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def turn_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return lambda p: (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def chain(*steps):
    def apply(p):
        for step in steps:
            p = step(p)
        return p
    return apply


def _normal(points):
    """Newell's method: robust for any planar polygon."""
    nx = ny = nz = 0.0
    for (x1, y1, z1), (x2, y2, z2) in zip(points, points[1:] + points[:1]):
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)


def _key(a, b):
    a = tuple(round(v, 4) for v in a)
    b = tuple(round(v, 4) for v in b)
    return (a, b) if a <= b else (b, a)


# ── Scene items ───────────────────────────────────────────────────────

class Solid:
    """A convex solid: faces wound counter-clockwise seen from outside."""

    def __init__(self, faces, crease=25, open_sharp=True, soft=()):
        self.faces = faces
        self.crease = crease
        self.open_sharp = open_sharp
        self.soft = set(soft)
        self.decals = []

    def decal(self, points, style='thin', closed=False, normal=None):
        """A line drawn on the solid; with a normal, only when that side faces us."""
        self.decals.append((points + points[:1] if closed else points, style, normal))
        return self

    def points(self):
        return [p for face in self.faces for p in face]


class Lines:
    """Free-standing polylines."""

    def __init__(self, paths, style='line'):
        self.paths = paths
        self.style = style

    def points(self):
        return [p for path in self.paths for p in path]


class Group:
    """Items drawn in the order given, inside one <g> (optionally animated)."""

    def __init__(self, items, cls='', style=''):
        self.items = items
        self.cls = cls
        self.style = style

    def points(self):
        return [p for item in self.items for p in item.points()]


class Sorted(Group):
    """Items whose drawing order is worked out from the view."""


class Bar(Solid):
    """A box that can sink into the surface it stands on.

    The box is clipped to its own full-height silhouette and slid straight
    down: in an orthographic view that is exactly a bar getting shorter.
    `sink` is the still pose (0 = full height, 1 = gone).
    """

    def __init__(self, faces, sink=0.0, cls='', style=''):
        super().__init__(faces)
        self.sink = sink
        self.cls = cls
        self.style = style


def box(w, h, d, xf=lambda p: p, kind=Solid, **options):
    x, y, z = w / 2, h / 2, d / 2
    faces = [
        [(-x, y, z), (x, y, z), (x, y, -z), (-x, y, -z)],      # top
        [(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z)],  # bottom
        [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)],      # front (+z)
        [(x, -y, -z), (-x, -y, -z), (-x, y, -z), (x, y, -z)],  # back
        [(x, -y, z), (x, -y, -z), (x, y, -z), (x, y, z)],      # right (+x)
        [(-x, -y, -z), (-x, -y, z), (-x, y, z), (-x, y, -z)],  # left
    ]
    return kind([[xf(p) for p in face] for face in faces], **options)


def cylinder(r_top, r_bottom, h, segments, xf=lambda p: p, crease=40,
             caps=(True, True), rims=(True, True)):
    """Axis along y. `caps` and `rims` are (bottom, top)."""
    ring = [(math.cos(2 * math.pi * i / segments), math.sin(2 * math.pi * i / segments))
            for i in range(segments)]
    top = [xf((c * r_top, h / 2, -s * r_top)) for c, s in ring]
    bottom = [xf((c * r_bottom, -h / 2, -s * r_bottom)) for c, s in ring]
    faces, soft = [], []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append([bottom[i], bottom[j], top[j], top[i]])
        if not rims[0]:
            soft.append(_key(bottom[i], bottom[j]))
        if not rims[1]:
            soft.append(_key(top[i], top[j]))
    if caps[1]:
        faces.append(top)
    if caps[0]:
        faces.append(bottom[::-1])
    return Solid(faces, crease=crease, soft=soft)


def octahedron(radius, xf=lambda p: p):
    r = radius
    px, nx, py, ny, pz, nz = (r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, r), (0, 0, -r)
    faces = [[py, pz, px], [py, px, nz], [py, nz, nx], [py, nx, pz],
             [ny, px, pz], [ny, nz, px], [ny, nx, nz], [ny, pz, nx]]
    return Solid([[xf(p) for p in face] for face in faces], crease=1)


# ── Camera and renderer ───────────────────────────────────────────────

class Camera:
    def __init__(self, center, view, yaw, width, height, cx, cy, elevation=ELEVATION):
        aspect = width / height
        self.scale = height / 2 / max(view, view * 1.6 / aspect)
        self.yaw, self.elevation = yaw, elevation
        self.cx, self.cy = cx, cy
        self._spin = chain(move(-center[0], -center[1], -center[2]), turn_y(yaw))
        self._tilt = turn_x(elevation)
        self._turn = chain(turn_y(yaw), turn_x(elevation))

    def screen(self, p):
        x, y, _ = self._tilt(self._spin(p))
        return (self.cx + x * self.scale, self.cy - y * self.scale)

    def depth(self, p):
        """Distance towards the viewer along the ground."""
        return self._spin(p)[2]

    def facing(self, normal):
        return self._turn(normal)

    def shade(self, normal):
        """The portfolio's shader: paper, tinted with ink as a face turns from the light."""
        length = math.sqrt(sum(v * v for v in LIGHT))
        lit = min(max(sum(n * l for n, l in zip(self.facing(normal), LIGHT)) / length, 0.0), 1.0)
        k = (1.0 - lit) * 0.2

        def linear(c):
            c /= 255
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        def srgb(c):
            c = c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
            return round(min(max(c, 0), 1) * 255)

        mixed = [srgb(linear(p) * (1 - k) + linear(i) * k) for p, i in zip(PAPER_RGB, INK_RGB)]
        return '#%02x%02x%02x' % tuple(mixed)


def _d(points, closed=False):
    out = 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in points)
    return out + 'Z' if closed else out


def _hull(points):
    points = sorted(set(points))

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]

    return half(points) + half(points[::-1])


class Renderer:
    def __init__(self, camera, prefix):
        self.camera = camera
        self.prefix = prefix
        self.clips = []

    def lines(self, paths, style):
        cam = self.camera
        d = ''.join(_d([cam.screen(p) for p in path]) for path in paths)
        attrs = STYLES[style].format(dash=0.11 * cam.scale, gap=0.08 * cam.scale)
        return f'<path d="{d}"{attrs}/>'

    def solid(self, solid):
        cam = self.camera
        normals = [_normal(face) for face in solid.faces]
        visible = [cam.facing(n)[2] > 1e-6 for n in normals]
        edges = {}
        for index, face in enumerate(solid.faces):
            for a, b in zip(face, face[1:] + face[:1]):
                edges.setdefault(_key(a, b), []).append(index)
        fills = {}
        for index, face in enumerate(solid.faces):
            if visible[index]:
                colour = cam.shade(normals[index])
                fills[colour] = fills.get(colour, '') + _d([cam.screen(p) for p in face], True)
        out = [f'<path d="{d}" fill="{c}" stroke="{c}" stroke-width=".6"/>' for c, d in fills.items()]
        limit = math.cos(math.radians(solid.crease))
        strokes = ''
        for key, owners in edges.items():
            if key in solid.soft or not any(visible[i] for i in owners):
                continue
            if len(owners) == 1:
                sharp = solid.open_sharp
            else:
                a, b = normals[owners[0]], normals[owners[1]]
                sharp = sum(x * y for x, y in zip(a, b)) < limit
                # A smooth surface still shows its outline where it turns away.
                sharp = sharp or visible[owners[0]] != visible[owners[1]]
            if sharp:
                strokes += _d([cam.screen(key[0]), cam.screen(key[1])])
        if strokes:
            out.append(f'<path d="{strokes}"/>')
        for points, style, normal in solid.decals:
            if normal is None or cam.facing(normal)[2] > 1e-6:
                out.append(self.lines([points], style))
        return ''.join(out)

    def bar(self, bar):
        cam = self.camera
        outline = _hull([cam.screen(p) for p in bar.points()])
        ys = [y for _, y in outline]
        travel = max(ys) - min(ys)  # body height plus the top face: fully under
        clip = f'{self.prefix}{len(self.clips)}'
        self.clips.append(f'<clipPath id="{clip}"><path d="{_d(outline, True)}"/></clipPath>')
        cls = f' class="{bar.cls}"' if bar.cls else ''
        still = f' transform="translate(0 {bar.sink * travel:.1f})"' if bar.sink else ''
        style = f' style="--h:{travel:.1f}px{";" + bar.style if bar.style else ""}"'
        return f'<g clip-path="url(#{clip})"><g{cls}{style}{still}>{self.solid(bar)}</g></g>'

    def order(self, items):
        """Back-to-front order for a set of compact items.

        Seen from above, something entirely below another thing can never
        hide it; otherwise whichever is nearer along the ground goes on top.
        """
        cam = self.camera
        info = []
        for item in items:
            points = item.points()
            screen = [cam.screen(p) for p in points]
            info.append({
                'low': min(p[1] for p in points), 'high': max(p[1] for p in points),
                'x0': min(x for x, _ in screen), 'x1': max(x for x, _ in screen),
                'y0': min(y for _, y in screen), 'y1': max(y for _, y in screen),
                'depth': sum(cam.depth(p) for p in points) / len(points),
            })
        count = len(items)
        after = [set() for _ in range(count)]  # after[i]: items that must come before i
        for i in range(count):
            for j in range(i + 1, count):
                a, b = info[i], info[j]
                if a['x1'] < b['x0'] or b['x1'] < a['x0'] or a['y1'] < b['y0'] or b['y1'] < a['y0']:
                    continue
                if a['high'] <= b['low'] + 1e-3:
                    after[j].add(i)
                elif b['high'] <= a['low'] + 1e-3:
                    after[i].add(j)
                elif a['depth'] <= b['depth']:
                    after[j].add(i)
                else:
                    after[i].add(j)
        done, result = set(), []
        while len(result) < count:
            ready = [i for i in range(count) if i not in done and after[i] <= done]
            if not ready:  # a cycle: fall back to plain depth
                ready = [i for i in range(count) if i not in done]
            pick = min(ready, key=lambda i: (info[i]['depth'], info[i]['low']))
            done.add(pick)
            result.append(items[pick])
        return result

    def draw(self, item):
        if isinstance(item, Bar):
            return self.bar(item)
        if isinstance(item, Solid):
            return self.solid(item)
        if isinstance(item, Lines):
            return self.lines(item.paths, item.style)
        items = self.order(item.items) if isinstance(item, Sorted) else item.items
        body = ''.join(self.draw(child) for child in items)
        if not (item.cls or item.style):
            return body
        cls = f' class="{item.cls}"' if item.cls else ''
        style = f' style="{item.style}"' if item.style else ''
        return f'<g{cls}{style}>{body}</g>'


def fit(camera, points, x0, y0, x1, y1):
    """Scale and shift the view so the projected points fill a box."""
    def bounds():
        screen = [camera.screen(p) for p in points]
        xs, ys = [x for x, _ in screen], [y for _, y in screen]
        return min(xs), min(ys), max(xs), max(ys)

    left, top, right, bottom = bounds()
    camera.scale *= min((x1 - x0) / (right - left), (y1 - y0) / (bottom - top))
    left, top, right, bottom = bounds()
    camera.cx += (x0 + x1) / 2 - (left + right) / 2
    camera.cy += (y0 + y1) / 2 - (top + bottom) / 2


def render(model, width, height, cx, cy, prefix, pad=8, stroke=1.3):
    """Project a model into a width × height box centred on (cx, cy).

    Returns the drawing, its clip paths and the CSS for its moving parts.
    """
    camera = Camera(model['center'], model['view'], model['yaw'], width, height, cx, cy)
    points = [p for item in model['items'] for p in item.points()] + model.get('reach', [])
    fit(camera, points, cx - width / 2 + pad, cy - height / 2 + pad, cx + width / 2 - pad, cy + height / 2 - pad)
    renderer = Renderer(camera, prefix)
    body = ''.join(renderer.draw(item) for item in model['items'])
    svg = (f'<g fill="none" stroke="{INK}" stroke-width="{stroke}" stroke-linecap="round" '
           f'stroke-linejoin="round">{body}</g>')
    return {'svg': svg, 'defs': ''.join(renderer.clips), 'camera': camera,
            'css': model.get('css', lambda cam: '')(camera)}


# ── Fig. — levels to climb, one hop at a time (LearnQuest) ────────────

def steps():
    count, rise, first = 11, 0.19, 0.28
    yaw = 0.5
    base = cylinder(1.5, 1.5, 0.06, 40, move(0, 0.03, 0))

    column_height = first + count * rise + 0.25
    column_top = 0.06 + column_height
    parts, tops = [], []
    # The column is cut at every tread so each piece can be ordered against it.
    floor = 0.06
    for i in range(count):
        angle = i / 8 * 2 * math.pi
        y = first + i * rise
        parts.append(box(1.0, 0.08, 0.5, chain(turn_y(-angle), move(math.cos(angle) * 0.6, y, math.sin(angle) * 0.6))))
        ceiling = y + 0.04
        parts.append(cylinder(0.13, 0.13, ceiling - floor, 12, move(0, (floor + ceiling) / 2, 0),
                              caps=(False, False), rims=(i == 0, False)))
        floor = ceiling
        tops.append((math.cos(angle) * 0.78, y + 0.04, math.sin(angle) * 0.78))
    parts.append(cylinder(0.13, 0.13, column_top - floor, 12, move(0, (floor + column_top) / 2, 0),
                          caps=(False, True), rims=(False, True)))

    # The learner: a token mid-hop between two levels.
    u = 4.45
    i, f = int(u), u - int(u)
    at = [a + (b - a) * f for a, b in zip(tops[i], tops[i + 1])]
    at[1] += 0.2 + math.sin(f * math.pi) * 0.32
    parts.append(octahedron(0.14, chain(turn_y(0.5 * u * 2.4), move(*at))))

    flag = [
        Lines([[(0, column_top, 0), (0, column_top + 0.6, 0)]]),
        Lines([[(0, column_top + 0.6, 0), (0, column_top + 0.32, 0), (0.4, column_top + 0.46, 0),
                (0, column_top + 0.6, 0)]], 'accent'),
    ]
    return {'items': [base, Sorted(parts), *flag], 'center': (0, 1.3, 0), 'view': 1.75, 'yaw': yaw}


# ── Fig. — a journal, with the week's mood rising off the page ────────

def journal():
    yaw = -0.5
    base = box(2.95, 0.05, 2.02, move(0, 0.025, 0))
    on_left = chain(turn_z(0.05), move(-0.71, 0.135, 0))
    on_right = chain(turn_z(-0.05), move(0.71, 0.135, 0))
    left = box(1.4, 0.1, 1.9, on_left)
    right = box(1.4, 0.1, 1.9, on_right)

    for i in range(8):  # handwriting
        z = -0.72 + i * 0.17
        left.decal([on_left((-0.52, 0.052, z)), on_left((0.05 if i == 7 else 0.52, 0.052, z))])
    for i in range(3):
        z = -0.72 + i * 0.17
        right.decal([on_right((-0.52, 0.052, z)), on_right((0.52, 0.052, z))])
    right.decal([on_right((-0.62, 0.052, 0.42)), on_right((0.62, 0.052, 0.42))])

    on_pencil = chain(turn_y(0.5), move(0.05, 0.088, 0.62), on_left)
    barrel = cylinder(0.035, 0.035, 0.9, 6, chain(turn_z(math.pi / 2), on_pencil), crease=20)
    tip = cylinder(0.0005, 0.035, 0.13, 6, chain(turn_z(-math.pi / 2), move(0.515, 0, 0), on_pencil), crease=20)

    # Seven days of mood. Each bar is built at full height and sunk to its reading.
    full = 0.8
    bars = []
    for i in range(7):
        low, high = 0.42 - 0.3, 0.42 + 0.3
        still = 0.42 + 0.24 * math.sin(0.54 + i * 0.95) + 0.1 * math.sin(0.3 + i * 2.1)
        style = f'--a:{1 - low / full:.3f};--b:{1 - high / full:.3f};animation-delay:{-i * 1.06:.2f}s'
        bars.append(box(0.12, full, 0.12, chain(move(-0.51 + i * 0.17, 0.05 + full / 2, 0.3), on_right),
                        kind=Bar, sink=1 - still / full, cls='mood', style=style))

    # The companion's reply: a speech bubble over the entry.
    w, h, r = 0.5, 0.27, 0.12
    on_bubble = chain(turn_y(0.5), move(-0.72, 1.12 + math.sin(0.78) * 0.04, -0.2))
    outline = []

    def corner(cx, cy, start):
        for k in range(7):
            a = start + k / 6 * (math.pi / 2)
            outline.append((cx + math.cos(a) * r, cy + math.sin(a) * r, 0))

    corner(w - r, h - r, 0)
    corner(-w + r, h - r, math.pi / 2)
    corner(-w + r, -h + r, math.pi)
    outline.extend([(-0.2, -h, 0), (-0.32, -h - 0.2, 0), (-0.02, -h, 0)])
    corner(w - r, -h + r, -math.pi / 2)
    shapes = [outline + outline[:1]]
    for x in (-0.2, 0, 0.2):
        shapes.append([(x + math.cos(k / 12 * 2 * math.pi) * 0.04, math.sin(k / 12 * 2 * math.pi) * 0.04, 0)
                       for k in range(13)])
    bubble = Group([Lines([[on_bubble(p) for p in shape] for shape in shapes], 'accent')], cls='bob')

    def css(cam):
        lift = 0.04 * math.cos(cam.elevation) * cam.scale
        return (f'.bob{{animation:bob 2.4s ease-in-out infinite alternate}}'
                f'@keyframes bob{{from{{transform:translateY({lift:.1f}px)}}to{{transform:translateY({-lift:.1f}px)}}}}'
                '.mood{animation:mood 3.5s ease-in-out infinite alternate}'
                '@keyframes mood{from{transform:translateY(calc(var(--h)*var(--a)))}'
                'to{transform:translateY(calc(var(--h)*var(--b)))}}')

    return {'items': [base, left, Sorted([barrel, tip]), right, Sorted(bars), bubble],
            'center': (0, 0.6, 0), 'view': 1.55, 'yaw': yaw, 'css': css}


# ── Fig. — a dense symmetric matrix collapsing to tridiagonal form ────

MATRIX_N = 9
MATRIX_PERIOD = 9.5


def matrix_start(distance):
    """Seconds into the loop at which entries this far from the diagonal vanish."""
    return 1.4 + (MATRIX_N - 1 - distance) / (MATRIX_N - 3) * 2.2


def matrix_keyframes(name, distance, hidden, shown):
    """One loop: dense, entries vanish from the corners inwards, hold T, restore A."""
    start = matrix_start(distance) / MATRIX_PERIOD * 100
    gone = (matrix_start(distance) + 0.8) / MATRIX_PERIOD * 100
    back = 7.8 / MATRIX_PERIOD * 100
    full = 9.0 / MATRIX_PERIOD * 100
    return (f'@keyframes {name}{distance}{{0%,{start:.1f}%{{{shown}}}{gone:.1f}%,{back:.1f}%{{{hidden}}}'
            f'{full:.1f}%,100%{{{shown}}}}}')


def matrix():
    n, cell = MATRIX_N, 0.32
    span = n * cell
    plate = box(span + 0.3, 0.06, span + 0.3, move(0, 0.03, 0))
    for k in range(n + 1):
        p = -span / 2 + k * cell
        plate.decal([(p, 0.062, -span / 2), (p, 0.062, span / 2)])
        plate.decal([(-span / 2, 0.062, p), (span / 2, 0.062, p)])

    def entry(i, j):
        a, b = min(i, j), max(i, j)
        x = math.sin(a * 127.1 + b * 311.7) * 43758.5453
        return x - math.floor(x)

    def smooth(x):
        c = min(max(x, 0.0), 1.0)
        return c * c * (3 - 2 * c)

    bars = []
    for i in range(n):
        for j in range(n):
            distance = abs(i - j)
            height = 0.55 + entry(i, j) * 0.6 if distance <= 1 else 0.18 + entry(i, j) * 0.7
            at = move((j - (n - 1) / 2) * cell, 0.06 + height / 2, (i - (n - 1) / 2) * cell)
            if distance <= 1:
                bars.append(box(cell * 0.62, height, cell * 0.62, at))
            else:  # still pose: mid-collapse, 3.1 s into the loop
                sink = smooth((3.1 - matrix_start(distance)) / 0.8)
                bars.append(box(cell * 0.62, height, cell * 0.62, at, kind=Bar, sink=sink, cls=f'sink s{distance}'))

    def css(cam):
        rules = f'.sink{{animation:{MATRIX_PERIOD}s ease-in-out infinite}}'
        for distance in range(2, n):
            rules += f'.s{distance}{{animation-name:sink{distance}}}'
            rules += matrix_keyframes('sink', distance, 'transform:translateY(var(--h))', 'transform:translateY(0)')
        return rules

    return {'items': [plate, Sorted(bars)], 'center': (0, 0.4, 0), 'view': 1.7, 'yaw': -0.62, 'css': css}


# ── Fig. — a railcar on its track (RailSense) ─────────────────────────

def rail():
    gauge, half, yaw = 0.36, 2.3, -0.6
    sleepers = []
    x = -half + 0.12
    while x <= half:
        sleepers.append(box(0.14, 0.06, 1.02, move(x, 0.03, 0)))
        x += 0.37
    rails = [box(half * 2, 0.07, 0.05, move(0, 0.095, z)) for z in (-gauge, gauge)]

    wire_y = 1.86
    masts, overhead = [], [[(-half, wire_y, 0), (half, wire_y, 0)]]
    arms = []
    for x in (-half + 0.3, half - 0.3):
        masts.append(box(0.06, wire_y + 0.1, 0.06, move(x, (wire_y + 0.1) / 2, -0.78)))
        arms.append([(x, wire_y + 0.06, -0.78), (x, wire_y + 0.06, 0.05)])

    def wheel(x, z):
        return cylinder(0.16, 0.16, 0.07, 14, chain(turn_x(math.pi / 2), move(x, 0.29, z)))

    body = box(2.0, 0.78, 0.8, move(0, 0.91, 0))
    for z in (-0.402, 0.402):
        for x in (-0.7, -0.24, 0.24, 0.7):
            body.decal([(x - 0.16, 0.86, z), (x + 0.16, 0.86, z), (x + 0.16, 1.18, z), (x - 0.16, 1.18, z)],
                       closed=True, normal=(0, 0, z))
    for x in (-1.002, 1.002):
        body.decal([(x, 0.86, -0.28), (x, 0.86, 0.28), (x, 1.18, 0.28), (x, 1.18, -0.28)],
                   closed=True, normal=(x, 0, 0))
    top = 1.37
    pantograph = Lines([[(-0.3, top, 0), (0.05, (top + wire_y) / 2, 0), (-0.15, wire_y, 0)],
                        [(-0.15, wire_y, -0.2), (-0.15, wire_y, 0.2)]])
    car = Group([
        wheel(-0.6, -gauge), wheel(0.6, -gauge),          # far side first
        box(1.75, 0.1, 0.62, move(0, 0.47, 0)),
        wheel(-0.6, gauge), wheel(0.6, gauge),
        body,
        box(1.8, 0.07, 0.62, move(0, 1.335, 0)),
        pantograph,
    ], cls='car')

    def css(cam):
        ox, oy = cam.screen((0, 0, 0))
        px, py = cam.screen((1.0, 0, 0))
        dx, dy = px - ox, py - oy
        return ('.car{animation:car 5.7s ease-in-out infinite alternate}'
                f'@keyframes car{{from{{transform:translate({-dx:.1f}px,{-dy:.1f}px)}}'
                f'to{{transform:translate({dx:.1f}px,{dy:.1f}px)}}}}')

    reach = [(x + shift, y, z) for x, y, z in car.points() for shift in (-1.0, 1.0)]
    return {'items': [*masts, Sorted(sleepers), *rails, car, Lines(overhead, 'thin'), Lines(arms)],
            'center': (0, 0.85, 0), 'view': 1.75, 'yaw': yaw, 'css': css, 'reach': reach}


MODELS = {'steps': steps, 'journal': journal, 'matrix': matrix, 'rail': rail}


# ── Fig. — the contribution calendar as a skyline ─────────────────────

def skyline(days, first_weekday, width, height, cx, cy, tallest=5.5, pad=(10, 44, 10, 44)):
    """One block per day on a week × weekday grid; height is the day's count.

    `pad` (left, top, right, bottom) keeps room for the annotations. Returns
    the drawing plus the anchor points the composer annotates.
    """
    peak = max(day['count'] for day in days) or 1
    weeks = (first_weekday + len(days) + 6) // 7
    camera = Camera((weeks / 2, 1.4, 3.5), 1, -0.3, width, height, cx, cy)
    # The calendar's footprint plus its tallest block.
    corners = [(0, 0, 0), (weeks, 0, 0), (weeks, 0, 7), (0, 0, 7), (0, tallest + 0.35, 0), (weeks, tallest + 0.35, 7)]
    fit(camera, corners, cx - width / 2 + pad[0], cy - height / 2 + pad[1],
        cx + width / 2 - pad[2], cy + height / 2 - pad[3])
    renderer = Renderer(camera, 'k')

    blocks, flat, peak_top, months = [], '', None, []
    seen_month = None
    for index, day in enumerate(days):
        week, weekday = divmod(first_weekday + index, 7)
        x, z = week + 0.5, weekday + 0.5
        month = day['date'][:7]
        if month != seen_month:
            seen_month = month
            if day['date'][8:] <= '07' or index == 0:
                months.append((day['date'], camera.screen((week + (1 if weekday else 0), 0, 7))))
        count = day['count']
        if not count:
            tile = [(x - 0.39, 0, z + 0.39), (x + 0.39, 0, z + 0.39), (x + 0.39, 0, z - 0.39), (x - 0.39, 0, z - 0.39)]
            flat += _d([camera.screen(p) for p in tile], True)
            continue
        h = 0.35 + tallest * math.log1p(count) / math.log1p(peak)
        block = box(0.78, h, 0.78, move(x, h / 2, z))
        blocks.append((camera.depth((x, 0, z)), renderer.solid(block)))
        if count == peak and peak_top is None:
            peak_top = (camera.screen((x, h, z)), day)
    body = f'<path d="{flat}" fill="{INK}" fill-opacity=".13" stroke="none"/>'
    body += ''.join(svg for _, svg in sorted(blocks, key=lambda b: b[0]))
    svg = (f'<g fill="none" stroke="{INK}" stroke-width=".9" stroke-linecap="round" '
           f'stroke-linejoin="round">{body}</g>')
    front = (camera.screen((0, 0, 7)), camera.screen((weeks, 0, 7)))
    return {'svg': svg, 'camera': camera, 'peak': peak_top, 'months': months, 'front': front, 'weeks': weeks}
