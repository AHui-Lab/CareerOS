# 2027届秋招-室内定位算法工程师笔试题库

> **整体说明：** 来源为考试界面截图整理。图中绿色高亮为考试时选中项，不等于官方答案；答案与解析由整理者根据领域知识补写。考查重点：多模态时序对齐与融合、实时信号处理（因果滤波）、深度学习时序建模、室内定位（Wi-Fi/气压/PDR）、评估与实验设计、缺失值处理。

---

## 一、选择题

### 第1题（单选题）
**题目：** 关于气压计用于室内楼层判定，下列说法正确的是（ ）

**选项：**
- A. 气压随高度升高而降低（约 12 Pa/m），可据此判楼层，但需结合天气漂移校准并采用相对高度基准
- B. 气压计读数与楼层判定完全无关
- C. 气压随高度升高而升高
- D. 气压与高度无关，无法用于楼层判定

**答案：A**

**解析：** 大气压随高度近似以约 12 Pa/m（或 1 hPa / 8.3 m）递减，可换算相对高度用于楼层判定；但天气系统也会引起气压漂移，需做时间上的基线校准，并以相对高度而非绝对气压为准。

---

### 第2题（单选题）
**题目：** 开发手表端实时 PPG 推理流程时，工程师准备使用 scipy.signal.filtfilt 做零相位滤波。关于该选择，正确的是？

**选项：**
- A. filtfilt 与 lfilter 完全等价，只是函数名不同
- B. filtfilt 会使用未来样本；实时场景应改用因果滤波并维护状态
- C. 只要窗口长度固定，filtfilt 就不会使用未来样本
- D. filtfilt 只使用历史样本，因此天然适合在线推理

**答案：B**

**解析：** filtfilt 做前后向双向滤波以实现零相位，本质上使用了整段（含"未来"）样本，是非因果的，只适合离线处理。实时推理应使用 lfilter/sosfilt 等因果滤波器并维护滤波器状态。

---

### 第3题（单选题）
**题目：** 多模态时序统计分析中伪相关现象的产生原因是？

**选项：**
- A. 无真实因果，但存在共同时间趋势
- B. 采样频率过高
- C. 数据完全平稳
- D. 信号信噪比过高

**答案：A**

**解析：** 伪相关（spurious correlation）常见原因是两个序列本身无因果关系，却因共享时间趋势/非平稳性而表现出高相关。采样率、平稳性、SNR 都不是伪相关的典型成因。

---

### 第4题（单选题）
**题目：** Which method can solve the asynchronous sampling problem of multimodal time series?

**选项：**
- A. One-hot encoding
- B. Feature normalization
- C. Gradient clipping
- D. Resampling and linear interpolation

**答案：D**

**解析：** 多模态时序各传感器采样率/时刻不同（异步采样），标准做法是统一时间轴后重采样并插值（如线性插值）。One-hot、归一化、梯度裁剪都不解决时间对齐问题。

---

### 第5题（单选题）
**题目：** When fusing multimodal time series at the feature level, we most commonly:

**选项：**
- A. Combine learned latent representations extracted from each modality
- B. Upsample all raw time series to 1Hz before fusion
- C. Directly average the final prediction scores of separate single-modal models
- D. Concatenate raw sensor signals before model input

**答案：A**

**解析：** 特征级融合（feature-level / intermediate fusion）是在各模态编码器提取的隐层表示上做拼接/注意力融合。C 是决策级融合，D 更接近数据级拼接，B 只是重采样不是融合。

---

### 第6题（单选题）
**题目：** 手表端要实时利用加速度和陀螺仪进行行人航位推算。关于 scipy.signal.filtfilt 与在线滤波，哪项说法正确？

**选项：**
- A. 先反转时间序列再调用 filtfilt，并将反向结果视为严格的在线因果输出
- B. 随机打乱窗口内样本再做低通滤波，并将滤波输出视为严格实时因果结果
- C. 使用 sosfilt 或 lfilter，在相邻数据块之间连续维护状态
- D. 每个窗口调用 filtfilt，并将窗口之后的样本视为可用的历史传感器数据

