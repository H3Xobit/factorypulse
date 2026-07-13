"""LLM provider router with offline deterministic fallback for CI/demo."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from factorypulse.settings import get_settings

_CODE = re.compile(r"E-\d{3}|E-AUDIO")


class LLMRouter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.offline = os.getenv("FP_OFFLINE_LLM", "1") == "1" or not (
            self.settings.anthropic_api_key or self.settings.groq_api_key
        )

    def available_providers(self) -> list[str]:
        providers: list[str] = []
        if self.settings.anthropic_api_key:
            providers.append("anthropic")
        if self.settings.groq_api_key:
            providers.append("groq")
        if self.offline:
            providers.append("offline")
        return providers

    def complete_json(self, *, role: str, system: str, user: str) -> dict[str, Any]:
        if self.offline or role in {"diagnose", "verify"} and self.offline:
            return self._offline_json(role=role, user=user)
        prefer = "anthropic" if role == "diagnose" else "groq"
        raw = self._complete(system=system, user=user, prefer=prefer)
        return json.loads(raw)

    def complete_text(self, *, role: str, system: str, user: str) -> str:
        if self.offline or role == "translate" and self.offline:
            return self._offline_translate(user)
        return self._complete(system=system, user=user, prefer="groq")

    def _complete(self, *, system: str, user: str, prefer: str) -> str:
        if prefer == "groq" and self.settings.groq_api_key:
            from groq import Groq

            client = Groq(api_key=self.settings.groq_api_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.0,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content or ""
        if self.settings.anthropic_api_key:
            import anthropic

            client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                temperature=0.2,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return resp.content[0].text
        return json.dumps(self._offline_json(role="diagnose", user=user))

    def _offline_json(self, *, role: str, user: str) -> dict[str, Any]:
        if role == "verify":
            return {"unsupported_claims": 0, "notes": "offline verify: evidence present"}
        codes = _CODE.findall(user.upper())
        code = codes[0] if codes else None
        cause_map = {
            "E-102": "Seal jaw heater PID drift",
            "E-105": "Worn PTFE seal tape",
            "E-110": "Thermocouple lag on jaw B",
            "E-310": "Outer race bearing spall",
            "E-312": "Fan blade imbalance from dust buildup",
            "E-315": "Loose pedestal bolts",
            "E-220": "Impeller cavitation from low NPSH",
            "E-225": "Coupling misalignment after maintenance",
            "E-AUDIO": "Bearing grease contamination",
        }
        root = cause_map.get(code or "", "Process deviation requiring inspection")
        m_cause = re.search(r"Root cause:\s*([^.\n]+)", user)
        if m_cause:
            root = m_cause.group(1).strip()
        section_ids = re.findall(r"section_id=([^\s]+)", user)
        section = section_ids[0] if section_ids else f"generic:{code or 'NA'}"
        source_type = "incident" if section.startswith("INC-") else "manual"
        return {
            "root_cause": root,
            "confidence": 0.82 if code else 0.55,
            "evidence": [
                {
                    "source_type": source_type,
                    "section_id": section,
                    "quote": f"Matched guidance for {code or 'symptom'}",
                }
            ],
            "recommended_action": (
                f"Inspect and remediate cause linked to {code or 'alarm'}; verify clear."
            ),
            "estimated_downtime_risk": "medium",
        }

    def _offline_translate(self, report_en: str) -> str:
        # Keep codes; provide a concise JA wrapper for demo without external API.
        codes = ", ".join(_CODE.findall(report_en.upper())) or "N/A"
        return (
            "【トリアージ報告】\n"
            f"{report_en}\n\n"
            f"（日本語要約）故障コード {codes} について、上記の原因と処置を実施してください。"
            "部品番号と故障コードはそのまま維持しています。"
        )
