# -*- coding: utf-8 -*-
"""四批工单终审：①每句"原文"逐字对照08277文本层 ②图源文件名对照磁盘 ③禁用数字/对抗词扫描"""
import pymupdf, re, os, json, glob

doc = pymupdf.open('01-PPT成品/08277.pdf')
def norm(s):
    return re.sub(r'[\s/　]', '', s)
pages = [norm(doc[i].get_text()) for i in range(len(doc))]
full = ''.join(pages)

DOCS = [
 ("02-方案与评审文档/08277_P1-P6全装备精修方案.md",  list(range(1,7))),
 ("02-方案与评审文档/08277_P7-P12全装备精修方案.md", list(range(7,13))),
 ("02-方案与评审文档/08277_P13-P18全装备精修方案.md", list(range(13,19))),
 ("02-方案与评审文档/08277_P19-P26全装备精修方案.md", list(range(19,27))),
]


# ---- v2: 交叠假阴性白名单（P6三卡：碎片全在版，整句因PDF阅读顺序交叠不连续） ----
FRAGMENT_WHITELIST = {
 ('08277_P1-P6全装备精修方案.md', 6): [
   ['摩擦界面剪切强度','降至','0.05M','以下'],
   ['构件结晶度','提升至','39.09%','以上'],
   ['宽温域内摩擦系数','稳定在','0.1'],
 ]
}

# ---- 1) 原文引用逐字核对 ----
miss_total = 0
for path, pagenos in DOCS:
    md = open(path).read()
    # 当前页码追踪
    cur = pagenos[0]
    quotes = []  # (page, quote, line_no)
    lines = md.split('\n')
    for i, ln in enumerate(lines):
        m = re.match(r'###\s*■\s*(?:第\s*)?P?(\d+)', ln)
        if m:
            p = int(m.group(1))
            if p in pagenos: cur = p
        # 表格行 | `原文` | `新` |
        tm = re.match(r'\|\s*`([^`]+)`\s*\|\s*`([^`]*)`', ln)
        if tm:
            quotes.append((cur, tm.group(1), i+1))
        # 第一批格式 【原文】xxx（截断到 ➔ / 【替换】 / 尾注）
        for om in re.finditer(r'【原文】(.+)', ln):
            q = re.split(r'➔|【替换】', om.group(1))[0].strip().strip('`').strip()
            q = re.sub(r'（{1,2}(?:🔴[^）]*）?)?$', '', q).strip()
            if len(q) >= 4:
                quotes.append((cur, q, i+1))
    miss = []
    for p, q, ln_no in quotes:
        n = norm(q)
        if len(n) < 3: continue
        if n in pages[p-1]: continue
        # 交叠白名单：碎片全部在版即判忠实
        wl = FRAGMENT_WHITELIST.get((os.path.basename(path), p), [])
        for frags in wl:
            if frags[0] in q and all(f in pages[p-1] for f in frags):
                continue
        # 全文档兜底匹配（可能页码标错）
        hit = [i+1 for i,pg in enumerate(pages) if n in pg]
        if any(frags[0] in q and all(x in pages[p-1] for x in frags) for frags in wl):
            continue
        miss.append((p, q, ln_no, hit[:3]))
    print(f"{os.path.basename(path)}: 引用{len(quotes)}条，未逐字命中 {len(miss)} 条")
    for p,q,l,hit in miss:
        print(f"   [P{p} L{l}] {q[:44]}  实际命中页:{hit if hit else '无'}")
    miss_total += len(miss)

# ---- 2) 图源文件名存在性 ----
have = set(os.path.basename(f) for f in glob.glob('03-素材库/毕业答辩素材/*'))
bad = []
for path,_ in DOCS:
    md = open(path).read()
    for fn in re.findall(r'P\d{2}_\d{2}_L[\d.]+T[\d.]+W[\d.]+H[\d.]+\.\w+', md):
        if fn not in have: bad.append((os.path.basename(path), fn))
print(f"\n图源文件名引用核验：素材库{len(have)}个文件，无效引用 {len(bad)} 条")
for p,fn in bad: print(f"   {p}: {fn}")

# ---- 3) 禁用数字/对抗词扫描（应只出现在禁用清单/返工说明的删除线上下文） ----
print("\n禁用内容扫描：")
for tok in ['防御','反杀','免检','话术','>420','±0.50','0.5%以下','99.5','超60%','>70%','350℃大关','简立方','面心八面体','开裂翘曲率','±0.5%','平均绝对偏差']:
    hits = []
    for path,_ in DOCS:
        for i, ln in enumerate(open(path).read().split('\n')):
            if tok in ln:
                ctx = ln.strip()[:60]
                ok = ('不是话术' in ln) or ('~~' in ln) or ('禁用' in ln) or ('返工' in ln) or ('清除' in ln) or ('v1' in ln) or ('纠偏' in ln) or ('张冠李戴' in ln) or ('停用' in ln) or ('订正' in ln) or ('P37' in ln) or ('48.00%' in ln)
                hits.append((os.path.basename(path), i+1, ctx, ok))
    bad2 = [h for h in hits if not h[3]]
    print(f"  {tok}: 命中{len(hits)}处，非豁免上下文 {len(bad2)} 处")
    for p,l,c,_ in bad2[:4]: print(f"     {p}:L{l} {c}")
print(f"\n=== 汇总：原文未命中 {miss_total} 条｜无效图源 {len(bad)} 条 ===")
