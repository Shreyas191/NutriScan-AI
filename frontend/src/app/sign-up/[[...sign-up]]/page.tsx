import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
    return (
        <div
            style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                minHeight: "calc(100vh - 64px)",
                padding: "40px 24px",
            }}
        >
            <SignUp
                appearance={{
                    elements: {
                        rootBox: { width: "100%" },
                        card: {
                            backgroundColor: "var(--bg-card)",
                            border: "1px solid var(--border-default)",
                            borderRadius: "var(--radius-xl)",
                            boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
                        },
                    },
                }}
            />
        </div>
    );
}
