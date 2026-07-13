"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DEMO_EVAL } from "@/lib/demo-data";

type EvalRow = {
  timestamp: string;
  n: number;
  diagnosis_accuracy: number;
  retrieval_precision_at_5: number;
  hallucination_rate: number;
  latency_p50_s: number;
  latency_p95_s: number;
};

export default function EvalsPage() {
  const [latest, setLatest] = useState<EvalRow | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_BASE_PATH || ""}/evals/latest.json`)
      .then(async (r) => {
        if (!r.ok) return DEMO_EVAL;
        const d = await r.json();
        if (!d || typeof d.diagnosis_accuracy !== "number") return DEMO_EVAL;
        return d as EvalRow;
      })
      .then(setLatest)
      .catch(() => setLatest(DEMO_EVAL));
  }, []);

  const chart = latest
    ? [
        { name: "Diagnosis", value: latest.diagnosis_accuracy },
        { name: "Retrieval@5", value: latest.retrieval_precision_at_5 },
        { name: "1-Halluc", value: 1 - latest.hallucination_rate },
      ]
    : [];

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="font-display text-4xl text-white">Eval dashboard</h1>
      <p className="mt-2 max-w-2xl text-zinc-400">
        Numbers from evals/results. CI fails if diagnosis accuracy drops below 0.7 or hallucination
        exceeds 0.05.
      </p>
      {latest && (
        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/[0.06] bg-ink-surface p-5">
            <div className="grid grid-cols-2 gap-4">
              <Metric label="Diagnosis accuracy" value={latest.diagnosis_accuracy} />
              <Metric label="Retrieval P@5" value={latest.retrieval_precision_at_5} />
              <Metric label="Hallucination rate" value={latest.hallucination_rate} />
              <Metric label="Latency p50 (s)" value={latest.latency_p50_s} raw />
            </div>
            <p className="mt-4 font-mono text-xs text-zinc-500">
              n={latest.n} · {latest.timestamp}
            </p>
          </div>
          <div className="h-72 rounded-2xl border border-white/[0.06] bg-ink-surface p-5">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="name" stroke="#a1a1aa" />
                <YAxis domain={[0, 1]} stroke="#a1a1aa" />
                <Tooltip />
                <Bar dataKey="value" fill="#f97316" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </main>
  );
}

function Metric({ label, value, raw }: { label: string; value: number; raw?: boolean }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="font-mono text-2xl text-accent">
        {raw ? value.toFixed(2) : `${(value * 100).toFixed(1)}%`}
      </div>
    </div>
  );
}
