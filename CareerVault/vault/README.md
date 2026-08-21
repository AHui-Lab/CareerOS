# CareerVault data directory

This directory is the human-readable source of truth created by the app.

- `profile/public.yaml` — non-sensitive profile data that may be versioned.
- `experiences/<id>/index.md` — one experience per folder, YAML frontmatter + Markdown body.
- `experiences/<id>/attachments/` — evidence/reference files attached to an experience.
- `inbox/*.md` — quick notes, ideas, and work logs waiting to be organized.
- `applications/` — reserved for application records shared with JobPilot.
- `generated/` — generated resume outputs; ignored by Git by default.

Phone/email are stored in `../private/profile.yaml`, not here, and are ignored by Git.
