"""Builds Lucky's two looks from the Better Dogs resource pack (OptiFine CEM, by MrBlueYeti):

  furry  = the Cairn terrier rig (Better Dogs "west_shihtzu" skeleton, skin wolf_tame93)
  shaved = the Chihuahua rig (skin wolf_tame45) wearing the Cairn's head

The CEM file keeps every breed in one 3002x32 texture; each skin only paints its own breed, so a box
belongs to the breed when its UV area is painted in that skin. The boxes are flattened into
world-aligned groups (body, head, ears, tail, 4 legs) so ModelLucky can animate them simply,
their UV areas are packed into one 128x64 texture and recoloured to Lucky's coat.

usage: python tools/gen_betterdogs.py <better_dogs_dir> <preview_dir>
writes src/main/java/com/luckymod/client/LuckyRigs.java and textures/entity/lucky.png
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

BD, PREVIEW = sys.argv[1], sys.argv[2]
# The texture is hand-painted from v1.8 on (see the Lucky_*.bbmodel files): only rebuild it when asked.
WRITE_TEXTURE = '--texture' in sys.argv[3:]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JEM = os.path.join(BD, 'assets/minecraft/optifine/cem/wolf.jem')
SKINS = os.path.join(BD, 'assets/minecraft/optifine/mob/wolf')
jem = json.load(open(JEM))
Z_SHIFT = -5.0  # Better Dogs bodies sit ~5px behind the wolf's origin; centre them


def rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler_zyx(M):
    """M = Rz(z) Ry(y) Rx(x) -> (x, y, z), the order ModelRenderer applies its angles."""
    y = math.asin(max(-1.0, min(1.0, -M[2, 0])))
    if abs(math.cos(y)) > 1e-6:
        x = math.atan2(M[2, 1], M[2, 2]); z = math.atan2(M[1, 0], M[0, 0])
    else:
        x = math.atan2(-M[1, 2], M[1, 1]); z = 0.0
    return x, y, z


# rest-pose values the pack's animations write (standing, not a puppy)
ANIM = {'mane_rotation': {'rx': 0.0}, 'west_shihtzu_head': {'tz': math.radians(45)},
        'west_shihtzu_bodymane': {'tz': math.radians(-70)}, 'west_shihtzu_body': {'ty': 0.0}}


def node_local(n):
    inv = n.get('invertAxis', '')
    t = list(n.get('translate', [0, 0, 0])); r = [math.radians(v) for v in n.get('rotate', [0, 0, 0])]
    for i, a in enumerate('xyz'):
        if a in inv and i < 2:
            t[i] = -t[i]; r[i] = -r[i]
    for k, v in ANIM.get(n.get('id') or n.get('part'), {}).items():
        (t if k[0] == 't' else r)['xyz'.index(k[1])] = v
    return t, r


def box_local(n, b):
    x, y, z, dx, dy, dz = b['coordinates']
    inv = n.get('invertAxis', '')
    if 'x' in inv: x = -x - dx
    if 'y' in inv: y = -y - dy
    return [x, y, z, dx, dy, dz]


def find(n, name, path=()):
    if (n.get('id') or n.get('part')) == name: return path + (n,)
    for s in n.get('submodels', []):
        r = find(s, name, path + (n,))
        if r: return r


def skin(n):
    return Image.open(os.path.join(SKINS, f'wolf_tame{n}.png')).convert('RGBA')


def uv_rect(b):
    u, v = b['textureOffset']; dx, dy, dz = [int(round(t)) for t in b['coordinates'][3:]]
    return (u, v, 2 * (dx + dz), dz + dy)


def painted(img, r):
    u, v, w, h = r
    return img.crop((u, v, u + max(w, 1), v + max(h, 1))).getchannel('A').getextrema()[1] > 0


def collect(breed_root, groups, img, face_img=None):
    """-> list of boxes: dict(group, T, M, local box, uv, delta, mirror). groups: node id -> group name."""
    mane = [m for m in jem['models'] if m['part'] == 'mane'][0]
    path = find(mane, breed_root)
    T = np.array([-1.0, 14.0, 2.0]); M = rx(math.pi / 2)  # vanilla wolf mane pivot, standing
    for n in path[:-1]:
        t, r = node_local(n); T = T + M @ np.array(t); M = M @ rz(r[2]) @ ry(r[1]) @ rx(r[0])
    out, pivots = [], {}

    def walk(n, T, M, group, mirror):
        t, r = node_local(n); T = T + M @ np.array(t); M = M @ rz(r[2]) @ ry(r[1]) @ rx(r[0])
        nid = n.get('id')
        if nid in groups:
            group = groups[nid]; pivots[group] = T + [0, 0, Z_SHIFT]
        mirror = mirror ^ ('u' in n.get('mirrorTexture', ''))
        for b in n.get('boxes', []):
            if 'textureOffset' not in b or not painted(img, uv_rect(b)): continue
            src = face_img if (face_img is not None and group == 'head') else img
            out.append(dict(group=group, T=T + [0, 0, Z_SHIFT], M=M, box=box_local(n, b), uv=uv_rect(b),
                            delta=b.get('sizeAdd', 0.0), mirror=mirror, src=src, node=nid))
        for s in n.get('submodels', []): walk(s, T, M, group, mirror)

    walk(path[-1], T, M, 'body', False)
    return out, pivots


cairn_img, chi_img, face_img = skin(93), skin(45), skin(92)  # 92: light wheaten face -> silver
CAIRN_GROUPS = {'west_shihtzu_head': 'head', 'bone137': 'earRight', 'bone141': 'earLeft', 'west_staart': 'tail',
                'west_shihtzu_leg1': 'legBackRight', 'west_shihtzu_leg2': 'legBackLeft',
                'west_shihtzu_leg3': 'legFrontRight', 'west_shihtzu_leg4': 'legFrontLeft'}
CHI_GROUPS = {'chihuahuahead': 'head', 'tail2': 'tail',
              'chihuahualeg1': 'legBackRight', 'chihuahualeg2': 'legBackLeft',
              'chihuahualeg3': 'legFrontRight', 'chihuahualeg4': 'legFrontLeft'}
cairn, cairn_piv = collect('west_shihtzu', CAIRN_GROUPS, cairn_img, face_img)
chi, chi_piv = collect('chihuahua2', CHI_GROUPS, chi_img)

# shaved Lucky: chihuahua body, legs and tail + the cairn's face (its ears included)
HEAD_PARTS = ('head', 'earLeft', 'earRight')
chi = [b for b in chi if b['group'] not in HEAD_PARTS]
head_shift = np.array([0.0, 2.6, 1.2])
# the furry coat is the cairn shrunk to the chihuahua's height (its body then matches the chihuahua's),
# with the head scaled back up so both looks share the same face size and position
FURRY_SCALE = (24.0 - (cairn_piv['head'][1] + head_shift[1])) / (24.0 - cairn_piv['head'][1])
RIG_SCALE = {'furry': FURRY_SCALE, 'shaved': 1.0}
HEAD_SCALE = {'furry': 1.0 / FURRY_SCALE, 'shaved': 1.0}
shaved_piv = dict(chi_piv)
for g in HEAD_PARTS: shaved_piv[g] = cairn_piv[g] + head_shift
shaved = chi + [dict(b, T=b['T'] + head_shift) for b in cairn if b['group'] in HEAD_PARTS]
# the cairn's chest fur (mane hair) has no place on a trimmed dog either
RIGS = {'furry': (cairn, cairn_piv), 'shaved': (shaved, shaved_piv)}

# ---------- texture: pack every UV area into 128x64 and recolour ----------
TW, TH = 128, 64
atlas = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
placed, shelf_x, shelf_y, shelf_h = {}, 0, 0, 0


def recolor(img, kind):
    """Lucky is greyscale: near-black coat, silver face, white chest. Keep pinks (tongue)."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0: continue
            if r > 150 and r > g + 40 and b >= g - 5:  # pink tongue / inner ear (not tan)
                continue
            l = 0.3 * r + 0.59 * g + 0.11 * b
            if kind == 'face':
                l = 30 + (l - 70) * 0.25 if l > 70 else l * 0.3  # dark grey fur; eyes/nose stay black
            elif kind == 'cairn':
                l = 14 + l * 0.45  # near-black coat, same as the shaved look
            else:
                l = l * 0.85 if l < 110 else min(240, l * 1.1)
            l = max(10, min(245, l))
            px[x, y] = (int(l * 0.97), int(l * 0.99), int(l * 1.03 if l * 1.03 < 255 else 255), a)
    return img


