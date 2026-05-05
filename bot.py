import os
import json
import random
import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo
from threading import Thread

import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from flask import Flask
from supabase import create_client

# ─────────────────────────────
# LOAD TOKEN
# ─────────────────────────────

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to Render Environment Variables.")

# ─────────────────────────────
# BOT SETUP
# ─────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ─────────────────────────────
# KEEP ALIVE WEB SERVER FOR RENDER
# ─────────────────────────────

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!"


def run_web():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    thread = Thread(target=run_web, daemon=True)
    thread.start()

# ─────────────────────────────
# DATABASE + IDS
# ─────────────────────────────

TZ = ZoneInfo("America/Toronto")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing.")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY is missing.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_ROW_ID = "main"
REPORT_CHANNEL_ID = 1500707305631780984
COMMAND_CHANNEL_ID = 1500705057207746610
WEATHER_CHANNEL_ID = 1441502516591202394

HELPER_ROLE_ID = 1484027097784516668
MODERATOR_ROLE_ID = 1441506626371715103
WEATHER_REPORT_ROLE_ID = 1500967820194877490

# ─────────────────────────────
# CLANS, RANKS, AND CHOICES
# ─────────────────────────────

CLANS = [
    "BlizzardClan",
    "FossilClan",
    "TorrentClan",
    "SpruceClan",
    "Outsider"
]

CLAN_NAMES_ONLY = [
    "BlizzardClan",
    "FossilClan",
    "TorrentClan",
    "SpruceClan"
]

CLAN_RANKS = [
    "Kit",
    "Apprentice",
    "Warrior",
    "Elder",
    "Leader",
    "Deputy",
    "Medicine Cat",
    "Medicine Cat Apprentice",
    "Preymaster",
    "Healer",
    "Digger",
    "Pathfinder",
    "Sporekeeper",
    "River Guardian",
    "Queen",
    "Den Dad"
]

OUTSIDER_RANKS = [
    "Rogue",
    "Loner",
    "Wanderer",
    "Kittypet"
]

ALL_RANKS = CLAN_RANKS + OUTSIDER_RANKS

FACTIONS = [
    "Bloodseekers",
    "Birds of Prey",
    "The Hollowborn",
    "The Scorched",
    "Barn Cats"
]

AFTERLIVES = [
    "StarClan",
    "Dark Forest",
    "Unknown Residence"
]

AGING_TO_ELDER_RANKS = [
    "Warrior",
    "Preymaster",
    "Healer",
    "Digger",
    "Pathfinder",
    "Sporekeeper",
    "River Guardian"
]

RANK_ORDER = [
    "Leader",
    "Deputy",
    "Medicine Cat",
    "Medicine Cat Apprentice",
    "Preymaster",
    "Healer",
    "Digger",
    "Pathfinder",
    "Sporekeeper",
    "River Guardian",
    "Warrior",
    "Elder",
    "Queen",
    "Den Dad",
    "Apprentice",
    "Kit"
]

OUTSIDER_RANK_ORDER = [
    "Rogue",
    "Loner",
    "Wanderer",
    "Kittypet"
]

CLAN_CHOICES = [
    app_commands.Choice(name=clan, value=clan)
    for clan in CLANS
]

CLAN_FILTER_CHOICES = [
    app_commands.Choice(name="All", value="All")
] + CLAN_CHOICES

CLAN_ONLY_CHOICES = [
    app_commands.Choice(name=clan, value=clan)
    for clan in CLAN_NAMES_ONLY
]

RANK_CHOICES = [
    app_commands.Choice(name=rank, value=rank)
    for rank in ALL_RANKS
]

FACTION_CHOICES = [
    app_commands.Choice(name=faction, value=faction)
    for faction in FACTIONS
]

AFTERLIFE_CHOICES = [
    app_commands.Choice(name=afterlife, value=afterlife)
    for afterlife in AFTERLIVES
]

AFTERLIFE_FILTER_CHOICES = [
    app_commands.Choice(name="All", value="All")
] + AFTERLIFE_CHOICES



# ─────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────

DEFAULT_DATA = {
    "cats": {},
    "moon": 4,
    "last_moon_month": None,
    "season": "Newleaf",
    "last_weather_week": None,
    "used_prophecies": []
}


def fresh_default_data():
    return {
        "cats": {},
        "moon": 4,
        "last_moon_month": None,
        "season": "Newleaf",
        "last_weather_week": None,
        "used_prophecies": []
    }


def load_data():
    try:
        response = (
            supabase.table("bot_data")
            .select("data")
            .eq("id", DATA_ROW_ID)
            .limit(1)
            .execute()
        )

        if response.data:
            loaded = response.data[0]["data"]
        else:
            loaded = fresh_default_data()
            save_data(loaded)

    except Exception as error:
        print(f"Could not load Supabase data: {error}")
        loaded = fresh_default_data()

    defaults = fresh_default_data()
    for key, value in defaults.items():
        loaded.setdefault(key, value)

    return loaded


def save_data(data_to_save):
    try:
        supabase.table("bot_data").upsert({
            "id": DATA_ROW_ID,
            "data": data_to_save
        }).execute()

        print("Data saved to Supabase successfully.")

    except Exception as error:
        print(f"Could not save Supabase data: {error}")
        raise


data = load_data()
data_lock = asyncio.Lock()

# ─────────────────────────────
# PERMISSION HELPERS
# ─────────────────────────────


def is_staff(interaction: discord.Interaction):
    if not hasattr(interaction.user, "roles"):
        return False

    allowed_role_ids = {HELPER_ROLE_ID, MODERATOR_ROLE_ID}
    user_role_ids = {role.id for role in interaction.user.roles}
    return bool(allowed_role_ids.intersection(user_role_ids))


