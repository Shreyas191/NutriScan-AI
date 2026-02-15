"use client";

import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";

export default function MedicalDisclaimer() {
    const [visible, setVisible] = useState(true);

    if (!visible) return null;

    return (
        <div
            style={{
                background: "rgba(245, 158, 11, 0.08)",
                border: "1px solid rgba(245, 158, 11, 0.2)",
                borderRadius: "var(--radius-md)",
                padding: "12px 20px",
                display: "flex",
                alignItems: "center",
                gap: 12,
                fontSize: "0.85rem",
                color: "var(--severity-insufficient)",
            }}
        >
            <AlertTriangle size={18} style={{ flexShrink: 0 }} />
            <p style={{ flex: 1, margin: 0, lineHeight: 1.5 }}>
                <strong>Disclaimer:</strong> NutriScan AI is not a substitute for
                professional medical advice. Always consult a healthcare provider for
                diagnosis and treatment.
            </p>
            <button
                onClick={() => setVisible(false)}
                style={{
                    background: "none",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    flexShrink: 0,
                    padding: 4,
                }}
                aria-label="Dismiss disclaimer"
            >
                <X size={16} />
            </button>
        </div>
    );
}
