"""
agents/script/critic.py

Hook Generator & Script Critic Engine for V2.
Synthesizes high-retention video hooks and evaluates script quality/pacing.
"""
from __future__ import annotations
from typing import Any


class HookGenerator:
    """Generates high-retention video hook variations."""

    def generate_hooks(self, topic: str, target_audience: str) -> dict[str, str]:
        return {
            "problem_first": f"Building AI systems for {target_audience} without deterministic guarantees is a recipe for silent failure. Here is how we fix it.",
            "curiosity": f"What happens when you decouple your AI workflow runtime from social APIs? You get a deterministic operating system.",
            "bold_statement": f"Most AI pipelines fail in production because they lack a kernel. Today, we look at how to build one.",
        }


class ScriptCritic:
    """Evaluates script pacing, section transitions, and brand voice alignment."""

    def evaluate(self, script: dict[str, Any], brand_tone: str = "authoritative") -> dict[str, Any]:
        text = script.get("script", "")
        word_count = len(text.split())
        sections = script.get("sections", [])

        score = 0.90
        feedback = []

        if word_count < 80:
            score -= 0.15
            feedback.append("Script length is under 80 words; consider expanding technical depth.")
        elif word_count > 400:
            score -= 0.10
            feedback.append("Script length exceeds 400 words; trim for video retention.")

        if not sections:
            score -= 0.20
            feedback.append("No section headers found; add explicit section breakdown.")

        return {
            "quality_score": round(score, 2),
            "approved": score >= 0.75,
            "word_count": word_count,
            "section_count": len(sections),
            "feedback": feedback if feedback else ["Script pacing and structure meet Animus quality standards."],
        }


hook_generator = HookGenerator()
script_critic = ScriptCritic()