async def staff_command_check(interaction: discord.Interaction):
    if not is_staff(interaction):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True
        )
        return False

    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.response.send_message(
            "Use bot commands in the command channel only.",
            ephemeral=True
        )
        return False

    return True

# ─────────────────────────────
# SMALL HELPERS
# ─────────────────────────────


def add_history(cat, entry):
    cat.setdefault("history", [])
    cat["history"].append(f"Moon {data['moon']}: {entry}")


def prepare_cat_record(name, cat):
    cat.setdefault("history", [])
    cat.setdefault("born_moon", max(0, data.get("moon", 4) - cat.get("age", 0)))
    cat.setdefault("status", "alive")
    cat.setdefault("afterlife", None)
    cat.setdefault("faction", None)
    cat.setdefault("death_moon", None)


def validate_cat_rank(clan, rank, faction=None):
    if clan != "Outsider" and rank in OUTSIDER_RANKS:
        return "Clan cats cannot use outsider ranks."

    if clan == "Outsider" and rank in CLAN_RANKS:
        return "Outsiders cannot use clan ranks."

    if rank == "Kittypet" and faction is not None:
        return "Kittypets cannot join factions."

    if clan != "Outsider" and faction is not None:
        return "Clan cats cannot join outsider factions."

    return None


async def safe_respond(interaction, message, ephemeral=False):
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(message, ephemeral=ephemeral)


async def send_long_message(channel, text):
    max_length = 1900
    chunks = []

    while len(text) > max_length:
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    chunks.append(text)

    for chunk in chunks:
        if chunk.strip():
            await channel.send(chunk)

# ─────────────────────────────
# SEASON SYSTEM
# ─────────────────────────────


