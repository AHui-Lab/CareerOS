---
schema_version: 1
id: internship-nanjing-heyue
type: internship
title: 南京合越智能科技有限公司 · Unity可视化人机交互、BLE与传感器数据处理
organization: 南京合越智能科技有限公司
role: Unity可视化人机交互、BLE与传感器数据处理
start: 2024-06
end: 2024-08
status: archived
domains:
- 人机交互
- 可穿戴设备
- 上位机
- BLE
- 数字人
skills:
- Unity3D
- C#
- BLE
- MPU6050
- 互补滤波
- 数据归一化
- Blender
resume_ready: true
created_at: 2026-08-21
updated_at: 2026-09-14T02:45:43+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 南京合越科技有限公司实习/合越智能科技实习.md
- Resume.md
source_conflict_note: 详细实习记录优先于 Resume.md 中仅写 DigiHuman 的简化版本
migration_reviewed_at: 2026-08-22T01:06:49+08:00
related_experience_ids: []
related_experiences: []
details:
  department: ''
  internship_type: ''
---

# 南京合越智能科技有限公司 · Unity可视化人机交互、BLE与传感器数据处理

## 项目概述
负责多传感器动作采集系统的 BLE 通信与 Unity 端：用丢包测试数据推动方案取舍、选定 100 Hz，交付现场可运行演示。

## 事实记录
- 负责通信方案与 Unity 端（5 路手指弯曲 + 3 路 IMU）：与嵌入式协作定协议，完成数据接入、姿态复原与三维动作映射，现场演示。
- 推动通信由经典蓝牙 SPP 迁移至 BLE：设计消息流水号丢包测试，当次测试 50/100 Hz 零丢包、200 Hz 丢 2.63%，据此选定 100 Hz。
- 针对手型与佩戴差异做在线归一化、零点校准与姿态漂移处理；协同嵌入式引入互补滤波抑制抖动与轴间耦合。
- Unity 端独立完成：双手交互、设备状态管理、压力可视化，支持双手多设备同时连接。

## 量化成果
- 丢包测试（当次）：50 Hz 0%、100 Hz 0%、200 Hz 2.63%；据此选定 100 Hz。
- 系统扩展至双手多设备同时动作捕捉。

## Notes
