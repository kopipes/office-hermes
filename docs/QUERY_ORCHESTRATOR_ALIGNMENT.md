# Query Orchestrator Alignment

Dokumen ini mencocokkan brief `Query Orchestrator` dengan implementasi Hermes + Brain OS saat ini.

## Sudah Match

- Donna / Hermes adalah agent utama untuk query Brain OS.
- Query masuk melalui gateway terkontrol, bukan akses Postgres langsung.
- MCP/API server menjadi pintu resmi akses data.
- Skill runtime `provaliant-brain-os-query` menjadi antarmuka query domain.
- Query types utama dari brief sudah tercermin:
  - `structured_operational`
  - `wiki_truth`
  - `evidence_lookup`
  - `relationship_context`
  - `report_generation`
- Logging query sudah aktif melalui `query_logs`.

## Baru Ditambahkan

- Endpoint orkestrator: `POST /brain/query`
- Intent classifier dasar di layer MCP
- Entity extractor dasar untuk `project`, `client`, `vendor`, `business_unit`
- Cache key builder berbasis user/role/intent/entity/query hash
- L1 in-memory cache dengan TTL per intent
- Router dari query ke tool:
  - `get_project`
  - `search_db`
  - `search_wiki`
  - `search_evidence`
  - `get_vendor`
  - `get_budget`
  - `get_action_items`
  - `generate_report`
- Answer formatter untuk hasil query utama

## Belum Full Match

- Redis cache belum diaktifkan. Saat ini masih L1 in-memory cache.
- Permission enforcement masih level dasar (`confidentiality_max` by role), belum row-level policy penuh di router.
- `relationship_context` masih gabungan sederhana vendor + evidence, belum terhubung ke GBrain graph/context sesungguhnya.
- Intent classification masih rule-based, belum memakai classifier modular terpisah.
- Runtime Hermes masih memakai satu skill aktif utama, belum modular multi-skill orchestration seperti opsi B pada brief.

## Keputusan Implementasi

Untuk fase sekarang dipilih model yang direkomendasikan brief sebagai langkah tercepat:

- `Option A — Inside ONE Skill`
- Skill aktif tetap `provaliant-brain-os-query`
- Skill ini sekarang diarahkan ke `POST /brain/query` sebagai orchestration entrypoint

## Dampak

- Donna sekarang bisa memakai satu endpoint query resmi untuk status, vendor, wiki, evidence, budget, dan report.
- Flow jadi lebih dekat ke brief tanpa memecah arsitektur yang sudah stabil.
- Upgrade ke Redis dan router modular nanti bisa dilakukan tanpa mengubah interface user.
