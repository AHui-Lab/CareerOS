# 室内定位算法笔试（提取中间稿）

来源：C:\Users\cyh\Desktop\questionXTC
说明：图中绿色高亮为考试时选中项，不等于官方答案；答案/解析由整理者补写。

## 已识别题目

### 第1题（单选题）
**题目：** 关于气压计用于室内楼层判定，下列说法正确的是（ ）

**选项：**
- A. 气压随高度升高而降低（约 12 Pa/m），可据此判楼层，但需结合天气漂移校准并采用相对高度基准
- B. 气压计读数与楼层判定完全无关
- C. 气压随高度升高而升高
- D. 气压与高度无关，无法用于楼层判定

**答案：** A

**解析：** 大气压随高度近似以约 12 Pa/m（或 1 hPa/8.3 m）递减，可换算相对高度用于楼层判定；但天气系统也会引起气压漂移，需做时间上的基线校准，并以相对高度而非绝对气压为准。

**来源图片：** 3d166d7e4c1b3f4af0126418bfa263aa.jpg
**图中选中：** 无

---

### 第2题（单选题）
**题目：** 开发手表端实时 PPG 推理流程时，工程师准备使用 scipy.signal.filtfilt 做零相位滤波。关于该选择，正确的是？

**选项：**
- A. filtfilt 与 lfilter 完全等价，只是函数名不同
- B. filtfilt 会使用未来样本；实时场景应改用因果滤波并维护状态
- C. 只要窗口长度固定，filtfilt 就不会使用未来样本
- D. filtfilt 只使用历史样本，因此天然适合在线推理

**答案：** B

**解析：** filtfilt 做前后向双向滤波以实现零相位，本质上使用了整段（含“未来”）样本，是非因果的，只适合离线处理。实时推理应使用 lfilter/sosfilt 等因果滤波器并维护滤波器状态。

**来源图片：** d3fb85f2e8e72813e6f2a79d1bb87d16.jpg
**图中选中：** 无

---

### 第3题（单选题）
**题目：** 多模态时序统计分析中伪相关现象的产生原因是？

**选项：**
- A. 无真实因果，但存在共同时间趋势
- B. 采样频率过高
- C. 数据完全平稳
- D. 信号信噪比过高

**答案：** A

**解析：** 伪相关（spurious correlation）常见原因是两个序列本身无因果关系，却因共享时间趋势/非平稳性而表现出高相关。采样率、平稳性、SNR 都不是伪相关的典型成因。

**来源图片：** 714e12cbe4d9fa4411729014f736e2b9.jpg
**图中选中：** B（考试界面高亮，疑为误选）

---

### 第4题（单选题）
**题目：** Which method can solve the asynchronous sampling problem of multimodal time series?

**选项：**
- A. One-hot encoding
- B. Feature normalization
- C. Gradient clipping
- D. Resampling and linear interpolation

**答案：** D

**解析：** 多模态时序各传感器采样率/时刻不同（异步采样），标准做法是统一时间轴后重采样并插值（如线性插值）。One-hot、归一化、梯度裁剪都不解决时间对齐问题。

**来源图片：** 03834b9acb32578c66a1d0edf7f766de.jpg
**图中选中：** 无

---

### 第5题（单选题）
**题目：** When fusing multimodal time series at the feature level, we most commonly:

**选项：**
- A. Combine learned latent representations extracted from each modality
- B. Upsample all raw time series to 1Hz before fusion
- C. Directly average the final prediction scores of separate single-modal models
- D. Concatenate raw sensor signals before model input

**答案：** A

**解析：** 特征级融合（feature-level / intermediate fusion）是在各模态编码器提取的隐层表示上做拼接/注意力融合。C 是决策级融合，D 更接近数据级拼接，B 只是重采样不是融合。

**来源图片：** 53e15ae47de2f199bb49d36448bba312.jpg
**图中选中：** 无

---

### 第6题（单选题）
**题目：** 手表端要实时利用加速度和陀螺仪进行行人航位推算。关于 scipy.signal.filtfilt 与在线滤波，哪项说法正确？

**选项：**
- A. 先反转时间序列再调用 filtfilt，并将反向结果视为严格的在线因果输出
- B. 随机打乱窗口内样本再做低通滤波，并将滤波输出视为严格实时因果结果
- C. 使用 sosfilt 或 lfilter，在相邻数据块之间连续维护状态
- D. 每个窗口调用 filtfilt，并将窗口之后的样本视为可用的历史传感器数据

**答案：** C

**解析：** 实时 PDR 需要因果滤波。sosfilt/lfilter 是因果 IIR/FIR 实现；分块处理时用 `zi`/`sosfilt_zi` 跨块延续状态，才能保证滤波连续且不偷看未来。filtfilt 非因果，A/B/D 的做法都会破坏实时因果性。

**来源图片：** 4c22d7d7e83afe9b02c40136d761cd37.jpg
**图中选中：** 无

---

### 第7题（单选题）
**题目：** 手表以不同频率采集 Wi-Fi RSSI、BLE RSSI、IMU 和气压，并且存在时间抖动。构建统一的 50 Hz 多模态序列时，最合理的处理是？

**选项：**
- A. 建立统一时间轴，按真实时间戳重采样并选择合适的插值策略
- B. 随机重复低频模态的样本，直到各模态拥有相同的样本行数
- C. 截断到最短模态的样本数，再依据原始数组行号直接完成拼接
- D. 分别按传感器数值排序，再依据排序后的行号完成跨模态拼接

**答案：** A

**解析：** 不同频率 + 时间抖动时必须以真实时间戳对齐：建立 50 Hz 时间网格后按戳重采样，对 IMU/气压等选择合适插值（如线性/保持）。B 破坏时间结构，C 忽略真实时间，D 用数值排序彻底打乱时序。

**来源图片：** 9968ebff8be2fb7f512f688ee7975b81.jpg（另有重复截图 b28bba122b0f5c81b4a85465a8eec397.jpg）
**图中选中：** A（与参考答案一致）

---
