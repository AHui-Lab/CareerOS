---
schema_version: 1
id: compute-empire-game
type: project
title: LLM 驱动的叙事经营游戏《Heirloom Ledger》
organization: 个人项目
role: 独立产品负责人（AI 辅助开发）
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
updated_at: 2026-09-07T15:31:30+08:00
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
---

# LLM 驱动的叙事经营游戏《Heirloom Ledger》

## 项目概述
一款"古玩店经营 + LLM 动态世界"的单机游戏原型（Godot 4）。核心设计是"确定性 Game Core 裁决事实、LLM 仅负责表达"：LLM 驱动 NPC 对话、谈判与叙事表现，但物品真伪、价格、交易结果等权威状态全部由规则引擎裁决，从架构上防止模型幻觉破坏游戏公平性。已交付可玩的第一章（10 天流程、8 名 NPC、28 件道具），支持玩家自带 API Key（BYOK）接入兼容 OpenAI 协议的模型服务。

## 事实记录
- 独立设计了一款"古玩店经营 + LLM 动态世界"单机游戏可玩原型（Godot 4）：10 天章节流程、8 名 NPC、28 件道具，完整跑通鉴定、谈判、交易、信誉结算闭环。
- 针对 LLM 幻觉破坏游戏规则的核心风险，设计"确定性 Game Core 裁决事实、LLM 仅负责表达"的架构，输出多条 AI 权限边界规范，覆盖信息隐藏、渐进披露、越权拦截等场景。
- 设计结构化输出 + Parser 校验机制：LLM 仅产出候选对话行为分类，经校验后由规则引擎结算，实现 NPC 耐心按语义行为而非消息数扣减。
- 进行质量测试：游戏的核心规则写了自动化测试——价格、真伪、信誉结算这些数值逻辑全部有测试覆盖，保证游戏公平性不受模型影响；二是用不同模型API做了真实模型联调，逐个场景检查 NPC 对话是否符合设计预期，并综合评估不同模型的效率、准确率、成本。
- 全程以 AI 编码工具实现，通过"设计文档锁定规则 + Task 验收标准 + 自动化检查"的治理流程控制 AI 产出质量。

## 量化成果


## Notes
当前专门项目源文件尚未在旧 Resume 仓库中发现，本条主要依据 `Resume.md` 汇总，因此标记为 medium confidence。建议后续关联实际项目 GitHub 仓库、测试日志或发布构建后再开启 Resume Ready。