**答案：C**

**解析：** 实时 PDR 需要因果滤波。sosfilt/lfilter 是因果 IIR/FIR 实现；分块处理时用 `zi`/`sosfilt_zi` 跨块延续状态，才能保证滤波连续且不偷看未来。filtfilt 非因果，A/B/D 的做法都会破坏实时因果性。

---

### 第7题（单选题）
**题目：** 手表以不同频率采集 Wi-Fi RSSI、BLE RSSI、IMU 和气压，并且存在时间抖动。构建统一的 50 Hz 多模态序列时，最合理的处理是？

**选项：**
- A. 建立统一时间轴，按真实时间戳重采样并选择合适的插值策略
- B. 随机重复低频模态的样本，直到各模态拥有相同的样本行数
- C. 截断到最短模态的样本数，再依据原始数组行号直接完成拼接
- D. 分别按传感器数值排序，再依据排序后的行号完成跨模态拼接

**答案：A**

**解析：** 不同频率 + 时间抖动时必须以真实时间戳对齐：建立 50 Hz 时间网格后按戳重采样，对 IMU/气压等选择合适插值（如线性/保持）。B 破坏时间结构，C 忽略真实时间，D 用数值排序彻底打乱时序。

---

### 第8题（单选题）
**题目：** 使用多位用户的手表数据训练活动识别模型，同一用户会产生大量重叠窗口。若目标是评估对新用户的泛化能力，正确方法是？

**选项：**
- A. 把所有窗口打乱后用 train_test_split 随机划分
- B. 先用全部用户拟合标准化器，再随机划分窗口
- C. 把每位用户的偶数窗口用于训练、奇数窗口用于验证
- D. 使用 GroupKFold，并将 user_id 作为 groups

**答案：D**

**解析：** 同一用户的重叠窗口高度相关，随机划分会造成泄漏，无法评估对新用户的泛化。GroupKFold 以 user_id 分组，保证同一用户的所有窗口不跨训练/验证集。标准化器也应在训练折上拟合。

---

### 第9题（单选题）
**题目：** 时序差分法对多模态时序数据预处理的核心作用是？

**选项：**
- A. 将非平稳时序转化为平稳时序
- B. 提取时频特征
- C. 填充时序缺失数据
- D. 消除量纲差异

**答案：A**

**解析：** 差分（differencing）通过相邻时刻作差去除趋势/低频漂移，是把非平稳序列转化为平稳序列的经典手段。时频特征对应小波/STFT，缺失填充是 imputation，量纲差异由标准化处理。

---

### 第10题（单选题）
**题目：** 多模态时序数据 Z-score 标准化的核心目的是？

**选项：**
- A. 滤除环境采集噪声
- B. 实现时序数据平稳化
- C. 补齐时序缺失样本
- D. 消除传感器量纲差异，统一数据分布

**答案：D**

**解析：** Z-score 标准化（减均值除标准差）把不同量纲/尺度的传感器特征拉到相近分布，便于模型训练与融合。它不滤噪声、不平稳化（那是差分的作用）、不填补缺失。

---

### 第11题（单选题）
**题目：** 在多模态时间序列任务中，早融合（Early Fusion）的核心定义是？

**选项：**
- A. 模型输入阶段合并原始信号或底层特征
- B. 筛选最优单模态信号完成预测
- C. 输出层加权融合各模态预测概率
- D. 各模态单独训练模型，最终融合预测结果

**答案：A**

**解析：** Early Fusion 在输入层或底层特征就进行合并，让统一模型学习跨模态交互。C/D 描述的是 late fusion（决策级融合），B 是单模态选择而非融合。

---

### 第12题（单选题）
**题目：** 多模态时序融合中"特征级融合"（feature-level fusion）的典型含义是？

**选项：**
- A. 先将各模态特征拼接后统一输入模型学习
- B. 将各模态信号拼接为一维序列后直接输入模型
- C. 分别用单模态模型输出预测结果，再对结果投票
- D. 将多个模态结果拼接为一维序列后输入

**答案：A**

