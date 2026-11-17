# AgentOps Evaluation Methodology & Scoring Rubric

## Overview
AgentOps implements reproducible, automated evaluation for AI agents. Subjective scores are clearly differentiated from deterministic assertions.

## Automated Evaluator Dimensions

| Evaluator | Methodology | Pass Threshold | Formula / Criteria |
|---|---|---|---|
| **Exact Match** | Case-insensitive normalized string comparison | 1.0 (100%) | `actual.strip().lower() == expected.strip().lower()` |
| **JSON Schema Compliance** | JSON parser & required fields validation | 1.0 (100%) | Valid JSON syntax + all `required` properties present |
| **Keyword Adherence** | Ground-truth keyword presence check | $\ge 0.70$ (70%) | $1.0 - (\text{missing\_keywords} / \text{total\_keywords})$ |
| **Tool Selection Accuracy** | Verification of expected tool invocations | $\ge 0.70$ (70%) | $\text{matched\_tools} / \text{expected\_tools}$ |
| **Latency SLA Threshold** | Wall-clock execution time upper bound | 1.0 (100%) | $\text{latency\_ms} \le \text{max\_latency\_ms}$ |
| **LLM-as-Judge (Rule-based)**| Structured rubric evaluation | $\ge 0.70$ (70%) | Groundedness, relevance, constraint satisfaction |

## Regression Comparison
- Golden evaluation datasets are versioned (`v1.0.0`, `v1.1.0`).
- Each evaluation run stores the agent version (`agent_version`), pass rate, average latency, and per-case diagnostic reasons.
- Developers can immediately identify whether a prompt engineering or tool modification degraded regression scores.
