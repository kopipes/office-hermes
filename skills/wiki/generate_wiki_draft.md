# Skill: generate_wiki_draft

## Purpose
Generate human-readable wiki draft from structured records and evidence.

## Inputs
- entity_type
- entity_id
- source records
- evidence chunks

## Rules
- never publish directly
- set `approval_status=draft`
- include source document references
- include `last_reviewed` and `freshness_rule`

## Output
Markdown page with YAML frontmatter.
