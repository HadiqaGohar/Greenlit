"""
Storyboard Agent - Generates visual storyboard frames from script scenes
Uses Gemini for prompt engineering + Imagen 4 for image generation
"""

import asyncio
import base64
import io
import json
import logging
import re
import time
from typing import Dict, List, Any, Optional

from ..agent.gemini_client import get_gemini_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Max scenes to generate storyboard for
MAX_SCENES = 10
# Timeout per image generation in seconds
IMAGE_TIMEOUT = 60.0
# Delay between image generations to avoid rate limits
IMAGE_DELAY = 3.0
# Imagen model used for frame generation
IMAGEN_MODEL = "imagen-4.0-generate-001"


class StoryboardAgent:
    """
    Agent that generates visual storyboard frames from screenplay scenes.
    Phase 1: Gemini generates cinematic visual prompts per scene
    Phase 2: Imagen 4 generates actual images from prompts
    """

    def __init__(self):
        self.agent_type = "storyboard"

    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process storyboard generation task"""

        start_time = time.time()

        try:
            script_text = task.task_data.get("script_text", "")
            scenes = task.task_data.get("scenes", [])

            if not script_text:
                raise ValueError("No script text provided")

            # Get Gemini client for prompt generation
            gemini_client = await get_gemini_client()

            # Phase 1: Generate visual prompts for each scene
            logger.info("Phase 1: Generating visual prompts for scenes...")
            scene_prompts = await self._generate_visual_prompts(
                gemini_client, script_text, scenes
            )

            # Phase 2: Generate images using Imagen 4
            logger.info(f"Phase 2: Generating images for {len(scene_prompts)} scenes...")
            storyboard_frames = await self._generate_images(scene_prompts)

            # Build result data
            result_data = {
                "frames": storyboard_frames,
                "total_frames": len(storyboard_frames),
                "successful_frames": len([f for f in storyboard_frames if f.get("image_base64")]),
                "failed_frames": len([f for f in storyboard_frames if not f.get("image_base64")]),
                "generation_method": "gemini_prompt + imagen4",
                "model_used": "imagen-4.0-fast-generate-001"
            }

            processing_time = time.time() - start_time

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                data=result_data,
                confidence_score=0.85,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Storyboard agent processing failed: {str(e)}")
            processing_time = time.time() - start_time

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )

    async def _generate_visual_prompts(
        self,
        gemini_client,
        script_text: str,
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use Gemini to generate cinematic visual prompts for each scene"""

        # Limit scenes
        scenes_to_process = scenes[:MAX_SCENES]

        system_prompt = """You are a cinematic visual designer creating storyboard prompts for a film production AI tool.

For each scene provided, generate a detailed visual prompt that could be used with an AI image generator (like Imagen) to create a cinematic storyboard frame.

IMPORTANT RULES:
- Each prompt MUST be a single paragraph, max 200 words
- Focus on VISUAL elements: lighting, camera angle, composition, mood, colors
- Include character positions and actions
- Include environment/setting details
- Use cinematic language: "wide shot", "close-up", "overhead view", "dutch angle"
- Describe the MOOD: tense, romantic, dramatic, mysterious, etc.
- Do NOT include dialogue or text in the prompt
- Make prompts suitable for a 16:9 widescreen frame

Format as JSON array:
[
  {
    "scene_number": 1,
    "title": "scene title",
    "visual_prompt": "detailed cinematic prompt for image generation",
    "description": "brief 1-2 sentence summary of what this frame shows",
    "mood": "dramatic/tense/romantic/etc",
    "camera_angle": "wide/close-up/etc"
  }
]"""

        # Build scene data for prompt
        scene_list = []
        for i, scene in enumerate(scenes_to_process):
            scene_num = scene.get("scene_number", i + 1)
            title = scene.get("title", f"Scene {scene_num}")
            desc = scene.get("description", "")
            location = scene.get("location", "")
            time_of_day = scene.get("time_of_day", "DAY")
            characters = scene.get("characters_present", [])

            scene_list.append(
                f"Scene {scene_num}: {title}\n"
                f"Location: {location}\n"
                f"Time: {time_of_day}\n"
                f"Characters: {', '.join(characters) if characters else 'unknown'}\n"
                f"Description: {desc[:300]}"
            )

        scenes_text = "\n\n".join(scene_list)

        response = await gemini_client.generate_content(
            prompt=f"Generate cinematic storyboard prompts for these scenes:\n\n{scenes_text}",
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=4000
        )

        # Parse response
        prompts = self._parse_prompts_response(response)

        # If parsing fails, create basic prompts from scene data
        if not prompts:
            logger.warning("Failed to parse Gemini prompts, creating fallback prompts")
            prompts = self._create_fallback_prompts(scenes_to_process)

        return prompts

    def _parse_prompts_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Gemini response to extract visual prompts"""

        # Strip markdown code fences
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Extract JSON array
        json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)

        if not json_match:
            # Try to fix truncated JSON
            if cleaned.startswith('['):
                truncated = cleaned
                open_braces = truncated.count('{') - truncated.count('}')
                open_brackets = truncated.count('[') - truncated.count(']')
                truncated += '}' * open_braces + ']' * open_brackets
                last_complete = truncated.rfind('},')
                if last_complete > 0:
                    truncated = truncated[:last_complete + 1] + ']'
                    json_match = re.search(r'\[.*\]', truncated, re.DOTALL)

        if not json_match:
            logger.error("No JSON array found in prompts response")
            return []

        try:
            prompts = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return []

        # Validate and clean
        cleaned_prompts = []
        for p in prompts:
            if isinstance(p, dict) and "visual_prompt" in p:
                cleaned_prompts.append({
                    "scene_number": p.get("scene_number", len(cleaned_prompts) + 1),
                    "title": p.get("title", f"Scene {len(cleaned_prompts) + 1}"),
                    "visual_prompt": p["visual_prompt"][:500],
                    "description": p.get("description", "")[:200],
                    "mood": p.get("mood", "dramatic"),
                    "camera_angle": p.get("camera_angle", "wide shot")
                })

        return cleaned_prompts[:MAX_SCENES]

    def _create_fallback_prompts(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create basic visual prompts when Gemini parsing fails"""

        prompts = []
        for scene in scenes:
            scene_num = scene.get("scene_number", 1)
            title = scene.get("title", f"Scene {scene_num}")
            location = scene.get("location", "indoor setting")
            time_of_day = scene.get("time_of_day", "DAY")
            desc = scene.get("description", "")

            # Build a basic cinematic prompt
            lighting = "natural daylight" if time_of_day == "DAY" else "dramatic nighttime lighting with shadows"
            prompt_text = (
                f"Cinematic film storyboard frame, {location}, {lighting}, "
                f"wide angle shot, movie production quality, professional cinematography, "
                f"visually detailed, dramatic composition, 16:9 aspect ratio"
            )
            if desc:
                prompt_text += f", {desc[:100]}"

            prompts.append({
                "scene_number": scene_num,
                "title": title,
                "visual_prompt": prompt_text,
                "description": desc[:200] if desc else f"Scene at {location}",
                "mood": "dramatic",
                "camera_angle": "wide shot"
            })

        return prompts

    async def _generate_images(
        self,
        scene_prompts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate images using Imagen 4 API"""

        storyboard_frames = []

        for i, scene in enumerate(scene_prompts):
            scene_num = scene.get("scene_number", i + 1)
            visual_prompt = scene.get("visual_prompt", "")

            logger.info(f"Generating image for scene {scene_num}: {visual_prompt[:80]}...")

            frame = {
                "scene_number": scene_num,
                "title": scene.get("title", f"Scene {scene_num}"),
                "description": scene.get("description", ""),
                "mood": scene.get("mood", "dramatic"),
                "camera_angle": scene.get("camera_angle", "wide shot"),
                "visual_prompt": visual_prompt,
                "image_base64": None,
                "image_mime_type": "image/png",
                "generation_error": None
            }

            image_bytes = None
            try:
                image_bytes = await self._call_imagen(visual_prompt)
            except Exception as e:
                logger.warning(
                    f"Scene {scene_num}: Imagen unavailable ({str(e)[:120]}); "
                    f"using local placeholder frame"
                )

            if image_bytes:
                frame["image_base64"] = base64.b64encode(image_bytes).decode('utf-8')
                logger.info(f"Scene {scene_num}: Image generated successfully")
            else:
                placeholder = self._generate_placeholder_image(
                    scene.get("title", f"Scene {scene_num}"), visual_prompt
                )
                frame["image_base64"] = base64.b64encode(placeholder).decode('utf-8')
                frame["is_placeholder"] = True
                frame["generation_error"] = (
                    "Imagen API unavailable for this key — showing stylized placeholder"
                )

            storyboard_frames.append(frame)

            # Rate limit delay between images (except last)
            if i < len(scene_prompts) - 1:
                await asyncio.sleep(IMAGE_DELAY)

        return storyboard_frames

    async def _call_imagen(self, prompt: str) -> Optional[bytes]:
        """Call Imagen 4 API to generate an image"""

        from google import genai
        from google.genai import types
        from ..config import settings

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Enhance prompt for better results
        enhanced_prompt = (
            f"Cinematic film storyboard frame, {prompt}, "
            f"professional movie production quality, detailed visual storytelling, "
            f"dramatic lighting, 16:9 widescreen composition"
        )

        try:
            response = await client.aio.models.generate_images(
                model=IMAGEN_MODEL,
                prompt=enhanced_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                )
            )

            if response.generated_images:
                return response.generated_images[0].image.image_bytes
            return None

        except Exception as e:
            logger.error(f"Imagen API call failed: {str(e)}")
            raise

    def _generate_placeholder_image(self, title: str, prompt: str) -> bytes:
        """Render a stylized cinematic placeholder frame locally (no external API).

        Used when Imagen is unavailable (e.g., API not enabled for the key) so the
        Storyboard tab still shows coherent, on-theme frames instead of failing.
        """
        from PIL import Image, ImageDraw, ImageFont

        W, H = 1024, 576
        img = Image.new("RGB", (W, H), (24, 24, 27))
        draw = ImageDraw.Draw(img)

        # Subtle vertical gradient (charcoal -> slightly lighter)
        for y in range(H):
            t = y / H
            draw.line(
                [(0, y), (W, y)],
                fill=(int(24 + 36 * t), int(24 + 21 * t), int(27 + 8 * t)),
            )

        # Film-strip border (amber) + accent line
        draw.rectangle([16, 16, W - 16, H - 16], outline=(250, 204, 21), width=3)
        draw.rectangle([0, H // 2 - 2, W, H // 2 + 2], fill=(217, 119, 6))

        try:
            font_big = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22
            )
        except Exception:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.text((W // 2, 110), "STORYBOARD", font=font_big,
                  fill=(245, 158, 11), anchor="mm")
        draw.text((W // 2, 168), (title or "Scene")[:44], font=font_small,
                  fill=(255, 255, 255), anchor="mm")

        # Word-wrap the visual prompt
        words = (prompt or "").split()
        lines, cur = [], ""
        for w in words:
            if len(cur) + len(w) + 1 <= 62:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        y = 250
        for ln in lines[:5]:
            draw.text((W // 2, y), ln, font=font_small,
                      fill=(203, 203, 203), anchor="mm")
            y += 32

        draw.text(
            (W // 2, H - 56),
            "Placeholder frame — enable Imagen for AI-rendered visuals",
            font=font_small, fill=(148, 148, 148), anchor="mm",
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


# Async function for on-demand storyboard generation (called by router)
async def generate_storyboard(
    script_text: str,
    scenes: List[Dict[str, Any]],
    scene_numbers: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Generate storyboard for specified scenes.
    Called by the storyboard router for on-demand generation.
    """
    agent = StoryboardAgent()

    # Filter scenes if specific numbers requested
    if scene_numbers:
        scenes = [s for s in scenes if s.get("scene_number") in scene_numbers]

    # Create a mock task
    task = AgentTask(
        agent_type="storyboard",
        task_data={
            "script_text": script_text,
            "scenes": scenes,
            "focus": "storyboard_generation"
        }
    )

    result = await agent.process_task(task)

    return {
        "success": result.success,
        "frames": result.data.get("frames", []) if result.data else [],
        "total_frames": result.data.get("total_frames", 0) if result.data else 0,
        "processing_time": result.processing_time,
        "error": result.error_message if not result.success else None
    }
