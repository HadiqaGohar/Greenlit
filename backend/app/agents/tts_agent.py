"""
TTS Agent - Generates multi-speaker audio read-throughs of scripts
Uses Gemini TTS API with voice assignment for different characters
"""

import asyncio
import base64
import json
import logging
import re
import time
import wave
from io import BytesIO
from typing import Dict, List, Any, Optional

from ..agent.gemini_client import get_gemini_client
from ..models.agent_schemas import AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Max scenes to generate TTS for
MAX_SCENES = 8
# Timeout per scene in seconds
SCENE_TIMEOUT = 120.0
# Delay between scene generations
SCENE_DELAY = 5.0
# Gemini TTS model (native audio generation via generate_content)
TTS_MODEL = "gemini-2.5-flash-preview-tts"

# Voice assignments for characters
MALE_VOICES = ["Puck", "Fenrir", "Orus", "Enceladus", "Iapetus", "Umbriel", "Algieba"]
FEMALE_VOICES = ["Kore", "Zephyr", "Leda", "Aoede", "Callirrhoe", "Autonoe", "Despina"]
NARRATOR_VOICE = "Charon"  # Informative male voice for narration

# Mapping of character gender heuristics
MALE_INDICATORS = ["he", "him", "his", "man", "mr", "sir", "boy", "father", "dad", "brother", "son"]
FEMALE_INDICATORS = ["she", "her", "hers", "woman", "mrs", "ms", "miss", "girl", "mother", "mom", "sister", "daughter"]


