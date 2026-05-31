import Link from "next/link";
import {
  ScanLine,
  FileUp,
  Brain,
  ShoppingCart,
  ArrowRight,
  Sparkles,
  Shield,
  Zap,
} from "lucide-react";

const features = [
  {
    icon: FileUp,
    title: "Upload Lab Report",
    desc: "Drop your bloodwork PDF — scanned or digital. We handle the rest.",
  },
  {
    icon: Brain,
    title: "AI-Powered Analysis",
    desc: "Detects deficiencies and explains results in plain English.",
  },
  {
    icon: ShoppingCart,
    title: "Instant Grocery Cart",
    desc: "Get a personalised list of foods & supplements to fix what's low.",
  },
];

const stats = [
  { value: "<60s", label: "Upload to cart" },
  { value: "100%", label: "Evidence-based" },
  { value: "Free", label: "To get started" },
];

export default function Home() {
  return (
    <div style={{ overflow: "hidden" }}>
      {/* ---- Hero ---- */}
      <section
        style={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "120px 24px 80px",
          minHeight: "85vh",
        }}
      >
        {/* Decorative neumorphic circles — desktop only */}
        <div
          style={{
            position: "absolute",
            right: "5%",
            top: "50%",
            transform: "translateY(-50%)",
            pointerEvents: "none",
          }}
          className="hidden lg:block"
        >
          {/* Outer ring — extruded */}
          <div
            style={{
              width: 280,
              height: 280,
              borderRadius: "50%",
              background: "var(--bg-primary)",
              boxShadow: "var(--shadow-extruded)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {/* Middle ring — inset */}
            <div
              style={{
                width: 180,
                height: 180,
                borderRadius: "50%",
                background: "var(--bg-primary)",
                boxShadow: "var(--shadow-inset)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {/* Inner — extruded accent */}
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: "50%",
                  background:
                    "linear-gradient(135deg, var(--accent-start), var(--accent-end))",
                  boxShadow:
                    "5px 5px 12px rgba(108,99,255,0.4), -3px -3px 8px rgba(255,255,255,0.5)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <ScanLine size={32} color="#fff" />
              </div>
            </div>
          </div>
        </div>

        <div className="animate-fade-in-up" style={{ position: "relative", zIndex: 1 }}>
          {/* Badge */}
          <div
            className="badge"
            style={{
              color: "var(--accent-start)",
              marginBottom: 24,
              fontSize: "0.8rem",
              padding: "6px 16px",
            }}
          >
            <Sparkles size={14} />
            AI-Powered Health Intelligence
          </div>

          <h1
            style={{
              fontSize: "clamp(2.5rem, 6vw, 4.5rem)",
              fontWeight: 800,
              lineHeight: 1.1,
              maxWidth: 720,
              margin: "0 auto 20px",
              letterSpacing: "-0.03em",
              fontFamily: "var(--font-display)",
              color: "var(--text-primary)",
            }}
          >
            From Bloodwork
            <br />
            to <span className="gradient-text">Basket</span>
          </h1>

          <p
            style={{
              fontSize: "clamp(1rem, 2vw, 1.2rem)",
              color: "var(--text-secondary)",
              maxWidth: 520,
              margin: "0 auto 40px",
              lineHeight: 1.7,
            }}
          >
            Upload your lab report. Understand your deficiencies.
            Get a personalised grocery cart — automatically.
          </p>

          {/* CTAs */}
          <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/upload" className="btn-primary" style={{ fontSize: "1rem", padding: "14px 32px" }}>
              Get Started <ArrowRight size={18} />
            </Link>
            <Link href="/dashboard" className="btn-secondary" style={{ fontSize: "1rem", padding: "14px 32px" }}>
              View Demo
            </Link>
          </div>
        </div>
      </section>

      {/* ---- Stats ---- */}
      <section
        style={{
          maxWidth: 800,
          margin: "0 auto",
          padding: "0 24px 80px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: 24,
          textAlign: "center",
        }}
      >
        {stats.map(({ value, label }) => (
          <div key={label} className="card" style={{ padding: 24 }}>
            {/* Inset well for the number */}
            <div
              style={{
                background: "var(--bg-primary)",
                boxShadow: "var(--shadow-inset)",
                borderRadius: "var(--radius-lg)",
                padding: "12px 20px",
                marginBottom: 8,
                display: "inline-block",
              }}
            >
              <span
                className="gradient-text"
                style={{
                  fontSize: "1.8rem",
                  fontWeight: 800,
                  fontFamily: "var(--font-mono)",
                }}
              >
                {value}
              </span>
            </div>
            <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 4 }}>
              {label}
            </div>
          </div>
        ))}
      </section>

      {/* ---- How it works ---- */}
      <section style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px 100px" }}>
        <h2
          style={{
            textAlign: "center",
            fontSize: "2rem",
            fontWeight: 700,
            marginBottom: 12,
            fontFamily: "var(--font-display)",
            color: "var(--text-primary)",
          }}
        >
          How It Works
        </h2>
        <p
          style={{
            textAlign: "center",
            color: "var(--text-secondary)",
            marginBottom: 48,
            maxWidth: 480,
            marginLeft: "auto",
            marginRight: "auto",
          }}
        >
          Three simple steps from confusing lab numbers to a healthier plate.
        </p>

        <div
          className="stagger-children"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 28,
          }}
        >
          {features.map(({ icon: Icon, title, desc }, i) => (
            <div
              key={title}
              className="card animate-fade-in-up"
              style={{ padding: 32, position: "relative" }}
            >
              {/* Step number — extruded pill */}
              <div
                style={{
                  position: "absolute",
                  top: 16,
                  right: 20,
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.7rem",
                  color: "var(--text-muted)",
                  letterSpacing: "0.1em",
                  background: "var(--bg-primary)",
                  boxShadow: "var(--shadow-extruded-sm)",
                  borderRadius: "var(--radius-full)",
                  padding: "3px 10px",
                }}
              >
                {String(i + 1).padStart(2, "0")}
              </div>

              {/* Icon well — inset deep */}
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: "var(--radius-md)",
                  background: "var(--bg-primary)",
                  boxShadow: "var(--shadow-inset-deep)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 20,
                }}
              >
                <Icon size={24} color="var(--accent-start)" />
              </div>

              <h3
                style={{
                  fontSize: "1.15rem",
                  fontWeight: 600,
                  marginBottom: 8,
                  color: "var(--text-primary)",
                }}
              >
                {title}
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>
                {desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ---- Trust bar ---- */}
      <section
        style={{
          maxWidth: 800,
          margin: "0 auto",
          padding: "0 24px 100px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 20,
        }}
      >
        {[
          { icon: Shield, label: "HIPAA-Ready Architecture" },
          { icon: Zap, label: "Results in Under 60 Seconds" },
          { icon: ScanLine, label: "Evidence-Based Nutrition" },
        ].map(({ icon: Icon, label }) => (
          <div
            key={label}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "16px 24px",
              borderRadius: "var(--radius-full)",
              background: "var(--bg-primary)",
              boxShadow: "var(--shadow-extruded-sm)",
              fontSize: "0.85rem",
              color: "var(--text-secondary)",
            }}
          >
            <Icon size={18} color="var(--accent-start)" />
            {label}
          </div>
        ))}
      </section>

      {/* ---- CTA banner ---- */}
      <section
        className="gradient-border"
        style={{
          maxWidth: 900,
          margin: "0 auto 80px",
          borderRadius: "var(--radius-xl)",
          padding: "60px 40px",
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontSize: "1.8rem",
            fontWeight: 700,
            marginBottom: 12,
            fontFamily: "var(--font-display)",
            color: "var(--text-primary)",
          }}
        >
          Ready to decode your bloodwork?
        </h2>
        <p
          style={{
            color: "var(--text-secondary)",
            marginBottom: 32,
            maxWidth: 420,
            marginLeft: "auto",
            marginRight: "auto",
          }}
        >
          Upload your lab report and get personalised food recommendations in
          under a minute.
        </p>
        <Link href="/upload" className="btn-primary" style={{ fontSize: "1rem", padding: "14px 36px" }}>
          Upload Your Report <ArrowRight size={18} />
        </Link>
      </section>
    </div>
  );
}
