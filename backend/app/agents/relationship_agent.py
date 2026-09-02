"""
Character Relationship Agent
Analyzes parsed screenplay scenes and builds a character relationship graph:
nodes = characters, edges = co-occurrence in shared scenes with heuristic
relationship-type classification (family / romantic / rivalry / authority / ally / associate).
Deterministic, no external model dependency.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)


# Relationship type inference: keyword -> type, in priority order (first match wins)
RELATIONSHIP_KEYWORDS: List[Tuple[str, str]] = [
    ("family", ["brother", "sister", "father", "mother", "son", "daughter", "parent",
                "child", "uncle", "aunt", "cousin", "family", "grandfather", "grandmother", "twin"]),
    ("romantic", ["wife", "husband", "lover", "girlfriend", "boyfriend", "fiance", "fiancé",
                  "marry", "married", "kiss", "romance", "ex-wife", "ex-husband"]),
    ("rivalry", ["enemy", "rival", "opponent", "foe", "nemesis", "betray"]),
    ("authority", ["boss", "captain", "commander", "chief", "mentor", "teacher",
                   "sergeant", "general", "lieutenant", "supervisor", "drill"]),
    ("ally", ["friend", "ally", "partner", "colleague", "teammate", "comrade", "trusted"]),
]

DEFAULT_TYPE = "associate"

# Scenes a character must appear in to be considered a "primary" character
PRIMARY_MIN_SCENES = 3


class CharacterRelationshipAgent:
    """Builds a character relationship graph from screenplay scene data."""

    def __init__(self):
        self.agent_type = "relationship"

    async def process_task(self, task: AgentTask) -> AgentResult:
        start_time = time.time()
        try:
            scenes = task.task_data.get("scenes", [])
            if not scenes:
                raise ValueError("No scenes provided for relationship analysis")

            logger.info(f"Building relationship graph from {len(scenes)} scenes")

            nodes, edges = self._build_graph(scenes)

            if not nodes:
                raise ValueError("No characters found in script scenes")

            most_connected = max(
                nodes, key=lambda n: n["centrality"]
            )["name"] if nodes else ""

            scene_count_total = len(scenes)
            result_data = {
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "character_count": len(nodes),
                    "relationship_count": len(edges),
                    "scene_count": scene_count_total,
                    "most_connected": most_connected,
                    "primary_characters": [n["name"] for n in nodes if n["is_primary"]],
                },
                "analysis_method": "cooccurrence_heuristic",
            }

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                confidence_score=0.8,
                processing_time=time.time() - start_time,
                data=result_data,
                metadata={"algorithm": "scene_cooccurrence_graph"},
            )

        except Exception as e:
            logger.error(f"Relationship analysis failed: {e}", exc_info=True)
            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    # ── Graph construction ───────────────────────────────────────────────────

    def _build_graph(self, scenes: List[Dict[str, Any]]):
        """Build nodes and edges from scene co-occurrence."""
        cooccurrence: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "scenes": [], "text": []}
        )
        character_scenes: Dict[str, int] = defaultdict(int)
        all_characters: set = set()

        for scene in scenes:
            chars = [c.upper().strip() for c in scene.get("characters_present", []) if c]
            chars = list(dict.fromkeys(chars))  # dedupe, preserve order
            desc = (scene.get("description", "") or "").lower()
            scene_no = scene.get("scene_number", 0)

            for c in chars:
                all_characters.add(c)
                character_scenes[c] += 1

            # Pairwise co-occurrence
            for i in range(len(chars)):
                for j in range(i + 1, len(chars)):
                    a, b = chars[i], chars[j]
                    key = (a, b) if a < b else (b, a)
                    cooccurrence[key]["count"] += 1
                    cooccurrence[key]["scenes"].append(scene_no)
                    cooccurrence[key]["text"].append(desc)

        # Degree (sum of weights) per character for centrality
        degree: Dict[str, int] = defaultdict(int)
        for (a, b), info in cooccurrence.items():
            degree[a] += info["count"]
            degree[b] += info["count"]

        max_degree = max(degree.values()) if degree else 1

        # Build nodes
        nodes = []
        for name in sorted(all_characters):
            sc = character_scenes[name]
            centrality = round(degree.get(name, 0) / max_degree, 3) if max_degree else 0.0
            nodes.append({
                "id": name,
                "name": name,
                "scenes_count": sc,
                "is_primary": sc >= PRIMARY_MIN_SCENES,
                "centrality": centrality,
                "degree": degree.get(name, 0),
            })

        # Build edges
        edges = []
        for (a, b), info in cooccurrence.items():
            if info["count"] < 1:
                continue
            rel_type, label, confidence = self._classify_relationship(
                info["text"], info["count"]
            )
            edges.append({
                "source": a,
                "target": b,
                "weight": info["count"],
                "shared_scenes": sorted(info["scenes"]),
                "type": rel_type,
                "label": label,
                "confidence": confidence,
            })

        # Sort edges by weight desc for stable rendering
        edges.sort(key=lambda e: -e["weight"])
        return nodes, edges

    def _classify_relationship(
        self, scene_texts: List[str], shared_count: int
    ) -> Tuple[str, str, float]:
        """Infer relationship type from shared-scene descriptions."""
        combined = " ".join(scene_texts)
        rel_type = DEFAULT_TYPE
        for rtype, keywords in RELATIONSHIP_KEYWORDS:
            if any(kw in combined for kw in keywords):
                rel_type = rtype
                break

        label_map = {
            "family": "Family",
            "romantic": "Romantic",
            "rivalry": "Rivalry",
            "authority": "Authority",
            "ally": "Ally",
            "associate": "Associate",
        }
        label = label_map.get(rel_type, "Associate")

        # Confidence grows with shared scenes (more evidence = more confident)
        confidence = min(1.0, 0.4 + shared_count * 0.12)
        return rel_type, label, round(confidence, 2)