def get_current_season():
    seasons = ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"]
    season_index = ((data["moon"] - 2) // 3) % len(seasons)
    return seasons[season_index]


def get_season_moon():
    return ((data["moon"] - 2) % 3) + 1

# ─────────────────────────────
# SUCCESSION SYSTEM
# ─────────────────────────────


def handle_succession(report):
    for clan in CLAN_NAMES_ONLY:
        living_leaders = [
            (name, cat) for name, cat in data["cats"].items()
            if cat.get("clan") == clan
            and cat.get("rank") == "Leader"
            and cat.get("status") != "dead"
        ]

        if living_leaders:
            continue

        deputies = [
            (name, cat) for name, cat in data["cats"].items()
            if cat.get("clan") == clan
            and cat.get("rank") == "Deputy"
            and cat.get("status") != "dead"
        ]

        if deputies:
            name, cat = deputies[0]
            cat["rank"] = "Leader"
            add_history(cat, f"Became leader of {clan}")
            report["succession"].append(f"👑 {name} became leader of {clan}.")


def handle_medicine_succession(report):
    for clan in CLAN_NAMES_ONLY:
        living_meds = [
            (name, cat) for name, cat in data["cats"].items()
            if cat.get("clan") == clan
            and cat.get("rank") == "Medicine Cat"
            and cat.get("status") != "dead"
        ]

        if living_meds:
            continue

        med_apps = [
            (name, cat) for name, cat in data["cats"].items()
            if cat.get("clan") == clan
            and cat.get("rank") == "Medicine Cat Apprentice"
            and cat.get("status") != "dead"
        ]

        if med_apps:
            name, cat = med_apps[0]
            cat["rank"] = "Medicine Cat"
            add_history(cat, f"Became Medicine Cat of {clan}")
            report["succession"].append(f"🌿 {name} became Medicine Cat of {clan}.")

# ─────────────────────────────
# PROPHECY SYSTEM
# ─────────────────────────────

PROPHECIES = [
    "🌙 StarClan whispers: “When the sun burns brightest, the water will hide its secrets.”",
    "🌙 StarClan warns: “A golden leaf in Greenleaf marks a path to rot.”",
    "🌙 StarClan murmurs: “The thickest brambles grow over the deepest lies.”",
    "🌙 StarClan speaks: “A leader's heart can beat within an apprentice's chest.”",
    "🌙 StarClan sends an omen: “The dry grass will sing of a fire yet to come.”",
    "🌙 StarClan warns: “A thirst for power is harder to quench than a summer drought.”",
    "🌙 StarClan whispers: “Heed the bird that flies toward the setting sun.”",
    "🌙 StarClan calls: “Where the honey drips, the sting follows.”",
    "🌙 StarClan murmurs: “A single thorn can bring down the strongest leader.”",
    "🌙 StarClan warns: “The moon shall hide its face when kin turn on kin.”",
    "🌙 StarClan speaks: “Green leaves may hide a black heart.”",
    "🌙 StarClan whispers: “The dust of the path holds the scent of the past.”",
    "🌙 StarClan sends word: “A heavy sky brings more than just rain.”",
    "🌙 StarClan warns: “The snake does not hiss before it strikes from the ferns.”",
    "🌙 StarClan murmurs: “Silver light will reveal the red on the clover.”",
    "🌙 StarClan whispers: “The oldest oak knows the youngest warrior’s sin.”",
    "🌙 StarClan speaks: “A hollow tree makes a poor fortress.”",
    "🌙 StarClan warns: “Beware the cat who hunts where the shadows never move.”",
    "🌙 StarClan sends an omen: “A fallen feather marks the end of a flight.”",
    "🌙 StarClan whispers: “The river's song will turn to a roar of mourning.”",
    "🌙 StarClan murmurs: “When the flowers wilt, the truth will bloom.”",
    "🌙 StarClan warns: “A paw stained with nectar may still hide a sharp claw.”",
    "🌙 StarClan speaks: “The wind carries whispers that the forest tries to drown.”",
    "🌙 StarClan whispers: “An empty den is louder than a crowded camp.”",
    "🌙 StarClan sends word: “The sun rises red on the day of reckoning.”",
    "🌙 StarClan warns: “A kit’s dream is a warrior’s nightmare.”",
    "🌙 StarClan murmurs: “Moss grows thickest where the blood was spilled.”",
    "🌙 StarClan speaks: “To lead the many, one must walk alone.”",
    "🌙 StarClan whispers: “The roots of the willow reach for the bones of the dead.”",
    "🌙 StarClan warns: “Do not mistake a moth’s wing for a sign of peace.”",
    "🌙 StarClan sends an omen: “Three stars will fall before the sun climbs high.”",
    "🌙 StarClan murmurs: “A muddy print leads to a clean conscience.”",
    "🌙 StarClan whispers: “The heat of the day will boil the blood of the angry.”",
    "🌙 StarClan warns: “A crow’s cry is the only eulogy for a traitor.”",
    "🌙 StarClan speaks: “Beneath the high stones, a low secret waits.”",
    "🌙 StarClan sends word: “The lake reflects the stars, but hides the mud.”",
    "🌙 StarClan whispers: “A stray spark will consume the greenest meadow.”",
    "🌙 StarClan warns: “Not every cat who crosses the border is an enemy.”",
    "🌙 StarClan murmurs: “The scent of lavender hides the smell of decay.”",
    "🌙 StarClan speaks: “A warrior’s oath is only as strong as their heart.”",
    "🌙 StarClan whispers: “When the cicadas go silent, the forest is watching.”",
    "🌙 StarClan warns: “The sharpest tooth is the one you cannot see.”",
    "🌙 StarClan sends an omen: “Fire and water shall meet in a dance of death.”",
    "🌙 StarClan murmurs: “A golden pelt does not guarantee a golden soul.”",
    "🌙 StarClan whispers: “The sky will bleed before the moon is full.”",
    "🌙 StarClan warns: “A heavy mist hides a heavier heart.”",
    "🌙 StarClan speaks: “The eagle does not care for the troubles of the mouse.”",
    "🌙 StarClan whispers: “A broken claw marks a broken promise.”",
    "🌙 StarClan murmurs: “The ants know the secrets of the earth.”",
    "🌙 StarClan sends word: “When Greenleaf ends, the reckoning begins.”"
]


def generate_prophecy(report):
    data.setdefault("used_prophecies", [])

    if random.randint(1, 100) > 65:
        return

    available = [prophecy for prophecy in PROPHECIES if prophecy not in data["used_prophecies"]]

    if not available:
        data["used_prophecies"] = []
        available = PROPHECIES.copy()

    prophecy = random.choice(available)
    data["used_prophecies"].append(prophecy)
    report["prophecies"].append(prophecy)

# ─────────────────────────────
# MOON UPDATE SYSTEM
# ─────────────────────────────


async def run_moon_update():
    async with data_lock:
        report = {
            "promotions": [],
            "births": [],
            "deaths": [],
            "succession": [],
            "prophecies": [],
            "season": None
        }

        data["moon"] += 1
        data["season"] = get_current_season()
        report["season"] = data["season"]

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if cat.get("status") == "dead":
                continue

            cat["age"] = cat.get("age", 0) + 1

            if cat.get("rank") == "Kit" and cat["age"] >= 6:
                cat["rank"] = "Apprentice"
                add_history(cat, "Became an Apprentice")
                report["promotions"].append(f"🐾 {name} became an Apprentice.")

            elif cat.get("rank") == "Apprentice" and cat["age"] >= 12:
                cat["rank"] = "Warrior"
                add_history(cat, "Became a Warrior")
                report["promotions"].append(f"⚔ {name} became a Warrior.")

            elif cat.get("rank") in AGING_TO_ELDER_RANKS and cat["age"] >= 95:
                cat["rank"] = "Elder"
                add_history(cat, "Retired as an Elder")
                report["promotions"].append(f"🍂 {name} retired as an Elder.")

        handle_succession(report)
        handle_medicine_succession(report)
        generate_prophecy(report)
        save_data(data)

        return report

# ─────────────────────────────
# CLAN REPORT BUILDER
# ─────────────────────────────


async def build_clan_report_text(report=None):
    if report is None:
        report = {
            "promotions": [],
            "births": [],
            "deaths": [],
            "succession": [],
            "prophecies": [],
            "season": data.get("season", get_current_season())
        }

    lines = [
        f"🌙 Moon {data['moon']} Report",
        f"🍃 Season: {report.get('season', data.get('season', 'Unknown'))} ({get_season_moon()}/3)",
        "Clan records updated.",
        ""
    ]

    for clan_name in CLAN_NAMES_ONLY:
        lines.append(f"⛺ {clan_name}")

        clan_cats = {
            name: cat for name, cat in data.get("cats", {}).items()
            if cat.get("clan") == clan_name and cat.get("status") != "dead"
        }

        if not clan_cats:
            lines.append("No cats")
            lines.append("")
            continue

        for rank in RANK_ORDER:
            ranked_cats = [
                (name, cat) for name, cat in clan_cats.items()
                if cat.get("rank") == rank
            ]

            if not ranked_cats:
                continue

            ranked_cats.sort(key=lambda item: item[1].get("age", 0), reverse=True)
            lines.append(f"{rank}:")

            for name, cat in ranked_cats:
                lines.append(f"• {name} — {cat.get('age', 0)} moons")

            lines.append("")

    lines.append("🌫 Outsiders")

    outsiders = [
        (name, cat) for name, cat in data.get("cats", {}).items()
        if cat.get("clan") == "Outsider" and cat.get("status") != "dead"
    ]

    if outsiders:
        outsiders.sort(key=lambda item: item[1].get("age", 0), reverse=True)
        for name, cat in outsiders:
            faction = f" | {cat.get('faction')}" if cat.get("faction") else ""
            lines.append(f"• {name} — {cat.get('rank')} — {cat.get('age', 0)} moons{faction}")
    else:
        lines.append("No outsiders")

    lines.extend(["", "💀 Deaths This Moon"])

    recent_dead = [
        (name, cat) for name, cat in data.get("cats", {}).items()
        if cat.get("status") == "dead" and cat.get("death_moon") == data["moon"]
    ]

    if recent_dead:
        for name, cat in recent_dead:
            lines.append(f"• {name} — {cat.get('age', 0)} moons → {cat.get('afterlife')}")
    else:
        lines.append("No deaths")

    lines.extend(["", "🍼 Births This Moon"])
    lines.extend(report["births"] if report.get("births") else ["No births"])

    lines.extend(["", "⚔ Promotions This Moon"])
    lines.extend(report["promotions"] if report.get("promotions") else ["No promotions"])

    lines.extend(["", "👑 Succession Updates"])
    lines.extend(report["succession"] if report.get("succession") else ["No succession changes"])

    lines.extend(["", "🌙 Prophecies / Omens"])
    lines.extend(report["prophecies"] if report.get("prophecies") else ["No omens this moon"])

    return "\n".join(lines)

# ─────────────────────────────
# WEATHER SYSTEM
# ─────────────────────────────

BANFF_MONTHLY_AVERAGES = {
    1: {"high": -4, "temp": -9, "low": -14},
    2: {"high": -1, "temp": -7, "low": -12},
    3: {"high": 3, "temp": -3, "low": -8},
    4: {"high": 9, "temp": 2, "low": -3},
    5: {"high": 14, "temp": 7, "low": 1},
    6: {"high": 18, "temp": 11, "low": 5},
    7: {"high": 21, "temp": 14, "low": 8},
    8: {"high": 21, "temp": 14, "low": 7},
    9: {"high": 16, "temp": 9, "low": 3},
    10: {"high": 9, "temp": 3, "low": -1},
    11: {"high": 0, "temp": -4, "low": -8},
    12: {"high": -5, "temp": -10, "low": -14}
}

SEASONAL_OPENERS = {
    "Newleaf": [
        "🌱 The frost has begun to loosen its grip on the territories. Soft earth returns beneath each pawstep, and fresh green shoots push through the mud.",
        "🌧️ Newleaf has washed over the land in rain and fresh growth. The trails are damp, the air smells of earth, and prey begins to stir."
    ],
    "Greenleaf": [
        "☀️ Greenleaf stretches warmly across the territories. Thick leaves cast shade over the forest floor, rivers run clear, and prey moves boldly.",
        "🌿 The land is full and bright beneath Greenleaf’s warmth. Herbs grow thick, insects hum in the grass, and the forest feels alive."
    ],
    "Leaf-fall": [
        "🍂 Bright colours fade to muted browns, and morning frost begins to blanket the territories, bringing a crunch to each cat’s step.",
        "🌫️ Leaf-fall settles heavily over the forest. Trails grow damp, branches grow bare, and prey begins preparing for colder moons."
    ],
    "Leafbare": [
        "❄️ Leaf-bare tightens its cold grip around the territories. Snow hushes the forest floor, prey shelters deep, and bitter winds test every warrior.",
        "🌨️ Frost blankets the dens, branches, and trails. The world feels quieter now, as though the forest itself is saving strength."
    ]
}

PREY_REPORTS = {
    "Newleaf": [
        "🐇 Prey is returning, though many creatures remain cautious after leaf-bare. Rain may weaken scent trails, but fresh growth draws small prey out.",
        "🌿 Herbs are sprouting again, making this an important time for medicine cats to gather while the forest renews itself."
    ],
    "Greenleaf": [
        "🐿️ Prey is plentiful in many parts of the territory, especially where shade and fresh water are nearby.",
        "🌾 Herbs are abundant, though hot weather may dry exposed patches if they are not gathered in time."
    ],
    "Leaf-fall": [
        "🦎 Amphibians and reptiles are slower now, and prey animals are beginning to store food before leaf-bare.",
        "🍁 The territory is preparing for the cold. Prey is cautious, herbs are fading, and patrols should use good hunting weather wisely."
    ],
    "Leafbare": [
        "🐁 Prey is scarce, but not impossible to find. Tracks in snow, clear visibility, or a brief thaw can turn a difficult hunt lucky.",
        "🌨️ Herbs are difficult to replace, and medicine cats may need to rely on stored supplies until Newleaf returns."
    ]
}

WEATHER_BY_SEASON = {
    "Newleaf": [
        ("Heavy rain", -2, "Heavy rain makes scent trails muddy and visibility poor."),
        ("Cold rain", -2, "Cold rain soaks the territory and keeps prey hidden."),
        ("Thunder showers", -2, "Sudden thunder makes prey scatter quickly."),
        ("Thick mist", -1, "Mist makes movement harder to track."),
        ("Wet underpaws", -1, "The ground is slippery and scent is weak."),
        ("Chilly drizzle", -1, "A damp chill makes hunting uncomfortable."),
        ("Cloudy", 0, "Cloud cover keeps the forest calm."),
        ("Soft breeze", 0, "A soft breeze moves through the trees without helping or hurting hunts."),
        ("Cool morning", 0, "The air is cool, but conditions are steady."),
        ("Overcast skies", 0, "The sky is grey, but the territory is manageable."),
        ("Damp forest", 0, "The ground is damp, but not enough to affect hunting."),
        ("Fresh newleaf air", 0, "The territory feels awake, but prey remains cautious."),
        ("Light clouds", 0, "Light clouds drift overhead."),
        ("Quiet drizzle", 0, "A light drizzle falls, but it causes little trouble."),
        ("Sunny breaks", 1, "Warm light brings prey out between showers."),
        ("Warm breeze", 1, "A warm breeze carries scent gently through the territory."),
        ("Clear afternoon", 1, "Clear skies make prey movement easier to spot."),
        ("Fresh growth", 1, "New growth attracts prey into the open."),
        ("Mild sunshine", 2, "The pleasant warmth draws prey from shelter."),
        ("Bright newleaf day", 2, "A perfect newleaf day brings strong hunting conditions.")
    ],
    "Greenleaf": [
        ("Thunderstorm", -3, "Thunder and heavy rain scatter prey."),
        ("Heat haze", -2, "Heavy heat makes prey hide deep in shade."),
        ("Dry wind", -1, "Dry wind scatters scent trails."),
        ("Sudden downpour", -1, "A fast storm interrupts hunting patrols."),
        ("Warm and cloudy", 0, "The day is warm but ordinary."),
        ("Still air", 0, "The air is still, making the forest feel quiet."),
        ("Humid morning", 0, "Humidity hangs in the air, but prey is still active."),
        ("Cloudy with sun", 0, "Mixed skies bring average hunting conditions."),
        ("Light summer rain", 0, "A small rain cools the territory."),
        ("Mild greenleaf day", 0, "The weather is steady and calm."),
        ("Sunny", 2, "Warm sun brings prey into the open."),
        ("Partly cloudy", 1, "Good hunting weather with mild cover."),
        ("Light breeze", 1, "A breeze helps carry scent through the territory."),
        ("Golden sunshine", 2, "Bright sun warms the forest and prey is active."),
        ("Clear skies", 2, "Clear weather makes hunting easier."),
        ("Warm forest paths", 1, "Dry paths make travel easy for hunting patrols."),
        ("Cool shade", 1, "Shade keeps prey moving instead of hiding."),
        ("Fresh breeze", 1, "Fresh air helps hunters catch scent."),
        ("Perfect hunting day", 2, "The territory is full of movement and scent."),
        ("Peaceful greenleaf morning", 2, "Prey is active in the soft morning warmth.")
    ],
    "Leaf-fall": [
        ("Cold rain", -2, "Cold rain makes hunting uncomfortable and difficult."),
        ("Foggy", -2, "Fog makes it hard to see movement clearly."),
        ("Windy", -1, "Wind scatters scent trails."),
        ("Wet leaves", -1, "Wet leaves make pawsteps slippery."),
        ("Early frost", -1, "Frost keeps prey hidden in warmer dens."),
        ("Sharp gusts", -2, "Strong gusts make scent unreliable."),
        ("Cloudy and cool", 0, "Prey is cautious as the air grows colder."),
        ("Grey sky", 0, "The day is gloomy but manageable."),
        ("Dry leaves", 0, "Leaves crunch underpaw, but prey can still be found."),
        ("Cool breeze", 0, "The breeze is steady and not too harsh."),
        ("Quiet forest", 0, "The territory feels still and watchful."),
        ("Pale sunlight", 0, "Weak sunlight filters through thinning trees."),
        ("Crisp morning", 0, "The air is crisp but calm."),
        ("Damp leaf-fall air", 0, "The air is damp, but hunting remains normal."),
        ("Crisp and clear", 1, "Clear air makes tracking easier."),
        ("Fresh leaf-fall breeze", 1, "The breeze carries scent cleanly."),
        ("Dry clear day", 1, "Dry ground helps hunting patrols move quietly."),
        ("Bright cold sun", 1, "Bright sunlight helps cats spot prey movement."),
        ("Prey gathering day", 2, "Prey is active while gathering food before leafbare."),
        ("Golden leaf-fall afternoon", 2, "The mild weather brings prey into the open.")
    ],
    "Leafbare": [
        ("Heavy snow", -4, "Deep snow makes hunting very difficult."),
        ("Snow", -3, "Snow covers scent trails and muffles prey movement."),
        ("Freezing fog", -3, "The cold fog makes it hard to see or scent prey."),
        ("Ice crust", -2, "Ice makes travel dangerous and noisy."),
        ("Bitter wind", -2, "The wind cuts through fur and scatters scent."),
        ("Blizzard", -4, "A blizzard makes hunting nearly impossible."),
        ("Frozen rain", -3, "Frozen rain coats the territory in slippery ice."),
        ("Deep cold", -2, "The cold keeps prey hidden and cats tired."),
        ("Clear and cold", 0, "The cold is sharp, but visibility is good."),
        ("Cloudy with flurries", 0, "Light flurries fall without causing much trouble."),
        ("Still winter air", 0, "The air is cold but calm."),
        ("Pale winter sun", 0, "Weak sunlight brightens the territory."),
        ("Hard-packed snow", 0, "The snow is firm enough to walk on."),
        ("Quiet frozen morning", 0, "The forest is still, but manageable."),
        ("Cold cloudy day", 0, "The sky is grey and the air is cold."),
        ("Light frost", 0, "Frost covers the ground but does not stop patrols."),
        ("Fresh tracks in snow", 1, "Fresh pawprints make prey easier to follow."),
        ("Bright snowlight", 1, "The snow reflects light and makes movement easy to spot."),
        ("Calm winter sun", 1, "A rare calm day helps hunting patrols."),
        ("Thawing afternoon", 2, "A brief thaw brings prey out from shelter.")
    ]
}


def generate_weekly_weather():
    now = datetime.now(TZ)
    averages = BANFF_MONTHLY_AVERAGES[now.month]
    season = data.get("season", get_current_season())

    weather, modifier, reason = random.choice(
        WEATHER_BY_SEASON.get(season, WEATHER_BY_SEASON["Newleaf"])
    )

    avg_temp = random.randint(averages["low"], averages["high"])
    modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)

    return (
        "🌦️ Weekly Territory Weather Report 🌦️\n\n"
        f"🍃 Season: {season}\n"
        f"🌡️ Average Temp: {avg_temp}°C\n"
        f"☁️ Weekly Weather: {weather}\n"
        f"🎯 Hunting Modifier: {modifier_text}\n"
        f"📖 Effect: {reason}"
    )

