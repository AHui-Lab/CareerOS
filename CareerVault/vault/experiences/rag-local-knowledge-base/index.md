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
details: {}
---

# 本地知识库RAG对话obsdian插件

## 项目概述
独立设计并交付本地优先的知识库问答产品 OPSB（Obsidian 插件为主、Web 版为辅）：笔记向量化存于本地 IndexedDB，问答时检索 TopK 片段由 LLM 流式生成带出处、可跳转原文的回答，数据不出本机。

## 事实记录
个人独立完成（产品+研发+测试一体）：需求来自自己的真实痛点（Obsidian 笔记记了用不上）；独立完成方案设计、交互界面、核心代码（AI 辅助开发，我负责架构与取舍决策、review 与整合）及上线后自测迭代。迭代来自真实使用：专有名词答非所问 → 定位纯向量弱点 → 落地混合检索；不敢信 AI 回答 → 做来源跳原文与检索明细；调参没底气 → 建评测集让调参有据。全程留痕，每个功能对应真实 commit 与文档。

## 量化成果
- 支持 5 类常用文档格式：PDF / DOCX / Markdown / TXT / HTML。
- 检索策略包含双倍召回、相似度阈值过滤和来源去重三层处理。
- 实现 Web + Obsidian 双客户端共享后端架构。

## Notes
迁移时已排除原文中的“面试准备”“为什么选某技术”等问答内容；这些属于学习/表达材料，不作为简历事实。首次审核通过后再开启 Resume Ready。
