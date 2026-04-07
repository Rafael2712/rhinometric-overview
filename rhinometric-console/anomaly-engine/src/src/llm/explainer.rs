use serde::{Deserialize, Serialize};

use crate::persistence::repository::AnomalyRow;

// ─── Output types ───

/// The structured LLM explanation — V1.6.1 calibrated output format.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ExplanationResponse {
    pub summary: String,
    pub current_state: String,
    pub prediction_outlook: String,
    pub key_signals: Vec<String>,
    pub risk_interpretation: String,
    pub confidence_note: String,
}

/// Full API response including metadata.
#[derive(Debug, Serialize, Clone)]
pub struct ExplanationApiResponse {
    pub anomaly_id: uuid::Uuid,
    pub service_name: String,
    pub explanation: ExplanationResponse,
    pub model: String,
    pub cached: bool,
}

// ─── OpenAI request/response types ───

#[derive(Serialize)]
struct ChatRequest {
    model: String,
    messages: Vec<ChatMessage>,
    temperature: f32,
    top_p: f32,
    response_format: ResponseFormat,
}

#[derive(Serialize)]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct ResponseFormat {
    #[serde(rename = "type")]
    format_type: String,
}

#[derive(Deserialize)]
struct ChatResponse {
    choices: Vec<ChatChoice>,
}

#[derive(Deserialize)]
struct ChatChoice {
    message: ChatMessageResponse,
}

#[derive(Deserialize)]
struct ChatMessageResponse {
    content: String,
}

// ─── Prompt construction ───

/// Fixed system prompt — V1.6.1 calibrated with signal prioritization, language consistency, state/prediction separation.
fn system_prompt() -> &'static str {
    r#"You are a STRICT, deterministic explanation layer for a service monitoring anomaly engine. Your ONLY role is to translate structured anomaly and prediction data into clear, human-readable explanations.

HARD RULES — VIOLATION OF ANY RULE IS A FAILURE:

RULE 1 — NO NEW INFORMATION:
You MUST NOT add causes, reasons, or details not present in the input data.
You MUST NOT mention infrastructure, network, databases, servers, containers, or architecture unless explicitly present in the reason_codes or prediction_reason_codes.
You MUST NOT speculate about possible causes.

RULE 2 — REASON CODES AS PRIMARY DRIVER:
Build ALL explanations directly from reason_codes and prediction_reason_codes.
These are the authoritative source for what is happening and what is predicted.
Do NOT infer causes from raw signal numbers alone — use the codes.

RULE 3 — TRACE SIGNAL FILTERING (CRITICAL):
Trace signals (trace_bottleneck_score, trace_p95_latency_ms, trace_error_rate, trace_slow_operations) MUST be completely ignored UNLESS:
  - The TRACE_SCORE category score (from category_scores) is >= 20, OR
  - trace_bottleneck_score >= 0.5
If NEITHER condition is met, do NOT mention trace data at all — not in current_state, not in key_signals, not anywhere.
When trace IS included, it is ALWAYS secondary supporting evidence, never a primary driver.

RULE 4 — SIGNAL PRIORITY ORDER:
When listing or discussing signals, ALWAYS follow this priority order:
  1. Latency signals (baseline_deviation, latency_trend_slope, latency_trend_r2)
  2. Error signals (log_error_burst_ratio)
  3. Availability signals (from reason_codes if present)
  4. Trace signals (only if Rule 3 conditions are met)
Higher-priority signals that are non-trivial MUST appear before lower-priority ones.

RULE 5 — HARDCODED LANGUAGE BY SCORE RANGE:
You MUST use these EXACT opening phrases in the summary based on anomaly_score:
  - Score < 10:  Start summary with "The service is currently stable"
  - Score 10–30: Start summary with "The service is showing minor degradation"
  - Score 30–60: Start summary with "The service is in a degraded state"
  - Score > 60:  Start summary with "The service is in a critical state"
NEVER contradict the score. A score of 5 MUST NOT use words like "pressure", "concerning", "elevated", "anomalous". A score > 60 MUST NOT use "stable" or "minor".

