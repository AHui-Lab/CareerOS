---
schema_version: 1
id: compute-empire-game
type: project
title: LLM 驱动的叙事经营游戏《Heirloom Ledger》
organization: 个人项目
role: 原型试玩与体验改进（AI 辅助开发）
start: 2026-08
end: 至今
status: verified
domains:
- AI辅助开发
- 游戏开发
- 数据驱动系统
- 自动化测试
skills:
- Godot 4
- GDScript
- Python
- JSON
- AI Agent
- 自动化测试
resume_ready: true
created_at: 2026-08-21
updated_at: 2026-09-10T21:37:19+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: medium
source_paths:
- Resume.md
migration_reviewed_at: 2026-08-21T22:58:02+08:00
related_experience_ids: []
related_experiences: []
details:
  project_role: ''
  project_pitch: 借助 AI 编码工具开发的"古玩经营 + LLM 对话"游戏原型：LLM 只负责对话表达，物品真伪与交易结果由确定性规则引擎裁决，防止幻觉破坏公平。
  personal_contribution: 负责需求、玩法取舍与试玩验收：发现"反复交易缺持续目标"，提出加剧情任务并从 AI 方案中选定冲突叙事方向；对核心数值规则编写自动化测试。
  project_outcome: 已交付可玩第一章（10 天流程、8 名 NPC、28 件道具），可产出 Web 试玩包；新增剧情仍在细化。
  hr_intro: 我用 AI 编码工具做了个能玩的游戏原型，我负责需求、玩法取舍和验收。比如试玩发现缺长期目标，就提出加剧情任务。架构上让 AI 只管对话、数值由规则引擎裁决，防止幻觉破坏公平。
---


# LLM 驱动的叙事经营游戏《Heirloom Ledger》

## 项目概述
用 AI 编码工具做出的"古玩店经营 + LLM 动态世界"游戏原型（Godot 4）：LLM 驱动 NPC 对话与叙事，但物品真伪、价格、交易结果全部由确定性规则引擎裁决，从架构上防止模型幻觉破坏公平。已交付可玩第一章（10 天流程、8 名 NPC、28 件道具），支持玩家自带 API Key。

## 事实记录
- 借助 AI 编码工具做出可玩原型：完整跑通鉴定、谈判、交易、信誉结算闭环，可产出 Web 试玩包。
- 设计"确定性 Game Core 裁决事实、LLM 仅负责表达"的架构，并输出 AI 权限边界规范（信息隐藏、渐进披露、越权拦截）。
- 设计结构化输出 + 校验机制：LLM 只产出候选对话行为，经校验后由规则引擎结算。
- 对价格、真伪、信誉结算等核心数值规则编写自动化测试；用不同模型 API 逐场景联调，检查 NPC 对话是否符合设计预期。
- 通过"设计文档锁定规则 + Task 验收标准 + 自动化检查"控制 AI 产出质量。

## 量化成果


## Notes
当前专门项目源文件尚未在旧 Resume 仓库中发现，本条主要依据 `Resume.md` 汇总，因此标记为 medium confidence。建议后续关联实际项目 GitHub 仓库、测试日志或发布构建后再开启 Resume Ready。
