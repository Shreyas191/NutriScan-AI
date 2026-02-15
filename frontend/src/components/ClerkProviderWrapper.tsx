"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";

/**
 * Conditional ClerkProvider that gracefully handles missing publishable key
 * (e.g., during build / CI where env vars aren't available).
 */
export default function ClerkProviderWrapper({
    children,
}: {
    children: React.ReactNode;
}) {
    const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

    if (!publishableKey) {
        // No Clerk key — render children without auth wrapper (build / dev without keys)
        return <>{children}</>;
    }

    return (
        <ClerkProvider
            publishableKey={publishableKey}
            appearance={{
                baseTheme: dark,
                variables: {
                    colorPrimary: "#10b981",
                    colorBackground: "#0c1220",
                    colorInputBackground: "#111827",
                    colorText: "#f1f5f9",
                },
            }}
        >
            {children}
        </ClerkProvider>
    );
}