RULE 6 — STRICT STATE vs PREDICTION SEPARATION:
current_state MUST describe ONLY the present situation using present tense ("is", "shows", "indicates").
current_state MUST NOT contain any forward-looking language ("will", "may become", "could lead to", "trending toward").
prediction_outlook MUST describe ONLY the predicted future using future/conditional tense ("is expected to", "may", "is likely to").
prediction_outlook MUST NOT restate current conditions.
These two fields must never cross-reference each other's time domain.

RULE 7 — CONFIDENCE AWARENESS — Match language tone to confidence level:
- high → assertive language ("is experiencing", "will likely", "clearly shows")
- medium → cautious language ("appears to be", "may indicate", "suggests")
- low → uncertain language ("shows some signs of", "there are limited indications of", "possibly")

RULE 8 — CONSISTENCY CHECK:
Before outputting, verify:
  a) summary STARTS with the exact phrase from Rule 5
  b) current_state contains ZERO future-tense words
  c) prediction_outlook contains ZERO present-state descriptions
  d) key_signals list contains NO trace signals if Rule 3 excludes them
  e) No signal is described as "elevated" or "concerning" if its value is within normal range

RULE 9 — NO RECOMMENDATIONS:
Do NOT suggest fixes, actions, remediation, next steps, or investigations.
Only describe the current situation and the predicted trajectory based on the data provided.

OUTPUT: Return ONLY a single JSON object with exactly these 6 keys — no markdown, no code fences, no extra text:
{
  "summary": "One or two sentences: MUST start with the hardcoded phrase from Rule 5. Then a brief outlook statement.",
  "current_state": "Paragraph explaining the current anomaly state, referencing category_scores and reason_codes. Present tense only. Follow signal priority order from Rule 4.",
  "prediction_outlook": "Paragraph explaining the predicted future risk using prediction_reason_codes and predicted_horizon_minutes. Future/conditional tense only. If predicted_risk_score is 0 or null, write exactly: 'No predictive risk signals are currently active.'",
  "key_signals": ["Each entry is one specific measurable signal from the data, e.g. 'Latency is 230% above baseline', 'Error burst ratio is 4.1x normal'. Follow priority order from Rule 4. Exclude trace signals unless Rule 3 conditions are met. Include only signals with non-trivial values."],
  "risk_interpretation": "One sentence interpreting predicted_risk_level: none='No elevated risk detected', low='Early signs of potential issues detected', medium='Growing instability observed in monitored signals', high='Continued degradation is likely based on current trends', critical='Imminent failure risk based on multiple converging signals'. Match to actual level.",
  "confidence_note": "One sentence explaining why confidence is at its current level, referencing signal count and consistency."
}"#
}