**解析：** 特征级融合是把各模态提取的特征向量拼接/对齐后送入后续网络联合学习。B 更像数据级原始拼接，C 是决策级融合，D 表述含糊且不典型。

---

### 第13题（单选题）
**题目：** PPG、加速度计和陀螺仪均出现缺失的多模态时序，如果要评估模型在"任一模态缺失"条件下的鲁棒性，最合适的实验设计是？

**选项：**
- A. 训练时随机丢弃不同模态，并在各缺失模态组合条件下分别评测
- B. 删除全部存在缺失值的窗口，只报告完整数据上的结果
- C. 仅在训练集上报告完整模态结果
- D. 将所有缺失值设为 0 后只测试完整模态场景

**答案：A**

**解析：** 评估缺失鲁棒性需要在训练中模拟缺失（modality dropout 等），并在多种缺失组合的测试子集上分别报告指标。B/C/D 都回避了缺失场景，无法回答鲁棒性问题。

---

### 第14题（单选题）
**题目：** For wearable multimodal time series with missing values, what is a key advantage of multimodal imputation?

**选项：**
- A. It can exploit correlations across different signal modalities
- B. It removes the need for any sensor calibration
- C. It makes the sampling frequencies of all sensors equal
- D. It guarantees zero imputation error under all conditions

**答案：A**

**解析：** 多模态填补的核心优势是利用模态间相关性（如加速度辅助 PPG 缺失段的估计）。它不能免除标定、不统一采样率，更不能保证零误差。

---

### 第15题（单选题）
**题目：** 当两种模态彼此高度冗余时，早期融合通常会带来什么影响？

**选项：**
- A. 使推理复杂度降至单模态基线以下
- B. 对模型性能没有任何影响
- C. 无法再利用时间戳进行对齐
- D. 引入冗余或共线性，可能使模型难以确定各模态贡献

**答案：D**

**解析：** 高度冗余的模态在输入层直接拼接会放大共线性，使优化不稳定、特征贡献难以解释。复杂度通常上升而非下降，性能一般也会受影响。

---

### 第16题（单选题）
**题目：** Which evaluation metric is extremely sensitive to outliers in multimodal time series forecasting?

**选项：**
- A. RMSE
- B. Pearson correlation coefficient
- C. Accuracy
- D. MAE

**答案：A**

**解析：** RMSE 对误差平方后再平均，离群点会被放大，因此对异常值最敏感。MAE 是绝对误差，稳健得多；相关系数和准确率也不按此方式受离群点支配。

---

### 第17题（单选题）
**题目：** 一维 CNN 中，kernel_size=3 的卷积层在步幅为 1 时，捕获局部信息的长度（感受野）是多少个时间步？

**选项：**
- A. 5
- B. 1
- C. 3
- D. 2

**答案：C**

**解析：** 单层卷积的感受野等于卷积核大小。kernel_size=3 时每个输出对应连续 3 个时间步的输入，与步幅在单层情形下无关。

---

### 第19题（单选题）
**题目：** Granger causality test for multimodal time series is essentially based on which logic?

**选项：**
- A. Historical information of one modality improves the prediction of another
- B. Gaussian distribution of data
- C. Consistency of signal sampling frequency
- D. Signal amplitude similarity

**答案：A**

**解析：** Granger 因果的定义是：若加入序列 X 的历史信息后对序列 Y 的预测显著优于只用 Y 自身历史，则称 X Granger-cause Y。本质是预测能力的增量，而非分布、采样率或幅值相似性。

---

### 第20题（单选题）
**题目：** Multimodal imputation for time series with missing values mainly relies on which core advantage?

**选项：**
- A. Complementary information between different signal modalities
- B. Zero noise of sensor acquisition
- C. Fixed stationary distribution of raw signals
- D. Unified sampling frequency of all modalities

**答案：A**

**解析：** 与第14题同考点：多模态填补依赖模态间互补信息重建缺失段，而不是"零噪声/平稳分布/统一采样率"这些不成立的假设。

---