# ─────────────────────────────
# READY + ERROR HANDLING
# ─────────────────────────────

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as error:
        print(f"Slash command sync failed: {error}")

    if not monthly_moon.is_running():
        monthly_moon.start()

    if not weekly_weather_report.is_running():
        weekly_weather_report.start()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"Slash command error: {error}")

    try:
        await safe_respond(
            interaction,
            "Something went wrong while running that command. Check the Render logs for the exact error.",
            ephemeral=True
        )
    except Exception as send_error:
        print(f"Could not send error response: {send_error}")

# ─────────────────────────────
# STAFF COMMANDS
# ─────────────────────────────

@bot.tree.command(name="add", description="Add a new cat")
@app_commands.describe(name="Cat name", age="Age in moons", clan="Select clan", rank="Select rank", faction="Optional outsider faction")
@app_commands.choices(clan=CLAN_CHOICES, rank=RANK_CHOICES, faction=FACTION_CHOICES)
async def add_cat(interaction: discord.Interaction, name: str, age: int, clan: app_commands.Choice[str], rank: app_commands.Choice[str], faction: app_commands.Choice[str] = None):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name in data["cats"]:
            await interaction.response.send_message("That cat already exists.", ephemeral=True)
            return

        faction_value = faction.value if faction else None
        validation_error = validate_cat_rank(clan.value, rank.value, faction_value)
        if validation_error:
            await interaction.response.send_message(validation_error, ephemeral=True)
            return

        data["cats"][name] = {
            "clan": clan.value,
            "age": age,
            "rank": rank.value,
            "faction": faction_value,
            "status": "alive",
            "afterlife": None,
            "death_moon": None,
            "born_moon": max(0, data["moon"] - age),
            "history": [f"Moon {data['moon']}: Added to records as {rank.value}"]
        }
        save_data(data)

    await interaction.response.send_message(
        f"🐾 Added **{name}**\n\n"
        f"⛺ Clan: {clan.value}\n"
        f"⚔ Rank: {rank.value}\n"
        f"🌙 Age: {age} moons"
    )


