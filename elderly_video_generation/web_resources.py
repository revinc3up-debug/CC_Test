"""
Web-Retrievable Resources for Elderly Video Generation

Provides structured access to free/open APIs and online platforms
for sourcing video, image, audio, and health content.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class APIResource:
    """A single web API resource."""
    name: str
    url: str
    api_docs_url: str
    description: str
    python_package: str | None = None
    api_key_required: bool = True
    free_tier: bool = True
    supports_video: bool = False
    supports_images: bool = False
    supports_audio: bool = False
    rate_limit: str | None = None
    attribution_required: bool = False
    notes: str = ""


@dataclass
class WebResources:
    """Collection of all web-retrievable resources for elderly video generation."""

    stock_media: list[APIResource] = field(default_factory=list)
    tts_apis: list[APIResource] = field(default_factory=list)
    music_sources: list[APIResource] = field(default_factory=list)
    health_content: list[APIResource] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stock_media:
            self.stock_media = self._default_stock_media()
        if not self.tts_apis:
            self.tts_apis = self._default_tts_apis()
        if not self.music_sources:
            self.music_sources = self._default_music_sources()
        if not self.health_content:
            self.health_content = self._default_health_content()

    @staticmethod
    def _default_stock_media() -> list[APIResource]:
        return [
            APIResource(
                name="Pexels",
                url="https://www.pexels.com",
                api_docs_url="https://www.pexels.com/api/documentation/",
                description=(
                    "Free stock photos and videos with a curated library. "
                    "Excellent for elderly lifestyle, nature, and wellness footage. "
                    "No attribution required. Part of Canva."
                ),
                python_package="pexels-api",
                api_key_required=True,
                free_tier=True,
                supports_video=True,
                supports_images=True,
                rate_limit="200 requests/hour, 20000 requests/month",
                attribution_required=False,
                notes="Best choice for video — search 'elderly', 'senior', 'wellness', 'nature walk'.",
            ),
            APIResource(
                name="Pixabay",
                url="https://pixabay.com",
                api_docs_url="https://pixabay.com/api/docs/",
                description=(
                    "Over 5 million free images and videos. "
                    "Must download and self-host — no hotlinking allowed."
                ),
                python_package="pixabay-python",
                api_key_required=True,
                free_tier=True,
                supports_video=True,
                supports_images=True,
                rate_limit="100 requests/minute",
                attribution_required=True,
                notes="Good for bulk downloads. Mention Pixabay in credits.",
            ),
            APIResource(
                name="Unsplash",
                url="https://unsplash.com",
                api_docs_url="https://unsplash.com/documentation",
                description=(
                    "High-quality, professionally curated photos. "
                    "No video support. Best for thumbnail and title card images."
                ),
                python_package="python-unsplash",
                api_key_required=True,
                free_tier=True,
                supports_video=False,
                supports_images=True,
                rate_limit="50 requests/hour (demo), 5000/hour (production)",
                attribution_required=False,
                notes="Photos only. Use for thumbnails, backgrounds, title slides.",
            ),
            APIResource(
                name="Wikimedia Commons",
                url="https://commons.wikimedia.org",
                api_docs_url="https://www.mediawiki.org/wiki/API:Main_page",
                description=(
                    "Massive open-license media repository. Includes historical "
                    "images, educational diagrams, and public domain content."
                ),
                python_package=None,
                api_key_required=False,
                free_tier=True,
                supports_video=True,
                supports_images=True,
                attribution_required=True,
                notes="Great for educational/historical content for seniors.",
            ),
        ]

    @staticmethod
    def _default_tts_apis() -> list[APIResource]:
        return [
            APIResource(
                name="Google Cloud Text-to-Speech",
                url="https://cloud.google.com/text-to-speech",
                api_docs_url="https://cloud.google.com/text-to-speech/docs",
                description=(
                    "High-quality neural TTS with SSML support. "
                    "Adjust speaking rate (0.75x recommended for elderly) "
                    "and pitch for clear, warm narration."
                ),
                python_package="google-cloud-texttospeech",
                api_key_required=True,
                free_tier=True,
                supports_audio=True,
                rate_limit="1 million characters/month free",
                notes="Use speakingRate=0.75, pitch=-1.0 for elderly-friendly voice.",
            ),
            APIResource(
                name="Amazon Polly",
                url="https://aws.amazon.com/polly/",
                api_docs_url="https://docs.aws.amazon.com/polly/",
                description=(
                    "AWS neural TTS with multiple natural-sounding voices. "
                    "SSML prosody tags allow fine-grained speed and tone control."
                ),
                python_package="boto3",
                api_key_required=True,
                free_tier=True,
                supports_audio=True,
                rate_limit="5 million characters/month free (first 12 months)",
                notes="Neural voices: Matthew, Joanna sound warm and clear.",
            ),
            APIResource(
                name="Microsoft Azure Speech",
                url="https://azure.microsoft.com/en-us/products/ai-services/text-to-speech",
                api_docs_url="https://learn.microsoft.com/en-us/azure/ai-services/speech-service/",
                description=(
                    "Azure Cognitive Services TTS with 400+ neural voices. "
                    "Supports emotion styles and fine-grained SSML control."
                ),
                python_package="azure-cognitiveservices-speech",
                api_key_required=True,
                free_tier=True,
                supports_audio=True,
                rate_limit="500K characters/month free",
                notes="Use 'friendly' or 'gentle' style for elderly content.",
            ),
            APIResource(
                name="ElevenLabs",
                url="https://elevenlabs.io",
                api_docs_url="https://docs.elevenlabs.io/api-reference",
                description=(
                    "State-of-the-art voice cloning and generation. "
                    "Extremely natural voices with emotional range."
                ),
                python_package="elevenlabs",
                api_key_required=True,
                free_tier=True,
                supports_audio=True,
                rate_limit="10K characters/month free",
                notes="Best quality but limited free tier. Good for premium content.",
            ),
        ]

    @staticmethod
    def _default_music_sources() -> list[APIResource]:
        return [
            APIResource(
                name="Free Music Archive (FMA)",
                url="https://freemusicarchive.org",
                api_docs_url="https://freemusicarchive.org/api",
                description=(
                    "Curated collection of free, legal music. "
                    "Filter by genre: classical, ambient, folk — ideal for elderly content."
                ),
                api_key_required=False,
                free_tier=True,
                supports_audio=True,
                notes="Search genres: classical, ambient, easy listening, folk.",
            ),
            APIResource(
                name="Freesound",
                url="https://freesound.org",
                api_docs_url="https://freesound.org/docs/api/",
                description=(
                    "Collaborative database of Creative Commons licensed sounds. "
                    "Sound effects, ambient sounds, and nature recordings."
                ),
                python_package="freesound-python",
                api_key_required=True,
                free_tier=True,
                supports_audio=True,
                attribution_required=True,
                notes="Excellent for nature sounds, gentle sound effects.",
            ),
            APIResource(
                name="Incompetech / Kevin MacLeod",
                url="https://incompetech.com/music/",
                api_docs_url="https://incompetech.com/music/royalty-free/",
                description=(
                    "Royalty-free music by Kevin MacLeod. Large library of "
                    "gentle, classical, and ambient tracks perfect for elderly content."
                ),
                api_key_required=False,
                free_tier=True,
                supports_audio=True,
                attribution_required=True,
                notes="CC-BY license. Calm categories: 'Peaceful', 'Gentle', 'Relaxing'.",
            ),
            APIResource(
                name="YouTube Audio Library",
                url="https://studio.youtube.com/channel/UC/music",
                api_docs_url="https://support.google.com/youtube/answer/3376882",
                description=(
                    "Free music and sound effects for YouTube creators. "
                    "Downloadable tracks sorted by mood, genre, and instrument."
                ),
                api_key_required=False,
                free_tier=True,
                supports_audio=True,
                attribution_required=False,
                notes="Filter by mood: 'calm', 'inspirational', 'peaceful'.",
            ),
        ]

    @staticmethod
    def _default_health_content() -> list[APIResource]:
        return [
            APIResource(
                name="National Institute on Aging (NIA)",
                url="https://www.nia.nih.gov",
                api_docs_url="https://www.nia.nih.gov/health",
                description=(
                    "US government health information for older adults. "
                    "Topics include exercise, nutrition, cognitive health, "
                    "chronic disease management, and caregiving."
                ),
                api_key_required=False,
                free_tier=True,
                notes="Public domain content. Authoritative health info for seniors.",
            ),
            APIResource(
                name="MedlinePlus",
                url="https://medlineplus.gov",
                api_docs_url="https://medlineplus.gov/webservices.html",
                description=(
                    "NIH consumer health information in plain language. "
                    "Web services API available for health topic lookups."
                ),
                python_package=None,
                api_key_required=False,
                free_tier=True,
                notes="XML/JSON API for health topics. Great for script research.",
            ),
            APIResource(
                name="WHO Ageing & Health",
                url="https://www.who.int/health-topics/ageing",
                api_docs_url="https://www.who.int/data",
                description=(
                    "World Health Organization resources on healthy ageing, "
                    "including guidelines, data, and educational materials."
                ),
                api_key_required=False,
                free_tier=True,
                notes="Global perspective on elder health. Good for diverse audiences.",
            ),
            APIResource(
                name="OpenFDA",
                url="https://open.fda.gov",
                api_docs_url="https://open.fda.gov/apis/",
                description=(
                    "Open API for FDA drug information. Useful for medication "
                    "awareness content — side effects, interactions, recalls."
                ),
                api_key_required=False,
                free_tier=True,
                rate_limit="240 requests/minute without key, 120K/day with key",
                notes="Drug label, adverse event, and recall data for medication safety content.",
            ),
        ]

    def get_all_resources(self) -> list[APIResource]:
        """Return all resources across all categories."""
        return self.stock_media + self.tts_apis + self.music_sources + self.health_content

    def get_by_category(self, category: str) -> list[APIResource]:
        """Get resources by category name."""
        categories = {
            "stock_media": self.stock_media,
            "tts": self.tts_apis,
            "music": self.music_sources,
            "health": self.health_content,
        }
        return categories.get(category, [])

    def get_free_no_key(self) -> list[APIResource]:
        """Get resources that require no API key."""
        return [r for r in self.get_all_resources() if not r.api_key_required]

    def get_video_sources(self) -> list[APIResource]:
        """Get resources that provide video content."""
        return [r for r in self.get_all_resources() if r.supports_video]

    def summary(self) -> str:
        """Return a human-readable summary of all web resources."""
        lines = ["=== Web-Retrievable Resources for Elderly Video Generation ===\n"]
        sections = [
            ("Stock Media APIs", self.stock_media),
            ("Text-to-Speech APIs", self.tts_apis),
            ("Music & Audio Sources", self.music_sources),
            ("Health Content Sources", self.health_content),
        ]
        for title, resources in sections:
            lines.append(f"\n--- {title} ---")
            for r in resources:
                lines.append(f"\n  {r.name}")
                lines.append(f"    URL: {r.url}")
                lines.append(f"    Docs: {r.api_docs_url}")
                lines.append(f"    Description: {r.description}")
                if r.python_package:
                    lines.append(f"    Python Package: pip install {r.python_package}")
                lines.append(f"    Free: {r.free_tier} | API Key: {r.api_key_required}")
                if r.rate_limit:
                    lines.append(f"    Rate Limit: {r.rate_limit}")
                if r.notes:
                    lines.append(f"    Notes: {r.notes}")
        return "\n".join(lines)