### 第21题（单选题）
**题目：** 对形状为 (B, C, T) 的在线腕带信号使用 kernel_size=k、padding=0 的 nn.Conv1d。若要求时刻 t 的输出不能看到 t 之后的数据，以下写法正确的是？

**选项：**
- A. y = conv(F.pad(x, (k-1, k-1)))
- B. y = conv(torch.flip(x, dims=[-1]))
- C. y = conv(F.pad(x, (k-1, 0)))
- D. y = conv(F.pad(x, (0, k-1)))

**答案：C**

**解析：** 因果卷积只需在左侧（过去方向）补 k-1 个零/重复，右侧不补，这样每个输出只依赖当前及过去。A 是对称 pad（非因果），D 在右侧补会看到"未来"，B 翻转破坏时序。

---

### 第22题（单选题）
**题目：** 定位网络输出 logits，形状为 (B,M)，coords 保存 M 个网格中心坐标，形状为 (M,2)。若希望用可微 soft-argmax 得到 (B,2) 坐标，应使用？

**选项：**
- A. p = torch.softmax(logits, dim=1), xy = p @ coords
- B. xy = coords.mean(dim=0).expand(logits.size(0), 2)
- C. p = torch.softmax(logits, dim=0), xy = p @ coords
- D. xy = coords[logits.argmax(dim=1)]

**答案：A**

**解析：** soft-argmax 对 M 个网格的 logits 在类别维（dim=1）做 softmax 得到概率，再与坐标矩阵 (M,2) 加权求和得到 (B,2)。C 在 batch 维 softmax 是错的；D 是硬 argmax 不可微；B 与 logits 无关。

---

### 第23题（单选题）
**题目：** 室内不同位置可扫描到的 Wi-Fi AP 集合不同。为了把每个时刻的 RSSI 输入固定维度模型，以下表示方法最合理的是？

**选项：**
- A. 每个窗口按 RSSI 排序，删除 AP 标识并仅保留排名靠前的若干数值
- B. 使用整个数据集的均值填充缺失 RSSI，但不提供任何可见性信息
- C. 遇到任一 AP 未扫描到时，删除该窗口以及同时采集的传感器数据
- D. 建立固定 AP 字典，缺失 RSSI 填噪声底并添加对应的可见性掩码

**答案：D**

**解析：** 固定 AP 字典保证维度对齐；缺失填噪声底（如 -100 dBm）并用可见性 mask 显式告知模型"未观测到"，既保维度又保留信息。A 丢掉 AP 身份，B 抹掉可见性差异，C 造成样本浪费与偏差。

---

### 第24题（单选题）
**题目：** For time-series modality with non-stationary statistics, which method can effectively stabilize data distribution?

**选项：**
- A. Time series differencing
- B. Max-min scaling
- C. One-hot encoding
- D. Z-score normalization

**答案：A**

**解析：** 差分去除趋势/单位根，使统计特性更平稳。Min-max 与 Z-score 只是缩放不改变平稳性；One-hot 是类别编码，与平稳化无关。

---

### 第27题（单选题）
**题目：** 评估智能通讯手表室内导航模型时，哪种测试设计与指标组合最能反映真实部署表现？

**选项：**
- A. 按用户或区域分组隔离，并报告 ADE、FDE、楼层准确率和到达成功率
- B. 将同一轨迹混入训练测试两侧，并报告终点误差、楼层准确率、召回率和成功率
- C. 反复使用测试集调整阈值，并报告测试准确率、F1、定位误差与最终训练损失
- D. 随机拆分重叠窗口，并报告窗口准确率、召回率、平均定位误差和楼层准确率

**答案：A**

**解析：** 真实部署要求泛化到新用户/新区域，因此按用户或区域分组隔离评估。ADE/FDE 反映轨迹质量，楼层准确率与到达成功率对齐产品目标。B/D 存在泄漏，C 用测试集调参属于过拟合测试集。

---

### 第28题（单选题）
**题目：** 批次中序列最大长度为 T，lengths 保存各样本真实长度。PyTorch MultiheadAttention 的 key_padding_mask 中 True 表示忽略该位置。以下构造方式正确的是？