for rig in (cairn, chi):
    for b in rig:
        key = (id(b['src']), b['uv'])
        if key in placed: continue
        u, v, w, h = b['uv']
        w, h = max(w, 1), max(h, 1)
        if shelf_x + w > TW: shelf_x, shelf_y, shelf_h = 0, shelf_y + shelf_h, 0
        if shelf_y + h > TH: raise SystemExit('texture atlas full')
        piece = recolor(b['src'].crop((u, v, u + w, v + h)),
                        'face' if b['src'] is face_img else 'cairn' if b['src'] is cairn_img else 'chi')
        atlas.paste(piece, (shelf_x, shelf_y))
        placed[key] = (shelf_x, shelf_y)
        shelf_x += w; shelf_h = max(shelf_h, h)
for rig in (cairn, shaved):
    for b in rig:
        b['nu'], b['nv'] = placed[(id(b['src']), b['uv'])]

print('atlas used up to y =', shelf_y + shelf_h)

# ---------- Java ----------
GROUP_ORDER = ['body', 'head', 'earLeft', 'earRight', 'tail',
               'legFrontLeft', 'legFrontRight', 'legBackLeft', 'legBackRight']
PARENT = {'earLeft': 'head', 'earRight': 'head'}


def f(v):
    v = round(float(v), 4) + 0.0
    return f'{v}F'


