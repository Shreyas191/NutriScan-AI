import { Heart } from "lucide-react";

export default function Footer() {
    return (
        <footer
            style={{
                borderTop: "1px solid rgba(163, 177, 198, 0.4)",
                paddingTop: 40,
                paddingBottom: 40,
                paddingLeft: 24,
                paddingRight: 24,
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
                        background: "rgba(163, 177, 198, 0.4)",
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
                        Made with <Heart size={12} color="#C53030" fill="#C53030" />
                    </span>
                </div>
            </div>
        </footer>
    );
}
