"use client";

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
    if (transactions.length === 0) return null;

    const hourly: Record<number, number> = {};
    transactions.forEach((t) => {
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
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Transaction Frequency</h3>
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
        </div>
    );
}
