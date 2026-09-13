---
schema_version: 1
id: wearable-unity-hmi
type: project
title: 可穿戴手部动作捕捉与虚拟交互系统
organization: 南京航空航天大学 自动化学院
role: 核心成员（硬件与算法）
start: '2023'
end: '2023'
status: verified
domains:
- 可穿戴设备
- 人机交互
- 嵌入式
- 传感器算法
skills:
- 弯曲传感器
- IMU
- ADC
- 蓝牙
- 四元数
- 二阶龙格-库塔
- SVM
- Unity3D
- C#
resume_ready: false
created_at: 2026-08-21
updated_at: 2026-08-27T08:25:27+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 江苏省智能仪器大赛/基于可穿戴传感和 Unity3D 的人机交互系统.md
- Resume.md
migration_reviewed_at: 2026-08-22T01:27:20+08:00
related_experience_ids: []
related_experiences: []
details:
  project_pitch: 可穿戴手部动作捕捉：5 路手指弯曲 + 2 路 IMU，姿态解算与动作分类后在 Unity3D 中驱动虚拟交互。
  personal_contribution: 核心成员（硬件与算法）：设计信号调理电路、四元数姿态解算、在线归一化与 SVM 动作分类，打通采集到 Unity 交互全链路。
  project_outcome: 获第六届江苏省智能（虚拟）仪器竞赛一等奖。
---

# 可穿戴手部动作捕捉与虚拟交互系统

## 项目概述
可穿戴手部动作捕捉与虚拟交互系统：5 路手指弯曲 + 2 路六轴 IMU 采集，四元数姿态解算与 SVM 动作分类，在 Unity3D 中驱动虚拟模型完成交互；获第六届江苏省智能（虚拟）仪器竞赛一等奖。

## 事实记录
- 设计弯曲电阻信号调理电路，完成 5 路手指弯曲 + 2 路六轴 IMU 的多通道采集与蓝牙传输。
- 实现四元数姿态解算（二阶龙格-库塔更新），将手部姿态映射至 Unity3D 模型骨骼，完成骨骼驱动、碰撞检测与虚拟交互。
- 针对手型与重复穿戴差异，设计在线最大/最小值归一化 + Reset 快速重标定，保证跨用户数据一致性。
- 融合传感器时域特征与虚拟模型轨迹特征，用 SVM 实现手臂动作分类。

## 量化成果
- 实验记录的手指伸直/完全弯曲电阻范围约为 9±0.7 kΩ 至 14±0.8 kΩ。
- 系统使用 5 路独立弯曲传感器和 2 个惯性节点进行动作采集。
- 项目参加第六届江苏省智能（虚拟）仪器竞赛并获一等奖。

## Notes
