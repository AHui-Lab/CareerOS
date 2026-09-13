---
schema_version: 1
id: internship-nanjing-metrology
type: internship
title: 南京市计量监督检测院 · 嵌入式系统开发与动作识别算法开发
organization: 南京市计量监督检测院
role: 嵌入式系统开发与动作识别算法开发
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
updated_at: 2026-09-14T02:43:26+08:00
migration_source: AHui-Lab/Resume
migration_review: completed
source_confidence: high
source_paths:
- 南京市计量监督检测院/南京市计量监督检测院实习.md
- 南京市计量监督检测院/032030121曹宇辉实习报告.docx
- Resume.md
migration_reviewed_at: 2026-08-22T01:09:19+08:00
related_experience_ids:
- 社团管理部活动中心主任
related_experiences:
- id: 社团管理部活动中心主任
  title: 社团管理部活动中心主任
  type: campus
details:
  department: ''
  internship_type: ''
---

# 南京市计量监督检测院 · 嵌入式系统开发与动作识别算法开发

## 项目概述
为上肢缺失人士做足部辅助交互原型：接入 9 路九轴 IMU，独立开发 MATLAB 上位机与动作识别，实现足部旋转、单击等 4 类动作，产出实物原型。

## 事实记录
- 搭建 9 路九轴 IMU 足部姿态采集链路：多路串口实时读取脚后跟、脚背、脚趾姿态数据，完成分帧、解析与数值化。
- 独立开发 MATLAB 上位机：多路数据实时读取、姿态角动态显示、识别结果可视化。
- 基于脚后跟滚转角与脚背/脚趾俯仰角构建规则型识别，实现足部内外旋、单击、脚趾抬起、弯曲 4 类动作。
- 设计静态零点校准处理姿态漂移与佩戴差异，提高不同用户、不同佩戴条件下的识别稳定性。

## 量化成果
- 接入 9 路九轴惯性传感器，实现 4 类足部动作识别，产出可运行实物原型。

## Notes
迁移以详细 Markdown 实习记录为事实主来源；DOCX 实习报告作为证据文件来源路径保留，当前迁移分支不复制二进制附件。
