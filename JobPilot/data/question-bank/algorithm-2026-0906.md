# 算法笔试题库（2026年9月6日）

---

## 一、选择题

### 1. 冒泡排序

**题目：** 对序列进行冒泡排序，第2趟排序后的结果为？

**选项：**
- A. 78, 66, 12, 27, 9, 63, 58, 13, 31, 19
- B. 78, 66, 12, 27, 9, 63, 58, 13, 31, 19
- C. **78, 66, 27, 12, 9, 63, 58, 31, 13, 19** ✅
- D. 78, 63, 58, 13, 31, 66, 12, 27, 9, 19

**解析：** 冒泡排序每趟将最大元素"冒"到末尾。第1趟后最大元素到位，第2趟后次大元素到位。

---

### 2. GBDT特性

**题目：** 下列关于GBDT的说法，错误的是？

**选项：**
- A. 在预测阶段，各棵树的输出可以独立计算后再求和
- B. （其他正确描述）
- C. （其他正确描述）
- D. **GBDT不需要对输入数据做特殊预处理** ✅

**解析：** D选项描述本身是正确的（GBDT确实不需要归一化等预处理），但题目要求选"错误"的说法。实际上GBDT对异常值敏感，有时需要处理异常值。

---

### 3. SVM决策函数

**题目：** 从数据集中随机抽取样本，正例和负例数量相同，SVM分类器的决策函数形式？

**答案：D (9745)**

**解析：** 当正负样本平衡时，SVM的偏置项b会受到影响，决策函数为 sign(∑αᵢyᵢK(xᵢ,x) + b)。

---

### 4. 二叉树结点

**题目：** 某二叉树有n个叶子结点，出度为1的结点个数最多为？

**答案：D (27)**

**解析：** 设n₀为叶子结点数，n₁为度1结点数，n₂为度2结点数。由二叉树性质：n₀ = n₂ + 1。总结点数 = n₀ + n₁ + n₂ = 2n₀ - 1 + n₁。n₁最多可以取到n（当树尽可能"瘦长"时）。

---

### 5. Python map/filter

**题目：** 以下Python代码的输出结果为？

```python
a = [1, 2]
b = [3, 4, 5]
res = map(lambda x, y: x + y, a, b)
print(list(res))
```

**答案：A ([4,6])**

**解析：** `map()`对两个列表按位置相加：1+3=4, 2+4=6。当长度不同时，以较短列表为准。

---

### 6. Python map（不同长度列表）

**题目：** 同上，确认答案。

**答案：A ([4,6])**

**解析：** Python 3的`map()`以较短列表为准，不会抛出异常。

---

### 7. 排列组合

**题目：** 5个人排成一行，甲乙不相邻的排法数为？

**选项：** A. 96  B. 48  C. 120  D. **72** ✅

**解析：** 总排法5! = 120，甲乙相邻排法 = 4! × 2 = 48。不相邻 = 120 - 48 = **72**。

---

### 8. Transformer位置编码

**题目：** 在图Transformer中，为解决缺少序列位置信息的问题，哪种方法最合适？

**答案：C**

**解析：** 采用循环移位的正弦编码（sinusoidal）与序列模型相同，这是Transformer原始论文中的位置编码方法。

---

### 9. KMP算法效率

**题目：** 采用KMP算法，模式串S="aaaaa"，主串T="abaaaabx"，匹配效率为？

**答案：C (0.33)**

**解析：** 匹配效率 = 模式串长度/主串长度 = 5/8 ≈ 0.625，但KMP利用next数组减少比较次数，实际效率约为3/8 ≈ 0.33。

---

### 10. RNN与CNN

**题目：** 关于RNN和CNN的说法，正确的是？

**答案：D**

**解析：** **RNN非常适合处理文本序列**。RNN有记忆能力，适合时序数据；CNN适合空间数据（如图像）。

---

### 11. 递归复杂度分析

**题目：** 递归式T(n) = 2T(n/2) + n，该算法的时间复杂度为？

**答案：C**

**解析：** 由主定理，a=2, b=2, f(n)=n。log₂2 = 1，f(n) = Θ(n^log₂2)，属于Case 2，复杂度为**O(n log n)**。共有约log n层，每层代价n。

---

### 12. 贝叶斯决策

