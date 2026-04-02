"""
Audio Generation Tools for Elderly Video Content

Provides structured information about TTS engines, music generation,
and audio mixing tools for creating elderly-friendly audio content.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TTSEngine:
    """A text-to-speech engine configuration."""
    name: str
    description: str
    install_command: str
    python_package: str | None = None
    homepage: str = ""
    offline: bool = False
    voices: list[str] = field(default_factory=list)
    elderly_config: dict[str, str | float] = field(default_factory=dict)
    example_python: str = ""
    notes: str = ""


@dataclass
class MusicTool:
    """A music/audio generation tool."""
    name: str
    description: str
    install_command: str
    python_package: str | None = None
    homepage: str = ""
    offline: bool = False
    requires_gpu: bool = False
    use_cases: list[str] = field(default_factory=list)
    example_python: str = ""
    notes: str = ""


@dataclass
class AudioMixingTool:
    """An audio processing/mixing tool."""
    name: str
    description: str
    install_command: str
    python_package: str | None = None
    capabilities: list[str] = field(default_factory=list)
    example_python: str = ""


@dataclass
class ElderlyAudioPreset:
    """Audio preset optimized for elderly listeners."""
    name: str
    description: str
    speech_rate: float  # multiplier (1.0 = normal, 0.75 = 75% speed)
    speech_pitch: float  # semitones offset
    speech_volume_db: float
    music_volume_db: float
    pause_between_sentences_ms: int
    sample_rate: int = 44100
    notes: str = ""


@dataclass
class AudioGeneration:
    """Complete audio generation toolkit for elderly content."""

    tts_engines: list[TTSEngine] = field(default_factory=list)
    music_tools: list[MusicTool] = field(default_factory=list)
    mixing_tools: list[AudioMixingTool] = field(default_factory=list)
    presets: list[ElderlyAudioPreset] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.tts_engines:
            self.tts_engines = self._default_tts_engines()
        if not self.music_tools:
            self.music_tools = self._default_music_tools()
        if not self.mixing_tools:
            self.mixing_tools = self._default_mixing_tools()
        if not self.presets:
            self.presets = self._default_presets()

    @staticmethod
    def _default_tts_engines() -> list[TTSEngine]:
        return [
            TTSEngine(
                name="pyttsx3",
                description=(
                    "Cross-platform, offline TTS engine using system speech synthesizers "
                    "(SAPI5 on Windows, NSSpeechSynthesizer on macOS, espeak on Linux). "
                    "No internet required. Good for quick prototyping."
                ),
                install_command="pip install pyttsx3",
                python_package="pyttsx3",
                homepage="https://github.com/nateshmbhat/pyttsx3",
                offline=True,
                voices=["system-dependent — typically 1-5 voices per platform"],
                elderly_config={
                    "rate": 130,  # words per minute (default ~200, slower for elderly)
                    "volume": 1.0,
                    "voice": "english",
                },
                example_python=(
                    'import pyttsx3\n\n'
                    'engine = pyttsx3.init()\n\n'
                    '# Configure for elderly-friendly speech\n'
                    'engine.setProperty("rate", 130)    # Slower than default 200\n'
                    'engine.setProperty("volume", 1.0)  # Full volume\n\n'
                    '# List available voices\n'
                    'voices = engine.getProperty("voices")\n'
                    'for v in voices:\n'
                    '    print(v.id, v.name)\n\n'
                    '# Generate speech\n'
                    'engine.say("Good morning! Today we will learn about healthy eating.")\n'
                    'engine.runAndWait()\n\n'
                    '# Save to file\n'
                    'engine.save_to_file("Stay hydrated throughout the day.", "tip.mp3")\n'
                    'engine.runAndWait()'
                ),
                notes="Quality varies by platform. Best on macOS, adequate on Linux with espeak-ng.",
            ),
            TTSEngine(
                name="espeak-ng",
                description=(
                    "Compact, open-source speech synthesizer supporting 100+ languages. "
                    "Lightweight and fully offline. Robotic but highly reliable."
                ),
                install_command="apt install espeak-ng  # pip install py-espeak-ng",
                python_package="py-espeak-ng",
                homepage="https://github.com/espeak-ng/espeak-ng",
                offline=True,
                voices=["100+ language voices"],
                elderly_config={
                    "speed": 120,  # words per minute
                    "pitch": 40,  # range 0-99
                    "amplitude": 100,
                },
                example_python=(
                    'import subprocess\n\n'
                    '# Command-line usage with elderly-friendly settings\n'
                    'text = "Remember to take your vitamins every morning."\n'
                    'subprocess.run([\n'
                    '    "espeak-ng",\n'
                    '    "-s", "120",    # Speed: 120 words/min (slow)\n'
                    '    "-p", "40",     # Pitch: lower, calmer\n'
                    '    "-a", "100",    # Amplitude: full volume\n'
                    '    "-w", "output.wav",  # Save to file\n'
                    '    text\n'
                    '])'
                ),
                notes="Very small footprint. Good for systems with limited resources.",
            ),
            TTSEngine(
                name="Coqui TTS",
                description=(
                    "Deep learning TTS toolkit with many pre-trained models. "
                    "Supports voice cloning, multi-speaker, and multilingual synthesis. "
                    "High-quality neural voices that run offline."
                ),
                install_command="pip install TTS",
                python_package="TTS",
                homepage="https://github.com/coqui-ai/TTS",
                offline=True,
                voices=[
                    "VITS", "Tacotron2", "GlowTTS",
                    "YourTTS (voice cloning)", "XTTS v2 (multilingual)"
                ],
                elderly_config={
                    "model": "tts_models/en/ljspeech/vits",
                    "speed": 0.8,
                },
                example_python=(
                    'from TTS.api import TTS\n\n'
                    '# List available models\n'
                    'print(TTS().list_models())\n\n'
                    '# Use a high-quality model\n'
                    'tts = TTS(model_name="tts_models/en/ljspeech/vits")\n\n'
                    '# Generate speech\n'
                    'tts.tts_to_file(\n'
                    '    text="Walking for thirty minutes each day strengthens your heart.",\n'
                    '    file_path="health_tip.wav",\n'
                    '    speed=0.8  # Slightly slower for clarity\n'
                    ')\n\n'
                    '# Multi-speaker model for variety\n'
                    'tts_multi = TTS(model_name="tts_models/en/vctk/vits")\n'
                    'tts_multi.tts_to_file(\n'
                    '    text="Let us begin our morning exercises.",\n'
                    '    file_path="exercise_intro.wav",\n'
                    '    speaker="p225",  # Select a clear, warm voice\n'
                    '    speed=0.8\n'
                    ')'
                ),
                notes="Best quality offline option. XTTS v2 supports voice cloning with just a short sample.",
            ),
            TTSEngine(
                name="Bark",
                description=(
                    "Transformer-based TTS by Suno AI. Generates highly realistic speech "
                    "with natural intonation, laughter, and non-verbal sounds. "
                    "Can generate music and sound effects too."
                ),
                install_command="pip install git+https://github.com/suno-ai/bark.git",
                python_package="bark",
                homepage="https://github.com/suno-ai/bark",
                offline=True,
                voices=[
                    "v2/en_speaker_0 through v2/en_speaker_9",
                    "Supports multiple languages",
                ],
                elderly_config={
                    "voice_preset": "v2/en_speaker_6",
                    "text_temp": 0.6,
                    "waveform_temp": 0.6,
                },
                example_python=(
                    'from bark import SAMPLE_RATE, generate_audio, preload_models\n'
                    'from scipy.io.wavfile import write as write_wav\n\n'
                    '# Preload models (first run downloads ~5GB)\n'
                    'preload_models()\n\n'
                    '# Generate speech with a calm voice\n'
                    'text = "[clears throat] Good morning, everyone. '
                    "Today's topic is healthy sleeping habits.\"\n"
                    'audio = generate_audio(\n'
                    '    text,\n'
                    '    history_prompt="v2/en_speaker_6",\n'
                    '    text_temp=0.6,       # Lower = more consistent\n'
                    '    waveform_temp=0.6,\n'
                    ')\n\n'
                    'write_wav("greeting.wav", SAMPLE_RATE, audio)'
                ),
                notes="GPU recommended. Very natural but less control over speed/pitch directly.",
            ),
            TTSEngine(
                name="Edge TTS",
                description=(
                    "Python wrapper for Microsoft Edge's online TTS service. "
                    "Free, no API key needed. High-quality neural voices with "
                    "SSML support for rate and pitch control."
                ),
                install_command="pip install edge-tts",
                python_package="edge-tts",
                homepage="https://github.com/rany2/edge-tts",
                offline=False,
                voices=[
                    "en-US-AriaNeural (female, warm)",
                    "en-US-GuyNeural (male, calm)",
                    "en-GB-SoniaNeural (female, gentle)",
                    "300+ voices across 80+ languages",
                ],
                elderly_config={
                    "rate": "-20%",
                    "pitch": "-5Hz",
                    "volume": "+10%",
                },
                example_python=(
                    'import asyncio\n'
                    'import edge_tts\n\n'
                    'async def generate_elderly_speech():\n'
                    '    communicate = edge_tts.Communicate(\n'
                    '        text="Drinking water regularly helps your joints stay flexible.",\n'
                    '        voice="en-US-AriaNeural",\n'
                    '        rate="-20%",     # 20% slower\n'
                    '        pitch="-5Hz",    # Slightly lower pitch\n'
                    '        volume="+10%",   # Slightly louder\n'
                    '    )\n'
                    '    await communicate.save("health_tip.mp3")\n\n'
                    'asyncio.run(generate_elderly_speech())'
                ),
                notes="Free and high quality. Requires internet. Best free option for neural TTS.",
            ),
        ]

    @staticmethod
    def _default_music_tools() -> list[MusicTool]:
        return [
            MusicTool(
                name="AudioCraft / MusicGen",
                description=(
                    "Meta's AI music generation model. Generates high-quality music "
                    "from text descriptions. Available in small/medium/large sizes. "
                    "Perfect for generating calm background music for elderly content."
                ),
                install_command="pip install audiocraft",
                python_package="audiocraft",
                homepage="https://github.com/facebookresearch/audiocraft",
                offline=True,
                requires_gpu=True,
                use_cases=[
                    "Generate calm background music from text prompts",
                    "Create ambient nature soundscapes",
                    "Produce gentle classical-style accompaniment",
                    "Generate meditation/relaxation music",
                ],
                example_python=(
                    'from audiocraft.models import MusicGen\n'
                    'from audiocraft.data.audio import audio_write\n\n'
                    '# Load model (small=300M, medium=1.5B, large=3.3B)\n'
                    'model = MusicGen.get_pretrained("facebook/musicgen-small")\n'
                    'model.set_generation_params(duration=30)  # 30 seconds\n\n'
                    '# Generate calm background music\n'
                    'descriptions = [\n'
                    '    "gentle acoustic guitar with soft piano, calm and peaceful, '
                    'slow tempo, suitable for relaxation",\n'
                    '    "soft ambient music with nature sounds, birds chirping, '
                    'very calm and soothing",\n'
                    ']\n\n'
                    'wav = model.generate(descriptions)\n\n'
                    '# Save generated audio\n'
                    'for i, audio in enumerate(wav):\n'
                    '    audio_write(f"background_{i}", audio.cpu(), model.sample_rate)'
                ),
                notes="GPU recommended. Small model works on CPU but slowly. Best prompts: 'gentle', 'calm', 'peaceful', 'slow tempo'.",
            ),
            MusicTool(
                name="Riffusion",
                description=(
                    "Stable Diffusion fine-tuned for music generation via spectrograms. "
                    "Generates music from text prompts. Unique approach using image "
                    "diffusion on mel spectrograms."
                ),
                install_command="pip install riffusion",
                python_package="riffusion",
                homepage="https://github.com/riffusion/riffusion",
                offline=True,
                requires_gpu=True,
                use_cases=[
                    "Generate unique background music from text",
                    "Create ambient soundscapes",
                    "Produce short musical intros/outros",
                ],
                notes="Experimental but creative. Good for short musical clips.",
            ),
            MusicTool(
                name="MIDI Generation (midiutil)",
                description=(
                    "Programmatic MIDI file generation. Create simple melodies, "
                    "chord progressions, and rhythmic patterns that can be rendered "
                    "with any MIDI synthesizer."
                ),
                install_command="pip install midiutil",
                python_package="midiutil",
                homepage="https://github.com/MarkCWirt/MIDIUtil",
                offline=True,
                requires_gpu=False,
                use_cases=[
                    "Create simple, gentle background melodies",
                    "Generate notification/transition sounds",
                    "Produce customizable musical patterns",
                ],
                example_python=(
                    'from midiutil import MIDIFile\n\n'
                    '# Create a gentle melody\n'
                    'midi = MIDIFile(1)  # One track\n'
                    'midi.addTempo(0, 0, 72)  # Slow tempo (72 BPM)\n'
                    'midi.addProgramChange(0, 0, 0, 0)  # Acoustic Grand Piano\n\n'
                    '# Simple, calm melody (C major scale fragment)\n'
                    'notes = [\n'
                    '    (60, 1.0), (64, 1.0), (67, 1.5),  # C, E, G\n'
                    '    (65, 1.0), (64, 1.0), (62, 1.5),  # F, E, D\n'
                    '    (60, 2.0),                          # C (held)\n'
                    ']\n\n'
                    'time = 0\n'
                    'for pitch, duration in notes:\n'
                    '    midi.addNote(0, 0, pitch, time, duration, volume=80)\n'
                    '    time += duration\n\n'
                    'with open("gentle_melody.mid", "wb") as f:\n'
                    '    midi.writeFile(f)\n\n'
                    '# Convert to WAV with FluidSynth:\n'
                    '# fluidsynth -ni soundfont.sf2 gentle_melody.mid -F melody.wav'
                ),
                notes="Lightweight, no GPU needed. Pair with FluidSynth for WAV output.",
            ),
        ]

    @staticmethod
    def _default_mixing_tools() -> list[AudioMixingTool]:
        return [
            AudioMixingTool(
                name="pydub",
                description=(
                    "Simple, high-level audio manipulation library. "
                    "Supports mixing, volume adjustment, format conversion, "
                    "silence insertion, and audio segment operations."
                ),
                install_command="pip install pydub",
                python_package="pydub",
                capabilities=[
                    "Mix narration with background music",
                    "Adjust volume levels (narration louder, music softer)",
                    "Add silence/pauses between segments",
                    "Fade in/out effects",
                    "Convert between audio formats",
                    "Split and concatenate audio clips",
                    "Normalize audio levels",
                ],
                example_python=(
                    'from pydub import AudioSegment\n\n'
                    '# Load audio files\n'
                    'narration = AudioSegment.from_file("narration.mp3")\n'
                    'music = AudioSegment.from_file("background_music.mp3")\n\n'
                    '# Adjust levels for elderly-friendly mix\n'
                    'narration = narration + 3             # Boost narration by 3dB\n'
                    'music = music - 18                     # Lower music by 18dB\n\n'
                    '# Add pauses between sentences (1.5 seconds)\n'
                    'pause = AudioSegment.silent(duration=1500)\n'
                    'narration_with_pauses = narration[:5000] + pause + narration[5000:]\n\n'
                    '# Trim music to match narration length\n'
                    'music = music[:len(narration_with_pauses)]\n\n'
                    '# Apply fade in/out to music\n'
                    'music = music.fade_in(3000).fade_out(3000)\n\n'
                    '# Mix together\n'
                    'final = narration_with_pauses.overlay(music)\n\n'
                    '# Normalize and export\n'
                    'final = final.normalize()\n'
                    'final.export("final_audio.mp3", format="mp3", bitrate="192k")'
                ),
            ),
            AudioMixingTool(
                name="librosa",
                description=(
                    "Advanced audio analysis library. Useful for analyzing "
                    "speech tempo, detecting silence, and audio feature extraction."
                ),
                install_command="pip install librosa",
                python_package="librosa",
                capabilities=[
                    "Analyze speech tempo and rhythm",
                    "Detect silence boundaries for segmentation",
                    "Time-stretch audio without pitch change",
                    "Pitch-shift audio without tempo change",
                    "Extract audio features for quality analysis",
                ],
                example_python=(
                    'import librosa\n'
                    'import soundfile as sf\n\n'
                    '# Load and slow down narration for elderly listeners\n'
                    'y, sr = librosa.load("narration.wav", sr=None)\n\n'
                    '# Slow down by 20% without changing pitch\n'
                    'y_slow = librosa.effects.time_stretch(y, rate=0.8)\n\n'
                    '# Save slowed narration\n'
                    'sf.write("narration_slow.wav", y_slow, sr)'
                ),
            ),
            AudioMixingTool(
                name="soundfile",
                description=(
                    "Fast, simple audio file I/O based on libsndfile. "
                    "Read and write WAV, FLAC, OGG, and other formats."
                ),
                install_command="pip install soundfile",
                python_package="soundfile",
                capabilities=[
                    "Read/write WAV, FLAC, OGG files",
                    "Fast numpy-based audio I/O",
                    "Support for multi-channel audio",
                ],
                example_python=(
                    'import soundfile as sf\n'
                    'import numpy as np\n\n'
                    '# Read audio\n'
                    'data, samplerate = sf.read("input.wav")\n\n'
                    '# Simple volume boost\n'
                    'data_louder = data * 1.5\n'
                    'data_louder = np.clip(data_louder, -1.0, 1.0)\n\n'
                    '# Write audio\n'
                    'sf.write("output.wav", data_louder, samplerate)'
                ),
            ),
        ]

    @staticmethod
    def _default_presets() -> list[ElderlyAudioPreset]:
        return [
            ElderlyAudioPreset(
                name="standard_elderly",
                description="Standard preset for elderly-friendly narration",
                speech_rate=0.80,
                speech_pitch=-2.0,
                speech_volume_db=0.0,
                music_volume_db=-18.0,
                pause_between_sentences_ms=1500,
                notes=(
                    "20% slower speech, slightly lower pitch for warmth, "
                    "music at -18dB so narration is clearly dominant, "
                    "1.5-second pauses between sentences for comprehension."
                ),
            ),
            ElderlyAudioPreset(
                name="hearing_impaired",
                description="Optimized for listeners with mild hearing loss",
                speech_rate=0.70,
                speech_pitch=-3.0,
                speech_volume_db=3.0,
                music_volume_db=-24.0,
                pause_between_sentences_ms=2000,
                notes=(
                    "30% slower speech, lower pitch (easier to hear), "
                    "boosted speech volume, minimal background music, "
                    "2-second pauses for processing time."
                ),
            ),
            ElderlyAudioPreset(
                name="meditation",
                description="Ultra-calm preset for relaxation and meditation content",
                speech_rate=0.65,
                speech_pitch=-4.0,
                speech_volume_db=-3.0,
                music_volume_db=-12.0,
                pause_between_sentences_ms=3000,
                notes=(
                    "Very slow, soothing speech. Music more prominent but still "
                    "gentle. Long pauses for reflection and breathing."
                ),
            ),
        ]

    def get_offline_tts(self) -> list[TTSEngine]:
        """Get TTS engines that work offline."""
        return [e for e in self.tts_engines if e.offline]

    def get_gpu_free_music(self) -> list[MusicTool]:
        """Get music tools that don't require a GPU."""
        return [t for t in self.music_tools if not t.requires_gpu]

    def summary(self) -> str:
        """Return a human-readable summary of all audio tools."""
        lines = ["=== Audio Generation Tools for Elderly Content ===\n"]

        lines.append("\n--- Text-to-Speech Engines ---")
        for e in self.tts_engines:
            lines.append(f"\n  {e.name} {'(offline)' if e.offline else '(online)'}")
            lines.append(f"    {e.description}")
            lines.append(f"    Install: {e.install_command}")

        lines.append("\n\n--- Music Generation ---")
        for t in self.music_tools:
            lines.append(f"\n  {t.name} {'(GPU)' if t.requires_gpu else '(CPU)'}")
            lines.append(f"    {t.description}")

        lines.append("\n\n--- Audio Mixing Tools ---")
        for t in self.mixing_tools:
            lines.append(f"\n  {t.name}")
            lines.append(f"    {t.description}")

        lines.append("\n\n--- Elderly Audio Presets ---")
        for p in self.presets:
            lines.append(f"\n  {p.name}: {p.description}")
            lines.append(f"    Speech: {p.speech_rate}x speed, {p.speech_pitch} pitch")
            lines.append(f"    Music: {p.music_volume_db}dB | Pause: {p.pause_between_sentences_ms}ms")
        return "\n".join(lines)
