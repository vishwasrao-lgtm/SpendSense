const API_BASE = "http://localhost:5000/api";

export interface Transaction {
  txn_id: string;
  user_id: string;
  timestamp: string;
  amount: number;
  category: string;
  recipient_status: string;
  monthly_budget_remaining: number;
  device_id: string;
  location: string;
  channel: string;
  is_flagged: boolean;
  user_decision: string;
}

export interface RiskFlag {
  rule_name: string;
  explanation: string;
  severity: "high" | "medium" | "low";
  detector_type: "behavioral" | "contextual";
}

export interface Assessment {
  transaction: Transaction;
  risk_flags: RiskFlag[];
  is_flagged: boolean;
  future_impact: { [key: string]: number };
}

export interface Metrics {
  total_transactions: number;
  total_flagged: number;
  money_saved: number;
  override_rate: number;
  impulsivity_score: number;
}

export interface InterceptEntry {
  txn_id: string;
  transaction: Transaction;
  risk_flags: RiskFlag[];
  user_decision: string;
  decision_timestamp: string;
  risk_explanations: string[];
}

export interface StatusResponse {
  loaded: boolean;
  total_transactions: number;
  processed: number;
  has_pending: boolean;
}

async function fetchJSON(url: string, opts?: RequestInit) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

export const api = {
  getStatus: (): Promise<StatusResponse> => fetchJSON(`${API_BASE}/status`),

  loadSample: () =>
    fetchJSON(`${API_BASE}/load-sample`, { method: "POST" }),

  uploadFile: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetchJSON(`${API_BASE}/load`, { method: "POST", body: fd });
  },

  processNext: () =>
    fetchJSON(`${API_BASE}/process-next`, { method: "POST" }),

  processAll: () =>
    fetchJSON(`${API_BASE}/process-all`, { method: "POST" }),

  decide: (decision: "cancelled" | "proceeded") =>
    fetchJSON(`${API_BASE}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    }),

  getTransactions: (): Promise<{ transactions: Transaction[]; total: number }> =>
    fetchJSON(`${API_BASE}/transactions`),

  getMetrics: (): Promise<Metrics> => fetchJSON(`${API_BASE}/metrics`),

  getInterceptLog: (
    filter?: string
  ): Promise<{ intercepts: InterceptEntry[]; total: number }> =>
    fetchJSON(
      `${API_BASE}/intercept-log${filter ? `?filter=${filter}` : ""}`
    ),
};
