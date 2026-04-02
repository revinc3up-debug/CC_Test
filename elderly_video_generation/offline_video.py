"""
Offline Video Generation Tools for Elderly Content

Provides structured information about tools that can generate
videos locally without requiring internet access.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VideoTool:
    """A local/offline video generation tool."""
    name: str
    description: str
    install_command: str
    python_package: str | None = None
    homepage: str = ""
    use_cases: list[str] = field(default_factory=list)
    elderly_tips: str = ""
    example_command: str = ""
    example_python: str = ""
    requires_gpu: bool = False
    min_ram_gb: int = 4


@dataclass
class VideoPreset:
    """A preset configuration for elderly-friendly video output."""
    name: str
    description: str
    resolution: str
    fps: int
    font_size: int
    text_speed: str
    color_scheme: dict[str, str] = field(default_factory=dict)
    ffmpeg_flags: str = ""


@dataclass
class OfflineVideoTools:
    """Collection of offline video generation tools and presets."""

    tools: list[VideoTool] = field(default_factory=list)
    presets: list[VideoPreset] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.tools:
            self.tools = self._default_tools()
        if not self.presets:
            self.presets = self._default_presets()

    @staticmethod
    def _default_tools() -> list[VideoTool]:
        return [
            VideoTool(
                name="FFmpeg",
                description=(
                    "Industry-standard multimedia framework for video/audio processing. "
                    "Can create videos from images, add text overlays, combine audio, "
                    "apply transitions, and encode to any format."
                ),
                install_command="apt install ffmpeg  # or brew install ffmpeg",
                homepage="https://ffmpeg.org",
                use_cases=[
                    "Combine image slideshows with audio narration",
                    "Add subtitle overlays with large, readable fonts",
                    "Create title cards and transition screens",
                    "Concatenate video segments into final output",
                    "Adjust playback speed for slower pacing",
                    "Add background music at reduced volume under narration",
                ],
                elderly_tips=(
                    "Use -filter_complex for large text overlays (fontsize=48+). "
                    "Set slower frame rates for slideshows (1 image per 5-8 seconds). "
                    "Mix background music at -18dB under narration."
                ),
                example_command=(
                    '# Create slideshow from images with audio\n'
                    'ffmpeg -framerate 1/5 -i img_%03d.jpg -i narration.mp3 \\\n'
                    '  -c:v libx264 -r 30 -pix_fmt yuv420p \\\n'
                    '  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,'
                    'pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \\\n'
                    '  -shortest output.mp4\n\n'
                    '# Add large subtitle overlay\n'
                    "ffmpeg -i input.mp4 -vf \"drawtext=text='Stay Healthy':"
                    "fontsize=56:fontcolor=white:x=(w-tw)/2:y=h-80\" output.mp4"
                ),
            ),
            VideoTool(
                name="MoviePy",
                description=(
                    "Python library for video editing — cutting, concatenation, "
                    "title insertions, compositing, and effects. Wraps FFmpeg with "
                    "a Pythonic API. Ideal for programmatic video assembly."
                ),
                install_command="pip install moviepy",
                python_package="moviepy",
                homepage="https://zulko.github.io/moviepy/",
                use_cases=[
                    "Programmatically assemble videos from scripts",
                    "Add animated text overlays and titles",
                    "Create picture-in-picture compositions",
                    "Apply crossfade transitions between segments",
                    "Composite narration audio over background video",
                    "Generate videos from Python data pipelines",
                ],
                elderly_tips=(
                    "Use TextClip with fontsize=56+ and color='white' on dark backgrounds. "
                    "Set clip durations to 6-10 seconds for comfortable reading. "
                    "Use crossfadein/crossfadeout for gentle transitions."
                ),
                example_python=(
                    'from moviepy.editor import (\n'
                    '    VideoFileClip, TextClip, CompositeVideoClip,\n'
                    '    AudioFileClip, concatenate_videoclips, ImageClip\n'
                    ')\n\n'
                    '# Create a title card\n'
                    'title = TextClip(\n'
                    '    "Daily Gentle Exercises",\n'
                    '    fontsize=60, color="white", bg_color="navy",\n'
                    '    size=(1920, 1080), method="caption"\n'
                    ').set_duration(5)\n\n'
                    '# Load and trim a video clip\n'
                    'clip = VideoFileClip("exercise.mp4").subclip(0, 30)\n\n'
                    '# Add narration\n'
                    'narration = AudioFileClip("narration.mp3")\n'
                    'clip = clip.set_audio(narration)\n\n'
                    '# Concatenate with crossfade\n'
                    'final = concatenate_videoclips(\n'
                    '    [title, clip],\n'
                    '    method="compose",\n'
                    '    padding=-1  # 1-second crossfade\n'
                    ')\n'
                    'final.write_videofile("output.mp4", fps=30)'
                ),
            ),
            VideoTool(
                name="OpenCV (cv2)",
                description=(
                    "Computer vision library with video I/O capabilities. "
                    "Can create videos frame-by-frame, add text/shapes, "
                    "process images, and build custom video pipelines."
                ),
                install_command="pip install opencv-python",
                python_package="opencv-python",
                homepage="https://opencv.org",
                use_cases=[
                    "Generate videos frame-by-frame with custom graphics",
                    "Create animated infographics and charts",
                    "Process and enhance images before video assembly",
                    "Add visual annotations and highlights",
                    "Build real-time video processing pipelines",
                ],
                elderly_tips=(
                    "Use cv2.putText with fontScale=2.0+ and thickness=3 for readability. "
                    "High contrast colors: white text on dark blue/green backgrounds. "
                    "Use cv2.FONT_HERSHEY_SIMPLEX for clean, readable text."
                ),
                example_python=(
                    'import cv2\n'
                    'import numpy as np\n\n'
                    '# Create a title card video\n'
                    'width, height, fps, duration = 1920, 1080, 30, 5\n'
                    'fourcc = cv2.VideoWriter_fourcc(*"mp4v")\n'
                    'writer = cv2.VideoWriter("title.mp4", fourcc, fps, (width, height))\n\n'
                    'for _ in range(fps * duration):\n'
                    '    frame = np.zeros((height, width, 3), dtype=np.uint8)\n'
                    '    frame[:] = (80, 40, 10)  # Dark blue background (BGR)\n'
                    '    cv2.putText(\n'
                    '        frame, "Health Tips for Seniors",\n'
                    '        (200, 540), cv2.FONT_HERSHEY_SIMPLEX,\n'
                    '        2.5, (255, 255, 255), 4, cv2.LINE_AA\n'
                    '    )\n'
                    '    writer.write(frame)\n\n'
                    'writer.release()'
                ),
            ),
            VideoTool(
                name="Manim",
                description=(
                    "Mathematical animation engine (used by 3Blue1Brown). "
                    "Creates beautiful animated explanations, diagrams, "
                    "and educational visualizations."
                ),
                install_command="pip install manim",
                python_package="manim",
                homepage="https://www.manim.community",
                use_cases=[
                    "Create animated health/nutrition infographics",
                    "Visualize exercise routines step by step",
                    "Explain medical concepts with clear animations",
                    "Build animated timelines and schedules",
                    "Generate medication reminder visualizations",
                ],
                elderly_tips=(
                    "Use large font_size=48+ in Text objects. "
                    "Slow animation run_time=3+ seconds. "
                    "High contrast color schemes. "
                    "Simple, uncluttered scenes."
                ),
                example_python=(
                    'from manim import *\n\n'
                    'class HealthTip(Scene):\n'
                    '    def construct(self):\n'
                    '        title = Text(\n'
                    '            "Daily Water Intake",\n'
                    '            font_size=56, color=BLUE\n'
                    '        )\n'
                    '        self.play(Write(title), run_time=3)\n'
                    '        self.wait(2)\n\n'
                    '        tip = Text(\n'
                    '            "Drink 6-8 glasses per day",\n'
                    '            font_size=44, color=WHITE\n'
                    '        ).next_to(title, DOWN, buff=1)\n'
                    '        self.play(FadeIn(tip), run_time=2)\n'
                    '        self.wait(3)\n\n'
                    '# Render: manim -pql script.py HealthTip'
                ),
            ),
            VideoTool(
                name="Pillow (PIL)",
                description=(
                    "Python imaging library for creating and manipulating images. "
                    "Use with FFmpeg or MoviePy to generate title cards, "
                    "infographic frames, and text overlays."
                ),
                install_command="pip install Pillow",
                python_package="Pillow",
                homepage="https://python-pillow.org",
                use_cases=[
                    "Generate title card images with custom layouts",
                    "Create infographic slides for health tips",
                    "Build text-heavy frames with proper typography",
                    "Design thumbnail images for video content",
                    "Create step-by-step instruction images",
                ],
                elderly_tips=(
                    "Use font sizes 40pt+ for body text, 60pt+ for titles. "
                    "High contrast: dark text on light backgrounds or vice versa. "
                    "Use sans-serif fonts (Arial, Helvetica) for readability."
                ),
                example_python=(
                    'from PIL import Image, ImageDraw, ImageFont\n\n'
                    '# Create a title card\n'
                    'img = Image.new("RGB", (1920, 1080), color=(20, 60, 100))\n'
                    'draw = ImageDraw.Draw(img)\n\n'
                    'try:\n'
                    '    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)\n'
                    '    font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)\n'
                    'except OSError:\n'
                    '    font_title = ImageFont.load_default()\n'
                    '    font_body = ImageFont.load_default()\n\n'
                    'draw.text((960, 400), "Morning Stretches", fill="white",\n'
                    '          font=font_title, anchor="mm")\n'
                    'draw.text((960, 550), "A gentle 10-minute routine for every day",\n'
                    '          fill=(200, 220, 255), font=font_body, anchor="mm")\n\n'
                    'img.save("title_card.png")'
                ),
            ),
            VideoTool(
                name="Stable Video Diffusion (SVD)",
                description=(
                    "AI model for generating short video clips from images. "
                    "Runs locally with a GPU. Can animate still images into "
                    "short, natural-looking video sequences."
                ),
                install_command="pip install diffusers torch accelerate",
                python_package="diffusers",
                homepage="https://huggingface.co/stabilityai/stable-video-diffusion-img2vid",
                requires_gpu=True,
                min_ram_gb=16,
                use_cases=[
                    "Animate still photographs into short clips",
                    "Create gentle motion effects from nature images",
                    "Generate ambient background video from scenery photos",
                    "Produce visual variety from limited stock images",
                ],
                elderly_tips=(
                    "Use calm, well-lit source images. Nature and indoor scenes "
                    "work best. Keep generated clips short (2-4 seconds) and loop "
                    "them for longer sequences. Avoid fast or jarring motion."
                ),
                example_python=(
                    'import torch\n'
                    'from diffusers import StableVideoDiffusionPipeline\n'
                    'from PIL import Image\n\n'
                    '# Load model (requires ~16GB VRAM)\n'
                    'pipe = StableVideoDiffusionPipeline.from_pretrained(\n'
                    '    "stabilityai/stable-video-diffusion-img2vid",\n'
                    '    torch_dtype=torch.float16\n'
                    ')\n'
                    'pipe.to("cuda")\n\n'
                    '# Generate video from image\n'
                    'image = Image.open("garden_scene.jpg").resize((1024, 576))\n'
                    'frames = pipe(image, num_frames=25).frames[0]\n\n'
                    '# Save frames or export with moviepy'
                ),
            ),
        ]

    @staticmethod
    def _default_presets() -> list[VideoPreset]:
        """Presets optimized for elderly viewers."""
        return [
            VideoPreset(
                name="elderly_standard",
                description="Standard preset for elderly-friendly video content",
                resolution="1920x1080",
                fps=30,
                font_size=56,
                text_speed="slow",
                color_scheme={
                    "background": "#14283C",
                    "text_primary": "#FFFFFF",
                    "text_secondary": "#C8DCFF",
                    "accent": "#4A90D9",
                    "warning": "#FFD700",
                },
                ffmpeg_flags=(
                    '-c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p '
                    '-c:a aac -b:a 128k -ar 44100'
                ),
            ),
            VideoPreset(
                name="elderly_large_text",
                description="Extra-large text for vision-impaired viewers",
                resolution="1920x1080",
                fps=30,
                font_size=72,
                text_speed="very_slow",
                color_scheme={
                    "background": "#000000",
                    "text_primary": "#FFFF00",
                    "text_secondary": "#FFFFFF",
                    "accent": "#00FF00",
                    "warning": "#FF6600",
                },
                ffmpeg_flags=(
                    '-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p '
                    '-c:a aac -b:a 128k -ar 44100'
                ),
            ),
            VideoPreset(
                name="elderly_slideshow",
                description="Slow-paced slideshow with long display times",
                resolution="1920x1080",
                fps=30,
                font_size=60,
                text_speed="very_slow",
                color_scheme={
                    "background": "#1A1A2E",
                    "text_primary": "#E8E8E8",
                    "text_secondary": "#A0C4FF",
                    "accent": "#BDB2FF",
                    "warning": "#FFC6FF",
                },
                ffmpeg_flags=(
                    '-framerate 1/8 -c:v libx264 -r 30 -pix_fmt yuv420p '
                    '-c:a aac -b:a 128k'
                ),
            ),
            VideoPreset(
                name="elderly_mobile",
                description="Optimized for viewing on tablets and phones with larger elements",
                resolution="1280x720",
                fps=24,
                font_size=48,
                text_speed="slow",
                color_scheme={
                    "background": "#FFFFFF",
                    "text_primary": "#1A1A1A",
                    "text_secondary": "#333333",
                    "accent": "#0066CC",
                    "warning": "#CC3300",
                },
                ffmpeg_flags=(
                    '-c:v libx264 -preset fast -crf 25 -pix_fmt yuv420p '
                    '-c:a aac -b:a 96k -ar 44100'
                ),
            ),
        ]

    def get_tool(self, name: str) -> VideoTool | None:
        """Get a tool by name (case-insensitive)."""
        for tool in self.tools:
            if tool.name.lower() == name.lower():
                return tool
        return None

    def get_preset(self, name: str) -> VideoPreset | None:
        """Get a preset by name."""
        for preset in self.presets:
            if preset.name == name:
                return preset
        return None

    def get_cpu_only_tools(self) -> list[VideoTool]:
        """Get tools that don't require a GPU."""
        return [t for t in self.tools if not t.requires_gpu]

    def summary(self) -> str:
        """Return a human-readable summary of all offline video tools."""
        lines = ["=== Offline Video Generation Tools ===\n"]
        for t in self.tools:
            lines.append(f"\n  {t.name}")
            lines.append(f"    {t.description}")
            lines.append(f"    Install: {t.install_command}")
            if t.python_package:
                lines.append(f"    Python: pip install {t.python_package}")
            lines.append(f"    GPU Required: {t.requires_gpu} | Min RAM: {t.min_ram_gb}GB")
            lines.append(f"    Use Cases: {', '.join(t.use_cases[:3])}")
            if t.elderly_tips:
                lines.append(f"    Elderly Tips: {t.elderly_tips}")

        lines.append("\n\n=== Elderly-Friendly Video Presets ===\n")
        for p in self.presets:
            lines.append(f"\n  {p.name}: {p.description}")
            lines.append(f"    Resolution: {p.resolution} | FPS: {p.fps} | Font: {p.font_size}pt")
            lines.append(f"    Colors: {p.color_scheme}")
        return "\n".join(lines)
