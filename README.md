# CareerOS

CareerOS 是一个本地优先的个人求职工作台，由两个协作模块组成：

- `JobPilot`：岗位管理、JD、投递跟踪、简历生成、邮件跟踪和浏览器辅助填表。
- `CareerVault`：经历、项目、教育背景、获奖、专利、论文和证明材料。

两个模块在代码和数据层面保持独立，但用户只需要一个安装入口和一个启动入口。

## Windows 快速开始

首次使用，在仓库根目录双击 `install.bat`。它会自动为两个模块创建 Python 虚拟环境并安装全部依赖。安装完成后，以后只需要双击根目录的 `start.bat`。

系统会自动启动两个本地服务，并打开统一的 CareerOS 页面：

- 求职管理：<http://127.0.0.1:8765>
- 经历和项目：<http://127.0.0.1:8766>

正常使用时请从 JobPilot 页面左侧进入“经历和项目”，不需要分别打开两个页面。关闭服务时运行根目录的 `stop.bat`，它只会停止 CareerOS 管理的服务。

## 更新代码

```bat
git pull origin main
install.bat
start.bat
```

重新运行 `install.bat` 只会补齐依赖，不会删除本地数据。

## 私有数据同步

同步功能使用单独的私有 GitHub 仓库，不要使用公开的 CareerOS 代码仓库保存个人数据。

1. 创建私有仓库，例如 `CareerOS-PrivateData`。
2. 确保 Git 已登录 GitHub，能够访问该私有仓库。
3. 打开 CareerOS → “设置和帮助” → “私有仓库同步”。
4. 填写私有仓库地址、分支和同步口令。
5. 点击“提交当前数据”。

远端只保存加密快照，包含 JobPilot 数据库、CareerVault 经历文件、私密资料和证件照。启动时只检查更新，不会自动覆盖本机；确认后才会接受远程数据。关闭时可自动提交，误接受后可以回滚。第二台电脑配置同一个仓库地址、分支和同步口令，再检查并接受远程更新即可。

## 常见问题

### 启动时报 `ModuleNotFoundError: cryptography`

说明当前电脑的旧虚拟环境没有安装最新依赖。在仓库根目录重新运行：

```bat
install.bat
```

也可以手动执行：

```bat
JobPilot\.venv\Scripts\python.exe -m pip install -r JobPilot\requirements.txt
```

### 服务在 15 秒内没有变健康

依次检查：

1. 是否运行过根目录 `install.bat`。
2. 是否有其他程序占用 `8765` 或 `8766` 端口。
3. 查看 `JobPilot\.runtime\careeros_求职管理.err.log` 和 `CareerVault\.runtime\careervault.err.log`。
4. 运行根目录 `stop.bat` 后再运行 `start.bat`。

启动器只会停止它识别为 CareerOS 的进程，不会强制关闭无关程序。

### GitHub 私有仓库无法访问

确认地址使用 `.git` 结尾，然后执行：

```bat
git ls-remote https://github.com/AHui-Lab/CareerOS-PrivateData.git
```

如果认证失败，请先配置 SSH 或 Git Credential Manager。仓库可以初始化 README，首次同步会自动接入远程历史。

### 浏览器插件无法自动填写

插件不会自动提交表单。确认 JobPilot 已通过根目录 `start.bat` 启动，浏览器已加载 `JobPilot\extension` 为未打包扩展，并且当前页面允许扩展访问。复杂动态下拉框、重复教育经历和证件照上传字段仍需要人工检查。

### 如何确认服务正常

打开以下地址，两个都返回 `"ok": true` 即正常：

- <http://127.0.0.1:8765/api/health>
- <http://127.0.0.1:8766/api/health>

## 数据位置与隐私

- JobPilot 数据默认位于 `%LOCALAPPDATA%\JobPilot`。
- CareerVault 经历文件位于 `CareerVault\vault`。
- 手机号、邮箱、身份证号、证件照和邮箱密码不应提交到公开代码仓库。
- 不要把 `private`、数据库、`.env`、浏览器 Cookie 或 API 密钥上传到公开仓库。