/// Build the user prompt by injecting structured anomaly data (and nothing else).
/// V1.6.1: adds explicit TRACE_SCORE value for trace filtering rule.
pub fn build_user_prompt(row: &AnomalyRow) -> String {
    let category_scores = serde_json::to_string_pretty(&row.category_scores)
        .unwrap_or_else(|_| "{}".to_string());

    let reason_codes = serde_json::to_string_pretty(&row.reason_codes)
        .unwrap_or_else(|_| "[]".to_string());

    let pred_reason_codes = row
        .prediction_reason_codes
        .as_ref()
        .map(|v| serde_json::to_string_pretty(v).unwrap_or_else(|_| "[]".to_string()))
        .unwrap_or_else(|| "[]".to_string());

    let pred_summary = row.prediction_summary.as_deref().unwrap_or("None");

    let pred_horizon = row
        .predicted_horizon_minutes
        .map(|v| v.to_string())
        .unwrap_or_else(|| "N/A".to_string());

    // Extract TRACE_SCORE from category_scores for trace filtering rule
    let trace_score = row
        .category_scores
        .get("TRACE_SCORE")
        .and_then(|v| v.as_f64())
        .unwrap_or(0.0);

    let bottleneck = row.trace_bottleneck_score.unwrap_or(0.0);
    let include_trace = trace_score >= 20.0 || bottleneck >= 0.5;

    format!(
        r#"Analyze this anomaly data and generate the explanation JSON.

SERVICE: {service_name}
ANOMALY SCORE: {score}/100
SEVERITY: {severity}
CONFIDENCE: {confidence_label}

CATEGORY SCORES:
{category_scores}

REASON CODES:
{reason_codes}

CURRENT SIGNALS:
- Baseline deviation: {baseline_dev:.1}%
- Latency trend slope: {slope:.4}
- Latency trend R²: {r2:.4}
- Log error burst ratio: {burst:.2}x
{trace_section}
TRACE FILTERING: TRACE_SCORE={trace_score:.0}, bottleneck={bn:.4} → trace signals {trace_verdict} (Rule 3)

PREDICTION:
- Predicted risk score: {pred_risk}/100
- Predicted risk level: {pred_level}
- Predicted horizon: {pred_horizon} minutes
- Prediction confidence: {pred_conf}
- Prediction reason codes: {pred_reason_codes}
- Prediction summary: {pred_summary}

EVIDENCE (engine-generated):
{evidence}

Generate the explanation JSON now."#,
        service_name = row.service_name,
        score = row.anomaly_score,
        severity = row.severity,
        confidence_label = row.confidence_label,
        category_scores = category_scores,
        reason_codes = reason_codes,
        baseline_dev = row.baseline_deviation_pct.unwrap_or(0.0),
        slope = row.latency_trend_slope.unwrap_or(0.0),
        r2 = row.latency_trend_r2.unwrap_or(0.0),
        burst = row.log_error_burst_ratio.unwrap_or(0.0),
        trace_section = if include_trace {
            format!(
                "- Trace bottleneck score: {:.4}\n- Trace P95 latency: {:.1}ms\n- Trace error rate: {:.4}\n- Trace slow operations: {}\n",
                bottleneck,
                row.trace_p95_latency_ms.unwrap_or(0.0),
                row.trace_error_rate.unwrap_or(0.0),
                row.trace_slow_operations.unwrap_or(0),
            )
        } else {
            String::new()
        },
        trace_score = trace_score,
        bn = bottleneck,
        trace_verdict = if include_trace { "INCLUDED — may be referenced" } else { "EXCLUDED — do NOT mention trace data" },
        pred_risk = row.predicted_risk_score.unwrap_or(0),
        pred_level = row.predicted_risk_level.as_deref().unwrap_or("none"),
        pred_horizon = pred_horizon,
        pred_conf = row.prediction_confidence.as_deref().unwrap_or("low"),
        pred_reason_codes = pred_reason_codes,
        pred_summary = pred_summary,
        evidence = row.evidence_summary,
    )
}

// ─── OpenAI API call ───

/// Call the OpenAI chat completions API with deterministic settings.
pub async fn generate_explanation(
    client: &reqwest::Client,
    api_key: &str,
    model: &str,
    row: &AnomalyRow,
) -> Result<ExplanationResponse, String> {
    let system = system_prompt().to_string();
    let user = build_user_prompt(row);

    let request = ChatRequest {
        model: model.to_string(),
        messages: vec![
            ChatMessage {
                role: "system".to_string(),
                content: system,
            },
            ChatMessage {
                role: "user".to_string(),
                content: user,
            },
        ],
        temperature: 0.0,
        top_p: 0.0,
        response_format: ResponseFormat {
            format_type: "json_object".to_string(),
        },
    };

    let resp = client
        .post("https://api.openai.com/v1/chat/completions")
        .header("Authorization", format!("Bearer {api_key}"))
        .header("Content-Type", "application/json")
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("OpenAI request failed: {e}"))?;

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("OpenAI API error {status}: {body}"));
    }

    let chat_resp: ChatResponse = resp
        .json()
        .await
        .map_err(|e| format!("Failed to parse OpenAI response: {e}"))?;

    let content = chat_resp
        .choices
        .first()
        .ok_or_else(|| "No choices in OpenAI response".to_string())?
        .message
        .content
        .clone();

    let explanation: ExplanationResponse = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse explanation JSON: {e}. Raw: {content}"))?;

    Ok(explanation)
}
