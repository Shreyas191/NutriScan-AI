import { Plus } from "lucide-react";

interface FoodRecommendationProps {
    emoji: string;
    name: string;
    nutrient: string;
    amount: string;
    onAdd?: () => void;
}

export default function FoodRecommendation({
    emoji,
    name,
    nutrient,
    amount,
    onAdd,
}: FoodRecommendationProps) {
    return (
        <div
            className="card"
            style={{
                padding: 16,
                display: "flex",
                alignItems: "center",
                gap: 14,
            }}
        >
            {/* Emoji icon */}
            <div
                style={{
                    width: 44,
                    height: 44,
                    borderRadius: "var(--radius-md)",
                    background: "var(--bg-elevated)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "1.4rem",
                    flexShrink: 0,
                }}
            >
                {emoji}
            </div>

            {/* Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: 2 }}>
                    {name}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {nutrient} · {amount}
                </div>
            </div>

            {/* Add button */}
            <button
                onClick={onAdd}
                style={{
                    width: 32,
                    height: 32,
                    borderRadius: "var(--radius-full)",
                    background: "var(--accent-glow)",
                    border: "1px solid var(--border-accent)",
                    color: "var(--accent-start)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    flexShrink: 0,
                    transition: "all 0.2s",
                }}
                aria-label={`Add ${name} to cart`}
            >
                <Plus size={16} />
            </button>
        </div>
    );
}
