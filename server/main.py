import os, sqlite3, csv, io, json
from flask import Flask, request, jsonify, send_from_directory

BASE = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(BASE, "public")
# Vercel: filesystem read-only, hanya /tmp bisa ditulis. Lokal: pakai data/ews.db
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/ews.db"
else:
    DB_PATH = os.path.join(BASE, "data", "ews.db")
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

API_KEY = os.environ.get("X_API_KEY", "")

app = Flask(__name__, static_folder=PUBLIC, static_url_path="")

SCHEMA = """
CREATE TABLE IF NOT EXISTS crawls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crawling_date TEXT NOT NULL,
  filename TEXT,
  total INTEGER NOT NULL DEFAULT 0,
  total_negative INTEGER NOT NULL DEFAULT 0,
  total_positive INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crawl_id INTEGER NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  priority INTEGER NOT NULL,
  tanggal TEXT NOT NULL,
  platform TEXT NOT NULL,
  kategori TEXT NOT NULL,
  topik TEXT NOT NULL,
  sentimen TEXT NOT NULL,
  url TEXT NOT NULL,
  react TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_posts_crawl ON posts(crawl_id);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def split_pipe(line):
    out=[]; cur=""; inQ=False; i=0
    while i < len(line):
        ch=line[i]
        if ch=='"':
            if inQ and i+1 < len(line) and line[i+1]=='"':
                cur+='"'; i+=1
            else:
                inQ=not inQ
        elif ch=='|' and not inQ:
            out.append(cur); cur=""
        else:
            cur+=ch
        i+=1
    out.append(cur)
    return [s.strip().strip('"') for s in out]

def parse_csv_text(text):
    lines=[l for l in text.splitlines() if l.strip()!=""]
    if len(lines)<2: return []
    header=split_pipe(lines[0])
    def idx(n):
        for j,h in enumerate(header):
            if n.lower() in h.lower(): return j
        return -1
    iP,iT,iPl,iK,iTo,iS,iU,iR = idx("priority"), idx("tanggal"), idx("platform"), idx("kategori"), idx("topik"), idx("sentimen"), idx("url"), idx("react")
    rows=[]
    for line in lines[1:]:
        c=split_pipe(line)
        def get(i):
            return c[i] if 0<=i<len(c) else ""
        try: pr=int(get(iP))
        except: pr=4
        rows.append({"priority":pr,"tanggal":get(iT),"platform":get(iPl),"kategori":get(iK),"topik":get(iTo),"sentimen":get(iS),"url":get(iU),"react":get(iR)})
    return rows

def sort_rows(rows):
    from datetime import datetime
    MONTHS={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    def parse_dt(s):
        try:
            # 09-Nov-2026 16:34:42
            parts=s.split(" "); d=parts[0].split("-"); t=parts[1].split(":") if len(parts)>1 else ["0","0","0"]
            return datetime(int(d[2]), MONTHS.get(d[1],1), int(d[0]), int(t[0]), int(t[1]), int(t[2]))
        except: return datetime.min
    return sorted(rows, key=lambda r: (r["priority"], r["kategori"], -parse_dt(r["tanggal"]).timestamp()))

@app.route("/")
def index():
    return send_from_directory(PUBLIC, "index.html")

@app.route("/api/ews/latest")
def latest():
    conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT * FROM crawls ORDER BY id DESC LIMIT 1")
    crawl=cur.fetchone()
    if not crawl:
        return jsonify({"success":True,"crawl_id":None,"crawling_date":None,"rows":[],"message":"Belum ada crawl, pakai data embed di dashboard"})
    cur.execute("SELECT priority,tanggal,platform,kategori,topik,sentimen,url,react FROM posts WHERE crawl_id=?", (crawl["id"],))
    rows=[dict(r) for r in cur.fetchall()]
    conn.close()
    rows=sort_rows(rows)
    return jsonify({"success":True,"crawl_id":crawl["id"],"crawling_date":crawl["crawling_date"],"total":crawl["total"],"rows":rows})

@app.route("/api/ews/history")
def history():
    conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT id,crawling_date,filename,total,total_negative,total_positive,created_at FROM crawls ORDER BY id DESC")
    out=[dict(r) for r in cur.fetchall()]; conn.close()
    return jsonify({"success":True,"crawls":out})

@app.route("/api/ews/history/<int:crawl_id>")
def history_detail(crawl_id):
    conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT * FROM crawls WHERE id=?", (crawl_id,))
    crawl=cur.fetchone()
    if not crawl:
        conn.close(); return jsonify({"success":False,"error":"Crawl tidak ditemukan"}), 404
    cur.execute("SELECT priority,tanggal,platform,kategori,topik,sentimen,url,react FROM posts WHERE crawl_id=?", (crawl_id,))
    rows=sort_rows([dict(r) for r in cur.fetchall()]); conn.close()
    return jsonify({"success":True,"crawl":dict(crawl),"rows":rows})

@app.route("/api/ews", methods=["POST"])
def upload():
    # Auth: header X-API-Key harus sama dengan env X_API_KEY
    if not API_KEY:
        return jsonify({"success":False,"error":"Server belum set X_API_KEY"}), 500
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"success":False,"error":"Unauthorized: X-API-Key salah"}), 401
    if "file" not in request.files:
        return jsonify({"success":False,"error":"Field file tidak ditemukan"}), 400
    f=request.files["file"]
    crawling_date=request.form.get("crawling_date","").strip() or "11-Nov-2026 13:21:52"
    try:
        text=f.read().decode("utf-8-sig")
    except Exception as e:
        return jsonify({"success":False,"error":f"Gagal baca CSV: {e}"}), 400
    rows=parse_csv_text(text)
    if not rows:
        return jsonify({"success":False,"error":"CSV kosong / format tidak dikenali"}), 400
    total=len(rows); neg=sum(1 for r in rows if r["sentimen"].lower()=="negative"); pos=sum(1 for r in rows if r["sentimen"].lower()=="positive")
    conn=get_db(); cur=conn.cursor()
    cur.execute("INSERT INTO crawls (crawling_date,filename,total,total_negative,total_positive) VALUES (?,?,?,?,?)", (crawling_date, f.filename, total, neg, pos))
    crawl_id=cur.lastrowid
    for r in rows:
        cur.execute("INSERT INTO posts (crawl_id,priority,tanggal,platform,kategori,topik,sentimen,url,react) VALUES (?,?,?,?,?,?,?,?,?)", (crawl_id, r["priority"], r["tanggal"], r["platform"], r["kategori"], r["topik"], r["sentimen"], r["url"], r["react"]))
    conn.commit(); conn.close()
    # Simpan latest untuk lokal (di Vercel akan gagal tulis, abaikan)
    try:
        if not os.environ.get("VERCEL"):
            os.makedirs(os.path.join(BASE,"data"), exist_ok=True)
            with open(os.path.join(BASE,"data","latest.json"),"w",encoding="utf-8") as fh:
                json.dump({"crawling_date":crawling_date,"total":total,"rows":rows}, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return jsonify({"success":True,"crawl_id":crawl_id,"crawling_date":crawling_date,"total":total,"total_negative":neg,"total_positive":pos,"rows":rows})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), debug=False)
