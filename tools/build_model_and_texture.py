"""Lucky v3: shaggy cairn-terrier build with big corgi-style ears, in Lucky's own colours
(black coat, silver/white face, white chest and front paws) plus a red collar.
Writes Lucky.bbmodel (texture embedded) + lucky.png into OUT_DIR.
usage: python build_model_and_texture.py <out_dir>"""
import base64, json, random, struct, sys, uuid, zlib

OUT_DIR = sys.argv[1]
W = H = 64
rng = random.Random(42)
CLEAR = (0, 0, 0, 0)
px = [[CLEAR] * W for _ in range(H)]


def c(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


BLK = [c('16181c'), c('1c1f24'), c('23262d'), c('1a1c21')]
SHEEN = [c('323844'), c('3b4250'), c('2b303a')]
GRY = [c('55585f'), c('686b72'), c('4a4d54')]
SIL = [c('a8a7a4'), c('bcbab5'), c('cfccc5'), c('949390')]
WHT = [c('f1eee7'), c('e4e0d7'), c('d8d3c9')]
PAD = [c('5e4c4a'), c('6d5855')]
INNER = [c('6b5054'), c('7a5d61'), c('5c4448')]
TAN = [c('7d6650'), c('8c735a'), c('6e5844')]
RED = [c('b3262e'), c('c22f37')]
RED_D = c('7e1a20')
GOLD = [c('f0c43c'), c('e0b032')]
NOSE = c('0c0c0e')
EYE = c('08080a')


def put(x, y, col):
    if 0 <= x < W and 0 <= y < H:
        px[y][x] = col


def fill(r, pal):
    x0, y0, x1, y1 = r
    for y in range(y0, y1):
        for x in range(x0, x1):
            put(x, y, rng.choice(pal))


def streaks(r, top, bottom, sheen=None, fade=0.5):
    """Hair strands: each column keeps its tone, top palette blending into bottom."""
    x0, y0, x1, y1 = r
    h = max(1, y1 - y0)
    for x in range(x0, x1):
        s = rng.random()
        for y in range(y0, y1):
            t = (y - y0 + 0.5) / h
            pal = bottom if t + (s - 0.5) * 0.5 > fade else top
            col = pal[int(s * len(pal)) % len(pal)]
            if sheen and rng.random() < 0.12:
                col = rng.choice(sheen)
            put(x, y, col)


def ragged(r, edge='bottom', step=2, start=1):
    """Shaggy outline: punch transparent gaps along one edge of a face."""
    x0, y0, x1, y1 = r
    if edge in ('bottom', 'top'):
        y = y1 - 1 if edge == 'bottom' else y0
        for i, x in enumerate(range(x0, x1)):
            if i % step == start:
                put(x, y, CLEAR)
    else:
        x = x1 - 1 if edge == 'right' else x0
        for i, y in enumerate(range(y0, y1)):
            if i % step == start:
                put(x, y, CLEAR)


def faces(u, v, w, h, d):
    return {
        'up': (u + d, v, u + d + w, v + d),
        'down': (u + d + w, v, u + d + 2 * w, v + d),
        'east': (u, v + d, u + d, v + d + h),
        'north': (u + d, v + d, u + d + w, v + d + h),
        'west': (u + d + w, v + d, u + 2 * d + w, v + d + h),
        'south': (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h),
    }


SIDES = ('east', 'north', 'west', 'south')
CUBES = {}


def box(name, uv, frm, to):
    CUBES[name] = (uv, frm, to)
    w, h, d = (int(round(to[i] - frm[i])) for i in range(3))
    return faces(uv[0], uv[1], w, h, d)


# ------------------------------------------------------------------ geometry
# head (pivot 0,10,-5)
F_head = box('head', (0, 0), [-3, 8, -10], [3, 14, -5])                    # 6x6x5
F_face = box('face_fur', (0, 11), [-4.5, 7, -10.25], [4.5, 14, -10.25])     # 9x7 plate
F_eyeL = box('eye_left', (54, 8), [1.5, 11, -10.75], [3.5, 13, -9.75])     # 2x2x1
box('eye_right', (54, 8), [-3.5, 11, -10.75], [-1.5, 13, -9.75])
F_tuft = box('head_tuft', (40, 12), [-3.5, 14, -9.5], [3.5, 15, -6.5])     # 7x1x3
F_muz = box('muzzle', (22, 10), [-1.5, 8, -12.25], [1.5, 10, -10.25])      # 3x2x2
F_nose = box('nose', (26, 39), [-1, 9, -12.75], [1, 11, -11.75])          # 2x2x1 big button nose
F_beard = box('beard', (0, 44), [-3.5, 5, -12.3], [3.5, 8, -12.3])         # 7x3 plate, rounded
F_beardS = box('beard_side_left', (14, 44), [3.5, 5, -12.3], [3.5, 8, -10.3])  # 0x3x2 jaw fluff
box('beard_side_right', (14, 44), [-3.5, 5, -12.3], [-3.5, 8, -10.3])
F_brow = box('brow_left', (32, 39), [1, 13, -11], [4, 14, -10])            # 3x1x1 bushy brows
box('brow_right', (32, 39), [-4, 13, -11], [-1, 14, -10])
F_fringe = box('fringe', (40, 39), [-1.5, 12, -10.6], [1.5, 15, -10.6])    # 3x3 plate, forehead fringe
F_whis = box('whiskers_left', (60, 8), [1.6, 7, -12.25], [1.6, 9, -10.25])  # 0x2x2
box('whiskers_right', (60, 8), [-1.6, 7, -12.25], [-1.6, 9, -10.25])
F_tongue = box('tongue', (54, 6), [-0.5, 7.5, -12.6], [0.5, 8.5, -11.6])   # 1x1x1
F_ear = box('ear_left', (54, 0), [0, 13.5, -7.5], [5, 18.5, -7.5])        # 5x5 plate
box('ear_right', (54, 0), [-5, 13.5, -7.5], [0, 18.5, -7.5])
# body (pivot 0,6.5,0)
F_body = box('body', (0, 25), [-3, 4, -4.5], [3, 9, 4.5])                  # 6x5x9
F_coat = box('back_coat', (22, 0), [-3.5, 8.5, -4.5], [3.5, 9.5, 4.5])     # 7x1x9
F_ruff = box('chest_ruff', (18, 16), [-3.5, 3.5, -5.5], [3.5, 9.5, -2.5])  # 7x6x3
F_collar = box('collar', (0, 39), [-4, 7.5, -6.5], [4, 9.5, -3.5])         # 8x2x3
F_tag = box('collar_tag', (22, 39), [-0.5, 6.5, -6.9], [0.5, 7.5, -5.9])       # 1x1x1
F_skirt = box('skirt_left', (38, 16), [3.25, 2.5, -4], [3.25, 5.5, 4])     # 0x3x8 plate
box('skirt_right', (38, 16), [-3.25, 2.5, -4], [-3.25, 5.5, 4])
# tail (pivot 0,8.5,4)
F_tail = box('tail', (54, 16), [-1, 8, 3.5], [1, 14, 5.5])                 # 2x6x2
F_plume = box('tail_plume', (30, 27), [-1.5, 11.5, 3], [1.5, 15.5, 6])     # 3x4x3
# legs
LEG_POS = {'leg_front_left': (1.75, -2.75), 'leg_front_right': (-1.75, -2.75),
           'leg_back_left': (1.75, 2.75), 'leg_back_right': (-1.75, 2.75)}
LEG_UV = {'leg_front_left': (42, 27), 'leg_front_right': (42, 27),
          'leg_back_left': (50, 27), 'leg_back_right': (50, 27)}
F_legs = {}
for n, (lx, lz) in LEG_POS.items():
    F_legs[n] = box(n, LEG_UV[n], [lx - 1, 0, lz - 1], [lx + 1, 5, lz + 1])     # 2x5x2

# ------------------------------------------------------------------ texture
# skull
for r in F_head.values():
    streaks(r, BLK, BLK + SHEEN, SHEEN)
x0, y0, x1, y1 = F_head['up']
fill((x0 + 2, y0, x1 - 2, y1), SIL + WHT)

# face fur plate (9x7, front side): the shaggy cairn face, Lucky's colours
fx, fy = F_face['north'][:2]
# one char per pixel, rows top->bottom (y 14 -> 7); eyes sit on rows 1-2, muzzle covers rows 4-5 centre
# . clear  k black  g grey  s silver  w white  e dark eye socket
FACE = [
    '.gsksksg.',   # under the brows: dark with silver streaks
    'geekwkeeg',   # eyes (cubes sit here), white blaze between them
    'geekskeeg',
    'ggtksktgg',   # a touch of tan under the eyes, like the photos
    'sggkkkggs',   # muzzle covers the middle
    'ssgkkkgss',
    '.ss...ss.',   # beard plate covers the centre
]
pal = {'k': BLK + SHEEN[:1], 'g': GRY + BLK[:1], 's': SIL + GRY[1:2], 'w': WHT + SIL[2:3],
       'e': [c('0f1013')], 't': TAN + GRY[:1]}
for ry, row in enumerate(FACE):
    for rx, ch in enumerate(row):
        put(fx + rx, fy + ry, CLEAR if ch == '.' else rng.choice(pal[ch]))
for k in ('south', 'up', 'down', 'east', 'west'):
    x0, y0, x1, y1 = F_face[k]
    for y in range(y0, y1):
        for x in range(x0, x1):
            mirror = px[fy + (y - y0)][fx + (x1 - 1 - x)] if k == 'south' else None
            put(x, y, CLEAR if mirror == CLEAR else rng.choice(BLK + GRY[:1]))

# eyes: warm brown with a dark pupil and a soft catchlight (the photos show brown eyes)
for r in F_eyeL.values():
    fill(r, [c('1a100a')])
ex, ey = F_eyeL['north'][:2]
put(ex, ey, c('dccab4'))          # soft catchlight
put(ex + 1, ey, c('5a3218'))      # iris
put(ex, ey + 1, c('4a2812'))      # iris
put(ex + 1, ey + 1, c('140b06'))  # pupil

# bushy silver eyebrows sticking out over the eyes
for r in F_brow.values():
    streaks(r, SIL + WHT, SIL + GRY[1:2])
bx0, by0 = F_brow['north'][:2]
put(bx0 + 2, by0, rng.choice(GRY))

# forehead fringe: white blaze in the middle, dark hair either side, wispy ends
FR = ['gwg', 'kwk', '.s.']
frx, fry = F_fringe['north'][:2]
frs = F_fringe['south'][:2]
for ry, row in enumerate(FR):
    for rx, ch in enumerate(row):
        col = CLEAR if ch == '.' else rng.choice(pal[ch])
        put(frx + rx, fry + ry, col)
        put(frs[0] + 2 - rx, frs[1] + ry, CLEAR if ch == '.' else rng.choice(BLK))

# tuft on top of the head (white blaze, like the photo)
for r in F_tuft.values():
    streaks(r, WHT + SIL, SIL + GRY[:1])
for k in SIDES:
    ragged(F_tuft[k], 'top', 2, 0)

# muzzle, nose, beard, whiskers, tongue
for k, r in F_muz.items():
    streaks(r, GRY + SIL, SIL + TAN[:1], fade=0.45)
x0, y0, x1, y1 = F_muz['up']
for y in range(y0, y1):
    put(x0 + 1, y, rng.choice(BLK))                      # dark bridge up to the nose
mx, my = F_muz['north'][:2]
put(mx, my + 1, rng.choice(TAN)); put(mx + 2, my + 1, rng.choice(TAN))
put(mx + 1, my + 1, c('2a1e1a'))                          # mouth
for r in F_nose.values():
    fill(r, [NOSE])
nx, ny = F_nose['north'][:2]
put(nx, ny, c('3a3a40'))                                  # shine
put(nx, ny + 1, c('050506')); put(nx + 1, ny + 1, c('050506'))  # nostrils
ux, uy = F_nose['up'][:2]
put(ux, uy, c('2c2c31'))

# rounded grizzled beard framing the jaw (the red line in the photo)
BEARD = ['swstsws', '.swwws.', '..s.s..']
bpal = {'s': SIL + GRY[1:2], 'w': WHT + SIL[1:3], 't': TAN}
bnx, bny = F_beard['north'][:2]
bsx, bsy = F_beard['south'][:2]
for ry, row in enumerate(BEARD):
    for rx, ch in enumerate(row):
        put(bnx + rx, bny + ry, CLEAR if ch == '.' else rng.choice(bpal[ch]))
        put(bsx + 6 - rx, bsy + ry, CLEAR if ch == '.' else rng.choice(GRY + SIL[3:]))
for k, r in F_beardS.items():
    streaks(r, SIL + GRY[1:2], SIL + WHT)
for k in ('east', 'west'):
    ragged(F_beardS[k], 'bottom', 2, 1)
for r in F_whis.values():
    streaks(r, SIL, WHT + SIL)
for k in ('east', 'west'):
    ragged(F_whis[k], 'bottom', 2, 0)
for r in F_tongue.values():
    fill(r, [c('e57b8e'), c('d66a7e')])

# corgi-style ears: big flat triangles, black back, rosy inner, silver fringe
EAR = ['..x..', '.xxx.', '.xxx.', 'xxxxx', 'xxxxx']
ax, ay = F_ear['north'][:2]
bx, by = F_ear['south'][:2]
for ry, row in enumerate(EAR):
    for rx, ch in enumerate(row):
        if ch == '.':
            put(ax + rx, ay + ry, CLEAR); put(bx + rx, by + ry, CLEAR)
            continue
        edge = rx in (0, 4) or ry == 0 or EAR[ry - 1][rx] == '.'
        inner = rng.choice(SIL + WHT) if edge else rng.choice(INNER)
        if ry >= 4 and not edge:
            inner = rng.choice(GRY + INNER[:1])
        put(ax + rx, ay + ry, inner)
        put(bx + rx, by + ry, rng.choice(SIL) if ry == 0 or (ry == 1 and rx in (1, 3)) else rng.choice(BLK + SHEEN))

# body core
for r in F_body.values():
    fill(r, BLK + SHEEN[:1])
fill(F_body['down'], SIL + GRY)

# shaggy back coat
for r in F_coat.values():
    fill(r, BLK + SHEEN)
for k in ('east', 'west'):
    ragged(F_coat[k], 'bottom', 2, 1)

# chest ruff: white chest, black shoulders
for k, r in F_ruff.items():
    if k == 'north':
        streaks(r, WHT + SIL, WHT)
    elif k in ('east', 'west'):
        streaks(r, BLK + GRY[:1], SIL + WHT, fade=0.45)
    elif k == 'down':
        fill(r, WHT + SIL)
    else:
        fill(r, BLK)
for k in ('north', 'east', 'west'):
    ragged(F_ruff[k], 'bottom', 2, 1)

# skirt plates: long black hair along the flanks with silver tips
for k in ('east', 'west'):
    streaks(F_skirt[k], BLK, GRY + SIL[3:], SHEEN, fade=0.7)
    ragged(F_skirt[k], 'bottom', 2, 0)

# collar + golden tag
for k, r in F_collar.items():
    fill(r, RED)
for k in SIDES:
    x0, y0, x1, y1 = F_collar[k]
    for x in range(x0, x1):
        if (x - x0) % 3 == 1:
            put(x, y0, c('d8d8d8'))   # little studs
fill(F_collar['up'], [RED_D]); fill(F_collar['down'], [RED_D])
for r in F_tag.values():
    fill(r, GOLD)
put(F_tag['north'][0], F_tag['north'][1], c('fff0a0'))

# legs: white front legs, black back legs with white socks
for n, F in F_legs.items():
    front = 'front' in n
    for r in F.values():
        if front:
            streaks(r, SIL + WHT, WHT)
        else:
            streaks(r, BLK, BLK + GRY)
    for k in SIDES:
        x0, y0, x1, y1 = F[k]
        fill((x0, y1 - 1, x1, y1), WHT + SIL)
    fill(F['down'], PAD)

# tail + plume
for r in F_tail.values():
    streaks(r, BLK, BLK + SHEEN)
for k, r in F_plume.items():
    streaks(r, SIL + WHT, BLK + SHEEN, fade=0.4)
for k in SIDES:
    ragged(F_plume[k], 'top', 2, 0)
fill(F_plume['up'], WHT + SIL)


def png_bytes():
    raw = b''.join(b'\x00' + b''.join(bytes(p) for p in row) for row in px)

    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


png = png_bytes()
with open(f'{OUT_DIR}/lucky.png', 'wb') as f:
    f.write(png)

# ------------------------------------------------------------------ model
urng = random.Random(1)


def uid():
    return str(uuid.UUID(int=urng.getrandbits(128)))


def face_uvs(u, v, w, h, d):
    return {
        'north': [u + d, v + d, u + d + w, v + d + h],
        'east': [u, v + d, u + d, v + d + h],
        'south': [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h],
        'west': [u + d + w, v + d, u + 2 * d + w, v + d + h],
        'up': [u + d + w, v + d, u + d, v],
        'down': [u + d + 2 * w, v, u + d + w, v + d],
    }


elements = []


def cube(name, origin):
    uv, frm, to = CUBES[name]
    w, h, d = (int(round(to[i] - frm[i])) for i in range(3))
    e = {'name': name, 'box_uv': True, 'rescale': False, 'locked': False, 'render_order': 'default',
         'allow_mirror_modeling': True, 'from': frm, 'to': to, 'autouv': 0, 'color': 0, 'origin': origin,
         'uv_offset': list(uv), 'mirror_uv': False,
         'faces': {k: {'uv': v, 'texture': 0} for k, v in face_uvs(uv[0], uv[1], w, h, d).items()},
         'type': 'cube', 'uuid': uid()}
    elements.append(e)
    return e['uuid']


groups = {}


def group(name, origin, children, rotation=(0, 0, 0)):
    g = {'name': name, 'origin': origin, 'rotation': list(rotation), 'color': 0, 'uuid': uid(),
         'export': True, 'mirror_uv': False, 'isOpen': True, 'locked': False, 'visibility': True,
         'autouv': 0, 'children': [cube(ch, origin) if isinstance(ch, str) else ch for ch in children]}
    groups[name] = g['uuid']
    return g


head = group('head', [0, 10, -5], [
    'head', 'face_fur', 'eye_left', 'eye_right', 'brow_left', 'brow_right', 'fringe', 'head_tuft',
    'muzzle', 'nose', 'beard', 'beard_side_left', 'beard_side_right',
    'whiskers_left', 'whiskers_right', 'tongue',
    group('ear_left', [2.5, 13.5, -7.5], ['ear_left'], (0, -15, -22)),
    group('ear_right', [-2.5, 13.5, -7.5], ['ear_right'], (0, 15, 22)),
])
body = group('body', [0, 6.5, 0], [
    'body', 'back_coat', 'chest_ruff', 'collar', 'collar_tag',
    group('skirt_left', [3.25, 5.5, 0], ['skirt_left'], (0, 0, 4)),
    group('skirt_right', [-3.25, 5.5, 0], ['skirt_right'], (0, 0, -4)),
])
tail = group('tail', [0, 8.5, 4], ['tail', 'tail_plume'], (25, 0, 0))
legs = [group(n, [LEG_POS[n][0], 5, LEG_POS[n][1]], [n]) for n in LEG_POS]
outliner = [body, head, tail] + legs


def kf(t, x, y, z):
    return {'channel': 'rotation', 'data_points': [{'x': str(x), 'y': str(y), 'z': str(z)}],
            'uuid': uid(), 'time': t, 'color': -1, 'interpolation': 'catmullrom'}


def cycle(length, frames):
    n = len(frames)
    out = [kf(round(length * i / n, 4), *f) for i, f in enumerate(frames)]
    out.append(kf(length, *frames[0]))
    return out


def anim(name, length, bones):
    return {'uuid': uid(), 'name': name, 'loop': 'loop', 'override': False, 'length': length,
            'snapping': 24, 'selected': False, 'anim_time_update': '', 'blend_weight': '',
            'start_delay': '', 'loop_delay': '',
            'animators': {groups[b]: {'name': b, 'type': 'bone', 'keyframes': k} for b, k in bones.items()}}


animations = [
    anim('animation.lucky.idle', 3.0, {
        'head': cycle(3.0, [(0, 0, 0), (0, 0, 0), (0, 0, 14), (0, 0, 14), (0, 0, 0), (-4, 0, 0)]),
        'ear_left': cycle(3.0, [(0, -15, -22), (0, -15, -22), (0, -15, -22), (0, -15, -22), (8, -15, -32), (0, -15, -22)]),
        'tail': cycle(3.0, [(25, -10, 0), (25, 10, 0)]),
    }),
    anim('animation.lucky.tail_wag', 0.4, {
        'tail': cycle(0.4, [(25, -30, 0), (25, 30, 0)]),
    }),
    anim('animation.lucky.walk', 0.5, {
        'leg_front_left': cycle(0.5, [(32, 0, 0), (-32, 0, 0)]),
        'leg_back_right': cycle(0.5, [(32, 0, 0), (-32, 0, 0)]),
        'leg_front_right': cycle(0.5, [(-32, 0, 0), (32, 0, 0)]),
        'leg_back_left': cycle(0.5, [(-32, 0, 0), (32, 0, 0)]),
        'skirt_left': cycle(0.5, [(4, 0, 4), (-4, 0, 8)]),
        'skirt_right': cycle(0.5, [(-4, 0, -8), (4, 0, -4)]),
        'head': cycle(0.5, [(0, 0, 0), (3, 0, 0)]),
        'tail': cycle(0.5, [(25, -15, 0), (25, 15, 0)]),
    }),
]

model = {
    'meta': {'format_version': '4.10', 'model_format': 'modded_entity', 'box_uv': True},
    'name': 'Lucky', 'model_identifier': 'lucky',
    'modded_entity_entity_class': 'ModelLucky', 'modded_entity_version': '1.12',
    'modded_entity_flip_y': False, 'visible_box': [1, 1, 0],
    'variable_placeholders': '', 'variable_placeholder_buttons': [], 'timeline_setups': [],
    'unhandled_root_fields': {}, 'resolution': {'width': 64, 'height': 64},
    'elements': elements, 'outliner': outliner,
    'textures': [{
        'path': '', 'name': 'lucky.png', 'folder': '', 'namespace': '', 'id': '0',
        'width': 64, 'height': 64, 'uv_width': 64, 'uv_height': 64, 'particle': False,
        'use_as_default': False, 'layers_enabled': False, 'sync_to_project': '',
        'render_mode': 'default', 'render_sides': 'auto', 'frame_time': 1,
        'frame_order_type': 'loop', 'frame_order': '', 'frame_interpolate': False,
        'visible': True, 'internal': True, 'saved': True, 'uuid': uid(),
        'source': 'data:image/png;base64,' + base64.b64encode(png).decode(),
    }],
    'animations': animations,
}
with open(f'{OUT_DIR}/Lucky.bbmodel', 'w', encoding='utf-8') as f:
    json.dump(model, f, separators=(',', ':'))

# UV overlap check (cubes sharing a UV on purpose are listed once)
SHARED = {'eye_right', 'whiskers_right', 'brow_right', 'beard_side_right', 'ear_right', 'skirt_right', 'leg_front_right', 'leg_back_right'}
used = {}
for n, (uv, frm, to) in CUBES.items():
    if n in SHARED:
        continue
    w, h, d = (int(round(to[i] - frm[i])) for i in range(3))
    for r in faces(uv[0], uv[1], w, h, d).values():
        for y in range(r[1], r[3]):
            for x in range(r[0], r[2]):
                assert 0 <= x < 64 and 0 <= y < 64, (n, x, y)
                if (x, y) in used:
                    raise SystemExit(f'UV overlap {n} with {used[(x, y)]} at {x},{y}')
                used[(x, y)] = n
print('ok', len(elements), 'cubes,', len(animations), 'animations')
