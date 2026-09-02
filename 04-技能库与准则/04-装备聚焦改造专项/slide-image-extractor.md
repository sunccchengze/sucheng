---
name: slide-image-extractor
description: |
  素材精确取图工具。从 pptx 按页码提取全部图片并按版面坐标命名导出；
  从 PDF 页面按区域高清裁剪导出 PNG；输出取图清单（页码+坐标+文件名+长宽比）。
  用于 PPT 改造时精确定位和导出素材，避免"毕业答辩 P14 那张设备照片"这种粗粒度描述。
---

# 素材精确取图工具

## 核心问题

配图建议停留在"毕业答辩 P14 那张设备照片"这种粗粒度描述，团队执行时还要自己找。
需要精确到：**页码 + 版面坐标 + 文件名 + 长宽比**，一次导出到位。

## 功能

### 1. 从 PPTX 按页提取全部图片

```python
#!/usr/bin/env python3
"""从 PPTX 按页提取所有图片，按版面坐标命名导出。"""

import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Emu
from PIL import Image
import io

def extract_pptx_images(pptx_path: str, output_dir: str):
    prs = Presentation(pptx_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    manifest = []
    
    for slide_idx, slide in enumerate(prs.slides, 1):
        img_idx = 0
        for shape in slide.shapes:
            if shape.shape_type == 13:  # Picture
                img_idx += 1
                image = shape.image
                ext = image.content_type.split("/")[-1]
                if ext == "jpeg":
                    ext = "jpg"
                
                # 版面坐标（EMU → cm）
                left_cm = shape.left / 914400 * 2.54
                top_cm = shape.top / 914400 * 2.54
                width_cm = shape.width / 914400 * 2.54
                height_cm = shape.height / 914400 * 2.54
                
                # 命名规则：P{页码}_{序号}_L{left}T{top}W{width}H{height}.{ext}
                fname = f"P{slide_idx:02d}_{img_idx:02d}_L{left_cm:.1f}T{top_cm:.1f}W{width_cm:.1f}H{height_cm:.1f}.{ext}"
                fpath = out / fname
                
                with open(fpath, "wb") as f:
                    f.write(image.blob)
                
                # 读取实际像素尺寸
                pil_img = Image.open(io.BytesIO(image.blob))
                px_w, px_h = pil_img.size
                
                manifest.append({
                    "page": slide_idx,
                    "index": img_idx,
                    "filename": fname,
                    "left_cm": round(left_cm, 1),
                    "top_cm": round(top_cm, 1),
                    "width_cm": round(width_cm, 1),
                    "height_cm": round(height_cm, 1),
                    "pixel_width": px_w,
                    "pixel_height": px_h,
                    "aspect_ratio": f"{px_w}:{px_h}",
                })
    
    # 输出清单
    manifest_path = out / "image_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"导出 {len(manifest)} 张图片到 {output_dir}/")
    print(f"清单: {manifest_path}")
    return manifest

if __name__ == "__main__":
    import sys
    extract_pptx_images(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "extracted_images")
```

**用法**：
```bash
python3 extract_pptx_images.py 毕业答辩.pptx extracted_images/
```

### 2. 从 PDF 按区域裁剪

```python
#!/usr/bin/env python3
"""从 PDF 按区域裁剪导出高清 PNG。"""

import fitz  # PyMuPDF
from pathlib import Path
import json

def extract_pdf_region(pdf_path: str, page_num: int, rect: tuple, output_path: str, dpi: int = 300):
    """
    rect: (x0, y0, x1, y1) 单位为 PDF 点（1点 = 1/72 英寸）
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # 0-indexed
    
    # 从 cm 转换为 PDF 点（1cm = 28.35点）
    pdf_rect = fitz.Rect(
        rect[0] * 28.35,
        rect[1] * 28.35,
        rect[2] * 28.35,
        rect[3] * 28.35,
    )
    
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(clip=pdf_rect, matrix=mat)
    pix.save(output_path)
    
    print(f"导出: {output_path} ({pix.width}x{pix.height}px @ {dpi}dpi)")
    return output_path

def batch_extract(pdf_path: str, extractions: list, output_dir: str):
    """
    extractions: [{"page": 14, "rect_cm": [x0,y0,x1,y1], "name": "设备照片"}, ...]
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    results = []
    for ext in extractions:
        fname = f"P{ext['page']:02d}_{ext['name']}.png"
        fpath = out / fname
        extract_pdf_region(pdf_path, ext["page"], ext["rect_cm"], str(fpath))
        results.append({
            "page": ext["page"],
            "rect_cm": ext["rect_cm"],
            "filename": fname,
            "description": ext.get("name", ""),
        })
    
    manifest_path = out / "extraction_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

if __name__ == "__main__":
    # 示例：提取用户点名的 8 张图块
    extractions = [
        {"page": 14, "rect_cm": [2, 3, 12, 10], "name": "设备照片"},    # 需实测坐标
        {"page": 38, "rect_cm": [1, 2, 10, 9], "name": "构件照片"},    # 需实测坐标
        {"page": 42, "rect_cm": [3, 4, 11, 11], "name": "数据图"},     # 需实测坐标
        # ... 用户根据实际需要填写
    ]
    batch_extract("08277.pdf", extractions, "extracted_regions/")
```

### 3. 取图清单格式

输出 JSON 清单：

```json
[
  {
    "page": 14,
    "source": "毕业答辩.pptx",
    "filename": "P14_01_L2.5T3.0W9.5H7.2.jpg",
    "left_cm": 2.5,
    "top_cm": 3.0,
    "width_cm": 9.5,
    "height_cm": 7.2,
    "pixel_width": 1200,
    "pixel_height": 907,
    "aspect_ratio": "1200:907",
    "description": "设备实物照片"
  }
]
```

## 依赖安装

```bash
pip install python-pptx PyMuPDF Pillow
```

## 使用流程

1. **列出所有图片**：运行 PPTX 提取脚本，得到 `image_manifest.json`
2. **确认目标图片**：从清单中挑选需要的图片（按页码和坐标定位）
3. **精确裁剪**：对 PDF 用区域裁剪脚本，输入页码和坐标（cm）
4. **导出清单**：JSON 清单包含页码+坐标+文件名+尺寸，团队可直接执行

## 注意事项

- PPTX 中的图片可能是嵌入的原始文件，分辨率可能高于页面渲染分辨率
- PDF 裁剪的 DPI 默认 300，可根据需要调整
- 坐标单位统一为 **cm**（从页面左上角开始）
- "坐标误差肉眼不可见"的验收标准：在 300dpi 下，1px ≈ 0.008cm，远小于肉眼分辨力
