---
name: page-image-text-audit
description: |
  页面图文一致性审计。输入渲染后的页面 PNG，做 OCR + 视觉解析，输出图文对照清单：
  每个文本块 ↔ 最近图像块的语义匹配度。自动标记：图文不符、同页近似重复图、
  AI 生成痕迹（手指/文字乱码/光影矛盾）、水印、竞品 logo/官方界面。
  用于 PPT 逐页改造时防止"改字不看图"的 A1/A2 级错误。
---

# 页面图文一致性审计

## 核心问题

PPT 改造中最常见的低级错误是**改了文字没看图**：
- 文案已经从"头骨修复"改成"装备 narratives"，但配图还是头骨 CT
- 页面混排 AI 生成图和真实产品照，观感割裂
- 竞品官方截图/Logo 残留在页面中

## 审计流程

### Step 1: 页面渲染

将目标 PPT/PDF 逐页导出为 PNG（建议 300dpi）：

```bash
# PDF 导出
python3 -c "
import fitz  # PyMuPDF
doc = fitz.open('08277.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=300)
    pix.save(f'page_{i+1:02d}.png')
"

# PPTX 导出（需要 LibreOffice）
libreoffice --headless --convert-to png output_dir/ 08277.pptx
```

### Step 2: OCR + 元素检测

对每页 PNG 做文本区域和图像区域分离：

```bash
python3 -c "
import easyocr
from PIL import Image

reader = easyocr.Reader(['ch_sim', 'en'])
img = Image.open('page_03.png')

# OCR 识别所有文本块及其位置
results = reader.readtext(str('page_03.png'))
for bbox, text, conf in results:
    x_min = min(p[0] for p in bbox)
    y_min = min(p[1] for p in bbox)
    x_max = max(p[0] for p in bbox)
    y_max = max(p[1] for p in bbox)
    print(f'[{x_min:.0f},{y_min:.0f},{x_max:.0f},{y_max:.0f}] conf={conf:.2f} text={text}')
"
```

### Step 3: 图文匹配清单

对每个文本块，找到最近的图像块（通过版面坐标距离），判断语义是否匹配：

| 文本块内容 | 最近图像 | 坐标距离 | 语义匹配 | 标记 |
|---|---|---|---|---|
| "大尺寸 PEEK 构件增材制造装备" | 头骨 CT 图 | 近 | ❌ 不符 | 🔴 图文不符 |
| "八区温控系统" | 触摸屏界面截图 | 近 | ⚠️ AI 生成? | 🟡 AI 痕迹 |
| "设备实物展示" | 黑色构件照片 | 近 | ✅ 匹配 | 🟢 通过 |

### Step 4: 自动标记项

#### 🔴 图文不符
- 文本提到的对象与图像内容主题不一致
- 检测方法：文本关键词 vs 图像视觉语义（通过多模态模型判断）

#### 🟡 AI 生成痕迹
常见 AI 图像特征：
- 手指数量异常（>5 或 <5）
- 文字/字母乱码（图中出现不可读的文字）
- 光影矛盾（同一物体不同部分光源方向不一致）
- 背景纹理过度平滑/重复
- 边缘模糊/伪影

#### 🟠 水印/竞品标识
- 检测页面中的 logo、水印文字
- 对比竞品品牌库：Victrex、君华、华曙、EOS、Stratasys

#### 🟣 同页重复图
- 检测同一页面内是否有近似重复的图像（IoU > 0.6）
- 标记为"疑似重复配图"

## 验收测试用例（08277.pdf）

以下问题应被自动抓出：

| 页码 | 预期检出 | 类型 |
|---|---|---|
| P3 | 头骨图与装备叙事不符 | 🔴 图文不符 |
| P3 右下 | "成形过程"弱图（低分辨率/信息量低） | 🟡 弱图标记 |
| P5 | AI 生成触摸屏图 | 🟡 AI 痕迹 |
| P5 | 竞品官方图混排风险 | 🟠 竞品标识 |

## 简化方案（无 OCR 依赖）

如果环境中没有 easyocr，可用**多模态 LLM 直接判断**：

```
逐页将 PNG 输入多模态模型，prompt：

"请审计这一页 PPT 的图文一致性：
1. 列出所有文本块和所有图像
2. 判断每个图像是否与最近的文本语义匹配
3. 检查图像是否有 AI 生成痕迹
4. 检查是否有水印、logo、竞品标识
5. 检查是否有同页重复图
输出 JSON 格式的审计报告。"
```

## 注意事项

- AI 生成检测不是 100% 准确，标记为"疑似"交由人工确认
- 水印/logo 检测建议使用模板匹配而非纯视觉判断
- 本技能的核心价值是**强制逐页检查**，防止"改字不看图"的系统性遗漏
