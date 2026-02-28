"use client";

import type { Transaction } from "@/lib/api";

interface TransactionFeedProps {
    transactions: Transaction[];
}

export default function TransactionFeed({ transactions }: TransactionFeedProps) {
    if (transactions.length === 0) {
        return (
            <div className="text-gray-500 text-center py-10">
                No transactions processed yet. Load data and start processing.
            </div>
        );
    }

    const sorted = [...transactions].sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    return (
        <div className="space-y-1">
            <div className="grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 px-4 py-2 text-xs text-gray-500 font-medium uppercase tracking-wider">
                <span>Status</span>
                <span>Details</span>
                <span className="text-right">Amount</span>
                <span>Time</span>
                <span>ID</span>
            </div>
            <div className="max-h-[400px] overflow-y-auto space-y-1 pr-1">
                {sorted.map((txn) => {
                    const style = getStyle(txn);
                    return (
                        <div
                            key={txn.txn_id}
                            className="grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 px-4 py-3 bg-gray-900/50 rounded-lg border border-gray-800/50 hover:border-gray-700 transition items-center"
                        >
                            <span className="text-lg">{style.icon}</span>
                            <div>
                                <span className="text-sm font-medium text-white">
                                    {txn.category.charAt(0).toUpperCase() + txn.category.slice(1)}
                                </span>
                                <span className="text-xs text-gray-500 ml-2">{txn.recipient_status}</span>
                            </div>
                            <span className={`text-sm font-semibold text-right ${style.amountColor}`}>
                                ${txn.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                            </span>
                            <span className="text-xs text-gray-400 font-mono">
                                {new Date(txn.timestamp).toLocaleTimeString()}
                            </span>
                            <span className="text-xs text-gray-600 font-mono">{txn.txn_id}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function getStyle(txn: Transaction) {
    if (!txn.is_flagged) return { icon: "🟢", amountColor: "text-emerald-400" };
    if (txn.user_decision === "cancelled") return { icon: "🔴", amountColor: "text-red-400" };
    if (txn.user_decision === "proceeded") return { icon: "🟡", amountColor: "text-amber-400" };
    return { icon: "🟠", amountColor: "text-orange-400" };
}
