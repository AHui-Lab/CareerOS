---
schema_version: 1
id: internship-nanjing-heyue
type: internship
title: 多传感器融合动作采集与交互系统
organization: 南京合越智能科技有限公司
role: 实习生 / Unity 上位机、BLE 与传感器数据处理
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
updated_at: 2026-08-27T07:57:24+08:00
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

# 多传感器融合动作采集与交互系统

## 项目概述
面向游戏交互和康复训练场景，主导低功耗蓝牙通信方案设计，完成最多5路手指弯曲传感器及手掌、小臂、大臂3个IMU传感器的数据接入、协议解析与统一管理。负责BLE设备扫描、特征订阅、数据包校验、姿态数值复原及丢包测试，并据此确定100 Hz传输频率。实现手指数据在线归一化、IMU角度初始化、姿态漂移校准和动作稳定性判断；独立完成Unity3D端数据接收及三维动作映射，支持双手交互、压力可视化和现场演示。

## 事实记录
面向游戏交互和康复训练场景，负责多传感器采集系统的通信方案与 Unity 端应用开发，完成现场可运行演示。
- 主导低功耗蓝牙通信整体方案设计，完成最多 5路手指弯曲传感器及手掌、小臂、大臂 3个IMU传感器的数据接入与统一管理。
- 与嵌入式端协作制定数据包格式，负责 BLE 设备扫描、Service/Characteristic 识别、数据订阅、十六进制数据包校验、字段解析及姿态数值复原。
- 推动设备通信方式由经典蓝牙 SPP 迁移至 BLE，并设计消息流水号开展丢包测试，结合测试结果确定 100 Hz 数据传输频率。
- 针对不同用户手型、佩戴位置及初始姿态差异，完成手指弯曲数据在线归一化、IMU 相对角度初始化、角度标准化及动作稳定性判断。
- 针对姿态轴间耦合和抖动问题，协同嵌入式端引入互补滤波方案；同时通过静态校准和零点设定处理姿态漂移问题。
- 独立完成 Unity3D 数据接收与动作映射，将手指弯曲、IMU 姿态及压力数据驱动至三维人体模型，实现双手交互、设备状态管理、视角切换、动作范围限制及压力可视化。

## 量化成果
- 数据丢包测试记录：50 Hz 为 0%，100 Hz 为 0%，200 Hz 为 2.63%；据此选取 100 Hz。
- 系统扩展至双手多设备同时连接与动作捕捉。

## Notes
