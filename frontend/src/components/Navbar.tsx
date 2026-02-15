"use client";

import Link from "next/link";
import { useState } from "react";
import {
    ScanLine,
    LayoutDashboard,
    Upload,
    ShoppingCart,
    Menu,
    X,
} from "lucide-react";

const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/upload", label: "Upload", icon: Upload },
    { href: "/cart", label: "Cart", icon: ShoppingCart },
];

// Dynamically import Clerk components — they may not be available if
// ClerkProvider is not mounted (e.g. build without publishable key)
let SignedIn: React.ComponentType<{ children: React.ReactNode }> | null = null;
let SignedOut: React.ComponentType<{ children: React.ReactNode }> | null = null;
let UserButton: React.ComponentType<Record<string, unknown>> | null = null;
let SignInButton: React.ComponentType<{ mode: string; children: React.ReactNode }> | null = null;

const clerkAvailable = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

if (clerkAvailable) {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const clerk = require("@clerk/nextjs");
    SignedIn = clerk.SignedIn;
    SignedOut = clerk.SignedOut;
    UserButton = clerk.UserButton;
    SignInButton = clerk.SignInButton;
}

export default function Navbar() {
    const [mobileOpen, setMobileOpen] = useState(false);

    return (
        <nav className="glass" style={{ position: "sticky", top: 0, zIndex: 50 }}>
            <div
                style={{
                    maxWidth: 1200,
                    margin: "0 auto",
                    padding: "0 24px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    height: 64,
                }}
            >
                {/* Logo */}
                <Link
                    href="/"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        textDecoration: "none",
                        color: "var(--text-primary)",
                    }}
                >
                    <div
                        style={{
                            width: 36,
                            height: 36,
                            borderRadius: "var(--radius-md)",
                            background:
                                "linear-gradient(135deg, var(--accent-start), var(--accent-end))",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                        }}
                    >
                        <ScanLine size={20} color="#fff" />
                    </div>
                    <span style={{ fontWeight: 700, fontSize: "1.15rem" }}>
                        Nutri<span className="gradient-text">Scan</span>
                    </span>
                </Link>

                {/* Desktop links */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                    }}
                    className="hidden md:flex"
                >
                    {navLinks.map(({ href, label, icon: Icon }) => (
                        <Link
                            key={href}
                            href={href}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 6,
                                padding: "8px 16px",
                                borderRadius: "var(--radius-full)",
                                color: "var(--text-secondary)",
                                textDecoration: "none",
                                fontSize: "0.9rem",
                                fontWeight: 500,
                                transition: "all 0.2s",
                            }}
                            className="hover:!bg-[var(--accent-glow)] hover:!text-[var(--text-primary)]"
                        >
                            <Icon size={16} />
                            {label}
                        </Link>
                    ))}

                    {/* Auth */}
                    {clerkAvailable && SignedOut && SignedIn && SignInButton && UserButton ? (
                        <>
                            <SignedOut>
                                <SignInButton mode="modal">
                                    <button className="btn-primary" style={{ padding: "8px 20px", fontSize: "0.85rem" }}>
                                        Sign In
                                    </button>
                                </SignInButton>
                            </SignedOut>
                            <SignedIn>
                                <UserButton
                                    afterSignOutUrl="/"
                                    appearance={{
                                        elements: {
                                            avatarBox: { width: 34, height: 34 },
                                        },
                                    }}
                                />
                            </SignedIn>
                        </>
                    ) : (
                        <Link href="/sign-in" className="btn-primary" style={{ padding: "8px 20px", fontSize: "0.85rem" }}>
                            Sign In
                        </Link>
                    )}
                </div>

                {/* Mobile toggle */}
                <button
                    className="md:hidden"
                    onClick={() => setMobileOpen(!mobileOpen)}
                    style={{
                        background: "none",
                        border: "none",
                        color: "var(--text-primary)",
                        cursor: "pointer",
                    }}
                >
                    {mobileOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            {/* Mobile menu */}
            {mobileOpen && (
                <div
                    style={{
                        padding: "12px 24px 20px",
                        display: "flex",
                        flexDirection: "column",
                        gap: 8,
                    }}
                    className="md:hidden"
                >
                    {navLinks.map(({ href, label, icon: Icon }) => (
                        <Link
                            key={href}
                            href={href}
                            onClick={() => setMobileOpen(false)}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                padding: "10px 16px",
                                borderRadius: "var(--radius-md)",
                                color: "var(--text-secondary)",
                                textDecoration: "none",
                                fontWeight: 500,
                                transition: "background 0.2s",
                            }}
                            className="hover:!bg-[var(--bg-elevated)]"
                        >
                            <Icon size={18} />
                            {label}
                        </Link>
                    ))}

                    {/* Mobile auth */}
                    {clerkAvailable && SignedOut && SignedIn && SignInButton && UserButton ? (
                        <>
                            <SignedOut>
                                <SignInButton mode="modal">
                                    <button className="btn-primary" style={{ marginTop: 8 }}>
                                        Sign In
                                    </button>
                                </SignInButton>
                            </SignedOut>
                            <SignedIn>
                                <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 10 }}>
                                    <UserButton afterSignOutUrl="/" />
                                    <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                                        Account
                                    </span>
                                </div>
                            </SignedIn>
                        </>
                    ) : (
                        <Link href="/sign-in" className="btn-primary" style={{ marginTop: 8 }}>
                            Sign In
                        </Link>
                    )}
                </div>
            )}
        </nav>
    );
}
