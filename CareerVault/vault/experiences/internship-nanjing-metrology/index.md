---
schema_version: 1
id: internship-nanjing-metrology
type: internship
title: 可穿戴运动传感器足部动作分析系统
organization: 南京市计量监督检测院
role: 项目成员 / MATLAB上位机开发与动作识别算法开发
start: 2023-07
end: 2023-08
status: verified
domains:
- 可穿戴传感
- 传感器数据采集
- 动作识别算法
skills:
- MATLAB AppDesigner
- 串口通信
- 九轴 IMU
- 姿态角解析
- 数据可视化
- 动作识别算法
resume_ready: true
created_at: 2026-08-21
updated_at: 2026-08-22T01:09:19+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 南京市计量监督检测院/南京市计量监督检测院实习.md
- 南京市计量监督检测院/032030121曹宇辉实习报告.docx
- Resume.md
migration_reviewed_at: 2026-08-22T01:09:19+08:00
---


# 可穿戴运动传感器足部动作分析系统

## 项目概述
参与基于可穿戴运动传感器的足部动作分析系统，负责 MATLAB AppDesigner 上位机、串口数据解析和基于姿态角变化的动作识别逻辑。

## 事实记录
- 使用多路 WIT-JY901S 九轴惯性传感器采集足部运动数据，覆盖加速度、角速度和姿态角等信息。
- 使用 MATLAB AppDesigner 开发上位机，实现串口选择、波特率设置、数据接收、姿态显示和动作结果可视化。
- 围绕多传感器数据流设计解析逻辑，通过数据头、分隔符和长度计数区分来源与字段，并将字符数据转换为数值数组供显示和识别使用。
- 通过校准记录初始姿态，以相对偏移量为判断基础，结合脚后跟滚转角、脚背俯仰角和脚趾俯仰角设计足部动作识别规则。
- 参与足部动作数据采集和整理，并配合 MATLAB 分类学习器进行初步特征分析，用于辅助选择较稳定、可区分的动作特征。

## 量化成果
- 原始记录覆盖放松、脚趾弯曲、抬大拇指、向内旋转、向外旋转等 5 类动作的数据采集与分析。
- 完成多传感器串口数据读取、格式转换、实时显示和动作反馈的上位机流程。

## Notes
迁移以详细 Markdown 实习记录为事实主来源；DOCX 实习报告作为证据文件来源路径保留，当前迁移分支不复制二进制附件。
