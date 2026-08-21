---
schema_version: 1
id: wearable-unity-hmi
type: project
title: 基于可穿戴传感和 Unity3D 的人机交互系统
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
resume_ready: true
created_at: 2026-08-21
updated_at: 2026-08-22T01:27:42+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 江苏省智能仪器大赛/基于可穿戴传感和 Unity3D 的人机交互系统.md
- Resume.md
migration_reviewed_at: 2026-08-22T01:27:20+08:00
---

# 基于可穿戴传感和 Unity3D 的人机交互系统

## 项目概述
参与设计并实现基于可穿戴传感器与 Unity3D 的实时人机交互系统，负责硬件与算法部分，通过弯曲传感器和 IMU 采集手部/手臂运动并驱动虚拟模型动作。

## 事实记录
- 设计基于串联分压的弯曲电阻信号调理电路，并对参考电压与固定电阻参数进行分析和优化。
- 集成 5 路手指弯曲传感器与 2 路六轴惯性传感器，完成多通道采集、数据打包和蓝牙无线传输。
- 基于惯性传感数据实现四元数姿态解算，并使用二阶龙格-库塔方法进行姿态状态更新，将姿态数据绑定到 Unity3D 模型骨骼。
- 针对不同用户手型与重复穿戴差异，设计在线最大/最小值更新的归一化算法，将弯曲量映射至 [0, 1]，并提供 Reset 重新标定机制。
- 提取传感器时域特征与虚拟模型轨迹特征，使用 SVM 进行手臂动作分类。
- 通过 Unity3D 骨骼动画与碰撞检测实现虚拟场景中的动作复现和物体交互。

## 量化成果
- 实验记录的手指伸直/完全弯曲电阻范围约为 9±0.7 kΩ 至 14±0.8 kΩ。
- 系统使用 5 路独立弯曲传感器和 2 个惯性节点进行动作采集。
- 项目参加第六届江苏省智能（虚拟）仪器竞赛并获一等奖。

## Notes
迁移时保留真实系统实现和实验结果；原文中的求职方向建议、能力总结等不作为独立事实。竞赛具体奖项等级在当前 Markdown 中未明确，因此不补写等级。
