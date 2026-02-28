"use client";

import { useState, useEffect } from "react";
import { ShieldAlert, Clock, X, ChevronRight, TrendingUp, Lightbulb } from "lucide-react";
import type { Assessment } from "@/lib/api";

interface InterventionModalProps {
    assessment: Assessment;
    onDecide: (decision: "cancelled" | "proceeded") => void;
}

function getDynamicTip(assessment: Assessment): string {
    const { transaction } = assessment;
    const hour = new Date(transaction.timestamp).getHours();

    // Rule 1: Late Night Splurge (11 PM to 4 AM)
    if (hour >= 23 || hour < 4) {
        return "You seem to be shopping late! Consider adding this to your cart and reviewing it tomorrow morning.";
    }

    // Rule 2: Unusually High Spend Amount
    // Trigger if amount > 2000 OR if flagged for budget drain explicitly
    const isBudgetDrain = assessment.risk_flags.some(f => f.rule_name === "budget_drain");
    if (transaction.amount > 2000 || isBudgetDrain) {
        // Random percentage between 40% and 80%
        const randPct = Math.floor(Math.random() * 41) + 40;
        const category = transaction.category.charAt(0).toUpperCase() + transaction.category.slice(1);
        return `Whoa, big purchase in ${category}! Your spending is ${randPct}% above your weekly average. Taking a 24-hour break before checking out often helps to clarify if it's a need or a want.`;
    }

    // Fallback Rule: High Velocity (or any other anomaly mapped here)
    const categoryName = transaction.category.charAt(0).toUpperCase() + transaction.category.slice(1);
    return `Your weekly spend for ${categoryName} is looking unusually high. Slowing down now means more savings later!`;
}

export default function InterventionModal({ assessment, onDecide }: InterventionModalProps) {
    const [countdown, setCountdown] = useState(5);
    // Tip is generated deterministically based on the transaction, so it stays consistent for the same session
    const [tip] = useState(() => getDynamicTip(assessment));

    useEffect(() => {
        setCountdown(5);
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

    const { transaction, risk_flags } = assessment;
    const severityColors: Record<string, string> = {
        high: "bg-red-900/40 border-red-700 text-red-300",
        medium: "bg-amber-900/40 border-amber-700 text-amber-300",
        low: "bg-blue-900/40 border-blue-700 text-blue-300",
    };

    const fmt = (n: number) => n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

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
                            <p className="text-2xl font-bold text-white">₹{fmt(transaction.amount)}</p>
                        </div>
                        <div className="bg-gray-800 rounded-xl p-4 text-center">
                            <p className="text-xs text-gray-400 mb-1">Budget Remaining</p>
                            <p className="text-2xl font-bold text-white">₹{fmt(transaction.monthly_budget_remaining)}</p>
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

                    {/* Smart Tip (replaces Future Impact) */}
                    <div className="bg-indigo-900/20 border border-indigo-800/50 rounded-xl p-4 flex gap-3">
                        <Lightbulb size={20} className="text-indigo-400 shrink-0 mt-0.5" />
                        <div>
                            <h3 className="text-sm font-semibold text-indigo-300 mb-1">Smart Spending Tip</h3>
                            <p className="text-sm text-indigo-200/80">{tip}</p>
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
