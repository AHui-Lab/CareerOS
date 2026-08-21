# 从 JobPilot V0.1.x 升级到 V0.2.0

## 1. 先关闭 JobPilot

关闭正在运行的 `start.bat` / 终端窗口。

## 2. 建议备份

复制一份：

```text
data/jobpilot.db
.env
data/profile.json
```

## 3. 覆盖 Patch

把 `jobpilot-v0.2.0-patch.zip` 解压到当前 JobPilot 根目录，选择覆盖同名文件。

Patch 不包含：
- `data/jobpilot.db`
- `.env`

因此不会主动覆盖已有机会数据或 API Key。

## 4. 重新运行 install.bat

V0.2.0 新增依赖：
- python-multipart
- pypdf
- python-docx

所以升级后需要再运行一次：

```text
install.bat
```

它会在现有项目目录重新创建/更新 `.venv` 并安装新依赖。

## 5. 运行 start.bat

启动后，SQLite 自动新增：
- profile
- experiences
- resume_sources
- resume_versions

同时会给原 `opportunities` 表增加 `note` 字段。

原机会记录会保留。

## 6. 重新加载浏览器扩展

Edge：`edge://extensions/`

Chrome：`chrome://extensions/`

找到 JobPilot，点击“重新加载”。版本应为 `0.2.0`，名称为 **JobPilot Assistant**。

## 7. 推荐第一次使用顺序

1. 打开“我的资料库”
2. 导入你目前正在使用的 PDF/DOCX 简历
3. 检查基础资料
4. 检查拆出来的经历，手动修正或补充
5. 打开“定制简历”，粘贴一个目标岗位 JD
6. 生成简历
7. 下载 DOCX 检查
8. 打开网申页面，用浏览器扩展点“智能填写当前页面”
9. 人工检查所有字段后再提交
