# Module: AI Insights

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

Generate human-readable summaries and contextual explanations for detected anomaly groups, giving operations teams immediate understanding without requiring manual metric analysis.

## What It Does

- Consumes anomaly group data produced by the AI Anomaly Detector.
- Generates natural-language summaries per anomaly group describing: what changed, by how much, since when, and potential impact.
- Assigns a confidence score reflecting the clarity and consistency of the underlying anomaly data.
- Provides severity context: explains why a group was classified at its severity level.
- Summaries are displayed on the Anomalies page within each group's detail panel.
- Updates summaries when anomaly groups evolve (new data points, severity changes).

## What It Does Not Do

- Does not identify root causes (see Root Cause module).
- Does not generate remediation recommendations.
- Does not learn from user feedback.
- Does not support multi-language summaries (English only).
- Does not provide trend predictions.

## Example Output

```
Summary: CPU usage on service "api-gateway" has exceeded normal bounds by 2.3x 
over the last 45 minutes. The deviation pattern is consistent with a sustained 
load increase rather than a spike. 3 related metrics (memory, latency_p99, 
error_rate) show concurrent deviations.

Severity: High (anomaly score 0.87, 4 concurrent metric deviations)
Confidence: 0.91
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/insights/{anomaly_group_id}` | Get AI insight summary for an anomaly group |
| GET | `/api/insights/recent` | Most recent generated insights |

## Dependencies

- **AI Anomaly Detector**: Provides anomaly group data to summarize.
- **VictoriaMetrics**: Queried for metric context during summary generation.
- **PostgreSQL**: Stores generated insight records.

## Frontend

- **Route:** Embedded within `/anomalies` detail panels
- **Key Features:** Summary card with confidence badge, severity explanation, metric context links.

## Known Limitations

1. English only.
2. No customization of summary tone or depth.
3. Does not learn from corrections.
4. Summary quality depends on anomaly data completeness.

---

*Rhinometric Team — info@rhinometric.com*
