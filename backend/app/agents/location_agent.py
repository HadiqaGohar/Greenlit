"""
Scene-to-Location Matching Agent - Suggests real-world filming locations per scene.

Uses Gemini to propose concrete real locations (city + venue) matching each
scene's descriptor, plus permit requirements, estimated cost, and travel notes.
Falls back to a keyword heuristic when Gemini is unavailable. No Google Maps API
key is required — frontend links to maps search URLs.
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional

from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


class LocationMatchAgent:
    """Matches script scenes to real-world filming locations."""

    def __init__(self):
        self.agent_type = "location"

    async def process_task(self, task: AgentTask) -> AgentResult:
        start_time = time.time()
        try:
            script_text = task.task_data.get("script_text", "")
            scenes_in = task.task_data.get("scenes", [])
            if not script_text and not scenes_in:
                raise ValueError("No script text provided for location matching")

            from ..services.scene_parser import parse_screenplay
            if scenes_in:
                scenes = scenes_in
            else:
                parsed, _ = parse_screenplay(script_text)
                scenes = [
                    {
                        "scene_number": s.scene_number,
                        "title": s.title,
                        "location": s.location,
                        "time_of_day": s.time_of_day,
                        "characters_present": s.characters_present,
                    }
                    for s in parsed
                ]

            try:
                matches = await self._match_with_gemini(scenes)
            except Exception as e:
                logger.warning(f"Gemini location match unavailable, using heuristic: {e}")
                matches = self._heuristic_match(scenes)

            result_data = {
                "matches": matches,
                "match_count": len(matches),
                "generation_method": "gemini_ai" if matches and matches[0].get("_ai") else "heuristic",
            }

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                confidence_score=0.72,
                processing_time=time.time() - start_time,
                data=result_data,
                metadata={"algorithm": "scene_location_matcher"},
            )

        except Exception as e:
            logger.error(f"Location matching failed: {e}", exc_info=True)
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    async def _match_with_gemini(self, scenes: List[Dict]) -> List[Dict]:
        from ..agent.gemini_client import get_gemini_client

        client = await get_gemini_client()
        scene_list = [
            {
                "index": i,
                "location": s.get("location", ""),
                "time_of_day": s.get("time_of_day", ""),
                "title": s.get("title", ""),
            }
            for i, s in enumerate(scenes)
        ]
        system_prompt = """You are a location scout. For each script scene, suggest a REAL-WORLD filming
location (a real city + venue type) that fits the scene's setting.

Return ONLY a JSON array (one object per scene, keyed by "index"):
[
  {
    "index": 0,
    "matched_location": "<Real venue / area name or type>",
    "city": "<Real city>",
    "venue_type": "<Short category>",
    "permit_required": true/false,
    "est_cost_usd": 0,
    "travel_note": "<short note>",
    "rationale": "<why this fits>"
  }
]
Keep bullets 2-10 words. Use well-known, plausible real locations."""

        response = await client.generate_content(
            prompt=f"Scenes:\n{json.dumps(scene_list)}",
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=2500,
        )
        out = self._parse_json_array(response)
        for m in out:
            m["_ai"] = True
        return out

    def _parse_json_array(self, text: str) -> List[Dict]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        m = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not m:
            raise ValueError("No JSON array in location response")
        return json.loads(m.group(0))

    def _heuristic_match(self, scenes: List[Dict]) -> List[Dict]:
        rules = [
            ("CAFE|RESTAURANT|BAR|DINER|PUB", "Cafe / Restaurant", ["Los Angeles", "New York", "Paris"], 3500, True),
            ("OFFICE|CORPORATE|BOARDROOM|COWORK", "Corporate Office", ["New York", "Chicago", "London"], 8000, True),
            ("BEACH|OCEAN|SEA|COAST|SHORE", "Beach / Coastal", ["Malibu", "Honolulu", "Barcelona"], 12000, True),
            ("PARK|FOREST|GARDEN|WOODS|MEADOW", "Park / Outdoor", ["Portland", "Vancouver", "Kyoto"], 4000, True),
            ("HOTEL|LOBBY|SUITE|RESORT", "Hotel", ["Las Vegas", "Dubai", "Singapore"], 9000, False),
            ("HOSPITAL|CLINIC|WARD|MEDICAL", "Medical Facility", ["Toronto", "Boston", "Berlin"], 6000, True),
            ("SCHOOL|UNIVERSITY|CLASSROOM|CAMPUS", "Educational", ["Boston", "Oxford", "Tokyo"], 5000, True),
            ("STREET|ROAD|ALLEY|AVENUE|BOULEVARD", "Urban Street", ["New York", "Hong Kong", "London"], 7000, True),
            ("HOME|HOUSE|APARTMENT|LIVING|KITCHEN|BEDROOM", "Residential", ["Los Angeles", "Austin", "Toronto"], 3000, False),
            ("MUSEUM|GALLERY|THEATRE|THEATER", "Museum / Gallery", ["Paris", "New York", "Rome"], 7500, True),
            ("AIRPORT|STATION|TERMINAL|TRAIN", "Transit Hub", ["Tokyo", "Singapore", "Dubai"], 10000, True),
            ("CHURCH|TEMPLE|MOSQUE|SYNAGOGUE|SHRINE", "Place of Worship", ["Rome", "Istanbul", "Kyoto"], 4500, True),
            ("CLUB|NIGHT|LOUNGE|CONCERT", "Nightclub / Venue", ["Berlin", "Ibiza", "Las Vegas"], 6500, True),
            ("LAB|LABORATORY|SCIENCE|RESEARCH", "Laboratory", ["Boston", "Zurich", "Seoul"], 8500, True),
            ("CASTLE|PALACE|FORT|RUINS", "Historic Site", ["Edinburgh", "Prague", "Jaipur"], 15000, True),
            ("MOUNTAIN|CLIFF|CAVE|DESERT|CLIFFS", "Wilderness", ["Banff", "Queenstown", "Moab"], 9000, True),
        ]
        out = []
        for i, s in enumerate(scenes):
            loc = (s.get("location", "") or s.get("title", "") or "").upper()
            is_ext = "EXT" in (s.get("title", "") or "").upper() or "EXT" in loc
            chosen = None
            for pat, vtype, cities, cost, permit in rules:
                if re.search(pat, loc):
                    chosen = (vtype, cities, cost, permit)
                    break
            if not chosen:
                chosen = ("Generic Location", ["Los Angeles", "New York"], 5000, is_ext)
            vtype, cities, cost, permit = chosen
            city = cities[i % len(cities)]
            out.append({
                "index": i,
                "matched_location": f"{vtype} - {city}",
                "city": city,
                "venue_type": vtype,
                "permit_required": bool(permit or is_ext),
                "est_cost_usd": cost,
                "travel_note": (f"Scout {city} permitting office; estimate {cost:,} USD day-rate."
                                if (permit or is_ext) else "Private location; minimal permit overhead."),
                "rationale": f"Heuristic match for '{s.get('location','') or s.get('title','')}'.",
            })
        return out