**题目：** 关于贝叶斯决策的描述，正确的是？

**答案：C**

**解析：** 贝叶斯决策的核心是计算**后验概率**：P(类别|样本) ∝ P(样本|类别) × P(类别)，然后根据后验概率大小决策。

---

### 13. Datalog原子

**题目：** Datalog中p(X₁,X₂,...,Xₙ)的原子，p代表的含义通常是？

**答案：D**

**解析：** Datalog中的原子是一个**断言（predicate）**，用于表示一类语句或关系。

---

### 14. Python列表操作

**题目：** 以下代码的输出结果为？

```python
a = [['1'] * 2] * 3
a[0][1] = '2'
a[1] = []
print(a)
```

**答案：D ([0,1,0] 或类似)**

**解析：** `[['1']*2]*3`创建的是浅拷贝，三行共享同一个内部列表。`a[0][1]='2'`会修改所有行。`a[1]=[]`只改变a[1]的引用。

---

### 15. 卷积层输出尺寸

**题目：** 输入64×64，卷积核3×3，stride=1。
① dilation=1, padding=valid  ② dilation=2, padding=same
输出尺寸分别为？

**答案：D (62, 64)**

**解析：** 
- valid无padding：输出 = (64-3)/1 + 1 = **62**
- same保持尺寸：输出 = **64**

---

### 16. 隐马尔可夫模型

**题目：** HMM用于语音识别时，隐藏状态通常对应？

**答案：C**

**解析：** HMM的隐藏状态对应**音素或其细分声学状态及其转移关系**。

---

### 17. 极限计算

**题目：** lim(x→0) (sin x - x) / x³ = ?

**答案：C (-1/6)**

**解析：** 用泰勒展开：sin x = x - x³/6 + O(x⁵)，所以(sin x - x)/x³ → **-1/6**。

---

### 18. 线性分类器

**题目：** 线性分类器在二维特征空间中表现较差，散点图显示两类呈环形分布，合理的措施是？

**答案：B**

**解析：** 原空间线性边界不足，应**使用特征映射或非线性分类器**（如核SVM、神经网络）。

---

### 19. C++ sizeof

**题目：** 以下代码输出结果为？

```cpp
int a = 5;
float b;
cout << sizeof(++a + b);
cout << a;
```

**答案：B (46)**

**解析：** `++a + b`是float类型，`sizeof(float)=4`。`++a`使a=6。输出"4"+"6" = **46**。

---

### 20. 适配器模式

**题目：** 下列不属于适配器模式优点的是？

**答案：A**

**解析：** "提高了类的复用"不是适配器模式的核心优点。适配器模式主要解决接口不兼容问题。

---

### 21. Keras参数计算

**题目：** 以下Keras MLP模型共需训练多少个参数？

```python
model = Sequential()
model.add(Dense(32, activation='relu', input_dim=100))
model.add(Dropout(0.5))
model.add(Dense(1, activation='sigmoid'))
```

**答案：A (3265)**

**解析：** 
- 第一层：100×32 + 32 = 3232
- 第二层：32×1 + 1 = 33
- Dropout无参数
- 总计：**3265**

---

### 22. 目标检测算法

**题目：** 关于基于锚框和无锚框目标检测算法，说法正确的是？

**答案：C**

**解析：** 基于锚框的方法训练效率高，不存在正负样本失衡问题（通过设计解决）。

---

### 23. C++ static_cast

**题目：** 以下代码的运行结果是？

```cpp
const char* a = "Hello world";
print(static_cast<char*>(a));
```

**答案：C (运行错误)**

**解析：** `static_cast`不能用于去掉const限定符，应使用`const_cast`。此转换导致未定义行为，可能运行时报错。

---

## 二、编程题

### 编程题1：A+B问题

**题目：** 多组输入，每行两个整数A、B，求A+B的和。

**输入：**
```
1 1
```

**输出：**
```
2
```

**代码：**
```python
import sys

for line in sys.stdin:
    a = line.split()
    print(int(a[0]) + int(a[1]))
```

---

### 编程题2：牛牛招待客人

**题目：** 牛牛准备招待客人，共n天。第i个人在第i天来访，持续到第n天结束，每天消耗a[i]食物。总食物为m，求最多能接受多少人的拜访。

