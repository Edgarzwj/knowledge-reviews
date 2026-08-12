#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_generator.py — 可复现的知识综述生成器 (Knowledge Review Generator)
=========================================================================

这是一个**零外部依赖**的纯标准库脚本，作用是把"一次真实检索得到的数据"
渲染成一页**单文件、全资源内联、暗色科技感**的 HTML 综述报告。

设计哲学（详见 docs/architecture.md）：
  1. 数据 / 内容 / 渲染 三层分离 —— 同一份 spec 永远渲染出同一份 HTML。
  2. 所有数字、标题、链接必须来自真实检索，本脚本不做任何编造。
  3. 报告自带"检索过程可视化"与"来源角标 + 引用列表"，可追溯、可核验。

输入（默认都在 samples/ 目录下）：
  - spec.json        : 元数据、query 命中统计、聚合说明、来源引用（纯数据）
  - body.html        : 综述正文（带 [n] 角标的 HTML 片段）
  - conclusion.html  : 结论 + 数据真实性说明（HTML 片段）

输出：
  - <out>.html       : 自包含的单文件报告（CSS 内联，无外部字体/脚本/图片）

用法：
  python3 src/review_generator.py
  python3 src/review_generator.py --spec samples/spec.json \
        --body samples/body.html --conclusion samples/conclusion.html \
        --out samples/企业知识问答系统_知识综述.html
