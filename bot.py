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
COMMAND_CHANNEL_ID = 1503486789900570784
WEATHER_CHANNEL_ID = 1441502516591202394
WEATHER_CHANNEL_ID = 123456789
WEATHER_REPORT_ROLE_ID = 987654321
REPORT_CHANNEL_ID = 1441502516591202394

HELPER_ROLE_ID = 1484027097784516668
MODERATOR_ROLE_ID = 1441506626371715103
WEATHER_REPORT_ROLE_ID = 1500967820194877490
LEADER_ROLE_ID = 1445530932659617994
DEPUTY_ROLE_ID = 1449118789521375312
MEDICINE_CAT_ROLE_ID = 1449118843485032599
MEDICINE_CAT_APPRENTICE_ROLE_ID = 1449118899860672683
HEALER_ROLE_ID = 1449118955418550364

MEDICAL_ROLE_IDS = {
    MEDICINE_CAT_ROLE_ID,
    MEDICINE_CAT_APPRENTICE_ROLE_ID,
    HEALER_ROLE_ID,
    LEADER_ROLE_ID,
    DEPUTY_ROLE_ID,
    HELPER_ROLE_ID,
    MODERATOR_ROLE_ID
}

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

FAMILY_RELATIONS = [
    "Mother",
    "Father",
    "Parent",
    "Non-Bio Mother",
    "Non-Bio Father",
    "Non-Bio Parent",
    "Non-Bio Parental Figure",
    "Sibling",
    "Cousin",
    "Kit",
    "Non-Bio Kit",
    "Grandmother",
    "Grandfather",
    "Grandparent",
    "Grandkit",
    "Other"
]
FAMILY_RELATION_CHOICES = [
    app_commands.Choice(name=relation, value=relation)
    for relation in FAMILY_RELATIONS
]

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
        "used_prophecies": [],
        "last_quest_period": None,
        "used_quests": {},
        "active_quests": {},
        "quest_results": {},
        "question_usage": {},
        "used_questions": []
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

def is_medical_staff(interaction: discord.Interaction):
    if not hasattr(interaction.user, "roles"):
        return False

    user_role_ids = {role.id for role in interaction.user.roles}
    return bool(MEDICAL_ROLE_IDS.intersection(user_role_ids))


MMEDICAL_COMMAND_CHANNEL_ID = 1503486789900570784

async def medical_command_check(interaction: discord.Interaction):
    if not is_medical_staff(interaction):
        await interaction.response.send_message(
            "You do not have permission to use medical commands.",
            ephemeral=True
        )
        return False

    if interaction.channel_id != MEDICAL_COMMAND_CHANNEL_ID:
        await interaction.response.send_message(
            "Use medical commands in the medical channel only.",
            ephemeral=True
        )
        return False

    return True


def days_since_iso(iso_value):
    if not iso_value:
        return None

    try:
        old_time = datetime.fromisoformat(iso_value)
        return (datetime.now(TZ) - old_time).days
    except Exception:
        return None


def recovery_days_needed(severity):
    return max(2, int(severity) * 2)
    
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
    cat.setdefault("status", "Alive")
    cat.setdefault("afterlife", None)
    cat.setdefault("faction", None)
    cat.setdefault("death_moon", None)


def format_history_entry(entry):
    if entry.startswith("Moon "):
        parts = entry.split(": ", 1)

        if len(parts) == 2:
            moon_part, text = parts

            if "Injured/ill:" in text:
                injury_name = text.split("Injured/ill:", 1)[1].split("|", 1)[0].strip()
                return f"**{moon_part}**: Injured/ill: {injury_name} | Recovering"

            if "Recovered from injury/illness:" in text:
                injury_name = text.split("Recovered from injury/illness:", 1)[1].strip()
                return f"**{moon_part}**: Recovered from {injury_name}"

            if "Recovered from injury" in text or "Injury/illness removed" in text:
                return f"**{moon_part}**: Recovered from injury/illness"

            return f"**{moon_part}**: {text}"

    return entry


def severity_label(severity):
    labels = {
        1: "Very Minor",
        2: "Minor",
        3: "Mild",
        4: "Moderate",
        5: "Concerning",
        6: "Serious",
        7: "Severe",
        8: "Critical",
        9: "Life-Threatening",
        10: "Gravely Critical"
    }
    return labels.get(severity, "Unknown")


def format_injury(cat):
    injury = cat.get("injury")

    if not injury:
        return "Healthy"

    severity = int(injury.get("severity", 1))
    label = severity_label(severity)

    return (
        f"{injury.get('type', 'Unknown')} "
        f"| Severity {severity}/10, {label} "
        f"| Moon {injury.get('moon', '?')}"
    )


def is_story_history(entry):
    important_keywords = [
        "Became an Apprentice",
        "Became a Warrior",
        "Retired as an Elder",
        "Rank changed to",
        "Died and went to",
        "Injured/ill",
        "Recovered from injury",
        "Injury/illness removed",
        "Became ",
        "Had a litter",
        "Became mates with",
        "Broke up with",
        "Born to"
    ]

    excluded_keywords = [
        "previous ",
        "previous apprentice",
        "Assigned",
        "Family relation added",
        "Excluded from Cat Tinder",
        "Included in Cat Tinder again"
    ]

    if any(excluded.lower() in entry.lower() for excluded in excluded_keywords):
        return False

    return any(keyword.lower() in entry.lower() for keyword in important_keywords)

def process_injury_recovery(cat):
    injury = cat.get("injury")
    if not injury:
        return False

    severity = int(injury.get("severity", 1))
    last_update = injury.get("last_recovery_update")

    now = datetime.now(TZ)

    if not last_update:
        injury["last_recovery_update"] = now.isoformat()
        return False

    last_time = datetime.fromisoformat(last_update)
    days_passed = (now - last_time).days

    if days_passed < 2:
        return False

    points_down = days_passed // 2
    new_severity = max(0, severity - points_down)

    if new_severity <= 0:
        injury_name = injury.get("type", "injury/illness")
        cat.pop("injury", None)
        add_history(cat, f"Recovered from injury/illness: {injury_name}")

    else:
        injury["severity"] = new_severity
        injury["last_recovery_update"] = now.isoformat()

    return True


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


def add_family_relation(cat, relation, relative_name):
    cat.setdefault("family", {})
    cat["family"].setdefault(relation, [])

    if relative_name not in cat["family"][relation]:
        cat["family"][relation].append(relative_name)


def reciprocal_family_relation(relation):
    opposites = {
        "Mother": "Kit",
        "Father": "Kit",
        "Parent": "Kit",

        "Kit": "Parent",

        "Non-Bio Mother": "Non-Bio Kit",
        "Non-Bio Father": "Non-Bio Kit",
        "Non-Bio Parent": "Non-Bio Kit",
        "Non-Bio Parental Figure": "Non-Bio Kit",

        "Non-Bio Kit": "Non-Bio Parent",

        "Sibling": "Sibling",
        "Cousin": "Cousin",

        "Grandmother": "Grandkit",
        "Grandfather": "Grandkit",
        "Grandparent": "Grandkit",

        "Grandkit": "Grandparent"
    }

    return opposites.get(relation, "Other")

def remove_from_list(cat, key, value):
    if key in cat:
        cat[key] = [item for item in cat[key] if item != value]


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
            and str(cat.get("status", "Alive")).lower() != "dead"
        ]

        if living_leaders:
            continue

        deputies = [
            (name, cat) for name, cat in data["cats"].items()
            if cat.get("clan") == clan
            and cat.get("rank") == "Deputy"
            and str(cat.get("status", "Alive")).lower() != "dead"
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
            and str(cat.get("status", "Alive")).lower() != "dead"
        ]

        if living_meds:
            continue

        med_apps = [
            (name, cat) for name, cat in data["cats"].items()
            if cat.get("clan") == clan
            and cat.get("rank") == "Medicine Cat Apprentice"
            and str(cat.get("status", "Alive")).lower() != "dead"
        ]

        if med_apps:
            name, cat = med_apps[0]
            cat["rank"] = "Medicine Cat"
            add_history(cat, f"Became Medicine Cat of {clan}")
            report["succession"].append(f"🌿 {name} became Medicine Cat of {clan}.")

# ─────────────────────────────
# OC QUESTION SYSTEM
# ─────────────────────────────

OC_QUESTIONS = [
    "What’s your OC’s favourite season?",
    "What’s your OC’s favourite weather?",
    "What’s your OC’s least favourite weather?",
    "What’s your OC’s favourite colour?",
    "What’s your OC’s least favourite colour?",
    "What’s your OC’s favourite flower?",
    "What’s your OC’s favourite smell?",
    "What’s your OC’s least favourite smell?",
    "What’s your OC’s favourite food?",
    "What food would your OC absolutely never eat?",
    "What’s your OC’s favourite dessert?",
    "What’s your OC’s favourite drink?",
    "Would your OC choose coffee, tea, or energy drinks?",
    "What’s your OC’s favourite animal besides cats?",
    "What would your OC’s dream vacation be?",
    "Would your OC prefer mountains, beach, forest, or city?",
    "Is your OC a morning cat or a night owl?",
    "What’s your OC’s biggest pet peeve?",
    "What’s one thing your OC is weirdly good at?",
    "What’s one thing your OC is hilariously bad at?",
    "What would your OC’s laugh sound like?",
    "What emoji represents your OC best?",
    "What’s your OC’s comfort item?",
    "What’s your OC’s favourite movie genre?",
    "What’s your OC’s favourite TV genre?",
    "What’s your OC’s favourite book genre?",
    "What’s your OC’s favourite music genre?",
    "What karaoke song would your OC absolutely destroy?",
    "What would your OC’s signature dance move be?",
    "What would your OC’s ideal birthday party look like?",
    "Does your OC prefer sweet, salty, spicy, or sour?",
    "What’s your OC’s favourite holiday?",
    "What would your OC’s dream job be outside the Clans?",
    "What sport would your OC secretly dominate?",
    "What sport would your OC fail instantly at?",
    "Would your OC rather be famous or rich?",
    "What would your OC’s dream car be?",
    "What would your OC order at a fast food place?",
    "What’s your OC’s favourite ice cream topping?",
    "Is your OC good at keeping secrets?",
    "What’s your OC’s guilty pleasure?",
    "What fashion style would your OC have?",
    "What accessory would your OC always wear?",
    "What’s your OC’s favourite board game?",
    "What video game would your OC obsess over?",
    "What social media app would your OC use most?",
    "Would your OC become an influencer?",
    "What would your OC go viral for?",
    "What’s your OC’s most chaotic trait?",
    "What’s your OC’s most wholesome trait?",
    "Is your OC competitive?",
    "Would your OC survive reality TV?",
    "What reality show would your OC absolutely win?",
    "What would your OC’s dream concert be?",
    "If your OC had a YouTube channel, what would it be about?",
    "What’s your OC’s ideal pizza topping?",
    "Would your OC support pineapple on pizza?",
    "What’s your OC’s favourite snack?",
    "What would your OC name a pet rock?",
    "What’s your OC’s biggest irrational fear?",
    "Would your OC rather fly or be invisible?",
    "If your OC had a superpower, what would it be?",
    "What Hogwarts house would your OC be in?",
    "What mythical creature matches your OC best?",
    "If your OC came with a warning label, what would it say?",
    "What’s your OC’s go-to excuse for being late?",
    "Is your OC the planner or the chaotic friend?",
    "What would your OC’s signature catchphrase be?",
    "What song would play every time your OC entered a room?",
    "What’s your OC’s favourite type of candy?",
    "What would your OC spend way too much money on?",
    "What skill does your OC think they could totally master… but definitely couldn’t?",
    "If your OC opened a business, what would it be?",
    "What’s your OC’s weirdest talent?",
    "If your OC were a meme, which one would they be?",
    "Which OC is most likely to accidentally become president?",
    "Which OC is most likely to join the NHL?",
    "Which OC is most likely to win the X Games?",
    "Which OC is most likely to have a wildly successful K-pop career?",
    "Which OC is most likely to start a cult by accident?",
    "Which OC is most likely to become a billionaire?",
    "Which OC is most likely to get cancelled on social media?",
    "Which OC is most likely to survive a zombie apocalypse?",
    "Which OC is most likely to cause the zombie apocalypse?",
    "Which OC is most likely to become a reality TV star?",
    "Which OC is most likely to get banned from an amusement park?",
    "Which OC is most likely to go viral for something ridiculous?",
    "Which OC is most likely to become a conspiracy theorist?",
    "Which OC is most likely to own 14 pets?",
    "Which OC is most likely to become a famous actor?",
    "Which OC is most likely to become a supervillain?",
    "Which OC is most likely to win a hot dog eating contest?",
    "Which OC is most likely to become a motivational speaker?",
    "Which OC is most likely to get arrested for something stupid?",
    "Which OC is most likely to marry rich?",
    "Which OC is most likely to live in a van by choice?",
    "Which OC is most likely to accidentally set something on fire?",
    "Which OC is most likely to become a meme legend?",
    "Which OC is most likely to survive entirely on snacks?",
    "Which OC is most likely to somehow end up on the news?",
    "What’s your OC’s favourite pizza chain?",
    "What’s your OC’s least favourite chore?",
    "What would your OC binge-watch for 12 hours straight?",
    "What’s your OC’s dream pet?",
    "What’s your OC’s favourite childhood memory?",
    "What is your OC’s worst habit?",
    "What’s your OC’s best habit?",
    "What would your OC do with a million dollars?",
    "What would your OC buy first after winning the lottery?",
    "Would your OC survive camping?",
    "Would your OC survive high school?",
    "What clique would your OC be in?",
    "Would your OC be prom king/queen?",
    "What’s your OC’s favourite amusement park ride?",
    "What ride would terrify your OC?",
    "Would your OC rather skydive or scuba dive?",
    "What’s your OC’s favourite cereal?",
    "What cereal perfectly matches your OC?",
    "What would your OC’s perfume/cologne smell like?",
    "What would your OC’s dating profile bio say?",
    "What’s your OC’s most embarrassing moment?",
    "What would instantly annoy your OC?",
    "What makes your OC cry every time?",
    "What’s your OC’s toxic trait?",
    "What’s your OC’s green flag?",
    "Would your OC thrive in a zombie apocalypse group?",
    "Would your OC betray the group first?",
    "What would your OC’s Starbucks order be?",
    "What aesthetic fits your OC best?",
    "What’s your OC’s favourite mythical beast?",
    "What’s your OC’s least favourite social situation?",
    "Would your OC rather text or call?",
    "Would your OC leave someone on read?",
    "What’s your OC’s favourite app?",
    "What app would your OC absolutely delete forever?",
    "Would your OC survive being famous?",
    "What scandal would your OC get cancelled for?",
    "What’s your OC’s weird food combo?",
    "What would your OC do during a power outage?",
    "Would your OC survive Ikea?",
    "Would your OC cry at weddings?",
    "Would your OC cry at dog videos?",
    "What’s your OC’s favourite conspiracy theory?",
    "What reality dating show would your OC dominate?",
    "Would your OC survive Big Brother?",
    "What’s your OC’s favourite holiday candy?",
    "Would your OC rather ghost someone or be ghosted?",
    "What’s your OC’s comfort movie?",
    "What would your OC name their first child?",
    "What’s your OC’s worst pickup line?",
    "What’s your OC’s best pickup line?",
    "Would your OC own Crocs?",
    "Would your OC wear socks with sandals?",
    "What’s your OC’s dream house?",
    "Would your OC survive living alone?",
    "Would your OC rather live in a mansion or cabin?",
    "What’s your OC’s favourite fast food sauce?",
    "What’s your OC’s weirdest fear?",
    "What’s your OC’s Roman Empire?",
    "What fictional world would your OC thrive in?",
    "What fictional world would destroy your OC?",
    "Would your OC survive The Hunger Games?",
    "Would your OC volunteer as tribute?",
    "What’s your OC’s favourite internet trend?",
    "What trend would your OC absolutely hate?",
    "Would your OC become a TikTok menace?",
    "What’s your OC’s secret talent show act?",
    "What would your OC get famous for on Twitch?",
    "What’s your OC’s dream band name?",
    "What would your OC’s wrestler name be?",
    "What’s your OC’s drag name?",
    "What’s your OC’s villain origin story?",
    "What minor inconvenience would turn your OC evil?",
    "What would your OC do first in Vegas?",
    "Would your OC survive a road trip?",
    "Would your OC be driver, DJ, or menace?",
    "What’s your OC’s dream festival?",
    "What’s your OC’s guilty pleasure song?",
    "What’s your OC’s favourite meme format?",
    "Would your OC win Survivor?",
    "Would your OC get voted off first?",
    "What’s your OC’s go-to prank?",
    "What prank would break your OC?",
    "What’s your OC’s cursed talent?",
    "Would your OC survive retail?",
    "Would your OC ask to speak to the manager?",
    "What would your OC’s autobiography be called?",
    "What would your OC’s TED Talk be about?",
    "What would your OC’s podcast be called?",
    "What’s your OC’s favourite emoji combo?",
    "What’s your OC’s most unhinged opinion?",
    "Which OC is most likely to get abducted by aliens?",
    "What would your OC get banned from?",
    "What would your OC’s warning announcement sound like?",
    "What’s your OC’s ultimate comfort purchase?",
    "What’s your OC’s “hear me out”?",
    "What would your OC’s catchphrase on reality TV be?",
    "What’s your OC’s biggest main character moment?",
    "What’s your OC’s most NPC trait?",
    "Would your OC survive Comic Con?",
    "What cosplay would your OC absolutely commit to?",
    "Would your OC thrive at karaoke night?",
    "What’s your OC’s dream viral tweet?",
    "What would your OC’s mugshot be for?",
    "Would your OC survive working customer service?",
    "What would your OC absolutely rage quit?",
]

