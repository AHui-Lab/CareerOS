# -*- coding: utf-8 -*-
"""ATS 兼容性体检脚本：模拟求职者跟踪系统(ATS)解析 PDF 简历的方式做全面检查"""
import json, os, re, sys
import fitz  # PyMuPDF

PDF = r"C:\CareerOS\docs\曹宇辉_简历.pdf"
OUT = r"C:\CareerOS\docs\ats-check"
os.makedirs(OUT, exist_ok=True)

doc = fitz.open(PDF)
report = {}

# ---------- 1. 基本元数据 ----------
meta = doc.metadata or {}
report["pdf_version"] = f"1.{doc.metadata.get('format','')}" if False else None
# PyMuPDF: doc.metadata has 'format' like 'PDF 1.7'
report["metadata"] = {k: meta.get(k) for k in ("title","author","producer","creator","creationDate","modDate","format","encryption")}
report["encrypted"] = doc.is_encrypted
report["page_count"] = doc.page_count
report["toc_entries"] = doc.get_toc()

pages_info = []
full_text_parts = []

for pno in range(doc.page_count):
    page = doc[pno]
    pinfo = {"page": pno + 1, "rect": list(page.rect[2:])}  # width,height

    # ---- 文本提取（ATS 最核心能力）----
    txt = page.get_text("text")
    full_text_parts.append(txt)
    pinfo["char_count"] = len(txt.replace("\n","").replace(" ",""))

    # 检查提取文本是否含乱码/替换字符
    bad = sum(1 for ch in txt if ch in "\ufffd\ue000")
    pinfo["replacement_chars"] = bad

    # CJK 与拉丁字符统计
    cjk = sum(1 for ch in txt if '\u4e00' <= ch <= '\u9fff')
    lat = sum(1 for ch in txt if ch.isascii() and ch.isalpha())
    pinfo["cjk_chars"] = cjk
    pinfo["latin_chars"] = lat

    # ---- 字体 ----
    fonts = []
    for f in page.get_fonts(full=True):
        xref, ext, ftype, name, refname, enc = f[:6]
        fonts.append({"name": name, "type": ftype, "encoding": enc})
    pinfo["fonts"] = fonts

    # ---- 图片 ----
    imgs = page.get_images(full=True)
    pinfo["image_count"] = len(imgs)
    img_details = []
    for im in imgs:
        xref = im[0]
        try:
            pix = fitz.Pixmap(doc, xref)
            img_details.append({"w": pix.width, "h": pix.height, "alpha": pix.alpha, "colorspace": pix.colorspace.name if pix.colorspace else None})
            pix = None
        except Exception as e:
            img_details.append({"error": str(e)})
    pinfo["images"] = img_details

    # ---- 版式分析：文本块布局（检测分栏/文本框）----
    blocks = [b for b in page.get_text("blocks") if b[6] == 0]  # 只看文本块
    pinfo["text_block_count"] = len(blocks)
    # 判断多栏：同一垂直区间内是否有多个水平错开的块
    col_like = 0
    for i, a in enumerate(blocks):
        for j, b in enumerate(blocks):
            if i >= j: continue
            ay0, ay1 = a[1], a[3]; by0, by1 = b[1], b[3]
            ax0, ax1 = a[0], a[2]; bx0, bx1 = b[0], b[2]
            v_overlap = min(ay1, by1) - max(ay0, by0)
            h_overlap = min(ax1, bx1) - max(ax0, bx0)
            if v_overlap > 8 and h_overlap <= 2:  # 垂直重叠但水平不重叠 => 并排
                col_like += 1
    pinfo["side_by_side_block_pairs"] = col_like

    # 旋转文本
    rotates = set()
    d = page.get_text("dict")
    for blk in d["blocks"]:
        if blk["type"] != 0: continue
        for line in blk["lines"]:
            rotates.add(round(line["dir"][1], 2))
    pinfo["text_directions"] = sorted(rotates)

    # 矢量绘图（下划线/分隔线/表格线/图形）
    try:
        drawings = page.get_drawings()
    except Exception:
        drawings = []
    pinfo["vector_drawing_count"] = len(drawings)

    # 链接
    links = page.get_links()
    pinfo["link_count"] = len(links)
    pinfo["links"] = [{"uri": l.get("uri")} for l in links if l.get("uri")]

    # 渲染页面图片供目视检查
    pix = page.get_pixmap(dpi=110)
    png = os.path.join(OUT, f"page{pno+1}.png")
    pix.save(png)

    pages_info.append(pinfo)

report["pages"] = pages_info

# ---------- 2. ATS 纯文本顺序提取 ----------
ats_text = "\n".join(doc[p].get_text("text", sort=True) for p in range(doc.page_count))  # ATS 常见做法：按位置排序读取
with open(os.path.join(OUT, "extracted_ats_order.txt"), "w", encoding="utf-8") as f:
    f.write(ats_text)

# 原始顺序（另一类 ATS 直接按内容流读）
raw_text = "\n".join(full_text_parts)
with open(os.path.join(OUT, "extracted_raw_order.txt"), "w", encoding="utf-8") as f:
    f.write(raw_text)

# ---------- 3. 关键信息命中检测（ATS 解析姓名/联系方式/板块的方式） ----------
all_text = ats_text
checks = {
    "电话(tel regex)": bool(re.search(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)|\d{3,4}-\d{7,8}", all_text)),
    "邮箱(email regex)": bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", all_text)),
    "常见板块词": {kw: (kw in all_text) for kw in ["教育", "工作", "实习", "项目", "技能", "经历", "校园", "获奖", "证书", "自我"]},
}
report["parse_checks"] = checks

with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("=== 体检原始数据完成 ===")
print(json.dumps(report, ensure_ascii=False, indent=1)[:4000])
print("\n渲染页数:", doc.page_count)
