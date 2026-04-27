# Skill: upsert_meeting

## Purpose
Write meeting, decisions, and action items into Postgres.

## Behavior
1. match project/client/business unit
2. insert `meetings`
3. insert `decisions`
4. insert `action_items`
5. update project `latest_summary` when relevant
6. create wiki draft suggestion for strategic meeting
7. return confirmation payload
