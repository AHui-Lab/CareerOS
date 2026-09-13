---
schema_version: 1
id: stm32-mower-sensor-fusion
type: project
title: 割草机多传感器融合定位导航系统
organization: 南京航空航天大学 自动化学院
role: 本科毕业设计 / 独立完成
start: 2023-12
end: 2024-06
status: verified
domains:
- 嵌入式
- 机器人定位
- 多传感器融合
- 导航算法
skills:
- STM32F407
- C
- UWB
- IMU
- ODOM
- EKF
- UART
- MATLAB AppDesigner
resume_ready: true
created_at: 2026-08-21
updated_at: 2026-09-14T02:41:10+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 本科毕设/本科毕设.md
- Resume.md
migration_reviewed_at: 2026-08-22T01:27:09+08:00
related_experience_ids: []
related_experiences: []
details:
  project_pitch: 割草机户外实时定位：在 STM32上通过扩展卡尔曼滤波将UWB、IMU 与轮式里程计多传感融合。
  personal_contribution: 本科毕设，独立完成全流程——EKF 融合算法实现、基站丢失自适应设计提高系统鲁棒性、MATLAB 上位机与真实草坪实车测试。
  project_outcome: 相较单 UWB，RMSE 降低 28.86%（当次测试）；关闭 2/4 基站仍持续定位，恢复后误差重新收敛；完成实车现场测试。
  hr_intro: ''
---

# 割草机多传感器融合定位导航系统

## 项目概述
本科毕设，独立完成：在 STM32F407 上融合 4 个 UWB 基站、IMU 与轮式里程计实现 EKF 实时定位；相较单 UWB 方案 RMSE 降低 28.86%（当次测试），关闭一半基站仍能持续定位，并在真实草坪完成实车测试。

## 事实记录
- 独立完成方案设计、底层通信、融合算法、上位机工具与户外实车测试全流程。
- 用 C 在 STM32F407 上实现 EKF：IMU/里程计做状态预测、UWB 测距做量测更新，含非线性量测方程、雅可比矩阵与坐标系自动对齐；设计多路 UART 协议解析，接入 4 基站 + IMU + 里程计。
- 设计基站信号丢失自适应（按信号状态动态调整量测噪声协方差）：关闭 2/4 基站仍持续输出定位，恢复后误差重新收敛。
- 用 MATLAB App Designer 开发 UWB 观测与 EKF 对比工具（串口读取、轨迹对比、在线调参），完成真实草坪现场测试与演示。

## 量化成果
- 相比单 UWB，融合后 RMSE 记录降低 28.86%，MAE 降低 23.14%。
- EKF 融合后 RMSE 记录范围为 0.0336–0.0545 m。
- 关闭 2/4 个 UWB 基站后仍可持续定位，基站恢复后误差重新收敛。
- 记录的室外测试区域约 17.42 m × 10.76 m。

## Notes
