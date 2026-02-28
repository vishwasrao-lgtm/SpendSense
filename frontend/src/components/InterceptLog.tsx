"use client";

import { useState, useEffect } from "react";
import type { InterceptEntry } from "@/lib/api";
import { api } from "@/lib/api";

export default function InterceptLog() {
    const [entries, setEntries] = useState<InterceptEntry[]>([]);
    const [filter, setFilter] = useState<string>("all");

    useEffect(() => {
        const load = async () => {
            try {
                const f = filter === "all" ? undefined : filter;
                const data = await api.getInterceptLog(f);
                setEntries(data.intercepts);
            } catch { }
        };
        load();
        const interval = setInterval(load, 2000);
        return () => clearInterval(interval);
    }, [filter]);

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-3">
                <h3 className="text-sm font-semibold text-gray-300">Intervention History</h3>
                <div className="flex gap-1 ml-auto">
                    {["all", "cancelled", "proceeded"].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-3 py-1 rounded-md text-xs font-medium transition ${filter === f
                                    ? "bg-indigo-600 text-white"
                                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                                }`}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {entries.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-6">No flagged transactions yet.</p>
            ) : (
                <div className="max-h-[350px] overflow-y-auto space-y-2 pr-1">
                    {[...entries].reverse().map((entry) => {
                        const isCancelled = entry.user_decision === "cancelled";
                        return (
                            <details
                                key={entry.txn_id}
                                className="bg-gray-900/50 border border-gray-800 rounded-lg overflow-hidden group"
                            >
                                <summary className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-800/50 transition">
                                    <span className="text-lg">{isCancelled ? "❌" : "⚠️"}</span>
                                    <span className="text-sm font-medium text-white flex-1">
                                        {entry.txn_id}
                                    </span>
                                    <span className="text-sm font-semibold text-gray-300">
                                        ${entry.transaction.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                                    </span>
                                    <span
                                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${isCancelled
                                                ? "bg-red-900/40 text-red-400"
                                                : "bg-amber-900/40 text-amber-400"
                                            }`}
                                    >
                                        {entry.user_decision}
                                    </span>
                                </summary>
                                <div className="px-4 pb-3 space-y-1.5 border-t border-gray-800 pt-3">
                                    <p className="text-xs text-gray-400">
                                        <span className="text-gray-500">Time:</span>{" "}
                                        {new Date(entry.decision_timestamp).toLocaleString()}
                                    </p>
                                    <p className="text-xs text-gray-400">
                                        <span className="text-gray-500">Category:</span>{" "}
                                        {entry.transaction.category}
                                    </p>
                                    <div className="space-y-1">
                                        <p className="text-xs text-gray-500">Risk Flags:</p>
                                        {entry.risk_explanations.map((exp, i) => (
                                            <p key={i} className="text-xs text-gray-400 pl-3">• {exp}</p>
                                        ))}
                                    </div>
                                </div>
                            </details>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
