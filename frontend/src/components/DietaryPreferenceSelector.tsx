"use client";

interface DietaryPreferenceSelectorProps {
    selected: string[];
    onChange: (prefs: string[]) => void;
}

const preferences = [
    { id: "vegan", label: "🌱 Vegan" },
    { id: "vegetarian", label: "🥬 Vegetarian" },
    { id: "lactose-free", label: "🥛 Lactose-Free" },
    { id: "gluten-free", label: "🌾 Gluten-Free" },
    { id: "nut-free", label: "🥜 Nut-Free" },
];

export default function DietaryPreferenceSelector({
    selected,
    onChange,
}: DietaryPreferenceSelectorProps) {
    const toggle = (id: string) => {
        onChange(
            selected.includes(id)
                ? selected.filter((s) => s !== id)
                : [...selected, id]
        );
    };

    return (
        <div>
            <label
                style={{
                    display: "block",
                    fontSize: "0.85rem",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    marginBottom: 10,
                }}
            >
                Dietary Preferences (optional)
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {preferences.map(({ id, label }) => {
                    const active = selected.includes(id);
                    return (
                        <button
                            key={id}
                            onClick={() => toggle(id)}
                            type="button"
                            style={{
                                padding: "8px 16px",
                                borderRadius: "var(--radius-full)",
                                border: active
                                    ? "1px solid var(--accent-start)"
                                    : "1px solid var(--border-default)",
                                background: active ? "var(--accent-glow)" : "var(--bg-card)",
                                color: active ? "var(--text-accent)" : "var(--text-secondary)",
                                fontSize: "0.8rem",
                                fontWeight: 500,
                                cursor: "pointer",
                                transition: "all 0.2s",
                            }}
                        >
                            {label}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
