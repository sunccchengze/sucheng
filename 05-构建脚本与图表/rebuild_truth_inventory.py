# -*- coding: utf-8 -*-
"""从三份PDF重建文字块+图片真值库：每页文字块坐标、嵌入图片(xref/md5/尺寸/落位bbox/最近图签)，跨文件哈希归并。"""
import pymupdf, hashlib, json, os

FILES = ["0823.pdf", "0827.pdf", "0827.1.pdf"]
inv = {}          # md5 -> {files, pages}
pagedump = {}     # (file,page) -> blocks

for f in FILES:
    doc = pymupdf.open(f)
    for pno in range(len(doc)):
        page = doc[pno]
        key = f"P{pno+1}"
        d = page.get_text("dict")
        texts = []
        for b in d["blocks"]:
            if b["type"] != 0: continue
            lines = ["".join(s["text"] for s in l["spans"]).strip() for l in b["lines"]]
            txt = " // ".join([x for x in lines if x])
            if txt:
                texts.append({"bbox": [round(v,1) for v in b["bbox"]], "t": txt})
        images = []
        seen_rects = {}
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                info = doc.extract_image(xref)
                md5 = hashlib.md5(info["image"]).hexdigest()[:10]
                w, h = info["width"], info["height"]
            except Exception:
                continue
            rects = page.get_image_rects(xref)
            if not rects: continue
            for r in rects:
                rb = [round(v,1) for v in (r.x0, r.y0, r.x1, r.y1)]
                # 面积太小的装饰性图片跳过
                if (rb[2]-rb[0]) * (rb[3]-rb[1]) < 4000: continue
                images.append({"bbox": rb, "md5": md5, "px": f"{w}x{h}"})
            inv.setdefault(md5, {"px": f"{w}x{h}", "where": []})
            if (f, key) not in inv[md5]["where"]:
                inv[md5]["where"].append((f, key))
        # 图片挂最近图签：同页内找bbox最近(中心距离)的文字块
        for im in images:
            cx, cy = (im["bbox"][0]+im["bbox"][2])/2, (im["bbox"][1]+im["bbox"][3])/2
            best = None; bestd = 1e9
            for t in texts:
                tx, ty = (t["bbox"][0]+t["bbox"][2])/2, (t["bbox"][1]+t["bbox"][3])/2
                dd = abs(tx-cx) + abs(ty-cy)*1.4   # 纵向加权，偏向上下图签
                if dd < bestd: bestd = dd; best = t
            im["near"] = best["t"][:60] if best else ""
            im["near_dist"] = round(bestd,1)
        pagedump[f"{f}|{key}"] = {"texts": texts, "images": images}
    doc.close()

json.dump({"inv": {k:v for k,v in inv.items()}, "pages": pagedump},
          open("03-素材库/truth_inventory.json","w"), ensure_ascii=False, indent=1)
print("images total md5:", len(inv))
for md5, v in sorted(inv.items(), key=lambda kv:-len(kv[1]["where"])):
    if len(v["where"]) >= 2:
        ws = "; ".join(f"{a}|{b}" for a,b in v["where"][:8])
        print(f"{md5} {v['px']:12s} x{len(v['where'])}  {ws}")
