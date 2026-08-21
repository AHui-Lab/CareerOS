# JobPilot V0.2.2 - CareerVault integration

V0.2.2 connects JobPilot to CareerVault while keeping the two applications independent.

## Responsibilities

- CareerVault (`127.0.0.1:8766`) is the source of truth for profile and factual experiences.
- JobPilot (`127.0.0.1:8765`) keeps opportunity/application state, creates targeted resume versions, and provides browser autofill.
- Final application submission is always manual.

## Resume generation

The resume page now has **优先使用 CareerVault 事实库**. When CareerVault is online this is enabled by default. JobPilot sends the target company, role, and JD to CareerVault `/api/jobpilot/context`, and CareerVault returns the most relevant `Resume Ready` experiences.

If you turn CareerVault off, JobPilot uses its older local experience chooser. Existing Obsidian/imported documents can still be enabled as secondary evidence.

If CareerVault is offline, JobPilot falls back to its existing local experience bank / imported documents.

Each generated resume stores a profile snapshot so a later CareerVault profile edit does not silently change an older DOCX export or preview.

## Upgrade from V0.2.1

1. Close the old JobPilot process completely.
2. Back up `%LOCALAPPDATA%\JobPilot\jobpilot.db` if desired.
3. Extract `jobpilot-v0.2.2-careervault-patch.zip` into the existing JobPilot root and overwrite same-name files.
4. Run `start.bat`.
5. Reload the JobPilot Assistant extension in Edge/Chrome extension management. Version should show `0.2.2`.
6. Start CareerVault separately on port 8766.

No database migration and no new Python dependency are required for this upgrade.

Optional `.env` setting:

```env
CAREERVAULT_URL=http://127.0.0.1:8766
```

## Verification

Open `http://127.0.0.1:8765/api/health`. The response should include a `careervault` object. When CareerVault is running, `available` should be true.
