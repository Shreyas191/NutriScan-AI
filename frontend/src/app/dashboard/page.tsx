export const dynamic = "force-dynamic";

import { Activity } from "lucide-react";
import DeficiencyCard from "@/components/DeficiencyCard";
import ExplanationPanel from "@/components/ExplanationPanel";
import FoodRecommendation from "@/components/FoodRecommendation";
import MedicalDisclaimer from "@/components/MedicalDisclaimer";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

/* ---- Mock data ---- */
const deficiencies = [
    {
        name: "Vitamin D",
        value: 14,
        unit: "ng/mL",
        normalRange: "30–100 ng/mL",
        severity: "severe" as const,
        percentage: 14,
    },
    {
        name: "Iron (Ferritin)",
        value: 18,
        unit: "ng/mL",
        normalRange: "20–200 ng/mL",
        severity: "insufficient" as const,
        percentage: 45,
    },
    {
        name: "Vitamin B12",
        value: 420,
        unit: "pg/mL",
        normalRange: "200–900 pg/mL",
        severity: "normal" as const,
        percentage: 72,
    },
];

const explanations = [
    {
        title: "Vitamin D — Severe Deficiency",
        severity: "severe" as const,
        explanation:
            "Your Vitamin D level is 14 ng/mL, which is significantly below the recommended range of 30–100 ng/mL. Low Vitamin D may contribute to fatigue, weakened immunity, muscle weakness, and reduced bone density. Increasing intake through diet (fatty fish, fortified milk) and supplementation may help improve levels. We recommend discussing a Vitamin D3 supplement with your healthcare provider.",
    },
    {
        title: "Iron (Ferritin) — Slightly Low",
        severity: "insufficient" as const,
        explanation:
            "Your Ferritin level is 18 ng/mL, just below the normal range of 20–200 ng/mL. Mildly low iron can cause fatigue, difficulty concentrating, and pale skin. Including iron-rich foods like spinach, lentils, and red meat in your diet can help. Pairing iron-rich foods with Vitamin C enhances absorption.",
    },
    {
        title: "Vitamin B12 — Normal",
        severity: "normal" as const,
        explanation:
            "Your Vitamin B12 level is 420 pg/mL, which is within the healthy range. No action needed — keep up your current dietary habits!",
    },
];

const foods = [
    { emoji: "🐟", name: "Wild Salmon", nutrient: "Vitamin D", amount: "570 IU per 3 oz" },
    { emoji: "🥛", name: "Fortified Milk", nutrient: "Vitamin D", amount: "120 IU per cup" },
    { emoji: "🥚", name: "Egg Yolks", nutrient: "Vitamin D", amount: "44 IU per yolk" },
    { emoji: "🍄", name: "UV Mushrooms", nutrient: "Vitamin D", amount: "400 IU per cup" },
    { emoji: "🥬", name: "Spinach", nutrient: "Iron", amount: "6.4 mg per cup" },
    { emoji: "🫘", name: "Lentils", nutrient: "Iron", amount: "3.3 mg per ½ cup" },
];

export default function DashboardPage() {
    return (
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px" }}>
            {/* Header */}
            <div style={{ marginBottom: 32 }}>
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        marginBottom: 8,
                    }}
                >
                    <Activity size={24} color="var(--accent-start)" />
                    <h1 style={{ fontSize: "1.6rem", fontWeight: 700 }}>Dashboard</h1>
                </div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
                    Your latest lab analysis — uploaded Feb 13, 2026
                </p>
            </div>

            <MedicalDisclaimer />

            {/* Deficiency Cards */}
            <section style={{ marginTop: 32 }}>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 16 }}>
                    Biomarker Summary
                </h2>
                <div
                    className="stagger-children"
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                        gap: 20,
                    }}
                >
                    {deficiencies.map((d) => (
                        <DeficiencyCard key={d.name} {...d} />
                    ))}
                </div>
            </section>

            {/* Explanations */}
            <section style={{ marginTop: 40 }}>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: 16 }}>
                    AI Explanations
                </h2>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {explanations.map((e) => (
                        <ExplanationPanel key={e.title} {...e} />
                    ))}
                </div>
            </section>

            {/* Food Recommendations */}
            <section style={{ marginTop: 40 }}>
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: 16,
                    }}
                >
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>
                        Recommended Foods
                    </h2>
                    <Link
                        href="/cart"
                        className="btn-secondary"
                        style={{ padding: "6px 16px", fontSize: "0.8rem" }}
                    >
                        View Cart <ArrowRight size={14} />
                    </Link>
                </div>
                <div
                    className="stagger-children"
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                        gap: 12,
                    }}
                >
                    {foods.map((f) => (
                        <FoodRecommendation key={f.name} {...f} />
                    ))}
                </div>
            </section>
        </div>
    );
}
