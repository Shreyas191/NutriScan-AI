"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Stethoscope } from "lucide-react";

interface ExplanationPanelProps {
    title: string;
    explanation: string;
    severity: "normal" | "insufficient" | "severe";
}

export default function ExplanationPanel({
    title,
    explanation,
    severity,
}: ExplanationPanelProps) {
    const [expanded, setExpanded] = useState(false);

    const accentColor =
        severity === "severe"
            ? "var(--severity-severe)"
            : severity === "insufficient"
                ? "var(--severity-insufficient)"
                : "var(--severity-normal)";

    return (
        <div
            className="card"
            style={{
                padding: 0,
                overflow: "hidden",
                borderLeft: `3px solid ${accentColor}`,
            }}
        >
            <button
                onClick={() => setExpanded(!expanded)}
                style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "16px 20px",
                    background: "none",
                    border: "none",
                    color: "var(--text-primary)",
                    cursor: "pointer",
                    fontSize: "0.95rem",
                    fontWeight: 600,
                }}
            >
                <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <Stethoscope size={18} color={accentColor} />
                    {title}
                </span>
                {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>

            {expanded && (
                <div
                    style={{
                        padding: "0 20px 20px",
                        color: "var(--text-secondary)",
                        fontSize: "0.9rem",
                        lineHeight: 1.7,
                    }}
                >
                    {explanation}
                </div>
            )}
        </div>
    );
}
