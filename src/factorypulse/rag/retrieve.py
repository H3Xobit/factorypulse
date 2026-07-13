"""Hybrid retrieval: exact fault-code match + vector similarity."""

from __future__ import annotations

import re
from typing import Any

from factorypulse.db import connect
from factorypulse.rag.embeddings import embed_text

_CODE = re.compile(r"E-\d{3}|E-AUDIO")


def extract_fault_codes(text: str) -> list[str]:
    return list(dict.fromkeys(_CODE.findall(text.upper())))


def retrieve(
    query: str,
    *,
    source_type: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    codes = extract_fault_codes(query)
    emb = embed_text(query)
    with connect() as conn:
        rows: list[dict[str, Any]] = []
        if codes:
            code_rows = conn.execute(
                """
                SELECT id, doc_id, section_id, source_type, machine, fault_code, title, body,
                       0.0::float8 AS distance
                FROM rag_chunks
                WHERE fault_code = ANY(%s)
                  AND (%s::text IS NULL OR source_type = %s)
                LIMIT %s
                """,
                (codes, source_type, source_type, top_k),
            ).fetchall()
            rows.extend(dict(r) for r in code_rows)
        vec_rows = conn.execute(
            """
            SELECT id, doc_id, section_id, source_type, machine, fault_code, title, body,
                   (embedding <=> %s::vector) AS distance
            FROM rag_chunks
            WHERE (%s::text IS NULL OR source_type = %s)
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (emb, source_type, source_type, emb, top_k),
        ).fetchall()
        seen = {r["section_id"] for r in rows}
        for r in vec_rows:
            item = dict(r)
            if item["section_id"] in seen:
                continue
            rows.append(item)
            seen.add(item["section_id"])
            if len(rows) >= top_k:
                break
    return rows[:top_k]
