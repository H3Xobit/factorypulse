"use client";

import { motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { fadeUp, stagger } from "@/lib/motion";

const features = [
  {
    title: "Multimodal detect",
    body: "Audio classifiers, time-series residuals, and rule thresholds fire AnomalyEvents in one stream.",
  },
  {
    title: "Cited diagnosis",
    body: "RAG over manuals and incidents returns root cause, confidence, and page-level citations.",
  },
  {
    title: "Bilingual triage",
    body: "English and Japanese reports keep fault codes and part numbers untouched.",
  },
  {
    title: "Eval-first",
    body: "Public accuracy, retrieval, and hallucination numbers ship with every model change.",
  },
];

const stats = [
  { label: "Median triage", value: "< 30s" },
  { label: "Fault inject types", value: "3" },
  { label: "Manual corpus", value: "3 PDFs" },
  { label: "Golden cases", value: "20" },
];

export default function LandingPage() {
  const reduce = useReducedMotion();
  return (
    <main>
      <section className="shader-hero relative overflow-hidden border-b border-white/[0.06]">
        <div className="pointer-events-none absolute inset-0 opacity-40">
          <div className="absolute -right-10 top-10 h-72 w-72 animate-pulse rounded-full bg-accent/20 blur-3xl" />
          <div className="absolute bottom-0 left-10 h-56 w-56 rounded-full bg-accent/10 blur-3xl" />
        </div>
        <motion.div
          className="relative mx-auto max-w-6xl px-6 py-24 md:py-32"
          variants={reduce ? undefined : stagger}
          initial={reduce ? undefined : "hidden"}
          animate={reduce ? undefined : "show"}
        >
          <motion.p variants={fadeUp} className="mb-4 text-sm uppercase tracking-[0.2em] text-accent">
            Manufacturing triage copilot
          </motion.p>
          <motion.h1
            variants={fadeUp}
            className="max-w-4xl font-display text-5xl leading-[1.05] tracking-tight text-white md:text-7xl"
          >
            FactoryPulse
          </motion.h1>
          <motion.p variants={fadeUp} className="mt-6 max-w-2xl text-lg text-zinc-400">
            Correlate machine audio, sensor streams, and equipment manuals into a cited bilingual
            triage report before the line loses another half hour.
          </motion.p>
          <motion.div variants={fadeUp} className="mt-10 flex flex-wrap gap-3">
            <Link
              href="/app"
              className="rounded-full bg-accent px-6 py-3 text-sm font-medium text-black shadow-accent"
            >
              Open console
            </Link>
            <Link
              href="/evals"
              className="rounded-full border border-white/[0.06] bg-ink-surface px-6 py-3 text-sm text-zinc-200"
            >
              View evals
            </Link>
          </motion.div>
          <motion.div variants={fadeUp} className="mt-16 grid grid-cols-2 gap-4 md:grid-cols-4">
            {stats.map((s) => (
              <div
                key={s.label}
                className="rounded-2xl border border-white/[0.06] bg-ink-surface/80 p-4"
              >
                <div className="font-mono text-2xl text-accent">{s.value}</div>
                <div className="mt-1 text-sm text-zinc-500">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      <motion.section
        className="mx-auto max-w-6xl px-6 py-24 md:py-32"
        variants={stagger}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-80px" }}
      >
        <motion.h2 variants={fadeUp} className="font-display text-3xl text-white md:text-5xl">
          Built for the maintenance bay
        </motion.h2>
        <div className="mt-12 grid gap-4 md:grid-cols-2">
          {features.map((f) => (
            <motion.div
              key={f.title}
              variants={fadeUp}
              className="rounded-2xl border border-white/[0.06] bg-ink-elevated p-6"
            >
              <h3 className="text-lg text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">{f.body}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>
    </main>
  );
}
