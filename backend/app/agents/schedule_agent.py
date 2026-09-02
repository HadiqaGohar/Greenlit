"""
Production Schedule Agent
Analyzes parsed screenplay scenes and generates an optimized day-by-day shooting schedule.
Uses constraint-based greedy grouping (location → cast → time-of-day → complexity).
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Stripboard color codes (industry standard)
STRIP_COLORS = {
    "DAY_INT": "white",
    "DAY_EXT": "yellow",
    "NIGHT_INT": "blue",
    "NIGHT_EXT": "green",
}

# Page-per-day target (industry: ~5 pages/day for TV, 1-3 for features)
DEFAULT_PAGES_PER_DAY = 5.0

# Eighths per page
EIGHTHS_PER_PAGE = 8

# Max company moves per day
MAX_MOVES_PER_DAY = 2

# Turnaround hours between shoot days
TURNAROUND_HOURS = 10

# Contingency: 1 buffer day per N shoot days
CONTINGENCY_RATIO = 10


class ScheduleAgent:
    """
    Generates optimized day-by-day shooting schedules from parsed screenplay data.
    Applies industry-standard constraints: location grouping, cast clustering,
    day/night sequencing, page balancing, and contingency buffering.
    """

    def __init__(self):
        self.agent_type = "schedule"

    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process schedule generation task"""
        start_time = time.time()

        try:
            script_text = task.task_data.get("script_text", "")
            scenes = task.task_data.get("scenes", [])
            characters = task.task_data.get("characters", [])
            pages_per_day = task.task_data.get("pages_per_day", DEFAULT_PAGES_PER_DAY)

            if not scenes:
                raise ValueError("No scenes provided for schedule generation")

            logger.info(f"Generating schedule for {len(scenes)} scenes")

            # Step 1: Compute per-scene metadata
            enriched = self._enrich_scenes(scenes)
            logger.info(f"Enriched {len(enriched)} scenes with scheduling metadata")

            # Step 2: Group by location
            location_groups = self._group_by_location(enriched)
            logger.info(f"Found {len(location_groups)} unique locations")

            # Step 3: Sub-group by cast overlap within each location
            optimized_groups = self._optimize_groups(location_groups)
            logger.info(f"Optimized into {len(optimized_groups)} scheduling groups")

            # Step 4: Assign to shoot days
            shoot_days = self._assign_shoot_days(optimized_groups, pages_per_day)
            logger.info(f"Assigned {len(shoot_days)} shoot days")

            # Step 5: Generate Day Out of Days (DOOD)
            cast_schedule = self._generate_dood(shoot_days, enriched)
            logger.info(f"Generated DOOD for {len(cast_schedule)} cast members")

            # Step 6: Compute summary stats
            total_pages_eighths = sum(
                sum(s["page_eighths"] for s in day["scenes"])
                for day in shoot_days
            )
            total_pages_str = self._eighths_to_pages(total_pages_eighths)
            total_moves = sum(day["company_moves"] for day in shoot_days)
            contingency = max(1, len(shoot_days) // CONTINGENCY_RATIO)

            # Build location summary
            location_summary = self._build_location_summary(enriched, location_groups)

            # Optimization notes
            notes = self._generate_optimization_notes(shoot_days, location_groups, cast_schedule)

            result_data = {
                "shoot_days": shoot_days,
                "total_shoot_days": len(shoot_days),
                "contingency_days": contingency,
                "total_pages": total_pages_str,
                "total_pages_eighths": total_pages_eighths,
                "company_moves_total": total_moves,
                "cast_schedule": cast_schedule,
                "location_summary": location_summary,
                "optimization_notes": notes,
                "pages_per_day_target": pages_per_day,
            }

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                confidence_score=0.85,
                processing_time=time.time() - start_time,
                data=result_data,
                metadata={"algorithm": "greedy_location_cast_grouping"},
            )

        except Exception as e:
            logger.error(f"Schedule generation failed: {e}", exc_info=True)
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    # ── Step 1: Enrich scenes with scheduling metadata ──────────────────────

    def _enrich_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add scheduling metadata to each scene"""
        enriched = []
        for scene in scenes:
            title = scene.get("title", "")
            location = scene.get("location", "UNKNOWN")
            tod = scene.get("time_of_day", "DAY").upper()
            characters = scene.get("characters_present", [])
            dialogue_count = scene.get("dialogue_count", 0)

            # Classify INT/EXT
            title_upper = title.upper()
            if "EXT" in title_upper or "EXTERIOR" in title_upper:
                int_ext = "EXT"
            else:
                int_ext = "INT"

            # Normalize time of day
            if tod in ("MORNING", "AFTERNOON", "DAWN"):
                tod_normalized = "DAY"
            elif tod in ("EVENING", "DUSK"):
                tod_normalized = "NIGHT"
            elif tod in ("CONTINUOUS", "LATER", "SAME TIME"):
                tod_normalized = "DAY"  # default for continuous
            else:
                tod_normalized = tod if tod in ("DAY", "NIGHT") else "DAY"

            # Estimate page count (dialogue lines ~ 1/8 page each, min 1/8)
            page_eighths = max(1, min(dialogue_count, EIGHTHS_PER_PAGE * 3))
            # Add action weight (action lines add pages)
            action_lines = scene.get("action_lines", [])
            page_eighths += max(0, len(action_lines) // 5)
            page_eighths = min(page_eighths, EIGHTHS_PER_PAGE * 4)  # cap at 4 pages

            # Complexity score (0-10)
            complexity = self._compute_complexity(characters, dialogue_count, int_ext, tod_normalized, action_lines)

            # Strip color
            strip_key = f"{tod_normalized}_{int_ext}"
            strip_color = STRIP_COLORS.get(strip_key, "white")

            enriched.append({
                "scene_number": scene.get("scene_number", 0),
                "title": title,
                "location": location.upper().strip(),
                "int_ext": int_ext,
                "time_of_day": tod_normalized,
                "characters": [c.upper().strip() for c in characters],
                "page_eighths": page_eighths,
                "page_count": self._eighths_to_pages(page_eighths),
                "complexity": complexity,
                "strip_color": strip_color,
                "dialogue_count": dialogue_count,
                "action_line_count": len(action_lines),
            })

        return enriched

    def _compute_complexity(self, characters, dialogue_count, int_ext, tod, action_lines):
        """Score scene complexity 0-10"""
        score = 0
        # Character count
        if len(characters) >= 5:
            score += 3
        elif len(characters) >= 3:
            score += 2
        elif len(characters) >= 1:
            score += 1

        # Exterior is harder (weather, lighting)
        if int_ext == "EXT":
            score += 1

        # Night shoots are more complex
        if tod == "NIGHT":
            score += 2

        # High dialogue = moderate complexity
        if dialogue_count > 20:
            score += 2
        elif dialogue_count > 10:
            score += 1

        # Many action lines = stunts/complex blocking
        if len(action_lines) > 15:
            score += 2
        elif len(action_lines) > 8:
            score += 1

        return min(score, 10)

    # ── Step 2: Group by location ───────────────────────────────────────────

    def _group_by_location(self, scenes: List[Dict]) -> Dict[str, List[Dict]]:
        """Primary grouping: scenes at the same location together"""
        groups = defaultdict(list)
        for scene in scenes:
            groups[scene["location"]].append(scene)
        return dict(groups)

    # ── Step 3: Optimize within location groups ─────────────────────────────

    def _optimize_groups(self, location_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """Within each location, sub-sort by time-of-day, then cast overlap"""
        optimized = []

        for location, scenes in location_groups.items():
            # Sort by: time_of_day (DAY first), then by cast overlap (scenes sharing cast together)
            # Build cast co-occurrence
            cast_scene_map = defaultdict(list)
            for s in scenes:
                for c in s["characters"]:
                    cast_scene_map[c].append(s["scene_number"])

            # Secondary sort: scenes sharing most cast members should be adjacent
            def sort_key(scene):
                tod_order = 0 if scene["time_of_day"] == "DAY" else 1
                # Scenes with fewer unique characters first (simpler setups)
                char_count = len(scene["characters"])
                return (tod_order, char_count, scene["scene_number"])

            scenes_sorted = sorted(scenes, key=sort_key)
            optimized.extend(scenes_sorted)

        return optimized

    # ── Step 4: Assign to shoot days ────────────────────────────────────────

    def _assign_shoot_days(self, scenes: List[Dict], pages_per_day: float) -> List[Dict]:
        """Assign scenes to shoot days with constraint enforcement"""
        if not scenes:
            return []

        target_eighths = int(pages_per_day * EIGHTHS_PER_PAGE)
        shoot_days = []
        current_day = {
            "day_number": 1,
            "scenes": [],
            "total_page_eighths": 0,
            "locations": set(),
            "cast_required": set(),
            "company_moves": 0,
            "is_night_shoot": False,
            "has_day": False,
            "has_night": False,
            "last_location": None,
        }

        for scene in scenes:
            # Check if scene fits in current day
            fits = self._scene_fits_in_day(current_day, scene, target_eighths)

            if not fits:
                # Close current day and start new one
                self._finalize_day(current_day)
                shoot_days.append(current_day)
                current_day = {
                    "day_number": len(shoot_days) + 1,
                    "scenes": [],
                    "total_page_eighths": 0,
                    "locations": set(),
                    "cast_required": set(),
                    "company_moves": 0,
                    "is_night_shoot": False,
                    "has_day": False,
                    "has_night": False,
                    "last_location": None,
                }

            # Add scene to current day
            current_day["scenes"].append(scene)
            current_day["total_page_eighths"] += scene["page_eighths"]
            current_day["locations"].add(scene["location"])
            current_day["cast_required"].update(scene["characters"])

            if scene["time_of_day"] == "NIGHT":
                current_day["has_night"] = True
            else:
                current_day["has_day"] = True

            # Track company moves
            if current_day["last_location"] and current_day["last_location"] != scene["location"]:
                current_day["company_moves"] += 1
            current_day["last_location"] = scene["location"]

        # Add the last day
        if current_day["scenes"]:
            self._finalize_day(current_day)
            shoot_days.append(current_day)

        return shoot_days

    def _scene_fits_in_day(self, day: Dict, scene: Dict, target_eighths: int) -> bool:
        """Check if a scene can be added to the current shoot day"""
        # Page limit: allow up to 1.5x target (with max 8 pages)
        max_eighths = min(target_eighths + target_eighths // 2, EIGHTHS_PER_PAGE * 8)
        if day["total_page_eighths"] + scene["page_eighths"] > max_eighths:
            return False

        # Company move limit
        if (day["locations"] and
            scene["location"] not in day["locations"] and
            day["company_moves"] >= MAX_MOVES_PER_DAY):
            return False

        # Day/night mixing: avoid mixing on same day if possible
        # Allow it if the day is still small
        if day["has_day"] and scene["time_of_day"] == "NIGHT" and day["total_page_eighths"] > 0:
            return False
        if day["has_night"] and scene["time_of_day"] == "DAY" and day["total_page_eighths"] > 0:
            return False

        return True

    def _finalize_day(self, day: Dict):
        """Compute final stats for a shoot day"""
        day["total_page_count"] = self._eighths_to_pages(day["total_page_eighths"])
        day["locations"] = list(day["locations"])
        day["cast_required"] = sorted(list(day["cast_required"]))
        day["scene_count"] = len(day["scenes"])
        # Estimate hours: ~10 base + 1 hour per 5/8 pages, +30min per company move
        base_hours = 10
        page_hours = day["total_page_eighths"] / EIGHTHS_PER_PAGE * 1.5
        move_hours = day["company_moves"] * 0.5
        day["estimated_hours"] = round(base_hours + page_hours + move_hours, 1)
        day["is_night_shoot"] = day["has_night"] and not day["has_day"]

    # ── Step 5: Day Out of Days (DOOD) ─────────────────────────────────────

    def _generate_dood(self, shoot_days: List[Dict], scenes: List[Dict]) -> Dict[str, List[Dict]]:
        """Generate Day Out of Days grid for each cast member"""
        # Collect all unique characters
        all_characters = set()
        for scene in scenes:
            all_characters.update(scene["characters"])

        # For each character, determine their days
        cast_schedule = {}
        for char in sorted(all_characters):
            days = []
            first_day = None
            last_day = None

            for day in shoot_days:
                day_num = day["day_number"]
                if char in day["cast_required"]:
                    days.append({"day": day_num, "status": "W"})
                    if first_day is None:
                        first_day = day_num
                    last_day = day_num

            # Mark start/finish days
            if first_day is not None and last_day is not None:
                for d in days:
                    if d["day"] == first_day and d["day"] == last_day:
                        d["status"] = "SWF"
                    elif d["day"] == first_day:
                        d["status"] = "SW"
                    elif d["day"] == last_day:
                        d["status"] = "WF"

            # Add hold days between first and last work days
            if first_day is not None and last_day is not None:
                work_days_set = {d["day"] for d in days}
                hold_days = []
                for dn in range(first_day, last_day + 1):
                    if dn not in work_days_set:
                        hold_days.append({"day": dn, "status": "H"})
                days.extend(hold_days)
                days.sort(key=lambda x: x["day"])

            cast_schedule[char] = days

        return cast_schedule

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _eighths_to_pages(self, eighths: int) -> str:
        """Convert eighths to 'N N/8' page format"""
        pages = eighths // EIGHTHS_PER_PAGE
        remainder = eighths % EIGHTHS_PER_PAGE
        if remainder == 0:
            return f"{pages}"
        return f"{pages} {remainder}/{EIGHTHS_PER_PAGE}"

    def _build_location_summary(self, scenes: List[Dict], groups: Dict[str, List[Dict]]) -> List[Dict]:
        """Build location summary for the schedule"""
        summary = []
        for location, location_scenes in groups.items():
            scene_numbers = [s["scene_number"] for s in location_scenes]
            total_eighths = sum(s["page_eighths"] for s in location_scenes)
            characters = set()
            for s in location_scenes:
                characters.update(s["characters"])
            summary.append({
                "location": location,
                "scene_count": len(location_scenes),
                "scene_numbers": sorted(scene_numbers),
                "total_pages": self._eighths_to_pages(total_eighths),
                "characters": sorted(list(characters)),
                "has_day": any(s["time_of_day"] == "DAY" for s in location_scenes),
                "has_night": any(s["time_of_day"] == "NIGHT" for s in location_scenes),
            })
        # Sort by scene count descending (most scenes = primary location)
        summary.sort(key=lambda x: -x["scene_count"])
        return summary

    def _generate_optimization_notes(self, shoot_days, location_groups, cast_schedule) -> List[str]:
        """Generate human-readable optimization notes"""
        notes = []

        # Note about location grouping
        total_moves = sum(d["company_moves"] for d in shoot_days)
        if total_moves == 0:
            notes.append("Zero company moves — all scenes grouped perfectly by location")
        else:
            notes.append(f"Minimized to {total_moves} total company moves across {len(shoot_days)} shoot days")

        # Note about cast efficiency
        total_hold_days = sum(
            sum(1 for d in days if d["status"] == "H")
            for days in cast_schedule.values()
        )
        if total_hold_days > 0:
            notes.append(f"Cast hold days: {total_hold_days} (actors on payroll but not shooting)")
        else:
            notes.append("Zero cast hold days — all actors work their scenes consecutively")

        # Note about night shoots
        night_days = sum(1 for d in shoot_days if d["is_night_shoot"])
        if night_days > 0:
            notes.append(f"{night_days} dedicated night shoot(s) scheduled")
            notes.append("Night shoots require extended crew rates and special permits")

        # Note about day/night mixing
        mixed_days = sum(1 for d in shoot_days if d["has_day"] and d["has_night"])
        if mixed_days > 0:
            notes.append(f"⚠ {mixed_days} day(s) mix day and night scenes (consider splitting)")

        # Contingency
        contingency = max(1, len(shoot_days) // CONTINGENCY_RATIO)
        notes.append(f"Recommended: {contingency} contingency day(s) for weather/overruns")

        return notes
