"use client";

import { useState, useRef } from "react";
import { Upload, Database, Play, FastForward, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface SidebarProps {
    onDataLoaded: () => void;
    loaded: boolean;
    processed: number;
    total: number;
    hasPending: boolean;
    onProcessNext: () => void;
    onProcessAll: () => void;
    processing: boolean;
}

export default function Sidebar({
    onDataLoaded,
    loaded,
    processed,
    total,
    hasPending,
    onProcessNext,
    onProcessAll,
    processing,
}: SidebarProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const fileRef = useRef<HTMLInputElement>(null);

    const handleLoadSample = async () => {
        setLoading(true);
        setError("");
        try {
            await api.loadSample();
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
        try {
            await api.uploadFile(file);
            onDataLoaded();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const progress = total > 0 ? (processed / total) * 100 : 0;

    return (
        <aside className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col p-5 gap-5 shrink-0">
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

            {!loaded ? (
                <div className="flex flex-col gap-3">
                    <button
                        onClick={handleLoadSample}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                    >
                        {loading ? <Loader2 size={16} className="animate-spin" /> : <Database size={16} />}
                        Load Sample Data
                    </button>

                    <div className="text-center text-xs text-gray-500">or</div>

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
            ) : (
                <div className="flex flex-col gap-4">
                    <div>
                        <div className="flex justify-between text-xs text-gray-400 mb-1.5">
                            <span>Progress</span>
                            <span>{processed}/{total}</span>
                        </div>
                        <div className="w-full bg-gray-800 rounded-full h-2">
                            <div
                                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>

                    {processed < total && !hasPending && (
                        <div className="flex flex-col gap-2">
                            <button
                                onClick={onProcessNext}
                                disabled={processing}
                                className="flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                            >
                                {processing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                                Process Next
                            </button>
                            <button
                                onClick={onProcessAll}
                                disabled={processing}
                                className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition border border-gray-700 disabled:opacity-50"
                            >
                                <FastForward size={14} />
                                Auto-Process All
                            </button>
                        </div>
                    )}

                    {processed >= total && !hasPending && (
                        <div className="text-center py-3 bg-emerald-900/30 border border-emerald-800 rounded-lg">
                            <p className="text-emerald-400 text-sm font-medium">✓ All processed</p>
                        </div>
                    )}
                </div>
            )}

            {error && (
                <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-xs">
                    {error}
                </div>
            )}

            <div className="mt-auto text-xs text-gray-600 text-center">
                Built for HackSprint 2026
            </div>
        </aside>
    );
}
