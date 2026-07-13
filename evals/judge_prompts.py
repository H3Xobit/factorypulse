"""LLM-as-judge rubrics for diagnosis accuracy."""

JUDGE_SYSTEM = """Score predicted root_cause vs expected_root_cause.
Return JSON {score: 0|0.5|1, rationale: string}.
1 = same cause, 0.5 = partially overlapping, 0 = unrelated.
"""

JUDGE_USER = """Expected: {expected}
Predicted: {predicted}
"""