@bot.tree.command(name="question", description="Post a silly OC question")
async def question(interaction: discord.Interaction):
    async with data_lock:
        data.setdefault("question_usage", {})
        data.setdefault("used_questions", [])

        today = datetime.now(TZ).date().isoformat()

        usage = data["question_usage"].setdefault(today, 0)

        if usage >= 2:
            await interaction.response.send_message(
                "❌ The OC question command has already been used twice today. Try again tomorrow!",
                ephemeral=True
            )
            return

        available_questions = [
            question for question in OC_QUESTIONS
            if question not in data["used_questions"]
        ]

        if not available_questions:
            data["used_questions"] = []
            available_questions = OC_QUESTIONS.copy()

        chosen_question = random.choice(available_questions)

        data["used_questions"].append(chosen_question)
        data["question_usage"][today] = usage + 1

        save_data(data)

    await interaction.response.send_message(
        f"<@&1503421848329650196> 🌟 **Gather round, mountain cats!** 🌟\n\n"
        f"🐾 **Today’s OC Question:**\n"
        f"**{chosen_question}**\n\n"
        f"💬 Feel free to answer below!"
    )

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

            recovered = process_injury_recovery(cat)

            if recovered:
                if cat.get("injury"):
                    report["promotions"].append(
                        f"🩹 {name}'s injury recovery progressed."
                    )
                else:
                    report["promotions"].append(
                        f"💚 {name} recovered from their injury."
                    )

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            cat["age"] = cat.get("age", 0) + 1

            delay = cat.get("ceremony_delay", 0)
            is_due_for_ceremony = (
                (cat.get("rank") == "Kit" and cat["age"] >= 6)
                or (cat.get("rank") == "Apprentice" and cat["age"] >= 12)
                or (cat.get("rank") in AGING_TO_ELDER_RANKS and cat["age"] >= 95)
            )

            if delay > 0 and is_due_for_ceremony:
                cat["ceremony_delay"] = delay - 1
                add_history(
                    cat,
                    f"Ceremony delayed. {cat['ceremony_delay']} moon(s) remaining"
                )
                report["promotions"].append(
                    f"⏳ {name}'s ceremony was delayed. {cat['ceremony_delay']} moon(s) remaining."
                )
                continue

            if cat.get("rank") == "Kit" and cat["age"] >= 6:
                cat["rank"] = "Apprentice"
                cat.pop("ceremony_delay", None)
                add_history(cat, "Became an Apprentice")
                report["promotions"].append(f"🐾 {name} became an Apprentice.")

            elif cat.get("rank") == "Apprentice" and cat["age"] >= 12:
                old_ = cat.get("")

                if old_:
                    if "(PAST)" not in str(old_):
                        cat[""] = f"{old_mentor} (PAST)"

                    if old_mentor in data["cats"]:
                        mentor_cat = data["cats"][old_mentor]
                        apprentices = mentor_cat.get("apprentices", [])

                        if name in apprentices:
                            apprentices.remove(name)

                        past_apprentices = mentor_cat.setdefault("past_apprentices", [])
                        if name not in past_apprentices:
                            past_apprentices.append(name)

                        add_history(
                            mentor_cat,
                            f"Former apprentice {name} became a Warrior"
                        )

                cat["rank"] = "Warrior"
                cat.pop("ceremony_delay", None)
                add_history(cat, "Became a Warrior")
                report["promotions"].append(f"⚔ {name} became a Warrior.")

            elif cat.get("rank") in AGING_TO_ELDER_RANKS and cat["age"] >= 95:
                cat["rank"] = "Elder"
                cat.pop("ceremony_delay", None)
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
            name: cat
            for name, cat in data.get("cats", {}).items()
            if cat.get("clan") == clan_name
            and str(cat.get("status", "Alive")).lower() != "dead"
        }

        if not clan_cats:
            lines.append("No cats")
            lines.append("")
            continue

        for rank in RANK_ORDER:
            ranked_cats = [
                (name, cat)
                for name, cat in clan_cats.items()
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
        (name, cat)
        for name, cat in data.get("cats", {}).items()
        if cat.get("clan") == "Outsider"
        and str(cat.get("status", "Alive")).lower() != "dead"
    ]

    if outsiders:
        outsiders.sort(key=lambda item: item[1].get("age", 0), reverse=True)

        for name, cat in outsiders:
            faction = f" | {cat.get('faction')}" if cat.get("faction") else ""
            lines.append(
                f"• {name} — {cat.get('rank')} — {cat.get('age', 0)} moons{faction}"
            )
    else:
        lines.append("No outsiders")

    lines.extend(["", "💀 Deaths This Moon"])

    recent_dead = [
        (name, cat)
        for name, cat in data.get("cats", {}).items()
        if str(cat.get("status", "Alive")).lower() == "dead"
        and cat.get("death_moon") == data["moon"]
    ]

    if recent_dead:
        for name, cat in recent_dead:
            lines.append(
                f"• {name} — {cat.get('age', 0)} moons → {cat.get('afterlife')}"
            )
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

    if not biweekly_quest_report.is_running():
        biweekly_quest_report.start()


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

@bot.tree.command(name="addlitter", description="Record that a cat had a litter this moon")
@app_commands.describe(
    mother="Mother cat name",
    kit1="First kit name",
    kit2="Second kit name optional",
    kit3="Third kit name optional",
    kit4="Fourth kit name optional",
    kit5="Fifth kit name optional",
    kit6="Sixth kit name optional"
)
async def add_litter(
    interaction: discord.Interaction,
    mother: str,
    kit1: str,
    kit2: str,
    kit3: str = None,
    kit4: str = None,
    kit5: str = None,
    kit6: str = None
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if mother not in cats:
            await interaction.response.send_message("Mother cat not found.", ephemeral=True)
            return

        kit_names = [name for name in [kit1, kit2, kit3, kit4, kit5, kit6] if name]

        missing_kits = [kit_name for kit_name in kit_names if kit_name not in cats]

        if missing_kits:
            await interaction.response.send_message(
                f"These kits are not in the records yet: {', '.join(missing_kits)}\n"
                f"Add them first with `/add`, then use `/addlitter`.",
                ephemeral=True
            )
            return

        for kit_name in kit_names:
            add_family_relation(cats[mother], "Kit", kit_name)
            add_family_relation(cats[kit_name], "Mother", mother)
            add_history(cats[kit_name], f"Born to {mother}")
        
        litter_text = ", ".join(kit_names)
        add_history(cats[mother], f"Had a litter: {litter_text}")

        save_data(data)

    await interaction.response.send_message(
        f"🍼 Litter recorded for **{mother}**:\n"
        + "\n".join([f"• {kit_name}" for kit_name in kit_names])
    )

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
            if str(cat.get("status", "Alive")).lower() != "dead":
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

# ─────────────────────────────
# /BOTINFO
# ─────────────────────────────

@bot.tree.command(name="botinfo", description="View a full guide to all major bot commands")
async def botinfo(interaction: discord.Interaction):
    message = (
        "📘 **ECHOSTONE MOUNTAIN BOT GUIDE** 📘\n\n"

        "🌙 **Moon / System Commands**\n"
        "`/moon` — View the current moon, season, and clan status\n"
        "`/advancemoon` — Staff only. Manually advances one moon and posts the report\n"
        "`/resetmoon` — Staff only. Resets moon count and adjusts living cat ages\n"
        "`/weatherreport` — Manually post or view this week's weather report\n"
        "`/setweather` — Staff only. Manually set custom weather\n"
        "`/question` — Public command. Posts a random OC question in any channel (max 2 uses per Toronto calendar day)\n\n"

        "📜 **Quest / Gathering Commands**\n"
        "`/quests` — Staff only. Manually post new biweekly quests\n"
        "`/questresult` — Staff only. Mark a Clan or Outsider quest as passed or failed\n"
        "`/gatheringreport [ClanName]` — Generate a Clan-specific report including recent promotions, deaths, injuries, quest results, and major story changes\n\n"

        "🐾 **General Member Commands**\n"
        "`/catinfo [Name]` — View full details about a cat\n"
        "`/cats [Clan]` — View all cats by clan or all clans\n"
        "`/clan [ClanName]` — View one clan roster\n"
        "`/cattinder [Name] [Clan]` — Find age-appropriate romance options\n"
        "`/question` — Random OC question prompt system\n\n"

        "🛠️ **Staff Cat Management**\n"
        "`/cat add` — Add a new living cat\n"
        "`/cat adddead` — Add a dead cat to records\n"
        "`/cat delete` — Permanently delete a cat\n"
        "`/cat rename` — Rename a cat and update all references\n"
        "`/cat rank` — Change rank manually\n"
        "`/cat age` — Set exact age\n"
        "`/cat markdead` — Mark a living cat as dead\n"
        "`/cat delayceremony` — Delay automatic rank-up ceremonies\n"
        "`/cat tinderhide` — Hide/unhide a cat from Cat Tinder\n\n"

        "🩹 **Staff Injury Commands**\n"
        "`/injury add` — Add an injury or illness\n"
        "`/injury remove` — Remove or resolve injury\n"
        "`/injury severity` — Override injury severity\n"
        "`/injury moon` — Change injury moon\n\n"

        "🎓 **Staff Mentor Commands**\n"
        "`/mentor assign` — Assign a mentor to an apprentice\n"
        "`/mentor previous` — Add previous mentor history\n\n"

        "💕 **Staff Relationship Commands**\n"
        "`/relationship mate` — Make two cats mates\n"
        "`/relationship breakup` — Break mates into ex-mates\n"
        "`/relationship family` — Add family relations\n"
        "`/relationship remove` — Remove a specific relationship\n"
        "`/relationship clearhistory` — Remove relationship history between two cats\n"
        "`/relationship removeall` — Remove all relationships from one cat\n\n"

        "🍼 **Litter Command**\n"
        "`/addlitter` — Record kits born to a mother and connect family automatically\n\n"

        "💭 **OC Question System**\n"
        "• `/question` works in any channel\n"
        "• Maximum 2 uses per Toronto calendar day\n"
        "• Pulls randomly from your massive OC question list\n"
        "• Prevents repeats until all questions are used\n"
        "• Includes personality prompts, silly hypotheticals, and “most likely to” questions\n\n"

        "📌 **Important Notes**\n"
        "• Most staff commands only work in the designated bot command channel\n"
        "• Quests automatically post every other Monday at 10 AM\n"
        "• Weather updates post weekly\n"
        "• Moon progression is monthly unless manually advanced\n"
        "• Dead cats cannot be mentored, injured, or appear in Cat Tinder\n"
        "• Cat Tinder excludes dead cats, mates, exes, mentors, family, and hidden cats\n"
        "• Once all OC questions are used, the question list resets automatically\n"
        "• `/catinfo` is your best debugging tool for checking records\n\n"

        "🌟 Tip: If records seem broken, check `/catinfo` first before editing anything."
    )

    await interaction.response.defer(ephemeral=True)

    max_length = 1900
    while message:
        chunk = message[:max_length]
        split_at = chunk.rfind("\n")

        if split_at == -1 or len(message) <= max_length:
            split_at = len(chunk)

        await interaction.followup.send(message[:split_at], ephemeral=True)
        message = message[split_at:].lstrip()

# ─────────────────────────────
# CLEANED STAFF COMMAND GROUPS
# ─────────────────────────────

cat_group = app_commands.Group(name="cat", description="Manage cat records")
injury_group = app_commands.Group(name="injury", description="Manage injuries and illnesses")
mentor_group = app_commands.Group(name="mentor", description="Manage mentors and apprentices")
relationship_group = app_commands.Group(name="relationship", description="Manage relationships")
medical_group = app_commands.Group(name="medical", description="Medicine cat treatment commands")


def cat_is_dead(cat):
    return str(cat.get("status", "Alive")).lower() == "dead"


def cat_is_tinder_hidden(cat):
    return bool(cat.get("exclude_from_tinder", False))


def relationship_blocked(cat, other_name):
    if other_name in cat.get("mates", []):
        return True

    if other_name in cat.get("ex_mates", []):
        return True

    family = cat.get("family", {})
    for relatives in family.values():
        if other_name in relatives:
            return True

    if cat.get("mentor") == other_name:
        return True

    if other_name in cat.get("previous_mentors", []):
        return True

    if other_name in cat.get("apprentices", []):
        return True

    if other_name in cat.get("past_apprentices", []):
        return True

    return False


def remove_relationship_history_between(cat, other_name):
    relationship_keywords = [
        "Became mates with",
        "Broke up with",
        "Family relation added",
        "Removed relationship",
        "Had a litter",
        "Born to",
        "Became mentor to",
        "Assigned",
        "previous mentor",
        "previous apprentice",
        "Love interest",
        "Crush"
    ]

    cat["history"] = [
        entry for entry in cat.get("history", [])
        if not (
            other_name.lower() in entry.lower()
            and any(keyword.lower() in entry.lower() for keyword in relationship_keywords)
        )
    ]

# ─────────────────────────────
# /CAT COMMANDS
# ─────────────────────────────

@cat_group.command(name="add", description="Add a new cat")
@app_commands.describe(
    name="Cat name",
    age="Age in moons",
    clan="Select clan",
    rank="Select rank",
    faction="Optional outsider faction"
)
@app_commands.choices(clan=CLAN_CHOICES, rank=RANK_CHOICES, faction=FACTION_CHOICES)
async def cat_add(
    interaction: discord.Interaction,
    name: str,
    age: int,
    clan: app_commands.Choice[str],
    rank: app_commands.Choice[str],
    faction: app_commands.Choice[str] = None
):
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
            "status": "Alive",
            "afterlife": None,
            "death_moon": None,
            "born_moon": max(0, data["moon"] - age),
            "history": [f"Moon {data['moon']}: Added to records as {rank.value}"],
            "exclude_from_tinder": False
        }

        save_data(data)

    await interaction.response.send_message(
        f"🐾 Added **{name}**\n\n"
        f"⛺ Clan: {clan.value}\n"
        f"⚔ Rank: {rank.value}\n"
        f"🌙 Age: {age} moons"
    )


