# knowledge-reviews · 知识综述生成器

> 一个**可复现、零幻觉、必溯源**的企业知识综述生成方案。
> 基于腾讯云知（乐享）知识库的语义检索，把"一次真实检索"渲染成一页**单文件、全资源内联、暗色科技感**的 HTML 综述报告。

[English version →](./README_EN.md)

---

## 一、这是做什么的

很多团队的"知识库"检索结果，最后只停留在聊天窗口里，既不可追溯、也无法沉淀成可分享的文档。

`knowledge-reviews` 解决一件事：**把一次真实的知识库检索，变成一份带源角标、可点击溯源、可离线打开的综述报告**，并且——同一份输入永远渲染出同一份输出（可复现）。

核心理念（详见 [`docs/architecture.md`](./docs/architecture.md)）：

1. **零幻觉**：报告里的每一个数字、标题、链接，都必须来自真实检索返回，绝不编造。
2. **必溯源**：每个论点都带 `[n]` 角标，对应底部"来源引用列表"里的标题 + 链接 + 关键词标签。
3. **可复现**：数据（`spec.json`）、内容（`body.html` / `conclusion.html`）与渲染（`src/review_generator.py`）三层分离。
4. **透明检索**：报告自带"检索过程可视化"——列出每次 `search_kb_search` 的 `total` 命中数与 `took_ms` 耗时。

---

## 二、目录结构（项目存放规范）

```
knowledge-reviews/
├─ README.md              # 中文主文档（本文件）
├─ README_EN.md           # 英文文档
├─ LICENSE                # MIT
├─ .gitignore
├─ docs/
│  ├─ conventions.md      # 项目存放规范（如何新增一篇综述）
│  └─ architecture.md     # 第一性原理方案 / 设计思路
├─ src/
│  └─ review_generator.py # 可复现的生成器（纯标准库，无外部依赖）
└─ samples/               # 示例：数据 + 内容 + 产物
   ├─ spec.json           # 真实检索数据（query 统计 / 来源引用）
   ├─ body.html           # 综述正文（带 [n] 角标）
   ├─ conclusion.html     # 结论 + 数据真实性说明
   └─ 企业知识问答系统_知识综述.html  # 由上面三者生成的示例报告
```

> 仓库根目录还保留了 `企业知识问答系统_知识综述.html` 的副本，方便访客直接打开；规范产物请以 `samples/` 为准。

---

## 三、如何复现示例报告

无需安装任何第三方库，只要本地有 Python 3：

```bash
cd knowledge-reviews
python3 src/review_generator.py
# 等价于：
python3 src/review_generator.py \
  --spec   samples/spec.json \
  --body   samples/body.html \
  --conclusion samples/conclusion.html \
  --out    samples/企业知识问答系统_知识综述.html
```

输出为单文件 HTML（CSS 内联，无外部字体 / 脚本 / 图片），可直接双击离线打开。

---

## 四、示例数据从哪来（真实性声明）

`samples/` 下这份示例，全部内容来自 **腾讯云知（乐享）知识库** 在 **2026-08-06** 的真实检索：

| Query | 命中数 `total` | 耗时 `took_ms` |
|-------|--------------:|---------------:|
| Q1 · 企业知识问答 **RAG** 检索增强生成 | 7 | 96 ms |
| Q2 · 企业知识问答 **Prompt** 工程 | 7 | 46 ms |
| Q3 · 企业知识问答 **Agent** 智能体 | 7 | 84 ms |

- 三次检索累计 21 次命中，去重后 **7 个唯一文档**（5 个含正文的内容页 + 2 个无正文的知识库容器）。
- 综述仅引用 5 个含正文的页面，2 个容器不计入论点来源。
- **诚实标注**：以"Prompt 工程"为关键词的检索与另两个方向完全重叠，知识库内并无专门论述该方法的页面——这是内容缺口，已如实标注，未做任何引申。

---

## 五、如何新增一篇综述

完整流程见 [`docs/conventions.md`](./docs/conventions.md)。简述：

1. 在你的腾讯云知（乐享）知识库里，用 `search_kb_search` 检索目标主题，记录每个 query 的 `total` / `took_ms`。
2. 用 `entry_describe_ai_parse_content` 解析命中页面，提取 snippet 要点。
3. 按 `samples/spec.json` 的格式填写 `meta` / `queries` / `aggregation` / `references`。
4. 把综述正文写入 `body.html`（论点用 `[n]` 角标对应 `references` 序号），结论写入 `conclusion.html`。
5. 运行生成器产出 HTML，核对角标与链接后再分享。

**红线**：任何无法对应到真实检索结果的内容，不得写入报告；存在的内容缺口应像示例那样显式标注，而非回避或编造。

---

## 六、下一步（Roadmap）

- [ ] 接入乐享 MCP 连接器，把"检索 → 填 spec → 生成"做成一键脚本
- [ ] 支持多知识库交叉检索与去重聚合
- [ ] 增加导出 Markdown / PDF 两种离线格式
- [ ] 为 `spec.json` 增加 JSON Schema 校验

---

## 语料充足度审计（本项目的差异化能力）

scholar-rag、automated-slr-generator 这类工具都默认"语料已经够好"，拿到就直接生成综述。它们漏掉了一个更前置的问题：**这套知识库配不配被用来做可靠的知识问答？** 本项目补上这一环。

`src/corpus_audit.py` 接收若干条真实检索（每条带命中文档 id 与空容器 id），算出四个硬指标并直接下结论：

- **唯一文档数**：去重后的真实文档总量。
- **跨查询重叠率**：不同意图的检索是否返回同一批文档（越高越同质）。
- **内容页占比**：去掉空的知识库 / 文件夹容器后，真正有正文的比例。
- **结论**：充足 / 临界 / 不足，附带一句话理由（带数字）。

为什么这比"再写一份漂亮的综述"更有用？因为 RAG 的回答质量天花板就是语料质量。语料只有几篇、还全是演示内容，RAG 再怎么"降幻觉"也救不回来——审计会直接把这事戳破，而不是粉饰。在报告里，审计卡紧跟"检索过程可视化"出现，用红 / 黄 / 绿徽章给出结论。

> 质量标准：本项目的叙述与代码同时采用 [deaify](https://github.com/Edgarzwj/deaify) 的两把尺子——`humanize-prose`（去 AI 味、有观点、有数字、不重写开头当结尾）与 `code-no-slop`（YAGNI、最短可用 diff、不造假模块）。

---

## 七、许可证

[MIT](./LICENSE) © 2026 Edgarzwj
