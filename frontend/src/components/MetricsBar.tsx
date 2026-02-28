"use client";

import { TrendingDown, AlertTriangle, DollarSign, BarChart3, Zap } from "lucide-react";
import type { Metrics } from "@/lib/api";

interface MetricsBarProps {
    metrics: Metrics | null;
}

const cards = [
    { key: "total_transactions", label: "Total Transactions", icon: BarChart3, color: "from-blue-500 to-cyan-400" },
    { key: "total_flagged", label: "Flagged", icon: AlertTriangle, color: "from-amber-500 to-orange-400" },
    { key: "money_saved", label: "Money Saved", icon: DollarSign, color: "from-emerald-500 to-green-400", isCurrency: true },
    { key: "override_rate", label: "Override Rate", icon: TrendingDown, color: "from-rose-500 to-pink-400", isPercent: true },
    { key: "impulsivity_score", label: "Impulsivity", icon: Zap, color: "from-purple-500 to-violet-400", isScore: true },
] as const;

export default function MetricsBar({ metrics }: MetricsBarProps) {
    if (!metrics) return null;

    return (
        <div className="grid grid-cols-5 gap-4">
            {cards.map((card) => {
                const value = metrics[card.key as keyof Metrics];
                let display: string;
                if ("isCurrency" in card && card.isCurrency) display = `₹${(value as number).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                else if ("isPercent" in card && card.isPercent) display = `${(value as number).toFixed(1)}%`;
                else if ("isScore" in card && card.isScore) display = `${Math.round(value as number)}/100`;
                else display = String(value);

                const Icon = card.icon;
                return (
                    <div key={card.key} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-2">
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-400 font-medium">{card.label}</span>
                            <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                                <Icon size={16} className="text-white" />
                            </div>
                        </div>
                        <span className="text-2xl font-bold text-white">{display}</span>
                    </div>
                );
            })}
        </div>
    );
}