@cat_group.command(name="age", description="Set a cat's age")
async def cat_age(interaction: discord.Interaction, name: str, age: int):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        data["cats"][name]["age"] = age
        add_history(data["cats"][name], f"Age changed to {age} moons")
        save_data(data)

    await interaction.response.send_message(f"🌙 **{name}** is now **{age} moons** old.")


@cat_group.command(name="rank", description="Change a cat's rank")
@app_commands.describe(name="Cat name", rank="New rank")
@app_commands.choices(rank=RANK_CHOICES)
async def cat_rank(interaction: discord.Interaction, name: str, rank: app_commands.Choice[str]):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]
        old_rank = cat.get("rank")
        old_mentor = cat.get("mentor")

        validation_error = validate_cat_rank(cat.get("clan"), rank.value, cat.get("faction"))
        if validation_error:
            await interaction.response.send_message(validation_error, ephemeral=True)
            return

        cat["rank"] = rank.value

        # If an apprentice becomes a warrior, move mentor to past
        if old_rank == "Apprentice" and rank.value == "Warrior" and old_mentor:
            if "(PAST)" not in str(old_mentor):
                cat["mentor"] = f"{old_mentor} (PAST)"

            if old_mentor in data["cats"]:
                mentor_cat = data["cats"][old_mentor]

                if name in mentor_cat.get("apprentices", []):
                    mentor_cat["apprentices"].remove(name)

                mentor_cat.setdefault("past_apprentices", [])
                if name not in mentor_cat["past_apprentices"]:
                    mentor_cat["past_apprentices"].append(name)

                add_history(mentor_cat, f"Former apprentice {name} became a Warrior")

        add_history(cat, f"Rank changed to {rank.value}")
        save_data(data)

    await interaction.response.send_message(f"⚔ **{name}** is now **{rank.value}**.")

@cat_group.command(name="rename", description="Rename a cat")
@app_commands.describe(old_name="Current name", new_name="New name")
async def cat_rename(interaction: discord.Interaction, old_name: str, new_name: str):
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

        for other_cat in data["cats"].values():
            for key in ["mates", "ex_mates", "apprentices", "past_apprentices", "previous_mentors"]:
                if key in other_cat:
                    other_cat[key] = [new_name if item == old_name else item for item in other_cat[key]]

            if other_cat.get("mentor") == old_name:
                other_cat["mentor"] = new_name

            family = other_cat.get("family", {})
            for relation in family:
                family[relation] = [
                    new_name if relative == old_name else relative
                    for relative in family[relation]
                ]

        save_data(data)

    await interaction.response.send_message(f"✏️ Renamed **{old_name} → {new_name}**")


@cat_group.command(name="markdead", description="Mark a cat as dead")
@app_commands.describe(name="Cat name", afterlife="Afterlife destination")
@app_commands.choices(afterlife=AFTERLIFE_CHOICES)
async def cat_markdead(interaction: discord.Interaction, name: str, afterlife: app_commands.Choice[str]):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]
        cat["status"] = "Dead"
        cat["afterlife"] = afterlife.value
        cat["death_moon"] = data["moon"]
        add_history(cat, f"Died and went to {afterlife.value}")
        save_data(data)

    await interaction.response.send_message(f"💀 **{name}** has been sent to **{afterlife.value}**.")

    channel = bot.get_channel(REPORT_CHANNEL_ID)
    if channel:
        await channel.send(
            f"💀 **Death Announcement**\n"
            f"**{name}** has died and now walks in **{afterlife.value}**."
        )


@cat_group.command(name="adddead", description="Add a cat who is already dead")
@app_commands.describe(
    name="Cat name",
    age="Age they died at in moons",
    clan="Clan they belonged to",
    rank="Rank they died as",
    afterlife="Where they went after death"
)
@app_commands.choices(clan=CLAN_CHOICES, rank=RANK_CHOICES, afterlife=AFTERLIFE_CHOICES)
async def cat_adddead(
    interaction: discord.Interaction,
    name: str,
    age: int,
    clan: app_commands.Choice[str],
    rank: app_commands.Choice[str],
    afterlife: app_commands.Choice[str]
):
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
            "status": "Dead",
            "afterlife": afterlife.value,
            "death_moon": "Before records",
            "born_moon": None,
            "history": [
                f"Moon {data['moon']}: Added to records as deceased. Died as {rank.value} and went to {afterlife.value}."
            ],
            "exclude_from_tinder": True
        }

        save_data(data)

    await interaction.response.send_message(
        f"💀 Added deceased cat **{name}**\n"
        f"⛺ Clan: {clan.value}\n"
        f"⚔ Rank at death: {rank.value}\n"
        f"🌙 Age at death: {age} moons\n"
        f"🌌 Afterlife: {afterlife.value}"
    )


@cat_group.command(name="delete", description="Delete a cat permanently")
async def cat_delete(interaction: discord.Interaction, name: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        for other_name, other_cat in data["cats"].items():
            if other_name == name:
                continue

            if other_cat.get("mentor") == name:
                other_cat["mentor"] = None

            for key in ["previous_mentors", "apprentices", "past_apprentices", "mates", "ex_mates"]:
                if key in other_cat:
                    other_cat[key] = [item for item in other_cat[key] if item != name]

            family = other_cat.get("family", {})
            for relation in family:
                family[relation] = [
                    relative for relative in family[relation]
                    if relative != name
                ]

        del data["cats"][name]
        save_data(data)

    await interaction.response.send_message(
        f"🗑 Deleted **{name}** permanently and removed related records."
    )


@cat_group.command(name="delayceremony", description="Delay a cat's automatic promotion")
@app_commands.describe(name="Cat name", moons="How many moons to delay their ceremony")
async def cat_delayceremony(interaction: discord.Interaction, name: str, moons: int):
    if not await staff_command_check(interaction):
        return

    if moons < 1:
        await interaction.response.send_message("Delay must be at least 1 moon.", ephemeral=True)
        return

    async with data_lock:
        if name not in data.get("cats", {}):
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]

        if cat_is_dead(cat):
            await interaction.response.send_message("Dead cats cannot have ceremonies delayed.", ephemeral=True)
            return

        cat["ceremony_delay"] = moons
        add_history(cat, f"Ceremony delayed by {moons} moon(s)")
        save_data(data)

    await interaction.response.send_message(
        f"⏳ **{name}**'s ceremony has been delayed by **{moons} moon(s)**."
    )


@cat_group.command(name="tinderhide", description="Hide or unhide a cat from Cat Tinder searches")
@app_commands.describe(
    name="Cat name",
    hidden="True hides them. False lets them appear again."
)
async def cat_tinderhide(interaction: discord.Interaction, name: str, hidden: bool):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cats[name]["exclude_from_tinder"] = hidden

        if hidden:
            add_history(cats[name], "Excluded from Cat Tinder")
            message = f"🙈 **{name}** is now hidden from Cat Tinder searches."
        else:
            add_history(cats[name], "Included in Cat Tinder again")
            message = f"💕 **{name}** can now appear in Cat Tinder searches again."

        save_data(data)

    await interaction.response.send_message(message)


# ─────────────────────────────
# /INJURY COMMANDS
# ─────────────────────────────

@injury_group.command(name="add", description="Give a cat an injury or illness")
@app_commands.describe(
    name="Cat name",
    injury="Injury or illness",
    severity="Severity from 1 to 10",
    moon="Moon the injury happened. Leave blank for current moon."
)
async def injury_add(
    interaction: discord.Interaction,
    name: str,
    injury: str,
    severity: int,
    moon: int = None
):
    if not await staff_command_check(interaction):
        return

    if severity < 1 or severity > 10:
        await interaction.response.send_message("Severity must be between 1 and 10.", ephemeral=True)
        return

    async with data_lock:
        if name not in data.get("cats", {}):
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]

        if cat_is_dead(cat):
            await interaction.response.send_message("Dead cats cannot be injured.", ephemeral=True)
            return

        injury_moon = moon if moon is not None else data.get("moon", 0)

        cat["injury"] = {
            "type": injury,
            "severity": severity,
            "moon": injury_moon,
            "last_recovery_update": datetime.now(TZ).isoformat()
        }

        add_history(cat, f"Injured/ill: {injury} | Severity {severity}/10 | Moon {injury_moon}")
        save_data(data)

    await interaction.response.send_message(
        f"🩹 **{name}** now has **{injury}**.\n"
        f"Severity: **{severity}/10, {severity_label(severity)}**\n"
        f"Injury Moon: **Moon {injury_moon}**"
    )


@injury_group.command(name="remove", description="Remove or resolve a cat's injury or illness")
@app_commands.describe(
    name="Cat name",
    mode="Recovered keeps history. Delete removes the injury like it never happened."
)
@app_commands.choices(mode=[
    app_commands.Choice(name="Recovered", value="Recovered"),
    app_commands.Choice(name="Delete", value="Delete")
])
async def injury_remove(
    interaction: discord.Interaction,
    name: str,
    mode: app_commands.Choice[str]
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data.get("cats", {}):
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]

        if not cat.get("injury"):
            await interaction.response.send_message(f"{name} has no injury to remove.", ephemeral=True)
            return

        old_injury = cat["injury"].get("type", "Unknown injury")
        cat.pop("injury", None)

        if mode.value == "Recovered":
            add_history(cat, f"Recovered from injury/illness: {old_injury}")
            response = f"🩹 **{name}** has recovered from **{old_injury}**."
        else:
            cat["history"] = [
                entry for entry in cat.get("history", [])
                if old_injury not in entry
            ]
            response = f"🧹 Deleted **{old_injury}** from **{name}**'s records."

        save_data(data)

    await interaction.response.send_message(response)


@injury_group.command(name="severity", description="Override a cat's injury severity")
async def injury_severity(interaction: discord.Interaction, name: str, severity: int):
    if not await staff_command_check(interaction):
        return

    if severity < 1 or severity > 10:
        await interaction.response.send_message("Severity must be between 1 and 10.", ephemeral=True)
        return

    async with data_lock:
        if name not in data.get("cats", {}):
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]

        if not cat.get("injury"):
            await interaction.response.send_message(f"{name} has no injury to update.", ephemeral=True)
            return

        cat["injury"]["severity"] = severity
        cat["injury"]["last_recovery_update"] = datetime.now(TZ).isoformat()

        add_history(cat, f"Injury severity changed to {severity}/10, {severity_label(severity)}")
        save_data(data)

    await interaction.response.send_message(
        f"🩹 **{name}**'s injury severity is now **{severity}/10, {severity_label(severity)}**."
    )


@injury_group.command(name="moon", description="Change the moon when a cat's injury happened")
async def injury_moon(interaction: discord.Interaction, name: str, moon: int):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data.get("cats", {}):
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]

        if not cat.get("injury"):
            await interaction.response.send_message(f"{name} has no injury to update.", ephemeral=True)
            return

        injury_name = cat["injury"].get("type", "Unknown injury")
        cat["injury"]["moon"] = moon

        # Update the visible injury history entry too
        updated_history = []

        for entry in cat.get("history", []):
            if "Injured/ill:" in entry and injury_name in entry:
                updated_history.append(
                    f"Moon {moon}: Injured/ill: {injury_name} | Severity {cat['injury'].get('severity', '?')}/10 | Moon {moon}"
                )
            elif "Injury moon changed to Moon" in entry:
                continue
            else:
                updated_history.append(entry)

        cat["history"] = updated_history

        save_data(data)

    await interaction.response.send_message(f"🌙 **{name}**'s injury moon is now **Moon {moon}**.")

# ─────────────────────────────
# /MEDICAL COMMANDS
# ─────────────────────────────

