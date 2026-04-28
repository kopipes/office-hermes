# Provaliant Brief Audit Procedure

Dokumen ini dipakai untuk mengaudit apakah implementasi dari brief sudah benar-benar berjalan di VPS.

## Scope Audit

Audit ini memverifikasi:
- Hermes Agent runtime terpasang dan bisa dipanggil.
- Primary model + fallback OpenRouter sesuai konfigurasi brief.
- Gateway Telegram aktif.
- Skill lokal `provaliant-brain-os-query` terpasang.
- MCP API server aktif dan endpoint inti merespons, termasuk `POST /brain/query`.
- Database Provaliant siap (schema utama + extension vector + tabel audit/query logs).
- Smoke test one-shot model (opsional) berhasil.

## Prasyarat

- Jalankan audit di VPS yang sudah terpasang Hermes + `office-hermes`.
- User shell: `ubuntu` (atau user yang punya akses ke `~/.hermes` dan `~/office-hermes`).
- `systemctl --user` aktif.

## Cara Menjalankan

Di VPS:

```bash
cd ~/office-hermes
chmod +x scripts/audit_brief_status.sh
bash scripts/audit_brief_status.sh
```

Dengan LLM smoke test (akan melakukan 1 call model):

```bash
RUN_LLM_TEST=1 bash scripts/audit_brief_status.sh
```

## Output dan Kriteria Lulus

Script akan menampilkan status:
- `PASS`: kontrol audit terpenuhi.
- `WARN`: tidak blocking, tapi perlu perhatian.
- `FAIL`: kontrol inti gagal.

Audit dinyatakan **lulus** jika:
- Tidak ada `FAIL`.
- Semua kontrol inti `PASS`:
  - Hermes runtime
  - model/fallback chain
  - gateway + mcp service active
  - API health + endpoint inti HTTP `200`
  - `POST /brain/query` HTTP `200`
  - DB schema dasar bisa di-query

## Checklist Manual Tambahan (UAT via Telegram)

Setelah script lulus, lakukan uji manual:

1. Kirim pesan ke bot: `status project CPP`
2. Pastikan jawaban memuat:
   - jawaban singkat
   - sumber data (endpoint/record)
   - confidence
   - next action
3. Coba query vendor: `vendor printing`
4. Coba query report: `weekly executive report`

Jika format dan data keluar konsisten, maka alur brief dari gateway -> skill -> MCP API -> DB terverifikasi end-to-end.

## Troubleshooting Ringkas

- Jika `hermes` tidak ditemukan: pakai `~/.local/bin/hermes`.
- Jika service user tidak aktif: `loginctl enable-linger <user>`.
- Jika API `401`: cek header `Authorization: Bearer <MCP_API_KEY>`.
- Jika API `500`: cek log `journalctl --user -u office-hermes-mcp.service -n 200 --no-pager`.
- Jika DB gagal: cek `DATABASE_URL` di `~/office-hermes/.env` dan status PostgreSQL.
