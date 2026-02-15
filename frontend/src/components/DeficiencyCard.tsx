import { TrendingDown, TrendingUp, Minus } from "lucide-react";

interface DeficiencyCardProps {
    name: string;
    value: number;
    unit: string;
    normalRange: string;
    severity: "normal" | "insufficient" | "severe";
    percentage: number; // 0-100, how close to normal range
}

const severityConfig = {
    normal: { label: "Normal", icon: TrendingUp, className: "badge-normal" },
    insufficient: { label: "Insufficient", icon: Minus, className: "badge-insufficient" },
    severe: { label: "Severe", icon: TrendingDown, className: "badge-severe" },
};

const barColors = {
    normal: "var(--severity-normal)",
    insufficient: "var(--severity-insufficient)",
    severe: "var(--severity-severe)",
};

export default function DeficiencyCard({
    name,
    value,
    unit,
    normalRange,
    severity,
    percentage,
}: DeficiencyCardProps) {
    const config = severityConfig[severity];
    const Icon = config.icon;

    return (
        <div className="card" style={{ padding: 24 }}>
            {/* Header */}
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: 16,
                }}
            >
                <div>
                    <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: 4 }}>
                        {name}
                    </h3>
                    <span
                        style={{
                            fontSize: "0.75rem",
                            color: "var(--text-muted)",
                        }}
                    >
                        Normal: {normalRange}
                    </span>
                </div>
                <span className={`badge ${config.className}`}>
                    <Icon size={12} />
                    {config.label}
                </span>
            </div>

            {/* Value */}
            <div
                style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "2rem",
                    fontWeight: 700,
                    color: barColors[severity],
                    marginBottom: 16,
                }}
            >
                {value}
                <span style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginLeft: 4 }}>
                    {unit}
                </span>
            </div>

            {/* Progress bar */}
            <div
                style={{
                    width: "100%",
                    height: 6,
                    borderRadius: "var(--radius-full)",
                    background: "var(--bg-elevated)",
                    overflow: "hidden",
                }}
            >
                <div
                    style={{
                        width: `${Math.min(percentage, 100)}%`,
                        height: "100%",
                        borderRadius: "var(--radius-full)",
                        background: barColors[severity],
                        transition: "width 0.8s ease",
                    }}
                />
            </div>
        </div>
    );
}
