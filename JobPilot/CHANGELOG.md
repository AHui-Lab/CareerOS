# Changelog

## 0.7.0 · 2026-10-12

- 新增独立 Offer 管理及首页、侧栏、搜索入口；支持 2–4 份对比、自定义维度、附件、CSV、归档恢复和回复 / 签约日程联动。
- 采用国内招聘参考，提供六组 94 个细节字段与 13 个国内来源；区分确认薪资、平均年收入、区间、浮动奖金、一次性待遇、公积金及政策资格。
- 新增实习、见习、劳动合同试用、转正等待遇阶段，按明确基数、金额与期限计算已知阶段工资，首年汇总标注完整度，不把平均年薪自动换算为保证月薪。
- 总览改为渐进式入口，展示八个模块、重点事项与近三天日程，完整行动和日历按需展开。
- 岗位列表补齐 JD 摘要、投递时间、关联材料和下一步；增加独立整理状态、批量搁置 / 不考虑 / 结束、回看日期、恢复与短时撤销。
- 资料库采用三个核心字段开始录入，区分草稿与简历事实，并保留长文、扩展字段、关联和证明材料。
- 修复短页面岗位导入及结构化错误显示，失败时保留输入，支持核对后补充 JD。
- 增加 macOS 统一安装、启动、停止入口与稳定数据目录；更新 README、使用说明和版本标识。

## 0.6.0 · 2026-10-09

- 统一工作台、岗位、简历、资料与面试页面的视觉和手机布局，增加深色外观。
- 新增岗位详情、投递看板、重点关注、本机搜索，以及行动完成、撤销和延期。
- 岗位与准备空间可持久关联，保留已有资料与笔记。
- 简历采用三步制作与清晰的版本状态，补齐 macOS 中文 PDF 导出和无照片导出。
- 保留原接口、数据和兼容工具；改进部分刷新失败、未保存输入、文件编辑关闭与无变化记录的处理。


## 0.3.0

- Made CareerVault the primary and only formal career-fact source for targeted resume generation.
- Removed the Obsidian Vault import and document-list API endpoints from JobPilot.
- Removed Obsidian indexing/import UI and the `use_vault` resume-generation switch.
- JobPilot now requests JD-specific `Resume Ready` experiences directly from CareerVault.
- Kept the old JobPilot profile/experience bank only as an explicit offline/legacy fallback and recovery path.
- Updated the browser assistant and launcher version contract to 0.3.0.
- Added tests that prevent the Obsidian API surface from being reintroduced accidentally.

## 0.2.2

- Added CareerVault integration and JD-specific factual context retrieval.
- Added profile snapshots to resume versions so later profile edits do not change old exports.
- Allowed CareerVault string experience IDs in resume generation.
- Added safer Windows launchers: start, restart, and stop.
- Added automatic GitHub CI for Python tests and browser JavaScript syntax checks.

## 0.2.1

- Moved the default database to a stable user data directory.
- Added legacy database merge and backup tools.
- Added Obsidian Vault import/update support. This path is retired in 0.3.0.
- Added POST opportunity edit compatibility endpoint.

## 0.2.0

- Added resume import, structured experience bank, targeted resume generation, DOCX export, and browser autofill package.
