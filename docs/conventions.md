# 项目存放规范（Conventions）

本文件定义 `knowledge-reviews` 的目录、命名、提交与数据完整性约定。新增一篇综述前请先读完。

---

## 1. 目录与文件职责

| 路径 | 职责 | 是否入库 |
|------|------|----------|
| `README.md` / `README_EN.md` | 中英主文档 | ✅ |
| `LICENSE` | MIT 许可证 | ✅ |
| `.gitignore` | 忽略产物/密钥/临时文件 | ✅ |
| `docs/conventions.md` | 本规范 | ✅ |
| `docs/architecture.md` | 设计思路 / 第一性原理 | ✅ |
| `src/review_generator.py` | 生成器（纯标准库） | ✅ |
| `samples/spec.json` | 真实检索数据（纯数据） | ✅ |
| `samples/body.html` | 综述正文（带 `[n]` 角标） | ✅ |
| `samples/conclusion.html` | 结论 + 真实性说明 | ✅ |
| `samples/*.html`（生成物） | 由上面三者生成的报告 | ✅ |
| 仓库根 `*.html` | 示例报告副本（方便访客） | ✅ |
| `tmp/` `*.tmp` `scratch/` | 本地草稿 | ❌（已忽略） |
| `tokens.json` `*.pem` `*.key` `credentials.*` `.env` | 任何密钥/令牌 | ❌（已忽略，绝不可提交） |

---

## 2. 命名约定

- **报告文件名**：`{主题}_知识综述.html`，主题用中文或英文短词，避免空格与特殊字符。
- **spec 数据**：固定 `samples/spec.json`；若一篇综述需要独立数据，建 `samples/{主题}/` 子目录，内部仍用 `spec.json` / `body.html` / `conclusion.html` 三件套。
- **分支**：默认 `main` 为主线；新综述可开 `review/{主题}` 分支，PR 合并进 `main`。

---

## 3. 新增一篇综述的标准流程

1. **检索**：在腾讯云知（乐享）用 `search_kb_search` 检索，每个 query 记录 `total` 与 `took_ms`。建议按 3 个方向拆关键词（如 RAG / Prompt / Agent）。
2. **解析**：对命中页面调 `entry_describe_ai_parse_content`，从 snippet / 全文提取要点。
3. **填数据**：复制 `samples/spec.json`，填 `meta` / `queries` / `aggregation` / `references`。`references` 顺序即正文 `[n]` 序号。
4. **写内容**：
   - `body.html`：综述正文，论点后加 `[n]` 角标（与 `references` 对应）。
   - `conclusion.html`：结论段落 + "数据来源与真实性说明"。
5. **生成**：`python3 src/review_generator.py --spec ... --body ... --conclusion ... --out ...`
6. **核验**：打开 HTML，确认角标可点击跳到底部引用、链接可达、耗时条形图比例正确。
7. **提交**：commit message 用 `docs(review): 新增 {主题} 知识综述` 风格；PR 描述里附检索日期与账号。

---

## 4. 数据完整性红线（最高优先级）

- **只写真实检索结果**。任何无法对应到 `references` 中某条链接的内容，不得写入报告。
- **内容缺口要显式标注**，不要回避、润色或编造来"补全"。示例中对"Prompt 工程"的诚实标注即范本。
- **链接遵循乐享约定**：`kb_page / kb_flink → /pages/{id}`，`kb_file / kb_video → /teams/{team_id}/docs/{id}`。
- 数字（命中数、耗时）必须来自工具返回的 `total` / `took_ms`，不得四舍五入后改写法（条形图比例除外，需注明基准）。

---

## 5. 提交信息（Commit Message）约定

采用 Conventional Commits 精简版：

- `feat(review):` 新增某主题综述
- `feat(gen):` 生成器功能增强
- `docs:` 文档/规范更新
- `fix:` 修复
- `chore:` 杂项

示例：`feat(review): 新增"向量数据库"知识综述（3 query / 12 唯一文档）`
