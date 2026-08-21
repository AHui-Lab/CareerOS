# Upgrade to JobPilot 0.3.0

V0.3.0 changes the resume-source architecture: CareerVault is now the formal source of truth and the old Obsidian import/index path is retired.

## Before upgrading

1. Make sure CareerVault is installed and can open at `http://127.0.0.1:8766`.
2. Keep your existing JobPilot database. V0.3.0 does not delete old opportunities, resume versions, local experiences, or historical vault tables.
3. Pull the new code and run `install.bat` if dependencies changed.
4. Run `restart.bat` so the 0.2.x process on port 8765 is replaced by 0.3.0.
5. Reload the unpacked browser extension because its version contract is now 0.3.0.

## What changes

Removed from the active JobPilot product:

- `POST /api/vault/import`
- `GET /api/vault/documents`
- Obsidian folder picker/import UI
- Obsidian document list UI
- `use_vault` resume-generation option
- Obsidian document retrieval during resume generation

Normal resume generation now calls CareerVault `POST /api/jobpilot/context` for the current JD.

## Old data is not deleted

Existing `vault_documents` rows in an old `jobpilot.db` are intentionally left untouched for safe rollback/recovery, but V0.3.0 does not read them when generating a resume.

The old JobPilot profile and experience bank also remain as an explicit offline/legacy fallback. New facts should be maintained in CareerVault only.

## Recommended workflow

```text
New experience / result / skill
        -> CareerVault
        -> review + Resume Ready
Job opportunity / JD
        -> JobPilot
        -> CareerVault context
        -> targeted resume
        -> browser autofill
        -> human review and submit
```

Historical Obsidian/Resume material should be filtered and migrated into CareerVault first rather than imported directly into JobPilot.
