# Changelog

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
