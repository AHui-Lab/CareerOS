# CareerVault / JobPilot boundary

## CareerVault owns facts

CareerVault is the canonical source for profile, education, experiences, skills, evidence, and future career notes. A fact is eligible for JobPilot only after it is represented as a CareerVault experience and marked `resume_ready: true`.

## JobPilot owns job-search state

JobPilot owns opportunity memos, JD text, generated resume versions, autofill packages, and application workflow state.

## No direct Obsidian ingestion

JobPilot must not expose an Obsidian folder import endpoint or query an Obsidian index. Historical notes must be curated into CareerVault first.

This boundary is deliberate: learning notes, interview preparation, future ideas, and duplicated old resume versions must not enter a resume-generation prompt merely because they happen to be stored in the same note repository.

## Fallback

The JobPilot-local profile/experience tables are legacy compatibility only. They may be used explicitly if CareerVault is offline, but must not silently override a connected CareerVault.
