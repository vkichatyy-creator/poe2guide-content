# -*- coding: utf-8 -*-
# Финальная сборка: панорамы-острова (бесшовные внутри), сложенные по порядку маршрута.
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os, glob, datetime

SRC = r'C:\Users\asus\Pictures\Screenshots'
files = [f for f in glob.glob(os.path.join(SRC, '*.png'))
         if datetime.datetime.fromtimestamp(os.path.getmtime(f)) >= datetime.datetime(2026, 6, 11, 0, 50)]
files.sort(key=lambda f: os.path.getmtime(f))

imgs, masks, grays = [], [], []
for f in files:
    im = Image.open(f).convert('RGB')
    w, h = im.size
    im = im.crop((0, 0, w, h - 8))
    w, h = im.size
    d = ImageDraw.Draw(im)
    mask = Image.new('L', (w, h), 255)
    dm = ImageDraw.Draw(mask)
    def blot(box):
        d.rectangle(box, fill=(0, 0, 0)); dm.rectangle(box, fill=0)
    blot((int(w*0.37), 0, int(w*0.64), 135))
    blot((0, 95, 48, 265))
    arr = np.asarray(im.convert('L'), dtype=np.float32)
    if arr[int(h*0.86):, int(w*0.76):].mean() > 35:
        blot((int(w*0.72), int(h*0.80), w, h))
    if arr[35:215, int(w*0.18):int(w*0.52)].mean() > 45:
        blot((int(w*0.14), 25, int(w*0.56), 235))
    imgs.append(im); masks.append(mask)
    grays.append(np.asarray(im.convert('L'), dtype=np.float32))

Hm = min(g.shape[0] for g in grays); Wm = min(g.shape[1] for g in grays)

def phase(a, b):
    fa = np.fft.rfft2(a); fb = np.fft.rfft2(b)
    R = fa * np.conj(fb); R /= (np.abs(R) + 1e-6)
    c = np.fft.irfft2(R, s=a.shape)
    dy, dx = np.unravel_index(np.argmax(c), c.shape)
    dy = int(dy); dx = int(dx)
    if dy > a.shape[0] // 2: dy -= a.shape[0]
    if dx > a.shape[1] // 2: dx -= a.shape[1]
    return dy, dx

def mad(j, i, dy, dx):
    ga = grays[j][:Hm, :Wm]; gb = grays[i][:Hm, :Wm]
    ya0, ya1 = max(0, dy), min(Hm, Hm + dy)
    xa0, xa1 = max(0, dx), min(Wm, Wm + dx)
    if ya1 - ya0 < 120 or xa1 - xa0 < 120: return 1e9
    pa = ga[ya0:ya1, xa0:xa1]; pb = gb[ya0 - dy:ya1 - dy, xa0 - dx:xa1 - dx]
    m = (pa > 10) | (pb > 10)
    if m.sum() < 15000: return 1e9
    return float(np.abs(pa - pb)[m].mean())

islands = [
    ('СТАРТ — КОЛЕСО КЛАССА (КРУПНО)', [0], []),
    ('НИЖНЯЯ ЧАСТЬ МАРШРУТА', list(range(1, 11)),
     [(2,1),(3,2),(4,3),(5,4),(6,5),(7,6),(8,7),(9,8),(10,3)]),
    ('СЕРЕДИНА МАРШРУТА — 1', [11, 12], [(12,11)]),
    ('СЕРЕДИНА МАРШРУТА — 2', [13], []),
    ('ВЕРХНЯЯ ЧАСТЬ МАРШРУТА', list(range(14, 24)),
     [(15,14),(16,15),(17,16),(18,17),(19,16),(20,19),(21,15),(22,21),(23,22)]),
]

font = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 48)
panels = []
for title, members, links in islands:
    pos = {members[0]: (0, 0)}
    for i, j in links:
        a = grays[j][:Hm, :Wm]; b = grays[i][:Hm, :Wm]
        dy, dx = phase(a, b)
        if mad(j, i, dy, dx) > mad(j, i, -dy, -dx): dy, dx = -dy, -dx
        pos[i] = (pos[j][0] + dy, pos[j][1] + dx)
    ys = [pos[i][0] for i in members]; xs = [pos[i][1] for i in members]
    y0, x0 = min(ys), min(xs)
    H = max(pos[i][0] - y0 + imgs[i].height for i in members)
    W = max(pos[i][1] - x0 + imgs[i].width for i in members)
    cv = Image.new('RGB', (W, H), (5, 5, 7))
    for i in members:
        cv.paste(imgs[i], (pos[i][1] - x0, pos[i][0] - y0), masks[i])
    panels.append((title, cv))
    print(title, cv.size)

OUT_W = 3400
parts = []
for title, cv in panels:
    s = OUT_W / cv.width
    cv = cv.resize((OUT_W, int(cv.height * s)), Image.LANCZOS)
    bar = Image.new('RGB', (OUT_W, 110), (201, 162, 39))
    d = ImageDraw.Draw(bar)
    tw = d.textlength(title, font=font)
    d.text(((OUT_W - tw) / 2, 28), title, fill=(26, 26, 26), font=font)
    parts.append(bar); parts.append(cv)

H = sum(p.height for p in parts)
canvas = Image.new('RGB', (OUT_W, H), (5, 5, 7))
y = 0
for p in parts:
    canvas.paste(p, (0, y)); y += p.height
print('итог:', canvas.size)

# Ограничение размера под телефон
MAXSIDE = 6000
if max(canvas.size) > MAXSIDE:
    s = MAXSIDE / max(canvas.size)
    canvas = canvas.resize((int(canvas.width * s), int(canvas.height * s)), Image.LANCZOS)
    print('после ужатия:', canvas.size)

canvas.save('trees/arc-stormweaver.jpg', quality=87, optimize=True)
print('MB:', round(os.path.getsize('trees/arc-stormweaver.jpg') / 1024 / 1024, 2))
canvas.thumbnail((1300, 1300), Image.LANCZOS)
canvas.save('trees/_preview.png')
