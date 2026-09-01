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
updated_at: 2026-08-27T08:36:31+08:00
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
  project_role: ''
---

# 割草机多传感器融合定位导航系统

## 项目概述
面向割草机户外自主移动场景，基于 STM32F407 融合4个UWB基站、IMU和轮式里程计，实现多传感器定位系统。使用C语言在MCU端实现EKF，以IMU/里程计进行状态预测、UWB测距进行量测更新，并完成UART协议解析、矩阵运算、雅可比矩阵及坐标系自动对齐。相较单UWB方案，融合后RMSE降低28.86%、MAE降低23.14%，测试区域内RMSE为0.0336–0.0545 m；关闭2/4个基站后仍可持续定位，基站恢复后误差重新收敛。配套开发MATLAB数据观测与轨迹对比工具，并完成真实草坪环境下的割草机现场测试。

## 事实记录
面向割草机户外自主移动场景，基于 STM32F407 融合 UWB、IMU 和轮式里程计，实现复杂环境下的实时定位与异常信号容错。
- 独立完成系统总体方案、底层通信、融合算法、上位机工具及户外实车测试，完成可运行的割草机定位系统。
- 集成 4个 UWB 基站、IMU 惯导及轮式里程计，设计 STM32 端多路 UART 通信与协议解析模块，实现多源传感器数据实时接入。
- 使用 C 语言在 STM32F407 上实现扩展卡尔曼滤波（EKF），以 IMU/里程计进行状态预测、UWB 测距进行量测更新，完成非线性量测方程、雅可比矩阵及矩阵运算模块。
- 相较单 UWB 定位方案，融合后 RMSE 降低28.86%，MAE降低23.14%；在户外约 17.42 m × 10.76 m 测试区域内，EKF 融合定位 RMSE 记录范围为 0.0336–0.0545 m。
- 设计 UWB 基站信号丢失自适应机制，根据信号状态动态调整量测噪声协方差矩阵 R；关闭4个基站中的2个时系统仍可持续输出定位结果，基站恢复后误差重新收敛。
- 设计车身坐标系与 UWB 全局坐标系自动对齐机制，降低割草机初始摆放方向不确定造成的偏航误差。
- 使用 MATLAB App Designer 开发 UWB 数据观测及 EKF 效果对比工具，支持串口读取、轨迹对比、在线调参和数据存储，并完成真实草坪环境下的现场测试与演示。

## 量化成果
- 相比单 UWB，融合后 RMSE 记录降低 28.86%，MAE 降低 23.14%。
- EKF 融合后 RMSE 记录范围为 0.0336–0.0545 m。
- 关闭 2/4 个 UWB 基站后仍可持续定位，基站恢复后误差重新收敛。
- 记录的室外测试区域约 17.42 m × 10.76 m。

## Notes
