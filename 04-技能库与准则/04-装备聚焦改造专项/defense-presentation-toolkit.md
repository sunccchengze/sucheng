---
name: defense-presentation-toolkit
description: |
  国创赛答辩路演 PPT 改造工具箱。整合已有技能覆盖 ⑤图表风格系统 ⑥导出前质检
  ⑦答辩证据映射 ⑧逐页叙事节奏审查四项需求。路由到最匹配的已有技能组合。
---

# 国创赛答辩路演 PPT 改造工具箱

## 需求 → 已有技能映射

### ⑤ 图表风格系统

**已有技能覆盖度：✅ 高**

| 角色 | 技能 | 路径 | 干什么 |
|---|---|---|---|
| 🎯 主技能 | **matplotlib** | `skills/community/scientific-agent-skills/skills/matplotlib/SKILL.md` | 全自定义图表：颜色、字体、布局、中文字体粗体方案 |
| 🎯 主技能 | **scientific-visualization** | `skills/community/scientific-agent-skills/skills/scientific-visualization/SKILL.md` | 出版级科研图表，含 Matplotlib + Seaborn + Plotly |
| 🔧 支撑 | **seaborn** | `skills/community/scientific-agent-skills/skills/seaborn/SKILL.md` | 统计图表快速生成 |
| 🔧 支撑 | **design (UI tokens)** | `skills/community/ui-ux-pro-max/cli/assets/skills/design/SKILL.md` | 设计令牌（design tokens）系统：颜色/字体/间距规范 |

**补充说明**：
- 用 `matplotlib` 技能定制与 deck 设计令牌对齐的图表模板
- 设计令牌：深蓝 `#0A1833` / 青 `#4FC3F7` / 金 `#F2C44C`
- 中文字体粗体问题：matplotlib 默认中文字体缺 Bold 权重，需在 rcParams 中指定 `fontweight` 或使用 `SimHei` + 手动 fallback
- 模板代码示例：

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

DECK_COLORS = {
    'bg': '#0A1833',
    'accent': '#4FC3F7',
    'highlight': '#F2C44C',
    'text': '#FFFFFF',
    'grid': '#1A2D4D',
}

def deck_style(ax, title, xlabel='', ylabel=''):
    ax.set_facecolor(DECK_COLORS['bg'])
    ax.figure.set_facecolor(DECK_COLORS['bg'])
    ax.set_title(title, color=DECK_COLORS['text'], fontsize=16, fontweight='bold', pad=12)
    ax.set_xlabel(xlabel, color=DECK_COLORS['text'], fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, color=DECK_COLORS['text'], fontsize=12, fontweight='bold')
    ax.tick_params(colors=DECK_COLORS['text'])
    ax.grid(color=DECK_COLORS['grid'], alpha=0.3)
    for spine in ax.spines.values():
        spine.set_color(DECK_COLORS['grid'])
```

### ⑥ 导出前质检

**已有技能覆盖度：⚠️ 中（需组合）**

| 角色 | 技能 | 路径 | 干什么 |
|---|---|---|---|
| 🎯 主技能 | **stop-slop** | `skills/core/stop-slop/SKILL.md` | 去 AI 模板腔/口语化残留 |
| 🎯 主技能 | **document-quality-check** | `full-sources/official/openai-plugins/plugins/datasite/skills/document-quality-check/SKILL.md` | 文档质量审计 |
| 🔧 支撑 | **paper-self-review** | `skills/community/claude-scholar/skills/paper-self-review/SKILL.md` | 结构化自查清单 |

**补充说明**：
- 现有技能不直接覆盖"PDF 文本层与画面双层残留比对"和"占位符扫描"
- 建议写一个轻量 Python 脚本做黑名单扫描：

```python
BLACKLIST = [
    "放点啥呢", "写点啥好呢", "TODO", "FIXME", "placeholder",
    "国际领先", "全球唯一",  # 无限定最高级
    "开创了", "颠覆了",  # 无证据的极端表述
]

def scan_text(text, page_num):
    issues = []
    for term in BLACKLIST:
        if term in text:
            issues.append(f"P{page_num}: 发现黑名单词「{term}」")
    return issues
```

### ⑦ 答辩证据映射

**已有技能覆盖度：⚠️ 中**

| 角色 | 技能 | 路径 | 干什么 |
|---|---|---|---|
| 🎯 主技能 | **rebuttal** | `full-sources/research/aris/skills/rebuttal/SKILL.md` | 学术 rebuttal 结构化回应 |
| 🔧 支撑 | **research-expert-system** | `skills/core/research-expert-system/SKILL.md` | 科研路由器，可路由到文献/证据子技能 |
| 🔧 支撑 | **guiguzi** | `skills/community/guiguzi/SKILL.md` | 纵横术谈判/答辩话术 |

**补充说明**：
- 建议手动构建**三联表**（规则维度→页面证据→答辩话术）：

```markdown
| 评审规则维度 | 对应页面 | 核心证据 | 刁钻问题 | 30秒话术 |
|---|---|---|---|---|
| 技术创新性 | P7-P9 | 八区温控+RL闭环 | "华曙也是八区，你们强在哪？" | "开环分区 vs 多模态测温+RL 闭环，温度均匀性提升 40%" |
| 竞品对比 | P12 | 性能对标表 | "数据怎么测的？" | "按 ASTM D638 标准，第三方检测机构 SGS 报告编号 XXX" |
```

### ⑧ 逐页叙事节奏审查

**已有技能覆盖度：✅ 高**

| 角色 | 技能 | 路径 | 干什么 |
|---|---|---|---|
| 🎯 主技能 | **analyze-pitch-deck** | `skills/community/buildwithclaude-hub/plugins/venture-capital-intelligence/skills/analyze-pitch-deck/SKILL.md` | Pitch Deck 全面分析：叙事、节奏、信息密度 |
| 🔧 支撑 | **victor-design-system** | `skills/community/victor-design/SKILL.md` | 版式美学和视觉节奏 |

**补充说明**：
- `analyze-pitch-deck` 已有完整的路演节奏分析框架
- 按 26 页路演时间轴分三段：
  - 黄金 90 秒（P1-P5）：问题定义→团队亮点→核心差异化
  - 中段（P6-P20）：技术细节→证据→竞品→商业模式
  - 收口（P21-P26）：财务→团队→融资需求→Call to Action
- 每段末尾必须有"钩子"把观众带入下一段

## 完整技能组总览

```
🎯 主技能组（必用）：
  • engineering-terminology-gate — ② 术语守门
  • page-image-text-audit        — ③ 图文一致性
  • slide-image-extractor        — ④ 精确取图
  • matplotlib + scientific-visualization — ⑤ 图表风格
  • stop-slop + document-quality-check    — ⑥ 导出质检
  • rebuttal + 手动三联表                 — ⑦ 答辩证据
  • analyze-pitch-deck                    — ⑧ 叙事节奏

🔧 支撑技能（选用）：
  • guizang-ppt-skill    — PPT 版式生成
  • agent-reach          — 情报检索
  • human-writing        — 文案写作
  • humanizer-zh         — 去 AI 味
  • victor-design-system — 视觉设计
  • guiguzi              — 答辩话术
```
