import { Trash2, RefreshCw, ExternalLink } from "lucide-react";

interface CartItemProps {
    name: string;
    emoji: string;
    category: string;
    quantity: number;
    href?: string;
    onRemove?: () => void;
    onSubstitute?: () => void;
    onQuantityChange?: (qty: number) => void;
}

export default function CartItem({
    name,
    emoji,
    category,
    quantity,
    href,
    onRemove,
    onSubstitute,
    onQuantityChange,
}: CartItemProps) {
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
            {/* Emoji */}
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
                <span className="badge badge-normal" style={{ fontSize: "0.65rem" }}>
                    {category}
                </span>
            </div>

            {/* Quantity */}
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    border: "1px solid var(--border-default)",
                    borderRadius: "var(--radius-full)",
                    padding: "4px 8px",
                }}
            >
                <button
                    onClick={() => onQuantityChange?.(Math.max(1, quantity - 1))}
                    style={{
                        background: "none",
                        border: "none",
                        color: "var(--text-secondary)",
                        cursor: "pointer",
                        fontSize: "1rem",
                        width: 24,
                        height: 24,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                >
                    −
                </button>
                <span
                    style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.85rem",
                        minWidth: 20,
                        textAlign: "center",
                    }}
                >
                    {quantity}
                </span>
                <button
                    onClick={() => onQuantityChange?.(quantity + 1)}
                    style={{
                        background: "none",
                        border: "none",
                        color: "var(--text-secondary)",
                        cursor: "pointer",
                        fontSize: "1rem",
                        width: 24,
                        height: 24,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                >
                    +
                </button>
            </div>

            {/* Actions */}
            <div style={{ display: "flex", gap: 6 }}>
                {href && (
                    <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="View on store"
                        style={{
                            width: 32,
                            height: 32,
                            borderRadius: "var(--radius-full)",
                            background: "none",
                            border: "1px solid var(--border-default)",
                            color: "var(--accent-start)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            cursor: "pointer",
                            transition: "all 0.2s",
                            textDecoration: "none",
                        }}
                    >
                        <ExternalLink size={14} />
                    </a>
                )}
                <button
                    onClick={onSubstitute}
                    title="Substitute"
                    style={{
                        width: 32,
                        height: 32,
                        borderRadius: "var(--radius-full)",
                        background: "none",
                        border: "1px solid var(--border-default)",
                        color: "var(--text-muted)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        transition: "all 0.2s",
                    }}
                >
                    <RefreshCw size={14} />
                </button>
                <button
                    onClick={onRemove}
                    title="Remove"
                    style={{
                        width: 32,
                        height: 32,
                        borderRadius: "var(--radius-full)",
                        background: "none",
                        border: "1px solid rgba(239,68,68,0.2)",
                        color: "var(--severity-severe)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        transition: "all 0.2s",
                    }}
                >
                    <Trash2 size={14} />
                </button>
            </div>
        </div>
    );
}
