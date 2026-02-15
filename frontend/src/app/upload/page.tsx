"use client";

import { useState, useCallback, useRef } from "react";
import {
    Upload,
    FileText,
    CheckCircle2,
    Loader2,
    CloudUpload,
    X,
    AlertTriangle,
    Brain,
    Wrench,
    MessageSquare,
} from "lucide-react";
import DietaryPreferenceSelector from "@/components/DietaryPreferenceSelector";
import Link from "next/link";
import {
    uploadReportStreaming,
    type ReasoningStep,
    type StreamDoneEvent,
} from "@/lib/api";

type UploadState = "idle" | "uploading" | "agent-running" | "done" | "error";

/* ------------------------------------------------------------------ */
/* Reasoning step display component                                    */
/* ------------------------------------------------------------------ */
function StepCard({ step }: { step: ReasoningStep }) {
    const isToolCall = step.action === "tool_call";
    const icon = isToolCall ? (
        <Wrench size={14} color="var(--accent-start)" />
    ) : (
        <MessageSquare size={14} color="var(--text-muted)" />
    );

    return (
        <div
            style={{
                display: "flex",
                gap: 12,
                padding: "12px 16px",
                borderRadius: "var(--radius-md)",
                background: isToolCall ? "var(--accent-glow)" : "transparent",
                border: `1px solid ${isToolCall ? "rgba(139, 92, 246, 0.2)" : "var(--border-default)"}`,
                animation: "fadeSlideUp 0.3s ease-out",
            }}
        >
            <div style={{ marginTop: 2, flexShrink: 0 }}>{icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
                {isToolCall && step.tool_name && (
                    <span
                        style={{
                            display: "inline-block",
                            fontSize: "0.7rem",
                            fontWeight: 700,
                            textTransform: "uppercase",
                            letterSpacing: "0.06em",
                            color: "var(--accent-start)",
                            fontFamily: "var(--font-mono)",
                            marginBottom: 4,
                        }}
                    >
                        {step.tool_name.replace(/_/g, " ")}
                    </span>
                )}
                {step.reasoning && (
                    <p
                        style={{
                            fontSize: "0.85rem",
                            color: "var(--text-secondary)",
                            lineHeight: 1.5,
                            margin: 0,
                        }}
                    >
                        {step.reasoning.length > 200
                            ? step.reasoning.slice(0, 200) + "…"
                            : step.reasoning}
                    </p>
                )}
                {step.result_summary && (
                    <p
                        style={{
                            fontSize: "0.82rem",
                            fontWeight: 600,
                            color: "var(--text-primary)",
                            marginTop: 4,
                            margin: 0,
                        }}
                    >
                        {step.result_summary}
                    </p>
                )}
            </div>
        </div>
    );
}

/* ------------------------------------------------------------------ */
/* Main upload page                                                    */
/* ------------------------------------------------------------------ */
export default function UploadPage() {
    const [state, setState] = useState<UploadState>("idle");
    const [file, setFile] = useState<File | null>(null);
    const [dragOver, setDragOver] = useState(false);
    const [preferences, setPreferences] = useState<string[]>([]);
    const [steps, setSteps] = useState<ReasoningStep[]>([]);
    const [doneResult, setDoneResult] = useState<StreamDoneEvent | null>(null);
    const [errorMessage, setErrorMessage] = useState("");
    const traceRef = useRef<HTMLDivElement>(null);

    const handleUpload = useCallback(
        async (selectedFile: File) => {
            setFile(selectedFile);
            setState("uploading");
            setSteps([]);
            setDoneResult(null);
            setErrorMessage("");

            // Brief delay for UI transition, then start streaming
            await new Promise((r) => setTimeout(r, 400));
            setState("agent-running");

            try {
                await uploadReportStreaming(selectedFile, preferences, {
                    onStep: (step) => {
                        setSteps((prev) => [...prev, step]);
                        // Auto-scroll trace panel
                        setTimeout(() => {
                            traceRef.current?.scrollTo({
                                top: traceRef.current.scrollHeight,
                                behavior: "smooth",
                            });
                        }, 50);
                    },
                    onDone: (result) => {
                        setDoneResult(result);
                        setState("done");
                    },
                    onError: (error) => {
                        setErrorMessage(error);
                        setState("error");
                    },
                });
            } catch (err) {
                setErrorMessage(
                    err instanceof Error ? err.message : "Agent failed"
                );
                setState("error");
            }
        },
        [preferences]
    );

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setDragOver(false);
            const droppedFile = e.dataTransfer.files[0];
            if (droppedFile?.type === "application/pdf") {
                handleUpload(droppedFile);
            }
        },
        [handleUpload]
    );

    const handleFileInput = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const selected = e.target.files?.[0];
            if (selected) handleUpload(selected);
        },
        [handleUpload]
    );

    const reset = () => {
        setState("idle");
        setFile(null);
        setSteps([]);
        setDoneResult(null);
        setErrorMessage("");
    };

    return (
        <div style={{ maxWidth: 760, margin: "0 auto", padding: "60px 24px" }}>
            {/* Header */}
            <div style={{ textAlign: "center", marginBottom: 40 }}>
                <div
                    style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 8,
                        background: "var(--accent-glow)",
                        borderRadius: "var(--radius-full)",
                        padding: "6px 16px",
                        marginBottom: 16,
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        color: "var(--accent-start)",
                    }}
                >
                    <Brain size={14} />
                    AI Agent Powered
                </div>
                <h1 style={{ fontSize: "1.8rem", fontWeight: 700, marginBottom: 8 }}>
                    Upload Your Lab Report
                </h1>
                <p style={{ color: "var(--text-secondary)", maxWidth: 480, margin: "0 auto" }}>
                    Our AI agent will autonomously analyse your bloodwork —
                    reasoning through each step and adapting to your results.
                </p>
            </div>

            {/* Upload zone */}
            {state === "idle" && (
                <>
                    <div
                        onDragOver={(e) => {
                            e.preventDefault();
                            setDragOver(true);
                        }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        style={{
                            border: `2px dashed ${dragOver ? "var(--accent-start)" : "var(--border-default)"}`,
                            borderRadius: "var(--radius-xl)",
                            padding: "60px 40px",
                            textAlign: "center",
                            transition: "all 0.3s",
                            background: dragOver ? "var(--accent-glow)" : "var(--bg-card)",
                            cursor: "pointer",
                        }}
                        onClick={() => document.getElementById("file-input")?.click()}
                    >
                        <div
                            className="animate-float"
                            style={{
                                width: 64,
                                height: 64,
                                borderRadius: "var(--radius-lg)",
                                background: "var(--accent-glow)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                margin: "0 auto 20px",
                            }}
                        >
                            <CloudUpload size={28} color="var(--accent-start)" />
                        </div>

                        <p style={{ fontWeight: 600, fontSize: "1rem", marginBottom: 8 }}>
                            Drag & drop your PDF here
                        </p>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 20 }}>
                            or click to browse · PDF format · Max 10 MB
                        </p>

                        <button className="btn-secondary" style={{ padding: "10px 24px", fontSize: "0.85rem" }}>
                            <Upload size={16} /> Choose File
                        </button>

                        <input
                            id="file-input"
                            type="file"
                            accept=".pdf"
                            onChange={handleFileInput}
                            style={{ display: "none" }}
                        />
                    </div>

                    <div style={{ marginTop: 32 }}>
                        <DietaryPreferenceSelector
                            selected={preferences}
                            onChange={setPreferences}
                        />
                    </div>
                </>
            )}

            {/* Brief uploading flash */}
            {state === "uploading" && (
                <div className="card" style={{ padding: 32, textAlign: "center" }}>
                    <FileText size={40} color="var(--accent-start)" style={{ margin: "0 auto 16px" }} />
                    <p style={{ fontWeight: 600 }}>{file?.name}</p>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                        Uploading to agent…
                    </p>
                </div>
            )}

            {/* Agent running — live reasoning trace */}
            {state === "agent-running" && (
                <div>
                    {/* Agent header */}
                    <div
                        className="card"
                        style={{
                            padding: "20px 24px",
                            display: "flex",
                            alignItems: "center",
                            gap: 14,
                            marginBottom: 16,
                        }}
                    >
                        <div
                            style={{
                                width: 40,
                                height: 40,
                                borderRadius: "var(--radius-full)",
                                background: "var(--accent-glow)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                flexShrink: 0,
                            }}
                        >
                            <Brain
                                size={20}
                                color="var(--accent-start)"
                                style={{ animation: "spin-slow 3s linear infinite" }}
                            />
                        </div>
                        <div>
                            <p style={{ fontWeight: 600, fontSize: "0.95rem", margin: 0 }}>
                                NutriScan AI Agent
                            </p>
                            <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", margin: 0, marginTop: 2 }}>
                                Analyzing {file?.name} · {steps.length} step{steps.length !== 1 ? "s" : ""} completed
                            </p>
                        </div>
                        <Loader2
                            size={20}
                            color="var(--accent-start)"
                            style={{ marginLeft: "auto", animation: "spin-slow 1.5s linear infinite" }}
                        />
                    </div>

                    {/* Reasoning trace panel */}
                    <div
                        ref={traceRef}
                        className="card"
                        style={{
                            padding: 16,
                            maxHeight: 420,
                            overflowY: "auto",
                            display: "flex",
                            flexDirection: "column",
                            gap: 8,
                        }}
                    >
                        {steps.length === 0 ? (
                            <p
                                style={{
                                    textAlign: "center",
                                    padding: 32,
                                    color: "var(--text-muted)",
                                    fontSize: "0.85rem",
                                }}
                            >
                                Agent is starting up…
                            </p>
                        ) : (
                            steps.map((step) => (
                                <StepCard key={step.step_number} step={step} />
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Done */}
            {state === "done" && doneResult && (
                <div>
                    {/* Success card */}
                    <div className="card" style={{ padding: 40, textAlign: "center", marginBottom: 16 }}>
                        <CheckCircle2
                            size={48}
                            color="var(--severity-normal)"
                            style={{ margin: "0 auto 16px" }}
                        />
                        <p style={{ fontWeight: 700, fontSize: "1.2rem", marginBottom: 8 }}>
                            Agent Analysis Complete!
                        </p>
                        <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: 8 }}>
                            {doneResult.biomarker_count} biomarkers extracted ·{" "}
                            {doneResult.deficiency_count > 0 ? (
                                <span style={{ color: "var(--severity-severe)", fontWeight: 600 }}>
                                    {doneResult.deficiency_count} deficienc{doneResult.deficiency_count !== 1 ? "ies" : "y"} detected
                                </span>
                            ) : (
                                <span style={{ color: "var(--severity-normal)", fontWeight: 600 }}>
                                    All normal
                                </span>
                            )}
                            {doneResult.recommendation_count > 0 && (
                                <> · {doneResult.recommendation_count} food recommendations</>
                            )}
                        </p>
                        <p
                            style={{
                                fontSize: "0.8rem",
                                color: "var(--text-muted)",
                                marginBottom: 28,
                            }}
                        >
                            Agent completed in {steps.length} reasoning steps
                        </p>

                        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
                            <Link href={`/results?id=${doneResult.report_id}`} className="btn-primary">
                                View Results
                            </Link>
                            <button className="btn-secondary" onClick={reset}>
                                <X size={16} /> Upload Another
                            </button>
                        </div>
                    </div>

                    {/* Collapsed trace */}
                    {steps.length > 0 && (
                        <details className="card" style={{ padding: 16 }}>
                            <summary
                                style={{
                                    cursor: "pointer",
                                    fontWeight: 600,
                                    fontSize: "0.85rem",
                                    color: "var(--text-secondary)",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 8,
                                }}
                            >
                                <Brain size={14} />
                                View Agent Reasoning Trace ({steps.length} steps)
                            </summary>
                            <div
                                style={{
                                    marginTop: 12,
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: 8,
                                    maxHeight: 320,
                                    overflowY: "auto",
                                }}
                            >
                                {steps.map((step) => (
                                    <StepCard key={step.step_number} step={step} />
                                ))}
                            </div>
                        </details>
                    )}
                </div>
            )}

            {/* Error */}
            {state === "error" && (
                <div>
                    <div className="card" style={{ padding: 40, textAlign: "center", marginBottom: 16 }}>
                        <AlertTriangle
                            size={48}
                            color="var(--severity-severe)"
                            style={{ margin: "0 auto 16px" }}
                        />
                        <p style={{ fontWeight: 700, fontSize: "1.2rem", marginBottom: 8 }}>
                            Agent Error
                        </p>
                        <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: 28 }}>
                            {errorMessage}
                        </p>
                        <button className="btn-secondary" onClick={reset}>
                            <X size={16} /> Try Again
                        </button>
                    </div>

                    {/* Show partial trace if available */}
                    {steps.length > 0 && (
                        <details className="card" style={{ padding: 16 }}>
                            <summary
                                style={{
                                    cursor: "pointer",
                                    fontWeight: 600,
                                    fontSize: "0.85rem",
                                    color: "var(--text-secondary)",
                                }}
                            >
                                Partial Reasoning Trace ({steps.length} steps)
                            </summary>
                            <div
                                style={{
                                    marginTop: 12,
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: 8,
                                    maxHeight: 320,
                                    overflowY: "auto",
                                }}
                            >
                                {steps.map((step) => (
                                    <StepCard key={step.step_number} step={step} />
                                ))}
                            </div>
                        </details>
                    )}

                    <div style={{ marginTop: 32 }}>
                        <DietaryPreferenceSelector
                            selected={preferences}
                            onChange={setPreferences}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
