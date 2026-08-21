# CareerOS

CareerOS is a local-first personal career workspace with two connected modules: job-search management and career assets.

**Career assets store verified career facts. Job-search management turns those facts into job-specific resumes and application-form data.**

Current version: **V0.3.0**

## Product structure

CareerOS contains two user-facing modules:

- **求职管理**：岗位导入、状态跟踪、JD 分析、岗位简历和浏览器辅助填表。
- **经历资产**：个人资料、教育背景、项目、实习、科研和成果证据。

The modules share one CareerOS launcher and one user-facing workspace. Their existing service and data boundaries remain intact for compatibility.

## Architecture

```text
CareerVault :8766
  profile / education / projects / internships / research / awards
  only Resume Ready experiences are exposed to JobPilot
            |
            | POST /api/jobpilot/context
            v
JobPilot    :8765
  opportunity memo -> JD matching -> tailored resume -> autofill package
```

From V0.3.0 onward, **JobPilot does not import or index Obsidian vaults**. Historical Obsidian/Resume content should first be reviewed, deduplicated, and migrated into CareerVault. This prevents interview notes, learning material, drafts, and unimplemented ideas from contaminating resume facts.

## What JobPilot does

- Keep opportunities as a lightweight memo instead of a heavy CRM.
- Query CareerVault for JD-relevant `Resume Ready` factual experiences.
- Generate a targeted resume for a specific company, role, and JD.
- Save immutable profile snapshots with resume versions.
- Export DOCX resumes.
- Provide a Chrome/Edge browser assistant for safe form autofill.
- Never auto-submit applications or bypass login/CAPTCHA/security controls.

## Unified workspace

The local workspace is organized under `C:\CareerOS`:

- `JobPilot`: job management, JD parsing, application tracking, resume generation, and browser autofill.
- `CareerVault`: career assets, education, projects, achievements, and resume-ready facts.

Each module keeps its existing Git history and service boundary. `JobPilot\career-os.bat` starts both modules together.

## Quick start on Windows

```bat
git clone https://github.com/AHui-Lab/CareerOS.git
cd CareerOS\JobPilot
install.bat
start.bat
```

Open `http://127.0.0.1:8765`.

CareerVault should also be running at:

```text
http://127.0.0.1:8766
```

### Launcher shortcuts

- `start.bat`: opens the current version; replaces an older JobPilot process on port 8765.
- `restart.bat`: force a clean restart after pull/update.
- `stop.bat`: stop only the JobPilot service on port 8765.

## CareerVault behavior

Normal resume generation always asks CareerVault for context. If CareerVault is connected but has no `Resume Ready` experiences, JobPilot stops and asks you to review the CareerVault data instead of silently falling back to old data.

The old JobPilot profile/experience bank remains only for:

- recovering historical JobPilot databases;
- temporary offline fallback when CareerVault is unavailable;
- compatibility with old generated versions.

Do not maintain new career facts in both systems.

## Browser assistant

Load the `extension/` folder as an unpacked extension in Edge or Chrome developer mode.

The assistant can fill common text/select fields such as name, phone, email, school, major, degree, graduation date, GPA, portfolio, self-introduction, and long-form experience blocks. Complex ATS repeatable rows/custom cascaders still need site-specific adapters.

The assistant never clicks the final submit button for you.

## Data locations and safety

JobPilot runtime data is not stored in this Git repository.

On Windows the default database is:

```text
%LOCALAPPDATA%\JobPilot\jobpilot.db
```

Career facts live in the `C:\CareerOS\CareerVault` module.

The following are intentionally ignored by Git:

- `.env`
- `.venv/`
- project-local databases and backups
- caches/bytecode

Never commit API keys, authentication cookies, or local job-application databases.

## Optional AI configuration

Copy `.env.example` to `.env` and configure an OpenAI-compatible endpoint if desired.

```env
AI_BASE_URL=https://api.deepseek.com
AI_API_KEY=your-key
AI_MODEL=deepseek-chat
CAREERVAULT_URL=http://127.0.0.1:8766
```

Without an AI provider, JobPilot still supports local fallback resume formatting; CareerVault remains the factual source.

## Development

Run tests:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Static checks:

```bat
.venv\Scripts\python.exe -m compileall jobpilot tests run.py
node --check jobpilot/static/app.js
node --check extension/popup.js
```

GitHub Actions runs these checks automatically on pushes and pull requests.

See `UPGRADE_0.3.0.md` for the migration from V0.2.2.
