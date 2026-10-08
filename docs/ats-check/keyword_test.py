# -*- coding: utf-8 -*-
"""模拟 ATS 关键词检索：检查关键词在原文/去空白文本中是否命中"""
import fitz, re

doc = fitz.open(r"C:\CareerOS\docs\曹宇辉_简历.pdf")
t = doc[0].get_text("text")
t2 = re.sub(r"\s+", "", t)  # 去掉所有空白后再匹配（宽松模式）

kws = ["嵌入式","ARM","STM32","C语言","Python","MATLAB","PCB","EDA",
       "卡尔曼","EKF","BLE","蓝牙","UWB","IMU","传感器","Unity","Git",
       "Linux","RAG","Langchain","测试","晶圆","半导体","检测","算法"]

only_after_strip = []
missing = []
for k in kws:
    raw_hit = k in t
    hit = k in t2
    if not hit:
        missing.append(k)
    elif not raw_hit:
        only_after_strip.append(k)

print("命中关键词:", [k for k in kws if k in t2])
print("仅去空白后命中(原文被空格打断):", only_after_strip)
print("完全未命中:", missing)

# 额外检查：中英文之间插入空格的实例（Word 排版空隙，可能打断关键词）
m = re.findall(r"[A-Za-z0-9]+ \s*[\u4e00-\u9fff]|[\u4e00-\u9fff] [A-Za-z0-9]+", t)
artifacts = re.findall(r"[\u4e00-\u9fff] [、，。；：（）]", t) + re.findall(r"[、，。；] ", t)
print("中文标点前异常空格示例:", artifacts[:10])
