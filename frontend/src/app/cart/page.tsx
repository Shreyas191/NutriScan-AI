"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ShoppingCart, ExternalLink, Sparkles, Loader2, AlertTriangle } from "lucide-react";
import CartItem from "@/components/CartItem";
import { getReport, type CartItem as CartItemType } from "@/lib/api";

export default function CartPage() {
    return (
        <Suspense fallback={
            <div style={{ maxWidth: 800, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
                <Loader2 size={40} color="var(--accent-start)" style={{ margin: "0 auto 16px", animation: "spin-slow 1.5s linear infinite" }} />
                <p style={{ color: "var(--text-secondary)" }}>Loading cart…</p>
            </div>
        }>
            <CartPageInner />
        </Suspense>
    );
}

function CartPageInner() {
    const searchParams = useSearchParams();
    const reportId = searchParams.get("id");

    const [cart, setCart] = useState<CartItemType[]>([]);
    const [shopAllUrl, setShopAllUrl] = useState("");
    const [loading, setLoading] = useState(!!reportId);
    const [error, setError] = useState(
        reportId ? "" : "No report ID. Please upload a lab report first."
    );

    useEffect(() => {
        if (!reportId) return;

        let cancelled = false;
        getReport(reportId)
            .then((data) => {
                if (!cancelled) {
                    setCart(data.cart_items);
                    setShopAllUrl(data.shop_all_url);
                }
            })
            .catch((err) => {
                if (!cancelled) setError(err.message);
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => { cancelled = true; };
    }, [reportId]);

    const remove = (id: number) => setCart((c) => c.filter((item) => item.id !== id));

    const updateQty = (id: number, qty: number) =>
        setCart((c) => c.map((item) => (item.id === id ? { ...item, quantity: qty } : item)));

    // Group by nutrient
    const nutrients = [...new Set(cart.map((i) => i.nutrient))];

    if (loading) {
        return (
            <div style={{ maxWidth: 800, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
                <Loader2
                    size={40}
                    color="var(--accent-start)"
                    style={{ margin: "0 auto 16px", animation: "spin-slow 1.5s linear infinite" }}
                />
                <p style={{ color: "var(--text-secondary)" }}>Loading cart…</p>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ maxWidth: 600, margin: "0 auto", padding: "80px 24px", textAlign: "center" }}>
                <AlertTriangle size={48} color="var(--severity-severe)" style={{ margin: "0 auto 16px" }} />
                <h2 style={{ fontWeight: 700, marginBottom: 8 }}>Could not load cart</h2>
                <p style={{ color: "var(--text-secondary)", marginBottom: 24 }}>{error}</p>
                <Link href="/upload" className="btn-primary">Upload a Report</Link>
            </div>
        );
    }

    return (
        <div style={{ maxWidth: 800, margin: "0 auto", padding: "40px 24px" }}>
            {/* Header */}
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                    <ShoppingCart size={24} color="var(--accent-start)" />
                    <h1 style={{ fontSize: "1.6rem", fontWeight: 700 }}>Your Grocery Cart</h1>
                </div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
                    {cart.length} items based on your deficiency analysis · Edit before checkout
                </p>
            </div>

            {/* Category groups */}
            {nutrients.map((nutrient) => {
                const items = cart.filter((i) => i.nutrient === nutrient || i.category === nutrient.toLowerCase());
                if (items.length === 0) return null;
                return (
                    <section key={nutrient} style={{ marginBottom: 32 }}>
                        <h2
                            style={{
                                fontSize: "0.85rem",
                                fontWeight: 600,
                                color: "var(--text-muted)",
                                textTransform: "uppercase",
                                letterSpacing: "0.06em",
                                marginBottom: 12,
                            }}
                        >
                            {nutrient} Foods
                        </h2>
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                            {items.map((item) => (
                                <CartItem
                                    key={item.id}
                                    name={item.name}
                                    emoji={item.emoji}
                                    category={item.nutrient}
                                    quantity={item.quantity}
                                    onRemove={() => remove(item.id)}
                                    onQuantityChange={(qty) => updateQty(item.id, qty)}
                                />
                            ))}
                        </div>
                    </section>
                );
            })}

            {/* Empty state */}
            {cart.length === 0 && (
                <div
                    className="card"
                    style={{
                        padding: 48,
                        textAlign: "center",
                        color: "var(--text-muted)",
                    }}
                >
                    <ShoppingCart size={40} style={{ margin: "0 auto 12px", opacity: 0.4 }} />
                    <p>Your cart is empty. Upload a lab report to get recommendations.</p>
                </div>
            )}

            {/* Checkout bar */}
            {cart.length > 0 && (
                <div
                    className="gradient-border"
                    style={{
                        borderRadius: "var(--radius-xl)",
                        padding: 28,
                        display: "flex",
                        flexDirection: "column",
                        gap: 16,
                        alignItems: "center",
                        textAlign: "center",
                    }}
                >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <Sparkles size={18} color="var(--accent-start)" />
                        <span style={{ fontWeight: 600 }}>
                            Ready to shop — {cart.length} items
                        </span>
                    </div>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", maxWidth: 400 }}>
                        Click below to open your personalized Instacart shopping list with all items ready to add to cart.
                    </p>
                    <a
                        href={shopAllUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary"
                        style={{ fontSize: "1rem", padding: "14px 36px" }}
                    >
                        Shop on Instacart <ExternalLink size={16} />
                    </a>
                </div>
            )}
        </div>
    );
}
