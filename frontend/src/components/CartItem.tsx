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
            {/* Emoji — inset-deep well */}
            <div
                style={{
                    width: 44,
                    height: 44,
                    borderRadius: "var(--radius-md)",
                    background: "var(--bg-card)",
                    boxShadow: "var(--shadow-inset-deep)",
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
                <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: 2, color: "var(--text-primary)" }}>
                    {name}
                </div>
                <span className="badge badge-normal" style={{ fontSize: "0.65rem" }}>
                    {category}
                </span>
            </div>

            {/* Quantity stepper — inset-sm pill */}
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    boxShadow: "var(--shadow-inset-sm)",
                    border: "none",
                    borderRadius: "var(--radius-full)",
                    padding: "4px 8px",
                    background: "var(--bg-card)",
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
                        color: "var(--text-primary)",
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

            {/* Actions — small extruded circles */}
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
                            background: "var(--bg-card)",
                            border: "none",
                            color: "var(--accent-start)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            cursor: "pointer",
                            boxShadow: "var(--shadow-extruded-sm)",
                            transition: "box-shadow 0.2s ease",
                            textDecoration: "none",
                        }}
                        onMouseEnter={(e) =>
                            (e.currentTarget.style.boxShadow = "var(--shadow-inset-sm)")
                        }
                        onMouseLeave={(e) =>
                            (e.currentTarget.style.boxShadow = "var(--shadow-extruded-sm)")
                        }
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
                        background: "var(--bg-card)",
                        border: "none",
                        color: "var(--text-muted)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        boxShadow: "var(--shadow-extruded-sm)",
                        transition: "box-shadow 0.2s ease",
                    }}
                    onMouseEnter={(e) =>
                        (e.currentTarget.style.boxShadow = "var(--shadow-inset-sm)")
                    }
                    onMouseLeave={(e) =>
                        (e.currentTarget.style.boxShadow = "var(--shadow-extruded-sm)")
                    }
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
                        background: "var(--bg-card)",
                        border: "none",
                        color: "var(--severity-severe)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        boxShadow: "var(--shadow-extruded-sm)",
                        transition: "box-shadow 0.2s ease",
                    }}
                    onMouseEnter={(e) =>
                        (e.currentTarget.style.boxShadow = "var(--shadow-inset-sm)")
                    }
                    onMouseLeave={(e) =>
                        (e.currentTarget.style.boxShadow = "var(--shadow-extruded-sm)")
                    }
                >
                    <Trash2 size={14} />
                </button>
            </div>
        </div>
    );
}