**选项：**
- A. mask = torch.arange(T, device=lengths.device)[None, :] < lengths[:, None]
- B. mask = lengths == T
- C. mask = torch.ones(T, T, dtype=torch.bool)
- D. mask = torch.arange(T, device=lengths.device)[None, :] >= lengths[:, None]

**答案：D**

**解析：** key_padding_mask 中 True 表示该位置是 padding、需要忽略。位置索引 i >= 真实长度 lengths[b] 的位置才是 padding，故用 `>=` 构造。A 得到的是"有效位置"掩码（语义相反）；B/C 形状或语义都不对。

---

### 第29题（单选题）
**题目：** 在大量无标签手表导航轨迹上进行跨模态对比学习时，以下哪种正样本构造最合理？

**选项：**
- A. 不同用户任意轨迹的 BLE 与气压窗口，不要求时间同步或位置接近
- B. 同一手表同一时段的同步模态，或同一窗口经过两种合理增强后的数据视图
- C. 同一窗口中分别随机打乱时间顺序的 RSSI 与航向序列再进行配对
- D. 同一建筑任意时段的 Wi-Fi 与 IMU 窗口，不要求时间同步或位置接近

**答案：B**

**解析：** 跨模态对比学习的正样本必须对应同一时空语义：同步采集的不同模态，或同一窗口的两种增强视图。A/D 缺乏时空对应会引入假正样本；C 打乱时序破坏语义。

---

### 第30题（单选题）
**题目：** 一批导航序列补齐到长度 T，真实长度为 lengths。PyTorch MultiheadAttention 的 key_padding_mask 中 True 表示忽略该位置。正确构造方式是？

**选项：**
- A. mask = torch.arange(T)[None, :] < lengths[:, None]
- B. mask = torch.arange(T)[None, :] != lengths[:, None]
- C. mask = torch.arange(T)[None, :] == lengths[:, None]
- D. mask = torch.arange(T)[None, :] >= lengths[:, None]

**答案：D**

**解析：** 与第28题同考点：True 表示该位置被忽略（padding）。索引 i >= 真实长度 lengths[b] 的位置才是 padding。A 给出的是有效位置掩码（语义相反）；B/C 只标记边界点，无法覆盖整段 padding。

---

### 第31题（单选题）
**题目：** 同一用户的一条室内导航轨迹被切成大量重叠窗口。若要评估模型对新用户和新轨迹的泛化能力，以下划分方式最合适的是？

**选项：**
- A. 把每条轨迹的奇数窗口用于训练，偶数窗口用于测试
- B. 按用户或完整轨迹会话分组，使同一组不跨数据子集
- C. 先利用全部轨迹拟合预处理器，再随机划分各个窗口
- D. 随机打乱全部窗口，再按窗口比例划分训练集和测试集

**答案：B**

**解析：** 重叠窗口高度相关，必须按用户或完整轨迹会话分组隔离，才能评估对新用户/新轨迹的泛化。A/C/D 都会把高度相关的窗口拆到训练与测试两侧，造成信息泄漏。

---

### 第32题（单选题）
**题目：** 智能戒指在佩戴松动时会产生间歇性 PPG 缺失。为了让模型区分"真实零值"和"缺失后填充值"，以下处理方式正确的是？

**选项：**
- A. 删除所有包含任意缺失点的窗口
- B. 利用测试集标签选择使验证精度最高的填充值
- C. 用训练集确定的规则填补，并增加观测掩码或距上次观测的时间间隔特征
- D. 把所有 NaN 直接替换为 0，且不增加任何额外特征

**答案：C**

**解析：** 必须显式提供缺失指示（mask 或 time-since-last-observed），模型才能区分真实零与填补值。填补规则只能在训练集上确定，避免泄漏。A 丢样本，B 用测试集标签是泄漏，D 会把缺失与真实零混淆。

---

### 第33题（单选题）
**题目：** What is the main purpose of modality dropout in wearable multimodal signal classification?

