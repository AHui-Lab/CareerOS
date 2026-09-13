---
schema_version: 1
id: rag-local-knowledge-base
type: project
title: 本地知识库RAG对话obsdian插件
organization: 个人项目
role: 独立开发
start: 2024-09
end: 至今
status: verified
domains:
- AI应用
- RAG
- LLM
- Agent
- 本地知识库
skills:
- Python
- LangChain
- FastAPI
- ChromaDB
- HuggingFace
- Ollama
- TypeScript
- SSE
resume_ready: true
created_at: 2026-08-21
updated_at: 2026-09-07T16:38:42+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 基于Langchain/基于LangChain的本地知识库智能问答系统.md
- Resume.md
migration_reviewed_at: 2026-08-22T01:23:24+08:00
related_experience_ids: []
related_experiences: []
details:
  project_pitch: 给自己的笔记做的问答工具（Obsidian 插件）：问一句，AI 从笔记里找答案并标注出处，可跳回原文核对。
  personal_contribution: 独立完成产品设计、实现取舍与自测迭代（AI 辅助开发）；专有名词答不准时定位为检索问题，调整检索策略并用固定问题复测；为回答加来源跳转，每句可回原文核对。
  project_outcome: 支持 PDF/DOCX/Markdown/TXT/HTML 五类文档，Web 与 Obsidian 双端；日常自用中持续迭代。
  hr_intro: 我做了个问笔记的工具——问一句，AI 从笔记里找答案并标出处、能跳回原文，我自己天天在用。答不准时我定位是检索的问题，调了策略，用固定问题复测。
---

# 本地知识库RAG对话obsdian插件

## 项目概述
独立开发的笔记问答工具（Obsidian 插件为主、Web 版为辅）：问一句，AI 从自己的笔记里找答案，回答带出处、可跳回原文核对；笔记与向量存本机，日常自用中持续迭代。

## 事实记录
- 需求来自真实痛点（笔记记了用不上）：独立完成产品设计、实现取舍与自测迭代；AI 辅助开发，本人负责架构与取舍决策、review 与整合。
- 按真实使用迭代：专有名词答非所问 → 定位为纯向量检索的弱点 → 调整检索策略（双倍召回、阈值过滤、来源去重），并用固定问题复测验证。
- 为"不敢信 AI 回答"加来源跳转：每句回答可跳回原文核对，并附检索明细；调参以固定问题复测为据，不凭感觉。
- 每个功能对应真实 commit 与文档，全程留痕。

## 量化成果
- 支持 5 类常用文档格式：PDF / DOCX / Markdown / TXT / HTML。
- 检索策略包含双倍召回、相似度阈值过滤和来源去重三层处理。
- 实现 Web + Obsidian 双客户端共享后端架构。

## Notes
迁移时已排除原文中的“面试准备”“为什么选某技术”等问答内容；这些属于学习/表达材料，不作为简历事实。首次审核通过后再开启 Resume Ready。
