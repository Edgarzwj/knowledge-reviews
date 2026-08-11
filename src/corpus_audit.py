#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
corpus_audit.py — 知识库语料充足度审计
=====================================

第一性原理：RAG（检索增强生成）的回答质量，天花板就是你的语料质量。
语料单薄、同质、或满是空容器，RAG 再怎么"降幻觉"也救不回来。
所以在生成任何知识综述之前，先量化回答一个问题：
    "这套知识库，到底配不配被用来做可靠的知识问答？"

GitHub 上已有的综述工具（scholar-rag / automated-slr-generator /
AI-Literature-Review-Generator）都假设"语料已经够好"，直接在其上生成。
它们缺的，正是本模块填补的这一环——语料充足度审计。

输入：若干条真实检索，每条带命中的文档 id 列表，以及其中"空容器"的 id。
输出：去重文档数、跨查询重叠率、内容页占比、覆盖广度，以及
      充足 / 临界 / 不足 的结论与理由。

纯标准库，无外部依赖。逻辑非空，故在 __main__ 留一个自测。
"""

from itertools import combinations


def assess(queries):
    """queries: [{"label": str, "doc_ids": [str], "container_ids": [str]}]

    返回审计字典：
        unique_docs   去重后的文档总数
        avg_overlap   跨查询两两 Jaccard 相似度的均值（越高越同质）
        content_ratio 内容页（非空文档）占去重文档的比例
        containers    空容器数量
        verdict       充足 / 临界 / 不足
        reason        结论理由（一句话，带数字）
    """
    if not queries:
        return {"verdict": "insufficient", "reason": "没有检索数据，无法评估。"}

    sets = [set(q.get("doc_ids", [])) for q in queries]
    all_ids = set().union(*sets) if sets else set()
    unique = len(all_ids)

    # 跨查询重叠：两两 Jaccard 均值。重叠越高，说明不同意图返回的是同一批文档，
    # 语料区分度越低。
    if len(sets) >= 2:
        js = []
        for a, b in combinations(sets, 2):
            union = len(a | b)
            js.append(len(a & b) / union if union else 0.0)
        overlap = sum(js) / len(js)
    else:
        overlap = 1.0 if sets and len(sets[0]) > 0 else 0.0

    # 内容页占比：空容器（知识库/文件夹类，无正文）不计入可用语料。
    containers = set()
    for q in queries:
        containers.update(q.get("container_ids", []))
    content = all_ids - containers
    content_ratio = len(content) / unique if unique else 0.0

    # 结论：先卡数量与同质，再卡覆盖与比例。
    if unique < 10 or overlap >= 0.9:
        verdict = "insufficient"
        reason = (f"唯一文档仅 {unique} 篇，跨查询重叠率 {overlap:.0%}，"
                  f"语料过于单薄且高度同质，撑不起可靠的知识问答 / RAG。")
    elif unique < 30 or content_ratio < 0.6 or overlap >= 0.7:
        verdict = "borderline"
        reason = (f"唯一文档 {unique} 篇、内容页占比 {content_ratio:.0%}、"
                  f"跨查询重叠率 {overlap:.0%}，能起步，但覆盖仍需扩充。")
    else:
        verdict = "sufficient"
        reason = (f"唯一文档 {unique} 篇、内容页占比 {content_ratio:.0%}、"
                  f"跨查询重叠率 {overlap:.0%}，语料具备一定覆盖度。")

    return {
        "unique_docs": unique,
        "avg_overlap": round(overlap, 3),
        "content_ratio": round(content_ratio, 3),
        "containers": len(containers),
        "verdict": verdict,
        "reason": reason,
    }


_VERDICTS_ZH = {"insufficient": "不足", "borderline": "临界", "sufficient": "充足"}


def verdict_label(verdict):
    return _VERDICTS_ZH.get(verdict, verdict)


def demo():
    # 用真实演示知识库自测：3 个意图均命中同一批 7 文档（5 内容页 + 2 空容器）。
    seven = ["a", "b", "c", "d", "e", "f", "g"]
    cont = ["f", "g"]
    queries = [
        {"label": "Q1", "doc_ids": list(seven), "container_ids": list(cont)},
        {"label": "Q2", "doc_ids": list(seven), "container_ids": list(cont)},
        {"label": "Q3", "doc_ids": list(seven), "container_ids": list(cont)},
    ]
    r = assess(queries)
    assert r["unique_docs"] == 7, r
    assert r["avg_overlap"] == 1.0, r
    assert r["verdict"] == "insufficient", r
    assert r["content_ratio"] == round(5 / 7, 3), r
    print("self-check OK ->", r)


if __name__ == "__main__":
    demo()
