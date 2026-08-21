---
schema_version: 1
id: stm32-mower-sensor-fusion
type: project
title: 基于 STM32 的割草机多传感器组合定位系统
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
updated_at: 2026-08-22T01:27:15+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 本科毕设/本科毕设.md
- Resume.md
migration_reviewed_at: 2026-08-22T01:27:09+08:00
---

# 基于 STM32 的割草机多传感器组合定位系统

## 项目概述
独立设计并实现基于 STM32F407 的 UWB / IMU / ODOM 多传感器组合定位系统，覆盖硬件集成、串口协议解析、EKF 嵌入式实现、MATLAB 上位机与室外实验验证。

## 事实记录
- 集成 STM32F407 主控、UWB 定位、IMU 惯导和轮式里程计，设计多路 UART 数据通信与协议解析。
- 在 STM32 上实现EKF（扩展卡尔曼滤波），将 UWB 测距作为量测、IMU/ODOM 航迹推算作为状态预测，并处理非线性量测方程与雅可比矩阵计算。
- 使用 C 语言自建矩阵加减乘、转置、求逆等运算模块，并处理嵌入式动态内存管理。
- 设计基站信号丢失自适应机制，根据信号状态调整量测噪声协方差矩阵 R；在部分 UWB 基站失效时维持定位输出，恢复后重新收敛。
- 设计车身坐标系与 UWB 全局坐标系自动对齐机制，用于降低任意初始摆放造成的偏航偏差。
- 使用 MATLAB AppDesigner 开发 UWB 数据实时观测和 EKF 效果对比工具，支持串口读取、轨迹对比、在线调参和数据存储。

## 量化成果
- 相比单 UWB，融合后 RMSE 记录降低 28.86%，MAE 降低 23.14%。
- EKF 融合后 RMSE 记录范围为 0.0336–0.0545 m。
- 关闭 2/4 个 UWB 基站后仍可持续定位，基站恢复后误差重新收敛。
- 记录的室外测试区域约 17.42 m × 10.76 m。

## Notes
`本科毕设 1.md` 与 `本科毕设.md` 内容 SHA 相同，迁移时已去重。原文中的“与求职方向关联”“体现能力”等总结未作为独立事实导入。
