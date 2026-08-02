"""
Review Agent — Department: Creative

Checks scripts for:
- Grammar and clarity
- Factual accuracy (flags claims that need verification)
- Brand tone compliance
- Copyright / hallucination risk
- Duplicate ideas (vs knowledge base)

Returns: Approved or Rewrite with specific feedback
"""
from __future__ import annotations
from typing import Any

from agents.base import BaseAgent, AgentContext

REVIEW_SYSTEM_PROMPT = """You are the Review Agent for Animus Studio.
Your job is to quality-check video scripts before production.

Check for:
1. Grammar and readability
2. Factual risk (flag any specific claims that could be wrong)
3. Brand tone compliance
4. Copyright risk (flag any content that might be problematic)
5. Duplicate / generic content

Return JSON:
{
  "verdict": "approved | rewrite",
  "score": 0-100,
  "issues": [{"type": "grammar|factual|tone|copyright|duplicate", "description": "..."}],
  "suggestions": ["..."],
  "revised_hook": "...",  // optional improved hook
  "approved_for_production": true | false
}"""


class ReviewAgent(BaseAgent):
    name = "review"
    department = "creative"

    async def _run(self, context: AgentContext, input_data: dict[str, Any]) -> dict[str, Any]:
        script = context.get("script", input_data.get("script", {}))
        brand = context.brand

        self._log.info("review.checking", title=script.get("title"))

        review = await self.llm_json([
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Brand name: {brand.get('name')}\n"
                    f"Brand tone: {brand.get('tone')}\n"
                    f"Avoid: {brand.get('avoid', [])}\n\n"
                    f"Script title: {script.get('title')}\n"
                    f"Hook: {script.get('hook')}\n"
                    f"Script:\n{script.get('script')}\n\n"
                    "Review this script and return the verdict JSON."
                ),
            },
        ])

        self._log.info(
            "review.complete",
            verdict=review.get("verdict"),
            score=review.get("score"),
        )
        context.set("review", review)
        return review
