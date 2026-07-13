#!/bin/sh
set -e
echo "Waiting for database..."
python -c "import time,os,psycopg
url=os.environ['DATABASE_URL']
ok=False
for _ in range(40):
  try:
    with psycopg.connect(url) as c:
      c.execute('SELECT 1')
    ok=True
    break
  except Exception:
    time.sleep(2)
if not ok:
  raise SystemExit('database not ready')
"

if [ -f data/manuals/manual_chunks.json ] && [ -f data/incidents/incidents_corpus.json ]; then
  echo "Ingesting RAG corpus..."
  python -m factorypulse.rag.ingest || true
fi

exec uvicorn factorypulse.api.main:app --host 0.0.0.0 --port 8000
