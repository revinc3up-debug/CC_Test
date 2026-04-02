"""
Topic Library for Silver-Haired Elderly Video Content

A comprehensive, categorized database of content topics suitable
for elderly/senior audiences. Each topic includes subtopics,
video script ideas, keywords for stock footage search, and
estimated engagement level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Difficulty(Enum):
    """Content complexity level for the target audience."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Engagement(Enum):
    """Expected audience engagement level."""
    HIGH = "high"
    MEDIUM = "medium"
    NICHE = "niche"


@dataclass
class VideoIdea:
    """A specific video content idea with production notes."""
    title: str
    description: str
    duration_minutes: int
    script_outline: list[str]
    stock_footage_keywords: list[str]
    difficulty: Difficulty = Difficulty.BEGINNER
    engagement: Engagement = Engagement.HIGH


@dataclass
class Topic:
    """A content topic with subtopics and video ideas."""
    name: str
    category: str
    description: str
    subtopics: list[str] = field(default_factory=list)
    video_ideas: list[VideoIdea] = field(default_factory=list)
    target_audience: str = "seniors 60+"
    keywords: list[str] = field(default_factory=list)


@dataclass
class TopicLibrary:
    """Comprehensive topic library for elderly video content."""

    topics: list[Topic] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.topics:
            self.topics = self._build_full_library()

    def get_by_category(self, category: str) -> list[Topic]:
        """Get all topics in a given category."""
        return [t for t in self.topics if t.category.lower() == category.lower()]

    def get_categories(self) -> list[str]:
        """Get all unique category names."""
        return sorted(set(t.category for t in self.topics))

    def get_high_engagement(self) -> list[VideoIdea]:
        """Get all high-engagement video ideas across all topics."""
        ideas = []
        for topic in self.topics:
            ideas.extend(v for v in topic.video_ideas if v.engagement == Engagement.HIGH)
        return ideas

    def get_beginner_content(self) -> list[VideoIdea]:
        """Get all beginner-level video ideas."""
        ideas = []
        for topic in self.topics:
            ideas.extend(v for v in topic.video_ideas if v.difficulty == Difficulty.BEGINNER)
        return ideas

    def search(self, query: str) -> list[Topic]:
        """Search topics by keyword in name, description, subtopics, and keywords."""
        query_lower = query.lower()
        results = []
        for topic in self.topics:
            searchable = " ".join([
                topic.name, topic.description,
                " ".join(topic.subtopics), " ".join(topic.keywords),
            ]).lower()
            if query_lower in searchable:
                results.append(topic)
        return results

    def summary(self) -> str:
        """Return a human-readable summary of the topic library."""
        lines = ["=== Elderly Video Content Topic Library ===\n"]
        for category in self.get_categories():
            topics = self.get_by_category(category)
            lines.append(f"\n--- {category} ({len(topics)} topics) ---")
            for t in topics:
                video_count = len(t.video_ideas)
                lines.append(f"  {t.name} — {t.description} [{video_count} video ideas]")
                for sub in t.subtopics[:5]:
                    lines.append(f"    • {sub}")
        total_ideas = sum(len(t.video_ideas) for t in self.topics)
        lines.append(f"\n\nTotal: {len(self.topics)} topics, {total_ideas} video ideas")
        return "\n".join(lines)

    @staticmethod
    def _build_full_library() -> list[Topic]:
        """Build the complete topic library with all categories."""
        topics: list[Topic] = []

        # ---- HEALTH & WELLNESS ----
        topics.append(Topic(
            name="Gentle Daily Exercise",
            category="Health & Wellness",
            description="Low-impact exercise routines safe for seniors",
            subtopics=[
                "Chair exercises for mobility",
                "Morning stretching routines (10-15 min)",
                "Balance exercises to prevent falls",
                "Gentle yoga for seniors",
                "Walking programs for heart health",
                "Hand and finger exercises for arthritis",
                "Breathing exercises for lung health",
                "Tai Chi basics for beginners",
            ],
            keywords=["exercise", "fitness", "stretching", "yoga", "walking", "balance"],
            video_ideas=[
                VideoIdea(
                    title="5-Minute Morning Chair Stretches",
                    description="A gentle routine to start the day with seated stretches",
                    duration_minutes=7,
                    script_outline=[
                        "Welcome and safety reminder",
                        "Neck rolls (30 seconds each direction)",
                        "Shoulder shrugs and circles",
                        "Seated torso twist",
                        "Ankle circles and toe raises",
                        "Cool down and encouragement",
                    ],
                    stock_footage_keywords=["senior exercise", "chair workout", "elderly stretching", "morning routine"],
                    engagement=Engagement.HIGH,
                ),
                VideoIdea(
                    title="Balance Exercises to Prevent Falls",
                    description="Simple balance exercises using a chair for support",
                    duration_minutes=10,
                    script_outline=[
                        "Why balance matters as we age",
                        "Safety setup: sturdy chair, clear space",
                        "Heel-to-toe walk",
                        "Single leg stands with chair support",
                        "Side leg raises",
                        "Marching in place",
                        "Summary and daily practice reminder",
                    ],
                    stock_footage_keywords=["balance exercise", "fall prevention", "senior standing", "chair support"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Nutrition & Healthy Eating",
            category="Health & Wellness",
            description="Diet guidance and simple recipes for seniors",
            subtopics=[
                "Calcium-rich foods for bone health",
                "Hydration — how much water to drink daily",
                "Easy-to-chew nutritious meals",
                "Understanding food labels",
                "Heart-healthy diet basics",
                "Managing diabetes through diet",
                "Vitamins and supplements guide",
                "Meal prep for one or two people",
            ],
            keywords=["nutrition", "diet", "cooking", "healthy eating", "recipes", "vitamins"],
            video_ideas=[
                VideoIdea(
                    title="5 Easy Heart-Healthy Breakfasts",
                    description="Simple breakfast recipes that support cardiovascular health",
                    duration_minutes=8,
                    script_outline=[
                        "Why breakfast matters for heart health",
                        "Recipe 1: Oatmeal with berries and walnuts",
                        "Recipe 2: Whole wheat toast with avocado",
                        "Recipe 3: Greek yogurt parfait",
                        "Recipe 4: Veggie egg white scramble",
                        "Recipe 5: Smoothie with spinach and banana",
                        "Weekly meal planning tip",
                    ],
                    stock_footage_keywords=["healthy breakfast", "cooking seniors", "oatmeal", "fresh fruits"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Medication Management",
            category="Health & Wellness",
            description="Safe medication practices and organization",
            subtopics=[
                "Organizing medications with pill boxes",
                "Understanding prescription labels",
                "Common drug interactions to watch for",
                "When to talk to your pharmacist",
                "Setting medication reminders",
                "Over-the-counter medication safety",
                "Proper medication storage",
            ],
            keywords=["medication", "pills", "prescription", "pharmacy", "drug safety"],
            video_ideas=[
                VideoIdea(
                    title="How to Organize Your Weekly Medications",
                    description="Step-by-step guide to using pill organizers effectively",
                    duration_minutes=6,
                    script_outline=[
                        "Why organization prevents missed doses",
                        "Choosing the right pill organizer",
                        "Setting up your weekly supply",
                        "Setting phone reminders",
                        "What to do if you miss a dose",
                        "When to call your doctor",
                    ],
                    stock_footage_keywords=["pill organizer", "medication", "pharmacy", "elderly health"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        # ---- TECHNOLOGY TUTORIALS ----
        topics.append(Topic(
            name="Smartphone Basics",
            category="Technology Tutorials",
            description="Learning to use smartphones confidently",
            subtopics=[
                "Making and receiving phone calls",
                "Sending text messages with larger text",
                "Taking and sharing photos",
                "Adjusting display settings (font size, brightness)",
                "Installing and using apps safely",
                "Using voice assistants (Siri, Google Assistant)",
                "Setting up emergency contacts and SOS",
                "Managing battery life",
            ],
            keywords=["smartphone", "phone", "texting", "apps", "technology", "mobile"],
            video_ideas=[
                VideoIdea(
                    title="Your First Smartphone: Getting Started",
                    description="Complete beginner's guide to using a smartphone",
                    duration_minutes=12,
                    script_outline=[
                        "Phone layout: buttons and screen",
                        "Turning on and unlocking",
                        "Making your first call",
                        "Reading and sending a text message",
                        "Making text bigger for easier reading",
                        "Connecting to Wi-Fi",
                        "Practice exercises",
                    ],
                    stock_footage_keywords=["senior smartphone", "elderly phone", "technology learning", "phone tutorial"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Video Calling Family",
            category="Technology Tutorials",
            description="Staying connected with family through video calls",
            subtopics=[
                "Setting up FaceTime (iPhone)",
                "Using Google Meet / Duo",
                "WhatsApp video calls",
                "Zoom for family gatherings",
                "Troubleshooting camera and microphone",
                "Good lighting and positioning tips",
                "Group video calls with the whole family",
            ],
            keywords=["video call", "FaceTime", "Zoom", "WhatsApp", "family", "connection"],
            video_ideas=[
                VideoIdea(
                    title="Video Call Your Grandchildren in 5 Easy Steps",
                    description="Simple guide to making video calls to stay connected",
                    duration_minutes=8,
                    script_outline=[
                        "Why video calls bring families closer",
                        "Choosing an app (WhatsApp / FaceTime)",
                        "Step-by-step: starting a video call",
                        "Camera positioning and lighting",
                        "What to do if the call drops",
                        "Scheduling regular call times",
                    ],
                    stock_footage_keywords=["senior video call", "grandparent phone", "family connection", "elderly technology"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Online Safety & Scam Awareness",
            category="Technology Tutorials",
            description="Protecting yourself from online threats and scams",
            subtopics=[
                "Recognizing phishing emails and texts",
                "Phone scams targeting seniors",
                "Safe online shopping practices",
                "Creating strong passwords",
                "Social media privacy settings",
                "What to do if you've been scammed",
                "Two-factor authentication explained",
            ],
            keywords=["scam", "fraud", "online safety", "phishing", "password", "security"],
            video_ideas=[
                VideoIdea(
                    title="5 Common Scams Targeting Seniors (And How to Avoid Them)",
                    description="Awareness guide for the most frequent elder-targeted scams",
                    duration_minutes=10,
                    script_outline=[
                        "Why scammers target seniors",
                        "Scam 1: Fake tech support calls",
                        "Scam 2: Grandparent impersonation scam",
                        "Scam 3: Medicare/insurance fraud",
                        "Scam 4: Lottery/prize scams",
                        "Scam 5: Romance scams",
                        "Golden rule: never share personal info",
                        "Who to call if you suspect a scam",
                    ],
                    stock_footage_keywords=["phone scam", "online fraud", "elderly warning", "internet safety"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        # ---- MENTAL WELLNESS ----
        topics.append(Topic(
            name="Memory & Cognitive Health",
            category="Mental Wellness",
            description="Exercises and habits to keep the mind sharp",
            subtopics=[
                "Daily brain exercises and puzzles",
                "Memory techniques for everyday life",
                "Benefits of reading and lifelong learning",
                "Music therapy and memory",
                "Social engagement for cognitive health",
                "When to talk to a doctor about memory",
                "Brain-healthy foods",
                "Learning new skills at any age",
            ],
            keywords=["memory", "brain", "cognitive", "puzzles", "mental health", "learning"],
            video_ideas=[
                VideoIdea(
                    title="5 Daily Brain Exercises to Keep Your Mind Sharp",
                    description="Simple mental exercises you can do every day",
                    duration_minutes=8,
                    script_outline=[
                        "Why mental exercise matters",
                        "Exercise 1: Word association game",
                        "Exercise 2: Number sequences",
                        "Exercise 3: Story recall (listen and retell)",
                        "Exercise 4: Observation challenge",
                        "Exercise 5: Learn one new word each day",
                        "Making it a daily habit",
                    ],
                    stock_footage_keywords=["brain exercise", "puzzle", "senior thinking", "mental wellness"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Meditation & Relaxation",
            category="Mental Wellness",
            description="Guided relaxation techniques for stress relief and sleep",
            subtopics=[
                "Beginner's guide to meditation",
                "Deep breathing exercises",
                "Progressive muscle relaxation",
                "Guided imagery for relaxation",
                "Better sleep techniques",
                "Managing anxiety and worry",
                "Mindfulness in daily activities",
                "Gratitude practice",
            ],
            keywords=["meditation", "relaxation", "sleep", "stress", "mindfulness", "breathing"],
            video_ideas=[
                VideoIdea(
                    title="10-Minute Guided Relaxation Before Bed",
                    description="A calming guided relaxation to help with sleep",
                    duration_minutes=12,
                    script_outline=[
                        "Getting comfortable in bed or a chair",
                        "Deep breathing countdown (10 breaths)",
                        "Progressive muscle relaxation: feet to head",
                        "Peaceful garden visualization",
                        "Gentle affirmations for restful sleep",
                        "Slow fade-out with soft music",
                    ],
                    stock_footage_keywords=["peaceful nature", "sunset", "calm water", "garden", "relaxation"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Social Connection & Loneliness",
            category="Mental Wellness",
            description="Combating isolation and building social connections",
            subtopics=[
                "Joining local community groups",
                "Volunteering opportunities for seniors",
                "Finding online communities and forums",
                "Reconnecting with old friends",
                "Intergenerational activities",
                "Pet companionship benefits",
                "Senior centers and activity programs",
            ],
            keywords=["social", "loneliness", "community", "friends", "connection", "volunteering"],
            video_ideas=[
                VideoIdea(
                    title="10 Ways to Stay Connected After Retirement",
                    description="Practical ideas for building and maintaining social connections",
                    duration_minutes=9,
                    script_outline=[
                        "The importance of social connection for health",
                        "Join a walking group or book club",
                        "Volunteer at a local school or library",
                        "Learn to use social media to reconnect",
                        "Adopt a pet for daily companionship",
                        "Take a class at a community center",
                        "Start small — one new activity per month",
                    ],
                    stock_footage_keywords=["senior friends", "community group", "elderly social", "volunteer"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        # ---- HOBBIES & LEISURE ----
        topics.append(Topic(
            name="Gardening for Seniors",
            category="Hobbies & Leisure",
            description="Accessible gardening techniques and projects",
            subtopics=[
                "Raised bed and container gardening",
                "Indoor herb gardens",
                "Low-maintenance flower gardens",
                "Adaptive tools for limited mobility",
                "Seasonal planting guides",
                "Benefits of gardening for mental health",
                "Water-wise gardening",
            ],
            keywords=["gardening", "plants", "flowers", "herbs", "outdoor", "nature"],
            video_ideas=[
                VideoIdea(
                    title="Start an Indoor Herb Garden in 3 Easy Steps",
                    description="Growing fresh herbs on your windowsill with minimal effort",
                    duration_minutes=7,
                    script_outline=[
                        "Why grow herbs at home",
                        "Choosing your herbs: basil, mint, rosemary",
                        "Setting up pots and soil",
                        "Watering and sunlight basics",
                        "Harvesting and using your herbs",
                        "Troubleshooting common issues",
                    ],
                    stock_footage_keywords=["herb garden", "indoor plants", "senior gardening", "windowsill garden"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        topics.append(Topic(
            name="Easy Cooking & Recipes",
            category="Hobbies & Leisure",
            description="Simple, nutritious recipes with clear instructions",
            subtopics=[
                "One-pot meals for one or two",
                "No-cook meals for hot days",
                "Slow cooker recipes",
                "Traditional family recipes to share",
                "Baking simple breads and cookies",
                "Kitchen safety tips",
                "Cooking with grandchildren",
            ],
            keywords=["cooking", "recipes", "baking", "kitchen", "meals", "food"],
            video_ideas=[
                VideoIdea(
                    title="3 Easy One-Pot Meals for Dinner Tonight",
                    description="Simple, nutritious dinners that require just one pot",
                    duration_minutes=10,
                    script_outline=[
                        "Why one-pot meals are perfect",
                        "Meal 1: Chicken vegetable soup",
                        "Meal 2: Pasta primavera",
                        "Meal 3: Bean and rice bowl",
                        "Storing leftovers safely",
                        "Next week's recipes preview",
                    ],
                    stock_footage_keywords=["cooking seniors", "one pot meal", "simple recipe", "home cooking"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Arts, Crafts & Creative Projects",
            category="Hobbies & Leisure",
            description="Creative activities that are enjoyable and therapeutic",
            subtopics=[
                "Watercolor painting for beginners",
                "Knitting and crocheting basics",
                "Scrapbooking and photo albums",
                "Simple origami projects",
                "Adult coloring books",
                "Writing memoirs and life stories",
                "Photography with a smartphone",
            ],
            keywords=["crafts", "art", "painting", "knitting", "creative", "hobbies"],
            video_ideas=[
                VideoIdea(
                    title="Beginner Watercolor: Paint a Simple Sunset",
                    description="A relaxing step-by-step watercolor painting session",
                    duration_minutes=15,
                    script_outline=[
                        "Materials needed (minimal supplies)",
                        "Setting up your workspace",
                        "Mixing warm colors: orange, pink, purple",
                        "Painting the sky gradient (wet-on-wet)",
                        "Adding a simple horizon line",
                        "Final touches and drying",
                        "Display ideas for your painting",
                    ],
                    stock_footage_keywords=["watercolor painting", "art class", "senior hobby", "sunset painting"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        # ---- SAFETY & EMERGENCY ----
        topics.append(Topic(
            name="Fall Prevention",
            category="Safety & Emergency",
            description="Practical steps to reduce fall risk at home",
            subtopics=[
                "Home safety walkthrough checklist",
                "Removing tripping hazards",
                "Proper lighting throughout the home",
                "Non-slip solutions for bathrooms",
                "Choosing supportive footwear",
                "When to use a walker or cane",
                "Getting up safely after a fall",
                "Stair safety modifications",
            ],
            keywords=["fall prevention", "home safety", "tripping", "bathroom safety", "mobility"],
            video_ideas=[
                VideoIdea(
                    title="Home Safety Tour: 10 Changes to Prevent Falls",
                    description="Room-by-room guide to making your home safer",
                    duration_minutes=10,
                    script_outline=[
                        "Why falls are the #1 risk for seniors",
                        "Entryway: lighting and shoe storage",
                        "Living room: rug anchors and cord management",
                        "Kitchen: step stools and spill cleanup",
                        "Bathroom: grab bars and non-slip mats",
                        "Bedroom: nightlights and bed height",
                        "Stairways: handrails and visibility",
                        "Quick checklist summary",
                    ],
                    stock_footage_keywords=["home safety", "grab bars", "senior home", "fall prevention"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Emergency Preparedness",
            category="Safety & Emergency",
            description="Being ready for emergencies and knowing what to do",
            subtopics=[
                "Building an emergency supply kit",
                "Emergency contact card in your wallet",
                "Medical alert devices and services",
                "What to do during a power outage",
                "Natural disaster preparation",
                "When to call 911 vs. your doctor",
                "First aid basics refresher",
            ],
            keywords=["emergency", "preparedness", "first aid", "911", "disaster", "safety"],
            video_ideas=[
                VideoIdea(
                    title="Your Emergency Kit: What Every Senior Should Have Ready",
                    description="Building a simple emergency supply kit step by step",
                    duration_minutes=8,
                    script_outline=[
                        "Why everyone needs an emergency kit",
                        "Water and non-perishable food (3-day supply)",
                        "Medications and medical documents",
                        "Flashlight, batteries, and radio",
                        "Emergency contact list",
                        "Storing and checking your kit quarterly",
                    ],
                    stock_footage_keywords=["emergency kit", "first aid", "preparedness", "safety supplies"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        # ---- FINANCIAL LITERACY ----
        topics.append(Topic(
            name="Retirement Financial Planning",
            category="Financial Literacy",
            description="Managing finances in retirement wisely",
            subtopics=[
                "Budgeting on a fixed income",
                "Understanding Social Security benefits",
                "Medicare and supplemental insurance explained",
                "Senior discounts — where and how to ask",
                "Avoiding unnecessary subscriptions",
                "Estate planning basics",
                "Talking to family about finances",
            ],
            keywords=["finance", "retirement", "budget", "Social Security", "Medicare", "money"],
            video_ideas=[
                VideoIdea(
                    title="Simple Budgeting for Retirement: A Practical Guide",
                    description="How to create and stick to a retirement budget",
                    duration_minutes=9,
                    script_outline=[
                        "Why budgeting matters in retirement",
                        "Listing your income sources",
                        "Tracking essential expenses",
                        "Finding areas to save",
                        "Senior discounts you might not know about",
                        "Simple spreadsheet or notebook method",
                        "Reviewing your budget monthly",
                    ],
                    stock_footage_keywords=["retirement planning", "budget", "senior finances", "money management"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        topics.append(Topic(
            name="Fraud & Financial Scam Prevention",
            category="Financial Literacy",
            description="Protecting your money from fraud and scams",
            subtopics=[
                "Common financial scams targeting seniors",
                "Protecting bank account information",
                "Safe online banking practices",
                "Investment fraud red flags",
                "Power of attorney and trusted contacts",
                "Reporting financial abuse",
                "Identity theft prevention",
            ],
            keywords=["fraud", "scam", "financial abuse", "identity theft", "bank safety"],
            video_ideas=[
                VideoIdea(
                    title="Protect Your Money: Financial Scam Red Flags",
                    description="How to recognize and avoid common financial fraud",
                    duration_minutes=8,
                    script_outline=[
                        "Why seniors are targeted by financial scams",
                        "Red flag 1: Pressure to act immediately",
                        "Red flag 2: Requests for gift card payments",
                        "Red flag 3: Too-good-to-be-true investments",
                        "Red flag 4: Unsolicited calls about your accounts",
                        "What to do if you suspect fraud",
                        "Setting up account alerts with your bank",
                    ],
                    stock_footage_keywords=["financial fraud", "scam prevention", "bank security", "elder fraud"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        # ---- DAILY LIVING ----
        topics.append(Topic(
            name="Sleep & Rest",
            category="Daily Living",
            description="Improving sleep quality and establishing healthy routines",
            subtopics=[
                "Creating a bedtime routine",
                "Bedroom environment for better sleep",
                "Foods that help or hinder sleep",
                "Managing nighttime bathroom trips",
                "Napping — when it helps and when it doesn't",
                "Dealing with insomnia naturally",
            ],
            keywords=["sleep", "rest", "insomnia", "bedtime", "routine", "napping"],
            video_ideas=[
                VideoIdea(
                    title="7 Tips for Better Sleep Tonight",
                    description="Practical advice for improving sleep quality naturally",
                    duration_minutes=8,
                    script_outline=[
                        "Why good sleep is vital for seniors",
                        "Tip 1: Consistent bedtime schedule",
                        "Tip 2: Limit screen time before bed",
                        "Tip 3: Create a cool, dark bedroom",
                        "Tip 4: Gentle evening stretches",
                        "Tip 5: Avoid caffeine after noon",
                        "Tip 6: Try a warm bath before bed",
                        "Tip 7: Keep a worry journal",
                    ],
                    stock_footage_keywords=["sleep", "bedroom", "relaxation", "evening routine", "peaceful night"],
                    engagement=Engagement.HIGH,
                ),
            ],
        ))

        topics.append(Topic(
            name="Personal Care & Hygiene",
            category="Daily Living",
            description="Maintaining personal care with comfort and dignity",
            subtopics=[
                "Skin care for aging skin",
                "Dental hygiene and denture care",
                "Foot care and nail trimming",
                "Dressing aids for limited mobility",
                "Bathing safety and adaptive equipment",
                "Hair care tips",
            ],
            keywords=["hygiene", "skincare", "dental", "grooming", "personal care", "bathing"],
            video_ideas=[
                VideoIdea(
                    title="Daily Skincare Routine for Mature Skin",
                    description="Simple skincare steps to keep your skin healthy and comfortable",
                    duration_minutes=6,
                    script_outline=[
                        "How skin changes with age",
                        "Gentle cleansing (avoid harsh soaps)",
                        "Moisturizing — when and how much",
                        "Sun protection every day",
                        "When to see a dermatologist",
                    ],
                    stock_footage_keywords=["skincare", "moisturizer", "senior beauty", "healthy skin"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        topics.append(Topic(
            name="Seasonal & Holiday Content",
            category="Daily Living",
            description="Seasonal activities, holiday tips, and celebrations",
            subtopics=[
                "Spring cleaning made simple",
                "Summer heat safety for seniors",
                "Autumn activities and fall prevention",
                "Winter warmth and holiday traditions",
                "Holiday crafts with grandchildren",
                "Seasonal recipe collections",
                "Garden planning by season",
            ],
            keywords=["seasons", "holidays", "spring", "summer", "autumn", "winter", "celebrations"],
            video_ideas=[
                VideoIdea(
                    title="Staying Safe and Cool This Summer",
                    description="Essential summer safety tips for seniors",
                    duration_minutes=7,
                    script_outline=[
                        "Heat-related illness warning signs",
                        "Hydration reminders and tips",
                        "Best times to go outdoors",
                        "Dressing for hot weather",
                        "Indoor activity ideas for hot days",
                        "When to seek medical help",
                    ],
                    stock_footage_keywords=["summer safety", "senior outdoors", "hydration", "sunny day"],
                    engagement=Engagement.MEDIUM,
                ),
            ],
        ))

        return topics
