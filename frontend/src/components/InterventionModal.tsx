"use client";

import { useState, useEffect, useCallback } from "react";
import { ShieldAlert, Clock, X, ChevronRight } from "lucide-react";
import type { Assessment } from "@/lib/api";

interface InterventionModalProps {
    assessment: Assessment;
    onDecide: (decision: "cancelled" | "proceeded") => void;
}

export default function InterventionModal({ assessment, onDecide }: InterventionModalProps) {
    const [countdown, setCountdown] = useState(10);

    useEffect(() => {
        setCountdown(10);
        const timer = setInterval(() => {
            setCountdown((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
        return () => clearInterval(timer);
    }, [assessment.transaction.txn_id]);

    const { transaction, risk_flags, future_impact } = assessment;
    const severityColors: Record<string, string> = {
        high: "bg-red-900/40 border-red-700 text-red-300",
        medium: "bg-amber-900/40 border-amber-700 text-amber-300",
        low: "bg-blue-900/40 border-blue-700 text-blue-300",
    };

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-red-900/50 to-amber-900/50 px-6 py-4 flex items-center gap-3">
                    <ShieldAlert className="text-red-400" size={24} />
                    <h2 className="text-lg font-bold text-white">Risk Alert</h2>
                </div>

                <div className="p-6 space-y-5">
                    {/* Transaction details */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-800 rounded-xl p-4 text-center">
                            <p className="text-xs text-gray-400 mb-1">Transaction Amount</p>
                            <p className="text-2xl font-bold text-white">
                                ${transaction.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                            </p>
                        </div>
                        <div className="bg-gray-800 rounded-xl p-4 text-center">
                            <p className="text-xs text-gray-400 mb-1">Budget Remaining</p>
                            <p className="text-2xl font-bold text-white">
                                ${transaction.monthly_budget_remaining.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                            </p>
                        </div>
                    </div>

                    <p className="text-sm text-gray-400">
                        <span className="font-medium text-white">{transaction.category}</span> · {transaction.recipient_status}
                    </p>

                    {/* Risk flags */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-semibold text-gray-300">Why was this flagged?</h3>
                        {risk_flags.map((flag, i) => (
                            <div
                                key={i}
                                className={`px-3 py-2 rounded-lg border text-sm ${severityColors[flag.severity]}`}
                            >
                                <span className="font-semibold">
                                    {flag.rule_name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                                </span>
                                <span className="mx-1">—</span>
                                {flag.explanation}
                            </div>
                        ))}
                    </div>

                    {/* Future impact */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-300 mb-2">Future Impact (if invested)</h3>
                        <div className="grid grid-cols-3 gap-2">
                            {Object.entries(future_impact).map(([label, value]) => (
                                <div key={label} className="bg-emerald-900/20 border border-emerald-800/50 rounded-lg p-3 text-center">
                                    <p className="text-xs text-emerald-400/70">{label}</p>
                                    <p className="text-sm font-bold text-emerald-400">
                                        ${value.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Countdown */}
                    {countdown > 0 && (
                        <div className="flex items-center gap-2 text-amber-400 bg-amber-900/20 border border-amber-800/50 rounded-lg px-4 py-2">
                            <Clock size={16} />
                            <span className="text-sm font-medium">
                                Cooling-off period: {countdown}s remaining
                            </span>
                        </div>
                    )}

                    {/* Buttons */}
                    <div className="grid grid-cols-2 gap-3 pt-2">
                        <button
                            onClick={() => onDecide("cancelled")}
                            className="flex items-center justify-center gap-2 py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl font-semibold transition"
                        >
                            <X size={18} />
                            Cancel &amp; Save
                        </button>
                        <button
                            onClick={() => onDecide("proceeded")}
                            disabled={countdown > 0}
                            className="flex items-center justify-center gap-2 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-semibold transition disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            <ChevronRight size={18} />
                            Proceed
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