@medical_group.command(name="report", description="Show cats who need medical treatment")
@app_commands.describe(clan="Optional clan filter")
@app_commands.choices(clan=CLAN_FILTER_CHOICES)
async def medical_report(
    interaction: discord.Interaction,
    clan: app_commands.Choice[str] = None
):
    if not await medical_command_check(interaction):
        return

    async with data_lock:
        chosen_clan = clan.value if clan else "All"
        lines = ["🩺 **Medical Treatment Report**", ""]

        injured_cats = []

        for name, cat in data.get("cats", {}).items():
            if cat_is_dead(cat):
                continue

            if not cat.get("injury"):
                continue

            if chosen_clan != "All" and cat.get("clan") != chosen_clan:
                continue

            injury = cat["injury"]
            severity = int(injury.get("severity", 1))
            last_treated_days = days_since_iso(injury.get("last_treated"))
            last_recovery_days = days_since_iso(injury.get("last_recovery_update"))

            injured_cats.append((cat.get("clan", "Unknown"), name, cat, severity, last_treated_days, last_recovery_days))

        if not injured_cats:
            await interaction.response.send_message(
                "💚 No cats currently need medical treatment.",
                ephemeral=True
            )
            return

        injured_cats.sort(key=lambda item: (item[0], -item[3], item[1].lower()))

        current_clan = None

        for clan_name, name, cat, severity, last_treated_days, last_recovery_days in injured_cats:
            injury = cat["injury"]

            if clan_name != current_clan:
                current_clan = clan_name
                lines.append(f"⛺ **{clan_name}**")

            treatment_status = injury.get("care_status", "Needs Care")

            if last_treated_days is None:
                treated_text = "Not treated yet"
            elif last_treated_days == 0:
                treated_text = "Treated today"
            else:
                treated_text = f"Last treated {last_treated_days} day(s) ago"

            lines.append(
                f"**Name:** {name} — {injury.get('type', 'Unknown')}\n"
                f"**Severity:** {severity}/10, {severity_label(severity)}\n"
                f"**Status:** {treatment_status}\n"
                f"**Care:** {treated_text}\n"
            )

        message = "\n".join(lines)

    await interaction.response.send_message("🩺 Medical report posted.", ephemeral=True)

    channel = interaction.channel
    await send_long_message(channel, message)


@medical_group.command(name="treat", description="Mark that a cat received medical care")
@app_commands.describe(
    name="Cat name",
    status="Choose whether the cat is still recovering or fully recovered",
    notes="Optional treatment notes"
)
@app_commands.choices(status=[
    app_commands.Choice(name="Recovering", value="Recovering"),
    app_commands.Choice(name="Recovered", value="Recovered")
])
async def medical_treat(
    interaction: discord.Interaction,
    name: str,
    status: app_commands.Choice[str],
    notes: str = None
):
    if not await medical_command_check(interaction):
        return

    async with data_lock:
        if name not in data.get("cats", {}):
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]

        if cat_is_dead(cat):
            await interaction.response.send_message("Dead cats cannot receive medical treatment.", ephemeral=True)
            return

        if not cat.get("injury"):
            await interaction.response.send_message(f"**{name}** has no current injury or illness.", ephemeral=True)
            return

        injury = cat["injury"]
        injury_name = injury.get("type", "injury/illness")
        now_iso = datetime.now(TZ).isoformat()

        if status.value == "Recovered":
            cat.pop("injury", None)

            history_text = f"Recovered from injury/illness: {injury_name}"
            if notes:
                history_text += f" | Treatment notes: {notes}"

            add_history(cat, history_text)
            response = f"💚 **{name}** has recovered from **{injury_name}**."

        else:
            injury["care_status"] = "Recovering"
            injury["last_treated"] = now_iso
            injury["last_recovery_update"] = now_iso

            history_text = f"Received medical care for {injury_name}. Still recovering"
            if notes:
                history_text += f" | Notes: {notes}"

            add_history(cat, history_text)
            response = f"🩹 **{name}** received care for **{injury_name}** and is still recovering."

        save_data(data)

    await interaction.response.send_message(response)


# ─────────────────────────────
# /MENTOR COMMANDS
# ─────────────────────────────

def remove_mentor_history_between(cat, other_name):
    mentor_keywords = [
        "Assigned",
        "as mentor",
        "Became mentor to",
        "added as a previous mentor",
        "added as a previous apprentice",
        "Former apprentice"
    ]

    cat["history"] = [
        entry for entry in cat.get("history", [])
        if not (
            other_name.lower() in entry.lower()
            and any(keyword.lower() in entry.lower() for keyword in mentor_keywords)
        )
    ]


