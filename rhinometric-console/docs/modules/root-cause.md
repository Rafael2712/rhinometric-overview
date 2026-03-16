# Module: Root Cause Analysis

**Version:** 2.7.0  
**Classification:** Internal  
**Maintained by:** Rhinometric Team — info@rhinometric.com

---

## Purpose

When an incident is created from anomaly alerts, automatically identify the most likely origin of the failure by analyzing service dependencies, temporal sequences, and anomaly propagation patterns.

## What It Does

- Triggered automatically when an incident is created from one or more anomaly alerts.
- Traverses the service dependency graph (from Service Map data) starting from the alerted service.
- Identifies upstream and downstream services that show concurrent anomalies.
- Ranks candidate root causes by:
  - **Temporal precedence**: Which service anomaly appeared first.
  - **Dependency depth**: Services closer to the dependency root score higher.
  - **Anomaly severity**: Higher severity groups rank higher.
  - **Propagation pattern**: Fan-out from a single source increases confidence.
- Produces a ranked list of candidate root causes with confidence scores.
- Results are displayed on the incident detail page.

## What It Does Not Do

- Does not perform code-level analysis (no stack trace parsing).
- Does not integrate with change management (no deployment correlation).
- Does not provide remediation suggestions.
- Does not learn from past incident resolutions.
- Does not work if Service Map data is not available.

## Analysis Flow

```
Incident Created
      │
      ▼
Fetch linked anomaly groups
      │
      ▼
Query Service Map for dependencies
      │
      ▼
Search adjacent services for concurrent anomalies
      │
      ▼
Score and rank candidates
      │
      ▼
Store results → Display on incident page
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/root-cause/{incident_id}` | Get root cause analysis for an incident |
| POST | `/api/root-cause/{incident_id}/refresh` | Re-run analysis with updated data |

## Dependencies

- **Incident Module**: Triggers analysis on incident creation.
- **AI Anomaly Detector**: Provides anomaly group data.
- **Service Map**: Provides dependency graph for traversal.
- **PostgreSQL**: Stores analysis results.

## Frontend

- **Route:** `/root-cause` (also embedded in `/incidents/{id}`)
- **Key Features:** Ranked candidate list with confidence bars, dependency path visualization, temporal sequence chart.

## Known Limitations

1. Requires Service Map data — will not function without it.
2. Accuracy depends on the completeness of the dependency graph.
3. No learning from resolved incidents.
4. No integration with CI/CD for deployment correlation.
5. Analysis is point-in-time — does not update as new data arrives.

---

*Rhinometric Team — info@rhinometric.com*
