"""Ingest manuals + incidents into pgvector."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from factorypulse.db import connect
from factorypulse.rag.embeddings import embed_text

logger = logging.getLogger(__name__)


def _upsert_chunk(conn, chunk: dict, embedding: list[float]) -> None:
    conn.execute(
        """
        INSERT INTO rag_chunks (
            doc_id, section_id, source_type, machine, fault_code, title, body, metadata, embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        """,
        (
            chunk["doc_id"],
            chunk["section_id"],
            chunk["source_type"],
            chunk.get("machine"),
            chunk.get("fault_code"),
            chunk["title"],
            chunk["body"],
            json.dumps(chunk.get("metadata") or {}),
            embedding,
        ),
    )


def load_manual_chunks(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_incident_chunks(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    chunks = []
    for r in rows:
        chunks.append(
            {
                "doc_id": r["id"],
                "section_id": r["id"],
                "source_type": "incident",
                "machine": r["machine"],
                "fault_code": r.get("fault_code"),
                "title": f"{r['id']} {r['machine']}",
                "body": (
                    f"Symptom: {r['symptom_description']}. "
                    f"Root cause: {r['root_cause']}. "
                    f"Resolution: {r['resolution']}. "
                    f"Downtime minutes: {r['downtime_minutes']}."
                ),
                "metadata": {"timestamp": r["timestamp"]},
            }
        )
    return chunks


def ingest(manuals: Path, incidents: Path) -> int:
    chunks = load_manual_chunks(manuals) + load_incident_chunks(incidents)
    with connect() as conn:
        conn.execute("DELETE FROM rag_chunks")
        for chunk in chunks:
            text = f"{chunk['title']}\n{chunk['body']}"
            if chunk.get("fault_code"):
                text = f"{chunk['fault_code']} {text}"
            emb = embed_text(text)
            _upsert_chunk(conn, chunk, emb)
        conn.commit()
    logger.info("ingested %s chunks", len(chunks))
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manuals", type=Path, default=Path("data/manuals/manual_chunks.json"))
    parser.add_argument(
        "--incidents", type=Path, default=Path("data/incidents/incidents_corpus.json")
    )
    args = parser.parse_args()
    logging.basicConfig(level="INFO")
    n = ingest(args.manuals, args.incidents)
    print(f"ingested {n}")


if __name__ == "__main__":
    main()
