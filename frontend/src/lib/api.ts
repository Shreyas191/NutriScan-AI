/**
 * API client for NutriScan AI backend.
 *
 * Base URL defaults to localhost:8000 in development.
 * Set NEXT_PUBLIC_API_URL to override.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

export interface UploadResponse {
    report_id: string;
    filename: string;
    message: string;
}

export interface Biomarker {
    test_name: string;
    value: number;
    unit: string;
    reference_range: string;
    flag: string | null;
}

export interface Deficiency {
    name: string;
    value: number;
    unit: string;
    normal_range: string;
    severity: "normal" | "insufficient" | "severe";
    percentage: number;
}

export interface Explanation {
    title: string;
    severity: "normal" | "insufficient" | "severe";
    explanation: string;
}

export interface CartItem {
    id: number;
    name: string;
    emoji: string;
    nutrient: string;
    amount: string;
    category: string;
    quantity: number;
    instacart_url: string;
}

export interface ReasoningStep {
    step_number: number;
    action: "reasoning" | "tool_call";
    tool_name: string | null;
    reasoning: string;
    result_summary: string;
}

export interface AnalysisResponse {
    report_id: string;
    status: string;
    biomarkers: Biomarker[];
    deficiencies: Deficiency[];
    explanations: Explanation[];
    cart_items: CartItem[];
    shop_all_url: string;
    ocr_confidence: number;
    ocr_method: string;
    reasoning_steps: ReasoningStep[];
}

export interface StreamDoneEvent {
    report_id: string;
    deficiency_count: number;
    biomarker_count: number;
    recommendation_count: number;
}

/* ------------------------------------------------------------------ */
/* API calls                                                           */
/* ------------------------------------------------------------------ */

/**
 * Upload a PDF and run the AI agent (non-streaming).
 */
export async function uploadReport(
    file: File,
    dietaryPreferences: string[] = [],
): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (dietaryPreferences.length > 0) {
        formData.append("dietary_preferences", dietaryPreferences.join(","));
    }

    const res = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload failed");
    }

    return res.json();
}

/**
 * Upload a PDF and stream the AI agent's reasoning steps in real-time.
 *
 * Uses Server-Sent Events (SSE) via POST to stream steps.
 */
export async function uploadReportStreaming(
    file: File,
    dietaryPreferences: string[] = [],
    callbacks: {
        onStep: (step: ReasoningStep) => void;
        onDone: (result: StreamDoneEvent) => void;
        onError: (error: string) => void;
    },
): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);
    if (dietaryPreferences.length > 0) {
        formData.append("dietary_preferences", dietaryPreferences.join(","));
    }

    const res = await fetch(`${API_BASE}/api/upload/stream`, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload failed");
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error("Streaming not supported");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const events = buffer.split("\n\n");
        buffer = events.pop() || ""; // Keep incomplete event in buffer

        for (const event of events) {
            if (!event.trim()) continue;

            const lines = event.split("\n");
            let eventType = "";
            let eventData = "";

            for (const line of lines) {
                if (line.startsWith("event: ")) {
                    eventType = line.slice(7);
                } else if (line.startsWith("data: ")) {
                    eventData = line.slice(6);
                }
            }

            if (!eventData) continue;

            try {
                const parsed = JSON.parse(eventData);

                switch (eventType) {
                    case "step":
                        callbacks.onStep(parsed as ReasoningStep);
                        break;
                    case "done":
                        callbacks.onDone(parsed as StreamDoneEvent);
                        break;
                    case "error":
                        callbacks.onError(parsed.error || "Unknown error");
                        break;
                }
            } catch {
                // Skip malformed events
            }
        }
    }
}

/**
 * Get the full analysis results for a report.
 */
export async function getReport(reportId: string): Promise<AnalysisResponse> {
    const res = await fetch(`${API_BASE}/api/reports/${reportId}`);

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Report not found" }));
        throw new Error(err.detail || "Report not found");
    }

    return res.json();
}
