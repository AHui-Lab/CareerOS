---
schema_version: 1
id: internship-nanjing-heyue
type: internship
title: 人机交互系统开发实习
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
updated_at: 2026-08-22T01:07:01+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 南京合越科技有限公司实习/合越智能科技实习.md
- Resume.md
source_conflict_note: 详细实习记录优先于 Resume.md 中仅写 DigiHuman 的简化版本
migration_reviewed_at: 2026-08-22T01:06:49+08:00
---

# 人机交互系统开发实习

## 项目概述
围绕公司数据手套产品开发 Unity3D 人机交互上位机，工作覆盖传感器数据解析、BLE 通信、归一化与姿态处理、3D 人体模型、多设备扩展和 DigiHuman 项目复现。

## 事实记录
- 从零搭建 Unity3D 可视化交互系统，解析手指弯曲、IMU 姿态、压力等传感器数据并驱动 3D 模型动作。
- 与嵌入式端协作确定数据包格式，使用 C# 完成串口/数据字段解析，并开发 MATLAB AppDesigner 数据观察工具支持波形显示与标定。
- 将通信从经典蓝牙 SPP 迁移到 BLE，完成设备扫描、Service / Characteristic 识别、Subscribe、十六进制数据包校验和数值复原。
- 实现手指弯曲在线归一化、陀螺仪相对角度初始化、角度标准化和稳定性判断，用于降低不同用户和佩戴位置差异。
- 使用 MakeHuman 创建全身人体模型，并经 Blender 处理中转后导入 Unity，解决模型材质/渲染问题。
- 针对姿态轴间耦合抖动，在嵌入式侧应用互补滤波；原记录中陀螺仪权重为 0.96。
- 设计消息流水号进行数据丢包测试，并据测试结果选择 100 Hz 作为系统传输频率。
- 扩展系统至双手/多设备连接，完善设备状态、视角切换、动作范围限制和压力可视化等交互功能。
- 在实习后期完成 DigiHuman 项目环境搭建与运行复现，包括 MediaPipe、OpenCV、Flask 后端、Unity 配置和视频驱动动作/表情验证。
- 编写 Unity 软件操作指南和新设备接入说明，整理工程结构、控制脚本和多设备配置流程。

## 量化成果
- 数据丢包测试记录：50 Hz 为 0%，100 Hz 为 0%，200 Hz 为 2.63%；据此选取 100 Hz。
- 系统扩展至双手多设备同时连接与动作捕捉。

## Notes
旧 `Resume.md` 将该实习简化为“DigiHuman 数字人项目复现”，且时间写法不完整；详细实习记录显示主要工作是持续约 7 周的数据手套 HMI 开发，DigiHuman 是最后阶段的一部分。迁移以详细记录为准。
