import { Heart } from "lucide-react";

export default function Footer() {
    return (
        <footer
            style={{
                borderTop: "1px solid var(--border-default)",
                padding: "40px 24px",
                marginTop: 80,
            }}
        >
            <div
                style={{
                    maxWidth: 1200,
                    margin: "0 auto",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 16,
                    textAlign: "center",
                }}
            >
                {/* Disclaimer */}
                <p
                    style={{
                        fontSize: "0.8rem",
                        color: "var(--text-muted)",
                        maxWidth: 540,
                        lineHeight: 1.6,
                    }}
                >
                    ⚕️ <strong>Medical Disclaimer:</strong> NutriScan AI does not provide
                    medical advice, diagnosis, or treatment. Always consult your
                    healthcare provider before making dietary changes.
                </p>

                <div
                    style={{
                        width: 60,
                        height: 1,
                        background: "var(--border-default)",
                    }}
                />

                {/* Bottom bar */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: "0.8rem",
                        color: "var(--text-muted)",
                    }}
                >
                    <span>© {new Date().getFullYear()} NutriScan AI</span>
                    <span>·</span>
                    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                        Made with <Heart size={12} color="var(--severity-severe)" fill="var(--severity-severe)" />
                    </span>
                </div>
            </div>
        </footer>
    );
}