@mentor_group.command(name="assign", description="Assign a mentor to an apprentice")
async def mentor_assign(interaction: discord.Interaction, apprentice: str, mentor: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if apprentice not in cats:
            await interaction.response.send_message("Apprentice not found.", ephemeral=True)
            return

        if mentor not in cats:
            await interaction.response.send_message("Mentor not found.", ephemeral=True)
            return

        app_cat = cats[apprentice]
        mentor_cat = cats[mentor]

        if cat_is_dead(app_cat) or cat_is_dead(mentor_cat):
            await interaction.response.send_message("Dead cats cannot be assigned as mentors/apprentices.", ephemeral=True)
            return

        if app_cat.get("rank") not in ["Apprentice", "Medicine Cat Apprentice"]:
            await interaction.response.send_message(f"{apprentice} is not an apprentice.", ephemeral=True)
            return

        valid_mentor_ranks = [
            "Warrior",
            "Leader",
            "Deputy",
            "Medicine Cat",
            "Preymaster",
            "Healer",
            "Digger",
            "Pathfinder",
            "Sporekeeper",
            "River Guardian"
        ]

        if mentor_cat.get("rank") not in valid_mentor_ranks:
            await interaction.response.send_message(f"{mentor} cannot mentor apprentices.", ephemeral=True)
            return

        old_mentor = app_cat.get("mentor")

        if old_mentor:
            clean_old_mentor = str(old_mentor).replace(" (PAST)", "").strip()

            if clean_old_mentor in cats:
                old_mentor_cat = cats[clean_old_mentor]

                remove_from_list(old_mentor_cat, "apprentices", apprentice)

                old_mentor_cat.setdefault("past_apprentices", [])
                if apprentice not in old_mentor_cat["past_apprentices"]:
                    old_mentor_cat["past_apprentices"].append(apprentice)

                app_cat.setdefault("previous_mentors", [])
                if clean_old_mentor not in app_cat["previous_mentors"]:
                    app_cat["previous_mentors"].append(clean_old_mentor)

        app_cat["mentor"] = mentor

        mentor_cat.setdefault("apprentices", [])
        if apprentice not in mentor_cat["apprentices"]:
            mentor_cat["apprentices"].append(apprentice)

        add_history(app_cat, f"Assigned {mentor} as mentor")
        add_history(mentor_cat, f"Became mentor to {apprentice}")

        save_data(data)

    await interaction.response.send_message(f"🐾 **{mentor}** is now mentoring **{apprentice}**.")


@mentor_group.command(name="previous", description="Add a previous mentor to a cat")
async def mentor_previous(interaction: discord.Interaction, name: str, mentor: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        if mentor not in cats:
            await interaction.response.send_message("Mentor not found.", ephemeral=True)
            return

        cat = cats[name]
        mentor_cat = cats[mentor]

        cat.setdefault("previous_mentors", [])
        if mentor not in cat["previous_mentors"]:
            cat["previous_mentors"].append(mentor)

        mentor_cat.setdefault("past_apprentices", [])
        if name not in mentor_cat["past_apprentices"]:
            mentor_cat["past_apprentices"].append(name)

        add_history(cat, f"{mentor} added as a previous mentor")
        add_history(mentor_cat, f"{name} added as a previous apprentice")

        save_data(data)

    await interaction.response.send_message(
        f"🐾 **{mentor}** is now listed as **{name}**'s previous mentor."
    )


@mentor_group.command(name="remove", description="Remove mentor records between two cats without showing in history")
async def mentor_remove(interaction: discord.Interaction, apprentice: str, mentor: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if apprentice not in cats:
            await interaction.response.send_message("Apprentice/cat not found.", ephemeral=True)
            return

        if mentor not in cats:
            await interaction.response.send_message("Mentor not found.", ephemeral=True)
            return

        app_cat = cats[apprentice]
        mentor_cat = cats[mentor]

        # Remove current mentor from apprentice
        current_mentor = app_cat.get("mentor")
        if current_mentor:
            clean_current_mentor = str(current_mentor).replace(" (PAST)", "").strip()
            if clean_current_mentor.lower() == mentor.lower():
                app_cat.pop("mentor", None)

        # Remove mentor from apprentice's past mentor lists
        remove_from_list(app_cat, "previous_mentors", mentor)

        # Also clean exact PAST version if it exists in list by mistake
        remove_from_list(app_cat, "previous_mentors", f"{mentor} (PAST)")

        # Remove apprentice from mentor's lists
        remove_from_list(mentor_cat, "apprentices", apprentice)
        remove_from_list(mentor_cat, "past_apprentices", apprentice)

        # Remove old mentor history from both cats
        remove_mentor_history_between(app_cat, mentor)
        remove_mentor_history_between(mentor_cat, apprentice)

        save_data(data)

    await interaction.response.send_message(
        f"🧹 Removed mentor records between **{apprentice}** and **{mentor}**."
    )


# ─────────────────────────────
# /RELATIONSHIP COMMANDS
# ─────────────────────────────

@relationship_group.command(name="mate", description="Set two cats as mates")
async def relationship_mate(interaction: discord.Interaction, cat1: str, cat2: str):
    if not await staff_command_check(interaction):
        return

    if cat1 == cat2:
        await interaction.response.send_message("A cat cannot be mates with themselves.", ephemeral=True)
        return

    async with data_lock:
        cats = data.get("cats", {})

        if cat1 not in cats:
            await interaction.response.send_message("First cat not found.", ephemeral=True)
            return

        if cat2 not in cats:
            await interaction.response.send_message("Second cat not found.", ephemeral=True)
            return

        cats[cat1].setdefault("mates", [])
        cats[cat2].setdefault("mates", [])

        if cat2 not in cats[cat1]["mates"]:
            cats[cat1]["mates"].append(cat2)

        if cat1 not in cats[cat2]["mates"]:
            cats[cat2]["mates"].append(cat1)

        remove_from_list(cats[cat1], "ex_mates", cat2)
        remove_from_list(cats[cat2], "ex_mates", cat1)

        add_history(cats[cat1], f"Became mates with {cat2}")
        add_history(cats[cat2], f"Became mates with {cat1}")

        save_data(data)

    await interaction.response.send_message(f"💕 **{cat1}** and **{cat2}** are now mates.")


@relationship_group.command(name="breakup", description="Break up two mates and mark them as ex-mates")
async def relationship_breakup(interaction: discord.Interaction, cat1: str, cat2: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if cat1 not in cats:
            await interaction.response.send_message("First cat not found.", ephemeral=True)
            return

        if cat2 not in cats:
            await interaction.response.send_message("Second cat not found.", ephemeral=True)
            return

        remove_from_list(cats[cat1], "mates", cat2)
        remove_from_list(cats[cat2], "mates", cat1)

        cats[cat1].setdefault("ex_mates", [])
        cats[cat2].setdefault("ex_mates", [])

        if cat2 not in cats[cat1]["ex_mates"]:
            cats[cat1]["ex_mates"].append(cat2)

        if cat1 not in cats[cat2]["ex_mates"]:
            cats[cat2]["ex_mates"].append(cat1)

        add_history(cats[cat1], f"Broke up with {cat2}")
        add_history(cats[cat2], f"Broke up with {cat1}")

        save_data(data)

    await interaction.response.send_message(f"💔 **{cat1}** and **{cat2}** are now ex-mates.")


@relationship_group.command(name="family", description="Add a family relation between two cats")
@app_commands.describe(
    name="First cat",
    relation="How the second cat is related to the first cat",
    relative="Second cat",
    custom_relation="Only use this if relation is Other. Example: Uncle",
    custom_reverse_relation="Only use this if relation is Other. Example: Nephew"
)
@app_commands.choices(relation=FAMILY_RELATION_CHOICES)
async def relationship_family(
    interaction: discord.Interaction,
    name: str,
    relation: app_commands.Choice[str],
    relative: str,
    custom_relation: str = None,
    custom_reverse_relation: str = None
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if name not in cats:
            await interaction.response.send_message("First cat not found.", ephemeral=True)
            return

        if relative not in cats:
            await interaction.response.send_message("Second cat not found.", ephemeral=True)
            return

        relation_value = relation.value

        if relation_value == "Other":
            if not custom_relation or not custom_reverse_relation:
                await interaction.response.send_message(
                    "When using Other, please fill in both custom_relation and custom_reverse_relation.\n"
                    "Example: Rabbitpaw → Uncle: Sher, Sher → Nephew: Rabbitpaw",
                    ephemeral=True
                )
                return

            relation_value = custom_relation.strip()
            reverse_relation = custom_reverse_relation.strip()
        else:
            reverse_relation = reciprocal_family_relation(relation_value)

        add_family_relation(cats[name], relation_value, relative)
        add_family_relation(cats[relative], reverse_relation, name)

        add_history(cats[name], f"Family relation added: {relative} as {relation_value}")
        add_history(cats[relative], f"Family relation added: {name} as {reverse_relation}")

        save_data(data)

    await interaction.response.send_message(
        f"👪 Family relation added:\n"
        f"**{name}** → {relation_value}: **{relative}**\n"
        f"**{relative}** → {reverse_relation}: **{name}**"
    )


@relationship_group.command(name="remove", description="Remove a relationship between two cats by typing the relationship name")
@app_commands.describe(
    cat1="First cat",
    relation="Relationship type to remove, example: Mother, Nephew, Grandparent, Other",
    cat2="Second cat"
)
async def relationship_remove(
    interaction: discord.Interaction,
    cat1: str,
    relation: str,
    cat2: str
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if cat1 not in cats:
            await interaction.response.send_message("First cat not found.", ephemeral=True)
            return

        if cat2 not in cats:
            await interaction.response.send_message("Second cat not found.", ephemeral=True)
            return

        relation_value = relation.strip()

        if relation_value.lower() in ["mate", "mates"]:
            remove_from_list(cats[cat1], "mates", cat2)
            remove_from_list(cats[cat2], "mates", cat1)

        elif relation_value.lower() in ["ex-mate", "ex mate", "ex-mates", "ex mates"]:
            remove_from_list(cats[cat1], "ex_mates", cat2)
            remove_from_list(cats[cat2], "ex_mates", cat1)

        else:
            family1 = cats[cat1].get("family", {})
            for saved_relation in list(family1.keys()):
                if saved_relation.lower() == relation_value.lower():
                    family1[saved_relation] = [
                        relative for relative in family1[saved_relation]
                        if relative != cat2
                    ]

                    if not family1[saved_relation]:
                        del family1[saved_relation]

            family2 = cats[cat2].get("family", {})
            for saved_relation in list(family2.keys()):
                family2[saved_relation] = [
                    relative for relative in family2[saved_relation]
                    if relative != cat1
                ]

                if not family2[saved_relation]:
                    del family2[saved_relation]

        add_history(cats[cat1], f"Removed relationship with {cat2}: {relation_value}")
        add_history(cats[cat2], f"Removed relationship with {cat1}: {relation_value}")

        save_data(data)

    await interaction.response.send_message(
        f"🧹 Removed **{relation_value}** relationship between **{cat1}** and **{cat2}**."
    )


@relationship_group.command(name="clearhistory", description="Clear relationship history between two cats")
async def relationship_clearhistory(interaction: discord.Interaction, cat1: str, cat2: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if cat1 not in cats:
            await interaction.response.send_message("First cat not found.", ephemeral=True)
            return

        if cat2 not in cats:
            await interaction.response.send_message("Second cat not found.", ephemeral=True)
            return

        remove_relationship_history_between(cats[cat1], cat2)
        remove_relationship_history_between(cats[cat2], cat1)

        save_data(data)

    await interaction.response.send_message(
        f"🧹 Cleared relationship history between **{cat1}** and **{cat2}**."
    )


@relationship_group.command(name="removeall", description="Remove all relationship records from one cat")
async def relationship_removeall(interaction: discord.Interaction, name: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        target_cat = cats[name]

        for other_name, other_cat in cats.items():
            if other_name == name:
                continue

            remove_from_list(other_cat, "mates", name)
            remove_from_list(other_cat, "ex_mates", name)
            remove_from_list(other_cat, "apprentices", name)
            remove_from_list(other_cat, "past_apprentices", name)
            remove_from_list(other_cat, "previous_mentors", name)

            if other_cat.get("mentor") == name:
                other_cat["mentor"] = None

            family = other_cat.get("family", {})
            for relation in list(family.keys()):
                family[relation] = [
                    relative for relative in family[relation]
                    if relative != name
                ]

                if not family[relation]:
                    del family[relation]

        target_cat.pop("mates", None)
        target_cat.pop("ex_mates", None)
        target_cat.pop("mentor", None)
        target_cat.pop("apprentices", None)
        target_cat.pop("past_apprentices", None)
        target_cat.pop("previous_mentors", None)
        target_cat.pop("family", None)

        add_history(target_cat, "All relationship records removed")

        save_data(data)

    await interaction.response.send_message(
        f"🧹 Removed all relationship records for **{name}**."
    )
# ─────────────────────────────
# CLEANED CAT TINDER
# ─────────────────────────────

@bot.tree.command(name="cattinder", description="Find age-appropriate romance options for a cat")
@app_commands.describe(
    name="Your cat's name",
    clan="Choose a Clan to search, or All"
)
@app_commands.choices(clan=CLAN_FILTER_CHOICES)
async def cattinder(interaction: discord.Interaction, name: str, clan: app_commands.Choice[str]):
    cats = data.get("cats", {})

    if name not in cats:
        await interaction.response.send_message("Cat not found.", ephemeral=True)
        return

    seeker = cats[name]

    if cat_is_dead(seeker):
        await interaction.response.send_message("Dead cats cannot use Cat Tinder.", ephemeral=True)
        return

    if cat_is_tinder_hidden(seeker):
        await interaction.response.send_message("This cat is hidden from Cat Tinder.", ephemeral=True)
        return

    if seeker.get("mates"):
        await interaction.response.send_message("Cats who already have mates cannot use Cat Tinder.", ephemeral=True)
        return

    seeker_age = int(seeker.get("age", 0))
    seeker_rank = seeker.get("rank", "Unknown")
    selected_clan = clan.value

    if seeker_age < 6:
        await interaction.response.send_message(
            "Cats under 6 moons are too young for Cat Tinder.",
            ephemeral=True
        )
        return

    childhood_crushes = []
    love_interests = []
    mate_options = []

    def get_match_type(seeker_age, other_age):
        if other_age < 6:
            return None

        # 6–11 moons: childhood crushes only, within 4 moons
        if 6 <= seeker_age <= 11:
            if 6 <= other_age <= 11 and abs(seeker_age - other_age) <= 4:
                return "childhood"
            return None

        # 12–14 moons: crushes/love interests from 10–18 moons
        if 12 <= seeker_age <= 14:
            if 10 <= other_age <= 18:
                return "love"
            return None

        # 15–17 moons: love interests/crushes, 4 younger to 6 older
        if 15 <= seeker_age <= 17:
            if seeker_age - 4 <= other_age <= seeker_age + 6:
                return "love"
            return None

        # 18–24 moons: love interests up to 6 younger, mates up to 12 older
        if 18 <= seeker_age <= 24:
            if seeker_age - 6 <= other_age < 18:
                return "love"

            if other_age >= 18 and seeker_age - 6 <= other_age <= seeker_age + 12:
                return "mate"

            return None

        # 25–36 moons: any 18+ cat up to 12 moons older
        if 25 <= seeker_age <= 36:
            if other_age >= 18 and other_age <= seeker_age + 12:
                return "mate"
            return None

        # 37–53 moons: any 18+ cat within 18 moons older or younger
        if 37 <= seeker_age <= 53:
            if other_age >= 18 and seeker_age - 18 <= other_age <= seeker_age + 18:
                return "mate"
            return None

        # 54+ moons: 18 moons younger to 24 moons older
        if seeker_age >= 54:
            if other_age >= 18 and seeker_age - 18 <= other_age <= seeker_age + 24:
                return "mate"
            return None

        return None

    for other_name, other_cat in cats.items():
        if other_name == name:
            continue

        if cat_is_dead(other_cat):
            continue

        if cat_is_tinder_hidden(other_cat):
            continue

        if other_cat.get("mates"):
            continue

        if selected_clan != "All" and other_cat.get("clan") != selected_clan:
            continue

        if other_cat.get("rank") == "Medicine Cat Apprentice":
            continue

        if relationship_blocked(seeker, other_name):
            continue

        if relationship_blocked(other_cat, name):
            continue

        other_age = int(other_cat.get("age", 0))
        match_type = get_match_type(seeker_age, other_age)

        if not match_type:
            continue

        line = f"• **{other_name}** — {other_age} moons | {other_cat.get('clan')} | {other_cat.get('rank')}"

        if match_type == "childhood":
            childhood_crushes.append(line)
        elif match_type == "love":
            love_interests.append(line)
        elif match_type == "mate":
            mate_options.append(line)

    childhood_crushes = list(dict.fromkeys(childhood_crushes))
    love_interests = list(dict.fromkeys(love_interests))
    mate_options = list(dict.fromkeys(mate_options))

    childhood_crushes.sort(key=lambda item: int(item.split("— ")[1].split(" moons")[0]))
    love_interests.sort(key=lambda item: int(item.split("— ")[1].split(" moons")[0]))
    mate_options.sort(key=lambda item: int(item.split("— ")[1].split(" moons")[0]))

    lines = [
        f"💕 Cat Tinder for **{name}**",
        f"Age: **{seeker_age} moons**",
        f"Rank: **{seeker_rank}**",
        f"Searching: **{selected_clan}**",
        "",
        "Dead cats, cats with mates, family members, blocked relationships, hidden cats, and Medicine Cat Apprentices are excluded.",
        ""
    ]

    if childhood_crushes:
        lines.append("**Childhood Crushes Only**")
        lines.extend(childhood_crushes)
        lines.append("")

    if love_interests:
        lines.append("**Love Interests / Crushes Only**")
        lines.extend(love_interests)
        lines.append("")

    if mate_options:
        lines.append("**Mate / Love Interest Options**")
        lines.extend(mate_options)
        lines.append("")

    if not childhood_crushes and not love_interests and not mate_options:
        lines.append("No compatible matches found.")

    full_message = "\n".join(lines)

    chunks = []
    max_length = 1900

    while len(full_message) > max_length:
        split_at = full_message.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(full_message[:split_at])
        full_message = full_message[split_at:].lstrip()

    chunks.append(full_message)

    await interaction.response.send_message(chunks[0])

    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


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
        await channel.send(
            content=f"<@&{WEATHER_REPORT_ROLE_ID}>",
            embed=discord.Embed(
                description=report,
                color=discord.Color.blue()
            )
        )

# ─────────────────────────────
# QUEST SYSTEM
# ─────────────────────────────

ROLEPLAY_ANNOUNCEMENTS_ROLE_ID = 1442996267470033026
QUEST_CHANNEL_ID = 1441502516591202394

# ─────────────────────────────
# QUEST DATABASE
# ─────────────────────────────

QUEST_TEXT = """
BLIZZARDCLAN

**Whitecough Outbreak**
A brutal mountain chill has swept through the Hollow of Teeth, and harsh coughs are beginning to echo beneath the Frozen Teeth. Roll a D4 for each BlizzardClan cat: 1-2 = sick, 3-4 = healthy. If sick, roll a D6 for severity. If your initial D4 roll was a 1, add +1 to severity. Severity: 1 = Very Minor, 2-3 = Mild, 4-5 = Moderate, 6-7 = Serious. Medicine cats must treat the sick before whitecough tightens its icy grip. Remember: no OC will ever be killed without your permission.

**Catch 5 Snowshoe Hares**
Fresh tracks streak across Cloud Plateau! BlizzardClan has 2 real-life weeks to catch 5 snowshoe hares before they vanish deeper into the snowfields.

**Catch 10 Frost Tunnel Mice**
The tunnels are practically squeaking with prey. Hunt 10 mice from Frost Tunnels before they scatter through the ice cracks.

**Ptarmigan Patrol**
A sharp-eyed patrol has spotted a hardy flock of ptarmigan scratching through the snowdrifts near Glacier’s Edge. BlizzardClan must catch 4 before the next mountain storm sends them skyward.

**Young Cats Demand Storytime**
BlizzardClan’s kits and Apprentices are bouncing off icy den walls. A warrior or elder must gather them for a night of snowy legends and mountain myths before camp descends into adorable chaos.

**Frozen Falls Reflection**
The sacred Frozen Falls are glowing strangely beneath the moonlight, their icy spray shimmering like StarClan itself. At least 3 cats must journey there for a spiritual vigil and seek wisdom from the mountain.

**Catch 3 Marmots**
Chunky marmots have been spotted basking on rare sun-warmed stones near Glacier’s Edge. Catch 3 before they retreat into deep burrows and deny the Clan a hearty feast.

**Lost in the Whiteout**
A sudden snow squall has separated a young apprentice from their patrol! BlizzardClan must organize a rescue mission and brave blinding winds to guide them safely home.

**Avalanche Scare (Rare Event)**
The mountain groans ominously, and heavy snow shifts dangerously above Glacier’s Edge. Any cat traveling there must roll D20. Roll 1 = caught in a minor avalanche and injured.

**Catch 6 Pikas**
The warriors are craving the fresh meat of Pikas. Catch 6 pikas before they vanish deeper into BlizzardClan’s icy terrain and boost Blizzardclan’s Morale!
**Snow Shelter Night**
The wind is merciless this moon, and every BlizzardClan cat must prove their resilience. Spend one roleplay setting up a temporary camp and sleeping beyond camp’s icy shelter to honour your Clan’s strength.

**Catch 5 Voles**
Fresh burrows beneath powdery snow have revealed a surge of vole activity. Hunt 5 before the prey disappears beneath the frost.

**Frost Tunnel Herb Patrol**
Rumours of hardy winter herbs hidden in the frozen dark have reached camp. Lead a brave herb patrol into Frost Tunnels and return before the cave’s dangers close in.

**Catch 10 Shrews**
The snowbanks are rustling with tiny prey. BlizzardClan must catch 10 shrews to keep the fresh-kill pile strong through bitter nights.
**Cloud Plateau Bonding Night**
For one peaceful evening, BlizzardClan cats are encouraged to set aside duty and gather beneath the stars of Cloud Plateau. Friendships, confessions, and snowy bonds await.

**Catch 4 Ptarmigan**
Another flock has landed high among BlizzardClan’s peaks. Catch 4 before they blend once more into the endless white.
**Frostbite Check**
The frost bites hard this moon. Roll D4 for each elder: 1 = frostbite scare, requiring warmth and care from Clanmates. (this one only do if the season is Leaf-Bare)

**Night Hunting Patrol**
Under silver moonlight, prey moves differently across snow and ice. Lead a patrol into the darkness and prove BlizzardClan’s senses are as sharp as winter itself. No matter what, this patrol’s rolls will have a -3 to every roll.

**Catch 2 Snowshoe Hares Without Injury**
These hares are swift, clever, and desperate. Catch 2 cleanly without any patrol injuries to prove true hunting precision.

**Frozen Stream Crossing**
A vital ice crossing has become dangerously slick. BlizzardClan cats must roleplay safely navigating the frozen stream before prey routes are lost. (Roll D4, 1-2 means a -1 on your hunting rolls at Glacier's edge, 3 means no modifier and 4 means +1 to your rolls)

**Catch 5 Mice**
The Frost Tunnels are bustling once more. Hunt 5 mice before tunnel predators claim them first.

**Campwide Story Night**
The storm howls outside, but BlizzardClan gathers beneath the Frozen Teeth for warmth, stories, and shared history. A Clan that survives together stays together.

**Tunnel Echo Investigation**
Strange whispers and unnatural echoes have been reported deep in Frost Tunnels. Is it only shifting ice... or something more? Investigate carefully.

**Catch 3 Red Squirrels**
Rare flashes of fiery red have been spotted against BlizzardClan’s snowy terrain. Catch 3 red squirrels before they flee to lower forests.

**Blizzard Endurance Race**
Who is truly BlizzardClan’s swiftest warrior? Race across Cloud Plateau’s icy stretches and prove your stamina. (Roll a D8, the highest roll wins, in case of a tie, roll again!)

**Sacred Dream Visit**
StarClan’s whispers seem louder near Frozen Falls this moon. Spend one roleplay night seeking visions, omens, or ancient guidance.

**Catch 8 Pikas**
The mountain cracks are alive with movement. BlizzardClan must catch 8 pikas before prey grows scarce again.

**Apprentice Blizzard Test**
Every apprentice must one day prove they can survive where others freeze. Complete a BlizzardClan endurance or hunting trial. (Roll a D8, the highest roll wins, in case of a tie, roll again!)

**Snow Den Building**
Heavy storms are forecasted. BlizzardClan must work together to reinforce shelters for safety beyond camp.

**Great Blizzard Feast**
The mountain offers prey, but only for the prepared. BlizzardClan has 2 real-life weeks to catch 20 total prey and prove they are the true rulers of ice and stone.

TORRENTCLAN
**Flood on the Island**
Relentless rain and swelling tides have begun to swallow parts of TorrentClan’s island home. Water creeps dangerously close to dens, and every paw is needed. At least 3 cats must roleplay helping move kits, elders, and supplies to safety before the tide rises further.

**Catch 10 Catfish**
The muddy depths of Reedmarsh are stirring with whiskered giants! TorrentClan has 2 real-life weeks to catch 10 catfish before shifting currents send them into deeper, murkier waters.

**Catch 8 Minnows**
Glistening Pools are flashing silver beneath the sun, packed with darting schools of minnows. Catch 8 before they scatter into reeds and roots.

**Kits Demand Beach Storytime**
TorrentClan’s kits are absolutely refusing to settle down unless someone takes them to Sunspirit Sands for a proper beachside story. A warrior or elder must answer the call before sleepy chaos turns into sandy rebellion.

**Lead a Marsh Herb Patrol**
Recent rains have caused Reedmarsh to bloom with medicinal opportunity. The medicine cat needs brave escorts willing to brave mud, reeds, and hidden water channels to gather what the marsh offers.

**Otter Scare**
Something sleek and mischievous has been slipping through TorrentClan waters! During fishing patrols, roll a D8. Roll 1-2 = an otter steals your hard-earned prey and vanishes downstream.

**Catch 5 Walleye**
Deep shadows move beneath Reedmarsh’s murkier waters. Catch 5 walleye before they retreat to the hidden depths.

**Duckling Rescue**
A sudden shift in tide has separated several ducklings from their mother near Trout Run. Will TorrentClan guide the little fluffballs back to safety... or let nature take its course?

**Mud Fever Check**
Too much time in soggy marshland may come with consequences... Roll a D4 for your cat. 1-2 = Mud Fever symptoms, 3-4 = healthy and muddy.

**Catch 4 Ducks**
A flock of plump ducks has been paddling a little too boldly near camp. TorrentClan must remind them whose waters these are.

**Sunspirit Sands Celebration**
Golden sand, warm breezes, and sparkling waves call to TorrentClan! Gather for a celebration of stories, sunning, and seaside joy.

**Catch 6 Perch**
Trout Run is alive with darting silver prey this moon. Catch 6 perch before stronger currents carry them away.

**Stormy Swim Challenge**
Dark clouds gather overhead, but TorrentClan does not fear rough water. Brave cats may challenge themselves to a storm swim and prove their river-born strength.

**Medicine Willow Escort**
The sacred willow roots must be reached, and the medicine cat cannot travel alone. Escort them safely through rising tides and slick crossings. Travel to the Glistening Pools, roll a d8 for success. 1-2 means you slip and get injured, 3+ = safe travels. Roll a D4 for severity.

**Catch 3 Catfish in One Patrol**
The marsh is thick with prey, but only skilled teamwork will secure victory. One patrol must catch 3 catfish in a single outing.

**Flood Debris Cleanup**
High waters have scattered branches, reeds, shells, and driftwood across camp. TorrentClan must work together to restore their island sanctuary before the next tide.

**Catch 5 Frogs Without Injury**
The frogs are practically croaking insults from every muddy bank. Catch 5 cleanly without slips, bites, or embarrassing failures. (Rolling a 1 or lower due to current hunting modifier will result in an injury)

**Reedmarsh Wrestling Day**
Mud, reeds, and total chaos await! Apprentices and warriors alike are invited to prove that if you can fight in marsh mud, you can fight anywhere. (Roll a D8, the highest roll wins, in case of a tie, roll again!)

**Catch 2 Loons**
Their haunting calls have echoed over the waters for nights. Catch 2 elusive loons before they vanish into mist and moonlight.

**Island Root Safety Check**
The tides have been rough, and TorrentClan’s island roots must remain strong. Patrol camp thoroughly and ensure no den is at risk.

**Catch 12 Minnows**
Minnows are everywhere this moon, flashing through clear shallows and weaving between roots. A Clanwide frenzy is on.

**Fishing Tournament**
Who is TorrentClan’s greatest fisher? Compete with your Clanmates to catch the most prey before moonhigh.

**Low Tide Adventure**
The waters have receded farther than usual, revealing hidden stones, forgotten paths, and mysterious shoreline treasures. Explore while the tide allows.

**Goose Avoidance Patrol**
A furious goose has claimed part of TorrentClan’s shoreline and is absolutely not in the mood for visitors. Patrol carefully... or prepare for feathery violence. On hunting patrols, at the start each cat will roll a D10. Rolling a 1-3 will result in a modifier for your OC for this patrol. A 1 = -3, a 2 =-2 and 3 =-1

**Catch 4 Crayfish**
Sharp claws, snapping pincers, and slippery shells await. Catch 4 crayfish from beneath river stones for a crunchy challenge.

**Beach Feast Prep**
Sunspirit Sands calls for a proper feast beneath open skies. Gather prey, friends, and celebration-worthy vibes.

**Storm Flood Warning**
Dark clouds gather, winds howl, and the tides are rising fast. TorrentClan must prepare camp before floodwaters claim vulnerable ground.

**Catch 5 Fish Any Type**
The waters are rich this moon, and TorrentClan must take advantage. Catch any 5 fish before prey patterns shift.

**Duck Nest Watch**
A duck nest near camp may offer prey... or trouble. Observe carefully and decide whether to guard, hunt, or avoid.

**River Crossing Trial**
Only TorrentClan’s strongest swimmers can conquer Trout Run’s roughest currents. Cross successfully and prove your place among the tideborn. (Roll a d20, if you roll a 12 or higher, you win bragging rights at the next gathering, if you roll a 3 or lower, risk being injured. River Guardians get a +5 to their roll)

**Catch 8 Frogs**
The marsh chorus is out of control this moon. TorrentClan must thin the croaking crowd before sleep becomes impossible.

**Loon Song Night**
The loons are singing beneath silver moonlight, their haunting voices drifting across still waters. Gather for stories, songs, and perhaps mysterious warnings.

**Speedy Marsh Patrol**
Mud, reeds, water, and speed! Compete a fast-paced patrol challenge through Reedmarsh’s thickest terrain. (Roll a D8, the highest roll wins, in case of a tie, roll again!)

**Catch 3 Duck**
Tiny, fluffy, and deceptively difficult. Catch 3 ducks before they paddle out of reach.

**Water Safety Lesson**
Young paws must learn quickly in TorrentClan. Lead a lesson for kits or apprentices about tides, currents, and river dangers.

**Catch 6 Perch**
Another school has arrived in Trout Run! Don’t waste this second wave of bounty.

**Flood Escape Drill**
If the island flooded tonight, would TorrentClan be ready? Practise emergency flood response before disaster strikes for real.

**Island Camp Bonding Night**
A peaceful evening beneath sheltering branches, surrounded by soft waves and moonlit tides. Groom, laugh, and strengthen Clan bonds.

**Catch 10 Minnows Clanwide**
Every paw counts this moon! Work together to catch 10 minnows for an easy but important prey boost.

**Young Cats Swimming Lesson**
The next generation must swim like true TorrentClan cats. Lead a lesson and teach survival through water.

**Catch 2 Catfish**
Whiskered prey lurks below. Catch 2 before they disappear beneath muddy depths.

**Mudslide RP Event**
Heavy rain has shifted Reedmarsh terrain dangerously. Cats must navigate unstable mud and changing waters. (Roll a D10, rolling a 1-2 will result in an injury)

**Catch 4 Water Voles**
Quick little marsh runners are thriving among reeds and roots. Catch 4 before they vanish.

**Sunspirit Race**
Race from camp to Sunspirit Sands and back! The winner earns shoreline bragging rights until next moon.

**Storm Story Night**
Rain pounds leaves, thunder shakes roots, and TorrentClan gathers for dramatic tales of water, bravery, and survival.

**Catch 5 Frogs**
Simple, slimy, and satisfying. Reedmarsh is croaking with opportunity.

**Medicine Patrol**
The medicine cat requires another brave escort through TorrentClan’s shifting wetlands.

**Catch 3 Walleye**
Three sleek river hunters await skilled paws in the deeper waters.

**TorrentClan Whitecough Outbreak**
Cold river mist and relentless damp winds have settled over TorrentClan’s island, and coughs now ripple through reeds, roots, and shoreline dens. Roll a D4 for each TorrentClan cat: 1-2 = sick, 3-4 = healthy. If sick, roll a D6 for severity. If your initial D4 roll was a 1, add +1 to severity. Severity: 1 = Very Minor, 2-3 = Mild, 4-5 = Moderate, 6-7 = Serious. Medicine cats must act quickly before damp-chill sickness spreads deeper through camp. Remember: no OC will ever be killed without your permission.

FOSSILCLAN

**Western Terrestrial Garter Snake in Camp**
A sleek garter snake has slithered into FossilClan territory, weaving dangerously between warm stones and unsuspecting paws. Any cat may attempt to catch it without using the hunting bot. Roll a D20, 15+ = successful catch, 3 or lower = snakebite injury. No hunting modifiers apply.

**Catch 10 Mice at Dustwind Flats**
The tumbleweeds are rustling, and Dustwind Flats are teeming with tiny paws. FossilClan has 2 real-life weeks to catch 10 mice before shifting sands bury their trails.

**Catch 5 Snowshoe Hares**
Fast white shapes have been spotted darting between red stone and dry brush. Catch 5 snowshoe hares before they flee FossilClan’s hunting grounds.

**Sandstorm Warning**
The wind has begun to howl across Dustwind Flats, carrying red dust and stinging grit. FossilClan must roleplay protecting kits, elders, and prey stores before the storm swallows camp.

**Kits Demand Dinosaur Stories**
FossilClan’s youngest are demanding tales of mighty Dinosaur Spirits, ancient claws, and legendary ancestors. A warrior or elder must host storytime before restless kits become total cave-chaos.

**Lead a Dinosaur Spine Herb Patrol**
The sacred ridge is blooming with precious medicinal opportunity. Escort the medicine cat safely through FossilClan’s spiritual heart while ancient stones whisper beneath your paws.

**Catch 6 Blue Grouse**
Blue grouse have been scratching through dry brush and root tangles near camp. Catch 6 before they scatter beyond FossilClan’s reach.

**Raptorfang Race Day**
The towering spires are calling, and FossilClan apprentices are eager to prove themselves. Race, climb, and leap through Raptorfang Spires for glory... or embarrassment. (Roll a D8, the highest roll wins, in case of a tie, roll again!)

**Catch 8 Voles**
Dustwind Flats are alive with burrowing movement. Catch 8 voles before the dry earth swallows them whole.

**Rockslide Scare**
Loose stone has begun shifting near the cliffs and spires. FossilClan must roleplay securing vulnerable paths and protecting younger cats from falling rock.

**Catch 4 Chipmunks**
Quick little prey is darting through cracks and roots. Catch 4 chipmunks before they vanish into FossilClan’s ancient stone maze.

**Spiritual Fossil Night**
The moon is bright over Dinosaur Spine, and the ancient bones seem to hum with old power. Gather beneath the stars to honour the Dinosaur Spirits.

**Catch 2 Snakes**
More snakes have been spotted basking on warm red rocks. Roll carefully, hunt bravely, and prove FossilClan fears no slithering threat.

**Cliff Safety Lesson**
The Red Rock’s edge is no place for foolish paws. Warriors must guide kits or apprentices through an important safety lesson before disaster strikes.

**Catch 3 Pikas**
Tiny paws skitter through stone cracks and fossil ridges. Catch 3 pikas before they disappear beneath ancient earth.

**Dustwind Sprint**
The dry flats stretch wide and dangerous. FossilClan cats are challenged to a speed trial across open terrain. (Roll a D8, the highest roll wins, in case of a tie, roll again!)

**Sandstorm Illness Check**
Too much dust can choke even the strongest hunter. Roll a D4: 1-2 = dust sickness symptoms, 3-4 = healthy.

**Catch 5 Mice**
Simple prey, but necessary. Dustwind’s small runners are abundant this moon.

**Rexhead Strength Trial**
The mighty pillars of Rexhead call for bold leaps and fearless displays. FossilClan warriors must prove their power atop the stone heights.

**Catch 3 Squirrels**
Quick prey has been spotted weaving between fossil ridges and brush. Catch 3 before they vanish.

**Medicine Cat Vision Escort**
The medicine cat has received troubling dreams from the Dinosaur Spirits. Escort them safely to Dinosaur Spine for answers.

**Catch 4 Grouse**
Feathers and dust fill the air as grouse surge through FossilClan lands. Hunt 4 before they scatter beyond the stone ridges.

**Camp Story Circle**
As warm winds hum through red stone, FossilClan gathers to share stories of ancestors, spirits, and victories.

**Snakebite Emergency**
A FossilClan cat has been bitten! Medicine cats must act quickly, and Clanmates must respond before panic spreads.

**Catch 8 Rodents**
Dustwind Flats are overflowing with small prey. Catch any 8 rodents before prey patterns shift.

**Spire Climbing Challenge**
Raptorfang Spires test balance, agility, and courage. Complete a climbing challenge and prove your worth.

**Catch 2 Hares**
Swift prey has crossed FossilClan’s path. Catch 2 before they outrun you through the flats.

**Sand Den Repair**
Strong winds and shifting dust have damaged camp walls. FossilClan must roleplay restoring safety to their warm stone home.

**Ancestor Night**
The moon rises over Dinosaur Spine, and FossilClan is called to honour those who came before through prayer, storytelling, or silent reflection.

**FossilClan Great Hunt**
The Dinosaur Spirits demand strength this moon. FossilClan has 2 real-life weeks to catch 20 total prey and prove their might beneath red stone and ancient bone.

**FossilClan Whitecough Outbreak**
A bitter dust storm and sudden cold snap have swept across the Red Rock, leaving FossilClan’s air dry, sharp, and filled with dangerous coughing fits. Roll a D4 for each FossilClan cat: 1-2 = sick, 3-4 = healthy. If sick, roll a D6 for severity. If your initial D4 roll was a 1, add +1 to severity. Severity: 1 = Very Minor, 2-3 = Mild, 4-5 = Moderate, 6-7 = Serious. Medicine cats must treat the sick before dry coughs become something far worse. Remember: no OC will ever be killed without your permission.

SPRUCECLAN 

**Fungal Outbreak in Toadstool Glade**
A strange bloom of aggressive spores has spread through Toadstool Glade, and sneezes, coughs, and irritated paws are beginning to surface throughout SpruceClan. Roll a D4 for each SpruceClan cat: 1-2 = infected, 3-4 = healthy. Medicine cats must lead a herb patrol before the spores worsen.

**Catch 8 Squirrels**
Whispering Branches are alive with rustling tails and chattering prey! SpruceClan has 2 real-life weeks to catch 8 squirrels before they retreat deeper into the evergreen canopy.

**Catch 10 Nestlings**
Greenleaf has filled the lower branches with vulnerable nests. Catch 10 nestlings before stronger winds or rival predators claim them first.

**Kits Demand Mossy Storytime**
SpruceClan’s kits are refusing to settle unless someone fills the nursery with tales of ancient forests, owls, and brave warriors. A warrior or elder must step up before bedtime becomes a riot.

**Lead a Toadstool Herb Patrol**
The damp glade is rich with medicinal opportunity... if you know which fungi to avoid. Escort the medicine cat safely through spores and shadows. (Roll a d10, 1-2 means an infection, 3+ means safe passage. Sporekeepers get a +2 on this.)

**Catch 5 Frogs**
Sundance Pond is croaking with opportunity. Catch 5 frogs before they vanish beneath lily pads and roots.

**Owl Alert**
Silent wings have been spotted gliding through Whispering Branches after dusk. During hunting patrols, roll D8 every 3 hunting attempts. Roll 1-2 = owl encounter. Retreat immediately.

**Catch 6 Blue Jays**
Bright flashes of blue have been taunting SpruceClan from above. Catch 6 before they vanish into the canopy.

**Root Maze Rescue**
A young apprentice has become tangled or lost in Deeproot Tangle’s twisting maze. Lead a rescue patrol and guide them safely home.

**Catch 4 Chipmunks**
Tiny striped prey are darting through roots and brush. Catch 4 before they disappear underground.

**Sundance Bonding Night**
Moonlight glimmers across still pond water, and SpruceClan is invited to gather, groom, and bond beneath the stars.

**Catch 3 Ducks**
Sundance Pond’s calm waters have drawn feathered visitors. Catch 3 before they paddle away.

**Spore Safety Check**
Toadstool Glade’s fungal bloom is worsening. Roll a D4: 1-2 = minor spore irritation, 3-4 = safe.

**Catch 5 Minnows**
The shallows are silver with life. Catch 5 minnows from Sundance Pond.

**Great Spruce Vigil**
The oldest tree in the camp seems especially restless this moon. Gather beneath its roots to honour it’s strength.

**Catch 4 Water Voles**
The roots are crawling with movement. Catch 4 water voles before they retreat deeper into the tangle.

**Tree Climbing Trial**
SpruceClan’s apprentices must prove they are worthy of the forest heights. Complete a climbing challenge in Whispering Branches. (Roll a d10, a 5 or higher is a pass and bragging rights at the next gathering, a 4 or lower is a fail and a 1 is a minor injury)

**Catch 2 Herons**
Tall shadows stalk Sundance Pond’s edge. Catch 2 herons... if your patrol is brave enough.

**Toadstool Hide-and-Seek**
Toadstool Glade’s giant mushrooms make for perfect hiding spots. Kits, apprentices, and playful warriors are invited to a fun roleplay challenge.

**Catch 5 Songbirds**
The branches are alive with chirping prey. Catch any 5 songbirds before predators from above intervene.

**Root Tangle Patrol**
Deeproot Tangle’s winding paths require sharp minds and sharper paws. Patrol and ensure no dangers lurk beneath roots.

**Catch 8 Frogs**
The frogs are loud, plentiful, and impossible to ignore. Thin their chorus.

**Elder Moss Night**
SpruceClan’s elders deserve fresh bedding and warm company. Spend a night caring for camp’s wisest paws.

**Fungal Bloom Warning**
Spores have become dangerously thick in parts of Toadstool Glade. Cats must roleplay navigating or avoiding hazardous growth. Roll a D4: 1-2 = minor spore irritation, 3-4 = safe.

**Catch 3 Turtles**
Slow, sturdy prey has been spotted sunning by the pond. Catch 3... if you can crack the challenge.

**Sundance Fishing Day**
A peaceful day of fishing and bonding at Sundance Pond has been declared. Relaxation and prey await.

**Branch Sprint Race**
Who is SpruceClan’s swiftest through roots, trunks, and branches? Race through forest terrain for bragging rights. (Roll a D8, the highest roll wins, in case of a tie, roll again!)

**Catch 10 Mixed Prey**
The forest is thriving! Catch any 10 prey from SpruceClan territory before prey patterns shift.

**Medicine Cat Mushroom Watch**
Some fungi heal. Others harm. Assist the medicine cat in identifying dangerous growth before accidents happen.

**SpruceClan Forest Feast**
The evergreen forest has provided, but only if SpruceClan is worthy. Catch 20 total prey Clanwide before the 2 weeks end and celebrate beneath the Great Spruce.

**SpruceClan Whitecough Outbreak**
Freezing rain and damp evergreen winds have soaked Shadow Hearth, and now coughs are rustling through mossy dens beneath the spruce boughs. Roll a D4 for each SpruceClan cat: 1-2 = sick, 3-4 = healthy. If sick, roll a D6 for severity. If your initial D4 roll was a 1, add +1 to severity. Severity: 1 = Very Minor, 2-3 = Mild, 4-5 = Moderate, 6-7 = Serious. Medicine cats must move swiftly before the illness spreads through the forest’s shadows. Remember: no OC will ever be killed without your permission.

OUTSIDER

**Donkey Escape at the Sanctuary**
One of the Sanctuary’s donkeys has slipped free from its pasture and is trotting far too confidently into unfamiliar territory! Barn cats, rogues, loners, or even visiting Clan cats must work together to safely guide the stubborn runaway back home before twolegs panic.

**Catch 15 Barn Mice**
The haylofts are practically rustling with fat, careless mice. Outsiders have 2 real-life weeks to catch 15 barn mice before the Sanctuary’s well-fed prey learns caution.

**Neon Path Dumpster Dive**
The dumpsters are overflowing after a busy twoleg night, and the Neon Path is bursting with rats and scraps. Catch 8 rats... if rival rogues don’t beat you to it first.

**Frostbite Ridge Wind Check**
The cliffside gusts are especially brutal this moon. Any cat spying or hunting on Frostbite Ridge must roll a D6. Roll 1 = dangerous gust, retreat immediately.

**Kittypet Catmint Mission**
Rumours are spreading of lush catmint patches hidden deep in Twoleg Town gardens. Sneak through fences, avoid dogs, and return with your dignity intact.

**Sanctuary Story Circle**
The hay is warm, the night is calm, and the barn cats are gathering for stories beneath lantern light. Share tales, wisdom, or outsider gossip.

**Catch 4 Barn Rats**
Bigger, bolder, and nastier than mice, barn rats are becoming a nuisance near feed stores. Catch 4 before they grow too confident.

**Rogue Turf Tension**
Tensions are rising on Neon Path as rival rogue groups eye the same food sources. Roleplay negotiations, alliances, or dramatic confrontations.

**Catch 3 Pigeons**
Twoleg Town rooftops are bustling with plump city birds. Catch 3 before they take flight.

**Frostbite Ridge Bird Hunt**
Cliffside winds carry gulls, sparrows, and starlings high above dangerous ledges. Brave the ridge and catch 5 birds.

**Dog Escape Drill**
A loud, overly enthusiastic dog has broken free in Twoleg Town! Outsiders must roleplay dodging, escaping, or warning others before disaster strikes.

**Catch 8 Village Mice**
The alleyways and gardens are full of skittish prey. Catch 8 mice from Twoleg Town before they disappear into stone cracks.

**Sanctuary Hayloft Sleepover**
For once, survival takes a back seat to comfort. Spend a peaceful roleplay night among warm hay, moonlit rafters, and friendly farm scents.

**Catch 5 Gulls**
Frostbite Ridge is alive with shrieking gulls riding dangerous air currents. Catch 5 before winds grow too fierce.

**Rogue Alliance Night**
Not every Neon Path gathering has to end in claws. Form alliances, trade stories, or negotiate territory under flickering neon signs.

**Catch 2 Raccoons (Group Hunt)**
Trash bandits have become bold near Neon Path dumpsters. A hunting party may attempt to catch 2, but teamwork is strongly advised. (To catch a raccoon, no matter the hunting factor, you must roll a 16 or higher).

**Twoleg Monster Dodge**
Twoleg roads are especially dangerous this moon. Any cat crossing major roads must roleplay carefully avoiding monsters.

**Catch 10 Dumpster Mice**
Neon Path’s alleys are teeming with prey beneath scraps and garbage. Catch 10 before rival scavengers take over.

**Frostbite Spy Mission**
The ridge offers a perfect view of nearby Clan movement... if you can handle the cold. Spy carefully and report what you see.

**Sanctuary Peace Patrol**
Not every patrol is about danger. Check fences, greet familiar animals, and ensure the Sanctuary remains safe and calm.

**Catch 4 Sparrows**
Twoleg Town gardens and rooftops are alive with tiny fluttering prey. Catch 4 before they scatter.

**Dog Warning Patrol**
Dogs have been unusually active near key outsider paths. Patrol and warn vulnerable cats.

**Barn Cat Advice Night**
The Sanctuary’s barn cats have seen everything from foxes to floods. Spend a night hearing wisdom from cats who know survival differently.

**Catch 6 Rats**
The Neon Path’s shadows are crawling with whiskers. Catch 6 rats before they overrun your scavenging grounds.

**Lost Kittypet Escort**
A pampered housecat has wandered too far from home and clearly regrets every life choice. Guide them back... or let them learn.

**Sanctuary Feast Prep**
A rare peaceful feast is being planned among barns and pastures. Gather prey and prepare for a night of safety and shared food.

**Catch 5 Mice**
Simple, reliable, and always useful. Catch 5 mice from any outsider territory.

**Frostbite Storm Survival**
A brutal windstorm has swept Frostbite Ridge. Any cats there must roleplay surviving the dangerous cold.

**Neon Path Rivalry**
Territory disputes are heating up beneath glowing signs. Will you defend, negotiate, or challenge?

**Outsider Survival Challenge**
From barns to cliffs to alleyways, outsider life demands adaptability. Catch 25 total prey across outsider territories before the 2 weeks end and prove that survival beyond Clan borders requires just as much strength.
"""

def parse_quests():
    quest_data = {}
    current_group = None
    current_title = None
    current_description = []

    valid_groups = {
        "BLIZZARDCLAN": "BlizzardClan",
        "TORRENTCLAN": "TorrentClan",
        "FOSSILCLAN": "FossilClan",
        "SPRUCECLAN": "SpruceClan",
        "OUTSIDER": "Outsider"
    }

    for raw_line in QUEST_TEXT.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        upper_line = line.upper()

        if upper_line in valid_groups:
            if current_group and current_title:
                quest_data.setdefault(current_group, []).append({
                    "title": current_title,
                    "description": " ".join(current_description).strip()
                })

            current_group = valid_groups[upper_line]
            current_title = None
            current_description = []
            quest_data.setdefault(current_group, [])
            continue

        if line.startswith("**") and line.endswith("**"):
            if current_group and current_title:
                quest_data.setdefault(current_group, []).append({
                    "title": current_title,
                    "description": " ".join(current_description).strip()
                })

            current_title = line.replace("**", "").strip()
            current_description = []
            continue

        if current_group and current_title:
            current_description.append(line)

    if current_group and current_title:
        quest_data.setdefault(current_group, []).append({
            "title": current_title,
            "description": " ".join(current_description).strip()
        })

    cleaned = {}

    for group, quests in quest_data.items():
        seen = set()
        cleaned[group] = []

        for quest in quests:
            key = f"{quest['title']}|{quest['description']}"
            if key not in seen:
                cleaned[group].append(quest)
                seen.add(key)

    return cleaned


def quest_is_allowed(quest):
    season = data.get("season", get_current_season())
    text = f"{quest['title']} {quest['description']}".lower()

    if (
        "leaf-bare only" in text
        or "leafbare only" in text
        or "only do if the season is leaf-bare" in text
        or "only do if the season is leafbare" in text
    ):
        return season.lower().replace("-", "") == "leafbare"

    return True


def choose_quest_for_group(group, quests):
    data.setdefault("used_quests", {})
    data["used_quests"].setdefault(group, [])

    allowed_quests = [quest for quest in quests if quest_is_allowed(quest)]

    if not allowed_quests:
        allowed_quests = quests

    used_keys = set(data["used_quests"].get(group, []))

    available = [
        quest for quest in allowed_quests
        if f"{quest['title']}|{quest['description']}" not in used_keys
    ]

    if not available:
        data["used_quests"][group] = []
        available = allowed_quests

    chosen = random.choice(available)

    quest_key = f"{chosen['title']}|{chosen['description']}"
    data["used_quests"][group].append(quest_key)

    return chosen


def record_active_quest(group, quest):
    data.setdefault("active_quests", {})

    data["active_quests"].setdefault(group, [])

    quest_record = {
        "title": quest["title"],
        "description": quest["description"],
        "moon": data.get("moon", 0),
        "result": "Pending"
    }

    data["active_quests"][group].append(quest_record)

    # Keep only the most recent 2 quests for this group
    data["active_quests"][group] = data["active_quests"][group][-2:]


def build_quest_announcement():
    quest_data = parse_quests()

    lines = [
        "🌙 **A half moon has passed...**",
        "",
        "New quests are now available for every Clan and the Outsiders! Complete them within the next **2 real-life weeks** before the next quest cycle begins.",
        ""
    ]

    group_order = [
        "BlizzardClan",
        "TorrentClan",
        "FossilClan",
        "SpruceClan",
        "Outsider"
    ]

    for group in group_order:
        quests = quest_data.get(group, [])

        if not quests:
            continue

        chosen = choose_quest_for_group(group, quests)
        record_active_quest(group, chosen)

        lines.append("━━━━━━━━━━━━━━━")
        lines.append(f"**{group.upper()} QUEST**")
        lines.append(f"**{chosen['title']}**")
        lines.append(chosen["description"])
        lines.append("")

    return "\n".join(lines)


async def send_quest_announcement(channel, message):
    await channel.send(f"<@&{ROLEPLAY_ANNOUNCEMENTS_ROLE_ID}>")
    await send_long_message(channel, message)

@tasks.loop(minutes=30)
async def biweekly_quest_report():
    now = datetime.now(TZ)

    # Monday at 10 AM
    if now.weekday() != 0 or now.hour != 10:
        return

    # Every other week, starting from your chosen launch week
    START_QUEST_WEEK = 20  # May 11, 2026 launch week

    if (now.isocalendar().week - START_QUEST_WEEK) % 2 != 0:
        return

    quest_period = f"{now.year}-W{now.isocalendar().week}"

    async with data_lock:
        if data.get("last_quest_period") == quest_period:
            return

        data["last_quest_period"] = quest_period
        message = build_quest_announcement()
        save_data(data)

    channel = bot.get_channel(QUEST_CHANNEL_ID)

    if channel:
        await send_quest_announcement(channel, message)

@bot.tree.command(name="quests", description="Manually post new biweekly quests")
async def quests(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        message = build_quest_announcement()
        save_data(data)

    channel = bot.get_channel(QUEST_CHANNEL_ID)

    if channel:
        await send_quest_announcement(channel, message)
        await interaction.response.send_message("🌙 New quests posted.", ephemeral=True)
    else:
        await interaction.response.send_message("Quest channel not found. Check QUEST_CHANNEL_ID.", ephemeral=True)


@bot.tree.command(name="questresult", description="Mark a Clan or Outsider quest as passed or failed")
@app_commands.describe(
    group="Select the Clan or Outsider group",
    result="Did the most recent quest pass or fail?"
)
@app_commands.choices(
    group=CLAN_CHOICES,
    result=[
        app_commands.Choice(name="Pass", value="Passed"),
        app_commands.Choice(name="Fail", value="Failed")
    ]
)
async def questresult(
    interaction: discord.Interaction,
    group: app_commands.Choice[str],
    result: app_commands.Choice[str]
):
    if not await staff_command_check(interaction):
        return

    selected_group = group.value

    async with data_lock:
        data.setdefault("active_quests", {})
        active_quests = data["active_quests"].get(selected_group, [])

        if not active_quests:
            await interaction.response.send_message(
                f"No recent quests found for **{selected_group}**. Use `/quests` first.",
                ephemeral=True
            )
            return

        active_quests[-1]["result"] = result.value
        latest_quest = active_quests[-1]

        save_data(data)

    emoji = "✅" if result.value == "Passed" else "❌"

    await interaction.response.send_message(
        f"{emoji} **{selected_group}**'s latest quest was marked as **{result.value}**.\n"
        f"Quest: **{latest_quest['title']}**",
        ephemeral=True
    )


@bot.tree.command(name="setweather", description="Manually set this week's weather report")
@app_commands.describe(
    weather="Weather name, example: Heavy rain",
    modifier="Hunting modifier, example: -2, 0, 1, 2",
    reason="Why this weather affects hunting"
)
async def setweather(interaction: discord.Interaction, weather: str, modifier: int, reason: str):
    if not await staff_command_check(interaction):
        return

    modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)

    report = (
        f"☁️ Weather: {weather}\n"
        f"🎯 Hunting Modifier: {modifier_text}\n"
        f"📖 Effect: {reason}"
    )

    channel = bot.get_channel(WEATHER_CHANNEL_ID)
    if channel:
        await channel.send(
            content=f"<@&{WEATHER_REPORT_ROLE_ID}>",
            embed=discord.Embed(
                description=report,
                color=discord.Color.blue()
            )
        )

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
        and str(cat.get("status", "Alive")).lower() != "dead"
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

@bot.tree.command(name="catinfo", description="View details about a cat")
async def catinfo(interaction: discord.Interaction, name: str):
    if name not in data.get("cats", {}):
        await interaction.response.send_message("Cat not found.", ephemeral=True)
        return

    async with data_lock:
        cat = data["cats"][name]

        if process_injury_recovery(cat):
            save_data(data)

                # ─────────────────────────────
        # CLEAN HISTORY DISPLAY
        # ─────────────────────────────
        history = [
            entry for entry in cat.get("history", [])
            if is_story_history(entry)
        ]

        formatted_history = []

        for entry in history[-10:]:

            # Recovery history
            if "Recovered from injury/illness:" in entry:
                try:
                    moon_part, injury_part = entry.split(": ", 1)

                    injury_name = injury_part.replace(
                        "Recovered from injury/illness:",
                        ""
                    ).strip()

                    formatted_history.append(
                        f"**{moon_part}**: Recovered from {injury_name}"
                    )

                except Exception:
                    formatted_history.append(format_history_entry(entry))

            # Medical treatment history
            elif "Received medical care for" in entry:
                try:
                    moon_part, treatment_part = entry.split(": ", 1)

                    treatment_text = treatment_part.replace(
                        "Received medical care for",
                        ""
                    ).strip()

                    formatted_history.append(
                        f"**{moon_part}**: Received care for {treatment_text}"
                    )

                except Exception:
                    formatted_history.append(format_history_entry(entry))

            # Older generic recovery entries
            elif "Recovered from injury/illness" in entry:
                formatted_history.append(format_history_entry(entry))

            else:
                formatted_history.append(format_history_entry(entry))

        history_text = (
            "\n".join(formatted_history)
            if formatted_history else "No major history yet."
        )

        afterlife = cat.get("afterlife") or "None"

        # ─────────────────────────────
        # MENTOR DISPLAY
        # ─────────────────────────────
        current_mentor = cat.get("mentor")
        previous_mentors = cat.get("previous_mentors", [])

        mentor_parts = []

        if current_mentor:
            mentor_parts.append(current_mentor)

        for mentor_name in previous_mentors:
            mentor_parts.append(f"{mentor_name} (PAST)")

        mentor = ", ".join(mentor_parts) if mentor_parts else "None"

        # ─────────────────────────────
        # APPRENTICE DISPLAY
        # ─────────────────────────────
        current_apps = cat.get("apprentices", [])
        past_apps = [
            f"{app} (PAST)"
            for app in cat.get("past_apprentices", [])
        ]

        all_apps = current_apps + past_apps
        apprentices = ", ".join(all_apps) if all_apps else "None"

        # ─────────────────────────────
        # HEALTH DISPLAY
        # ─────────────────────────────
        injury_text = format_injury(cat)

        # ─────────────────────────────
        # CLEAN RELATIONSHIP DISPLAY
        # ─────────────────────────────
        mates = cat.get("mates", [])
        ex_mates = cat.get("ex_mates", [])
        family = cat.get("family", {})

        relationship_lines = []

        if mates:
            relationship_lines.append(
                f"**Mates**: {', '.join(mates)}"
            )

        if ex_mates:
            relationship_lines.append(
                f"**Ex-Mates**: {', '.join(ex_mates)}"
            )

        for relation, relatives in family.items():
            if relatives:
                relationship_lines.append(
                    f"**{relation}**: {', '.join(relatives)}"
                )

        if relationship_lines:
            relationships_text = (
                "👪 **Relationships:**\n"
                + "\n".join(relationship_lines)
            )
        else:
            relationships_text = "👪 **Relationships:** None"

        # ─────────────────────────────
        # CLEAN STATUS
        # ─────────────────────────────
        raw_status = str(cat.get("status", "Alive")).lower()

        if raw_status == "dead":
            status = "Dead"
        else:
            status = "Alive"

        # ─────────────────────────────
        # FINAL DISPLAY
        # ─────────────────────────────
        message = (
            f"🐾 **{name}**\n"
            f"**Clan**: {cat.get('clan')}\n"
            f"**Rank**: {cat.get('rank')}\n"
        )

        # Outsider faction
        if cat.get("clan") == "Outsider":
            faction = cat.get("faction") or "None"
            message += f"**Faction**: {faction}\n"

        message += (
            f"**Age**: {cat.get('age', 0)} moons\n"
            f"**Status**: {status}\n"
            f"**Current Health**: {injury_text}\n"
            f"**Mentor**: {mentor}\n"
            f"**Apprentices**: {apprentices}\n"
            f"**Afterlife**: {afterlife}\n\n"
            f"{relationships_text}\n\n"
            f"📜 **Recent History:**\n"
            f"{history_text}"
        )

    await safe_respond(interaction, message[:1900])

@bot.tree.command(name="upcomingceremonies", description="See upcoming ceremonies for the next 3 moons")
@app_commands.describe(clan="Select clan")
@app_commands.choices(clan=CLAN_ONLY_CHOICES)
async def upcomingceremonies(interaction: discord.Interaction, clan: app_commands.Choice[str]):
    selected_clan = clan.value

    upcoming = {
        1: [],
        2: [],
        3: []
    }

    for name, cat in data.get("cats", {}).items():
        if cat.get("clan") != selected_clan:
            continue

        if str(cat.get("status", "Alive")).lower() == "dead":
            continue

        age = cat.get("age", 0)
        rank = cat.get("rank")

        for moons_ahead in range(1, 4):
            future_age = age + moons_ahead

            if rank == "Kit" and future_age >= 6:
                upcoming[moons_ahead].append(f"🐾 **{name}** will become an Apprentice")
                break

            if rank == "Apprentice" and future_age >= 12:
                upcoming[moons_ahead].append(f"⚔️ **{name}** will become a Warrior")
                break

            if rank in AGING_TO_ELDER_RANKS and future_age >= 95:
                upcoming[moons_ahead].append(f"🍂 **{name}** will become an Elder")
                break

    lines = [f"🌙 Upcoming Ceremonies for **{selected_clan}**"]

    for moons_ahead in range(1, 4):
        moon_number = data.get("moon", 0) + moons_ahead
        lines.append(f"\n**Moon {moon_number}**")

        if upcoming[moons_ahead]:
            lines.extend(upcoming[moons_ahead])
        else:
            lines.append("No ceremonies expected.")

    await interaction.response.send_message("\n".join(lines)[:1900])

@bot.tree.command(name="mentorlist", description="View apprentices, mentors, and eligible mentors")
@app_commands.choices(clan=CLAN_ONLY_CHOICES)
async def mentorlist(interaction: discord.Interaction, clan: app_commands.Choice[str]):
    selected_clan = clan.value

    apprentices = []
    kits_soon = []
    eligible_mentors = []

    valid_mentor_ranks = ["Warrior", "Leader", "Deputy", "Medicine Cat", "Preymaster", "Healer", "Digger", "Pathfinder", "Sporekeeper", "River Guardian"]

    for name, cat in data.get("cats", {}).items():
        if cat.get("clan") != selected_clan or str(cat.get("status", "Alive")).lower() == "dead":
            continue

        rank = cat.get("rank")
        age = cat.get("age", 0)

        if rank in ["Apprentice", "Medicine Cat Apprentice"]:
            mentor = cat.get("mentor", "No mentor assigned")
            apprentices.append(f"• **{name}** — {age} moons | Mentor: {mentor}")

        elif rank == "Kit":
            moons_left = max(0, 6 - age)
            kits_soon.append(f"• **{name}** — {age} moons | {moons_left} moon(s) until Apprentice")

        elif rank in valid_mentor_ranks:
            current_apps = cat.get("apprentices", [])
            app_text = f" | Apprentice(s): {', '.join(current_apps)}" if current_apps else ""
            eligible_mentors.append(f"• **{name}** — {rank}{app_text}")

    lines = [f"🐾 Mentor List for **{selected_clan}**"]

    lines.append("\n**Current Apprentices**")
    lines.extend(apprentices if apprentices else ["No apprentices."])

    lines.append("\n**Kits Becoming Apprentices Soon**")
    lines.extend(kits_soon if kits_soon else ["No kits currently listed."])

    lines.append("\n**Eligible Mentors**")
    lines.extend(eligible_mentors if eligible_mentors else ["No eligible mentors found."])

    await interaction.response.send_message("\n".join(lines)[:1900])

@bot.tree.command(name="gatheringreport", description="Generate a Clan-specific Gathering report")
@app_commands.describe(clan="Select clan")
@app_commands.choices(clan=CLAN_ONLY_CHOICES)
async def gatheringreport(interaction: discord.Interaction, clan: app_commands.Choice[str]):
    selected_clan = clan.value
    current_moon = data.get("moon", 0)

    important_keywords = [
        "Became an Apprentice",
        "Became a Warrior",
        "Retired as an Elder",
        "Rank changed to",
        "Died and went to",
        "Injured/ill",
        "Recovered from injury",
        "Ceremony delayed",
        "Became mentor",
        "Had a litter",
        "Became mates with",
        "Broke up with"
    ]

    events = []

    for name, cat in data.get("cats", {}).items():
        if cat.get("clan") != selected_clan:
            continue

        history = cat.get("history", [])

        for entry in history:
            if not entry.startswith(f"Moon {current_moon}:"):
                continue

            if any(keyword in entry for keyword in important_keywords):
                clean_entry = entry.replace(f"Moon {current_moon}: ", "")
                events.append(f"• **{name}** — {clean_entry}")

    recent_quests = data.get("active_quests", {}).get(selected_clan, [])[-2:]

    lines = [
        f"📜 Gathering Report for **{selected_clan}**",
        f"🌙 Moon {current_moon}",
        f"🍃 Season: {data.get('season', get_current_season())} ({get_season_moon()}/3)",
        ""
    ]

    if events:
        lines.append("**Clan Updates**")
        lines.extend(events)
    else:
        lines.append("No major updates recorded for this Clan this moon.")

    lines.append("")
    lines.append("**Recent Quest Results**")

    if recent_quests:
        for quest in recent_quests:
            result = quest.get("result", "Pending")

            if result == "Passed":
                emoji = "✅"
            elif result == "Failed":
                emoji = "❌"
            else:
                emoji = "⏳"

            lines.append(
                f"{emoji} **{quest.get('title', 'Unknown Quest')}** — {result}"
            )
    else:
        lines.append("No recent quests recorded for this Clan yet.")

    await interaction.response.send_message("\n".join(lines)[:1900])

@bot.tree.command(name="dead", description="View dead cats by clan and afterlife")
@app_commands.describe(clan="Filter by clan", afterlife="Filter by afterlife")
@app_commands.choices(clan=CLAN_FILTER_CHOICES, afterlife=AFTERLIFE_FILTER_CHOICES)
async def dead(interaction: discord.Interaction, clan: app_commands.Choice[str], afterlife: app_commands.Choice[str]):
    dead_cats = []

    for name, cat in data.get("cats", {}).items():
        if str(cat.get("status", "Alive")).lower() != "dead":
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

@bot.tree.command(name="bothelp", description="View a list of member bot commands")
async def bothelp(interaction: discord.Interaction):
    message = (
        "📘 **ECHOSTONE MOUNTAIN BOT HELP** 📘\n\n"

        "🐾 **General Member Commands**\n"
        "`/moon` — Check the current moon, season, and Clan status.\n"
        "`/clan [ClanName]` — View the roster and ranks for one Clan.\n"
        "`/cats [clan]` — View cats by Clan, or view all cats.\n"
        "`/catinfo [Name]` — Look up a specific cat’s full information.\n"
        "`/cattinder [Name] [Clan]` — Find age-appropriate romance options for a cat.\n"
        "`/question` — Posts a silly OC question for the server. This can be used in any channel, but only twice per calendar day.\n\n"

        "🌦️ **Weather / World Commands**\n"
        "`/weather` or `/weatherreport` — View the current weekly weather report, if available.\n\n"

        "📜 **Quest / Story Commands**\n"
        "`/gatheringreport [ClanName]` — View recent story updates, quest results, injuries, rank changes, and major events for a specific Clan.\n\n"

        "💭 **About /question**\n"
        "The `/question` command randomly pulls from the OC question list. Questions can be silly personality questions, modern AU-style questions, or “most likely to” prompts.\n"
        "It resets by calendar day using Toronto time.\n"
        "Once all questions have been used, the list resets so questions can appear again.\n\n"

        "📌 **Notes**\n"
        "• Member commands can be used by anyone unless stated otherwise.\n"
        "• Some commands may only work in certain channels depending on how staff set them up.\n"
        "• If something looks wrong with a cat’s records, use `/catinfo` first to check their details.\n"
        "• Staff commands are not listed here to keep this guide simple.\n"
    )

    if interaction.response.is_done():
        await send_long_message(interaction.channel, message)
    else:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(message[:1900], ephemeral=True)

        remaining = message[1900:]
        while remaining:
            chunk = remaining[:1900]
            await interaction.followup.send(chunk, ephemeral=True)
            remaining = remaining[1900:]

# ─────────────────────────────
# RUN BOT
# ─────────────────────────────

bot.tree.add_command(cat_group)
bot.tree.add_command(injury_group)
bot.tree.add_command(mentor_group)
bot.tree.add_command(relationship_group)
bot.tree.add_command(medical_group)
keep_alive()
bot.run(TOKEN)
