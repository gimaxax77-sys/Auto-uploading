# 1단계 시험 — 육안 검사용 밀착 인화지(장면 번호 표시, 한 장에 24컷). 사용: python sheets.py <화풍키>
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
style = sys.argv[1]
fs = sorted(glob.glob(os.path.join(HERE, "out", f"img_{style}", "*.png")))
W, H, C, R = 480, 270, 6, 4
font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 26)
for p in range(0, len(fs), C * R):
    sh = Image.new("RGB", (C * (W + 4), R * (H + 4)), "black")
    for k, f in enumerate(fs[p:p + C * R]):
        im = Image.open(f).convert("RGB").resize((W, H))
        ImageDraw.Draw(im).text((8, 4), os.path.basename(f)[:3], fill="yellow", font=font, stroke_width=3, stroke_fill="black")
        sh.paste(im, ((k % C) * (W + 4), (k // C) * (H + 4)))
    sh.save(os.path.join(HERE, "out", f"sheet_{style}_{p // (C * R) + 1:02d}.jpg"), quality=80)
print(style, len(fs))