@bot.tree.command(name="addlitter", description="Manually add a litter with custom kit names")
@app_commands.describe(mother="Mother cat name", clan="Clan for the kits", kit1="First kit name", kit2="Second kit name", kit3="Third kit name optional", kit4="Fourth kit name optional", kit5="Fifth kit name optional", kit6="Sixth kit name optional")
@app_commands.choices(clan=CLAN_CHOICES)
async def add_litter(interaction: discord.Interaction, mother: str, clan: app_commands.Choice[str], kit1: str, kit2: str, kit3: str = None, kit4: str = None, kit5: str = None, kit6: str = None):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if mother not in data["cats"]:
            await interaction.response.send_message("Mother cat not found.", ephemeral=True)
            return

        kit_names = [name for name in [kit1, kit2, kit3, kit4, kit5, kit6] if name]
        duplicates = [kit_name for kit_name in kit_names if kit_name in data["cats"]]

        if duplicates:
            await interaction.response.send_message(f"These names already exist: {', '.join(duplicates)}", ephemeral=True)
            return

        born_names = []
        mother_faction = data["cats"][mother].get("faction")

        for kit_name in kit_names:
            data["cats"][kit_name] = {
                "clan": clan.value,
                "age": 0,
                "rank": "Kit" if clan.value != "Outsider" else "Loner",
                "faction": mother_faction if clan.value == "Outsider" else None,
                "status": "alive",
                "afterlife": None,
                "death_moon": None,
                "born_moon": data["moon"],
                "history": [f"Moon {data['moon']}: Born to {mother}"]
            }
            born_names.append(kit_name)

        add_history(data["cats"][mother], f"Had a litter of {len(born_names)} kit(s): {', '.join(born_names)}")
        save_data(data)

    await interaction.response.send_message(
        f"🍼 {mother} had a litter of {len(born_names)} kit(s):\n" +
        "\n".join([f"• {kit_name}" for kit_name in born_names])
    )