class TTSAgent:
    """
    Agent that generates multi-speaker audio read-throughs of screenplays.
    Parses dialogue, assigns voices, and calls Gemini TTS API.
    """

    def __init__(self):
        self.agent_type = "tts"

    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process TTS generation task"""

        start_time = time.time()

        try:
            script_text = task.task_data.get("script_text", "")
            scenes = task.task_data.get("scenes", [])

            if not script_text:
                raise ValueError("No script text provided")

            # Step 1: Parse dialogue per scene
            logger.info("Step 1: Parsing dialogue from script...")
            scene_dialogues = self._parse_dialogue_per_scene(script_text, scenes)

            if not scene_dialogues:
                raise ValueError("No dialogue found in script")

            # Step 2: Assign voices to characters
            logger.info("Step 2: Assigning voices to characters...")
            voice_map = self._assign_voices(scene_dialogues)

            # Step 3: Generate audio per scene using Gemini TTS
            logger.info(f"Step 3: Generating audio for {len(scene_dialogues)} scenes...")
            audio_results = await self._generate_audio_for_scenes(scene_dialogues, voice_map)

            # Build result data
            successful = [r for r in audio_results if r.get("audio_base64")]
            result_data = {
                "scenes": audio_results,
                "total_scenes": len(audio_results),
                "successful_scenes": len(successful),
                "failed_scenes": len(audio_results) - len(successful),
                "voice_map": voice_map,
                "total_duration_seconds": sum(r.get("duration_seconds", 0) for r in successful),
                "generation_method": "gemini_tts",
                "model_used": TTS_MODEL
            }

            processing_time = time.time() - start_time

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=True,
                data=result_data,
                confidence_score=0.9,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"TTS agent processing failed: {str(e)}")
            processing_time = time.time() - start_time

            return AgentResult(
                agent_type=self.agent_type,
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                processing_time=processing_time
            )

    def _parse_dialogue_per_scene(
        self,
        script_text: str,
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse script to extract dialogue lines per scene"""

        scene_dialogues = []
        lines = script_text.split('\n')

        # Build scene boundaries
        scene_starts = []
        for i, line in enumerate(lines):
            line_upper = line.strip().upper()
            if re.match(r'^(INT\.|EXT\.|INTERIOR|EXTERIOR)', line_upper):
                scene_starts.append(i)

        if not scene_starts:
            # No scene headers found — treat whole script as one scene
            scene_starts = [0]

        # Process each scene
        for scene_idx, start_line in enumerate(scene_starts):
            end_line = scene_starts[scene_idx + 1] if scene_idx + 1 < len(scene_starts) else len(lines)
            scene_lines = lines[start_line:end_line]

            # Get scene title from header
            scene_title = scene_lines[0].strip() if scene_lines else f"Scene {scene_idx + 1}"

            # Extract dialogue from this scene
            dialogue_lines = []
            current_character = None
            scene_characters = set()

            for line in scene_lines:
                line_clean = line.strip()
                if not line_clean:
                    continue

                # Check if it's a character name (ALL CAPS, alone on line)
                if self._is_character_name(line_clean):
                    current_character = line_clean
                    scene_characters.add(line_clean)
                elif current_character:
                    # This is dialogue after a character name
                    # Skip parentheticals
                    if re.match(r'^\s*\([^)]+\)\s*$', line_clean):
                        continue
                    dialogue_lines.append({
                        'speaker': current_character,
                        'text': line_clean,
                        'type': 'dialogue'
                    })
                    current_character = None
                elif self._is_action_line(line_clean) and len(line_clean) > 15:
                    # Action/narration line
                    dialogue_lines.append({
                        'speaker': 'NARRATOR',
                        'text': line_clean,
                        'type': 'action'
                    })

            if dialogue_lines:
                scene_dialogues.append({
                    'scene_number': scene_idx + 1,
                    'title': scene_title,
                    'characters': list(scene_characters),
                    'dialogue': dialogue_lines
                })

        # Limit to MAX_SCENES
        return scene_dialogues[:MAX_SCENES]

    def _is_character_name(self, line: str) -> bool:
        """Check if a line is a character name (ALL CAPS, alone on line)"""
        # Character names: ALL CAPS, 2-30 chars, not a scene header, not a transition
        if not re.match(r'^[A-Z][A-Z\s\.]+[A-Z]?$', line):
            return False
        if len(line) < 2 or len(line) > 30:
            return False
        # Exclude common non-character words
        excluded = {'THE', 'AND', 'BUT', 'FOR', 'WITH', 'FROM', 'INT', 'EXT',
                     'DAY', 'NIGHT', 'FADE', 'CUT', 'DISSOLVE', 'CONTINUED'}
        if line in excluded:
            return False
        return True

    def _is_action_line(self, line: str) -> bool:
        """Check if a line is an action/description line"""
        if not line[0].isupper():
            return False
        if re.match(r'^(INT\.|EXT\.|FADE|CUT)', line):
            return False
        return len(line) > 15

    def _assign_voices(self, scene_dialogues: List[Dict[str, Any]]) -> Dict[str, str]:
        """Assign TTS voices to characters based on dialogue analysis"""

        # Collect all characters and their dialogue context
        character_contexts = {}
        for scene in scene_dialogues:
            for line in scene['dialogue']:
                if line['type'] == 'dialogue':
                    speaker = line['speaker']
                    if speaker not in character_contexts:
                        character_contexts[speaker] = []
                    character_contexts[speaker].append(line['text'].lower())

        # Determine gender for each character
        voice_map = {}
        male_idx = 0
        female_idx = 0

        for speaker, texts in character_contexts.items():
            all_text = ' '.join(texts)

            # Check for gender indicators
            is_male = any(ind in all_text for ind in MALE_INDICATORS)
            is_female = any(ind in all_text for ind in FEMALE_INDICATORS)

            # Default: alternate between male and female
            if is_female and not is_male:
                voice = FEMALE_VOICES[female_idx % len(FEMALE_VOICES)]
                female_idx += 1
            elif is_male and not is_female:
                voice = MALE_VOICES[male_idx % len(MALE_VOICES)]
                male_idx += 1
            else:
                # Ambiguous — alternate
                if (male_idx + female_idx) % 2 == 0:
                    voice = MALE_VOICES[male_idx % len(MALE_VOICES)]
                    male_idx += 1
                else:
                    voice = FEMALE_VOICES[female_idx % len(FEMALE_VOICES)]
                    female_idx += 1

            voice_map[speaker] = voice

        # Always assign narrator
        voice_map['NARRATOR'] = NARRATOR_VOICE

        return voice_map

    async def _generate_audio_for_scenes(
        self,
        scene_dialogues: List[Dict[str, Any]],
        voice_map: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Generate audio for each scene using Gemini TTS"""

        audio_results = []

        for scene in scene_dialogues:
            scene_num = scene['scene_number']
            title = scene['title']
            dialogue = scene['dialogue']

            logger.info(f"Generating audio for scene {scene_num}: {title}")

            result = {
                "scene_number": scene_num,
                "title": title,
                "characters": scene['characters'],
                "audio_base64": None,
                "audio_format": "wav",
                "duration_seconds": 0,
                "generation_error": None
            }

            try:
                # Get unique speakers in this scene
                scene_speakers = list(set(line['speaker'] for line in dialogue))

                # Gemini TTS multi-speaker requires exactly 2 voices. Collapse
                # to <=2 voices: keep the primary speaker distinct, map everyone
                # else to a single "CHARACTER" voice.
                if len(scene_speakers) > 2:
                    primary = scene_speakers[0]
                    label_map = {
                        sp: (primary if sp == primary else "CHARACTER")
                        for sp in scene_speakers
                    }
                    tts_input = self._build_tts_input(dialogue, label_map)
                    speech_config = [
                        {"speaker": primary, "voice": voice_map.get(primary, NARRATOR_VOICE)},
                        {"speaker": "CHARACTER", "voice": voice_map.get(scene_speakers[1], MALE_VOICES[0])},
                    ]
                elif len(scene_speakers) == 2:
                    tts_input = self._build_tts_input(dialogue)
                    speech_config = [
                        {"speaker": scene_speakers[0], "voice": voice_map.get(scene_speakers[0], NARRATOR_VOICE)},
                        {"speaker": scene_speakers[1], "voice": voice_map.get(scene_speakers[1], MALE_VOICES[0])},
                    ]
                else:
                    # Single speaker: read plainly without "SPEAKER:" labels
                    sp = scene_speakers[0] if scene_speakers else "NARRATOR"
                    tts_input = '\n'.join(line['text'] for line in dialogue)
                    speech_config = [
                        {"speaker": sp, "voice": voice_map.get(sp, NARRATOR_VOICE)}
                    ]

                # Generate audio
                audio_bytes = await self._call_gemini_tts(tts_input, speech_config)

                if audio_bytes:
                    # Convert PCM to WAV
                    wav_bytes = self._pcm_to_wav(audio_bytes, channels=1, rate=24000, sample_width=2)
                    result["audio_base64"] = base64.b64encode(wav_bytes).decode('utf-8')
                    result["duration_seconds"] = len(audio_bytes) / (24000 * 2)  # 24kHz, 16-bit
                    logger.info(f"Scene {scene_num}: Audio generated ({result['duration_seconds']:.1f}s)")
                else:
                    result["generation_error"] = "No audio returned from TTS"

            except asyncio.TimeoutError:
                result["generation_error"] = "Audio generation timed out"
                logger.warning(f"Scene {scene_num}: Timeout after {SCENE_TIMEOUT}s")

            except Exception as e:
                result["generation_error"] = f"Generation failed: {str(e)}"
                logger.error(f"Scene {scene_num}: Error - {str(e)}")

            audio_results.append(result)

            # Rate limit delay between scenes
            if scene != scene_dialogues[-1]:
                await asyncio.sleep(SCENE_DELAY)

        return audio_results

    def _build_tts_input(
        self,
        dialogue: List[Dict[str, Any]],
        label_map: Optional[Dict[str, str]] = None
    ) -> str:
        """Build TTS input text with speaker labels"""

        lines = []
        for line in dialogue:
            speaker = line['speaker']
            if label_map:
                speaker = label_map.get(speaker, speaker)
            text = line['text']
            # Gemini TTS uses "SPEAKER: text" format
            lines.append(f"{speaker}: {text}")

        return '\n'.join(lines)

    async def _call_gemini_tts(
        self,
        text: str,
        speech_config: List[Dict[str, str]]
    ) -> Optional[bytes]:
        """Call Gemini TTS (native audio generation) to produce multi-speaker audio.

        Uses generate_content with response_modalities=["AUDIO"] and a
        MultiSpeakerVoiceConfig so each script character maps to a distinct
        prebuilt voice. Returns raw 16-bit/24kHz PCM audio bytes.
        """

        from google import genai
        from google.genai import types
        from ..config import settings

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Build per-speaker voice configs (dedup by speaker label).
        speaker_voice_configs = []
        seen = set()
        for sc in speech_config:
            speaker = sc.get("speaker")
            if not speaker or speaker in seen:
                continue
            seen.add(speaker)
            speaker_voice_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=speaker,
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=sc.get("voice", NARRATOR_VOICE)
                        )
                    ),
                )
            )

        if len(speaker_voice_configs) == 1:
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=speaker_voice_configs[0].voice_config
                ),
            )
        else:
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=speaker_voice_configs
                    )
                ),
            )

        try:
            response = await client.aio.models.generate_content(
                model=TTS_MODEL,
                contents=text,
                config=config,
            )

            part = response.candidates[0].content.parts[0]
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data
            return None

        except Exception as e:
            logger.error(f"Gemini TTS API call failed: {str(e)}")
            raise

    def _pcm_to_wav(
        self,
        pcm_data: bytes,
        channels: int = 1,
        rate: int = 24000,
        sample_width: int = 2
    ) -> bytes:
        """Convert raw PCM data to WAV format"""

        buffer = BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)
        return buffer.getvalue()


# Async function for on-demand TTS generation (called by router)
async def generate_table_read(
    script_text: str,
    scenes: List[Dict[str, Any]],
    scene_numbers: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Generate table read audio for specified scenes.
    Called by the TTS router for on-demand generation.
    """
    agent = TTSAgent()

    # Filter scenes if specific numbers requested
    if scene_numbers:
        scenes = [s for s in scenes if s.get("scene_number") in scene_numbers]

    # Create a mock task
    task = AgentTask(
        agent_type="tts",
        task_data={
            "script_text": script_text,
            "scenes": scenes,
            "focus": "table_read_generation"
        }
    )

    result = await agent.process_task(task)

    return {
        "success": result.success,
        "scenes": result.data.get("scenes", []) if result.data else [],
        "total_scenes": result.data.get("total_scenes", 0) if result.data else 0,
        "voice_map": result.data.get("voice_map", {}) if result.data else {},
        "total_duration": result.data.get("total_duration_seconds", 0) if result.data else 0,
        "processing_time": result.processing_time,
        "error": result.error_message if not result.success else None
    }