**选项：**
- A. Force the model to learn complementary features of heart rate and motion modalities
- B. Calibrate sensor sampling frequency deviation
- C. Shorten the length of physiological time series
- D. Eliminate high-frequency noise of watch acceleration signals

**答案：A**

**解析：** Modality dropout 在训练中随机丢弃整条模态通道，迫使模型学习各模态的互补表征、提升缺失鲁棒性。它与采样率校准、序列缩短、高频噪声去除无关。

---

### 第34题（单选题）
**题目：** 多模态时序长距离依赖建模中最优的模块是？

**选项：**
- A. 自注意力机制
- B. 基础循环神经网络
- C. 最大池化
- D. 一维卷积

**答案：A**

**解析：** 自注意力（Transformer）可直接建模任意距离的依赖，且并行度高。基础 RNN 有长程梯度问题；池化和一维卷积感受野有限，长距离依赖需堆叠很多层。

---

### 第36题（单选题）
**题目：** 粒子滤波中 w 是已归一化权重，N 是粒子数，cdf=np.cumsum(w)，u0=np.random.rand()/N。哪段代码实现系统重采样索引计算？

**选项：**
- A. u=np.random.rand(N)*N; idx=np.searchsorted(w,u)
- B. u=u0+np.arange(N)/N; idx=np.searchsorted(cdf,u)
- C. u=np.linspace(0,1,N); idx=np.argsort(cdf)[:N]
- D. u=u0+np.arange(N)/N; idx=np.argsort(w)

**答案：B**

**解析：** 系统重采样（systematic resampling）的阈值为 u_i = u0 + i/N，在权重 CDF 上 searchsorted 得到索引。A 是多项式重采样；C 的 linspace/argsort 不构成系统重采样；D 对权重排序而非按 CDF 抽样。

---

### 第37题（单选题）
**题目：** 一维卷积神经网络（1D-CNN）处理多模态时序，擅长提取哪类特征？

**选项：**
- A. 局部时序窗口内的短时特征
- B. 时序缺失值
- C. 跨模态因果关系
- D. 超长距离全局时序依赖

**答案：A**

**解析：** 1D-CNN 的卷积核在时间维滑动，擅长提取局部短时模式（波形、峰谷、短节律）。缺失填补、因果推断、超长程依赖都不是 CNN 的主要能力。

---

### 第38题（单选题）
**题目：** 智能通讯手表的 Wi-Fi、IMU 和气压序列已对齐，编码后张量形状分别为 (B, T, 16)、(B, T, 6) 和 (B, T, 1)。调用 torch.cat([wifi, imu, baro], dim=-1) 后的形状是？

**选项：**
- A. (B, 23, T)，特征维移动到时间维之前
- B. (B, T, 16)，只保留 Wi-Fi 的原有维度
- C. (T, B, 23)，时间维移动到批次维之前
- D. (B, T, 23)，批次维和时间维保持不变

**答案：D**

**解析：** torch.cat 在 dim=-1（最后一维，特征维）拼接：16+6+1=23，批次维 B 与时间维 T 保持不变，得到 (B, T, 23)。

---

### 第39题（单选题）
**题目：** Compared with early fusion, the core advantage of late fusion for multimodal time series is

**选项：**
- A. Stronger robustness to single-modal noise
- B. Better performance on small sample datasets
- C. No need for independent feature extraction
- D. Higher utilization of fine-grained temporal alignment

**答案：A**

**解析：** 晚期融合各模态独立建模后再融合决策，单一模态噪声/失效不易污染其他模态，因此对单模态噪声更稳健。早期融合才更依赖细粒度时间对齐；C 与晚融合相反（恰恰需要独立特征提取）；小样本并非晚融合的核心优势。

---

### 第40题（单选题）
**题目：** Which of the following belongs to unsupervised statistical analysis method for multimodal time series dimensionality reduction?

**选项：**
- A. LSTM
- B. Transformer
- C. SVM
- D. PCA

**答案：D**

**解析：** PCA 是经典的无监督降维/统计分析方法。LSTM/Transformer 是有监督或自监督的序列模型，SVM 是有监督分类器。

---
