"""Writes an OptiFine/MCPatcher custom lightmap that reproduces Minecraft Beta 1.7.3 lighting:
grey (no warm torch tint), no torch flicker, Beta's brightness curve and its darker nights.

Lightmap layout (16 px per light level): rows 0-15 = sky light by level, columns = sun brightness
(left night, right noon); rows 16-31 = block light by level, columns = flicker (kept flat);
rows 32-63 = the same with night vision. The game adds the sky and block colours.

usage: python tools/gen_beta_lightmap.py <resource_pack_dir>
"""
import os, sys
from PIL import Image

out = sys.argv[1]


def beta_table(ambient):
    # WorldProvider.generateLightBrightnessTable() from Beta 1.7.3 (overworld 0.05, nether 0.1)
    t = []
    for i in range(16):
        f1 = 1.0 - i / 15.0
        t.append((1.0 - f1) / (f1 * 3.0 + 1.0) * (1.0 - ambient) + ambient)
    return t


def lightmap(ambient, has_sky, cols=32):
    t = beta_table(ambient)
    img = Image.new('RGB', (cols, 64))
    for nv in (0, 1):
        for x in range(cols):
            sun = x / (cols - 1)
            # Beta darkens sky light by up to 11 levels at night (skylightSubtracted)
            sub = round((1.0 - sun) * 11) if has_sky else 15
            for lvl in range(16):
                sky = t[max(lvl - sub, 0)] if has_sky else t[0]
                if nv: sky = min(1.0, sky * 1.6 + 0.25)
                v = int(round(min(1.0, sky) * 255))
                img.putpixel((x, nv * 32 + lvl), (v, v, v))
                # block light: Beta's curve minus the ambient already counted in the sky row
                blk = max(0.0, t[lvl] - t[0])
                if nv: blk = min(1.0, blk * 1.3)
                b = int(round(blk * 255))
                img.putpixel((x, nv * 32 + 16 + lvl), (b, b, b))
    return img


d = os.path.join(out, 'assets/minecraft/mcpatcher/lightmap')
os.makedirs(d, exist_ok=True)
lightmap(0.05, True).save(os.path.join(d, 'world0.png'))
lightmap(0.10, False).save(os.path.join(d, 'world-1.png'))
open(os.path.join(out, 'pack.mcmeta'), 'w').write(
    '{\n  "pack": {\n    "pack_format": 1,\n    "description": "Beta 1.7.3 lighting (needs OptiFine Custom Colors)"\n  }\n}\n')
print('wrote', d)
