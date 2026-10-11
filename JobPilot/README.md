# JobPilot · CareerOS 求职管理

**当前版本：v0.7.0 · 2026-10-12**

JobPilot 是 CareerOS 的求职管理服务，默认运行于 `http://127.0.0.1:8765`，通过 CareerVault 获取经过确认的经历事实。安装、更新、数据同步和完整功能介绍见 [CareerOS 主 README](../README.md)。

## 功能

- 总览：八个模块入口、进展、重点行动与近三天日程，完整月历和列表按需打开。
- 岗位：JD 导入预览与核对、搜索筛选、列表 / 看板 / 紧凑视图、投递进度、关联材料和下一步。
- 岗位整理：进行中、稍后再看、不考虑、已结束；批量整理、回看日期、恢复和短时撤销，独立于投递状态。
- Offer：独立录入或关联岗位，六组 94 个细节字段、13 个国内参考来源、自定义维度、附件、2–4 份比较、CSV 导出、归档和日程联动。
- 国内待遇：固定月薪、固定年现金、平均年收入及区间分别记录；实习、见习、试用、转正分阶段记录，确认基数后折算，已知阶段与首年完整度清楚展示。
- 简历：目标、经历、核查三步制作，保存不可变资料快照和版本，导出中文 PDF、DOCX 与辅助填表数据。
- 准备与练习：岗位准备空间、材料和笔记、面试经验、笔试试卷及题组。
- 邮件：IMAP 招聘邮件检查，人工确认关联、忽略和恢复。
- 通用体验：本机全局搜索、浅色 / 深色外观、手机导航、未保存编辑提示、数据备份和加密私有仓库同步。

## 运行与数据

在仓库根目录统一安装和启动两个服务：macOS 使用 `install.command` / `start.command`，Windows 使用 `install.bat` / `start.bat`。CareerVault 默认运行于 `http://127.0.0.1:8776`，通过工作台侧栏进入资料库。

macOS 统一启动器的数据库为 `.local-data/jobpilot/jobpilot.db`；Windows 默认为 `%LOCALAPPDATA%\JobPilot\jobpilot.db`。开发时用 `JOBPILOT_DATA_DIR` 指定独立目录。Offer 附件存储在数据库中，完整数据库备份包含附件。

正式简历使用 CareerVault 中的 `Resume Ready` 经历。服务已连接但没有可用事实时，会提示先整理资料；历史 JobPilot 资料只保留为恢复和明确的离线兼容入口。从 v0.3.0 起不再直接索引 Obsidian，历史内容需先审核迁入 CareerVault。

## 浏览器助手与 AI

在 Chrome / Edge 中将 `extension/` 加载为未打包扩展，辅助填写常见文本和选择字段；动态重复行、复杂级联选项及照片需人工检查，插件不会点击最终提交或绕过登录验证。

基础功能不需要 API 密钥。AI 功能使用 `JobPilot/.env` 中配置的兼容接口，字段见 [.env.example](.env.example)。不要提交密钥、Cookie、招聘数据库或个人资料。

## 开发

从仓库根目录执行（macOS / Linux，已安装统一虚拟环境）：

```sh
JOBPILOT_DATA_DIR="$PWD/.runtime/tests/jobpilot" PYTHONPATH=JobPilot \
  .venv/bin/python -m unittest discover -s JobPilot/tests -v
for test in JobPilot/tests/*.cjs; do node "$test"; done
```

Windows 可使用本模块虚拟环境中的 Python，并先设置 `JOBPILOT_DATA_DIR`。版本更新见 [CHANGELOG](CHANGELOG.md)，国内待遇说明见 [Offer 使用说明](../docs/Offer-评估维度与使用说明-20261011.md) 和 [分阶段薪资](../docs/Offer-国内参考与分阶段薪资-20261011.md)。
