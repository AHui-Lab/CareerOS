# CareerVault

CareerVault is a local-first, file-backed career knowledge base designed to work with JobPilot.

It is intentionally not another resume editor. CareerVault stores **facts**: profile, education, projects, internships, research, achievements, evidence, files, and quick notes. JobPilot consumes those facts to generate targeted resumes and fill recruitment forms.

## CareerOS v0.7.0 integration

CareerVault is the career-assets service behind CareerOS's “资料库”. Use the unified macOS or Windows installer and launcher at the repository root; see the [current CareerOS README](../README.md) for installation, updates, data locations, and all features.

The current capture workflow starts with a name, personal contribution, and result. Additional details open progressively. Drafts and resume-ready facts have separate views; saving returns to the list while preserving long-form content, custom metadata, links, and evidence. Only confirmed `Resume Ready` facts are supplied to JobPilot for formal resume generation. See the [capture and organization guide](../docs/资料库-录入与整理产品化-20261009.md).

## Core capabilities

- Add/edit/delete experiences from a lightweight browser UI.
- Autosave edits to ordinary Markdown + YAML files.
- Maintain multiple education records and a reusable profile.
- Quick Inbox for new ideas and work logs.
- Upload files and browse/edit Markdown, YAML, TXT, and JSON directly in the UI.
- Upload attachments to an experience.
- Keep sensitive phone/email in a Git-ignored local file.
- Provide a stable API for JobPilot.
- Use Git snapshots for history without turning every keystroke into a commit.

## Quick start on Windows

推荐从 CareerOS 仓库根目录统一安装和启动：

```bat
cd ..
install.bat
start.bat
```

正常使用不需要单独安装或打开 CareerVault。以下独立命令仅用于开发和故障排查。

```bat
git clone https://github.com/AHui-Lab/CareerVault_system.git
cd CareerVault_system
install.bat
start.bat
```

Then open `http://127.0.0.1:8776`.

## Data model

```text
vault/
├─ profile/public.yaml
├─ experiences/<experience-id>/index.md
├─ experiences/<experience-id>/attachments/
├─ inbox/*.md
├─ inbox/files/
├─ applications/
└─ generated/

private/
└─ profile.yaml   # phone/email, never committed
```

One experience is one source of truth. Targeted resumes are outputs, not sources.

## CareerVault + JobPilot

CareerVault answers: **what have I actually done?**

JobPilot answers: **which facts fit this job, how should they be presented, and which recruitment-form fields should they fill?**

JobPilot integration endpoints are documented in `integrations/jobpilot/README.md`.

## Git safety

This repository is currently public. The app deliberately writes phone/email to `private/profile.yaml`, which is ignored by Git. Experience attachments and generated resumes are also ignored by default.

Because career data can still contain personal information, in-repo data snapshots are **disabled by default**. If you want GitHub to version your actual profile and experience Markdown, first make this repository private, then set:

```yaml
# config/settings.yaml
git_data_snapshots_enabled: true
```

After that, the UI's **创建 Git 快照** button can commit the structured `vault/` data and configuration. Always review `git status` before pushing.
