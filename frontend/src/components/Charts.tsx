"use client";

import { useState, useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import type { Transaction } from "@/lib/api";

const COLORS = ["#6366f1", "#ec4899", "#10b981", "#f59e0b", "#3b82f6", "#8b5cf6", "#ef4444", "#14b8a6"];

interface ChartsProps {
    transactions: Transaction[];
}

export function CategoryPieChart({ transactions }: ChartsProps) {
    if (transactions.length === 0) return null;

    const counts: Record<string, number> = {};
    transactions.forEach((t) => {
        counts[t.category] = (counts[t.category] || 0) + 1;
    });

    const data = Object.entries(counts).map(([name, value]) => ({ name, value }));

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Spending by Category</h3>
            <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        dataKey="value"
                        stroke="none"
                    >
                        {data.map((_, idx) => (
                            <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: "8px", color: "#e5e7eb" }}
                    />
                    <Legend
                        wrapperStyle={{ fontSize: "12px", color: "#9ca3af" }}
                    />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}

export function TimelineChart({ transactions }: ChartsProps) {
    const [fromDate, setFromDate] = useState("");
    const [toDate, setToDate] = useState("");

    const filtered = useMemo(() => {
        return transactions.filter((t) => {
            const d = new Date(t.timestamp);
            if (fromDate && d < new Date(fromDate)) return false;
            if (toDate) {
                const end = new Date(toDate);
                end.setHours(23, 59, 59, 999);
                if (d > end) return false;
            }
            return true;
        });
    }, [transactions, fromDate, toDate]);

    if (transactions.length === 0) return null;

    const hourly: Record<number, number> = {};
    filtered.forEach((t) => {
        const h = new Date(t.timestamp).getHours();
        hourly[h] = (hourly[h] || 0) + 1;
    });

    const data = Object.entries(hourly)
        .map(([hour, count]) => ({
            hour: `${String(hour).padStart(2, "0")}:00`,
            count,
        }))
        .sort((a, b) => a.hour.localeCompare(b.hour));

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <h3 className="text-sm font-semibold text-gray-300">Transaction Frequency</h3>
                <div className="flex items-center gap-2">
                    <label className="text-xs text-gray-500">From</label>
                    <input
                        type="date"
                        value={fromDate}
                        onChange={(e) => setFromDate(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-xs text-white focus:border-indigo-500 focus:outline-none"
                    />
                    <label className="text-xs text-gray-500">To</label>
                    <input
                        type="date"
                        value={toDate}
                        onChange={(e) => setToDate(e.target.value)}
                        className="bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-xs text-white focus:border-indigo-500 focus:outline-none"
                    />
                    {(fromDate || toDate) && (
                        <button
                            onClick={() => { setFromDate(""); setToDate(""); }}
                            className="text-xs text-gray-500 hover:text-gray-300 ml-1"
                        >
                            Clear
                        </button>
                    )}
                </div>
            </div>
            {filtered.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-16">No transactions in this date range.</p>
            ) : (
                <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="hour" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                        <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
                        <Tooltip
                            contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: "8px", color: "#e5e7eb" }}
                        />
                        <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            )}
            <p className="text-xs text-gray-600 mt-2 text-right">
                Showing {filtered.length} of {transactions.length} transactions
            </p>
        </div>
    );
}
