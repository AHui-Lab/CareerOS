# 2026-08 legacy Resume / Obsidian migration

Source repository: `AHui-Lab/Resume`

Goal: extract reusable career facts into CareerVault without importing the old vault structure, duplicated resume versions, interview preparation, or future ideas.

## Safety rule

Every migrated experience is initially:

```yaml
status: draft
resume_ready: false
migration_review: required
```

JobPilot therefore cannot use these records until they are reviewed in CareerVault and explicitly marked Resume Ready.

## Imported in this batch

| CareerVault ID | Main source | Confidence | Notes |
|---|---|---|---|
| `rag-local-knowledge-base` | `基于Langchain/...md` | high | Interview-prep sections excluded |
| `miniled-nanowire-probe` | miniLED detailed project note | high | Resume-writing / future-work sections excluded |
| `stm32-mower-sensor-fusion` | `本科毕设/本科毕设.md` | high | Duplicate `本科毕设 1.md` had the same content SHA and was deduplicated |
| `wearable-unity-hmi` | 江苏省智能仪器大赛 detailed note | high | Career-direction advice excluded |
| `internship-nanjing-heyue` | 合越智能详细实习记录 | high | Detailed record overrides simplified Resume.md description |
| `internship-nanjing-metrology` | 计量院详细实习记录 | high | DOCX retained as source reference, not copied in this batch |
| `compute-empire-game` | `Resume.md` | medium | No dedicated source note found yet; requires project evidence review |
| `software-copyright-data-glove` | repeated resume/project records | high | Registration identifier intentionally not copied |
| `provincial-innovation-data-glove` | repeated resume/project records | high | Personal role/details need more source evidence if expanded |
| `scholarship-2022-2023` | `Resume.md` | medium | Recommend attaching award evidence before Resume Ready |

A public-profile draft was also created from `Resume.md` with education and reusable skill tags. Phone/email were deliberately not committed.

## Explicitly skipped

The following types are not career facts and were not copied into CareerVault experiences:

- `.obsidian/`, `.workbuddy/`, caches and generated inspection files;
- interview preparation and memorized-answer notes;
- AI algorithm learning plans and system-test learning materials;
- semiconductor/process-integration learning notes;
- “future improvement”, “next steps”, and planned-but-not-completed features;
- resume-writing suggestions such as “if applying for hardware, write it this way”;
- multiple complete resume variants as separate experiences;
- generated DOCX/PDF resume outputs;
- scripts/render/debug artifacts;
- raw application tracking such as `投递记录.md` (belongs to JobPilot/application history, not CareerVault facts).

## Important conflict resolved

`Resume.md` simplified the 南京合越智能科技有限公司 internship as mainly a DigiHuman reproduction project with an incomplete date range. The detailed internship note records about seven weeks of data-glove HMI work, BLE migration, sensor processing, Unity development, multi-device support, and DigiHuman only in the final phase. The detailed note was treated as the stronger source.

## Review checklist before enabling Resume Ready

For each migrated item:

1. Confirm title, organization, role and dates.
2. Confirm every number/metric against the source or evidence.
3. Remove any fact that was team-level but not personally performed.
4. Add/attach evidence where valuable.
5. Only then set `resume_ready: true`.

## Not migrated yet

Binary evidence (PDF/DOCX/video/certificates) is not copied in this first pass. It can be imported selectively later and attached to the corresponding CareerVault experience instead of duplicating the entire legacy vault.
