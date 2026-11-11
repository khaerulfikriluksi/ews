# Dashboard EWS Bank Mandiri — VERSI FINAL VERCEL

Desain ralat: title Dashboard EWS, header tanpa Bank Mandiri, KPI sub Semua postingan, judul chart Distribusi per Platform.
Total 14, Positive 3, Negative 11. Periode 08-11 Nov 2026, Tarikan 11-Nov-2026 13:21:52.

## Struktur (sudah Vercel-ready)
```
.
├── api/index.py          ← entry point Vercel
├── vercel.json           ← rewrite /api/* dan /* ke api/index.py
├── public/index.html     ← Dashboard (buka via server, bukan file://)
├── server/main.py        ← Flask API + SQLite
├── server/requirements.txt
├── server/schema.sql
├── data/archive/*.csv
└── .gitignore
```

## Cara upload ke repo + import ke Vercel
1. Extract ZIP ini, upload SEMUA isi ke repo GitHub (misal khaerulfikri13/ews).
   JANGAN upload key.txt, .env, ews.db.
2. Vercel → Add New → Project → Import dari GitHub → pilih repo.
3. Setting di layar New Project:
   - Root Directory: KOSONGKAN / isi `.` (JANGAN `server`)
   - Framework Preset: Flask (atau Other)
   - Build Command: kosong / None
   - Output Directory: N/A
   - Install Command: `pip install -r server/requirements.txt`
4. Environment Variables:
   - Hapus EXAMPLE_NAME
   - Add: Key = `X_API_KEY`, Value = isi key.txt kamu, Environments = Production + Preview
5. Klik Deploy.

## Test setelah Deploy
- Buka https://<nama-project>.vercel.app/ → Dashboard muncul
- Buka https://<nama-project>.vercel.app/api/ews/latest → JSON
- POST:
  curl -X POST https://<nama-project>.vercel.app/api/ews -H "X-API-Key: <key>" -F "file=@data/archive/Bank-Mandiri-EWS-08-11-Nov-2026.csv" -F "crawling_date=11-Nov-2026 13:21:52"

## API
POST /api/ews — header X-API-Key, body file + crawling_date
GET /api/ews/latest — crawl terbaru
GET /api/ews/history — semua crawl
GET /api/ews/history/:id — detail 1 crawl, sort Priority 1→4, Kategori A-Z, Tanggal terbaru dulu

## SQLite di Vercel — PENTING
Vercel itu serverless, filesystem read-only kecuali /tmp.
Code ini pakai DB_PATH=/tmp/ews.db kalau env VERCEL ada.
Artinya: POST + GET jalan normal, tapi history bisa hilang saat redeploy / cold start.
Untuk history permanen, pindah ke Turso / Neon / Supabase.

## Jalankan lokal
cd . && pip install -r server/requirements.txt && X_API_KEY=$(cat key.txt) python server/main.py
Buka http://localhost:3000/
