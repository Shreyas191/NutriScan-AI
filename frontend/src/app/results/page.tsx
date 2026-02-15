"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { FlaskConical, ArrowRight, Loader2, AlertTriangle } from "lucide-react";
import DeficiencyCard from "@/components/DeficiencyCard";
import ExplanationPanel from "@/components/ExplanationPanel";
import MedicalDisclaimer from "@/components/MedicalDisclaimer";
import { getReport, type AnalysisResponse } from "@/lib/api";

export default function ResultsPage() {
    return (
        <Suspense fallback={
            <div style={{ maxWidth: 1100, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
                <Loader2 size={40} color="var(--accent-start)" style={{ margin: "0 auto 16px", animation: "spin-slow 1.5s linear infinite" }} />
                <p style={{ color: "var(--text-secondary)" }}>Loading results…</p>
            </div>
        }>
            <ResultsPageInner />
        </Suspense>
    );
}

function ResultsPageInner() {
    const searchParams = useSearchParams();
    const reportId = searchParams.get("id");

    const [data, setData] = useState<AnalysisResponse | null>(null);
    const [loading, setLoading] = useState(!!reportId);
    const [error, setError] = useState(
        reportId ? "" : "No report ID provided. Please upload a lab report first."
    );

    useEffect(() => {
        if (!reportId) return;

        let cancelled = false;
        getReport(reportId)
            .then((result) => {
                if (!cancelled) setData(result);
            })
            .catch((err) => {
                if (!cancelled) setError(err.message);
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => { cancelled = true; };
    }, [reportId]);

    if (loading) {
        return (
            <div style={{ maxWidth: 1100, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
                <Loader2
                    size={40}
                    color="var(--accent-start)"
                    style={{ margin: "0 auto 16px", animation: "spin-slow 1.5s linear infinite" }}
                />
                <p style={{ color: "var(--text-secondary)" }}>Loading results…</p>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div style={{ maxWidth: 600, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
                <AlertTriangle size={48} color="var(--severity-severe)" style={{ margin: "0 auto 16px" }} />
                <h2 style={{ fontWeight: 700, marginBottom: 8 }}>Could not load results</h2>
                <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>{error}</p>
                <Link href="/upload" className="btn-primary">Upload a Report</Link>
            </div>
        );
    }

    return (
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px" }}>
            {/* Header */}
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                    <FlaskConical size={24} color="var(--accent-start)" />
                    <h1 style={{ fontSize: "1.6rem", fontWeight: 700 }}>Lab Results</h1>
                </div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
                    Parsed from your uploaded report · {data.biomarkers.length} biomarkers extracted
                    {data.ocr_method && (
                        <span style={{ marginLeft: 12, fontSize: "0.8rem", color: "var(--text-muted)" }}>
                            OCR: {data.ocr_method} ({(data.ocr_confidence * 100).toFixed(0)}% confidence)
                        </span>
                    )}
                </p>
            </div>

            <MedicalDisclaimer />

            {/* Raw Lab Table */}
            <section style={{ marginTop: 32 }}>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 16 }}>
                    Extracted Biomarkers
                </h2>
                <div className="card" style={{ overflow: "hidden" }}>
                    <div style={{ overflowX: "auto" }}>
                        <table
                            style={{
                                width: "100%",
                                borderCollapse: "collapse",
                                fontSize: "0.88rem",
                            }}
                        >
                            <thead>
                                <tr
                                    style={{
                                        borderBottom: "1px solid var(--border-default)",
                                        textAlign: "left",
                                    }}
                                >
                                    {["Test", "Value", "Unit", "Reference Range", "Flag"].map(
                                        (h) => (
                                            <th
                                                key={h}
                                                style={{
                                                    padding: "14px 16px",
                                                    fontWeight: 600,
                                                    color: "var(--text-secondary)",
                                                    fontSize: "0.75rem",
                                                    textTransform: "uppercase",
                                                    letterSpacing: "0.05em",
                                                }}
                                            >
                                                {h}
                                            </th>
                                        )
                                    )}
                                </tr>
                            </thead>
                            <tbody>
                                {data.biomarkers.map((row) => (
                                    <tr
                                        key={row.test_name}
                                        style={{
                                            borderBottom: "1px solid var(--border-default)",
                                        }}
                                    >
                                        <td style={{ padding: "12px 16px", fontWeight: 500 }}>
                                            {row.test_name}
                                        </td>
                                        <td
                                            style={{
                                                padding: "12px 16px",
                                                fontFamily: "var(--font-mono)",
                                                fontWeight: 600,
                                                color: row.flag
                                                    ? "var(--severity-severe)"
                                                    : "var(--text-primary)",
                                            }}
                                        >
                                            {row.value}
                                        </td>
                                        <td
                                            style={{
                                                padding: "12px 16px",
                                                color: "var(--text-muted)",
                                            }}
                                        >
                                            {row.unit}
                                        </td>
                                        <td
                                            style={{
                                                padding: "12px 16px",
                                                color: "var(--text-muted)",
                                                fontFamily: "var(--font-mono)",
                                                fontSize: "0.82rem",
                                            }}
                                        >
                                            {row.reference_range}
                                        </td>
                                        <td style={{ padding: "12px 16px" }}>
                                            {row.flag && (
                                                <span className="badge badge-severe">{row.flag}</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            {/* Deficiency Cards */}
            {data.deficiencies.length > 0 && (
                <section style={{ marginTop: 40 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 16 }}>
                        Detected Deficiencies
                    </h2>
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                            gap: 20,
                        }}
                    >
                        {data.deficiencies.map((d) => (
                            <DeficiencyCard
                                key={d.name}
                                name={d.name}
                                value={d.value}
                                unit={d.unit}
                                normalRange={d.normal_range}
                                severity={d.severity}
                                percentage={d.percentage}
                            />
                        ))}
                    </div>
                </section>
            )}

            {/* Explanations */}
            {data.explanations.length > 0 && (
                <section style={{ marginTop: 40 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 16 }}>
                        AI Explanations
                    </h2>
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        {data.explanations.map((e) => (
                            <ExplanationPanel key={e.title} {...e} />
                        ))}
                    </div>
                </section>
            )}

            {/* No deficiencies */}
            {data.deficiencies.length === 0 && (
                <section style={{ marginTop: 40, textAlign: "center" }}>
                    <div className="card" style={{ padding: 48 }}>
                        <p style={{ fontSize: "2rem", marginBottom: 8 }}>🎉</p>
                        <h2 style={{ fontWeight: 700, marginBottom: 8 }}>All Clear!</h2>
                        <p style={{ color: "var(--text-secondary)" }}>
                            No deficiencies detected. Your biomarkers are within normal range.
                        </p>
                    </div>
                </section>
            )}

            {/* CTA */}
            {data.cart_items.length > 0 && (
                <div style={{ textAlign: "center", marginTop: 48 }}>
                    <Link
                        href={`/cart?id=${reportId}`}
                        className="btn-primary"
                        style={{ fontSize: "1rem", padding: "14px 36px" }}
                    >
                        Generate Grocery Cart <ArrowRight size={18} />
                    </Link>
                </div>
            )}
        </div>
    );
}
