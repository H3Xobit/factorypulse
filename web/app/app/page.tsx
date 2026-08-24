"use client";

import { useEffect, useState } from "react";
import { apiBase, apiHealthy } from "@/lib/api";
import { DEMO_EVENTS, demoReportFor, type EventRow, type ReportRow } from "@/lib/demo-data";

function readLang(): "en" | "ja" {
  if (typeof window === "undefined") return "en";
  try {
    const saved = window.localStorage.getItem("fp.lang");
    if (saved === "en" || saved === "ja") return saved;
  } catch {
    /* ignore */
  }
  return "en";
}

export default function AppPage() {
  const [events, setEvents] = useState<EventRow[]>([]);
  const [report, setReport] = useState<ReportRow | null>(null);
  const [lang, setLang] = useState<"en" | "ja">(() => readLang());

  useEffect(() => {
    try {
      window.localStorage.setItem("fp.lang", lang);
    } catch {
      /* ignore quota / private mode */
    }
  }, [lang]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"checking" | "live" | "demo">("checking");
  const [faultTypes, setFaultTypes] = useState<string[]>([
    "bearing_degradation",
    "abnormal_pump_audio",
    "seal_temp_drift",
  ]);
  const [lastInjectedType, setLastInjectedType] = useState<string | null>(null);

  async function refreshEventsLive() {
    const res = await fetch(`${apiBase()}/events?limit=20`, { cache: "no-store" });
    if (!res.ok) throw new Error(`events ${res.status}`);
    setEvents(await res.json());
  }

  useEffect(() => {
    let es: EventSource | null = null;
    (async () => {
      const healthy = await apiHealthy();
      if (!healthy) {
        setMode("demo");
        setEvents(DEMO_EVENTS);
        return;
      }
      setMode("live");
      try {
        const meta = await fetch(`${apiBase()}/meta`);
        if (meta.ok) {
          const body = await meta.json();
          if (Array.isArray(body.fault_types) && body.fault_types.length) {
            setFaultTypes(body.fault_types);
          }
        }
      } catch {
        /* keep defaults */
      }
      try {
        await refreshEventsLive();
      } catch (e) {
        setMode("demo");
        setEvents(DEMO_EVENTS);
        setError(String(e));
        return;
      }
      es = new EventSource(`${apiBase()}/events/stream`);
      es.addEventListener("events", (msg) => {
        try {
          setEvents(JSON.parse((msg as MessageEvent).data));
        } catch {
          /* ignore */
        }
      });
    })();
    return () => {
      if (es) es.close();
    };
  }, []);


  useEffect(() => {
    if (!lastInjectedType) return;
    const id = window.setTimeout(() => setLastInjectedType(null), 1500);
    return () => window.clearTimeout(id);
  }, [lastInjectedType]);

  async function inject(type: string) {
    setLastInjectedType(type);
    setBusy(true);
    setError(null);
    try {
      if (mode !== "live") {
        const stamped = DEMO_EVENTS.map((e, i) =>
          i === 0
            ? {
                ...e,
                summary: `Showcase inject: ${type}`,
                created_at: new Date().toISOString(),
              }
            : e
        );
        setEvents(stamped);
        return;
      }
      await fetch(`${apiBase()}/simulate/inject-fault?type=${type}`, { method: "POST" });
      await refreshEventsLive();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function diagnose(eventId: string) {
    setBusy(true);
    setError(null);
    try {
      if (mode !== "live") {
        setReport(demoReportFor(eventId));
        return;
      }
      const res = await fetch(`${apiBase()}/diagnose/${eventId}`, { method: "POST" });
      if (!res.ok) throw new Error(`diagnose ${res.status}`);
      setReport(await res.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }


  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const tag = target?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || target?.isContentEditable) return;

      if (e.key === "l" || e.key === "L") {
        if (busy) return;
        e.preventDefault();
        setLang((prev) => (prev === "en" ? "ja" : "en"));
        return;
      }

      if (!faultTypes.length || busy) return;

      let idx = -1;
      if (e.key === "i" || e.key === "I") {
        idx = 0;
      } else if (/^[1-9]$/.test(e.key)) {
        idx = Number(e.key) - 1;
      } else {
        return;
      }
      if (idx < 0 || idx >= faultTypes.length) return;
      e.preventDefault();
      void inject(faultTypes[idx]);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [faultTypes, busy, mode]);


  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-6 py-10 lg:grid-cols-2">
      <div className="lg:col-span-2">
      {mode === "demo" && (
        <div className="mb-4 rounded-2xl border border-accent/40 bg-accent/10 px-4 py-3 text-sm text-zinc-200">
          Showcase mode: API offline. Inject and diagnose still work with demo data.
          For the full stack, run <span className="font-mono text-accent">make demo</span> locally.
        </div>
      )}

      </div>
      <section className="rounded-2xl border border-white/[0.06] bg-ink-surface p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl text-white">Live events</h1>
            <p className="mt-1 text-xs uppercase tracking-wide text-zinc-500">
              {mode === "checking" && "Checking API..."}
              {mode === "live" && "Connected to FastAPI backend"}
              {mode === "demo" && "Showcase mode (API offline)"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {faultTypes.map((t, i) => (
              <button
                key={t}
                disabled={busy}
                onClick={() => inject(t)}
                className={`rounded-full border px-3 py-1 text-xs disabled:opacity-50 ${
                  lastInjectedType === t
                    ? "border-accent text-accent"
                    : "border-white/[0.06] text-zinc-300 hover:border-accent hover:text-accent"
                }`}
              >
                {i < 9 && (
                  <span className="mr-1 font-mono text-accent">{i + 1}</span>
                )}
                inject {t.replaceAll("_", " ")}
              </button>
            ))}
          </div>
        </div>
        {faultTypes.length > 0 && (
          <p className={`mb-3 text-xs ${busy ? "text-zinc-600" : "text-zinc-500"}`}>
            {busy ? (
              <>Injecting...</>
            ) : (
              <>
                Press <span className="font-mono text-accent">i</span> or{" "}
                <span className="font-mono text-accent">1-9</span> to inject a fault type.
              </>
            )}
          </p>
        )}
        {mode === "live" && (
          <p className="mb-3 text-xs text-zinc-500">
            Fault inject types come from <span className="font-mono text-accent">GET /meta</span>.
            Full API reference:{" "}
            <a
              href={`${apiBase()}/docs`}
              target="_blank"
              rel="noreferrer"
              className="text-accent underline-offset-2 hover:underline"
            >
              /docs
            </a>
            .
          </p>
        )}
        {error && <p className="mb-3 text-sm text-red-400">{error}</p>}
        <div className="space-y-3">
          {events.map((e) => (
            <button
              key={e.event_id}
              onClick={() => diagnose(e.event_id)}
              className="block w-full rounded-2xl border border-white/[0.06] bg-ink-elevated p-4 text-left hover:border-accent/40"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-mono text-sm text-accent">{e.fault_code || "n/a"}</span>
                <span className="text-xs uppercase text-zinc-500">{e.severity}</span>
              </div>
              <div className="mt-1 text-sm text-white">{e.summary}</div>
              <div className="mt-2 flex justify-between text-xs text-zinc-500">
                <span>{e.machine}</span>
                <span>{(e.score * 100).toFixed(0)}%</span>
              </div>
            </button>
          ))}
          {!events.length && <p className="text-sm text-zinc-500">No events yet. Inject a fault.</p>}
        </div>
      </section>

      <section className="rounded-2xl border border-white/[0.06] bg-ink-surface p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-2xl text-white">Triage report</h2>
          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] uppercase tracking-wide ${
                busy ? "text-zinc-700" : "text-zinc-600"
              }`}
            >
              <span className={`font-mono normal-case ${busy ? "text-zinc-700" : "text-zinc-500"}`}>
                l
              </span>{" "}
              toggle
            </span>
            <div className="flex rounded-full border border-white/[0.06] p-1">
              {(["en", "ja"] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  disabled={busy}
                  onClick={() => setLang(l)}
                  className={`rounded-full px-3 py-1 text-xs uppercase disabled:opacity-50 ${
                    lang === l ? "bg-accent text-black" : "text-zinc-400"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
        </div>
        {!report && <p className="text-sm text-zinc-500">Select an event to run diagnosis.</p>}
        {report && (
          <div className="space-y-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-zinc-500">Root cause</div>
              <div className="text-lg text-white">{report.root_cause}</div>
            </div>
            <div className="font-mono text-accent">{(report.confidence * 100).toFixed(0)}% confidence</div>
            <div>
              <div className="text-xs uppercase tracking-wide text-zinc-500">Action</div>
              <p className="text-sm text-zinc-300">{report.recommended_action}</p>
            </div>
            <pre className="whitespace-pre-wrap rounded-2xl border border-white/[0.06] bg-ink-base p-4 text-sm leading-relaxed text-zinc-300">
              {lang === "en" ? report.report_en : report.report_ja}
            </pre>
          </div>
        )}
      </section>
    </main>
  );
}
