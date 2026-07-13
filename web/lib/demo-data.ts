export type EventRow = {
  event_id: string;
  machine: string;
  source: string;
  severity: string;
  fault_code?: string;
  score: number;
  summary: string;
  created_at?: string;
};

export type ReportRow = {
  report_id: string;
  event_id?: string;
  machine: string;
  root_cause: string;
  confidence: number;
  report_en: string;
  report_ja: string;
  recommended_action: string;
};

export const DEMO_EVENTS: EventRow[] = [
  {
    event_id: "11111111-1111-1111-1111-111111111101",
    machine: "fan_unit",
    source: "injected",
    severity: "fault",
    fault_code: "E-310",
    score: 0.95,
    summary: "Injected fault: bearing_degradation",
    created_at: "2026-07-13T01:00:00Z",
  },
  {
    event_id: "11111111-1111-1111-1111-111111111102",
    machine: "centrifugal_pump",
    source: "audio",
    severity: "fault",
    fault_code: "E-AUDIO",
    score: 0.88,
    summary: "Audio classifier flagged anomalous machine sound",
    created_at: "2026-07-13T00:58:00Z",
  },
  {
    event_id: "11111111-1111-1111-1111-111111111103",
    machine: "vffs_packager",
    source: "rules",
    severity: "warn",
    fault_code: "E-102",
    score: 0.76,
    summary: "Seal jaw temperature deviation",
    created_at: "2026-07-13T00:55:00Z",
  },
];

const REPORTS: Record<string, ReportRow> = {
  "11111111-1111-1111-1111-111111111101": {
    report_id: "22222222-2222-2222-2222-222222222201",
    event_id: "11111111-1111-1111-1111-111111111101",
    machine: "fan_unit",
    root_cause: "Outer race bearing spall",
    confidence: 0.86,
    recommended_action: "Replace DE bearing; verify alignment and pedestal torque.",
    report_en:
      "FactoryPulse Triage Report\nMachine: fan_unit\nFault code: E-310\nRoot cause: Outer race bearing spall\nConfidence: 0.86\nRecommended action: Replace DE bearing; verify alignment and pedestal torque.\nDowntime risk: medium\nEvidence:\n- [manual] fan_unit:E-310: Bearing acceleration peak guidance",
    report_ja:
      "【トリアージ報告】\n設備: fan_unit\n故障コード: E-310\n推定原因: アウターレース軸受のスポール\n信頼度: 0.86\n推奨処置: DE軸受を交換し、芯出しと台座トルクを確認してください。\n故障コードと部品番号はそのまま維持しています。",
  },
  "11111111-1111-1111-1111-111111111102": {
    report_id: "22222222-2222-2222-2222-222222222202",
    event_id: "11111111-1111-1111-1111-111111111102",
    machine: "centrifugal_pump",
    root_cause: "Bearing grease contamination",
    confidence: 0.81,
    recommended_action: "Inspect grease condition; relubricate or replace bearing as needed.",
    report_en:
      "FactoryPulse Triage Report\nMachine: centrifugal_pump\nFault code: E-AUDIO\nRoot cause: Bearing grease contamination\nConfidence: 0.81\nRecommended action: Inspect grease condition; relubricate or replace bearing as needed.\nEvidence:\n- [manual] centrifugal_pump:E-AUDIO: Abnormal acoustic signature",
    report_ja:
      "【トリアージ報告】\n設備: centrifugal_pump\n故障コード: E-AUDIO\n推定原因: 軸受グリース汚染\n信頼度: 0.81\n推奨処置: グリース状態を確認し、必要に応じて再給油または軸受交換を行ってください。",
  },
  "11111111-1111-1111-1111-111111111103": {
    report_id: "22222222-2222-2222-2222-222222222203",
    event_id: "11111111-1111-1111-1111-111111111103",
    machine: "vffs_packager",
    root_cause: "Seal jaw heater PID drift",
    confidence: 0.84,
    recommended_action: "Retune jaw heater PID; inspect thermocouple and SSR.",
    report_en:
      "FactoryPulse Triage Report\nMachine: vffs_packager\nFault code: E-102\nRoot cause: Seal jaw heater PID drift\nConfidence: 0.84\nRecommended action: Retune jaw heater PID; inspect thermocouple and SSR.\nEvidence:\n- [manual] vffs_packager:E-102: Seal jaw temperature deviation",
    report_ja:
      "【トリアージ報告】\n設備: vffs_packager\n故障コード: E-102\n推定原因: シールジョーヒータPIDドリフト\n信頼度: 0.84\n推奨処置: ジョーヒータPIDを再調整し、熱電対とSSRを点検してください。",
  },
};

export function demoReportFor(eventId: string): ReportRow {
  return (
    REPORTS[eventId] || {
      report_id: "22222222-2222-2222-2222-222222222299",
      event_id: eventId,
      machine: "fan_unit",
      root_cause: "Process deviation requiring inspection",
      confidence: 0.7,
      recommended_action: "Inspect the alarmed subsystem and verify clear.",
      report_en: "FactoryPulse Triage Report\nRoot cause: Process deviation requiring inspection",
      report_ja: "【トリアージ報告】点検が必要な工程偏差です。",
    }
  );
}

export const DEMO_EVAL = {
  timestamp: "2026-07-13T01:15:00Z",
  n: 10,
  diagnosis_accuracy: 0.9,
  retrieval_precision_at_5: 1.0,
  hallucination_rate: 0.0,
  latency_p50_s: 0.03,
  latency_p95_s: 0.05,
  cost_per_report_usd: 0.0,
};
