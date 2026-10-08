# -*- coding: utf-8 -*-
"""版式还原分析：块位置/图片位置/矢量线条/字号/颜色，用于替代目视检查"""
import json, os
import fitz

PDF = r"C:\CareerOS\docs\曹宇辉_简历.pdf"
OUT = r"C:\CareerOS\docs\ats-check"
doc = fitz.open(PDF)
page = doc[0]
W, H = page.rect.width, page.rect.height
print(f"页面尺寸: {W:.0f} x {H:.0f} pt (A4=595x842)")

# ---- 文本块位置 ----
print("\n=== 文本块布局 (x0,y0 -> x1,y1 | 字号 | 前40字) ===")
blocks = sorted([b for b in page.get_text("blocks") if b[6] == 0], key=lambda b: (round(b[1]), b[0]))
for b in blocks:
    x0, y0, x1, y1, text, *_ = b
    t = text.replace("\n", "⏎")[:40]
    print(f"({x0:5.0f},{y0:5.0f})-({x1:5.0f},{y1:5.0f}) {t}")

# ---- span 级字号与颜色 ----
print("\n=== span 字号分布 ===")
sizes = {}
white_text = []
d = page.get_text("dict")
for blk in d["blocks"]:
    if blk["type"] != 0: continue
    for line in blk["lines"]:
        for sp in line["spans"]:
            s = round(sp["size"], 1)
            sizes[s] = sizes.get(s, 0) + len(sp["text"])
            c = sp["color"]
            r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
            if r > 240 and g > 240 and b > 240:
                white_text.append(sp["text"][:20])
for s in sorted(sizes):
    print(f"  {s}pt: {sizes[s]} 字符")
print("白色/近白文字:", white_text if white_text else "无")

# ---- 图片位置 ----
print("\n=== 图片位置 ===")
for im in page.get_images(full=True):
    xref = im[0]
    rects = page.get_image_rects(xref)
    for r in rects:
        print(f"  图片 {im[2]}x{im[3]}px 放置于 ({r.x0:.0f},{r.y0:.0f})-({r.x1:.0f},{r.y1:.0f})  宽{r.width:.0f}x高{r.height:.0f}pt  占页面宽 {r.width/W*100:.0f}%")

# ---- 矢量图形 ----
print("\n=== 矢量图形（分隔线/边框/图形）===")
for dr in page.get_drawings():
    r = dr["rect"]
    kind = "线条" if (r.height < 2.5 or r.width < 2.5) else "形状/框"
    fill = dr.get("fill"); stroke = dr.get("color")
    print(f"  {kind} ({r.x0:.0f},{r.y0:.0f})-({r.x1:.0f},{r.y1:.0f}) w{r.width:.0f} h{r.height:.0f} fill={fill} stroke={stroke}")

# ---- 页边距估算 ----
xs = [b[0] for b in blocks]; xe = [b[2] for b in blocks]
ys = [b[1] for b in blocks]; ye = [b[3] for b in blocks]
print(f"\n文本范围: 左{min(xs):.0f} 右{W-max(xe):.0f} 上{min(ys):.0f} 下{H-max(ye):.0f} pt 边距")

# ---- 与图片重叠的文字块（检测文字压在图片上 => 可能解析混乱）----
img_rects = []
for im in page.get_images(full=True):
    for r in page.get_image_rects(im[0]):
        img_rects.append(r)
for b in blocks:
    br = fitz.Rect(b[:4])
    for ir in img_rects:
        inter = br & ir
        if not inter.is_empty and inter.get_area() > 0.3 * br.get_area():
            print(f"  ⚠ 文字块压在图片上: {b[4][:30]!r}")