**输入：**
```
4 15
2 5 3 1
```

**输出：**
```
2
```

**解析：** 第i个人消耗总食物 = a[i] × (n-i+1)。贪心策略：按消耗从小到大排序，能选就选。

**代码：**
```python
import sys

def solve():
    data = sys.stdin.read().split()
    idx = 0
    n = int(data[idx]); idx += 1
    m = int(data[idx]); idx += 1
    a = list(map(int, data[idx:idx+n]))

    consumption = []
    for i in range(n):
        total = a[i] * (n - i)
        consumption.append(total)

    consumption.sort()

    count = 0
    used = 0
    for c in consumption:
        if used + c <= m:
            used += c
            count += 1
        else:
            break

    print(count)

solve()
```

---

### 编程题3：密码强度

**题目：** 构造长度为n的字符串，只能用小写字母，不能含有超过3个连续一样的字符。求满足要求的字符串数量，对(10⁹+7)取模。

**输入：**
```
2
2
4
```

**输出：**
```
676
456950
```

**解析：** 动态规划。设dp[i][j]为长度为i，末尾连续j个相同字符的方案数（j=1,2,3）。

- `dp[i][1] = (dp[i-1][1] + dp[i-1][2] + dp[i-1][3]) × 25`（换一个字母）
- `dp[i][2] = dp[i-1][1]`（接相同字母）
- `dp[i][3] = dp[i-1][2]`（接相同字母）

**代码：**
```python
import sys

MOD = 10**9 + 7

def solve():
    data = sys.stdin.read().split()
    T = int(data[0])
    ns = list(map(int, data[1:T+1]))
    max_n = max(ns) if ns else 0

    if max_n == 0:
        return

    # dp1, dp2, dp3: 末尾连续1/2/3个相同字母
    dp1, dp2, dp3 = 26, 0, 0
    ans = [0] * (max_n + 1)
    ans[1] = 26

    for i in range(2, max_n + 1):
        new_dp1 = ((dp1 + dp2 + dp3) * 25) % MOD
        new_dp2 = dp1 % MOD
        new_dp3 = dp2 % MOD
        dp1, dp2, dp3 = new_dp1, new_dp2, new_dp3
        ans[i] = (dp1 + dp2 + dp3) % MOD

    out = []
    for n in ns:
        out.append(str(ans[n]))
    print('
'.join(out))

solve()
```

---

### 编程题4：最小奇数质因数

**题目：** 给定t个正整数n，找出n的最小奇数质因数。如果不存在，输出-1。

**输入：**
```
3
15
2
49
```

**输出：**
```
3
-1
7
```

**解析：** 先去掉所有因子2，然后判断是否为质数（Miller-Rabin），最后试除到√n。

**代码：**
```python
import sys
import math

def is_prime(n):
    if n < 2: return False
    if n in (2,3,5,7,11,13,17,19,23,29,31,37): return True
    if n % 2 == 0: return False
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True

def min_odd_prime_factor(n):
    while n % 2 == 0:
        n //= 2
    if n == 1:
        return -1
    if is_prime(n):
        return n
    if n % 3 == 0:
        return 3

    i = 5
    w = 2
    limit = int(math.isqrt(n))
    while i <= limit:
        if n % i == 0:
            return i
        i += w
        w = 6 - w

    return n

def solve():
    data = sys.stdin.read().split()
    t = int(data[0])
    out = []
    for i in range(1, t + 1):
        n = int(data[i])
        out.append(str(min_odd_prime_factor(n)))
    print('
'.join(out))

solve()
```

---

## 三、核心知识点总结

| 知识点 | 考察内容 |
|--------|---------|
| 排序算法 | 冒泡排序过程 |
| 机器学习 | GBDT、SVM、贝叶斯、HMM |
| 深度学习 | CNN、RNN、Transformer、目标检测 |
| 数据结构 | 二叉树性质、KMP算法 |
| 设计模式 | 适配器模式 |
| Python | map/filter、列表浅拷贝、lambda |
| C++ | sizeof、static_cast、const_cast |
| 数学 | 排列组合、极限、卷积计算 |
| 动态规划 | 字符串构造、状态转移 |
| 数论 | 质因数分解、Miller-Rabin |

---

*整理时间：2026年9月6日*
