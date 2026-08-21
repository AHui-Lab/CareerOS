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
updated_at: 2026-08-22T01:28:04+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 基于Langchain/基于LangChain的本地知识库智能问答系统.md
- Resume.md
migration_reviewed_at: 2026-08-22T01:23:24+08:00
---

# 本地知识库RAG对话obsdian插件

## 项目概述
独立设计并实现端到端本地 RAG 知识库系统，支持多格式文档导入、索引、检索、带来源引用的问答和流式输出；Web 应用与 Obsidian 桌面插件共用同一 FastAPI 后端。

## 事实记录
- 支持 PDF、DOCX、Markdown、TXT、HTML 等文档导入，并完成递归分块、Embedding、ChromaDB 检索和 LLM 生成链路。
- 基于 LangChain LCEL 组织 ChatPromptTemplate、RunnableParallel、StrOutputParser 等组件，并针对中文文本配置语义分隔符。
- 设计“扩大召回 + 相似度阈值过滤 + 来源去重”的检索策略，默认相似度阈值记录为 0.3。
- 使用工厂模式统一 LLM 与 Embedding 接口，支持 OpenAI 兼容 API 与本地 Ollama 模型切换；Embedding 变更时可重建向量索引。
- 使用 FastAPI 实现异步 REST API，覆盖文档管理、检索、SSE 流式对话和模型配置更新，使用 Pydantic 做数据校验并以 YAML 持久化配置。
- 使用原生 JavaScript 开发 Web 客户端；使用 TypeScript 开发 Obsidian 插件，支持笔记、文件夹和 Vault 级索引、侧边栏对话及保存同步。
- 系统具备完全本地部署路径，记录的默认中文 Embedding 模型为 bge-small-zh-v1.5，并可配合 Ollama 本地 LLM 使用。

## 量化成果
- 支持 5 类常用文档格式：PDF / DOCX / Markdown / TXT / HTML。
- 检索策略包含双倍召回、相似度阈值过滤和来源去重三层处理。
- 实现 Web + Obsidian 双客户端共享后端架构。

## Notes
迁移时已排除原文中的“面试准备”“为什么选某技术”等问答内容；这些属于学习/表达材料，不作为简历事实。首次审核通过后再开启 Resume Ready。
