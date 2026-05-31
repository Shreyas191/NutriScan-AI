"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ShoppingCart, ExternalLink, Sparkles, Loader2, AlertTriangle, Check } from "lucide-react";
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

const MARKETPLACES = [
    { id: "instacart", name: "Instacart", icon: "🛒" },
    { id: "walmart", name: "Walmart", icon: "🥕" },
    { id: "amazon", name: "Amazon", icon: "📦" },
];

function CartPageInner() {
    const searchParams = useSearchParams();
    const reportId = searchParams.get("id");

    const [cart, setCart] = useState<CartItemType[]>([]);
    const [shopLinks, setShopLinks] = useState<Record<string, string>>({});
    const [selectedMarketplace, setSelectedMarketplace] = useState("instacart");
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
                    setShopLinks(data.shopping_links || { walmart: data.shop_all_url });
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

    const currentShopUrl = shopLinks[selectedMarketplace] || "";

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
                <h2 style={{ fontWeight: 700, marginBottom: 8, color: "var(--text-primary)" }}>Could not load cart</h2>
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
                    <h1 style={{ fontSize: "1.6rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
                        Your Grocery Cart
                    </h1>
                </div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
                    {cart.length} items based on your deficiency analysis · Select your preferred store
                </p>
            </div>

            {/* Marketplace Selector */}
            <div style={{ marginBottom: 32, display: "flex", gap: 12, flexWrap: "wrap" }}>
                {MARKETPLACES.map((m) => {
                    const active = selectedMarketplace === m.id;
                    return (
                        <button
                            key={m.id}
                            onClick={() => setSelectedMarketplace(m.id)}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                padding: "10px 20px",
                                borderRadius: "var(--radius-lg)",
                                border: "none",
                                background: "var(--bg-primary)",
                                color: active ? "var(--accent-start)" : "var(--text-secondary)",
                                fontWeight: 600,
                                cursor: "pointer",
                                transition: "box-shadow 0.2s ease, color 0.2s ease",
                                boxShadow: active
                                    ? "var(--shadow-inset-sm)"
                                    : "var(--shadow-extruded-sm)",
                            }}
                        >
                            <span>{m.icon}</span>
                            <span>{m.name}</span>
                            {active && <Check size={16} />}
                        </button>
                    );
                })}
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
                            {items.map((item) => {
                                const itemLink = item.links?.[selectedMarketplace] ||
                                    (selectedMarketplace === "walmart" ? item.walmart_url : "");

                                return (
                                    <div key={item.id} style={{ position: "relative" }}>
                                        <CartItem
                                            name={item.name}
                                            emoji={item.emoji}
                                            category={item.nutrient}
                                            quantity={item.quantity}
                                            href={itemLink || undefined}
                                            onRemove={() => remove(item.id)}
                                            onQuantityChange={(qty) => updateQty(item.id, qty)}
                                        />
                                    </div>
                                );
                            })}
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
                        <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                            Ready to shop on {MARKETPLACES.find(m => m.id === selectedMarketplace)?.name}
                        </span>
                    </div>

                    {selectedMarketplace !== "instacart" && (
                        currentShopUrl ? (
                            <>
                                <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", maxWidth: 400 }}>
                                    Click below to open your personalized shopping list with all items ready to add.
                                </p>
                                <a
                                    href={currentShopUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn-primary"
                                    style={{ fontSize: "1rem", padding: "14px 36px" }}
                                >
                                    Shop on {MARKETPLACES.find(m => m.id === selectedMarketplace)?.name} <ExternalLink size={16} />
                                </a>
                            </>
                        ) : (
                            <p style={{ color: "var(--severity-insufficient)", fontSize: "0.9rem" }}>
                                Shopping link unavailable for {MARKETPLACES.find(m => m.id === selectedMarketplace)?.name}
                            </p>
                        )
                    )}

                    {/* Auto-Shop Section */}
                    <div
                        style={{
                            marginTop: 24,
                            width: "100%",
                            borderTop: "1px solid rgba(163,177,198,0.4)",
                            paddingTop: 24,
                        }}
                    >
                        <AutoShopSection items={cart.map(c => c.name)} retailer={selectedMarketplace} />
                    </div>
                </div>
            )}
        </div>
    );
}

function AutoShopSection({ items, retailer }: { items: string[], retailer: string }) {
    const [mode, setMode] = useState<"idle" | "running" | "done">("idle");
    const [logs, setLogs] = useState<string[]>([]);
    const [expanded, setExpanded] = useState(retailer === "instacart");

    const retailerName = retailer.charAt(0).toUpperCase() + retailer.slice(1);

    const startAutoShop = async () => {
        setMode("running");
        setLogs([
            `Starting ${retailerName} browser agent…`,
            `Opening browser — complete any login in the browser window if prompted.`,
        ]);

        try {
            const { autoShop } = await import("@/lib/api");
            await autoShop(items, {
                onLog: (log) => setLogs(prev => [...prev, log]),
                onDone: () => {
                    setLogs(prev => [...prev, "✨ ALL TASKS COMPLETED ✨"]);
                    setMode("done");
                },
                onError: (err) => setLogs(prev => [...prev, `❌ Error: ${err}`])
            }, retailer);
        } catch (e) {
            setLogs(prev => [...prev, `❌ System Error: ${e}`]);
        }
    };

    if (!expanded) {
        return (
            <button
                onClick={() => setExpanded(true)}
                className="btn-secondary"
                style={{ width: "100%", gap: 8, justifyContent: "center" }}
            >
                <Sparkles size={16} /> or enable Auto-Shop Agent
            </button>
        );
    }

    return (
        <div style={{ textAlign: "left", width: "100%" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 12, display: "flex", alignItems: "center", gap: 8, color: "var(--text-primary)" }}>
                🤖 Autonomous {retailerName} Shopping Agent
            </h3>

            {mode === "idle" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                        The agent will open a browser and automatically add these {items.length} items to your {retailerName} cart.
                        {retailer === "instacart"
                            ? " If prompted to log in, complete it in the browser window — your session is saved for future runs."
                            : " If asked for an OTP, enter it in the browser window — the session is saved for future runs."}
                    </p>
                    <button
                        onClick={startAutoShop}
                        className="btn-primary"
                    >
                        Launch Agent 🚀
                    </button>
                    <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", textAlign: "center" }}>
                        Your login session is saved after the first run — no re-login needed next time.
                    </p>
                </div>
            ) : (
                /* Terminal — neumorphic inset-deep well with dark interior */
                <div
                    style={{
                        background: "#1a1e2e",
                        color: "#a5f3a5",
                        fontFamily: "var(--font-mono)",
                        padding: 16,
                        boxShadow: "var(--shadow-inset-deep)",
                        borderRadius: "var(--radius-xl)",
                        height: 300,
                        overflowY: "auto",
                        fontSize: "0.9rem",
                    }}
                >
                    {logs.map((log, i) => (
                        <div key={i} style={{ marginBottom: 4 }}>{"> "}{log}</div>
                    ))}
                    {mode === "running" && <div style={{ animation: "blink 1s infinite" }}>_</div>}
                </div>
            )}
        </div>
    );
}