@bot.tree.command(name="setage", description="Set a cat's age")
async def setage(interaction: discord.Interaction, name: str, age: int):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        data["cats"][name]["age"] = age
        add_history(data["cats"][name], f"Age manually set to {age} moons")
        save_data(data)

    await interaction.response.send_message(f"🌙 {name} is now {age} moons old.")


@bot.tree.command(name="setrank", description="Change a cat's rank")
@app_commands.describe(name="Cat name", rank="New rank")
@app_commands.choices(rank=RANK_CHOICES)
async def setrank(interaction: discord.Interaction, name: str, rank: app_commands.Choice[str]):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]
        validation_error = validate_cat_rank(cat.get("clan"), rank.value, cat.get("faction"))
        if validation_error:
            await interaction.response.send_message(validation_error, ephemeral=True)
            return

        cat["rank"] = rank.value
        add_history(cat, f"Rank changed to {rank.value}")
        save_data(data)

    await interaction.response.send_message(f"⚔ {name} is now {rank.value}.")


@bot.tree.command(name="rename", description="Rename a cat")
@app_commands.describe(old_name="Current name", new_name="New name")
async def rename_cat(interaction: discord.Interaction, old_name: str, new_name: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if old_name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        if new_name in data["cats"]:
            await interaction.response.send_message("That new name already exists.", ephemeral=True)
            return

        data["cats"][new_name] = data["cats"].pop(old_name)
        add_history(data["cats"][new_name], f"Renamed from {old_name} to {new_name}")
        save_data(data)

    await interaction.response.send_message(f"✏️ Renamed **{old_name} → {new_name}**")


@bot.tree.command(name="kill", description="Kill a cat")
@app_commands.describe(name="Cat name", afterlife="Afterlife destination")
@app_commands.choices(afterlife=AFTERLIFE_CHOICES)
async def kill_cat(interaction: discord.Interaction, name: str, afterlife: app_commands.Choice[str]):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]
        cat["status"] = "dead"
        cat["afterlife"] = afterlife.value
        cat["death_moon"] = data["moon"]
        add_history(cat, f"Died and went to {afterlife.value}")
        save_data(data)

    await interaction.response.send_message(f"💀 {name} has been sent to {afterlife.value}.")

    channel = bot.get_channel(REPORT_CHANNEL_ID)
    if channel:
        await channel.send(f"💀 **Death Announcement**\n{name} has died and now walks in **{afterlife.value}**.")


