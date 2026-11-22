"""Generates ModelLucky.java (Minecraft 1.7.10) from Lucky.bbmodel.

Run again after editing the model in Blockbench:
    python tools/gen_model.py ../Lucky.bbmodel src/main/java/com/luckymod/client/ModelLucky.java

Blockbench (modded entity) -> Minecraft model space is a 180-degree turn
around Z: x -> -x, y -> 24 - y, z -> z. Angles: X and Y flip sign, Z stays.
"""
import json, math, re, sys

src, dst = sys.argv[1], sys.argv[2]
m = json.load(open(src, encoding='utf-8'))
tw, th = m['resolution']['width'], m['resolution']['height']
cubes = {e['uuid']: e for e in m['elements']}


def camel(name):
    parts = re.split(r'[^A-Za-z0-9]+', name)
    return parts[0].lower() + ''.join(p[:1].upper() + p[1:] for p in parts[1:])


def f(v):
    v = round(float(v), 4) + 0.0
    return f'{v}F'


def mc_point(o):
    return (-o[0], 24 - o[1], o[2])


fields, build, reset, roots = [], [], [], []


def walk(g, parent_abs, parent_field):
    name = camel(g['name'])
    if name in [x for x in fields]:
        name += '2'
    fields.append(name)
    p = mc_point(g['origin'])
    rel = [p[i] - parent_abs[i] for i in range(3)]
    rx, ry, rz = (math.radians(a) for a in g.get('rotation', [0, 0, 0]))
    build.append(f'        {name} = new ModelRenderer(this);')
    for ch in g['children']:
        if isinstance(ch, str):
            c = cubes[ch]
            size = [int(round(c['to'][i] - c['from'][i])) for i in range(3)]
            mn = (-c['to'][0], 24 - c['to'][1], c['from'][2])
            off = [mn[i] - p[i] for i in range(3)]
            u, v = c['uv_offset']
            build.append(f'        {name}.cubeList.add(new ModelBox({name}, {u}, {v}, '
                         f'{f(off[0])}, {f(off[1])}, {f(off[2])}, {size[0]}, {size[1]}, {size[2]}, 0.0F)); // {c["name"]}')
    reset.append(f'        pose({name}, {f(rel[0])}, {f(rel[1])}, {f(rel[2])}, {f(-rx)}, {f(-ry)}, {f(rz)});')
    for ch in g['children']:
        if not isinstance(ch, str):
            child = walk(ch, p, name)
            build.append(f'        {name}.addChild({child});')
    if parent_field is None:
        roots.append(name)
    return name


for g in m['outliner']:
    walk(g, (0, 0, 0), None)

GEN = '\n'.join([
    '    // ---- generated from Lucky.bbmodel by tools/gen_model.py: do not edit by hand ----',
    *[f'    public ModelRenderer {n};' for n in fields],
    '',
    '    private void buildParts() {',
    f'        textureWidth = {tw};',
    f'        textureHeight = {th};',
    *build,
    '    }',
    '',
    '    /** Puts every part back in the rest pose drawn in Blockbench. */',
    '    private void resetPose() {',
    *reset,
    '    }',
    '',
    '    private void renderRoots(float scale) {',
    *[f'        {r}.render(scale);' for r in roots],
    '    }',
    '    // ---- end generated ----',
])

text = open(dst, encoding='utf-8').read()
a = text.index('    // ---- generated')
b = text.index('    // ---- end generated ----') + len('    // ---- end generated ----')
open(dst, 'w', encoding='utf-8', newline='\n').write(text[:a] + GEN + text[b:])
print('generated', len(fields), 'parts,', len(cubes), 'cubes ->', dst)
