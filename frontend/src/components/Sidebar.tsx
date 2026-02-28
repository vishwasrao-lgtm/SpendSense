"use client";

import { useState, useRef } from "react";
import { Upload, Database, Plus, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

const CATEGORIES = ["groceries", "dining", "entertainment", "shopping", "bills", "travel", "utilities", "health", "food"];

interface SidebarProps {
    onDataLoaded: () => void;
    onTransactionAdded: (result: any) => void;
    loaded: boolean;
    totalTransactions: number;
}

export default function Sidebar({
    onDataLoaded,
    onTransactionAdded,
    loaded,
    totalTransactions,
}: SidebarProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const fileRef = useRef<HTMLInputElement>(null);

    // Add transaction form state
    const [showForm, setShowForm] = useState(false);
    const [amount, setAmount] = useState("");
    const [category, setCategory] = useState("shopping");
    const [timestamp, setTimestamp] = useState(() => {
        const now = new Date();
        return now.toISOString().slice(0, 16); // YYYY-MM-DDTHH:mm
    });

    const handleLoadSample = async () => {
        setLoading(true);
        setError("");
        setSuccess("");
        try {
            const res = await api.loadSample();
            setSuccess(res.message);
            onDataLoaded();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setLoading(true);
        setError("");
        setSuccess("");
        try {
            const res = await api.uploadFile(file);
            setSuccess(res.message);
            onDataLoaded();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAddTransaction = async () => {
        if (!amount || parseFloat(amount) <= 0) {
            setError("Enter a valid amount");
            return;
        }
        setLoading(true);
        setError("");
        setSuccess("");
        try {
            const result = await api.addTransaction({
                amount: parseFloat(amount),
                category,
                timestamp,
            });
            setAmount("");
            // Reset timestamp to now
            setTimestamp(new Date().toISOString().slice(0, 16));
            onTransactionAdded(result);
            if (result.status === "clean") {
                setSuccess("Transaction added — no risk detected");
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <aside className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col p-5 gap-5 shrink-0">
            {/* Logo */}
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-xl">
                    💡
                </div>
                <div>
                    <h1 className="text-lg font-bold text-white">SpendSense</h1>
                    <p className="text-xs text-gray-400">Transaction Monitor</p>
                </div>
            </div>

            <div className="border-t border-gray-800" />

            {/* Data loading */}
            <div className="flex flex-col gap-3">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Load Data</p>
                <button
                    onClick={handleLoadSample}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                >
                    {loading ? <Loader2 size={16} className="animate-spin" /> : <Database size={16} />}
                    Load Sample Data
                </button>

                <button
                    onClick={() => fileRef.current?.click()}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition border border-gray-700 disabled:opacity-50"
                >
                    <Upload size={16} />
                    Upload CSV / JSON
                </button>
                <input
                    ref={fileRef}
                    type="file"
                    accept=".csv,.json"
                    className="hidden"
                    onChange={handleUpload}
                />
            </div>

            {/* Stats */}
            {loaded && (
                <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-white">{totalTransactions}</p>
                    <p className="text-xs text-gray-400">Transactions Loaded</p>
                </div>
            )}

            <div className="border-t border-gray-800" />

            {/* Add Transaction */}
            <div className="flex flex-col gap-3">
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition"
                >
                    <Plus size={16} />
                    Add Transaction
                </button>

                {showForm && (
                    <div className="bg-gray-800/50 rounded-lg p-4 space-y-3 border border-gray-700">
                        <div>
                            <label className="text-xs text-gray-400 block mb-1">Amount (₹)</label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">₹</span>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    placeholder="0.00"
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg py-2 pl-7 pr-3 text-white text-sm focus:border-indigo-500 focus:outline-none"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="text-xs text-gray-400 block mb-1">Category</label>
                            <select
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                className="w-full bg-gray-900 border border-gray-700 rounded-lg py-2 px-3 text-white text-sm focus:border-indigo-500 focus:outline-none"
                            >
                                {CATEGORIES.map((c) => (
                                    <option key={c} value={c}>
                                        {c.charAt(0).toUpperCase() + c.slice(1)}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs text-gray-400 block mb-1">Date & Time</label>
                            <input
                                type="datetime-local"
                                value={timestamp}
                                onChange={(e) => setTimestamp(e.target.value)}
                                className="w-full bg-gray-900 border border-gray-700 rounded-lg py-2 px-3 text-white text-sm focus:border-indigo-500 focus:outline-none"
                            />
                        </div>
                        <button
                            onClick={handleAddTransaction}
                            disabled={loading || !amount}
                            className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                        >
                            {loading ? "Processing..." : "Submit Transaction"}
                        </button>
                    </div>
                )}
            </div>

            {/* Feedback */}
            {error && (
                <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-xs">
                    {error}
                </div>
            )}
            {success && (
                <div className="p-3 bg-emerald-900/30 border border-emerald-800 rounded-lg text-emerald-400 text-xs">
                    {success}
                </div>
            )}

            <div className="mt-auto text-xs text-gray-600 text-center">
                Built for HackSprint 2026
            </div>
        </aside>
    );
}