def tail_axis(boxes, piv):
    """Side-to-side wag axis: perpendicular to the tail and to the dog's left-right axis."""
    pts = [b['T'] + b['M'] @ np.array([b['box'][0] + i * b['box'][3], b['box'][1] + j * b['box'][4],
                                       b['box'][2] + k * b['box'][5]])
           for b in boxes if b['group'] == 'tail' for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    tip = max(pts, key=lambda q: np.linalg.norm(q - piv['tail']))
    d = tip - piv['tail']; d = d / math.hypot(d[1], d[2])
    return d[2], -d[1]


java = ['package com.luckymod.client;', '',
        'import net.minecraft.client.model.ModelBase;', '',
        '/** Generated by tools/gen_betterdogs.py from the Better Dogs pack (MrBlueYeti): do not edit by hand. */',
        'final class LuckyRigs {', '', '    private LuckyRigs() {}', '']
for name, (boxes, piv) in RIGS.items():
    java.append(f'    static LuckyRig {name}(ModelBase model) {{')
    java.append('        LuckyRig r = new LuckyRig(model, 128, 64);')
    java.append(f'        r.scale = {f(RIG_SCALE[name])};')
    java.append(f'        r.headScale = {f(HEAD_SCALE[name])};')
    wy, wz = tail_axis(boxes, piv)
    java.append(f'        r.tailWagY = {f(wy)};')
    java.append(f'        r.tailWagZ = {f(wz)};')
    for g in GROUP_ORDER:
        p = piv.get(g, np.zeros(3))
        if g in PARENT: p = p - piv[PARENT[g]]
        java.append(f'        r.group("{g}", {PARENT.get(g) and chr(34) + PARENT[g] + chr(34) or "null"}, '
                    f'{f(p[0])}, {f(p[1])}, {f(p[2])});')
    for b in boxes:
        g = b['group']
        rel = b['T'] - piv.get(g, np.zeros(3))
        a = euler_zyx(b['M'])
        x, y, z, dx, dy, dz = b['box']
        java.append(f'        r.box("{g}", {f(rel[0])}, {f(rel[1])}, {f(rel[2])}, {f(a[0])}, {f(a[1])}, {f(a[2])}, '
                    f'{b["nu"]}, {b["nv"]}, {f(x)}, {f(y)}, {f(z)}, {int(round(dx))}, {int(round(dy))}, '
                    f'{int(round(dz))}, {f(b["delta"])}, {str(b["mirror"]).lower()}); // {b["node"]}')
    java += ['        return r;', '    }', '']
java.append('}')
open(os.path.join(ROOT, 'src/main/java/com/luckymod/client/LuckyRigs.java'), 'w', newline='\n').write('\n'.join(java) + '\n')

# ---------- preview: software render of both rigs, as ModelBox would draw them ----------
os.makedirs(PREVIEW, exist_ok=True)


def box_quads(b):
    x, y, z, dx, dy, dz = b['box']; d = b['delta']; u, v = b['nu'], b['nv']
    idx, idy, idz = [int(round(t)) for t in (dx, dy, dz)]
    x2, y2, z2 = x + dx + d, y + dy + d, z + dz + d
    x, y, z = x - d, y - d, z - d
    if b['mirror']: x, x2 = x2, x
    p = [(x, y, z), (x2, y, z), (x2, y2, z), (x, y2, z), (x, y, z2), (x2, y, z2), (x2, y2, z2), (x, y2, z2)]
    q = [((5, 1, 2, 6), (u + idz + idx, v + idz, u + idz + idx + idz, v + idz + idy)),
         ((0, 4, 7, 3), (u, v + idz, u + idz, v + idz + idy)),
         ((5, 4, 0, 1), (u + idz, v, u + idz + idx, v + idz)),
         ((2, 3, 7, 6), (u + idz + idx, v + idz, u + idz + idx + idx, v)),
         ((1, 0, 3, 2), (u + idz, v + idz, u + idz + idx, v + idz + idy)),
         ((4, 5, 6, 7), (u + idz + idx + idz, v + idz, u + idz + idx + idz + idx, v + idz + idy))]
    out = []
    for vi, (u1, v1, u2, v2) in q:
        verts = [np.array(p[i]) for i in vi]
        uvs = [(u2, v1), (u1, v1), (u1, v2), (u2, v2)]
        if b['mirror']: verts, uvs = verts[::-1], uvs[::-1]
        out.append(([b['T'] + b['M'] @ vv for vv in verts], uvs))
    return out


def scaled_all(boxes, s):
    feet = np.array([0.0, 24.0, 0.0])
    return [dict(b, T=feet + s * (b['T'] - feet), M=s * b['M']) for b in boxes]


def scaled_head(boxes, piv, s):
    out = []
    for b in boxes:
        if b['group'] in HEAD_PARTS:
            c = piv['head']; b = dict(b, T=c + s * (b['T'] - c), M=s * b['M'])
        out.append(b)
    return out


def texels(b):
    """(atlas x, atlas y, world point) for every texel the box draws."""
    for verts, uvs in b.get('_q') or box_quads(b):
        (u2, v1), (u1, _), (_, v2), _ = uvs
        if u1 == u2 or v1 == v2: continue
        V0, V1, V2, V3 = verts
        for ty in range(min(v1, v2), max(v1, v2)):
            for tx in range(min(u1, u2), max(u1, u2)):
                a = (tx + 0.5 - u1) / (u2 - u1); c = (ty + 0.5 - v1) / (v2 - v1)
                yield tx, ty, (1 - a) * (1 - c) * V1 + a * (1 - c) * V0 + (1 - a) * c * V2 + a * c * V3


def texels_facing(b):
    """Like texels(), plus whether the texel's face points forward (-Z, out of the face)."""
    quads = box_quads(b)
    centre = np.mean([v for verts, _ in quads for v in verts], axis=0)
    for verts, uvs in quads:
        d = np.mean(verts, axis=0) - centre
        n = d / np.linalg.norm(d) if np.linalg.norm(d) > 1e-6 else np.zeros(3)
        for tx, ty, w in texels(dict(b, _q=[(verts, uvs)])):
            yield tx, ty, w, n


WHITE = lambda l: int(min(245, 205 + (l - 90) * 0.35))


MUZZLE = {'west_mond', 'snor', 'snor2', 'snor3', 'snor4', 'bone142'}


def paint(boxes, piv, head_too, chest):
    """Lucky's markings: white chest, four white paws, white brows/fringe and muzzle."""
    body_pts = [w for b in boxes if b['group'] == 'body' for _, _, w in texels(b)]
    zfront = min(w[2] for w in body_pts); ymid = (min(w[1] for w in body_pts) + max(w[1] for w in body_pts)) / 2
    tail_pts = [w for b in boxes if b['group'] == 'tail' for _, _, w in texels(b)]
    tail_len = max(np.linalg.norm(w - piv['tail']) for w in tail_pts)
    apx = atlas.load()
    for b in boxes:
        g = b['group']
        if g in HEAD_PARTS and not head_too: continue
        for tx, ty, w, n in texels_facing(b):
            front, up = n[2] < -0.7, n[1] < -0.7
            r_, g_, b_, a_ = apx[tx, ty]
            if not a_: continue
            l = (r_ + g_ + b_) / 3
            white = False
            if g.startswith('leg'):
                white = w[1] > 21.6
            elif g == 'tail':
                white = np.linalg.norm(w - piv['tail']) > 0.68 * tail_len  # white tip
            elif g == 'body':
                # white collar: the whole middle of the chest front, plus the hanging chest fur
                white = chest and (b['node'] == 'west_shihtzu_mane_hair'
                                   or (front and w[2] < zfront + 1.2 and abs(w[0]) < 2.6)
                                   or (w[2] < zfront + 1.2 and w[1] > ymid + 0.5 and abs(w[0]) < 2.6))
            elif g == 'head':
                h = w - piv['head']
                # the black eyes and nose stay black (the face plate and skull are all fur)
                fur = l >= 27 or b['node'] in ('westie', 'west_shihtzu_head_rot')
                # fringe: a white tuft from the top of the head down between the eyes
                # tapers going down: wide at the top of the head, a thin point between the eyes
                fringe = h[1] < -3.4 and abs(h[0]) < 0.6 + (-3.4 - h[1]) * 0.75 and h[2] < -2.2
                # around the muzzle: the snout itself, the beard and the cheeks below the eyes
                # just above the nose: the top row of the snout's front and the top of the snout
                muzzle = b['node'] in MUZZLE and ((front and h[1] < -1.0) or (up and h[2] < -4.5 and l >= 18))
                white = (fur and fringe) or muzzle
            if white:
                v = WHITE(90 + (l % 7) * 6); apx[tx, ty] = (v - 3, v - 2, v, 255)


paint(cairn, cairn_piv, True, True)
paint(chi, chi_piv, False, False)  # the shaved coat already has its white chest
TEXTURE = os.path.join(ROOT, 'src/main/resources/assets/luckymod/textures/entity/lucky.png')
if WRITE_TEXTURE:
    atlas.save(TEXTURE)
else:
    atlas = Image.open(TEXTURE).convert('RGBA')  # keep the hand-painted pixels


def render(boxes, yaw, file, scale=14):
    V = ry(math.radians(yaw)) @ rx(math.radians(25))
    S = 520
    img = Image.new('RGBA', (S, S), (60, 64, 72, 255))
    faces = []
    for b in boxes:
        for verts, uvs in box_quads(b):
            w = [V @ (vv - np.array([0, 16, 0])) for vv in verts]
            n = np.cross(w[1] - w[0], w[2] - w[0])
            faces.append((np.mean([t[2] for t in w]), w, uvs))
    faces.sort(key=lambda t: -t[0])
    tex = atlas
    for _, w, uvs in faces:
        pts = [(S / 2 - t[0] * scale, S / 2 + t[1] * scale) for t in w]
        us = [t[0] for t in uvs]; vs = [t[1] for t in uvs]
        if max(us) == min(us) or max(vs) == min(vs): continue
        # affine map screen -> texture from three corners
        A = np.array([[pts[0][0], pts[0][1], 1], [pts[1][0], pts[1][1], 1], [pts[3][0], pts[3][1], 1]])
        if abs(np.linalg.det(A)) < 1e-6: continue
        cu = np.linalg.solve(A, [uvs[0][0], uvs[1][0], uvs[3][0]])
        cv = np.linalg.solve(A, [uvs[0][1], uvs[1][1], uvs[3][1]])
        layer = tex.transform((S, S), Image.AFFINE, tuple(cu) + tuple(cv), Image.NEAREST)
        mask = Image.new('L', (S, S), 0); ImageDraw.Draw(mask).polygon(pts, fill=255)
        alpha = Image.composite(layer.getchannel('A'), Image.new('L', (S, S), 0), mask)
        shade = 0.6 + 0.4 * abs(np.cross(w[1] - w[0], w[3] - w[0])[2] / (np.linalg.norm(np.cross(w[1] - w[0], w[3] - w[0])) + 1e-9))
        layer = Image.eval(layer.convert('RGB'), lambda c: int(c * shade))
        img.paste(layer, (0, 0), alpha)
    img.save(file)


for name, (boxes, piv) in RIGS.items():
    boxes = scaled_head(boxes, piv, HEAD_SCALE[name])
    boxes = scaled_all(boxes, RIG_SCALE[name])
    for yaw in (30, 150, 90, 0):
        render(boxes, yaw, os.path.join(PREVIEW, f'{name}_{yaw}.png'))
print('rigs:', {k: len(v[0]) for k, v in RIGS.items()})

# ---------- Blockbench files to paint the texture on the 3D model ----------
import base64, uuid


OUT = os.path.join(ROOT, 'blockbench')  # texture linked by a path relative to the .bbmodel


def bb_model(name, boxes, piv):
    """Modded-entity .bbmodel whose texture is linked to the mod's lucky.png (Ctrl+S saves it)."""
    rnd = __import__('random').Random(name)
    uid = lambda: str(uuid.UUID(int=rnd.getrandbits(128)))
    to_bb = lambda p: [-p[0], 24.0 - p[1], p[2]]
    elements, outliner = [], {}
    for g in GROUP_ORDER:
        outliner[g] = dict(name=g, origin=to_bb(piv.get(g, np.zeros(3))), rotation=[0, 0, 0], uuid=uid(),
                           export=True, isOpen=False, visibility=True, children=[])
    for k, b in enumerate(boxes):
        x, y, z, dx, dy, dz = b['box']
        ix, iy, iz = [int(round(t)) for t in (dx, dy, dz)]
        P = b['T']; ax, ay, az = euler_zyx(b['M'])
        u, v = b['nu'], b['nv']
        faces = {'north': [u + iz, v + iz, u + iz + ix, v + iz + iy], 'east': [u, v + iz, u + iz, v + iz + iy],
                 'south': [u + 2 * iz + ix, v + iz, u + 2 * iz + 2 * ix, v + iz + iy],
                 'west': [u + iz + ix, v + iz, u + 2 * iz + ix, v + iz + iy],
                 'up': [u + iz + ix, v + iz, u + iz, v], 'down': [u + iz + 2 * ix, v, u + iz + ix, v + iz]}
        cube = dict(name=b['node'], box_uv=True, rescale=False, locked=False, render_order='default',
                    allow_mirror_modeling=True,
                    **{'from': [-(P[0] + x + dx), 24.0 - (P[1] + y + dy), P[2] + z],
                       'to': [-(P[0] + x), 24.0 - (P[1] + y), P[2] + z + dz]},
                    autouv=0, color=k % 8, inflate=b['delta'], origin=to_bb(P), uv_offset=[u, v],
                    mirror_uv=b['mirror'], faces={f_: dict(uv=uvq, texture=0) for f_, uvq in faces.items()},
                    type='cube', uuid=uid())
        elements.append(cube)
        bone = dict(name=f"{b['node']}_{k}", origin=to_bb(P),
                    rotation=[-math.degrees(ax), -math.degrees(ay), math.degrees(az)], uuid=uid(), export=True,
                    isOpen=False, visibility=True, children=[cube['uuid']])
        outliner[b['group']]['children'].append(bone)
    for child, parent in PARENT.items():
        outliner[parent]['children'].append(outliner.pop(child))
    data = 'data:image/png;base64,' + base64.b64encode(open(TEXTURE, 'rb').read()).decode()
    model = dict(meta=dict(format_version='4.10', model_format='modded_entity', box_uv=True),
                 name=f'lucky_{name}', model_identifier='', visible_box=[1, 1, 0], variable_placeholders='',
                 variable_placeholder_buttons=[], timeline_setups=[], unhandled_root_fields={},
                 resolution=dict(width=TW, height=TH), elements=elements, outliner=list(outliner.values()),
                 textures=[dict(path='', relative_path=os.path.relpath(TEXTURE, OUT).replace(os.sep, '/'), name='lucky.png', folder='', namespace='', id='0',
                                width=TW, height=TH, uv_width=TW, uv_height=TH, particle=False,
                                render_mode='default', render_sides='auto', frame_time=1, frame_order_type='loop',
                                frame_order='', frame_interpolate=False, visible=True, internal=False,
                                saved=True, uuid=uid(), source=data)])
    return model


for name, (boxes, piv) in RIGS.items():
    label = {'furry': 'peludo', 'shaved': 'tosado'}[name]
    json.dump(bb_model(name, boxes, piv), open(os.path.join(OUT, f'Lucky_{label}.bbmodel'), 'w', encoding='utf-8'), indent=1)
print('wrote Lucky_peludo.bbmodel and Lucky_tosado.bbmodel in', OUT)
