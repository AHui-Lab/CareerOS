# JobPilot V0.2.1 升级说明

## 升级前
彻底关闭旧 JobPilot 的命令行窗口。

建议备份：

```text
data/jobpilot.db
.env
```

## 升级
将 `jobpilot-v0.2.1-patch.zip` 解压到现有 JobPilot 根目录并覆盖同名文件，然后运行：

```text
start.bat
```

通常不需要重新运行 `install.bat`，V0.2.1 没有新增 Python 第三方依赖。

## 数据位置变化
V0.2.1 默认把数据库放到：

```text
%LOCALAPPDATA%\JobPilot\jobpilot.db
```

如果当前项目目录仍存在旧的：

```text
data/jobpilot.db
```

第一次启动会自动迁移，并创建备份。

如果你之前已经换过项目目录导致旧机会“消失”，请找到旧 JobPilot 目录中的 `data/jobpilot.db`，进入：

**设置 → 数据安全 → 合并旧 jobpilot.db**

进行合并。

## 浏览器扩展
打开：

```text
edge://extensions/
```

或：

```text
chrome://extensions/
```

找到 JobPilot Assistant → 重新加载。版本应为 `0.2.1`。

## Obsidian
进入“我的资料库 → 直接导入你的 Obsidian 仓库”，选择 Vault 根文件夹即可。

重新导入同一仓库时会更新变化的文件，不会把同一路径反复添加成重复资料。
