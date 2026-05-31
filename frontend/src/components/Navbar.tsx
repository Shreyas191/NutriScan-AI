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

import {
    SignedIn,
    SignedOut,
    UserButton,
    SignInButton,
} from "@clerk/nextjs";

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
                            boxShadow: "var(--shadow-extruded-sm)",
                        }}
                    >
                        <ScanLine size={20} color="#fff" />
                    </div>
                    <span
                        style={{
                            fontWeight: 700,
                            fontSize: "1.15rem",
                            fontFamily: "var(--font-display)",
                        }}
                    >
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
                            className="hover:!bg-[rgba(108,99,255,0.1)] hover:!text-[var(--accent-start)]"
                        >
                            <Icon size={16} />
                            {label}
                        </Link>
                    ))}

                    {/* Auth */}
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
                </div>

                {/* Mobile toggle */}
                <button
                    className="md:hidden"
                    onClick={() => setMobileOpen(!mobileOpen)}
                    style={{
                        width: 36,
                        height: 36,
                        borderRadius: "var(--radius-md)",
                        background: "var(--bg-card)",
                        border: "none",
                        color: "var(--text-primary)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        boxShadow: mobileOpen ? "var(--shadow-inset-sm)" : "var(--shadow-extruded-sm)",
                        transition: "box-shadow 0.2s ease",
                    }}
                >
                    {mobileOpen ? <X size={20} /> : <Menu size={20} />}
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
                        boxShadow: "var(--shadow-extruded)",
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
                                borderRadius: "var(--radius-lg)",
                                color: "var(--text-secondary)",
                                textDecoration: "none",
                                fontWeight: 500,
                                transition: "background 0.2s",
                            }}
                            className="hover:!bg-[rgba(108,99,255,0.1)] hover:!text-[var(--accent-start)]"
                        >
                            <Icon size={18} />
                            {label}
                        </Link>
                    ))}

                    {/* Mobile auth */}
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
                </div>
            )}
        </nav>
    );
}
