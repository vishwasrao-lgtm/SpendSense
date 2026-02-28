"use client";

import { useState, useCallback, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import MetricsBar from "@/components/MetricsBar";
import TransactionFeed from "@/components/TransactionFeed";
import InterventionModal from "@/components/InterventionModal";
import InterceptLog from "@/components/InterceptLog";
import { CategoryPieChart, TimelineChart } from "@/components/Charts";
import ImpulsivityGauge from "@/components/ImpulsivityGauge";
import { api, type Transaction, type Assessment, type Metrics } from "@/lib/api";

export default function Home() {
  const [loaded, setLoaded] = useState(false);
  const [processed, setProcessed] = useState(0);
  const [total, setTotal] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [pendingAssessment, setPendingAssessment] = useState<Assessment | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [activeTab, setActiveTab] = useState<"feed" | "intercepts" | "insights">("feed");

  const refreshData = useCallback(async () => {
    try {
      const [txData, metricsData, status] = await Promise.all([
        api.getTransactions(),
        api.getMetrics(),
        api.getStatus(),
      ]);
      setTransactions(txData.transactions);
      setMetrics(metricsData);
      setProcessed(status.processed);
      setTotal(status.total_transactions);
      setLoaded(status.loaded);
    } catch { }
  }, []);

  const handleDataLoaded = useCallback(async () => {
    const status = await api.getStatus();
    setLoaded(true);
    setTotal(status.total_transactions);
    setProcessed(0);
    setPendingAssessment(null);
    await refreshData();
  }, [refreshData]);

  const handleProcessNext = useCallback(async () => {
    setProcessing(true);
    try {
      const result = await api.processNext();
      if (result.status === "flagged") {
        setPendingAssessment(result.assessment);
      } else {
        setProcessed(result.processed);
      }
      await refreshData();
    } finally {
      setProcessing(false);
    }
  }, [refreshData]);

  const handleProcessAll = useCallback(async () => {
    setProcessing(true);
    try {
      const result = await api.processAll();
      if (result.status === "flagged") {
        setPendingAssessment(result.assessment);
      }
      setProcessed(result.processed);
      await refreshData();
    } finally {
      setProcessing(false);
    }
  }, [refreshData]);

  const handleDecide = useCallback(
    async (decision: "cancelled" | "proceeded") => {
      await api.decide(decision);
      setPendingAssessment(null);
      await refreshData();
    },
    [refreshData]
  );

  // poll metrics every 2s
  useEffect(() => {
    if (!loaded) return;
    const interval = setInterval(refreshData, 2000);
    return () => clearInterval(interval);
  }, [loaded, refreshData]);

  const tabs = [
    { id: "feed" as const, label: "📋 Transaction Feed" },
    { id: "intercepts" as const, label: "🛡️ Intercept Log" },
    { id: "insights" as const, label: "📊 Patterns & Insights" },
  ];

  return (
    <div className="flex h-screen bg-gray-950 text-gray-200">
      <Sidebar
        onDataLoaded={handleDataLoaded}
        loaded={loaded}
        processed={processed}
        total={total}
        hasPending={!!pendingAssessment}
        onProcessNext={handleProcessNext}
        onProcessAll={handleProcessAll}
        processing={processing}
      />

      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        <MetricsBar metrics={metrics} />

        {/* Tabs */}
        <div className="flex gap-1 border-b border-gray-800 pb-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition ${activeTab === tab.id
                  ? "bg-gray-900 text-white border-b-2 border-indigo-500"
                  : "text-gray-500 hover:text-gray-300"
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="min-h-[400px]">
          {activeTab === "feed" && <TransactionFeed transactions={transactions} />}
          {activeTab === "intercepts" && <InterceptLog />}
          {activeTab === "insights" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <CategoryPieChart transactions={transactions} />
                <TimelineChart transactions={transactions} />
              </div>
              {metrics && <ImpulsivityGauge score={metrics.impulsivity_score} />}
            </div>
          )}
        </div>
      </main>

      {/* Intervention modal overlay */}
      {pendingAssessment && (
        <InterventionModal assessment={pendingAssessment} onDecide={handleDecide} />
      )}
    </div>
  );
}
