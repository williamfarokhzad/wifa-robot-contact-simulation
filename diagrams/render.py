"""Regenerate the two editable SVGs from the checked-in scenarios."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from contact import compare


def write(name, markup):
    (HERE / f'{name}.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="510" viewBox="0 0 900 510">'
        '<rect width="900" height="510" rx="20" fill="#f1f7f8"/>'
        '<g font-family="DejaVu Sans, sans-serif" fill="#19334a">' + markup + '</g></svg>\n',
        encoding='utf-8')


def label(x, y, s, size=26, bold=False, anchor='start'):
    weight = ' font-weight="700"' if bold else ''
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}"{weight}>{s}</text>'


def load(name):
    c = json.loads((HERE.parent / 'examples' / f'{name}.json').read_text())
    return c, compare(**c)


coarse, (event, sampled) = load('coarse')
x = lambda t: 115 + t * 3200
y = lambda h: 360 - h * 1230
times = [i / 2000 for i in range(411)]
flight = ' '.join(f'{x(t):.2f},{y(coarse["clearance_m"] - .5 * coarse["gravity_m_s2"] * t*t):.2f}' for t in times)
chart = label(42, 55, 'One crossing, two detection times', 38, True)
chart += label(45, 94, 'Coarse case: a floor check every 50 ms', 27)
chart += '<path d="M115 116V413M115 413H810" fill="none" stroke="#58778c" stroke-width="2"/>'
chart += '<path d="M115 360H810" stroke="#58778c" stroke-width="2" stroke-dasharray="7 5"/>'
chart += label(43, 368, 'floor', 23)
chart += f'<polyline points="{flight}" fill="none" stroke="#006b72" stroke-width="6"/>'
for ms in (0, 50, 100, 150, 200):
    tx = x(ms / 1000)
    ty = y(.18 - 5 * (ms / 1000) ** 2)
    chart += f'<circle cx="{tx}" cy="{ty}" r="7" fill="#aa420d"/>'
    chart += label(tx, 449, str(ms), 22, anchor='middle')
chart += f'<circle cx="{x(event.time_s)}" cy="360" r="9" fill="#006b72" stroke="#fff" stroke-width="2"/>'
chart += label(580, 200, f'Crossing: {event.time_s*1000:.2f} ms', 24)
chart += f'<path d="M750 210L{ x(event.time_s)-5 :.1f} 348" fill="none" stroke="#526b7e" stroke-width="2"/>'
chart += label(455, 390, f'200 ms: {sampled.clearance_before_clamp_m*1000:.0f} mm gap', 24)
chart += label(449, 487, 'Time after release (ms)', 24, anchor='middle')
write('contact-crossing', chart)

_, (_, fine) = load('fine')
chart = label(42, 55, 'What a late impact changes', 38, True)
chart += label(45, 94, 'Same release and restitution in all three cases', 26)
chart += label(45, 157, 'Method', 26, True)
chart += label(436, 157, 'Below floor', 26, True, 'middle')
chart += label(708, 157, 'Rebound apex', 26, True, 'middle')
for i, (name, value) in enumerate((('Exact event', event), ('50 ms check', sampled), ('2 ms check', fine))):
    top = 182 + 81*i
    chart += f'<rect x="39" y="{top}" width="822" height="68" rx="12" fill="{["#dfefef","#f9e9db","#e2eef4"][i]}"/>'
    chart += label(60, top+44, name, 27, True)
    depth_mm = abs(value.clearance_before_clamp_m * 1000)
    chart += label(436, top+44, f'{depth_mm:.1f} mm', 27, anchor='middle')
    chart += label(708, top+44, f'{value.rebound_height_m*1000:.3f} mm', 27, anchor='middle')
chart += label(45, 477, 'Depth is a numerical artifact, not material deformation.', 24)
write('contact-step-comparison', chart)