"""

import argparse
import json
import os
import sys

# 语料充足度审计：与生成器同目录，纯标准库，无外部依赖。
from corpus_audit import assess, verdict_label

# ----------------------------------------------------------------------------
# 渲染模板：暗色科技感主题（与首版报告一致的视觉语言，纯内联 CSS）
# ----------------------------------------------------------------------------
CSS = """\
  :root{
    --bg0:#05070f; --bg1:#0a0f1f; --bg2:#0f1626; --panel:#111a2e; --panel2:#13203a;
    --line:#1e2c47; --line2:#28395c;
    --cyan:#22d3ee; --purple:#a855f7; --green:#34d399; --amber:#fbbf24; --pink:#f472b6;
    --txt:#e6edf7; --txt2:#9fb0c9; --txt3:#6b7a99;
    --mono:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{
    font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
    color:var(--txt);
    background:
      radial-gradient(1200px 600px at 15% -10%, rgba(34,211,238,.10), transparent 60%),
      radial-gradient(1000px 500px at 95% 0%, rgba(168,85,247,.10), transparent 55%),
      linear-gradient(180deg,var(--bg0),var(--bg1) 40%,var(--bg0));
    background-attachment:fixed;
    line-height:1.7; padding:0 0 80px;
  }
  .wrap{max-width:1180px;margin:0 auto;padding:0 22px}
  header{
    border-bottom:1px solid var(--line);
    background:linear-gradient(180deg,rgba(17,26,46,.85),rgba(10,15,31,.4));
    backdrop-filter:blur(6px);
    padding:30px 0 26px; margin-bottom:30px;
  }
  .kicker{font:600 12px/1 var(--mono);letter-spacing:.22em;color:var(--cyan);text-transform:uppercase}
  h1{font-size:38px;line-height:1.15;margin:12px 0 6px;font-weight:800;
     background:linear-gradient(90deg,#fff,#9fe9ff 40%,#cfa8ff);-webkit-background-clip:text;background-clip:text;color:transparent}
  .sub{color:var(--txt2);font-size:15px}
  .src-pill{display:inline-flex;align-items:center;gap:8px;margin-top:14px;padding:7px 14px;border:1px solid var(--line2);
    border-radius:999px;background:var(--panel);font:600 13px/1 var(--mono);color:var(--green)}
  .src-pill::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 10px var(--green)}
  .meta{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}
  .meta .cell{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .meta .k{font:600 11px/1 var(--mono);letter-spacing:.12em;color:var(--txt3);text-transform:uppercase}
  .meta .v{font-size:20px;font-weight:800;margin-top:8px;color:#fff}
  .meta .v small{font-size:12px;color:var(--txt2);font-weight:600}
  section{margin:34px 0}
  .sec-h{display:flex;align-items:baseline;gap:12px;margin-bottom:16px}
  .sec-h .idx{font:800 13px/1 var(--mono);color:var(--bg0);background:var(--cyan);padding:5px 9px;border-radius:6px}
  .sec-h h2{font-size:22px;font-weight:800}
  .sec-h .tag{margin-left:auto;font:600 12px/1 var(--mono);color:var(--txt3);border:1px solid var(--line);padding:5px 10px;border-radius:999px}
  .flow{display:grid;grid-template-columns:1fr auto 1fr;gap:18px;align-items:stretch}
  .qcards{display:grid;gap:12px}
  .qcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 15px;position:relative;overflow:hidden}
  .qcard::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,var(--cyan),var(--purple))}
  .qcard .q{font:600 14px/1.4 var(--mono);color:#dbeafe}
  .qcard .row{display:flex;gap:16px;margin-top:11px}
  .qcard .row .m{flex:1}
  .qcard .row .mk{font:600 10px/1 var(--mono);letter-spacing:.1em;color:var(--txt3)}
  .qcard .row .mv{font-size:18px;font-weight:800;color:#fff;margin-top:4px}
  .qcard .row .mv.c{color:var(--cyan)} .qcard .row .mv.p{color:var(--purple)} .qcard .row .mv.g{color:var(--green)}
  .agg{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;min-width:190px}
  .agg .node{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line2);border-radius:14px;padding:16px 18px;text-align:center;width:100%}
  .agg .node .big{font-size:30px;font-weight:900;background:linear-gradient(90deg,var(--cyan),var(--purple));-webkit-background-clip:text;background-clip:text;color:transparent}
  .agg .node .lbl{font-size:12px;color:var(--txt2);margin-top:4px}
  .agg .sub2{font:600 12px/1.5 var(--mono);color:var(--txt3);text-align:center}
  .arrow{display:flex;align-items:center;color:var(--line2);font-size:26px}
  .prose{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px 24px}
  .prose p{margin:13px 0;color:var(--txt)}
  .prose p:first-child{margin-top:0}
  .prose h3{font-size:16px;margin:20px 0 4px;color:var(--cyan);font-weight:800}
  .prose h3:first-of-type{margin-top:6px}
  sup{font:700 11px/1 var(--mono);color:var(--amber);margin:0 1px;vertical-align:super}
  sup a{color:inherit;text-decoration:none}
  sup a:hover{text-decoration:underline}
  .note{margin-top:14px;padding:12px 14px;border-left:3px solid var(--amber);background:rgba(251,191,36,.07);border-radius:0 10px 10px 0;font-size:13.5px;color:var(--txt2)}
  .gap{color:var(--amber);font-weight:700}
  ul.tight{margin:8px 0 4px 20px} ul.tight li{margin:6px 0;color:var(--txt)}
  .hl{color:#fff;font-weight:700}
  .kw{color:var(--cyan)}
  .refs{display:grid;gap:12px}
  .ref{display:grid;grid-template-columns:48px 1fr;gap:14px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .ref .num{font:800 22px/1 var(--mono);color:var(--cyan);text-align:center}
  .ref .ttl{font-weight:800;font-size:15.5px;color:#fff}
  .ref .url{font:500 12.5px/1.5 var(--mono);color:var(--txt2);word-break:break-all;margin:5px 0 9px}
  .ref .url a{color:var(--cyan);text-decoration:none} .ref .url a:hover{text-decoration:underline}
  .tags{display:flex;flex-wrap:wrap;gap:7px}
  .tagchip{font:600 11px/1 var(--mono);padding:5px 9px;border-radius:999px;border:1px solid var(--line2);color:var(--txt2);background:var(--bg2)}
  .tagchip.r{color:#fda4af;border-color:#7f1d3a} .tagchip.p{color:#d8b4fe;border-color:#5b21b6}
  .tagchip.a{color:#7dd3fc;border-color:#0e4f6b} .tagchip.g{color:#86efac;border-color:#14532d}
  .concl{background:linear-gradient(160deg,rgba(34,211,238,.08),rgba(168,85,247,.08));border:1px solid var(--line2);border-radius:16px;padding:24px 26px}
  .concl h2{font-size:20px;margin-bottom:12px}
  .concl p{color:var(--txt);margin:10px 0}
  .method{margin-top:22px;border-top:1px dashed var(--line2);padding-top:16px;font-size:13px;color:var(--txt3)}
  .method b{color:var(--txt2)}
  .method code{font:600 12px/1.4 var(--mono);color:var(--green);background:var(--bg2);padding:2px 6px;border-radius:5px}
  footer{margin-top:40px;text-align:center;color:var(--txt3);font-size:12.5px}
  .bars{margin-top:14px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .bars .bar-h{font:600 12px/1 var(--mono);color:var(--txt3);letter-spacing:.08em;margin-bottom:12px;text-transform:uppercase}
  .bar{display:grid;grid-template-columns:84px 1fr 58px;align-items:center;gap:10px;margin:9px 0}
  .bar .bl{font:600 12px/1 var(--mono);color:var(--txt2)}
  .bar .bt{height:10px;border-radius:6px;background:linear-gradient(90deg,var(--cyan),var(--purple));box-shadow:0 0 10px rgba(34,211,238,.25)}
  .bar .bv{font:700 12px/1 var(--mono);color:#fff;text-align:right}
  .audit{background:linear-gradient(160deg,rgba(244,63,94,.08),rgba(251,191,36,.06));border:1px solid var(--line2);border-radius:16px;padding:22px 24px}
  .audit h2{font-size:20px;margin-bottom:14px}
  .audit .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:6px 0 14px}
  .audit .cell{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
  .audit .cell .k{font:600 11px/1 var(--mono);letter-spacing:.1em;color:var(--txt3);text-transform:uppercase}
  .audit .cell .v{font-size:22px;font-weight:800;color:#fff;margin-top:8px}
  .badge{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;border-radius:999px;font:700 14px/1 var(--mono);border:1px solid}
  .badge.insufficient{color:#fda4af;border-color:#7f1d3a;background:rgba(244,63,94,.10)}
  .badge.borderline{color:#fcd34d;border-color:#7c5e10;background:rgba(251,191,36,.10)}
  .badge.sufficient{color:#86efac;border-color:#14532d;background:rgba(52,211,153,.10)}
  @media(max-width:820px){.meta{grid-template-columns:repeat(2,1fr)}.flow{grid-template-columns:1fr}.arrow{transform:rotate(90deg);justify-content:center}.audit .grid{grid-template-columns:1fr}}
"""


def esc(text):
    """对插入到 HTML 文本节点/属性中的字符串做基础转义（防御性，非信任绕过）。"""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def render_meta(meta):
    cells = [
        ("account_label", "account", ""),
        ("searches_label", "searches", "searches_unit"),
        ("hits_label", "total_hits", "hits_unit"),
        ("date_label", "date", ""),
    ]
    out = []
    for label_key, val_key, unit_key in cells:
        unit = f" <small>{esc(meta.get(unit_key, ''))}</small>" if unit_key and meta.get(unit_key) else ""
        out.append(
            f'      <div class="cell"><div class="k">{esc(meta.get(label_key, ""))}</div>'
            f'<div class="v">{esc(str(meta.get(val_key, "")))}{unit}</div></div>'
        )
    return "\n".join(out)


def render_queries(queries):
    cards = []
    for q in queries:
        accent = q.get("accent", "")
        cls = f" mv {accent}" if accent else ""
        cards.append(
            f'        <div class="qcard">\n'
            f'          <div class="q">{esc(q.get("q", ""))}</div>\n'
            f'          <div class="row">\n'
            f'            <div class="m"><div class="mk">命中数 TOTAL</div><div class="mv{cls}">{esc(str(q.get("total", "")))}</div></div>\n'
            f'            <div class="m"><div class="mk">耗时 TOOK_MS</div><div class="mv">{esc(str(q.get("took_ms", "")))} ms</div></div>\n'
            f'          </div>\n'
            f'        </div>'
        )
    return "\n".join(cards)


def render_bars(queries):
    max_ms = max((int(q.get("took_ms", 0)) for q in queries), default=1) or 1
    rows = []
    for q in queries:
        ms = int(q.get("took_ms", 0))
        width = round(ms / max_ms * 100, 1)
        label = esc(q.get("q", "").split("·")[-1].strip()) if "·" in q.get("q", "") else esc(q.get("q", ""))
        rows.append(
            f'      <div class="bar"><span class="bl">{label}</span>'
            f'<span class="bt" style="width:{width}%"></span>'
            f'<span class="bv">{ms} ms</span></div>'
        )
    return "\n".join(rows)


def render_aggregation(agg):
    return (
        f'      <div class="agg">\n'
        f'        <div class="node">\n'
        f'          <div class="big">{esc(str(agg.get("unique_value", "")))}</div>\n'
        f'          <div class="lbl">{agg.get("unique_label", "")}</div>\n'
        f'        </div>\n'
        f'        <div class="sub2">{agg.get("hits_note", "")}</div>\n'
        f'        <div class="node" style="border-color:var(--line)">\n'
        f'          <div class="big" style="font-size:22px">{esc(str(agg.get("split_value", "")))}</div>\n'
        f'          <div class="lbl">{agg.get("split_label", "")}</div>\n'
        f'        </div>\n'
        f'      </div>'
    )


def render_references(refs):
    items = []
    for i, r in enumerate(refs, start=1):
        tags = "".join(f'<span class="tagchip">{esc(t)}</span>' for t in r.get("tags", []))
        items.append(
            f'      <div class="ref" id="ref{i}">\n'
            f'        <div class="num">{i}</div>\n'
            f'        <div>\n'
            f'          <div class="ttl">{esc(r.get("title", ""))}</div>\n'
            f'          <div class="url"><a href="{esc(r.get("url", ""))}" target="_blank" rel="noopener">{esc(r.get("url", ""))}</a></div>\n'
            f'          <div class="tags">{tags}</div>\n'
            f'        </div>\n'
            f'      </div>'
        )
    return "\n".join(items)


def render_audit(spec):
    """若 spec 提供 audit.queries（真实检索的文档 id 集合），渲染语料充足度审计卡。"""
    audit_q = spec.get("audit", {}).get("queries")
    if not audit_q:
        return ""
    r = assess(audit_q)
    return f"""  <section>
    <div class="sec-h"><span class="idx">审计</span><h2>语料充足度审计</h2><span class="tag">第一性原理：RAG 质量 ≤ 语料质量</span></div>
    <div class="audit">
      <div class="grid">
        <div class="cell"><div class="k">唯一文档</div><div class="v">{r['unique_docs']}</div></div>
        <div class="cell"><div class="k">跨查询重叠率</div><div class="v">{r['avg_overlap']:.0%}</div></div>
        <div class="cell"><div class="k">内容页占比</div><div class="v">{r['content_ratio']:.0%}</div></div>
      </div>
      <span class="badge {r['verdict']}">结论：{verdict_label(r['verdict'])}</span>
      <p style="margin-top:12px;color:var(--txt)">{esc(r['reason'])}</p>
      {f'<p style="margin-top:10px;font-size:13px;color:var(--txt2)">{esc(spec["audit"].get("note",""))}</p>' if spec.get("audit",{}).get("note") else ""}
    </div>
  </section>
"""


def build_html(spec, body_html, conclusion_html):
    meta = spec.get("meta", {})
    queries = spec.get("queries", [])
    agg = spec.get("aggregation", {})
    refs = spec.get("references", [])
    rev = spec.get("review_section", {"idx": "02", "title": "综述正文", "tag": "带源角标"})

    audit_html = render_audit(spec)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(meta.get('title', '知识综述'))} | 腾讯云知（乐享）</title>
<style>
{CSS}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="kicker">{esc(meta.get('kicker', 'Knowledge Review · 腾讯云知（乐享）'))}</div>
    <h1>{esc(meta.get('title', ''))}</h1>
    <div class="sub">{esc(meta.get('subtitle', ''))}</div>
    <div class="src-pill">{esc(meta.get('source', ''))}</div>
    <div class="meta">
{render_meta(meta)}
    </div>
  </div>
</header>

<div class="wrap">

  <!-- ===== 检索过程可视化 ===== -->
  <section>
    <div class="sec-h"><span class="idx">01</span><h2>{esc(spec.get('search_flow_title', '检索过程可视化'))}</h2><span class="tag">{esc(spec.get('search_flow_tag', 'query → hits → 聚合'))}</span></div>
    <div class="flow">
      <div class="qcards">
{render_queries(queries)}
      </div>

      <div class="arrow">➜</div>

{render_aggregation(agg)}
    </div>
    <div class="note">{agg.get('note', '')}</div>
    <div class="bars">
      <div class="bar-h">检索耗时对比 · 真实 took_ms（以最长 {max((int(q.get('took_ms',0)) for q in queries), default=0)}ms 为基准）</div>
{render_bars(queries)}
    </div>
  </section>

{audit_html}
  <!-- ===== 综述正文 ===== -->
  <section>
    <div class="sec-h"><span class="idx">{esc(rev.get('idx', '02'))}</span><h2>{esc(rev.get('title', '综述正文'))}</h2><span class="tag">{esc(rev.get('tag', '带源角标'))}</span></div>
    <div class="prose">
{body_html}
    </div>
  </section>

  <!-- ===== 来源引用 ===== -->
  <section>
    <div class="sec-h"><span class="idx">03</span><h2>{esc(spec.get('references_title', '来源引用列表'))}</h2><span class="tag">{esc(spec.get('references_tag', '标题 + 链接 + 关键词标签'))}</span></div>
    <div class="refs">
{render_references(refs)}
    </div>
  </section>

  <!-- ===== 结论与数据说明 ===== -->
  <section>
    <div class="concl">
      <h2>{esc(spec.get('conclusion_title', '结论'))}</h2>
{conclusion_html}
    </div>
  </section>

  <footer>Generated from 腾讯云知（乐享）知识库真实检索 · 单文件离线报告 · 所有资源内联</footer>
</div>
</body>
</html>
"""
    return html


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_spec = os.path.join(here, "..", "samples", "spec.json")
    default_body = os.path.join(here, "..", "samples", "body.html")
    default_concl = os.path.join(here, "..", "samples", "conclusion.html")
    default_out = os.path.join(here, "..", "samples", "企业知识问答系统_知识综述.html")

    ap = argparse.ArgumentParser(description="可复现的知识综述 HTML 生成器")
    ap.add_argument("--spec", default=default_spec, help="spec.json 路径")
    ap.add_argument("--body", default=default_body, help="综述正文 HTML 片段")
    ap.add_argument("--conclusion", default=default_concl, help="结论 HTML 片段")
    ap.add_argument("--out", default=default_out, help="输出 HTML 路径")
    args = ap.parse_args()

    try:
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
        with open(args.body, "r", encoding="utf-8") as f:
            body_html = f.read().strip()
        with open(args.conclusion, "r", encoding="utf-8") as f:
            conclusion_html = f.read().strip()
    except FileNotFoundError as e:
        sys.exit(f"[错误] 找不到输入文件：{e}")
    except json.JSONDecodeError as e:
        sys.exit(f"[错误] spec.json 解析失败：{e}")

    html = build_html(spec, body_html, conclusion_html)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(args.out)
    print(f"[完成] 已生成 {args.out} （{size} 字节，单文件、全资源内联）")


if __name__ == "__main__":
    main()
