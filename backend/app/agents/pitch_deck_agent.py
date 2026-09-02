"""
Pitch Deck Agent - Generates an investor/producer pitch deck from a script.
Uses Gemini AI for rich slides, with a structural heuristic fallback so the
feature always works without API access.
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional

from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


class PitchDeckAgent:
    """Generates a slide-based pitch deck from screenplay content."""

    def __init__(self):
        self.agent_type = "pitch_deck"

    async def process_task(self, task: AgentTask) -> AgentResult:
        start_time = time.time()
        try:
            script_text = task.task_data.get("script_text", "")
            if not script_text or len(script_text.strip()) < 20:
                raise ValueError("No script text provided for pitch deck")

            try:
                slides, title = await self._generate_with_gemini(script_text)
            except Exception as e:
                logger.warning(f"Gemini pitch deck unavailable, using heuristic: {e}")
                slides, title = self._heuristic_deck(script_text)

            result_data = {
                "title": title,
                "slides": slides,
                "slide_count": len(slides),
                "generation_method": "gemini_ai" if slides and slides[0].get("_ai") else "heuristic",
            }

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                confidence_score=0.78,
                processing_time=time.time() - start_time,
                data=result_data,
                metadata={"algorithm": "pitch_deck_generator"},
            )

        except Exception as e:
            logger.error(f"Pitch deck generation failed: {e}", exc_info=True)
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    async def _generate_with_gemini(self, script_text: str):
        from ..agent.gemini_client import get_gemini_client

        client = await get_gemini_client()
        system_prompt = """You are a Hollywood development executive. Read the screenplay and produce a concise
pitch deck for investors/producers.

Return ONLY a JSON object:
{
  "title": "<working title>",
  "slides": [
    {"title": "Logline", "bullets": ["..."]},
    {"title": "Synopsis", "bullets": ["..."]},
    {"title": "Genre & Tone", "bullets": ["..."]},
    {"title": "Key Characters", "bullets": ["NAME — one-line description", "..."]},
    {"title": "Themes", "bullets": ["..."]},
    {"title": "Visual Style", "bullets": ["..."]},
    {"title": "Target Audience", "bullets": ["..."]},
    {"title": "Comparable Films", "bullets": ["..."]},
    {"title": "Production Scale", "bullets": ["..."]},
    {"title": "Risks & Opportunities", "bullets": ["..."]}
  ]
}
Each bullet 3-12 words. 2-5 bullets per slide. Be specific to THIS script."""

        response = await client.generate_content(
            prompt=f"Create a pitch deck for this script:\n\n{script_text[:12000]}",
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=2500,
        )
        data = self._parse_json(response)
        slides = data.get("slides", [])
        for s in slides:
            s["_ai"] = True
        return slides, data.get("title", "Untitled Project")

    def _parse_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not m:
            raise ValueError("No JSON in pitch deck response")
        return json.loads(m.group(0))

    def _heuristic_deck(self, script_text: str):
        from ..services.scene_parser import parse_screenplay

        scenes, _ = parse_screenplay(script_text)
        all_chars: Dict[str, int] = {}
        int_n = ext_n = 0
        for s in scenes:
            for c in s.characters_present:
                all_chars[c.upper()] = all_chars.get(c.upper(), 0) + 1
            if str(s.time_of_day).upper().startswith("N"):
                pass
            loc = (s.location or "").upper()
            if "INT" in (s.title or "").upper() or "INT" in loc:
                int_n += 1
            elif "EXT" in (s.title or "").upper() or "EXT" in loc:
                ext_n += 1

        top_chars = sorted(all_chars.items(), key=lambda x: -x[1])[:6]
        # Guess genre from keywords
        low = script_text.lower()
        genre_hints = []
        if any(w in low for w in ["murder", "kill", "detective", "crime", "investigation"]):
            genre_hints.append("Crime / Thriller")
        if any(w in low for w in ["love", "kiss", "romance", "married", "wife", "husband"]):
            genre_hints.append("Romance")
        if any(w in low for w in ["war", "soldier", "battle", "army", "mission"]):
            genre_hints.append("War / Action")
        if any(w in low for w in ["spaceship", "alien", "future", "robot", "planet"]):
            genre_hints.append("Sci-Fi")
        if any(w in low for w in ["magic", "witch", "dragon", "kingdom", "curse"]):
            genre_hints.append("Fantasy")
        if not genre_hints:
            genre_hints.append("Drama")

        title_guess = "Untitled Project"
        m = re.search(r"(INT|EXT)[.\s]*([A-Z][A-Za-z0-9 ,.'-]+)", script_text)
        if m:
            title_guess = m.group(2).strip().title()[:40] or title_guess

        slides = [
            {
                "title": "Logline",
                "bullets": [
                    f"A {genre_hints[0].lower()} story across {len(scenes)} scenes.",
                    "Auto-generated draft — refine with AI for full logline.",
                ],
            },
            {
                "title": "Synopsis",
                "bullets": [
                    f"Script contains {len(scenes)} parsed scenes.",
                    f"{int_n} interior and {ext_n} exterior setups.",
                    "Paste a richer synopsis or enable AI for detail.",
                ],
            },
            {
                "title": "Genre & Tone",
                "bullets": genre_hints + ["Tone to be confirmed in development."],
            },
            {
                "title": "Key Characters",
                "bullets": [
                    f"{name.title()} — appears in {cnt} scene(s)" for name, cnt in top_chars
                ] or ["No named characters detected."],
            },
            {
                "title": "Themes",
                "bullets": ["Themes inferred during AI analysis.", "Run AI mode for specific themes."],
            },
            {
                "title": "Visual Style",
                "bullets": [
                    f"Mix of interior ({int_n}) and exterior ({ext_n}) locations.",
                    "Establish look via referenced films in script.",
                ],
            },
            {
                "title": "Target Audience",
                "bullets": ["Adults 18-45 (typical indie feature).", "Refine after genre lock."],
            },
            {
                "title": "Comparable Films",
                "bullets": ["Add comparables from similar releases.", "AI mode suggests titles."],
            },
            {
                "title": "Production Scale",
                "bullets": [
                    f"{len(scenes)} scenes, {len(all_chars)} characters.",
                    "See Budget Tracker tab for cost estimate.",
                ],
            },
            {
                "title": "Risks & Opportunities",
                "bullets": [
                    "See Risk Dashboard tab for legal/continuity flags.",
                    "Strong character depth is an opportunity.",
                ],
            },
        ]
        return slides, title_guess