@bot.tree.command(name="delete", description="Delete a cat permanently")
async def delete_cat(interaction: discord.Interaction, name: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        del data["cats"][name]
        save_data(data)

    await interaction.response.send_message(f"🗑 Deleted {name} permanently.")


@bot.tree.command(name="resetmoon", description="Set moon number and correct ages")
async def resetmoon(interaction: discord.Interaction, moon: int = 4):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        old_moon = data["moon"]
        difference = moon - old_moon
        data["moon"] = moon
        data["season"] = get_current_season()

        for cat in data["cats"].values():
            if cat.get("status") != "dead":
                cat["age"] = max(0, cat.get("age", 0) + difference)

        save_data(data)

    await interaction.response.send_message(f"🌙 Moon set to {moon} and all living ages adjusted by {difference} moons.")


@bot.tree.command(name="advancemoon", description="Advance the moon manually")
async def advance_moon(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer()

    report = await run_moon_update()
    message = await build_clan_report_text(report)

    channel = bot.get_channel(REPORT_CHANNEL_ID)

    if channel:
        await send_long_message(channel, "@everyone 🌙 A moon has been manually advanced...\n\n" + message)

    await interaction.followup.send("🌙 Moon advanced manually.")


@bot.tree.command(name="adddead", description="Add a cat who is already dead")
@app_commands.describe(name="Cat name", age="Age they died at in moons", clan="Clan they belonged to", rank="Rank they died as", afterlife="Where they went after death")
@app_commands.choices(clan=CLAN_CHOICES, rank=RANK_CHOICES, afterlife=AFTERLIFE_CHOICES)
async def adddead(interaction: discord.Interaction, name: str, age: int, clan: app_commands.Choice[str], rank: app_commands.Choice[str], afterlife: app_commands.Choice[str]):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name in data["cats"]:
            await interaction.response.send_message("That cat already exists.", ephemeral=True)
            return

        validation_error = validate_cat_rank(clan.value, rank.value, None)
        if validation_error:
            await interaction.response.send_message(validation_error, ephemeral=True)
            return

        data["cats"][name] = {
            "clan": clan.value,
            "age": age,
            "rank": rank.value,
            "faction": None,
            "status": "dead",
            "afterlife": afterlife.value,
            "death_moon": "Before records",
            "born_moon": None,
            "history": [f"Added to records as deceased. Died as {rank.value} and went to {afterlife.value}."]
        }
        save_data(data)

    await interaction.response.send_message(
        f"💀 Added deceased cat **{name}**\n"
        f"⛺ Clan: {clan.value}\n"
        f"⚔ Rank at death: {rank.value}\n"
        f"🌙 Age at death: {age} moons\n"
        f"🌌 Afterlife: {afterlife.value}"
    )

# ─────────────────────────────
# WEATHER LOOP + WEATHER COMMANDS
# ─────────────────────────────

@tasks.loop(minutes=30)
async def weekly_weather_report():
    now = datetime.now(TZ)

    if now.weekday() != 6 or now.hour != 10:
        return

    this_week = f"{now.year}-W{now.isocalendar().week}"

    async with data_lock:
        if data.get("last_weather_week") == this_week:
            return

        data["last_weather_week"] = this_week
        save_data(data)

    channel = bot.get_channel(WEATHER_CHANNEL_ID)
    if channel:
        report = generate_weekly_weather()
        await channel.send(f"<@&{WEATHER_REPORT_ROLE_ID}>\n\n{report}")


@bot.tree.command(name="weatherreport", description="Generate this week's territory weather report")
async def weatherreport(interaction: discord.Interaction):
    report = generate_weekly_weather()
    await interaction.response.send_message(report[:1900])


@bot.tree.command(name="setweather", description="Manually set this week's weather report")
@app_commands.describe(weather="Weather name, example: Heavy rain", modifier="Hunting modifier, example: -2, 0, 1, 2", reason="Why this weather affects hunting")
async def setweather(interaction: discord.Interaction, weather: str, modifier: int, reason: str):
    if not await staff_command_check(interaction):
        return

    modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)

    report = (
        "🌦️ Manual Territory Weather Update 🌦️\n\n"
        f"☁️ Weather: {weather}\n"
        f"🎯 Hunting Modifier: {modifier_text}\n"
        f"📖 Effect: {reason}"
    )

    channel = bot.get_channel(WEATHER_CHANNEL_ID)
    if channel:
        await channel.send(f"<@&{WEATHER_REPORT_ROLE_ID}>\n\n{report}")

    await interaction.response.send_message("🌦️ Weather report sent.", ephemeral=True)

# ─────────────────────────────
# MONTHLY MOON LOOP
# ─────────────────────────────

@tasks.loop(time=time(hour=0, minute=0, tzinfo=TZ))
async def monthly_moon():
    now = datetime.now(TZ)
    this_month = f"{now.year}-{now.month:02d}"

    async with data_lock:
        if data.get("last_moon_month") == this_month:
            return

        data["last_moon_month"] = this_month
        save_data(data)

    report = await run_moon_update()
    message = await build_clan_report_text(report)

    channel = bot.get_channel(REPORT_CHANNEL_ID)
    if channel:
        await send_long_message(channel, "@everyone 🌙 A new moon has passed across the Clans...\n\n" + message)

# ─────────────────────────────
# PUBLIC COMMANDS
# ─────────────────────────────

@bot.tree.command(name="moon", description="Check the current moon")
async def moon(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🌙 The current moon is **Moon {data.get('moon', 0)}**.\n"
        f"🍃 Current season: **{data.get('season', get_current_season())} ({get_season_moon()}/3)**."
    )


@bot.tree.command(name="clan", description="View one clan or outsider roster")
@app_commands.choices(clan=CLAN_CHOICES)
async def clan(interaction: discord.Interaction, clan: app_commands.Choice[str]):

    selected_clan = clan.value.strip()

    if selected_clan == "Outsider":
        lines = ["🌫 Outsider Roster"]
        rank_order = OUTSIDER_RANK_ORDER
    else:
        lines = [f"⛺ {selected_clan} Roster"]
        rank_order = RANK_ORDER

    clan_cats = [
        (name, cat) for name, cat in data.get("cats", {}).items()
        if str(cat.get("clan", "")).strip() == selected_clan
        and str(cat.get("status", "alive")).lower() != "dead"
    ]

    if not clan_cats:
        await interaction.response.send_message(
            f"No cats found for **{selected_clan}**."
        )
        return

    for rank in rank_order:
        ranked = [
            (name, cat) for name, cat in clan_cats
            if str(cat.get("rank", "")).strip() == rank
        ]

        if not ranked:
            continue

        ranked.sort(key=lambda item: item[1].get("age", 0), reverse=True)
        lines.append(f"\n{rank}:")

        for name, cat in ranked:
            faction = f" | {cat.get('faction')}" if cat.get("faction") else ""
            lines.append(f"• {name} — {cat.get('age', 0)} moons{faction}")

    await interaction.response.send_message("\n".join(lines)[:1900])


@bot.tree.command(name="cats", description="View all living cats")
async def cats(interaction: discord.Interaction):
    living_cats = [
        (name, cat) for name, cat in data.get("cats", {}).items()
        if cat.get("status") != "dead"
    ]

    if not living_cats:
        await interaction.response.send_message("No living cats found.")
        return

    lines = ["🐾 Living Cats"]

    living_cats.sort(key=lambda item: (item[1].get("clan", ""), item[0].lower()))

    for name, cat in living_cats:
        faction = f" | {cat.get('faction')}" if cat.get("faction") else ""
        lines.append(f"• {name} | {cat.get('clan')} | {cat.get('rank')} | {cat.get('age', 0)} moons{faction}")

    await interaction.response.send_message("\n".join(lines)[:1900])


@bot.tree.command(name="catinfo", description="View details about a cat")
async def catinfo(interaction: discord.Interaction, name: str):
    if name not in data.get("cats", {}):
        await interaction.response.send_message("Cat not found.", ephemeral=True)
        return

    cat = data["cats"][name]
    history = cat.get("history", [])
    history_text = "\n".join(history[-10:]) if history else "No history yet."
    faction = cat.get("faction") or "None"
    afterlife = cat.get("afterlife") or "None"

    message = (
        f"🐾 **{name}**\n"
        f"Clan: {cat.get('clan')}\n"
        f"Rank: {cat.get('rank')}\n"
        f"Faction: {faction}\n"
        f"Age: {cat.get('age', 0)} moons\n"
        f"Status: {cat.get('status')}\n"
        f"Afterlife: {afterlife}\n\n"
        f"📜 Recent History:\n{history_text}"
    )

    await interaction.response.send_message(message[:1900])


@bot.tree.command(name="dead", description="View dead cats by clan and afterlife")
@app_commands.describe(clan="Filter by clan", afterlife="Filter by afterlife")
@app_commands.choices(clan=CLAN_FILTER_CHOICES, afterlife=AFTERLIFE_FILTER_CHOICES)
async def dead(interaction: discord.Interaction, clan: app_commands.Choice[str], afterlife: app_commands.Choice[str]):
    dead_cats = []

    for name, cat in data.get("cats", {}).items():
        if cat.get("status") != "dead":
            continue

        if clan.value != "All" and cat.get("clan") != clan.value:
            continue

        if afterlife.value != "All" and cat.get("afterlife") != afterlife.value:
            continue

        dead_cats.append((name, cat))

    if not dead_cats:
        await interaction.response.send_message("No dead cats found.")
        return

    dead_cats.sort(key=lambda item: (item[1].get("clan", ""), item[0].lower()))

    lines = ["💀 Deceased Cats"]

    for name, cat in dead_cats:
        lines.append(
            f"• {name} — {cat.get('clan')} — died as {cat.get('rank')} "
            f"at {cat.get('age', 0)} moons → {cat.get('afterlife')}"
        )

    await interaction.response.send_message("\n".join(lines)[:1900])

# ─────────────────────────────
# RUN BOT
# ─────────────────────────────

keep_alive()
bot.run(TOKEN)
