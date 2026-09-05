import os
import json
import random
import re
import asyncio
import copy
import calendar
from datetime import datetime, date, time, timedelta
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
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to Railway Variables.")

# ─────────────────────────────
# BOT SETUP
# ─────────────────────────────

intents = discord.Intents.default()
intents.message_content = False
intents.members = True

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
REPORT_CHANNEL_ID = 1441502516591202394
AGE_REPORT_CHANNEL_ID = 1500707305631780984
COMMAND_CHANNEL_ID = 1500705057207746610
MEDICAL_COMMAND_CHANNEL_ID = 1503486789900570784
WEATHER_CHANNEL_ID = 1441502516591202394
WEATHER_REPORT_ROLE_ID = 1500967820194877490

# Automated allegiance boards.
ALLEGIANCE_CHANNEL_IDS = {
    "BlizzardClan": 1441545899229843678,
    "TorrentClan": 1441546037368979466,
    "FossilClan": 1441546099776294912,
    "SpruceClan": 1441546176292720670,
    "Outsider": 1441546421445857280
}
DECEASED_ALLEGIANCE_CHANNEL_ID = 1441546574697332787

# Slot counts mirror the existing allegiance layout shown in the staff reference.
ALLEGIANCE_SLOT_LIMITS = {
    "Leader": 1,
    "Deputy": 1,
    "Medicine Cat": 2,
    "Medicine Cat Apprentice": 1,
    "Pathfinder": 4,
    "Digger": 4,
    "Sporekeeper": 4,
    "River Guardian": 4,
    "Healer": 2,
    "Preymaster": 2,
    "Warrior": 40,
    "Apprentice": 20,
    "Elder": 15,
    "Queen/Den Dad": 10,
    "Kit": 24
}

ALLEGIANCE_UNIQUE_MIDRANK = {
    "BlizzardClan": "Pathfinder",
    "TorrentClan": "River Guardian",
    "FossilClan": "Digger",
    "SpruceClan": "Sporekeeper"
}

# Each Clan keeps its own decorative Messagestar-inspired allegiance style.
# These are plain Unicode/Discord markdown, so the bot can edit the boards normally.
ALLEGIANCE_CLAN_STYLES = {
    "BlizzardClan": {
        "header": "₊°｡❆ BLIZZARDCLAN ⋆⁺₊❅.",
        "divider": "────────── ⋆⋅ ❆ ⋅⋆ ──────────",
        "rank_prefix": "⋆⁺₊❅.",
    },
    "TorrentClan": {
        "header": "₊°｡๑ ⋆⁺₊TORRENTCLAN ⋆⁺₊๑｡°₊",
        "divider": "────────── ⋆⋅ ๑ ⋅⋆ ──────────",
        "rank_prefix": "⋆⁺₊๑.",
    },
    "FossilClan": {
        "header": "₊°｡⊰ ⋆⁺₊FOSSILCLAN ⋆⁺₊⊱｡°₊",
        "divider": "────────── ⋆⋅ ⊰⊱ ⋅⋆ ──────────",
        "rank_prefix": "⋆⁺₊⊰.",
    },
    "SpruceClan": {
        "header": "₊°｡𖥧 ⋆⁺₊SPRUCECLAN ⋆⁺₊𖥧｡°₊",
        "divider": "────────── ⋆⋅ 𖥧 ⋅⋆ ──────────",
        "rank_prefix": "⋆⁺₊𖥧.",
    }
}

ALLEGIANCE_OUTSIDER_STYLE = {
    "header": "₊°｡✧ ⋆⁺₊OUTSIDERS ⋆⁺₊✧｡°₊",
    "divider": "────────── ⋆⋅ ✧ ⋅⋆ ──────────",
    "Rogue": "˙˚ʚ ROGUES ɞ˚˙",
    "Kittypet": "₊˚｡୨୧ KITTYPETS ୨୧｡˚₊",
    "Loner": "₊˚｡☾ (LONERS) ☽｡˚₊",
    "Wanderer": "˗ˏˋ ✿ WANDERERS ✿ ˎˊ˗",
    "Other": "₊˚｡✧ OTHER OUTSIDERS ✧｡˚₊",
}

# Severe weather rolls are separate from the normal weekly weather report.
# Automatic severe-weather checks happen every Monday at 4 PM Toronto time.
SEVERE_WEATHER_WEEKLY_CHANCE = 20
SEVERE_WEATHER_DURATION_DAYS = 7
SEVERE_WEATHER_AUTO_HOUR = 16
SEVERE_WEATHER_AUTO_MINUTE = 0
SEVERE_WEATHER_RECENT_EVENT_MEMORY = 3
SEVERE_WEATHER_SECONDARY_SPREAD_CHANCE = 60
NORTHERN_LIGHTS_WEEKLY_CHANCE = 10
NORTHERN_LIGHTS_DURATION_HOURS = 24 * 7

HIATUS_CHANNEL_ID = 1441505660905984120
HIATUS_ROLE_ID = 1463773050242728049
MEMBER_ROLE_ID = 1441508526504808561

# Rules verification / onboarding.
RULES_VERIFICATION_MESSAGE_ID = 1544201037093535904
NEW_MEMBER_ROLE_ID = 1441509553001730098
# ALL bot-written onboarding/verification information belongs in this channel.
# Never send onboarding messages into the rules/verification-post channel itself.
VERIFICATION_INFO_CHANNEL_ID = 1441200938898423851
# Direct link to the exact verification post. The linked post lives in the rules channel,
# but the bot must never SEND onboarding/reminder messages to that channel.
RULES_LINK = "https://discord.com/channels/1441200937514434563/1441202727672877076/1544201037093535904"
RULES_REMINDER_AFTER_DAYS = 3
NEW_MEMBER_ROLE_REMOVE_AFTER_DAYS = 7

DEATH_ANNOUNCEMENT_CHANNEL_ID = 1441498271842304183
ACTIVITY_WARNING_CHANNEL_ID = 1500705057207746610
ACTIVITY_WARNING_USER_ID = 1440182563674132490

HONOUR_ANNOUNCEMENT_CHANNEL_ID = 1441502516591202394
HONOUR_TRACKER_CHANNEL_ID = 1441503004749594787
HONOUR_ANNOUNCEMENT_ROLE_ID = 1449118016360026253
HONOUR_DISCORD_TIMEOUT_SECONDS = 12

PLOT_MANAGER_ROLE_ID = 1531124178378428577
PLOT_MANAGER_CHANNEL_IDS = {
    1441537369923784857,
    1531125681361256509
}
PLOT_MODERATOR_CHANNEL_IDS = {
    COMMAND_CHANNEL_ID,
    *PLOT_MANAGER_CHANNEL_IDS
}

HONOUR_ROLE_LIMITS = {
    "Sentinel": 3,
    "Scout": 3,
    "Mediator": 2
}

HONOUR_ROLE_ORDER = ["Sentinel", "Scout", "Mediator"]

HONOUR_CLAN_FALLBACK_ICONS = {
    "BlizzardClan": "❄️",
    "TorrentClan": "🌊",
    "FossilClan": "🦴",
    "SpruceClan": "🌲"
}

MEMBERSHIP_MILESTONE_CHANNEL_ID = 1441505660905984120
MEMBERSHIP_MILESTONE_PING_ROLE_IDS = [
    1441506626371715103,
    1484027097784516668
]

# Members with any of these roles are not active RP members and should not
# receive automatic OC slot milestone rewards.
NON_RP_MILESTONE_ROLE_IDS = {
    1491988054301479004,
    1448897126976454747
}

OC_COUNT_ROLE_IDS = {
    11: 1489121685289570385,
    12: 1511063554311323879,
    13: 1489121950893609010,
    14: 1511063886860648458,
    15: 1489122040714760212,
    16: 1511064133250977924,
    17: 1489122237763027125,
    18: 1511064322242117804,
    19: 1489122317182308393,
    20: 1511064426197815456
}

ONE_MONTH_SLOT_DAYS = 30
THREE_MONTH_SLOT_DAYS = 90

HELPER_ROLE_ID = 1484027097784516668
MODERATOR_ROLE_ID = 1441506626371715103
WEATHER_REPORT_ROLE_ID = 1500967820194877490
LEADER_ROLE_ID = 1445530932659617994
DEPUTY_ROLE_ID = 1449118789521375312
MEDICINE_CAT_ROLE_ID = 1449118843485032599
MEDICINE_CAT_APPRENTICE_ROLE_ID = 1449118899860672683
HEALER_ROLE_ID = 1449118955418550364

PROPHECY_PING_ROLE_IDS = [
    LEADER_ROLE_ID,
    DEPUTY_ROLE_ID,
    MEDICINE_CAT_ROLE_ID,
    MEDICINE_CAT_APPRENTICE_ROLE_ID,
    HEALER_ROLE_ID
]

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
# GATHERING SCHEDULE SETTINGS
# ─────────────────────────────

# Both automated Gathering systems post in the main report/world channel.
# Discord Scheduled Events require a specific start time, so Gatherings begin
# at 7 PM Toronto time. The full Clan Gathering remains open until Monday at
# 11 PM; the Medicine Cat Gathering is a single-evening event ending at 11 PM.
GATHERING_CHANNEL_ID = REPORT_CHANNEL_ID
MEDICINE_GATHERING_CHANNEL_ID = REPORT_CHANNEL_ID
GATHERING_START_HOUR = 19
GATHERING_START_MINUTE = 0
GATHERING_END_HOUR = 23
MEDICINE_GATHERING_END_HOUR = 23
GATHERING_VOTE_LEAD_DAYS = 7
GATHERING_VOTE_DURATION_DAYS = 3
GATHERING_REMINDER_LEAD_DAYS = 1
STARCLAN_GATHERING_VOLUNTEER_ROLE_ID = 1543789507155861515

GATHERING_DESCRIPTION = (
    "The full moon rises once more, and cats from every corner of the territories gather beneath the stars "
    "to share the latest news. Leaders will speak of recent events, victories, troubles, and anything their "
    "Clans wish to bring to light. Whether you come to listen quietly, trade words with old friends, or stir "
    "up trouble among rivals, all are welcome at the Gathering."
)

MEDICINE_GATHERING_DESCRIPTION = (
    "Medicine cats and medicine cat apprentices gather beneath the moon to exchange news, share knowledge, "
    "and seek the guidance of StarClan. StarClan cats whose players volunteer may appear in spirit to speak "
    "with the living medicine cats and apprentices."
)

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

PLOT_MEMBER_TYPE_CHOICES = [
    app_commands.Choice(name="Clan", value="Clan"),
    app_commands.Choice(name="Outsider", value="Outsider")
]

PLOT_OUTSIDER_GROUP_CHOICES = [
    app_commands.Choice(name="The Murmur", value="Murmur"),
    app_commands.Choice(name="Other", value="Other")
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

PREY_SIZE_CHOICES = [
    app_commands.Choice(name="Normal Prey", value="normal"),
    app_commands.Choice(name="Large Prey", value="large")
]

HONOUR_ROLE_CHOICES = [
    app_commands.Choice(name="Sentinel", value="Sentinel"),
    app_commands.Choice(name="Scout", value="Scout"),
    app_commands.Choice(name="Mediator", value="Mediator")
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
    "used_prophecies": [],
    "plot_members": {}
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
        "used_questions": [],
        "hiatuses": {},
        "membership_milestones": {},
        "activity_reminders": {},
        "last_activity_reminder_id": 0,
        "honour_tracker_message_id": None,
        "plot_members": {},
        "outsider_groups": list(FACTIONS),
        "deleted_outsider_groups": [],
        "current_weather": None,
        "last_severe_weather_week": None,
        "severe_weather_week_results": {},
        "severe_weather_monthly_hits": {},
        "severe_weather_history": {},
        "active_severe_weather": [],
        "severe_weather_quiet_streak": 0,
        "aurora_active_until": None,
        "last_aurora_week": None,
        "allegiance_message_ids": {},
        "last_moon_snapshot": None,
        "rules_onboarding_reminders": {},
        "active_role_quest": None,
        "active_role_quests": [],
        "role_quest_history": [],
        "used_role_quests": [],
        "used_role_quest_roles": [],
        "used_role_quests_by_role": {},
        "role_quest_rollout_v1": False,
        "broad_hunting_quest_migration_v1": False,
        "gathering_cycles": {},
        "medicine_gathering_cycles": {},
        "gathering_history": [],
        "medicine_gathering_history": [],
        "last_gathering_skipped": None,
        "last_medicine_gathering_skipped": None,
        "ambient_hazard_last_triggered": {}
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

    # Legacy ambient hourly-check timestamps are no longer persisted. Dropping
    # this obsolete key keeps it out of future full-state Supabase writes.
    loaded.pop("ambient_hazard_last_checked", None)

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


def get_outsider_groups():
    """Return active built-in and staff-created Outsider groups in a stable order."""
    saved_groups = data.get("outsider_groups", [])
    if not isinstance(saved_groups, list):
        saved_groups = []

    deleted_groups = data.get("deleted_outsider_groups", [])
    if not isinstance(deleted_groups, list):
        deleted_groups = []
    deleted_keys = {
        str(value).strip().casefold()
        for value in deleted_groups
        if str(value).strip()
    }

    groups = []
    seen = set()
    for value in list(FACTIONS) + saved_groups:
        clean_value = str(value).strip()
        if not clean_value:
            continue
        key = clean_value.casefold()
        if key in deleted_keys or key in seen:
            continue
        seen.add(key)
        groups.append(clean_value)
    return groups


def resolve_outsider_group(value):
    """Resolve a typed group name to its saved capitalization."""
    if value is None:
        return None
    clean_value = str(value).strip()
    if not clean_value:
        return None
    for group_name in get_outsider_groups():
        if group_name.casefold() == clean_value.casefold():
            return group_name
    return None


async def outsider_group_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    current_lower = str(current or "").casefold()
    matches = [
        group_name for group_name in get_outsider_groups()
        if current_lower in group_name.casefold()
    ]
    return [
        app_commands.Choice(name=group_name, value=group_name)
        for group_name in matches[:25]
    ]


def normalize_outsider_group_storage():
    """Keep saved and deleted Outsider-group lists clean and de-duplicated."""
    groups = data.setdefault("outsider_groups", list(FACTIONS))
    if not isinstance(groups, list):
        groups = list(FACTIONS)
        data["outsider_groups"] = groups

    deleted = data.setdefault("deleted_outsider_groups", [])
    if not isinstance(deleted, list):
        deleted = []
        data["deleted_outsider_groups"] = deleted

    clean_groups = []
    seen_groups = set()
    for value in groups:
        clean = str(value).strip()
        if not clean:
            continue
        key = clean.casefold()
        if key in seen_groups:
            continue
        seen_groups.add(key)
        clean_groups.append(clean)

    clean_deleted = []
    seen_deleted = set()
    for value in deleted:
        clean = str(value).strip()
        if not clean:
            continue
        key = clean.casefold()
        if key in seen_deleted:
            continue
        seen_deleted.add(key)
        clean_deleted.append(clean)

    data["outsider_groups"] = clean_groups
    data["deleted_outsider_groups"] = clean_deleted
    return clean_groups, clean_deleted


def outsider_group_is_builtin(group_name):
    key = str(group_name or "").strip().casefold()
    return any(str(value).casefold() == key for value in FACTIONS)


def retire_outsider_group_name(group_name):
    """Hide a group name, including built-in groups that otherwise come from FACTIONS."""
    clean_name = str(group_name or "").strip()
    key = clean_name.casefold()
    groups, deleted = normalize_outsider_group_storage()

    data["outsider_groups"] = [
        value for value in groups
        if str(value).strip().casefold() != key
    ]

    if not any(str(value).strip().casefold() == key for value in deleted):
        deleted.append(clean_name)
    data["deleted_outsider_groups"] = deleted


def activate_outsider_group_name(group_name):
    """Ensure a group name is active again, even if that built-in name was deleted before."""
    clean_name = str(group_name or "").strip()
    key = clean_name.casefold()
    groups, deleted = normalize_outsider_group_storage()

    data["deleted_outsider_groups"] = [
        value for value in deleted
        if str(value).strip().casefold() != key
    ]

    # Built-ins already come from FACTIONS; custom names must be stored explicitly.
    if not outsider_group_is_builtin(clean_name):
        if not any(str(value).strip().casefold() == key for value in groups):
            groups.append(clean_name)
        data["outsider_groups"] = groups


def update_outsider_group_weather_references(old_group, new_group=None):
    """Keep severe-weather records consistent when an Outsider group is renamed or deleted."""
    old_group = str(old_group or "").strip()
    old_key = severe_entity_key(old_group, "outsider")
    new_group = str(new_group or "").strip() or None
    new_key = severe_entity_key(new_group, "outsider") if new_group else None

    # Active severe-weather effects target group names directly.
    for event in data.get("active_severe_weather", []) or []:
        effects = event.get("effects", []) if isinstance(event, dict) else []
        if not isinstance(effects, list):
            continue
        kept = []
        for effect in effects:
            if not isinstance(effect, dict):
                kept.append(effect)
                continue
            matches = (
                str(effect.get("entity_key") or "") == old_key
                or (
                    str(effect.get("kind") or "").casefold() == "outsider"
                    and str(effect.get("target") or "").casefold() == old_group.casefold()
                )
            )
            if not matches:
                kept.append(effect)
                continue
            if new_group:
                effect["entity_key"] = new_key
                effect["target"] = new_group
                kept.append(effect)
        event["effects"] = kept

    # Monthly direct-hit markers use the entity key.
    monthly_hits = data.get("severe_weather_monthly_hits", {})
    if isinstance(monthly_hits, dict):
        for month, raw_hits in list(monthly_hits.items()):
            if not isinstance(raw_hits, list):
                continue
            updated = []
            for value in raw_hits:
                value = new_key if str(value) == old_key and new_key else value
                if str(value) == old_key and not new_key:
                    continue
                if value not in updated:
                    updated.append(value)
            monthly_hits[month] = updated

    # Historical weather records are keyed by the same outsider entity key.
    history = data.get("severe_weather_history", {})
    if isinstance(history, dict) and old_key in history:
        old_history = history.pop(old_key)
        if new_key:
            merged = list(history.get(new_key, []) or []) + list(old_history or [])
            history[new_key] = merged[-12:]


def rename_outsider_group_records(old_group, new_group):
    """Rename a group everywhere it is referenced and return the affected cat count."""
    old_group = str(old_group).strip()
    new_group = str(new_group).strip()
    changed_cats = 0

    for cat_name, cat in data.get("cats", {}).items():
        current = str(cat.get("faction") or "").strip()
        if current.casefold() != old_group.casefold():
            continue
        cat["faction"] = new_group
        add_history(cat, f"Outsider group renamed from {old_group} to {new_group}")
        changed_cats += 1

    retire_outsider_group_name(old_group)
    activate_outsider_group_name(new_group)
    update_outsider_group_weather_references(old_group, new_group)
    return changed_cats


def delete_outsider_group_records(group_name):
    """Delete a group and make all of its cats unaffiliated. Return affected cat count."""
    group_name = str(group_name).strip()
    changed_cats = 0

    for cat_name, cat in data.get("cats", {}).items():
        current = str(cat.get("faction") or "").strip()
        if current.casefold() != group_name.casefold():
            continue
        cat["faction"] = None
        add_history(cat, f"Outsider group {group_name} was deleted; became unaffiliated")
        changed_cats += 1

    retire_outsider_group_name(group_name)
    update_outsider_group_weather_references(group_name, None)
    return changed_cats

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


def member_has_role_id(member, role_id):
    return any(role.id == role_id for role in getattr(member, "roles", []))


async def plot_command_check(interaction: discord.Interaction):
    # Plot commands require an approved role and an approved channel.
    is_moderator = member_has_role_id(interaction.user, MODERATOR_ROLE_ID)
    is_plot_manager = member_has_role_id(interaction.user, PLOT_MANAGER_ROLE_ID)
    channel_id = interaction.channel_id

    if is_moderator and channel_id in PLOT_MODERATOR_CHANNEL_IDS:
        return True

    if is_plot_manager and channel_id in PLOT_MANAGER_CHANNEL_IDS:
        return True

    if not is_moderator and not is_plot_manager:
        await interaction.response.send_message(
            "❌ You do not have permission to use plot commands.",
            ephemeral=True
        )
        return False

    if is_moderator:
        allowed_channels = " ".join(
            f"<#{allowed_id}>" for allowed_id in sorted(PLOT_MODERATOR_CHANNEL_IDS)
        )
    else:
        allowed_channels = " ".join(
            f"<#{allowed_id}>" for allowed_id in sorted(PLOT_MANAGER_CHANNEL_IDS)
        )

    await interaction.response.send_message(
        f"❌ Use plot commands in one of these channels: {allowed_channels}",
        ephemeral=True
    )
    return False

# ─────────────────────────────
# HIATUS ROLE HELPERS
# ─────────────────────────────

async def fetch_member_by_id(guild, user_id):
    if guild is None:
        return None

    try:
        raw_user_id = int(str(user_id).strip())
    except ValueError:
        return None

    member = guild.get_member(raw_user_id)

    if member:
        return member

    try:
        return await guild.fetch_member(raw_user_id)
    except discord.NotFound:
        return None
    except discord.Forbidden:
        return None
    except discord.HTTPException:
        return None


def get_guild_for_hiatus(info):
    guild_id = info.get("guild_id") if isinstance(info, dict) else None

    if guild_id:
        try:
            guild = bot.get_guild(int(guild_id))
            if guild:
                return guild
        except Exception:
            pass

    if len(bot.guilds) == 1:
        return bot.guilds[0]

    return None


async def update_hiatus_roles(guild, user_id, on_hiatus):
    if guild is None:
        return False, "I could not find the server to update roles."

    member = await fetch_member_by_id(guild, user_id)

    if member is None:
        return False, "I could not find that member in the server."

    hiatus_role = guild.get_role(HIATUS_ROLE_ID)
    member_role = guild.get_role(MEMBER_ROLE_ID)

    missing_roles = []

    if hiatus_role is None:
        missing_roles.append("Hiatus")

    if member_role is None:
        missing_roles.append("Member")

    if missing_roles:
        return False, f"I could not find the following role(s): {', '.join(missing_roles)}."

    try:
        if on_hiatus:
            roles_to_add = [hiatus_role] if hiatus_role not in member.roles else []
            roles_to_remove = [member_role] if member_role in member.roles else []
            reason = "Member placed on hiatus through the Echostone bot."
        else:
            roles_to_add = [member_role] if member_role not in member.roles else []
            roles_to_remove = [hiatus_role] if hiatus_role in member.roles else []
            reason = "Member returned from hiatus through the Echostone bot."

        if roles_to_add:
            await member.add_roles(*roles_to_add, reason=reason)

        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=reason)

    except discord.Forbidden:
        return False, "I do not have permission to change those roles. Make sure I have Manage Roles and my bot role is above the Member and Hiatus roles."
    except discord.HTTPException as error:
        return False, f"Discord rejected the role update: {error}"

    if on_hiatus:
        return True, "Hiatus role added and Member role removed."

    return True, "Member role restored and Hiatus role removed."


def get_membership_guild():
    if len(bot.guilds) == 1:
        return bot.guilds[0]

    for guild in bot.guilds:
        if guild.get_role(MEMBER_ROLE_ID):
            return guild

    return None


def milestone_ping_text():
    return " ".join(f"<@&{role_id}>" for role_id in MEMBERSHIP_MILESTONE_PING_ROLE_IDS)


def highest_oc_count_from_roles(member):
    member_role_ids = {role.id for role in getattr(member, "roles", [])}
    found_counts = [count for count, role_id in OC_COUNT_ROLE_IDS.items() if role_id in member_role_ids]

    if not found_counts:
        return None

    return max(found_counts)


async def increase_oc_count_role(member, reason):
    current_count = highest_oc_count_from_roles(member)

    if current_count is None:
        return False, None, None, "No 11–20 OC count role was found, so I could not tell which role to upgrade."

    if current_count >= 20:
        return True, current_count, current_count, "Already at the 20 OC maximum, so no role upgrade was applied."

    new_count = current_count + 1
    new_role = member.guild.get_role(OC_COUNT_ROLE_IDS[new_count])

    if new_role is None:
        return False, current_count, new_count, f"The {new_count} OCs role could not be found."

    roles_to_remove = []
    for count, role_id in OC_COUNT_ROLE_IDS.items():
        role = member.guild.get_role(role_id)
        if role and role in member.roles and count != new_count:
            roles_to_remove.append(role)

    try:
        await member.add_roles(new_role, reason=reason)

        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=reason)

    except discord.Forbidden:
        return False, current_count, new_count, "I do not have permission to update OC count roles. Make sure I have Manage Roles and my bot role is above the OC count roles."
    except discord.HTTPException as error:
        return False, current_count, new_count, f"Discord rejected the OC count role update: {error}"

    return True, current_count, new_count, f"OC slot role upgraded from {current_count} OCs to {new_count} OCs."


async def iter_fetch_guild_members(guild):
    try:
        async for member in guild.fetch_members(limit=None):
            yield member
    except discord.Forbidden:
        print("Could not fetch guild members. Server Members Intent may be disabled or the bot lacks access.")
    except discord.HTTPException as error:
        print(f"Could not fetch guild members: {error}")


def member_has_any_role(member, role_ids):
    member_role_ids = {role.id for role in getattr(member, "roles", [])}
    return bool(member_role_ids.intersection(set(role_ids)))


def milestone_was_processed(record, milestone_key):
    """
    Treat both the new processed flag and older awarded fields as already handled.
    This prevents the bot from giving the same 30-day or 90-day OC slot more than once,
    even if the data was saved by an older version of the bot.
    """
    return bool(
        record.get(f"{milestone_key}_processed")
        or record.get(f"{milestone_key}_awarded")
        or record.get(f"{milestone_key}_awarded_at")
    )


async def process_membership_milestone(member, user_id, milestone_key, milestone_label, days_in_server, reason):
    success, old_count, new_count, role_message = await increase_oc_count_role(member, reason)
    now_iso = datetime.now(TZ).isoformat()

    async with data_lock:
        member_record = data.setdefault("membership_milestones", {}).setdefault(user_id, {})

        # The important flag: once this milestone is attempted, it is done forever
        # unless staff manually edits the database. This stops daily repeat awards.
        member_record[f"{milestone_key}_processed"] = True
        member_record[f"{milestone_key}_processed_at"] = now_iso
        member_record[f"{milestone_key}_days_in_server"] = days_in_server
        member_record[f"{milestone_key}_role_success"] = success
        member_record[f"{milestone_key}_role_message"] = role_message
        member_record[f"{milestone_key}_old_oc_count"] = old_count
        member_record[f"{milestone_key}_new_oc_count"] = new_count

        # Keep the old field names too so /membership status and any older saved data
        # continue to make sense.
        member_record[f"{milestone_key}_awarded"] = True
        member_record[f"{milestone_key}_last_checked_at"] = now_iso
        member_record[f"{milestone_key}_awarded_at"] = now_iso

    if success and old_count is not None and new_count is not None and new_count > old_count:
        result_line = f"✅ I added **+1 OC slot**: **{old_count} OCs → {new_count} OCs**."
    elif success and old_count == 20:
        result_line = "✅ They are already at the **20 OC maximum**, so no extra slot was added."
    else:
        result_line = f"⚠️ I could not add the OC slot automatically: {role_message}"

    return (
        f"🌙 **{milestone_label}:** {member.mention} has been in the server for **{days_in_server} days**.\n"
        f"{result_line}"
    )


async def run_membership_milestone_check(post_to_channel=True):
    guild = get_membership_guild()

    if guild is None:
        return ["⚠️ I could not find the server for membership milestone checks."]

    now = datetime.now(TZ)
    today_key = now.date().isoformat()
    notices = []
    changed = False

    async with data_lock:
        data.setdefault("membership_milestones", {})

    member_role = guild.get_role(MEMBER_ROLE_ID)

    if member_role is None:
        return ["⚠️ I could not find the Member role, so membership milestones could not be checked."]

    async for member in iter_fetch_guild_members(guild):
        if member.bot:
            continue

        if member_role not in member.roles:
            continue

        # Ignore non-RP members entirely. They do not get slot upgrades and staff
        # does not get pinged for their 30/90-day milestones.
        if member_has_any_role(member, NON_RP_MILESTONE_ROLE_IDS):
            continue

        if member.joined_at is None:
            continue

        joined_at = member.joined_at.astimezone(TZ)
        days_in_server = (now.date() - joined_at.date()).days
        user_id = str(member.id)

        async with data_lock:
            member_record = data.setdefault("membership_milestones", {}).setdefault(user_id, {})
            one_month_processed = milestone_was_processed(member_record, "one_month")
            three_month_processed = milestone_was_processed(member_record, "three_month")

        member_notices = []

        if days_in_server >= ONE_MONTH_SLOT_DAYS and not one_month_processed:
            member_notices.append(await process_membership_milestone(
                member=member,
                user_id=user_id,
                milestone_key="one_month",
                milestone_label="30 Day Milestone",
                days_in_server=days_in_server,
                reason="30-day active membership milestone through the Echostone bot."
            ))
            changed = True

            # Refresh roles before checking the 90-day milestone, so a member who
            # legitimately receives both in one run climbs by exactly two slots.
            try:
                member = await guild.fetch_member(member.id)
            except Exception:
                pass

        if days_in_server >= THREE_MONTH_SLOT_DAYS and not three_month_processed:
            member_notices.append(await process_membership_milestone(
                member=member,
                user_id=user_id,
                milestone_key="three_month",
                milestone_label="90 Day Milestone",
                days_in_server=days_in_server,
                reason="90-day active membership milestone through the Echostone bot."
            ))
            changed = True

        if member_notices:
            notices.extend(member_notices)

    if changed:
        async with data_lock:
            data["last_membership_milestone_check"] = today_key
            save_data(data)

    if post_to_channel and notices:
        channel = bot.get_channel(MEMBERSHIP_MILESTONE_CHANNEL_ID)
        if channel:
            header = (
                f"{milestone_ping_text()}\n"
                f"🌙 **Membership Slot Milestone Update**\n"
                f"The following RP member milestone(s) were reached and processed automatically. Each milestone can only be processed once per member:"
            )
            await send_long_message(channel, header + "\n\n" + "\n\n".join(notices))

    return notices

# ─────────────────────────────
# SMALL HELPERS
# ─────────────────────────────

def add_history(cat, entry):
    cat.setdefault("history", [])
    cat["history"].append(f"Moon {data['moon']}: {entry}")


def normalize_permanent_conditions(cat):
    """Return a clean, de-duplicated list of permanent status conditions."""
    raw_conditions = cat.get("permanent_conditions", [])

    if isinstance(raw_conditions, str):
        raw_conditions = [raw_conditions]
    elif not isinstance(raw_conditions, list):
        raw_conditions = []

    cleaned_conditions = []
    seen = set()

    for value in raw_conditions:
        clean_value = str(value).strip()

        if not clean_value:
            continue

        key = clean_value.casefold()

        if key in seen:
            continue

        seen.add(key)
        cleaned_conditions.append(clean_value)

    cat["permanent_conditions"] = cleaned_conditions
    return cleaned_conditions


def display_cat_name(name, cat):
    """Add the NPC marker anywhere a roster-style display needs it."""
    return f"{name} (NPC)" if bool(cat.get("is_npc", False)) else name


def prepare_cat_record(name, cat):
    cat.setdefault("history", [])
    cat.setdefault("born_moon", max(0, data.get("moon", 4) - cat.get("age", 0)))
    cat.setdefault("status", "Alive")
    cat.setdefault("afterlife", None)
    cat.setdefault("faction", None)
    cat.setdefault("death_moon", None)
    cat.setdefault("hunger_level", "Satisfied")
    cat.setdefault("last_fed", None)
    cat.setdefault("last_hunger_update", None)
    cat.setdefault("freeze_age", False)
    cat.setdefault("freeze_hunger", False)
    cat.setdefault("freeze_age_until", None)
    cat.setdefault("freeze_hunger_until", None)
    cat.setdefault("previous_mentors", [])
    cat.setdefault("past_apprentices", [])
    cat.setdefault("honour_role", None)
    cat.setdefault("is_npc", False)
    cat.setdefault("allegiance_owner_id", None)
    cat.setdefault("allegiance_owner_name", None)
    # OC ownership is kept separately from allegiance publication so /oclist can
    # continue identifying a character's player even if staff temporarily removes
    # that character from the automated allegiance boards. Older records fall back
    # to the allegiance owner fields automatically.
    cat.setdefault("oc_owner_id", cat.get("allegiance_owner_id"))
    cat.setdefault("oc_owner_name", cat.get("allegiance_owner_name"))
    cat.setdefault("allegiance_npc", False)
    cat.setdefault("character_sheet_url", None)
    # Optional role-specific quest rewards are stored on the individual OC.
    cat.setdefault("role_quest_hunting_bonus", None)
    cat.setdefault("role_quest_injury_reduction_charges", 0)
    cat.setdefault("role_quest_hunger_pause_until", None)
    cat.setdefault("role_quest_lucky_paw_charges", 0)
    cat.setdefault("role_quest_well_rested_charges", 0)
    cat.setdefault("role_quest_starclan_luck_charges", 0)
    cat.setdefault("role_quest_collectibles", [])
    cat.setdefault("role_quest_bonus_catches", [])
    cat.setdefault("role_quest_nest_upgrades", [])
    cat.setdefault("role_quest_secret_spots", [])
    cat.setdefault("role_quest_connection_tokens", 0)
    # Connection Perks are permanent profile badges bought with Connection Tokens.
    # Only redeemed perks are shown on /catinfo.
    cat.setdefault("connection_perks", [])
    cat.setdefault("connection_perk_moon_uses", {})
    cat.setdefault("role_quest_skill_progress", {})
    cat.setdefault("role_quest_title", None)
    cat.setdefault("role_quest_streak", 0)
    cat.setdefault("role_quest_total_completed", 0)
    cat.setdefault("role_quest_streak_milestones", [])
    cat.setdefault("role_quest_accomplishments", [])
    normalize_permanent_conditions(cat)


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


def clean_name_value(value):
    return str(value).replace(" (PAST)", "").replace(" (Past)", "").strip()


def name_matches(value, target):
    return clean_name_value(value).lower() == clean_name_value(target).lower()


def list_has_name(values, target):
    return any(name_matches(value, target) for value in values)


def add_unique_name(cat, key, value):
    cat.setdefault(key, [])

    if not list_has_name(cat[key], value):
        cat[key].append(value)
        return True

    return False


def dedupe_name_list(values):
    clean_values = []
    seen = set()

    for value in values or []:
        clean_value = clean_name_value(value)

        if not clean_value:
            continue

        key = clean_value.lower()

        if key not in seen:
            seen.add(key)
            clean_values.append(clean_value)

    return clean_values


def format_past_names(values):
    return [f"{name} (Past)" for name in dedupe_name_list(values)]


def format_mentor_display(cat):
    current_mentor = cat.get("mentor")
    previous_mentors = dedupe_name_list(cat.get("previous_mentors", []))

    if current_mentor:
        clean_current = clean_name_value(current_mentor)
        past_text = format_past_names(
            name for name in previous_mentors
            if not name_matches(name, clean_current)
        )

        if past_text:
            return ", ".join([clean_current] + past_text)

        return clean_current

    past_text = format_past_names(previous_mentors)

    if past_text:
        return ", ".join(past_text)

    return "None"


def format_apprentices_display(cat):
    current_apprentices = dedupe_name_list(cat.get("apprentices", []))
    past_apprentices = [
        name for name in dedupe_name_list(cat.get("past_apprentices", []))
        if not list_has_name(current_apprentices, name)
    ]

    apprentice_text = current_apprentices + format_past_names(past_apprentices)

    if apprentice_text:
        return ", ".join(apprentice_text)

    return "None"


def dedupe_recent_history_for_display(history):
    deduped = []
    seen_previous_mentor_links = set()

    for entry in history or []:
        normalized = entry.lower()

        if " added as a previous mentor" in normalized:
            parts = entry.split(": ", 1)
            text_part = parts[1] if len(parts) == 2 else entry
            mentor_name = text_part.split(" added as a previous mentor", 1)[0].strip().lower()

            if mentor_name in seen_previous_mentor_links:
                continue

            seen_previous_mentor_links.add(mentor_name)

        if " added as a previous apprentice" in normalized:
            parts = entry.split(": ", 1)
            text_part = parts[1] if len(parts) == 2 else entry
            apprentice_name = text_part.split(" added as a previous apprentice", 1)[0].strip().lower()

            if apprentice_name in seen_previous_mentor_links:
                continue

            seen_previous_mentor_links.add(apprentice_name)

        deduped.append(entry)

    return deduped


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


def format_modifier(value):
    if value > 0:
        return f"+{value}"

    return str(value)


def discord_expiry_timestamp(value):
    """Format a datetime as Discord relative + full timestamps."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)

    unix_time = int(value.timestamp())
    return f"<t:{unix_time}:R> on <t:{unix_time}:f>"

# ─────────────────────────────
# AUTOMATED ALLEGIANCE SYSTEM
# ─────────────────────────────

allegiance_refresh_lock = asyncio.Lock()


def allegiance_tracker_clan(cat):
    """Return the canonical Clan stored on the same tracker record used by /catinfo."""
    raw_clan = str(cat.get("clan") or "").strip()

    for valid_clan in CLANS:
        if raw_clan.casefold() == valid_clan.casefold():
            return valid_clan

    return None


def allegiance_tracker_rank(cat):
    """Return the tracker rank exactly as /catinfo reads it, with whitespace cleaned."""
    return str(cat.get("rank") or "").strip()


def allegiance_tracker_status(cat):
    return str(cat.get("status", "Alive") or "Alive").strip()


def allegiance_tracker_snapshot(name, cat):
    """
    Read allegiance placement from the canonical cat tracker record.

    Allegiances never store a second Clan/rank value of their own. This means the
    Clan, rank, status, mentor, faction, and afterlife shown by /catinfo are the
    same values used to decide where the cat belongs on Allegiances.
    """
    return {
        "name": name,
        "clan": allegiance_tracker_clan(cat),
        "rank": allegiance_tracker_rank(cat),
        "status": allegiance_tracker_status(cat),
        "mentor": cat.get("mentor"),
        "faction": cat.get("faction"),
        "afterlife": cat.get("afterlife"),
        "is_npc": bool(cat.get("is_npc", False)),
    }


def allegiance_record_problem(name, cat):
    """Return a placement problem instead of guessing where an invalid tracker cat belongs."""
    snapshot = allegiance_tracker_snapshot(name, cat)
    clan_name = snapshot["clan"]
    rank = snapshot["rank"]

    if clan_name is None:
        return f"{name}: tracker Clan is missing or invalid ({cat.get('clan')!r})"

    if clan_name == "Outsider":
        if rank not in OUTSIDER_RANKS:
            return f"{name}: Outsider has invalid tracker rank {rank!r}"
    elif rank not in CLAN_RANKS:
        return f"{name}: {clan_name} cat has invalid tracker rank {rank!r}"

    return None


def allegiance_is_linked(cat):
    """Return whether a cat should appear on the automated allegiance boards."""
    if bool(cat.get("is_npc", False)):
        # NPCs can be published without a player or character sheet.
        # The owner/sheet fallback keeps already-linked cats visible if they are
        # later converted into NPCs before staff uses /allegiance addnpc.
        return bool(cat.get("allegiance_npc", False)) or (
            bool(cat.get("allegiance_owner_id")) and bool(cat.get("character_sheet_url"))
        )

    return bool(cat.get("allegiance_owner_id")) and bool(cat.get("character_sheet_url"))


def allegiance_has_any_linked_cats():
    return any(allegiance_is_linked(cat) for cat in data.get("cats", {}).values())


def allegiance_owner_mention(cat):
    owner_id = cat.get("allegiance_owner_id")
    if owner_id:
        try:
            return f"<@{int(owner_id)}>"
        except (TypeError, ValueError):
            pass

    owner_name = str(cat.get("allegiance_owner_name") or "unknown").strip()
    return f"@{owner_name}" if owner_name else "@unknown"


def allegiance_sheet_link(cat):
    url = str(cat.get("character_sheet_url") or "").strip()
    if not url:
        return None
    return url


def allegiance_linked_cat_name(name, cat):
    """Make playable OC names clickable; NPC names always stay plain text."""
    shown_name = display_cat_name(name, cat)

    if bool(cat.get("is_npc", False)):
        return shown_name

    url = allegiance_sheet_link(cat)

    if not url:
        return shown_name

    # A closing square bracket would break Discord link markdown.
    safe_name = str(shown_name).replace("\\", "\\\\").replace("]", "\\]")
    return f"[{safe_name}]({url})"


def allegiance_cat_entry(name, cat, deceased=False):
    shown_name = allegiance_linked_cat_name(name, cat)
    is_npc = bool(cat.get("is_npc", False))

    if deceased:
        clan_name = allegiance_tracker_clan(cat) or "Unknown"
        rank_name = allegiance_tracker_rank(cat) or "Unknown Rank"
        if clan_name == "Outsider":
            group_name = cat.get("faction") or "Outsider"
            origin = f"{group_name} {rank_name}"
        else:
            origin = f"{clan_name} {rank_name}"

        if is_npc:
            return f"• {shown_name} - {origin}"

        owner = allegiance_owner_mention(cat)
        return f"• {shown_name} - {origin} - **{owner}**"

    if is_npc:
        return f"• {shown_name}"

    owner = allegiance_owner_mention(cat)
    return f"• {shown_name} - **{owner}**"


def allegiance_sorted(cats):
    return sorted(cats, key=lambda item: item[0].casefold())


def allegiance_slot_limit(clan_name, rank_key):
    # The reference boards use two Medicine Cat slots for BlizzardClan and one
    # for TorrentClan, FossilClan, and SpruceClan.
    if rank_key == "Medicine Cat" and clan_name != "BlizzardClan":
        return 1
    return ALLEGIANCE_SLOT_LIMITS[rank_key]


def allegiance_rank_lines(clan_name, label, cats, limit, show_mentor=False):
    cats = allegiance_sorted(cats)
    style = ALLEGIANCE_CLAN_STYLES.get(clan_name, {})
    prefix = style.get("rank_prefix", "⋆⁺₊.")
    # Discord markdown hierarchy: Clan = #, section = ##, individual rank = ###.
    # The x/y count shows capacity; only real cats are listed underneath.
    lines = [f"### {prefix} **{label} {len(cats)}/{limit}**"]

    for name, cat in cats:
        lines.append(allegiance_cat_entry(name, cat))
        if show_mentor:
            mentor = cat.get("mentor")
            if mentor:
                mentor = clean_name_value(mentor)
            else:
                mentor = "unknown"
            lines.append(f"Mentor: {mentor}")

    # Keep the spacing without filling unused slots with placeholder bullets.
    lines.append("")
    return lines


def allegiance_clan_cats(clan_name):
    """Only return linked living cats whose /catinfo tracker Clan matches this board."""
    clan_name = str(clan_name).strip()
    matched = []

    for name, cat in data.get("cats", {}).items():
        if not allegiance_is_linked(cat):
            continue

        snapshot = allegiance_tracker_snapshot(name, cat)
        if snapshot["status"].casefold() == "dead":
            continue

        # STRICT BOARD ISOLATION: a BlizzardClan record can only ever enter the
        # BlizzardClan list, a FossilClan record only FossilClan, etc.
        if snapshot["clan"] != clan_name:
            continue

        matched.append((name, cat))

    return matched


def build_clan_allegiance_text(clan_name):
    clan_cats = allegiance_clan_cats(clan_name)
    unique_midrank = ALLEGIANCE_UNIQUE_MIDRANK[clan_name]

    def by_rank(rank):
        return [
            (name, cat) for name, cat in clan_cats
            if allegiance_tracker_rank(cat) == rank
        ]

    covered_ranks = {
        "Leader", "Deputy", "Medicine Cat", "Medicine Cat Apprentice",
        unique_midrank, "Healer", "Preymaster", "Warrior", "Apprentice",
        "Elder", "Queen", "Den Dad", "Kit"
    }

    # Use real Discord headings instead of decorative divider lines.
    lines = [
        f"# {clan_name}",
        "",
        "## High ranks",
        ""
    ]

    lines.extend(allegiance_rank_lines(
        clan_name, "Leader", by_rank("Leader"), allegiance_slot_limit(clan_name, "Leader")
    ))
    lines.extend(allegiance_rank_lines(
        clan_name, "Deputy", by_rank("Deputy"), allegiance_slot_limit(clan_name, "Deputy")
    ))
    lines.extend(allegiance_rank_lines(
        clan_name, "Medicine Cats", by_rank("Medicine Cat"), allegiance_slot_limit(clan_name, "Medicine Cat")
    ))
    lines.extend(allegiance_rank_lines(
        clan_name,
        "Medicine Apprentice",
        by_rank("Medicine Cat Apprentice"),
        allegiance_slot_limit(clan_name, "Medicine Cat Apprentice"),
        show_mentor=True
    ))

    lines.extend([
        "## Mid ranks",
        ""
    ])

    unique_label = {
        "Pathfinder": "Pathfinders",
        "River Guardian": "River Guardians",
        "Digger": "Diggers",
        "Sporekeeper": "Spore Keepers"
    }[unique_midrank]
    lines.extend(allegiance_rank_lines(
        clan_name,
        unique_label,
        by_rank(unique_midrank),
        allegiance_slot_limit(clan_name, unique_midrank)
    ))
    lines.extend(allegiance_rank_lines(
        clan_name, "Healers", by_rank("Healer"), allegiance_slot_limit(clan_name, "Healer")
    ))
    lines.extend(allegiance_rank_lines(
        clan_name, "Prey Masters", by_rank("Preymaster"), allegiance_slot_limit(clan_name, "Preymaster")
    ))

    lines.extend([
        "## Normal ranks",
        ""
    ])

    lines.extend(allegiance_rank_lines(
        clan_name, "Warriors", by_rank("Warrior"), allegiance_slot_limit(clan_name, "Warrior")
    ))
    lines.extend(allegiance_rank_lines(
        clan_name,
        "Apprentices",
        by_rank("Apprentice"),
        allegiance_slot_limit(clan_name, "Apprentice"),
        show_mentor=True
    ))
    lines.extend(allegiance_rank_lines(
        clan_name, "Elders", by_rank("Elder"), allegiance_slot_limit(clan_name, "Elder")
    ))

    queen_den_dad = [
        (name, cat) for name, cat in clan_cats
        if allegiance_tracker_rank(cat) in {"Queen", "Den Dad"}
    ]
    lines.extend(allegiance_rank_lines(
        clan_name,
        "Queens and Den Dads",
        queen_den_dad,
        allegiance_slot_limit(clan_name, "Queen/Den Dad")
    ))
    lines.extend(allegiance_rank_lines(
        clan_name, "Kits", by_rank("Kit"), allegiance_slot_limit(clan_name, "Kit")
    ))

    other_ranks = allegiance_sorted([
        (name, cat) for name, cat in clan_cats
        if allegiance_tracker_rank(cat) not in covered_ranks
    ])
    if other_ranks:
        lines.extend([
            "## Other ranks",
            ""
        ])
        for name, cat in other_ranks:
            lines.append(f"### **{allegiance_tracker_rank(cat) or 'Unknown Rank'}**")
            lines.append(allegiance_cat_entry(name, cat))
            lines.append("")

    return "\n".join(lines).rstrip()


def outsider_rank_header(rank):
    return ALLEGIANCE_OUTSIDER_STYLE.get(rank, ALLEGIANCE_OUTSIDER_STYLE["Other"])


def build_outsider_allegiance_text():
    outsiders = [
        (name, cat)
        for name, cat in data.get("cats", {}).items()
        if allegiance_tracker_clan(cat) == "Outsider"
        and allegiance_tracker_status(cat).casefold() != "dead"
        and allegiance_is_linked(cat)
    ]

    lines = ["# Outsiders"]

    if not outsiders:
        lines.extend(["", "No linked Outsider characters yet."])
        return "\n".join(lines)

    ordered_ranks = ["Rogue", "Kittypet", "Loner", "Wanderer"]
    extra_ranks = sorted({
        str(allegiance_tracker_rank(cat) or "Other")
        for _, cat in outsiders
        if allegiance_tracker_rank(cat) not in ordered_ranks
    }, key=str.casefold)

    for rank in ordered_ranks + extra_ranks:
        ranked = allegiance_sorted([
            (name, cat) for name, cat in outsiders
            if (allegiance_tracker_rank(cat) or "Other") == rank
        ])
        if not ranked:
            continue

        lines.extend(["", f"## {outsider_rank_header(rank)}", ""])

        buckets = {}
        bucket_order = []
        for name, cat in ranked:
            group = str(cat.get("faction") or "").strip()
            bucket = group if group else "__unaffiliated__"
            if bucket not in buckets:
                buckets[bucket] = []
                bucket_order.append(bucket)
            buckets[bucket].append((name, cat))

        bucket_order.sort(key=lambda value: (value != "__unaffiliated__", value.casefold()))

        for bucket in bucket_order:
            group_cats = allegiance_sorted(buckets[bucket])
            if bucket == "__unaffiliated__":
                if rank == "Rogue":
                    subgroup = "Lone rogues"
                elif len(bucket_order) > 1:
                    subgroup = "Unaffiliated"
                else:
                    subgroup = None
            else:
                subgroup = bucket

            if subgroup:
                lines.append(f"### {subgroup}")

            for name, cat in group_cats:
                lines.append(allegiance_cat_entry(name, cat))

            lines.append("")

    return "\n".join(lines).rstrip()


def deceased_rank_bucket(rank):
    if rank in {"Leader", "Deputy", "Medicine Cat", "Medicine Cat Apprentice"}:
        return "high"
    if rank in {"Preymaster", "Healer", "Digger", "Pathfinder", "Sporekeeper", "River Guardian"}:
        return "mid"
    return "low"


def build_deceased_allegiance_text():
    deceased = [
        (name, cat)
        for name, cat in data.get("cats", {}).items()
        if allegiance_tracker_status(cat).casefold() == "dead"
        and allegiance_is_linked(cat)
    ]

    lines = ["# Deceased Allegiances"]

    for afterlife in ["StarClan", "Unknown Residence", "Dark Forest"]:
        cats_here = allegiance_sorted([
            (name, cat) for name, cat in deceased
            if (cat.get("afterlife") or "Unknown Residence") == afterlife
        ])

        lines.extend(["", f"## {afterlife}", ""])

        high = [(name, cat) for name, cat in cats_here if deceased_rank_bucket(allegiance_tracker_rank(cat)) == "high"]
        mid = [(name, cat) for name, cat in cats_here if deceased_rank_bucket(allegiance_tracker_rank(cat)) == "mid"]
        low = [(name, cat) for name, cat in cats_here if deceased_rank_bucket(allegiance_tracker_rank(cat)) == "low"]

        lines.append("### High ranks")
        high_order = ["Leader", "Deputy", "Medicine Cat", "Medicine Cat Apprentice"]
        any_high = False
        for rank in high_order:
            ranked = allegiance_sorted([(name, cat) for name, cat in high if allegiance_tracker_rank(cat) == rank])
            if not ranked:
                continue
            any_high = True
            label = {
                "Leader": "Leaders",
                "Deputy": "Deputies",
                "Medicine Cat": "Medicine Cats",
                "Medicine Cat Apprentice": "Medicine Apprentices"
            }[rank]
            lines.append(f"**{label}**")
            for name, cat in ranked:
                lines.append(allegiance_cat_entry(name, cat, deceased=True))
        lines.extend(["", "### Mid ranks"])
        if mid:
            for rank in ["Pathfinder", "Digger", "Sporekeeper", "River Guardian", "Healer", "Preymaster"]:
                ranked = allegiance_sorted([(name, cat) for name, cat in mid if allegiance_tracker_rank(cat) == rank])
                if not ranked:
                    continue
                lines.append(f"**{plural_rank(rank)}**")
                for name, cat in ranked:
                    lines.append(allegiance_cat_entry(name, cat, deceased=True))

        lines.extend(["", "### Low ranks"])
        if low:
            for name, cat in low:
                lines.append(allegiance_cat_entry(name, cat, deceased=True))

    return "\n".join(lines).rstrip()


def split_allegiance_text(text, max_length=1900):
    chunks = []
    current = []
    current_len = 0

    for raw_line in str(text).splitlines():
        line = raw_line
        if len(line) > max_length:
            # This should be rare, but never let one malformed sheet link break posting.
            line = line[:max_length - 3] + "..."

        addition = len(line) + (1 if current else 0)
        if current and current_len + addition > max_length:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += addition

    if current:
        chunks.append("\n".join(current))

    return chunks or ["No allegiance data."]


async def get_allegiance_channel(channel_id):
    channel = bot.get_channel(channel_id)
    if channel is not None:
        return channel

    try:
        return await bot.fetch_channel(channel_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def update_allegiance_channel(channel_id, text, saved_message_ids):
    channel = await get_allegiance_channel(channel_id)
    if channel is None:
        raise RuntimeError(f"Could not access allegiance channel {channel_id}.")

    chunks = split_allegiance_text(text)
    old_messages = []

    for raw_id in saved_message_ids or []:
        try:
            message = await channel.fetch_message(int(raw_id))
            old_messages.append(message)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException, TypeError, ValueError):
            continue

    new_ids = []
    allowed_mentions = discord.AllowedMentions.none()

    for index, chunk in enumerate(chunks):
        if index < len(old_messages):
            message = old_messages[index]
            await message.edit(content=chunk, allowed_mentions=allowed_mentions)
        else:
            message = await channel.send(chunk, allowed_mentions=allowed_mentions)
        new_ids.append(message.id)

    for old_message in old_messages[len(chunks):]:
        try:
            await old_message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    return new_ids


async def refresh_all_allegiances(force=False):
    """Rebuild every managed allegiance board and edit the bot's existing messages in place."""
    global data
    existing_map = data.get("allegiance_message_ids", {})
    if not isinstance(existing_map, dict):
        existing_map = {}

    if not force and not existing_map and not allegiance_has_any_linked_cats():
        return {"updated": 0, "errors": [], "skipped": True}

    async with allegiance_refresh_lock:
        # Render all six boards from one consistent copy of the tracker. /catinfo and
        # Allegiances therefore cannot disagree because a rank/Clan edit happened
        # halfway through rendering multiple channels.
        live_data = data
        snapshot_data = copy.deepcopy(data)
        data = snapshot_data
        try:
            board_text = {
                ALLEGIANCE_CHANNEL_IDS["BlizzardClan"]: build_clan_allegiance_text("BlizzardClan"),
                ALLEGIANCE_CHANNEL_IDS["TorrentClan"]: build_clan_allegiance_text("TorrentClan"),
                ALLEGIANCE_CHANNEL_IDS["FossilClan"]: build_clan_allegiance_text("FossilClan"),
                ALLEGIANCE_CHANNEL_IDS["SpruceClan"]: build_clan_allegiance_text("SpruceClan"),
                ALLEGIANCE_CHANNEL_IDS["Outsider"]: build_outsider_allegiance_text(),
                DECEASED_ALLEGIANCE_CHANNEL_ID: build_deceased_allegiance_text()
            }
        finally:
            data = live_data

        # Defensive validation: log linked records that could not be placed safely.
        for cat_name, cat in live_data.get("cats", {}).items():
            if not allegiance_is_linked(cat):
                continue
            problem = allegiance_record_problem(cat_name, cat)
            if problem:
                print(f"Allegiance placement warning: {problem}")

        new_map = copy.deepcopy(existing_map)
        updated = 0
        errors = []

        for channel_id, content in board_text.items():
            key = str(channel_id)
            try:
                new_ids = await update_allegiance_channel(
                    channel_id,
                    content,
                    existing_map.get(key, [])
                )
                new_map[key] = new_ids
                updated += 1
            except Exception as error:
                errors.append(f"{channel_id}: {error}")
                print(f"Allegiance refresh failed for channel {channel_id}: {error}")

        async with data_lock:
            data["allegiance_message_ids"] = new_map
            save_data(data)

        return {"updated": updated, "errors": errors, "skipped": False}


async def refresh_allegiances_safely(reason=None, force=False):
    try:
        return await refresh_all_allegiances(force=force)
    except Exception as error:
        prefix = f" after {reason}" if reason else ""
        print(f"Could not refresh allegiance boards{prefix}: {error}")
        return {"updated": 0, "errors": [str(error)], "skipped": False}


def allegiance_member_names(member):
    names = []
    for value in [
        getattr(member, "display_name", None),
        getattr(member, "global_name", None),
        getattr(member, "name", None)
    ]:
        clean = str(value or "").strip()
        if clean and clean.casefold() not in {name.casefold() for name in names}:
            names.append(clean)
    return names


async def allegiance_user_autocomplete(interaction: discord.Interaction, current: str):
    guild = interaction.guild
    if guild is None:
        return []

    query = str(current or "").strip().casefold()
    scored = []

    for member in getattr(guild, "members", []):
        if member.bot:
            continue
        names = allegiance_member_names(member)
        if not names:
            continue
        searchable = " ".join(names).casefold()
        if query and query not in searchable:
            continue
        starts = any(name.casefold().startswith(query) for name in names) if query else True
        scored.append((0 if starts else 1, member.display_name.casefold(), member))

    scored.sort(key=lambda item: (item[0], item[1]))
    choices = []
    for _, _, member in scored[:25]:
        username = getattr(member, "name", member.display_name)
        label = member.display_name
        if username and username.casefold() != label.casefold():
            label = f"{label} (@{username})"
        choices.append(app_commands.Choice(name=label[:100], value=str(username)[:100]))
    return choices


async def resolve_allegiance_member(guild, raw_value):
    if guild is None:
        return None, "This command must be used inside the Discord server."

    raw = str(raw_value or "").strip()
    if not raw:
        return None, "Enter the player's display name or Discord username."

    numeric = raw
    if raw.startswith("<@") and raw.endswith(">"):
        numeric = raw[2:-1]
        if numeric.startswith("!"):
            numeric = numeric[1:]

    if numeric.isdigit():
        member = await fetch_member_by_id(guild, numeric)
        if member:
            return member, None

    lookup = raw.lstrip("@").casefold()
    members = [member for member in getattr(guild, "members", []) if not member.bot]

    def exact_matches(pool):
        return [
            member for member in pool
            if any(name.casefold() == lookup for name in allegiance_member_names(member))
        ]

    matches = exact_matches(members)

    if not matches:
        fetched = []
        async for member in iter_fetch_guild_members(guild):
            if not member.bot:
                fetched.append(member)
        if fetched:
            matches = exact_matches(fetched)
            members = fetched

    if len(matches) == 1:
        return matches[0], None

    if len(matches) > 1:
        names = ", ".join(f"{member.display_name} (@{member.name})" for member in matches[:5])
        return None, f"More than one member matches that display name. Use their username instead: {names}"

    partial = [
        member for member in members
        if any(lookup in name.casefold() for name in allegiance_member_names(member))
    ]
    if len(partial) == 1:
        return partial[0], None

    if len(partial) > 1:
        names = ", ".join(f"{member.display_name} (@{member.name})" for member in partial[:5])
        return None, f"That name matches multiple members. Be more specific or use the username: {names}"

    return None, f"I could not find a server member matching **{raw}**. Try their display name or Discord username."


def oc_owner_id(cat):
    """Return the saved player ID for an OC, including older allegiance-only records."""
    owner_id = cat.get("oc_owner_id") or cat.get("allegiance_owner_id")
    if owner_id is None:
        return None
    return str(owner_id).strip() or None


def oc_owner_name(cat):
    """Return a readable saved player name when a Discord mention cannot be used."""
    return str(
        cat.get("oc_owner_name")
        or cat.get("allegiance_owner_name")
        or "Unknown Player"
    ).strip()


def oc_list_entry(cat_name, cat):
    shown_name = allegiance_linked_cat_name(cat_name, cat)
    clan_name = allegiance_tracker_clan(cat) or str(cat.get("clan") or "Unknown")
    rank_name = allegiance_tracker_rank(cat) or "Unknown Rank"

    if clan_name == "Outsider":
        faction = str(cat.get("faction") or "").strip()
        location = f"Outsider • {rank_name}"
        if faction:
            location += f" • {faction}"
    else:
        location = f"{clan_name} • {rank_name}"

    if allegiance_tracker_status(cat).casefold() == "dead":
        afterlife = str(cat.get("afterlife") or "Unknown Residence").strip()
        location += f" • {afterlife}"

    hunger = get_hunger_status(cat) if allegiance_tracker_status(cat).casefold() != "dead" else "N/A"
    return f"• {shown_name} — {location} — 🍽️ Hunger: {hunger}"


def build_oc_list_for_owner(owner_id):
    owner_id = str(owner_id)
    owned = []

    for cat_name, cat in data.get("cats", {}).items():
        prepare_cat_record(cat_name, cat)

        if bool(cat.get("is_npc", False)):
            continue
        if oc_owner_id(cat) != owner_id:
            continue

        owned.append((cat_name, cat))

    owned = allegiance_sorted(owned)
    living = [
        (name, cat) for name, cat in owned
        if allegiance_tracker_status(cat).casefold() != "dead"
    ]
    deceased = [
        (name, cat) for name, cat in owned
        if allegiance_tracker_status(cat).casefold() == "dead"
    ]
    return living, deceased


def build_all_oc_owners():
    owners = {}

    for cat_name, cat in data.get("cats", {}).items():
        prepare_cat_record(cat_name, cat)

        if bool(cat.get("is_npc", False)):
            continue

        owner_id = oc_owner_id(cat)
        if not owner_id:
            continue

        owner = owners.setdefault(owner_id, {
            "name": oc_owner_name(cat),
            "cats": []
        })
        # Prefer the most recently available saved display name over Unknown Player.
        saved_name = oc_owner_name(cat)
        if saved_name and saved_name != "Unknown Player":
            owner["name"] = saved_name
        owner["cats"].append((cat_name, cat))

    return owners


@bot.tree.command(name="oclist", description="View which player owns which OCs")
@app_commands.describe(
    user="Optional: display name or Discord username to show only that player's OCs"
)
@app_commands.autocomplete(user=allegiance_user_autocomplete)
async def oc_list_command(interaction: discord.Interaction, user: str = None):
    # This roster is made from the same player links used by /allegiance add.
    # It is safe for members to view because that ownership is already public on Allegiances.
    await interaction.response.defer()

    allowed_mentions = discord.AllowedMentions.none()

    if user:
        member, member_error = await resolve_allegiance_member(interaction.guild, user)
        if member_error:
            await interaction.followup.send(f"❌ {member_error}")
            return

        living, deceased = build_oc_list_for_owner(member.id)
        total = len(living) + len(deceased)

        if total == 0:
            await interaction.followup.send(
                f"No OCs are currently linked to **{member.display_name}**. "
                "OCs become associated with a player when staff uses `/allegiance add`.",
            )
            return

        lines = [
            f"# OC List — {member.display_name}",
            "",
            f"**Total: {total} OC{'s' if total != 1 else ''}**"
        ]

        if living:
            lines.extend(["", f"## Living OCs — {len(living)}"] )
            for cat_name, cat in living:
                lines.append(oc_list_entry(cat_name, cat))

        if deceased:
            lines.extend(["", f"## Deceased OCs — {len(deceased)}"] )
            for cat_name, cat in deceased:
                lines.append(oc_list_entry(cat_name, cat))

        chunks = split_allegiance_text("\n".join(lines), max_length=1850)
        for chunk in chunks:
            await interaction.followup.send(
                chunk,
                allowed_mentions=allowed_mentions
            )
        return

    owners = build_all_oc_owners()
    if not owners:
        await interaction.followup.send(
            "No player-owned OCs are linked yet. Staff can link an OC to its player with `/allegiance add`."
        )
        return

    owner_rows = []
    for owner_id, owner_info in owners.items():
        cats = allegiance_sorted(owner_info["cats"])
        living = [
            (name, cat) for name, cat in cats
            if allegiance_tracker_status(cat).casefold() != "dead"
        ]
        deceased = [
            (name, cat) for name, cat in cats
            if allegiance_tracker_status(cat).casefold() == "dead"
        ]
        owner_rows.append((
            owner_info["name"].casefold(),
            owner_id,
            owner_info["name"],
            living,
            deceased
        ))

    owner_rows.sort(key=lambda row: row[0])
    lines = ["# OC List"]

    for _, owner_id, saved_name, living, deceased in owner_rows:
        total = len(living) + len(deceased)
        try:
            owner_label = f"<@{int(owner_id)}>"
        except (TypeError, ValueError):
            owner_label = f"@{saved_name}"

        lines.extend(["", f"## {owner_label} — {total} OC{'s' if total != 1 else ''}"] )

        if living:
            lines.append("### Living")
            for cat_name, cat in living:
                lines.append(oc_list_entry(cat_name, cat))

        if deceased:
            lines.append("### Deceased")
            for cat_name, cat in deceased:
                lines.append(oc_list_entry(cat_name, cat))

    chunks = split_allegiance_text("\n".join(lines), max_length=1850)
    for chunk in chunks:
        await interaction.followup.send(
            chunk,
            allowed_mentions=allowed_mentions
        )



def resolve_cat_name_casefold(raw_name):
    lookup = str(raw_name or "").strip().casefold()
    if not lookup:
        return None

    for cat_name in data.get("cats", {}):
        if cat_name.casefold() == lookup:
            return cat_name
    return None


@bot.tree.command(name="ocowner", description="Find which Discord user owns an OC")
@app_commands.describe(cat_name="Name of the OC")
async def ocowner_command(interaction: discord.Interaction, cat_name: str):
    resolved_name = resolve_cat_name_casefold(cat_name)
    if not resolved_name:
        await interaction.response.send_message(f"❌ I could not find an OC named **{cat_name}**.")
        return

    cat = data["cats"][resolved_name]
    prepare_cat_record(resolved_name, cat)

    if bool(cat.get("is_npc", False)):
        await interaction.response.send_message(
            f"🐾 **{display_cat_name(resolved_name, cat)}** is an NPC and does not have a player owner."
        )
        return

    owner_id = oc_owner_id(cat)
    if not owner_id:
        await interaction.response.send_message(
            f"❓ **{resolved_name}** does not currently have a saved player owner. Staff can link them with `/allegiance add`."
        )
        return

    member = await fetch_member_by_id(interaction.guild, owner_id) if interaction.guild else None
    owner_label = member.mention if member else f"<@{owner_id}>"
    shown_name = allegiance_linked_cat_name(resolved_name, cat)

    await interaction.response.send_message(
        f"🐾 {shown_name} is owned by **{owner_label}**.",
        allowed_mentions=discord.AllowedMentions.none()
    )


# ─────────────────────────────
# HONOUR ROLE SYSTEM
# ─────────────────────────────


def honour_role_category(saved_role):
    if saved_role == "Mediator Apprentice":
        return "Mediator"

    return saved_role


def honour_role_holders(clan_name, role_category):
    holders = []

    for cat_name, cat in data.get("cats", {}).items():
        if str(cat.get("status", "Alive")).lower() == "dead":
            continue

        if cat.get("clan") != clan_name:
            continue

        if honour_role_category(cat.get("honour_role")) != role_category:
            continue

        holders.append(cat_name)

    holders.sort(key=str.lower)
    return holders


def normalize_emoji_name(value):
    return "".join(character.lower() for character in str(value) if character.isalnum())


def honour_clan_label(guild, clan_name):
    target_names = {
        normalize_emoji_name(clan_name),
        normalize_emoji_name(clan_name.replace("Clan", ""))
    }

    if guild is not None:
        for emoji in getattr(guild, "emojis", []):
            if normalize_emoji_name(emoji.name) in target_names:
                return str(emoji)

    return HONOUR_CLAN_FALLBACK_ICONS.get(clan_name, "🐾")


def honour_slot_symbols(clan_name, role_category):
    limit = HONOUR_ROLE_LIMITS[role_category]
    used = min(len(honour_role_holders(clan_name, role_category)), limit)
    open_slots = max(0, limit - used)

    # The tracker uses ❌ for a filled position and ✅ for an open position.
    return ("❌" * used) + ("✅" * open_slots)


def build_honour_tracker_text(guild=None, include_heading=True):
    lines = []

    if include_heading:
        lines.extend([
            "## 🏅 Honour Role Availability",
            "✅ = open position • ❌ = filled position",
            ""
        ])

    for clan_name in CLAN_NAMES_ONLY:
        clan_label = honour_clan_label(guild, clan_name)

        for role_category in HONOUR_ROLE_ORDER:
            symbols = honour_slot_symbols(clan_name, role_category)
            lines.append(f"# {clan_label} {role_category} {symbols}")

        lines.append("")

    return "\n".join(lines).rstrip()


async def get_honour_channel(channel_id):
    channel = bot.get_channel(channel_id)

    if channel is not None:
        return channel

    try:
        return await bot.fetch_channel(channel_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def update_honour_tracker_message():
    channel = await get_honour_channel(HONOUR_TRACKER_CHANNEL_ID)

    if channel is None:
        raise RuntimeError("The Honour Role tracker channel could not be found.")

    tracker_text = build_honour_tracker_text(getattr(channel, "guild", None))
    saved_message_id = data.get("honour_tracker_message_id")
    tracker_message = None

    if saved_message_id:
        try:
            tracker_message = await channel.fetch_message(int(saved_message_id))
            await tracker_message.edit(content=tracker_text)
            return tracker_message
        except discord.NotFound:
            tracker_message = None
        except discord.Forbidden as error:
            raise RuntimeError("The bot cannot edit the Honour Role tracker message.") from error
        except (discord.HTTPException, ValueError, TypeError):
            tracker_message = None

    tracker_message = await channel.send(tracker_text)

    async with data_lock:
        data["honour_tracker_message_id"] = tracker_message.id
        save_data(data)

    return tracker_message


def honour_remaining_sentence(clan_name, role_category):
    limit = HONOUR_ROLE_LIMITS[role_category]
    used = len(honour_role_holders(clan_name, role_category))
    remaining = max(0, limit - used)

    if remaining == 0:
        return f"Every **{role_category}** position in **{clan_name}** is now filled."

    if remaining == 1:
        return f"Only **1 {role_category} position** remains open in **{clan_name}**."

    return f"**{remaining} {role_category} positions** remain open in **{clan_name}**."


async def announce_new_honour_role(cat_name, clan_name, display_role, role_category):
    channel = await get_honour_channel(HONOUR_ANNOUNCEMENT_CHANNEL_ID)

    if channel is None:
        return False

    tracker_text = build_honour_tracker_text(getattr(channel, "guild", None), include_heading=False)
    article = "an" if display_role[0].lower() in "aeiou" else "a"

    message = (
        f"<@&{HONOUR_ANNOUNCEMENT_ROLE_ID}>\n"
        f"🏅 **A New Honour Is Carved Into Clan History!**\n\n"
        f"**{clan_name}** has named **{cat_name}** {article} **{display_role}**. "
        f"Their service to the Clan will now be remembered among its honoured cats.\n"
        f"{honour_remaining_sentence(clan_name, role_category)}\n\n"
        f"## Honour Roles Still Remaining\n"
        f"{tracker_text}"
    )

    await channel.send(message)
    return True

# ─────────────────────────────
# INDIVIDUAL ROLE-QUEST BONUS HELPERS
# ─────────────────────────────

def get_role_quest_hunting_modifier(cat):
    """Return an OC's role-quest hunting bonus if it belongs to the current moon."""
    bonus = cat.get("role_quest_hunting_bonus")
    if not isinstance(bonus, dict):
        return 0

    try:
        bonus_moon = int(bonus.get("moon"))
        modifier = int(bonus.get("modifier", 0))
    except (TypeError, ValueError):
        return 0

    if bonus_moon != int(data.get("moon", 0)):
        return 0

    return modifier


def role_quest_hunger_pause_remaining(cat, now=None):
    now = now or datetime.now(TZ)
    raw_until = cat.get("role_quest_hunger_pause_until")
    if not raw_until:
        return None

    try:
        until = datetime.fromisoformat(raw_until)
    except Exception:
        cat["role_quest_hunger_pause_until"] = None
        return None

    if until <= now:
        cat["last_hunger_update"] = until.isoformat()
        cat["role_quest_hunger_pause_until"] = None
        return None

    return until


def active_role_quest_title(cat):
    raw = cat.get("role_quest_title")
    if not isinstance(raw, dict):
        return None
    try:
        expires_moon = int(raw.get("expires_moon", -1))
    except (TypeError, ValueError):
        return None
    if int(data.get("moon", 0)) > expires_moon:
        return None
    return str(raw.get("title") or "").strip() or None


def role_quest_bonus_summary(cat):
    bonuses = []

    hunting_bonus = get_role_quest_hunting_modifier(cat)
    if hunting_bonus:
        bonuses.append(
            f"{format_modifier(hunting_bonus)} hunting rolls for the remainder of Moon {data.get('moon', 0)}"
        )

    try:
        injury_charges = int(cat.get("role_quest_injury_reduction_charges", 0) or 0)
    except (TypeError, ValueError):
        injury_charges = 0
    if injury_charges > 0:
        charge_word = "use" if injury_charges == 1 else "uses"
        bonuses.append(f"-1 severity on the next injury/illness ({injury_charges} {charge_word} saved)")

    pause_until = role_quest_hunger_pause_remaining(cat)
    if pause_until:
        bonuses.append(f"hunger decay paused until {discord_expiry_timestamp(pause_until)}")

    try:
        lucky = int(cat.get("role_quest_lucky_paw_charges", 0) or 0)
    except (TypeError, ValueError):
        lucky = 0
    if lucky:
        bonuses.append(f"Lucky Paw: +1 on a future hunting attempt ({lucky} saved)")

    try:
        rested = int(cat.get("role_quest_well_rested_charges", 0) or 0)
    except (TypeError, ValueError):
        rested = 0
    if rested:
        bonuses.append(f"Well Rested: +1 on a future hunting/fishing or similar physical roll ({rested} saved)")

    try:
        star_luck = int(cat.get("role_quest_starclan_luck_charges", 0) or 0)
    except (TypeError, ValueError):
        star_luck = 0
    if star_luck:
        bonuses.append(f"StarClan's Little Blessing: +1 on one future hunting or fishing roll ({star_luck} saved)")

    title = active_role_quest_title(cat)
    if title:
        bonuses.append(f"temporary title: {title}")

    try:
        tokens = int(cat.get("role_quest_connection_tokens", 0) or 0)
    except (TypeError, ValueError):
        tokens = 0
    if tokens:
        bonuses.append(f"Connection Tokens: {tokens}")

    return "; ".join(bonuses) if bonuses else "None"


def role_quest_collection_summary(cat, max_items=5):
    items = []
    for value in cat.get("role_quest_collectibles", []) or []:
        if isinstance(value, dict):
            shown = str(value.get("item") or value.get("label") or "").strip()
        else:
            shown = str(value).strip()
        if shown:
            items.append(shown)
    for value in cat.get("role_quest_nest_upgrades", []) or []:
        shown = str(value.get("item") if isinstance(value, dict) else value).strip()
        if shown:
            items.append(f"Nest: {shown}")
    if not items:
        return "None"
    visible = items[-max_items:]
    prefix = f"+{len(items) - max_items} older, " if len(items) > max_items else ""
    return prefix + ", ".join(visible)


def role_quest_skill_summary(cat):
    raw = cat.get("role_quest_skill_progress", {})
    if not isinstance(raw, dict) or not raw:
        return "None"
    cleaned = []
    for skill, points in sorted(raw.items(), key=lambda item: str(item[0]).casefold()):
        try:
            points = int(points)
        except (TypeError, ValueError):
            continue
        if points > 0:
            cleaned.append(f"{skill}: {points}")
    return ", ".join(cleaned) if cleaned else "None"


# ─────────────────────────────
# HUNGER / FEEDING SYSTEM
# ─────────────────────────────

HUNGER_LEVELS = [
    "Starving",
    "Hungry",
    "Satisfied",
    "Full",
    "Well Fed"
]

HUNGER_MODIFIERS = {
    "Starving": -2,
    "Hungry": -1,
    "Satisfied": 0,
    "Full": 1,
    "Well Fed": 2
}

HUNGER_DECAY_DAYS = {
    "Well Fed": 14,
    "Full": 14,
    "Satisfied": 30,
    "Hungry": 30,
    "Starving": None
}


def normalize_hunger_level(level):
    raw_level = str(level or "Satisfied").strip()

    if raw_level in HUNGER_LEVELS:
        return raw_level

    aliases = {
        "Sated": "Satisfied",
        "Fed": "Full",
        "Well-fed": "Well Fed",
        "Well-Fed": "Well Fed",
        "Wellfed": "Well Fed",
        "Well fed": "Well Fed",
        "Thriving": "Well Fed",
        "Stuffed": "Well Fed"
    }

    return aliases.get(raw_level, "Satisfied")


def update_hunger_decay(cat):
    now = datetime.now(TZ)

    hunger = normalize_hunger_level(cat.get("hunger_level", "Satisfied"))

    # NPCs still have a stored hunger value for compatibility, but it never decays.
    if bool(cat.get("is_npc", False)):
        cat["hunger_level"] = hunger
        return hunger

    # A role-specific quest can temporarily pause hunger decay without changing
    # staff-managed freeze settings.
    if role_quest_hunger_pause_remaining(cat, now):
        cat["hunger_level"] = hunger
        return hunger

    if is_hunger_frozen(cat):
        cat["hunger_level"] = hunger
        return hunger

    last_hunger_update = cat.get("last_hunger_update") or cat.get("last_fed")

    if not last_hunger_update:
        cat["hunger_level"] = hunger
        cat["last_hunger_update"] = now.isoformat()
        return hunger

    try:
        last_update_time = datetime.fromisoformat(last_hunger_update)
    except Exception:
        cat["hunger_level"] = hunger
        cat["last_hunger_update"] = now.isoformat()
        return hunger

    while hunger != "Starving":
        decay_days = HUNGER_DECAY_DAYS.get(hunger)

        if decay_days is None:
            break

        next_decay_time = last_update_time + timedelta(days=decay_days)

        if now < next_decay_time:
            break

        current_index = HUNGER_LEVELS.index(hunger)
        hunger = HUNGER_LEVELS[max(0, current_index - 1)]
        last_update_time = next_decay_time

    cat["hunger_level"] = hunger
    cat["last_hunger_update"] = last_update_time.isoformat()

    return hunger


def get_hunger_status(cat):
    return update_hunger_decay(cat)


def get_hunger_modifier(cat):
    hunger = get_hunger_status(cat)
    return HUNGER_MODIFIERS.get(hunger, 0)


def days_until_next_hunger_drop(cat):
    hunger = get_hunger_status(cat)

    if bool(cat.get("is_npc", False)):
        return None

    if hunger == "Starving":
        return None

    if is_hunger_frozen(cat):
        return None

    last_hunger_update = cat.get("last_hunger_update") or cat.get("last_fed")

    if not last_hunger_update:
        return None

    try:
        last_update_time = datetime.fromisoformat(last_hunger_update)
    except Exception:
        return None

    decay_days = HUNGER_DECAY_DAYS.get(hunger)

    if decay_days is None:
        return None

    next_drop_time = last_update_time + timedelta(days=decay_days)
    days_left = (next_drop_time - datetime.now(TZ)).days

    return max(0, days_left)


def next_hunger_level(hunger):
    hunger = normalize_hunger_level(hunger)

    if hunger == "Starving":
        return None

    current_index = HUNGER_LEVELS.index(hunger)
    next_index = max(0, current_index - 1)

    return HUNGER_LEVELS[next_index]


def format_hunger_status(cat):
    hunger = get_hunger_status(cat)
    modifier = HUNGER_MODIFIERS.get(hunger, 0)

    modifier_text = ""
    if modifier != 0:
        modifier_text = f"{format_modifier(modifier)} hunting"

    hunger_freeze_text = freeze_remaining_text(
        cat,
        "freeze_hunger",
        "freeze_hunger_until"
    )

    if hunger_freeze_text:
        frozen_text = f"frozen {hunger_freeze_text}"
        details = [text for text in [modifier_text, frozen_text] if text]
        return f"{hunger} ({', '.join(details)})"

    days_left = days_until_next_hunger_drop(cat)
    next_level = next_hunger_level(hunger)

    countdown_text = ""
    if days_left is not None and next_level:
        day_word = "day" if days_left == 1 else "days"
        countdown_text = f"{days_left} {day_word} until {next_level}"

    details = [text for text in [modifier_text, countdown_text] if text]

    if details:
        return f"{hunger} ({', '.join(details)})"

    return hunger


def feed_cat(cat, prey_size="normal"):
    """
    Normal prey bumps hunger up by 1 level.
    Large prey bumps hunger up by 2 levels.

    Feeding resets the hunger decay timer.
    Feeding does not add to Recent History.
    """
    current_hunger = get_hunger_status(cat)
    current_index = HUNGER_LEVELS.index(current_hunger)

    bump = 2 if prey_size == "large" else 1
    new_index = min(current_index + bump, len(HUNGER_LEVELS) - 1)

    new_hunger = HUNGER_LEVELS[new_index]
    now = datetime.now(TZ).isoformat()

    cat["hunger_level"] = new_hunger
    cat["last_fed"] = now
    cat["last_hunger_update"] = now

    return current_hunger, new_hunger


def reset_cat_hunger(cat):
    """
    Resets a cat's hunger back to Satisfied and restarts their hunger decay timer.
    This does not change age/hunger freeze settings and does not add to Recent History.
    """
    current_hunger = get_hunger_status(cat)
    now = datetime.now(TZ).isoformat()

    cat["hunger_level"] = "Satisfied"
    cat["last_fed"] = now
    cat["last_hunger_update"] = now

    return current_hunger, "Satisfied"


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


def prophecy_role_mentions():
    return " ".join(f"<@&{role_id}>" for role_id in PROPHECY_PING_ROLE_IDS)


def get_saved_active_prophecy():
    active_prophecy = data.get("active_prophecy")

    if active_prophecy:
        return active_prophecy

    used_prophecies = data.get("used_prophecies", [])

    if used_prophecies:
        data["active_prophecy"] = used_prophecies[-1]
        return data["active_prophecy"]

    return None


def generate_prophecy(report):
    data.setdefault("used_prophecies", [])
    data.setdefault("prophecies_paused", False)
    data.setdefault("active_prophecy", None)

    if data.get("prophecies_paused"):
        active_prophecy = get_saved_active_prophecy()

        if active_prophecy:
            report["prophecies"].append(active_prophecy)
        else:
            report["prophecies"].append("🌙 Prophecy generation is currently paused. No active omen is saved.")

        return

    available = [
        prophecy for prophecy in PROPHECIES
        if prophecy not in data["used_prophecies"]
    ]

    if not available:
        data["used_prophecies"] = []
        available = PROPHECIES.copy()

    prophecy = random.choice(available)
    data["used_prophecies"].append(prophecy)
    data["active_prophecy"] = prophecy
    report["prophecies"].append(prophecy)


async def run_moon_update():
    async with data_lock:
        snapshot = copy.deepcopy(data)
        snapshot["last_moon_snapshot"] = None
        data["last_moon_snapshot"] = snapshot

        old_moon = data["moon"]
        new_moon = old_moon + 1

        report = {
            "old_moon": old_moon,
            "new_moon": new_moon,
            "recovered": [],
            "recovery_progress": [],
            "apprentice_news": [],
            "rank_changes": [],
            "elder_retirements": [],
            "ceremony_delays": [],
            "upcoming_apprentices": [],
            "warrior_assessments": [],
            "upcoming_elders": [],
            "births": [],
            "deaths": [],
            "succession": [],
            "prophecies": [],
            "season": None
        }

        # ─────────────────────────────
        # WHAT HAPPENED IN THE OLD MOON
        # ─────────────────────────────

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            recovered = process_injury_recovery(cat)

            if recovered:
                if cat.get("injury"):
                    report["recovery_progress"].append(
                        f"🩹 {name}'s recovery has progressed."
                    )
                else:
                    report["recovered"].append(
                        f"💚 {name} has recovered."
                    )

        for name, cat in data.get("cats", {}).items():
            history = cat.get("history", [])

            old_moon_entries = [
                entry for entry in history
                if entry.startswith(f"Moon {old_moon}:")
            ]

            if not old_moon_entries:
                continue

            latest_rank_change = None
            mentor_assigned = None

            for entry in old_moon_entries:
                clean_entry = entry.replace(f"Moon {old_moon}: ", "", 1)

                if clean_entry.startswith("Rank changed to "):
                    latest_rank_change = clean_entry.replace("Rank changed to ", "", 1).strip()

                if clean_entry.startswith("Assigned ") and " as mentor" in clean_entry:
                    mentor_assigned = clean_entry.replace("Assigned ", "", 1).replace(" as mentor", "", 1).strip()

                if clean_entry.startswith("Retired as an Elder"):
                    report["elder_retirements"].append(
                        f"🍂 {name} retired as an Elder."
                    )

                if clean_entry.startswith("Died and went to"):
                    report["deaths"].append(
                        f"💀 {name} {clean_entry.lower()}."
                    )

                if clean_entry.startswith("Had a litter"):
                    report["births"].append(
                        f"🍼 {name} {clean_entry.lower()}."
                    )

            if latest_rank_change:
                mentor = mentor_assigned or cat.get("mentor")

                if latest_rank_change == "Apprentice":
                    if mentor:
                        report["apprentice_news"].append(
                            f"🐾 {name} became an Apprentice to {mentor}."
                        )
                    else:
                        report["apprentice_news"].append(
                            f"🐾 {name} became an Apprentice."
                        )

                elif latest_rank_change == "Medicine Cat Apprentice":
                    if mentor:
                        report["apprentice_news"].append(
                            f"🌿 {name} became a Medicine Cat Apprentice to {mentor}."
                        )
                    else:
                        report["apprentice_news"].append(
                            f"🌿 {name} became a Medicine Cat Apprentice."
                        )

                elif latest_rank_change == "Warrior":
                    report["rank_changes"].append(
                        f"⚔ {name} became a Warrior."
                    )

                else:
                    report["rank_changes"].append(
                        f"⚔ {name} became {latest_rank_change}."
                    )

            elif mentor_assigned and cat.get("rank") == "Apprentice":
                report["apprentice_news"].append(
                    f"🐾 {name} became an Apprentice to {mentor_assigned}."
                )

            elif mentor_assigned and cat.get("rank") == "Medicine Cat Apprentice":
                report["apprentice_news"].append(
                    f"🌿 {name} became a Medicine Cat Apprentice to {mentor_assigned}."
                )

        # ─────────────────────────────
        # ADVANCE INTO THE NEW MOON
        # ─────────────────────────────

        data["moon"] = new_moon
        data["season"] = get_current_season()
        report["season"] = data["season"]

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            if not is_age_frozen(cat):
                cat["age"] = cat.get("age", 0) + 1

        # ─────────────────────────────
        # KIT CEREMONIES ARE MANUAL
        # ─────────────────────────────
        # Kits remain Kits after reaching 6 moons so /upcomingceremonies can
        # continue listing them until staff actually performs the ceremony and
        # changes their rank with /cat rank.

        # ─────────────────────────────
        # THINGS TO LOOK FORWARD TO IN THE NEW MOON
        # ─────────────────────────────

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            rank = cat.get("rank")
            age = cat.get("age", 0)
            clan = cat.get("clan", "Unknown Clan")

            try:
                delay = int(cat.get("ceremony_delay", 0) or 0)
            except Exception:
                delay = 0

            if delay > 0:
                is_due_for_ceremony = (
                    (rank == "Kit" and age >= 6)
                    or (rank == "Apprentice" and age >= 11)
                    or (rank in AGING_TO_ELDER_RANKS and age >= 95)
                )

                if is_due_for_ceremony:
                    new_delay = max(0, delay - 1)

                    if new_delay <= 0:
                        cat.pop("ceremony_delay", None)
                        add_history(cat, "Ceremony delay ended")
                        report["ceremony_delays"].append(
                            f"⏳ {name}'s ceremony delay is up. They may have their ceremony this moon."
                        )
                    else:
                        cat["ceremony_delay"] = new_delay
                        add_history(
                            cat,
                            f"Ceremony delayed. {new_delay} moon(s) remaining"
                        )
                        report["ceremony_delays"].append(
                            f"⏳ {name}'s ceremony is delayed. {new_delay} moon(s) remaining."
                        )
                        continue
                else:
                    continue

            if rank == "Kit" and age >= 6:
                report["upcoming_apprentices"].append(
                    f"🐾 {name} will be old enough to become an Apprentice."
                )

            elif rank == "Apprentice" and age >= 11:
                report["warrior_assessments"].append(
                    f"⚔ {name} of {clan} can take their Warrior Assessment."
                )

            elif rank in AGING_TO_ELDER_RANKS and age >= 95:
                report["upcoming_elders"].append(
                    f"🍂 {name} will be old enough to retire as an Elder."
                )

        handle_succession(report)
        handle_medicine_succession(report)
        generate_prophecy(report)
        save_data(data)

        return report

# ─────────────────────────────
# CLAN REPORT BUILDER
# ─────────────────────────────

def plural_rank(rank):
    plural_map = {
        "Leader": "Leaders",
        "Deputy": "Deputies",
        "Medicine Cat": "Medicine Cats",
        "Medicine Cat Apprentice": "Medicine Cat Apprentices",
        "Preymaster": "Preymasters",
        "Healer": "Healers",
        "Digger": "Diggers",
        "Pathfinder": "Pathfinders",
        "Sporekeeper": "Sporekeepers",
        "River Guardian": "River Guardians",
        "Warrior": "Warriors",
        "Elder": "Elders",
        "Queen": "Queens",
        "Den Dad": "Den Dads",
        "Apprentice": "Apprentices",
        "Kit": "Kits"
    }

    return plural_map.get(rank, f"{rank}s")


def bold_clan_names(text):
    for clan_name in CLAN_NAMES_ONLY:
        text = text.replace(f" of {clan_name} ", f" of **{clan_name}** ")

    text = text.replace(" of Outsider ", " of **Outsider** ")

    return text


async def build_age_report_text(report=None):
    if report is None:
        current_moon = data.get("moon", 0)
        report = {
            "new_moon": current_moon,
            "season": data.get("season", get_current_season())
        }

    new_moon = report.get("new_moon", data.get("moon", 0))

    lines = [
        f"🌙 Moon {new_moon} Age Report",
        f"🍃 Season: {report.get('season', data.get('season', 'Unknown'))} ({get_season_moon()}/3)",
        "",
        "A moon has passed over Echostone Mountain. Every living cat who is not age-frozen has grown one moon older, and the records below show each Clan's updated ages.",
        ""
    ]

    for clan_name in CLAN_NAMES_ONLY:
        lines.append(f"⛺ **{clan_name}**")

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
                if allegiance_tracker_rank(cat) == rank
            ]

            if not ranked_cats:
                continue

            ranked_cats.sort(key=lambda item: item[1].get("age", 0), reverse=True)
            lines.append(f"**{plural_rank(rank)}**")

            for name, cat in ranked_cats:
                mentor = cat.get("mentor")
                shown_name = display_cat_name(name, cat)
                age_text = f"{cat.get('age', 0)} moons"
                age_freeze_text = freeze_remaining_text(cat, "freeze_age", "freeze_age_until")

                if age_freeze_text:
                    age_text += f" (age frozen {age_freeze_text})"

                if rank in ["Apprentice", "Medicine Cat Apprentice"] and mentor:
                    lines.append(
                        f"• {shown_name} - {age_text} | Mentor: {mentor}"
                    )
                else:
                    lines.append(
                        f"• {shown_name} - {age_text}"
                    )

            lines.append("")

    lines.append("🌫 **Outsiders**")

    outsiders = [
        (name, cat)
        for name, cat in data.get("cats", {}).items()
        if cat.get("clan") == "Outsider"
        and str(cat.get("status", "Alive")).lower() != "dead"
    ]

    if outsiders:
        outsiders.sort(key=lambda item: item[1].get("age", 0), reverse=True)

        for name, cat in outsiders:
            shown_name = display_cat_name(name, cat)
            age_text = f"{cat.get('age', 0)} moons"
            age_freeze_text = freeze_remaining_text(cat, "freeze_age", "freeze_age_until")

            if age_freeze_text:
                age_text += f" (age frozen {age_freeze_text})"

            faction = f" | {cat.get('faction')}" if cat.get("faction") else ""
            lines.append(
                f"• {shown_name} - {cat.get('rank')} - {age_text}{faction}"
            )
    else:
        lines.append("No outsiders")

    return "\n".join(lines)


async def build_clan_report_text(report=None):
    if report is None:
        current_moon = data.get("moon", 0)

        report = {
            "old_moon": current_moon - 1,
            "new_moon": current_moon,
            "recovered": [],
            "recovery_progress": [],
            "apprentice_news": [],
            "rank_changes": [],
            "elder_retirements": [],
            "ceremony_delays": [],
            "upcoming_apprentices": [],
            "warrior_assessments": [],
            "upcoming_elders": [],
            "births": [],
            "deaths": [],
            "succession": [],
            "prophecies": [],
            "season": data.get("season", get_current_season())
        }

    old_moon = report.get("old_moon", data.get("moon", 0) - 1)
    new_moon = report.get("new_moon", data.get("moon", 0))

    lines = [
        f"🌙 Moon {new_moon} Story Report",
        f"🍃 Season: {report.get('season', data.get('season', 'Unknown'))} ({get_season_moon()}/3)",
        "",
        f"## 📜 What Happened in Moon {old_moon}"
    ]

    if (
        not report.get("recovered")
        and not report.get("recovery_progress")
        and not report.get("apprentice_news")
        and not report.get("rank_changes")
        and not report.get("elder_retirements")
        and not report.get("births")
        and not report.get("deaths")
        and not report.get("succession")
    ):
        lines.append("No major updates were recorded.")
    else:
        if report.get("recovered"):
            lines.extend(["", "### 💚 Recovered"])
            lines.extend(report["recovered"])

        if report.get("recovery_progress"):
            lines.extend(["", "### 🩹 Still Recovering"])
            lines.extend(report["recovery_progress"])

        if report.get("apprentice_news"):
            lines.extend(["", "### 🐾 New Apprentices"])
            lines.extend(report["apprentice_news"])

        if report.get("rank_changes"):
            lines.extend(["", "### ⚔ Rank Changes"])
            lines.extend(report["rank_changes"])

        if report.get("elder_retirements"):
            lines.extend(["", "### 🍂 Elder Retirements"])
            lines.extend(report["elder_retirements"])

        if report.get("births"):
            lines.extend(["", "### 🍼 Births"])
            lines.extend(report["births"])

        if report.get("deaths"):
            lines.extend(["", "### 💀 Deaths"])
            lines.extend(report["deaths"])

        if report.get("succession"):
            lines.extend(["", "### 👑 Succession Updates"])
            lines.extend(report["succession"])

    lines.extend(["", f"## 🔮 Things to Look Forward to in Moon {new_moon}"])

    if (
        not report.get("upcoming_apprentices")
        and not report.get("warrior_assessments")
        and not report.get("upcoming_elders")
        and not report.get("ceremony_delays")
    ):
        lines.append("No upcoming ceremonies are currently expected.")
    else:
        if report.get("upcoming_apprentices"):
            lines.extend(["", "### 🐾 Kits Old Enough to Become Apprentices"])
            lines.extend(report["upcoming_apprentices"])

        if report.get("warrior_assessments"):
            lines.extend(["", "### ⚔ Warrior Assessments"])

            for clan_name in CLAN_NAMES_ONLY:
                clan_assessments = [
                    bold_clan_names(line)
                    for line in report["warrior_assessments"]
                    if f" of {clan_name} " in line
                ]

                if clan_assessments:
                    lines.append(f"**{clan_name}**")
                    lines.extend(clan_assessments)
                    lines.append("")

            outsider_assessments = [
                bold_clan_names(line)
                for line in report["warrior_assessments"]
                if " of Outsider " in line
            ]

            if outsider_assessments:
                lines.append("**Outsider**")
                lines.extend(outsider_assessments)
                lines.append("")

        if report.get("upcoming_elders"):
            lines.extend(["", "### 🍂 Cats Old Enough to Retire"])
            lines.extend(report["upcoming_elders"])

        if report.get("ceremony_delays"):
            lines.extend(["", "### ⏳ Ceremony Delays"])
            lines.extend(report["ceremony_delays"])

    lines.extend(["", "### 🌙 Prophecies / Omens"])

    if report.get("prophecies"):
        lines.append(prophecy_role_mentions())
        lines.extend(report["prophecies"])
    else:
        lines.append("No prophecy was recorded.")

    return "\n".join(lines)


@bot.tree.command(name="moontest", description="Preview what the moon report would look like for a future moon")
@app_commands.describe(
    target_moon="The moon number you want to preview"
)
async def moontest(interaction: discord.Interaction, target_moon: int):
    if not await staff_command_check(interaction):
        return

    current_moon = data.get("moon", 0)

    if target_moon <= current_moon:
        await interaction.response.send_message(
            f"Please choose a moon higher than the current moon. Current moon is **{current_moon}**.",
            ephemeral=True
        )
        return

    moons_ahead = target_moon - current_moon

    preview_data = copy.deepcopy(data)

    old_data = globals()["data"]
    globals()["data"] = preview_data

    try:
        old_moon = current_moon
        preview_data["moon"] = target_moon
        preview_data["season"] = get_current_season()

        report = {
            "old_moon": old_moon,
            "new_moon": target_moon,
            "recovered": [],
            "recovery_progress": [],
            "apprentice_news": [],
            "rank_changes": [],
            "elder_retirements": [],
            "ceremony_delays": [],
            "upcoming_apprentices": [],
            "warrior_assessments": [],
            "upcoming_elders": [],
            "births": [],
            "deaths": [],
            "succession": [],
            "prophecies": [],
            "season": preview_data.get("season", get_current_season())
        }

        for name, cat in preview_data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            cat["age"] = cat.get("age", 0) + moons_ahead

        for name, cat in preview_data.get("cats", {}).items():
            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            rank = cat.get("rank")
            age = cat.get("age", 0)
            clan = cat.get("clan", "Unknown Clan")

            if rank == "Kit" and age >= 6:
                report["upcoming_apprentices"].append(
                    f"🐾 {name} will be old enough to become an Apprentice."
                )

            elif rank == "Apprentice" and age >= 11:
                report["warrior_assessments"].append(
                    f"⚔ {name} of {clan} can take their Warrior Assessment."
                )

            elif rank in AGING_TO_ELDER_RANKS and age >= 95:
                report["upcoming_elders"].append(
                    f"🍂 {name} will be old enough to retire as an Elder."
                )

        report["prophecies"].append("Preview only. No prophecy was rolled or saved.")

        message = await build_clan_report_text(report)

    finally:
        globals()["data"] = old_data

    channel = bot.get_channel(COMMAND_CHANNEL_ID)

    if channel:
        await send_long_message(channel, message)
        await interaction.response.send_message(
            f"🌙 Moon {target_moon} preview sent.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Command channel not found.",
            ephemeral=True
        )

def freeze_is_active(cat, freeze_key, until_key):
    if cat.get(freeze_key, False):
        return True

    freeze_until = cat.get(until_key)

    if not freeze_until:
        return False

    try:
        until_time = datetime.fromisoformat(freeze_until)
    except Exception:
        return False

    if datetime.now(TZ) <= until_time:
        return True

    cat[until_key] = None
    return False


def is_age_frozen(cat):
    return freeze_is_active(cat, "freeze_age", "freeze_age_until")


def is_hunger_frozen(cat):
    return freeze_is_active(cat, "freeze_hunger", "freeze_hunger_until")


def freeze_remaining_text(cat, freeze_key, until_key):
    if cat.get(freeze_key, False):
        return "indefinitely"

    freeze_until = cat.get(until_key)

    if not freeze_until:
        return None

    try:
        until_time = datetime.fromisoformat(freeze_until)
    except Exception:
        return None

    remaining = until_time - datetime.now(TZ)

    if remaining.total_seconds() <= 0:
        cat[until_key] = None
        return None

    days = remaining.days + 1
    day_word = "day" if days == 1 else "days"

    return f"{days} {day_word}"

FREEZE_TYPE_CHOICES = [
    app_commands.Choice(name="All", value="all"),
    app_commands.Choice(name="Hunger Only", value="hunger")
]


@bot.tree.command(
    name="freezecat",
    description="Freeze or unfreeze a cat's aging and/or hunger."
)
@app_commands.describe(
    cat_name="Name of the cat",
    freeze_type="Choose whether to freeze all or only hunger",
    frozen="True = freeze, False = unfreeze",
    days="Optional number of days. Leave blank for indefinite freeze."
)
@app_commands.choices(
    freeze_type=FREEZE_TYPE_CHOICES
)
async def freezecat(
    interaction: discord.Interaction,
    cat_name: str,
    freeze_type: app_commands.Choice[str],
    frozen: bool,
    days: int = None
):
    if not await staff_command_check(interaction):
        return

    if days is not None and days <= 0:
        await interaction.response.send_message(
            "❌ Days must be 1 or higher. Leave days blank for an indefinite freeze.",
            ephemeral=True
        )
        return

    async with data_lock:
        cat = data.get("cats", {}).get(cat_name)

        if not cat:
            await interaction.response.send_message(
                f"❌ Cat '{cat_name}' was not found.",
                ephemeral=True
            )
            return

        prepare_cat_record(cat_name, cat)

        now = datetime.now(TZ)
        freeze_until = None

        if frozen and days is not None:
            freeze_until = (now + timedelta(days=days)).isoformat()

        if freeze_type.value == "all":
            if frozen:
                if days is None:
                    cat["freeze_age"] = True
                    cat["freeze_hunger"] = True
                    cat["freeze_age_until"] = None
                    cat["freeze_hunger_until"] = None
                else:
                    cat["freeze_age"] = False
                    cat["freeze_hunger"] = False
                    cat["freeze_age_until"] = freeze_until
                    cat["freeze_hunger_until"] = freeze_until
            else:
                cat["freeze_age"] = False
                cat["freeze_hunger"] = False
                cat["freeze_age_until"] = None
                cat["freeze_hunger_until"] = None

        elif freeze_type.value == "hunger":
            if frozen:
                if days is None:
                    cat["freeze_hunger"] = True
                    cat["freeze_hunger_until"] = None
                else:
                    cat["freeze_hunger"] = False
                    cat["freeze_hunger_until"] = freeze_until
            else:
                cat["freeze_hunger"] = False
                cat["freeze_hunger_until"] = None

        age_freeze_text = freeze_remaining_text(cat, "freeze_age", "freeze_age_until")
        hunger_freeze_text = freeze_remaining_text(cat, "freeze_hunger", "freeze_hunger_until")

        save_data(data)

    await interaction.response.send_message(
        f"❄️ **{cat_name} freeze settings updated.**\n"
        f"**Age:** {'Frozen ' + age_freeze_text if age_freeze_text else 'Not frozen'}\n"
        f"**Hunger:** {'Frozen ' + hunger_freeze_text if hunger_freeze_text else 'Not frozen'}"
    )
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
    "Newleaf": {
        "wet": [
            "🌧️ Rain beads on fresh leaves as Newleaf settles over the mountain, turning the trails soft beneath every pawstep.",
            "🌧️ The territories smell of wet earth and new growth, with rain darkening the bark and weighing down the young grass.",
            "🌦️ Newleaf rain sweeps through the forest, waking roots, moss, and hidden seeds beneath the mud.",
            "🌧️ Damp air clings to the mountain, carrying the scent of rain-soaked soil and fresh shoots.",
            "🌧️ Water drips steadily from the branches, and the forest feels newly washed beneath the grey Newleaf sky."
        ],
        "clear": [
            "🌱 Newleaf sunlight spills across the mountain, warming fresh shoots and softening the last traces of cold.",
            "☀️ Clear skies brighten the new growth, and the forest feels awake beneath the warmth of Newleaf.",
            "🌿 Sunlight filters through budding branches, turning the damp forest floor bright and green.",
            "🌱 The mountain breathes easier beneath clear Newleaf skies, with young plants pushing boldly through the earth.",
            "☀️ Warm light catches on fresh leaves and open trails, giving the territories a bright, hopeful feeling."
        ],
        "cloudy": [
            "☁️ Soft clouds drift over the mountain, keeping the Newleaf air cool and comfortable.",
            "🌥️ The sky is muted, but the forest below is alive with fresh scents and new growth.",
            "☁️ A blanket of cloud settles above the territories, dimming the light without stealing Newleaf’s warmth.",
            "🌫️ The mountain rests under a pale Newleaf sky, quiet but full of life stirring beneath the leaves.",
            "☁️ Gentle cloud cover keeps the forest calm while fresh shoots brighten the trails below."
        ],
        "windy": [
            "🍃 A Newleaf breeze moves through the budding branches, carrying the scent of damp moss and fresh grass.",
            "🌬️ Wind stirs the young leaves and sends ripples through the grass along the trails.",
            "🍃 Fresh air sweeps across the mountain, shaking rainwater from the branches and waking the undergrowth.",
            "🌱 A cool breeze threads through the new growth, making the forest feel restless but alive.",
            "🍃 The mountain carries the clean scent of Newleaf on every gust, from fresh roots to open sky."
        ],
        "cold": [
            "🌱 Newleaf has arrived, but a chill still lingers in the shaded parts of the mountain.",
            "❄️ The last bite of leaf-bare clings to the air, even as fresh shoots break through the soil.",
            "🌬️ Cool Newleaf air settles over the territories, crisp enough to remind every cat that winter has only just passed.",
            "🌱 The forest is waking slowly, with cold earth underpaw and green life pushing through anyway.",
            "🧊 A faint chill hangs over the new growth, but the mountain is beginning to thaw."
        ],
        "neutral": [
            "🌱 Newleaf has softened the mountain, bringing fresh scents, muddy trails, and the first promise of warmer days.",
            "🌿 New growth spreads across the territories, brightening dens, trails, and hunting grounds alike.",
            "🌱 The forest feels newly awake, with fresh leaves unfurling and life stirring beneath the roots.",
            "🌿 Soft earth, young grass, and fresh moss mark Newleaf’s return to the mountain.",
            "🌱 The territories feel renewed, with the old cold fading and green life rising in its place."
        ]
    },

    "Greenleaf": {
        "wet": [
            "🌧️ Warm rain rolls through the Greenleaf canopy, darkening the leaves and cooling the forest floor.",
            "⛈️ Rain drums against the thick summer leaves, filling the territory with the scent of wet grass.",
            "🌧️ A humid rain settles over the mountain, leaving the trails slick and the air heavy.",
            "🌦️ Greenleaf rain sweeps across the territories, cooling the heat and sending drops scattering from every branch.",
            "⛈️ The forest shivers beneath summer rain, loud with dripping leaves and distant thunder."
        ],
        "clear": [
            "☀️ Greenleaf sunlight stretches warmly across the territories, brightening every path and pool.",
            "🌞 The mountain glows under clear Greenleaf skies, alive with buzzing insects and rustling grass.",
            "☀️ Sunlight pours through the canopy, warming the stones, dens, and open trails.",
            "🌿 The forest is bright and full beneath the Greenleaf sun, thick with scent and movement.",
            "☀️ Clear summer skies make the whole mountain feel wide awake and alive."
        ],
        "cloudy": [
            "☁️ Clouds soften the Greenleaf heat, leaving the forest warm but comfortable.",
            "🌥️ The canopy stirs beneath a muted sky, with the territory calm and steady below.",
            "☁️ A cloudy Greenleaf sky hangs over the mountain, dulling the heat without cooling the air too much.",
            "🌥️ Warm clouds drift above the forest, giving patrols shelter from the strongest sun.",
            "☁️ The territory rests under gentle cloud cover, with the thick leaves holding in the summer warmth."
        ],
        "windy": [
            "🍃 A warm Greenleaf breeze moves through the canopy, rustling leaves and carrying scent across the trails.",
            "🌬️ Wind pushes through the summer grass, making the whole territory whisper with movement.",
            "🍃 Fresh air cuts through the heat, stirring the ferns and cooling the shaded paths.",
            "🌿 A breeze ripples across the mountain, shaking sunlight through the leaves.",
            "🍃 The forest feels lively beneath the wind, with every branch and blade of grass in motion."
        ],
        "cold": [
            "🌿 A rare coolness settles over the Greenleaf territory, easing the heat from the trails.",
            "🌥️ The air is cooler than expected for Greenleaf, leaving the forest calm and comfortable.",
            "🍃 Cool shade gathers beneath the thick leaves, giving the mountain a softer summer feeling.",
            "🌿 The warmth of Greenleaf remains, but a cooler edge moves through the air.",
            "☁️ The mountain rests in gentle Greenleaf coolness, a welcome break from heavier heat."
        ],
        "neutral": [
            "🌿 Greenleaf is full across the mountain, with thick leaves, warm air, and busy trails.",
            "🌾 The territory hums with summer life, from buzzing insects to prey moving through the grass.",
            "🌿 The forest feels rich and crowded with life, every den and trail warmed by Greenleaf.",
            "🌳 Thick greenery covers the mountain, filling the air with the scent of leaves and sun-warmed earth.",
            "🌿 Greenleaf holds the territories in full bloom, bright, noisy, and alive."
        ]
    },

    "Leaf-fall": {
        "wet": [
            "🌧️ Cold rain darkens the fallen leaves, turning the trails slick beneath every pawstep.",
            "🍂 Rain clings to the fading leaves, weighing down the undergrowth and sharpening the scent of earth.",
            "🌧️ Leaf-fall rain sweeps through the territory, washing colour from the trees and mud onto the paths.",
            "🌫️ Damp air settles over the mountain, heavy with the smell of wet leaves and colder days ahead.",
            "🌧️ Rain patters through thinning branches, making the forest feel quieter and colder."
        ],
        "clear": [
            "🍂 Clear Leaf-fall skies brighten the golden leaves, making the whole mountain glow.",
            "☀️ Pale sunlight spills through thinning branches, lighting the forest in amber and brown.",
            "🍁 The territory shines beneath a clear Leaf-fall sky, crisp and bright underpaw.",
            "☀️ Cold sunlight catches on the fallen leaves, giving the mountain a sharp golden beauty.",
            "🍂 Clear air stretches across the territory, making every colour of Leaf-fall stand out."
        ],
        "cloudy": [
            "☁️ Grey clouds hang over the Leaf-fall forest, dulling the colours but keeping the air steady.",
            "🍂 A muted sky settles above the territory, while dry leaves gather along the trails.",
            "☁️ The mountain rests beneath heavy clouds, quiet with the feeling of colder moons approaching.",
            "🌥️ Cloud cover softens the Leaf-fall light, leaving the forest cool and watchful.",
            "☁️ The sky is pale and dim, but the forest remains calm beneath its thinning canopy."
        ],
        "windy": [
            "🍃 Wind scatters leaves across the trails, sending them skittering over roots and stones.",
            "🌬️ A sharp Leaf-fall breeze rattles the branches and pulls more leaves from the trees.",
            "🍂 Gusts move through the territory, making the fallen leaves dance underpaw.",
            "🌬️ The forest whispers and cracks beneath the wind, each branch warning of colder moons ahead.",
            "🍁 Fresh wind carries the scent of dry leaves, damp bark, and distant frost."
        ],
        "cold": [
            "❄️ A cold bite lingers in the Leaf-fall air, warning that leaf-bare is drawing closer.",
            "🍂 Frost touches the grass in shaded places, silvering the edges of fallen leaves.",
            "🌬️ The air is crisp and cold, making every breath feel sharper on the mountain.",
            "🍁 Leaf-fall has turned chilly, with frost hiding in the roots and cold air under the trees.",
            "❄️ The mountain feels colder now, the warmth of Greenleaf fading with every fallen leaf."
        ],
        "neutral": [
            "🍂 Leaf-fall has painted the mountain in gold, brown, and fading green.",
            "🍁 The forest is thinning, with fallen leaves gathering in dens, trails, and sheltered hollows.",
            "🍂 The territory feels watchful beneath the changing leaves, preparing for the cold ahead.",
            "🍁 Leaf-fall settles over the mountain, crisp, colourful, and quietly restless.",
            "🍂 The air smells of dry leaves and damp earth as the forest shifts toward leaf-bare."
        ]
    },

    "Leafbare": {
        "wet": [
            "🌨️ Frozen rain coats the territory, turning branches and stones slick beneath the cold sky.",
            "❄️ Snow falls across the mountain, softening every sound and hiding old scent trails.",
            "🌨️ Ice and snow cling to the forest, making the territory glitter but dangerous.",
            "❄️ Leaf-bare weather presses heavily over the mountain, covering paths and dens in cold white.",
            "🌨️ Snow drifts through the trees, leaving the forest quiet, pale, and difficult to cross."
        ],
        "clear": [
            "☀️ Pale winter sun shines over the frozen territory, bright against the snow.",
            "❄️ Clear Leafbare skies make the mountain glitter with frost and hard-packed snow.",
            "☀️ Cold sunlight spills across the territory, offering brightness without much warmth.",
            "❄️ The forest is sharp and clear beneath the winter sky, every movement easy to spot.",
            "☀️ A calm winter brightness settles over the mountain, turning frost into silver."
        ],
        "cloudy": [
            "☁️ Grey winter clouds hang low over the territory, heavy with the promise of more snow.",
            "❄️ The sky is dull and cold, leaving the forest quiet beneath a blanket of cloud.",
            "☁️ Cloud cover dims the snowlight, softening the frozen trails and shaded dens.",
            "🌨️ Pale clouds stretch above the mountain, holding the cold close to the ground.",
            "☁️ The territory feels hushed beneath the winter clouds, still and watchful."
        ],
        "windy": [
            "🌬️ Bitter wind cuts across the mountain, pulling at fur and scattering loose snow.",
            "❄️ Wind drives cold through the trees, making the frozen branches creak overhead.",
            "🌬️ Leaf-bare gusts sweep over the territory, carrying ice crystals and broken scent trails.",
            "❄️ The forest shudders beneath the wind, every den and hollow feeling the cold.",
            "🌬️ A hard winter wind moves through the mountain, sharp enough to make patrols lower their heads."
        ],
        "cold": [
            "🧊 Deep cold grips the mountain, sinking into stone, snow, and frozen earth.",
            "❄️ The territory lies under a hard Leafbare chill, with prey hidden deep and dens packed tight.",
            "🧊 Frost clings to every branch and blade of grass, making the forest glitter in silence.",
            "❄️ The cold is heavy across the mountain, slowing movement and stealing warmth from every pawstep.",
            "🧊 Leaf-bare holds the territory firmly, frozen and unforgiving beneath the pale sky."
        ],
        "neutral": [
            "❄️ Leaf-bare has settled over the mountain, quieting the forest beneath frost and snow.",
            "🌨️ The territory feels still and cold, with every trail marked by frozen pawprints.",
            "❄️ Snow and frost shape the forest now, muting scent and sound beneath the trees.",
            "🌨️ The mountain is deep in leaf-bare, harsh but beautiful beneath its winter covering.",
            "❄️ The clans move carefully through the frozen territory, saving strength where they can."
        ]
    }
}

WEATHER_BY_SEASON = {
    "Newleaf": [
        ("Heavy rain", -2, "Heavy rain churns the trails into mud, blurring scent and making every pawstep heavier."),
        ("Cold rain", -2, "Cold rain soaks through fur and keeps most prey tucked deep in shelter."),
        ("Thunder showers", -2, "Thunder rolls over the mountain, startling birds from the trees and sending small prey underground."),
        ("Thick mist", -1, "Mist curls between the trunks, softening shapes and making movement harder to track."),
        ("Wet ground", -1, "The forest floor is slick and muddy, weakening scent trails and slowing patrols."),
        ("Chilly drizzle", -1, "A damp chill lingers in the air, making hunting uncomfortable and prey cautious."),
        ("Cloudy", 0, "Cloud cover keeps the forest calm and dim, with steady but unremarkable hunting conditions."),
        ("Soft breeze", 0, "A soft breeze moves through the trees without helping or hurting the hunt."),
        ("Cool", 0, "The air is cool and steady, comfortable enough for patrols to move without trouble."),
        ("Overcast skies", 0, "Grey skies hang over the territory, but the forest remains manageable."),
        ("Damp forest", 0, "The ground is damp and the air smells of wet moss, though hunting remains steady."),
        ("Fresh newleaf air", 0, "The territory feels awake with fresh scents, though prey remains cautious."),
        ("Light clouds", 0, "Light clouds drift overhead, giving patrols easy travelling weather."),
        ("Quiet drizzle", 0, "A gentle drizzle falls through the branches, soft enough to cause little trouble."),
        ("Sunny breaks", 1, "Warm light breaks through the clouds, drawing prey out between patches of shade."),
        ("Warm breeze", 1, "A warm breeze carries scent gently through the territory, helping hunters track movement."),
        ("Clear skies", 1, "Clear skies brighten the forest, making prey movement easier to spot."),
        ("Fresh growth", 1, "New shoots and soft greenery draw small prey into the open."),
        ("Mild sunshine", 2, "Pleasant warmth spreads through the territory, coaxing prey from their hiding places."),
        ("Sunny", 2, "Bright sun warms the forest floor, creating strong hunting conditions across the territory.")
    ],

    "Greenleaf": [
        ("Thunderstorm", -3, "Thunder and heavy rain shake the canopy, scattering prey and making patrols difficult."),
        ("Heat haze", -2, "Heavy heat presses over the territory, pushing prey into deep shade and slowing hunters."),
        ("Dry wind", -1, "Dry wind tugs scent trails apart, making tracking unreliable."),
        ("Sudden downpour", -1, "A fast burst of rain interrupts patrols and sends prey scrambling for cover."),
        ("Warm and cloudy", 0, "Warm clouds hang overhead, leaving the forest comfortable but ordinary."),
        ("Still air", 0, "The air is still and heavy, making the forest feel watchful and quiet."),
        ("Humid", 0, "Humidity clings to the grass and leaves, but prey continues moving."),
        ("Cloudy with sun", 0, "Mixed skies bring average hunting conditions, with shifting light across the trails."),
        ("Light summer rain", 0, "A gentle rain cools the territory without causing much trouble."),
        ("Mild", 0, "The weather is mild and steady, giving patrols an easy day across the territory."),
        ("Sunny", 2, "Warm sun brings prey into the open and brightens the hunting trails."),
        ("Partly cloudy", 1, "Patchy cloud cover gives hunters good light with enough shade to move quietly."),
        ("Light breeze", 1, "A light breeze carries scent clearly through the territory."),
        ("Golden sunshine", 2, "Rich sunlight warms the forest, making prey active and easier to spot."),
        ("Clear skies", 2, "Clear weather gives hunters sharp visibility and easy travelling conditions."),
        ("Dry paths", 1, "Dry paths make travel quiet and easy for hunting patrols."),
        ("Cool shade", 1, "Cool pockets of shade keep prey moving instead of hiding from the heat."),
        ("Fresh breeze", 1, "Fresh air moves through the leaves, helping hunters catch scent."),
        ("Ideal hunting conditions", 2, "The territory is full of movement, scent, and opportunity."),
        ("Warm and calm", 2, "Soft warmth settles over the territory, keeping prey active and patrols comfortable.")
    ],

    "Leaf-fall": [
        ("Cold rain", -2, "Cold rain darkens the leaves and makes hunting uncomfortable and difficult."),
        ("Foggy", -2, "Fog pools low between the trees, making it hard to see movement clearly."),
        ("Windy", -1, "Wind rattles the branches and scatters scent trails across the territory."),
        ("Wet leaves", -1, "Wet leaves cling to the ground, making pawsteps slippery and quiet movement harder."),
        ("Early frost", -1, "Frost bites at the grass and keeps prey hidden in warmer dens."),
        ("Sharp gusts", -2, "Strong gusts tear through the trees, making scent unreliable and patrols tiring."),
        ("Cloudy and cool", 0, "The air is cool and the sky is dull, but hunting remains manageable."),
        ("Grey skies", 0, "A grey sky hangs over the territory, gloomy but steady."),
        ("Dry leaves", 0, "Dry leaves crunch beneath pawsteps, though careful hunters can still find prey."),
        ("Cool breeze", 0, "A cool breeze moves through the trees without becoming too harsh."),
        ("Quiet forest", 0, "The territory feels still and watchful, with average hunting conditions."),
        ("Pale sunlight", 0, "Weak sunlight filters through thinning branches, offering just enough visibility."),
        ("Crisp", 0, "The air is crisp and clean, but prey remains cautious."),
        ("Damp air", 0, "Damp leaf-fall air hangs over the trails, though hunting remains normal."),
        ("Crisp and clear", 1, "Clear air sharpens scent and sight, helping patrols track movement."),
        ("Fresh leaf-fall breeze", 1, "A fresh breeze carries scent cleanly through the thinning trees."),
        ("Dry and clear", 1, "Dry ground and clear skies help hunting patrols move quietly."),
        ("Bright cold sun", 1, "Cold sunlight brightens the leaves and helps cats spot prey movement."),
        ("Prey gathering weather", 2, "Prey is active while gathering food before leaf-bare, giving hunters a strong advantage."),
        ("Mild and golden", 2, "Mild air and golden leaves draw prey into the open.")
    ],

    "Leafbare": [
        ("Heavy snow", -4, "Deep snow weighs down the territory, covering scent and making every hunt difficult."),
        ("Snow", -3, "Snow covers tracks and muffles prey movement, leaving hunters with little to follow."),
        ("Freezing fog", -3, "Freezing fog clouds the forest, making it hard to see or scent prey."),
        ("Ice crust", -2, "A crust of ice makes travel dangerous, noisy, and slow."),
        ("Bitter wind", -2, "Bitter wind cuts through fur and scatters scent across the frozen ground."),
        ("Blizzard", -4, "A blizzard lashes the territory, making hunting nearly impossible."),
        ("Frozen rain", -3, "Frozen rain coats branches and paths in slick ice, making patrols risky."),
        ("Deep cold", -2, "The cold sinks into the earth, keeping prey hidden and cats tired."),
        ("Clear and cold", 0, "The cold is sharp, but visibility is good enough for careful patrols."),
        ("Cloudy with flurries", 0, "Light flurries drift through the air without causing much trouble."),
        ("Still winter air", 0, "The air is cold and still, leaving the forest quiet but manageable."),
        ("Pale winter sun", 0, "Weak sunlight brightens the snow, helping patrols see movement."),
        ("Hard-packed snow", 0, "Firm snow makes travel easier than fresh drifts."),
        ("Quiet and frozen", 0, "The forest is frozen and still, but manageable for steady patrols."),
        ("Cold and cloudy", 0, "The sky is grey and the air is cold, but conditions remain stable."),
        ("Light frost", 0, "Frost covers the ground without fully stopping patrols."),
        ("Fresh tracks", 1, "Fresh tracks mark the snow, giving hunters something useful to follow."),
        ("Bright snowlight", 1, "Snow reflects the light and makes small movements easier to spot."),
        ("Calm winter sun", 1, "A rare calm settles over the territory, helping hunting patrols move with care."),
        ("Brief thaw", 2, "A brief thaw softens the snow and brings prey out from shelter.")
    ]
}


def get_weather_opener_category(weather, modifier):
    weather_lower = weather.lower()

    wet_words = [
        "rain", "drizzle", "shower", "downpour", "thunder",
        "snow", "blizzard", "flurries", "fog", "mist"
    ]

    clear_words = [
        "sun", "sunny", "clear", "golden", "bright", "snowlight"
    ]

    cloudy_words = [
        "cloud", "overcast", "grey"
    ]

    windy_words = [
        "wind", "breeze", "gust"
    ]

    cold_words = [
        "cold", "frost", "frozen", "freezing", "ice", "thaw"
    ]

    if any(word in weather_lower for word in wet_words):
        return "wet"

    if any(word in weather_lower for word in clear_words):
        return "clear"

    if any(word in weather_lower for word in cloudy_words):
        return "cloudy"

    if any(word in weather_lower for word in windy_words):
        return "windy"

    if any(word in weather_lower for word in cold_words):
        return "cold"

    if modifier > 0:
        return "clear"

    if modifier < 0:
        return "cold"

    return "neutral"


def generate_weekly_weather_details():
    """Generate the normal weekly weather and keep the raw condition available to severe weather."""
    now = datetime.now(TZ)
    averages = BANFF_MONTHLY_AVERAGES[now.month]
    season = data.get("season", get_current_season())

    weather, modifier, reason = random.choice(
        WEATHER_BY_SEASON.get(season, WEATHER_BY_SEASON["Newleaf"])
    )

    opener_category = get_weather_opener_category(weather, modifier)

    opener_options = (
        SEASONAL_OPENERS
        .get(season, SEASONAL_OPENERS["Newleaf"])
        .get(opener_category, [])
    )

    if not opener_options:
        opener_options = (
            SEASONAL_OPENERS
            .get(season, SEASONAL_OPENERS["Newleaf"])
            .get("neutral", [])
        )

    opener = random.choice(opener_options)
    avg_temp = random.randint(averages["low"], averages["high"])
    modifier_text = f"+{modifier}" if modifier > 0 else str(modifier)

    report = (
        f"{opener}\n\n"
        f"🍃 Season: {season}\n"
        f"🌡️ Average Temp: {avg_temp}°C\n"
        f"☁️ Weekly Weather: {weather}\n"
        f"🎯 Hunting Modifier: {modifier_text}\n"
        f"📖 Effect: {reason}"
    )

    return {
        "generated_at": now.isoformat(),
        "season": season,
        "average_temp": avg_temp,
        "weather": weather,
        "modifier": modifier,
        "reason": reason,
        "opener": opener,
        "report": report
    }


def generate_weekly_weather():
    return generate_weekly_weather_details()["report"]


# ─────────────────────────────
# SEVERE WEATHER SYSTEM
# ─────────────────────────────

SEVERE_EFFECT_TYPE_LABELS = {
    "hunting": "hunting rolls",
    "fishing": "fishing rolls",
    "both": "hunting and fishing rolls",
    "none": "prey rolls"
}

SEVERE_EFFECT_TYPE_CHOICES = [
    app_commands.Choice(name="Hunting", value="hunting"),
    app_commands.Choice(name="Fishing", value="fishing"),
    app_commands.Choice(name="Hunting + Fishing", value="both"),
    app_commands.Choice(name="No Roll Modifier", value="none")
]

SEVERE_ROLL_TYPE_CHOICES = [
    app_commands.Choice(name="Hunting", value="hunting"),
    app_commands.Choice(name="Fishing", value="fishing")
]

SEVERE_TIER_WEIGHTS = {
    "local": 50,
    "territory": 35,
    "major": 15
}

SHARED_SEVERE_EVENTS = [
    {
        "key": "severe_thunderstorms",
        "name": "Severe Thunderstorms",
        "emoji": "⛈️",
        "tier": "territory",
        "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
        "regional": True,
        "description": "A powerful storm system crashes across the mountain with lightning, torrential rain, and violent gusts. Prey takes shelter and exposed routes become dangerous.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Thunder, rain, and erratic wind make hunting difficult."}
        ],
        "target_overrides": {
            "TorrentClan": [
                {"location": "Entire Territory", "modifier": -2, "type": "both", "note": "Hunting and fishing are both disrupted by swollen water and storm conditions."}
            ]
        },
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "Distant thunder, rain, and gusty wind disturb prey at the edge of the storm."
    },
    {
        "key": "violent_windstorm",
        "name": "Violent Windstorm",
        "emoji": "🌬️",
        "tier": "territory",
        "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
        "regional": True,
        "description": "Powerful sustained winds tear across Echostone Mountain. Scent trails scatter, branches strain, and birds disappear into shelter.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Strong winds scatter scent and make stalking difficult."}
        ],
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "Strong gusts reach the outer territory and make scent less reliable."
    },
    {
        "key": "extreme_heatwave",
        "name": "Extreme Heatwave",
        "emoji": "☀️",
        "tier": "territory",
        "seasons": ["Greenleaf"],
        "regional": True,
        "requires_dry": True,
        "description": "A stretch of oppressive heat settles over the mountain. Prey hides through the hottest hours and cats tire faster while travelling.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Prey stays hidden during the hottest parts of the day."}
        ],
        "target_overrides": {
            "TorrentClan": [
                {"location": "Entire Territory", "modifier": -1, "type": "both", "note": "Access to water helps TorrentClan cope, but prey and fish are still less active."}
            ]
        },
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "The edge of the heatwave still makes prey less active."
    },
    {
        "key": "cold_snap",
        "name": "Sudden Cold Snap",
        "emoji": "🥶",
        "tier": "territory",
        "seasons": ["Leaf-fall", "Leafbare", "Newleaf"],
        "regional": True,
        "description": "Temperatures suddenly plunge. The ground hardens, small prey retreats underground, and exposed patrol routes become sharply colder.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Prey retreats into warmer shelter."}
        ],
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "A weaker edge of the cold snap reaches the territory."
    },
    {
        "key": "ice_storm",
        "name": "Severe Ice Storm",
        "emoji": "🌨️",
        "tier": "major",
        "seasons": ["Leaf-fall", "Leafbare", "Newleaf"],
        "regional": True,
        "description": "Freezing rain coats stone, branches, roots, and paths in dangerous ice. Travelling becomes slow and prey is difficult to reach.",
        "effects": [
            {"location": "Entire Territory", "modifier": -3, "type": "hunting", "note": "Ice makes travel, stalking, and pouncing hazardous."}
        ],
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "Patchy ice reaches the edge of the storm system."
    },
    {
        "key": "severe_hailstorm",
        "name": "Severe Hailstorm",
        "emoji": "🧊",
        "tier": "territory",
        "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
        "regional": True,
        "description": "Large hail sweeps across exposed ground and hammers the canopy. Most prey stays hidden until the storm system passes.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Hail drives prey into shelter."}
        ],
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "Scattered hail and storm winds reach the outer edge."
    },
    {
        "key": "torrential_rain",
        "name": "Torrential Rain",
        "emoji": "🌧️",
        "tier": "territory",
        "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
        "regional": True,
        "description": "Relentless rain soaks the mountain, washes away scent trails, and turns low ground into mud and standing water.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Rain washes scent away and drives prey into shelter."}
        ],
        "target_overrides": {
            "TorrentClan": [
                {"location": "Entire Territory", "modifier": -2, "type": "both", "note": "Rain disrupts land prey while swollen water makes fishing difficult."}
            ]
        },
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "Steady rain reaches the outer territory and weakens scent trails."
    },
    {
        "key": "wildfire_smoke",
        "name": "Wildfire Smoke",
        "emoji": "🌫️",
        "tier": "territory",
        "seasons": ["Greenleaf", "Leaf-fall"],
        "regional": True,
        "description": "Smoke from a distant wildfire drifts across Echostone Mountain. Visibility drops and the sharp scent of smoke overwhelms normal prey trails.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Smoke reduces visibility and masks scent."}
        ],
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "A thinner veil of smoke reaches the territory."
    },
    {
        "key": "severe_blizzard",
        "name": "Severe Blizzard",
        "emoji": "❄️",
        "tier": "major",
        "seasons": ["Leafbare"],
        "regional": True,
        "description": "A severe blizzard sweeps over the mountain. Snow, wind, and near-whiteout visibility bury scent and force most prey deep into shelter.",
        "effects": [
            {"location": "Entire Territory", "modifier": -3, "type": "hunting", "note": "Snow and whiteout conditions make hunting extremely difficult."}
        ],
        "target_overrides": {
            "TorrentClan": [
                {"location": "Entire Territory", "modifier": -3, "type": "both", "note": "Snow and ice disrupt both land hunting and fishing access."}
            ]
        },
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "Heavy snow and wind reach the outer edge of the blizzard."
    },
    {
        "key": "heavy_snowdrifts",
        "name": "Heavy Snowdrifts",
        "emoji": "🌨️",
        "tier": "territory",
        "seasons": ["Leafbare"],
        "regional": True,
        "description": "Deep drifting snow piles across familiar routes and buries the entrances to many prey shelters.",
        "effects": [
            {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Deep snow slows travel and hides small prey."}
        ],
        "secondary_modifier": -1,
        "secondary_type": "hunting",
        "secondary_note": "Lighter drifting snow reaches the territory."
    }
]

CLAN_SEVERE_EVENTS = {
    "BlizzardClan": [
        {
            "key": "blizzard_avalanche",
            "name": "Avalanche at Glacier's Edge",
            "emoji": "🏔️",
            "tier": "major",
            "seasons": ["Leafbare", "Newleaf"],
            "regional": False,
            "description": "A slab of unstable snow breaks loose above Glacier's Edge, burying familiar paths beneath packed snow and broken ice. No cats are automatically injured; any story consequences are left to RP.",
            "effects": [
                {"location": "Glacier's Edge", "modifier": -3, "type": "hunting", "note": "Fresh avalanche debris makes the hunting ground unstable and difficult to cross."}
            ]
        },
        {
            "key": "blizzard_whiteout",
            "name": "Whiteout Over BlizzardClan",
            "emoji": "🌨️",
            "tier": "major",
            "seasons": ["Leafbare"],
            "regional": False,
            "description": "A brutal whiteout swallows BlizzardClan's exposed territory. The Hollow of Teeth remains shelter, but visibility outside drops to almost nothing.",
            "effects": [
                {"location": "Entire Territory", "modifier": -3, "type": "hunting", "note": "Visibility and scent are nearly erased by blowing snow."}
            ]
        },
        {
            "key": "blizzard_rockfall",
            "name": "Rockfall at Glacier's Edge",
            "emoji": "🪨",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "Weather-loosened stone breaks from the mountain face and crashes across part of Glacier's Edge.",
            "effects": [
                {"location": "Glacier's Edge", "modifier": -2, "type": "hunting", "note": "Loose rock and blocked routes make hunting more difficult."}
            ]
        },
        {
            "key": "blizzard_frozen_teeth_icefall",
            "name": "Frozen Teeth Icefall",
            "emoji": "🧊",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "Rapid temperature changes crack several of the Frozen Teeth loose inside the Hollow of Teeth. Parts of camp are temporarily hazardous while cats keep clear of unstable ice.",
            "effects": [
                {"location": "The Hollow of Teeth", "modifier": 0, "type": "none", "note": "Camp RP hazard only. Hunting and fishing are unaffected."}
            ]
        },
        {
            "key": "blizzard_frost_tunnel_collapse",
            "name": "Ice Collapse in the Frost Tunnels",
            "emoji": "🧊",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "A section of old ice fractures inside the Frost Tunnels, blocking familiar passages and forcing hunters through tighter routes.",
            "effects": [
                {"location": "Frost Tunnels", "modifier": -2, "type": "hunting", "note": "Blocked passages make tunnel hunting much harder."}
            ]
        },
        {
            "key": "blizzard_cloud_plateau_gale",
            "name": "Gale on Cloud Plateau",
            "emoji": "🌬️",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "A fierce high-altitude gale tears across Cloud Plateau, scattering scent and making the exposed rockland difficult to cross.",
            "effects": [
                {"location": "Cloud Plateau", "modifier": -2, "type": "hunting", "note": "Powerful crosswinds ruin scent and balance."}
            ]
        }
    ],
    "FossilClan": [
        {
            "key": "fossil_dust_storm",
            "name": "Dust Storm",
            "emoji": "🌪️",
            "tier": "territory",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_dry": True,
            "description": "Powerful wind tears dust and grit from the exposed stone, swallowing FossilClan territory beneath a reddish haze.",
            "effects": [
                {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Dust ruins visibility and scent."},
                {"location": "Dustwind Flats", "modifier": -3, "type": "hunting", "note": "The exposed Flats take the worst of the storm."}
            ]
        },
        {
            "key": "fossil_sandstorm",
            "name": "Sandstorm on Dustwind Flats",
            "emoji": "🌪️",
            "tier": "major",
            "seasons": ["Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_dry": True,
            "description": "A dense wall of windblown grit races across Dustwind Flats. Cats caught in the open have little visibility until it passes.",
            "effects": [
                {"location": "Dustwind Flats", "modifier": -3, "type": "hunting", "note": "Blowing grit makes tracking and visibility extremely poor."}
            ]
        },
        {
            "key": "fossil_raptorfang_rockslide",
            "name": "Rockslide at Raptorfang Spires",
            "emoji": "🪨",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "Stone breaks loose from the narrow Raptorfang Spires and tumbles across several climbing routes.",
            "effects": [
                {"location": "Raptorfang Spires", "modifier": -3, "type": "hunting", "note": "Unstable ledges and debris make hunting dangerous."}
            ]
        },
        {
            "key": "fossil_ground_collapse",
            "name": "Ground Collapse on Dustwind Flats",
            "emoji": "🕳️",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "Loose earth gives way beneath part of Dustwind Flats, opening a dangerous depression and disturbing prey routes.",
            "effects": [
                {"location": "Dustwind Flats", "modifier": -2, "type": "hunting", "note": "Broken ground disrupts running and tracking."}
            ]
        },
        {
            "key": "fossil_drought",
            "name": "Extreme Drought",
            "emoji": "☀️",
            "tier": "major",
            "seasons": ["Greenleaf"],
            "regional": False,
            "requires_dry": True,
            "description": "Long-lasting heat and dry air leave FossilClan's exposed territory parched. Small prey travels less and stays close to hidden water.",
            "effects": [
                {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Prey movement drops sharply during the drought."}
            ]
        },
        {
            "key": "fossil_red_rock_cliff_crumble",
            "name": "Cliff Crumble at the Red Rock",
            "emoji": "🪨",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "A weathered section of the cliff above the Red Rock sheds loose stone. Camp routes near the edge are treated with extra caution.",
            "effects": [
                {"location": "The Red Rock", "modifier": 0, "type": "none", "note": "Camp RP hazard only. Hunting is unaffected."}
            ]
        },
        {
            "key": "fossil_rexhead_wind_shear",
            "name": "Wind Shear at Rexhead Pillars",
            "emoji": "🌬️",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "Sudden crosswinds slam into the broad ledges of Rexhead Pillars, making leaps and aerial prey much harder to judge.",
            "effects": [
                {"location": "Rexhead Pillars", "modifier": -2, "type": "hunting", "note": "Strong crosswinds interfere with balance and prey movement."}
            ]
        }
    ],
    "TorrentClan": [
        {
            "key": "torrent_camp_flood",
            "name": "Camp Flood",
            "emoji": "🌊",
            "tier": "major",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_wet": True,
            "description": "Persistent rain and swollen water push the tide beyond its normal reach. Parts of the Island are flooded and cats may need to move nests or supplies to higher ground. No cats or herbs are automatically harmed.",
            "effects": [
                {"location": "Trout Run", "modifier": -2, "type": "both", "note": "Swollen rapids make hunting and fishing difficult."},
                {"location": "Reedmarsh", "modifier": -2, "type": "both", "note": "Floodwater disturbs prey and deepens the marsh."},
                {"location": "The Island", "modifier": 0, "type": "none", "note": "Camp RP effect only. Story consequences are left to players and staff."}
            ]
        },
        {
            "key": "torrent_river_flooding",
            "name": "River Flooding",
            "emoji": "🌊",
            "tier": "territory",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_wet": True,
            "description": "The river rises over familiar banks and covers normally safe stones around Trout Run.",
            "effects": [
                {"location": "Trout Run", "modifier": -2, "type": "both", "note": "High water makes fishing, land prey tracking, and crossings difficult."}
            ]
        },
        {
            "key": "torrent_flash_flood",
            "name": "Flash Flood in Reedmarsh",
            "emoji": "🌊",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "description": "A sudden rush of water tears through Reedmarsh, flooding reed tunnels and muddying the hunting ground.",
            "effects": [
                {"location": "Reedmarsh", "modifier": -3, "type": "both", "note": "Fast water and deep mud make prey extremely difficult to catch."}
            ]
        },
        {
            "key": "torrent_dangerous_rapids",
            "name": "Dangerous Rapids",
            "emoji": "🌊",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "description": "Snowmelt or upstream rain turns Trout Run into a violent torrent. Fish remain present, but reaching them is much more dangerous.",
            "effects": [
                {"location": "Trout Run", "modifier": -2, "type": "fishing", "note": "Fishing is disrupted by dangerous current speed."}
            ]
        },
        {
            "key": "torrent_frozen_river",
            "name": "Frozen River",
            "emoji": "🧊",
            "tier": "major",
            "seasons": ["Leafbare"],
            "regional": False,
            "description": "A brutal stretch of cold seals much of Trout Run beneath thick, uneven ice. TorrentClan cats can still travel, play, train, and slide across the ice, but reaching fish requires finding or breaking open water.",
            "effects": [
                {"location": "Trout Run", "modifier": -6, "type": "fishing", "note": "Fishing is nearly impossible through the thick ice. Land hunting is unaffected."}
            ]
        },
        {
            "key": "torrent_glistening_overflow",
            "name": "Glistening Pools Overflow",
            "emoji": "💧",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_wet": True,
            "description": "Heavy runoff causes the Glistening Pools to spill over their banks and merge through the low ground.",
            "effects": [
                {"location": "Glistening Pools", "modifier": -2, "type": "both", "note": "Cloudy water and flooded banks disturb both fish and land prey."}
            ]
        },
        {
            "key": "torrent_high_tide_surge",
            "name": "High Tide Surge",
            "emoji": "🌊",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "An unusually high tide surrounds the Island and pushes water farther through the roots than normal.",
            "effects": [
                {"location": "The Island", "modifier": 0, "type": "none", "note": "Camp and travel RP effect only. Hunting is unaffected."}
            ]
        }
    ],
    "SpruceClan": [
        {
            "key": "spruce_whispering_fire",
            "name": "Fire at Whispering Branches",
            "emoji": "🔥",
            "tier": "major",
            "seasons": ["Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_dry": True,
            "description": "After dry weather, a small localized fire breaks out around Whispering Branches. It does not automatically injure cats or destroy camp, but smoke and scorched undergrowth drive prey from the area.",
            "effects": [
                {"location": "Whispering Branches", "modifier": -3, "type": "hunting", "note": "The affected hunting ground is smoky and prey has scattered."}
            ]
        },
        {
            "key": "spruce_fallen_trees",
            "name": "Fallen Trees at Whispering Branches",
            "emoji": "🌲",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
            "regional": False,
            "description": "Storm-weakened spruce trees fall through part of Whispering Branches, blocking familiar paths and scattering canopy prey.",
            "effects": [
                {"location": "Whispering Branches", "modifier": -2, "type": "hunting", "note": "Blocked paths and disturbed prey make hunting harder."}
            ]
        },
        {
            "key": "spruce_deeproot_mudslide",
            "name": "Mudslide at Deeproot Tangle",
            "emoji": "🟤",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_wet": True,
            "description": "Saturated earth gives way around Deeproot Tangle, filling hollows with mud and shifting the root maze.",
            "effects": [
                {"location": "Deeproot Tangle", "modifier": -2, "type": "hunting", "note": "Mud and shifted roots make the hunting ground harder to navigate."}
            ]
        },
        {
            "key": "spruce_dense_fog",
            "name": "Dense Forest Fog",
            "emoji": "🌫️",
            "tier": "territory",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "description": "Dense fog settles beneath the evergreen canopy. Shapes vanish between the trunks and even familiar paths become difficult to read.",
            "effects": [
                {"location": "Entire Territory", "modifier": -2, "type": "hunting", "note": "Poor visibility makes tracking and pouncing difficult."}
            ]
        },
        {
            "key": "spruce_sundance_flood",
            "name": "Sundance Pond Flood",
            "emoji": "💧",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_wet": True,
            "description": "Heavy runoff raises Sundance Pond over its usual banks and clouds the shallows.",
            "effects": [
                {"location": "Sundance Pond", "modifier": -2, "type": "both", "note": "Flooded banks and cloudy water disturb prey."}
            ]
        },
        {
            "key": "spruce_canopy_ice",
            "name": "Ice-Heavy Canopy",
            "emoji": "🌨️",
            "tier": "major",
            "seasons": ["Leafbare"],
            "regional": False,
            "description": "Freezing rain coats the evergreen canopy until branches sag and crack beneath the weight. Different hunting grounds feel the storm at different strengths.",
            "effects": [
                {"location": "Whispering Branches", "modifier": -3, "type": "hunting", "note": "Falling ice and strained branches make canopy hunting extremely difficult."},
                {"location": "Deeproot Tangle", "modifier": -2, "type": "hunting", "note": "Ice and fallen debris clog the root maze."},
                {"location": "Sundance Pond", "modifier": -1, "type": "hunting", "note": "Icy banks make land hunting less reliable."}
            ]
        },
        {
            "key": "spruce_root_washout",
            "name": "Root Washout",
            "emoji": "🌧️",
            "tier": "local",
            "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
            "regional": False,
            "requires_wet": True,
            "description": "Heavy rain washes soil from beneath part of the forest floor, exposing unstable roots and opening new gaps around Deeproot Tangle.",
            "effects": [
                {"location": "Deeproot Tangle", "modifier": -2, "type": "hunting", "note": "Unstable roots and washed-out ground make hunting more difficult."}
            ]
        }
    ]
}

OUTSIDER_SEVERE_EVENTS = [
    {
        "key": "outsider_frostbite_gale",
        "name": "Extreme Gale at Frostbite Ridge",
        "emoji": "🌬️",
        "tier": "local",
        "seasons": ["Newleaf", "Greenleaf", "Leaf-fall", "Leafbare"],
        "regional": False,
        "description": "Extreme wind screams across Frostbite Ridge. Birds struggle against the gusts and narrow ledges become especially dangerous.",
        "effects": [
            {"location": "Frostbite Ridge", "modifier": -3, "type": "hunting", "note": "Crosswinds make bird hunting and balance extremely difficult."}
        ]
    },
    {
        "key": "outsider_frostbite_ice",
        "name": "Ice-Coated Frostbite Ridge",
        "emoji": "🧊",
        "tier": "local",
        "seasons": ["Leaf-fall", "Leafbare", "Newleaf"],
        "regional": False,
        "description": "Freezing moisture coats Frostbite Ridge in slick ice, turning already dangerous ledges into glassy footing.",
        "effects": [
            {"location": "Frostbite Ridge", "modifier": -3, "type": "hunting", "note": "Icy footing makes hunting on the cliffs extremely difficult."}
        ]
    },
    {
        "key": "outsider_sanctuary_flood",
        "name": "Sanctuary Field Flooding",
        "emoji": "🌧️",
        "tier": "local",
        "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
        "regional": False,
        "requires_wet": True,
        "description": "Heavy rain floods low sections of the Sanctuary fields and drives barn mice deeper into dry storage areas.",
        "effects": [
            {"location": "The Sanctuary", "modifier": -1, "type": "hunting", "note": "The Sanctuary remains safe, but mice are less exposed than usual."}
        ]
    },
    {
        "key": "outsider_neon_flash_flood",
        "name": "Flash Flood at the Neon Path",
        "emoji": "🌊",
        "tier": "local",
        "seasons": ["Newleaf", "Greenleaf", "Leaf-fall"],
        "regional": False,
        "description": "Storm drains overflow around the Neon Path, sending dirty water across concrete and around the dumpsters.",
        "effects": [
            {"location": "The Neon Path", "modifier": -2, "type": "hunting", "note": "Floodwater scatters rodents and makes the plaza difficult to cross."}
        ]
    },
    {
        "key": "outsider_town_ice",
        "name": "Twoleg Town Ice Storm",
        "emoji": "🌨️",
        "tier": "local",
        "seasons": ["Leaf-fall", "Leafbare", "Newleaf"],
        "regional": False,
        "description": "Freezing rain coats fences, paths, and rooftops throughout Twoleg Town.",
        "effects": [
            {"location": "The Twoleg Town", "modifier": -2, "type": "hunting", "note": "Icy footing makes the few available prey opportunities harder to reach."}
        ]
    },
    {
        "key": "outsider_neon_heat",
        "name": "Concrete Heat at the Neon Path",
        "emoji": "☀️",
        "tier": "local",
        "seasons": ["Greenleaf"],
        "regional": False,
        "requires_dry": True,
        "description": "Extreme heat radiates from the concrete around the Neon Path. Rodents and scavengers retreat into cooler hiding places.",
        "effects": [
            {"location": "The Neon Path", "modifier": -1, "type": "hunting", "note": "Prey stays hidden from the heat."}
        ]
    }
]


def severe_week_key(now=None):
    now = now or datetime.now(TZ)
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def severe_month_key(now=None):
    now = now or datetime.now(TZ)
    return now.strftime("%Y-%m")


def severe_entity_key(label, kind=None):
    if kind == "clan" or label in CLAN_NAMES_ONLY:
        return f"clan:{label}"
    return f"outsider:{label}"


def populated_outsider_groups():
    groups = []
    seen = set()

    for cat in data.get("cats", {}).values():
        if cat.get("clan") != "Outsider":
            continue
        if str(cat.get("status", "Alive")).lower() == "dead":
            continue

        group = cat.get("faction")
        if not group:
            continue

        resolved = resolve_outsider_group(group) or str(group).strip()
        key = resolved.casefold()
        if key in seen:
            continue
        seen.add(key)
        groups.append(resolved)

    groups.sort(key=str.casefold)
    return groups


def get_severe_entities(include_empty_outsider=False):
    entities = [
        {"key": severe_entity_key(clan, "clan"), "label": clan, "kind": "clan"}
        for clan in CLAN_NAMES_ONLY
    ]

    outsider_groups = get_outsider_groups() if include_empty_outsider else populated_outsider_groups()
    for group in outsider_groups:
        entities.append({
            "key": severe_entity_key(group, "outsider"),
            "label": group,
            "kind": "outsider"
        })

    return entities


def resolve_severe_target_name(value):
    clean = str(value or "").strip()
    if not clean:
        return None

    for entity in get_severe_entities(include_empty_outsider=True):
        if entity["label"].casefold() == clean.casefold():
            return entity

    return None


def parse_severe_targets(raw_targets, include_empty_outsider=True):
    if not raw_targets:
        return []

    available = get_severe_entities(include_empty_outsider=include_empty_outsider)
    by_name = {entity["label"].casefold(): entity for entity in available}

    tokens = [
        token.strip()
        for token in str(raw_targets).replace(";", ",").split(",")
        if token.strip()
    ]

    resolved = []
    seen = set()

    def add_entity(entity):
        if entity["key"] not in seen:
            seen.add(entity["key"])
            resolved.append(entity)

    for token in tokens:
        lowered = token.casefold()

        if lowered in {"all", "everyone", "all groups", "all territories"}:
            for entity in available:
                add_entity(entity)
            continue

        if lowered in {"all clans", "clans"}:
            for entity in available:
                if entity["kind"] == "clan":
                    add_entity(entity)
            continue

        if lowered in {"all outsiders", "outsider", "outsiders"}:
            for entity in available:
                if entity["kind"] == "outsider":
                    add_entity(entity)
            continue

        entity = by_name.get(lowered)
        if entity:
            add_entity(entity)
            continue

        raise ValueError(
            f"Unknown severe-weather target: {token}. Use Clan names or saved Outsider group names."
        )

    return resolved


def current_weather_condition():
    current = data.get("current_weather")
    if isinstance(current, dict):
        return str(current.get("weather", "")).strip()
    return ""


def current_weather_is_wet():
    condition = current_weather_condition().casefold()
    wet_words = [
        "rain", "drizzle", "shower", "downpour", "thunder",
        "snow", "blizzard", "flurr", "wet", "fog", "mist", "hail", "frozen rain"
    ]
    return bool(condition) and any(word in condition for word in wet_words)


def current_weather_is_dry():
    condition = current_weather_condition().casefold()
    if not condition:
        return False

    wet_words = [
        "rain", "drizzle", "shower", "downpour", "thunder",
        "snow", "blizzard", "flurr", "wet", "fog", "mist", "hail", "frozen"
    ]
    return not any(word in condition for word in wet_words)


def current_weather_allows_aurora():
    condition = current_weather_condition().casefold()
    if not condition:
        return True

    obscuring_words = [
        "rain", "drizzle", "shower", "downpour", "thunder",
        "snow", "blizzard", "flurr", "fog", "mist", "hail"
    ]
    return not any(word in condition for word in obscuring_words)


def aurora_date_allowed(now=None):
    now = now or datetime.now(TZ)
    month = now.month
    day = now.day

    if month in {10, 11, 12, 1, 2, 3}:
        return True
    if month == 9 and day >= 20:
        return True
    if month == 4 and day <= 10:
        return True
    return False


def cleanup_expired_severe_weather(now=None):
    now = now or datetime.now(TZ)
    active = data.setdefault("active_severe_weather", [])
    kept = []

    for event in active:
        expires_at = event.get("expires_at")
        try:
            expires = datetime.fromisoformat(expires_at) if expires_at else None
        except Exception:
            expires = None

        if expires and expires <= now:
            continue

        kept.append(event)

    changed = len(kept) != len(active)
    data["active_severe_weather"] = kept

    aurora_until = data.get("aurora_active_until")
    if aurora_until:
        try:
            if datetime.fromisoformat(aurora_until) <= now:
                data["aurora_active_until"] = None
                changed = True
        except Exception:
            data["aurora_active_until"] = None
            changed = True

    return changed


def severe_monthly_hit_keys(now=None):
    month = severe_month_key(now)
    raw = data.setdefault("severe_weather_monthly_hits", {}).get(month, [])
    return set(raw if isinstance(raw, list) else [])


def severe_has_monthly_hit(entity_key, now=None):
    return entity_key in severe_monthly_hit_keys(now)


def record_severe_primary_hit(entity, event_key, now=None):
    now = now or datetime.now(TZ)
    month = severe_month_key(now)

    monthly = data.setdefault("severe_weather_monthly_hits", {})
    hits = monthly.setdefault(month, [])
    if entity["key"] not in hits:
        hits.append(entity["key"])

    # Keep only the most recent 8 month buckets.
    for old_month in sorted(monthly.keys())[:-8]:
        monthly.pop(old_month, None)

    history = data.setdefault("severe_weather_history", {})
    entity_history = history.setdefault(entity["key"], [])
    entity_history.append({
        "event_key": event_key,
        "event_name": severe_event_name(event_key),
        "date": now.date().isoformat(),
        "month": month
    })
    history[entity["key"]] = entity_history[-12:]


def recent_severe_event_keys(entity_key):
    history = data.setdefault("severe_weather_history", {}).get(entity_key, [])
    return [
        entry.get("event_key")
        for entry in history[-SEVERE_WEATHER_RECENT_EVENT_MEMORY:]
        if entry.get("event_key")
    ]


def severe_event_catalog():
    catalog = {}

    for event in SHARED_SEVERE_EVENTS:
        catalog[event["key"]] = event

    for events in CLAN_SEVERE_EVENTS.values():
        for event in events:
            catalog[event["key"]] = event

    for event in OUTSIDER_SEVERE_EVENTS:
        catalog[event["key"]] = event

    return catalog


def severe_event_name(event_key):
    event = severe_event_catalog().get(event_key)
    if event:
        return event.get("name", event_key)
    if str(event_key).startswith("manual:"):
        return str(event_key).split("manual:", 1)[1].replace("_", " ").title()
    return str(event_key)


def severe_event_key_from_name(name):
    clean = str(name or "").strip()
    if not clean:
        return "manual:weather_event"

    for event in severe_event_catalog().values():
        if event.get("name", "").casefold() == clean.casefold():
            return event["key"]

    slug = "".join(character.lower() if character.isalnum() else "_" for character in clean)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return f"manual:{slug.strip('_') or 'weather_event'}"


def severe_event_is_eligible(event, season):
    seasons = event.get("seasons")
    if seasons and season not in seasons:
        return False

    if event.get("requires_dry") and not current_weather_is_dry():
        return False

    if event.get("requires_wet") and not current_weather_is_wet():
        return False

    return True


def severe_pool_for_entity(entity):
    pool = list(SHARED_SEVERE_EVENTS)

    if entity["kind"] == "clan":
        pool.extend(CLAN_SEVERE_EVENTS.get(entity["label"], []))
    else:
        pool.extend(OUTSIDER_SEVERE_EVENTS)

    return pool


def choose_severe_event_for_entity(entity, season, used_event_keys=None):
    used_event_keys = set(used_event_keys or [])
    eligible = [
        event for event in severe_pool_for_entity(entity)
        if severe_event_is_eligible(event, season)
    ]

    if not eligible:
        return None

    recent = set(recent_severe_event_keys(entity["key"]))
    fresh = [
        event for event in eligible
        if event["key"] not in recent and event["key"] not in used_event_keys
    ]

    if fresh:
        eligible = fresh
    else:
        no_same_week = [
            event for event in eligible
            if event["key"] not in used_event_keys
        ]
        if no_same_week:
            eligible = no_same_week

    tiers = {}
    for event in eligible:
        tiers.setdefault(event.get("tier", "territory"), []).append(event)

    tier_names = list(tiers.keys())
    tier_weights = [SEVERE_TIER_WEIGHTS.get(tier, 1) for tier in tier_names]
    chosen_tier = random.choices(tier_names, weights=tier_weights, k=1)[0]

    return random.choice(tiers[chosen_tier])


def event_effects_for_target(event, target_label, primary=True):
    if not primary:
        modifier = int(event.get("secondary_modifier", -1))
        effect_type = event.get("secondary_type", "hunting")

        if target_label == "TorrentClan" and event.get("key") in {
            "severe_thunderstorms", "torrential_rain", "severe_blizzard"
        }:
            effect_type = "both"

        return [{
            "location": "Entire Territory",
            "modifier": modifier,
            "type": effect_type,
            "note": event.get(
                "secondary_note",
                "The edge of the weather system reaches this territory."
            )
        }]

    overrides = event.get("target_overrides", {})
    if target_label in overrides:
        return copy.deepcopy(overrides[target_label])

    return copy.deepcopy(event.get("effects", []))


def severe_spread_direct_count(eligible_count):
    if eligible_count <= 1:
        return 1

    roll = random.randint(1, 100)
    if roll <= 55:
        count = 1
    elif roll <= 85:
        count = 2
    elif roll <= 95:
        count = 3
    else:
        count = eligible_count

    return min(max(1, count), eligible_count)


def make_severe_event_record(event, direct_entities, secondary_entities=None, now=None, manual=False, duration_days=None):
    now = now or datetime.now(TZ)
    duration_days = duration_days or SEVERE_WEATHER_DURATION_DAYS
    event_id = f"SW{int(now.timestamp())}{random.randint(100, 999)}"
    expires = now + timedelta(days=duration_days)

    effects = []

    for entity in direct_entities:
        for effect in event_effects_for_target(event, entity["label"], primary=True):
            effects.append({
                "entity_key": entity["key"],
                "target": entity["label"],
                "kind": entity["kind"],
                "primary": True,
                **effect
            })

    for entity in secondary_entities or []:
        for effect in event_effects_for_target(event, entity["label"], primary=False):
            effects.append({
                "entity_key": entity["key"],
                "target": entity["label"],
                "kind": entity["kind"],
                "primary": False,
                **effect
            })

    return {
        "id": event_id,
        "event_key": event["key"],
        "name": event["name"],
        "emoji": event.get("emoji", "⚠️"),
        "description": event.get("description", ""),
        "started_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "manual": bool(manual),
        "effects": effects
    }


def build_manual_severe_event(
    event_name,
    description,
    primary_entities,
    primary_location,
    primary_modifier,
    primary_effect_type,
    secondary_entities,
    secondary_location,
    secondary_modifier,
    secondary_effect_type,
    duration_days,
    now=None
):
    now = now or datetime.now(TZ)
    event_key = severe_event_key_from_name(event_name)

    event = {
        "key": event_key,
        "name": event_name.strip(),
        "emoji": "⚠️",
        "description": description.strip() if description else (
            "Staff have triggered a plot weather event. Exact story consequences are left to players and staff."
        ),
        "effects": [{
            "location": primary_location.strip() or "Entire Territory",
            "modifier": int(primary_modifier),
            "type": primary_effect_type,
            "note": "Staff-set severe weather modifier."
        }],
        "secondary_modifier": int(secondary_modifier),
        "secondary_type": secondary_effect_type,
        "secondary_note": "Staff-set secondary weather effect."
    }

    record = make_severe_event_record(
        event,
        direct_entities=primary_entities,
        secondary_entities=[],
        now=now,
        manual=True,
        duration_days=duration_days
    )

    for entity in secondary_entities:
        record["effects"].append({
            "entity_key": entity["key"],
            "target": entity["label"],
            "kind": entity["kind"],
            "primary": False,
            "location": secondary_location.strip() or "Entire Territory",
            "modifier": int(secondary_modifier),
            "type": secondary_effect_type,
            "note": "Staff-set secondary weather effect."
        })

    return record


def event_primary_targets(event_record):
    targets = []
    seen = set()

    for effect in event_record.get("effects", []):
        if not effect.get("primary"):
            continue
        key = effect.get("entity_key")
        if key in seen:
            continue
        seen.add(key)
        targets.append(effect.get("target"))

    return targets


def event_secondary_targets(event_record):
    targets = []
    seen = set()

    for effect in event_record.get("effects", []):
        if effect.get("primary"):
            continue
        key = effect.get("entity_key")
        if key in seen:
            continue
        seen.add(key)
        targets.append(effect.get("target"))

    return targets


def format_severe_modifier(modifier, effect_type):
    if effect_type == "none" or int(modifier) == 0:
        return "No hunting or fishing modifier"

    sign = "+" if int(modifier) > 0 else ""
    label = SEVERE_EFFECT_TYPE_LABELS.get(effect_type, "hunting rolls")
    return f"{sign}{int(modifier)} to {label}"


def format_severe_event(event_record):
    lines = [
        f"{event_record.get('emoji', '⚠️')} **{event_record.get('name', 'Severe Weather')}**",
        "",
        event_record.get("description", "").strip()
    ]

    effects_by_target = {}
    target_order = []

    for effect in event_record.get("effects", []):
        target = effect.get("target", "Unknown")
        if target not in effects_by_target:
            effects_by_target[target] = []
            target_order.append(target)
        effects_by_target[target].append(effect)

    for target in target_order:
        target_effects = effects_by_target[target]
        primary = any(effect.get("primary") for effect in target_effects)
        tag = "DIRECT HIT" if primary else "OUTER EDGE"
        lines.extend(["", f"**{target} - {tag}**"])

        for effect in target_effects:
            location = effect.get("location", "Entire Territory")
            modifier_text = format_severe_modifier(
                effect.get("modifier", 0),
                effect.get("type", "hunting")
            )
            lines.append(f"• **{location}:** {modifier_text}")
            note = effect.get("note")
            if note:
                lines.append(f"  {note}")

    try:
        expires = datetime.fromisoformat(event_record.get("expires_at"))
        lines.extend([
            "",
            f"⏳ **Effects expire:** {discord_expiry_timestamp(expires)}"
        ])
    except Exception:
        pass

    return "\n".join(lines)


def format_severe_bulletin(event_records, forced=False):
    lines = [
        f"<@&{WEATHER_REPORT_ROLE_ID}>",
        "⚠️ **SEVERE WEATHER ALERT**",
        ""
    ]

    if forced:
        lines.append(
            "Echostone Mountain has not gone two full weeks without a severe event, so at least one eligible territory was selected this week."
        )
        lines.append("")

    for index, event_record in enumerate(event_records):
        if index:
            lines.extend(["", "━━━━━━━━━━━━━━━━━━━━", ""])
        lines.append(format_severe_event(event_record))

    lines.extend([
        "",
        "No cats, kits, herbs, dens, or supplies are automatically injured, killed, or destroyed by these alerts. Any story consequences beyond the listed environmental effects are decided through RP and staff plot choices."
    ])

    return "\n".join(lines)


def active_severe_events_snapshot(now=None):
    now = now or datetime.now(TZ)
    active = []

    for event in data.get("active_severe_weather", []):
        try:
            expires = datetime.fromisoformat(event.get("expires_at"))
        except Exception:
            expires = None

        if expires and expires <= now:
            continue

        active.append(copy.deepcopy(event))

    return active


def normalize_location_for_match(value):
    return " ".join(str(value or "").casefold().split())


def severe_weather_modifier_for(target, location, roll_type, now=None):
    target_entity = resolve_severe_target_name(target)
    if not target_entity:
        return 0, []

    location_norm = normalize_location_for_match(location or "Entire Territory")
    matches = []

    for event in active_severe_events_snapshot(now):
        for effect in event.get("effects", []):
            if effect.get("entity_key") != target_entity["key"]:
                continue

            effect_type = effect.get("type", "hunting")
            if effect_type == "none":
                continue
            if effect_type not in {roll_type, "both"}:
                continue

            effect_location = normalize_location_for_match(effect.get("location", "Entire Territory"))
            if effect_location not in {"entire territory", "all", "all territory"}:
                if location_norm != effect_location:
                    continue

            matches.append({
                "event": event.get("name", "Severe Weather"),
                "location": effect.get("location", "Entire Territory"),
                "modifier": int(effect.get("modifier", 0)),
                "primary": bool(effect.get("primary"))
            })

    if not matches:
        return 0, []

    # Severe-weather effects do not stack with one another. Use the strongest penalty.
    strongest = min(match["modifier"] for match in matches)
    return strongest, matches


def prune_severe_week_results():
    results = data.setdefault("severe_weather_week_results", {})
    if len(results) <= 16:
        return

    for old_key in sorted(results.keys())[:-16]:
        results.pop(old_key, None)


def add_automatic_severe_event(start_entity, all_entities, season, used_event_keys, now):
    event = choose_severe_event_for_entity(start_entity, season, used_event_keys)
    if event is None:
        return None, []

    monthly_hits = severe_monthly_hit_keys(now)
    direct_entities = [start_entity]

    if event.get("regional"):
        available_direct = [
            entity for entity in all_entities
            if entity["key"] not in monthly_hits
            and entity["key"] != start_entity["key"]
        ]

        desired_count = severe_spread_direct_count(len(available_direct) + 1)
        additional_count = max(0, desired_count - 1)
        if additional_count and available_direct:
            direct_entities.extend(
                random.sample(
                    available_direct,
                    k=min(additional_count, len(available_direct))
                )
            )

    direct_keys = {entity["key"] for entity in direct_entities}
    remaining = [
        entity for entity in all_entities
        if entity["key"] not in direct_keys
    ]

    secondary_entities = []
    if event.get("regional") and remaining:
        if random.randint(1, 100) <= SEVERE_WEATHER_SECONDARY_SPREAD_CHANCE:
            secondary_count = 1
            if len(remaining) > 1 and random.randint(1, 100) <= 30:
                secondary_count = 2
            secondary_entities = random.sample(
                remaining,
                k=min(secondary_count, len(remaining))
            )

    record = make_severe_event_record(
        event,
        direct_entities,
        secondary_entities,
        now=now,
        manual=False,
        duration_days=SEVERE_WEATHER_DURATION_DAYS
    )

    for entity in direct_entities:
        record_severe_primary_hit(entity, event["key"], now)

    data.setdefault("active_severe_weather", []).append(record)
    used_event_keys.add(event["key"])
    return record, direct_entities


async def run_automatic_severe_weather(mark_week=True):
    now = datetime.now(TZ)
    week = severe_week_key(now)
    season = data.get("season", get_current_season())

    async with data_lock:
        cleanup_expired_severe_weather(now)

        if mark_week and data.get("last_severe_weather_week") == week:
            existing = data.setdefault("severe_weather_week_results", {}).get(week, {})
            return {
                "already_handled": True,
                "events": [],
                "forced": False,
                "had_primary": bool(existing.get("had_primary"))
            }

        all_entities = get_severe_entities(include_empty_outsider=False)
        monthly_hits = severe_monthly_hit_keys(now)
        eligible_entities = [
            entity for entity in all_entities
            if entity["key"] not in monthly_hits
        ]

        random.shuffle(eligible_entities)
        events = []
        used_event_keys = set()

        for entity in list(eligible_entities):
            if severe_has_monthly_hit(entity["key"], now):
                continue

            if random.randint(1, 100) > SEVERE_WEATHER_WEEKLY_CHANCE:
                continue

            record, _ = add_automatic_severe_event(
                entity,
                all_entities,
                season,
                used_event_keys,
                now
            )
            if record:
                events.append(record)

        forced = False
        quiet_streak = int(data.get("severe_weather_quiet_streak", 0) or 0)

        if not events and quiet_streak >= 1:
            forced_candidates = [
                entity for entity in all_entities
                if not severe_has_monthly_hit(entity["key"], now)
            ]

            random.shuffle(forced_candidates)
            for entity in forced_candidates:
                record, _ = add_automatic_severe_event(
                    entity,
                    all_entities,
                    season,
                    used_event_keys,
                    now
                )
                if record:
                    events.append(record)
                    forced = True
                    break

        had_primary = bool(events)
        data["severe_weather_quiet_streak"] = 0 if had_primary else 1

        if mark_week:
            data["last_severe_weather_week"] = week

        data.setdefault("severe_weather_week_results", {})[week] = {
            "had_primary": had_primary,
            "manual": False,
            "forced": forced,
            "checked_at": now.isoformat()
        }
        prune_severe_week_results()
        save_data(data)

        snapshot = copy.deepcopy(events)

    return {
        "already_handled": False,
        "events": snapshot,
        "forced": forced,
        "had_primary": had_primary
    }


async def post_severe_weather_events(event_records, forced=False):
    if not event_records:
        return False

    channel = bot.get_channel(WEATHER_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(WEATHER_CHANNEL_ID)
        except Exception:
            channel = None

    if channel is None:
        print("Could not find severe weather announcement channel.")
        return False

    message = format_severe_bulletin(event_records, forced=forced)
    await send_long_message(channel, message)
    return True


async def trigger_northern_lights(manual=False):
    now = datetime.now(TZ)
    week = severe_week_key(now)

    async with data_lock:
        if not manual:
            if data.get("last_aurora_week") == week:
                return False
            if not aurora_date_allowed(now):
                return False
            if not current_weather_allows_aurora():
                return False
            if random.randint(1, 100) > NORTHERN_LIGHTS_WEEKLY_CHANCE:
                return False

        active_until = now + timedelta(hours=NORTHERN_LIGHTS_DURATION_HOURS)
        data["aurora_active_until"] = active_until.isoformat()
        data["last_aurora_week"] = week
        save_data(data)

    channel = bot.get_channel(WEATHER_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(WEATHER_CHANNEL_ID)
        except Exception:
            channel = None

    if channel:
        message = (
            f"<@&{WEATHER_REPORT_ROLE_ID}>\n"
            "🌌 **NORTHERN LIGHTS OVER ECHOSTONE MOUNTAIN**\n\n"
            "Curtains of green, blue, and violet light ripple across the night sky. "
            "The mountain feels unusually still, and the boundary between the living and the dead seems thinner than usual.\n\n"
            "🌙 **StarClan feels closer than ever.** Medicine cats and leaders may feel their ancestors especially strongly beneath the lights.\n"
            "✨ **Spirit Veil:** For this event, StarClan cats may walk the living territories in spirit form and converse with living cats.\n"
            "⚠️ **Dark Forest beware:** The veil opens both ways. Dark Forest spirits may also cross into the living lands in spirit form.\n"
            "🎯 **Prey Effect:** None. Hunting and fishing rolls are unchanged.\n\n"
            f"⏳ The Spirit Veil remains open until **{discord_expiry_timestamp(active_until)}**."
        )
        await send_long_message(channel, message)

    return True

# ─────────────────────────────
# AUTOMATED CLAN + MEDICINE CAT GATHERINGS
# ─────────────────────────────

gathering_cycle_lock = asyncio.Lock()

GATHERING_CANCELLATION_OUTCOMES = [
    {
        "key": "clouds",
        "emoji": "☁️",
        "weight": 12,
        "text": """☁️ **There Will Be No Gathering This Moon**\n\nAs the night of the Gathering approaches, thick clouds settle over Echostone Mountain. When the full moon rises, its light is nowhere to be seen, completely hidden behind the darkened sky.\n\nWhether it is simply the weather or a warning from StarClan, the message is clear. **There will be no Gathering this moon.**\n\nThe Clans will have to wait until the next full moon to meet again."""
    },
    {
        "key": "storm",
        "emoji": "⛈️",
        "weight": 12,
        "text": """⛈️ **There Will Be No Gathering This Moon**\n\nDark clouds gather across Echostone Mountain as the full moon approaches. Thunder rolls between the peaks, and distant flashes of lightning warn the Clans against travelling far from home.\n\nWith the mountain caught beneath the storm, **there will be no Gathering this moon.**\n\nFor now, the Clans will remain within their own territories and wait for clearer skies beneath the next full moon."""
    },
    {
        "key": "fog",
        "emoji": "🌫️",
        "weight": 12,
        "text": """🌫️ **There Will Be No Gathering This Moon**\n\nAn unusually thick fog has settled across Echostone Mountain, swallowing trails, landmarks, and the paths leading toward the Gathering place. Even beneath the full moon, the territories disappear beneath a pale veil.\n\nTravelling so far in these conditions would be unwise. **There will be no Gathering this moon.**\n\nThe Clans will meet again when the mountain allows them safe passage."""
    },
    {
        "key": "winds",
        "emoji": "🌬️",
        "weight": 12,
        "text": """🌬️ **There Will Be No Gathering This Moon**\n\nRestless winds sweep across Echostone Mountain beneath the rising full moon. They howl through the trees, race between the cliffs, and carry unfamiliar scents across the territories until even well-known paths feel strange.\n\nTonight, the mountain is far too unsettled for the Clans to travel. **There will be no Gathering this moon.**\n\nWhatever has stirred the winds will hopefully have quieted by the next full moon."""
    },
    {
        "key": "rain",
        "emoji": "🌧️",
        "weight": 12,
        "text": """🌧️ **There Will Be No Gathering This Moon**\n\nRain has fallen across Echostone Mountain for hours without showing any sign of stopping. Trails have turned slick beneath countless paws, streams have swollen beyond their usual banks, and water runs down the mountainsides in muddy sheets.\n\nTravelling to the Gathering would put too many cats at risk. **There will be no Gathering this moon.**\n\nTonight, the Clans will remain sheltered in their camps and listen to the rain instead."""
    },
    {
        "key": "snow",
        "emoji": "❄️",
        "weight": 12,
        "text": """❄️ **There Will Be No Gathering This Moon**\n\nAn unexpected snowfall sweeps across Echostone Mountain as darkness falls, quickly burying familiar trails beneath fresh white drifts. Tracks disappear almost as soon as they are made, and the mountain paths grow harder to follow with every passing moment.\n\nThe journey to the Gathering place is no longer safe. **There will be no Gathering this moon.**\n\nPerhaps by the next full moon, the paths between the Clans will once again be clear."""
    },
    {
        "key": "ice",
        "emoji": "🧊",
        "weight": 12,
        "text": """🧊 **There Will Be No Gathering This Moon**\n\nA sudden freeze has coated the mountain paths in a thin layer of ice. Rocks have become slick beneath paw, narrow trails are dangerously unstable, and even experienced travellers find themselves choosing every step carefully.\n\nNo news is worth risking cats tumbling from the mountain trails. **There will be no Gathering this moon.**\n\nThe Clans will wait for safer footing before they meet again."""
    },
    {
        "key": "flood",
        "emoji": "🌊",
        "weight": 12,
        "text": """🌊 **There Will Be No Gathering This Moon**\n\nMelting snow and recent rain have sent water rushing down Echostone Mountain. Streams have overflowed their banks, familiar crossings have vanished beneath fast-moving water, and several routes toward the Gathering place have become impossible to safely cross.\n\nUntil the waters settle, **there will be no Gathering this moon.**\n\nThe mountain has divided the Clans for tonight, but the next full moon may bring them together once more."""
    },
    {
        "key": "stars_disappear",
        "emoji": "⭐",
        "weight": 3,
        "text": """⭐ **There Will Be No Gathering This Moon**\n\nThe full moon hangs clearly over Echostone Mountain, yet something is missing.\n\nThe stars have vanished.\n\nNot a single point of starlight can be seen surrounding the moon, despite the cloudless sky. Across the territories, an uncomfortable stillness settles over the mountain, as though something unseen is waiting.\n\nNo leader can say exactly what the silence means, but few are willing to ignore it. **There will be no Gathering this moon.**\n\nTonight, the Clans remain beneath a strangely empty sky."""
    },
    {
        "key": "starclan_distant",
        "emoji": "🌑",
        "weight": 1,
        "text": """🌑 **There Will Be No Gathering This Moon**\n\nThe full moon rises over Echostone Mountain, but something about its light feels wrong.\n\nThe stars seem faint and impossibly distant. The night is quiet, yet it is not peaceful. Even the mountain itself seems to be holding its breath, and where StarClan’s presence would normally feel strongest, there is only silence.\n\nWhether the ancestors are displeased, distracted, or simply unwilling to call the Clans together tonight, their absence is difficult to ignore.\n\n**There will be no Gathering this moon.**\n\nPerhaps by the next full moon, StarClan will welcome the Clans beneath the stars once more."""
    }
]

MEDICINE_GATHERING_CANCELLATION_TEXT = {
    "clouds": "Thick clouds swallow the moon and leave the route toward the medicine cats' meeting place without its familiar light. With the path dark and uncertain, the medicine cats and apprentices will remain with their Clans this moon.",
    "storm": "Thunder rolls across Echostone Mountain and lightning flashes between the peaks. The medicine cats and apprentices will not risk the journey through the storm, so there will be no Medicine Cat Gathering this moon.",
    "fog": "Dense fog has swallowed the mountain paths and hidden familiar landmarks. With even experienced travellers struggling to keep their bearings, the Medicine Cat Gathering will be skipped this moon.",
    "winds": "Violent, restless winds tear across the high trails and make the journey dangerously unpredictable. The medicine cats and apprentices will remain home this moon.",
    "rain": "Relentless rain has turned the mountain trails slick and swollen the streams along the route. The Medicine Cat Gathering will be skipped until safer travelling conditions return.",
    "snow": "Unexpected snow is burying the familiar route faster than tracks can be made. The medicine cats and apprentices will not make the journey this moon.",
    "ice": "A sudden freeze has left the mountain paths dangerously slick. Rather than risk a fall on the journey, the Medicine Cat Gathering will be skipped this moon.",
    "flood": "Floodwater has cut across several familiar crossings and made parts of the route unsafe. The medicine cats and apprentices will stay with their Clans this moon.",
    "stars_disappear": "The moon is clear, but the stars around it have vanished. The medicine cats cannot explain the empty sky, and none are eager to ignore such an unsettling sign. There will be no Medicine Cat Gathering this moon.",
    "starclan_distant": "The full moon rises, yet StarClan feels impossibly far away. The sacred silence feels wrong rather than peaceful, and the medicine cats choose not to make the journey. There will be no Medicine Cat Gathering this moon."
}


def last_weekday_of_month(year, month, weekday):
    last_day = calendar.monthrange(year, month)[1]
    final_date = date(year, month, last_day)
    return final_date - timedelta(days=(final_date.weekday() - weekday) % 7)


def nth_weekday_of_month(year, month, weekday, occurrence):
    first_date = date(year, month, 1)
    offset = (weekday - first_date.weekday()) % 7
    return first_date + timedelta(days=offset + ((occurrence - 1) * 7))


def gathering_cycle_times(year, month, medicine=False):
    gathering_date = (
        nth_weekday_of_month(year, month, 3, 2)
        if medicine
        else last_weekday_of_month(year, month, 3)
    )
    start = datetime(
        gathering_date.year,
        gathering_date.month,
        gathering_date.day,
        GATHERING_START_HOUR,
        GATHERING_START_MINUTE,
        tzinfo=TZ
    )
    if medicine:
        end = start.replace(hour=MEDICINE_GATHERING_END_HOUR, minute=0)
    else:
        monday = start + timedelta(days=4)
        end = monday.replace(hour=GATHERING_END_HOUR, minute=0)
    vote_open = start - timedelta(days=GATHERING_VOTE_LEAD_DAYS)
    vote_close = vote_open + timedelta(days=GATHERING_VOTE_DURATION_DAYS)
    reminder = start - timedelta(days=GATHERING_REMINDER_LEAD_DAYS)
    return {
        "start": start,
        "end": end,
        "vote_open": vote_open,
        "vote_close": vote_close,
        "reminder": reminder
    }


def gathering_cycle_key(now):
    return f"{now.year}-{now.month:02d}"


async def gathering_channel(medicine=False):
    channel_id = MEDICINE_GATHERING_CHANNEL_ID if medicine else GATHERING_CHANNEL_ID
    channel = bot.get_channel(channel_id)
    if channel is not None:
        return channel
    try:
        return await bot.fetch_channel(channel_id)
    except Exception:
        return None


def gathering_guild():
    if len(bot.guilds) == 1:
        return bot.guilds[0]
    for guild in bot.guilds:
        if guild.get_role(MEMBER_ROLE_ID):
            return guild
    return None


async def add_vote_reactions(message, medicine=False, include_vote=True):
    try:
        if include_vote:
            await message.add_reaction("✅")
            await message.add_reaction("❌")
        if medicine:
            await message.add_reaction("⭐")
    except discord.HTTPException as error:
        print(f"Could not add Gathering reactions: {error}")


async def reaction_user_ids(message, emoji, guild, required_role_ids=None):
    found = set()
    target_reaction = None
    for reaction in getattr(message, "reactions", []):
        if str(reaction.emoji) == emoji:
            target_reaction = reaction
            break
    if target_reaction is None:
        return found

    async for user in target_reaction.users(limit=None):
        if getattr(user, "bot", False):
            continue
        member = guild.get_member(user.id) if guild else None
        if member is None and guild is not None:
            member = await fetch_member_by_id(guild, user.id)
        if member is None:
            continue
        if required_role_ids:
            role_ids = {role.id for role in getattr(member, "roles", [])}
            if not role_ids.intersection(set(required_role_ids)):
                continue
        found.add(member.id)
    return found


async def fetch_gathering_vote_message(cycle, medicine=False):
    message_id = cycle.get("vote_message_id")
    if not message_id:
        return None
    channel = await gathering_channel(medicine=medicine)
    if channel is None:
        return None
    try:
        return await channel.fetch_message(int(message_id))
    except (discord.NotFound, discord.Forbidden, discord.HTTPException, TypeError, ValueError):
        return None


def choose_gathering_cancellation(cycle=None):
    saved_key = cycle.get("cancellation_outcome_key") if isinstance(cycle, dict) else None
    if saved_key:
        for outcome in GATHERING_CANCELLATION_OUTCOMES:
            if outcome["key"] == saved_key:
                return outcome
    return random.choices(
        GATHERING_CANCELLATION_OUTCOMES,
        weights=[outcome["weight"] for outcome in GATHERING_CANCELLATION_OUTCOMES],
        k=1
    )[0]


def medicine_cancellation_message(outcome, yes_votes, no_votes):
    body = MEDICINE_GATHERING_CANCELLATION_TEXT.get(outcome["key"], "The route is unsafe this moon.")
    return (
        f"{outcome['emoji']} **There Will Be No Medicine Cat Gathering This Moon**\n\n"
        f"**Medicine-team vote:** ✅ {yes_votes} • ❌ {no_votes}\n\n"
        f"{body}\n\n"
        "The medicine cats and apprentices will try again beneath the next moon."
    )


async def ensure_discord_gathering_event(cycle_key, medicine=False):
    store_key = "medicine_gathering_cycles" if medicine else "gathering_cycles"
    async with data_lock:
        cycle = copy.deepcopy(data.setdefault(store_key, {}).get(cycle_key, {}))
    if cycle.get("scheduled_event_id"):
        return cycle.get("scheduled_event_url")

    guild = gathering_guild()
    if guild is None:
        print("Could not create Gathering Scheduled Event: guild not found.")
        return None

    try:
        start = datetime.fromisoformat(cycle["start_at"])
        end = datetime.fromisoformat(cycle["end_at"])
    except Exception:
        return None

    try:
        event = await guild.create_scheduled_event(
            name="Medicine Cat Gathering" if medicine else "The Gathering",
            start_time=start,
            end_time=end,
            entity_type=discord.EntityType.external,
            privacy_level=discord.PrivacyLevel.guild_only,
            location="Echostone Mountain — Medicine Cat Gathering RP" if medicine else "Echostone Mountain — Gathering RP",
            description=MEDICINE_GATHERING_DESCRIPTION if medicine else GATHERING_DESCRIPTION,
            reason="Automated monthly Echostone Mountain Gathering"
        )
    except discord.Forbidden:
        print("Could not create Gathering Scheduled Event: bot needs Manage Events permission.")
        return None
    except (discord.HTTPException, TypeError, ValueError) as error:
        print(f"Could not create Gathering Scheduled Event: {error}")
        return None

    async with data_lock:
        saved = data.setdefault(store_key, {}).setdefault(cycle_key, {})
        saved["scheduled_event_id"] = event.id
        saved["scheduled_event_url"] = getattr(event, "url", None)
        save_data(data)
    return getattr(event, "url", None)


async def initialize_gathering_cycle(now, medicine=False):
    times = gathering_cycle_times(now.year, now.month, medicine=medicine)
    cycle_key = gathering_cycle_key(now)
    store_key = "medicine_gathering_cycles" if medicine else "gathering_cycles"
    async with data_lock:
        cycles = data.setdefault(store_key, {})
        cycle = cycles.setdefault(cycle_key, {})
        cycle.setdefault("cycle_key", cycle_key)
        cycle.setdefault("start_at", times["start"].isoformat())
        cycle.setdefault("end_at", times["end"].isoformat())
        cycle.setdefault("vote_open_at", times["vote_open"].isoformat())
        cycle.setdefault("vote_close_at", times["vote_close"].isoformat())
        cycle.setdefault("reminder_at", times["reminder"].isoformat())
        return copy.deepcopy(cycle), times, cycle_key


async def post_gathering_vote(cycle_key, times, medicine=False):
    channel = await gathering_channel(medicine=medicine)
    if channel is None:
        return False

    skip_key = "last_medicine_gathering_skipped" if medicine else "last_gathering_skipped"
    async with data_lock:
        last_was_skipped = data.get(skip_key) is True

    if medicine:
        med_ping = f"<@&{MEDICINE_CAT_ROLE_ID}> <@&{MEDICINE_CAT_APPRENTICE_ROLE_ID}>"
        star_ping = f"<@&{STARCLAN_GATHERING_VOLUNTEER_ROLE_ID}>"
        if last_was_skipped:
            content = (
                f"{med_ping} {star_ping}\n"
                "🌙 **The Medicine Cat Gathering Must Go Ahead This Moon**\n\n"
                "Last moon's Medicine Cat Gathering was skipped, so there will be **no skip vote this time**. "
                "The medicine cats and apprentices will meet on the second Thursday of the month.\n\n"
                f"📅 **Gathering:** {discord_expiry_timestamp(times['start'])}\n\n"
                f"{star_ping} If you have a **StarClan cat** available to speak with the medicine cats or apprentices, react with ⭐. "
                "There is no limit on how many StarClan volunteers may join."
            )
            message = await channel.send(content)
            await add_vote_reactions(message, medicine=True, include_vote=False)
            async with data_lock:
                cycle = data.setdefault("medicine_gathering_cycles", {}).setdefault(cycle_key, {})
                cycle.update({
                    "vote_posted": True,
                    "vote_message_id": message.id,
                    "forced_must_happen": True,
                    "result_finalized": True,
                    "result": "mandatory",
                    "approved": True,
                    "result_finalized_at": datetime.now(TZ).isoformat()
                })
                data[skip_key] = False
                data.setdefault("medicine_gathering_history", []).append({
                    "cycle": cycle_key,
                    "result": "mandatory_after_skip",
                    "recorded_at": datetime.now(TZ).isoformat()
                })
                data["medicine_gathering_history"] = data["medicine_gathering_history"][-24:]
                save_data(data)
            await ensure_discord_gathering_event(cycle_key, medicine=True)
            return True

        content = (
            f"{med_ping} {star_ping}\n"
            "🌙 **The Medicine Cat Gathering Is Approaching...**\n\n"
            "The second Thursday of the month is drawing near. Medicine cats and medicine cat apprentices, should this moon's gathering go ahead?\n\n"
            "✅ — **Hold the Medicine Cat Gathering**\n"
            "❌ — **Skip this moon's Medicine Cat Gathering**\n\n"
            f"Voting closes {discord_expiry_timestamp(times['vote_close'])}. Only members with the Medicine Cat or Medicine Cat Apprentice role count toward the yes/no vote.\n\n"
            f"{star_ping} If you have a **StarClan cat** ready to speak with the medicine cats or apprentices, react with ⭐. "
            "As many StarClan volunteers as want to participate may react."
        )
        message = await channel.send(content)
        await add_vote_reactions(message, medicine=True, include_vote=True)
        async with data_lock:
            cycle = data.setdefault("medicine_gathering_cycles", {}).setdefault(cycle_key, {})
            cycle.update({"vote_posted": True, "vote_message_id": message.id, "forced_must_happen": False})
            save_data(data)
        return True

    # Full Clan Gathering.
    if last_was_skipped:
        content = (
            f"<@&{MEMBER_ROLE_ID}>\n"
            "🌕 **The Gathering Must Go Ahead This Moon**\n\n"
            "The previous Gathering was skipped, so there will be **no vote to cancel this one**. "
            "The Clans will meet beneath the full moon on the last Thursday of the month.\n\n"
            f"📅 **The Gathering:** {discord_expiry_timestamp(times['start'])}\n\n"
            "Prepare whichever of your cats you would like to send. News, reunions, rivalries, gossip, and whatever chaos the night brings are all welcome."
        )
        message = await channel.send(content)
        async with data_lock:
            cycle = data.setdefault("gathering_cycles", {}).setdefault(cycle_key, {})
            cycle.update({
                "vote_posted": True,
                "vote_message_id": message.id,
                "forced_must_happen": True,
                "result_finalized": True,
                "result": "mandatory",
                "approved": True,
                "result_finalized_at": datetime.now(TZ).isoformat()
            })
            data[skip_key] = False
            data.setdefault("gathering_history", []).append({
                "cycle": cycle_key,
                "result": "mandatory_after_skip",
                "recorded_at": datetime.now(TZ).isoformat()
            })
            data["gathering_history"] = data["gathering_history"][-24:]
            save_data(data)
        await ensure_discord_gathering_event(cycle_key, medicine=False)
        return True

    content = (
        f"<@&{MEMBER_ROLE_ID}>\n"
        "🌕 **The Gathering is Fast Approaching...**\n\n"
        "The full moon will soon rise over Echostone Mountain, calling the Clans together once again.\n\n"
        "Should we hold this moon's Gathering?\n\n"
        "✅ — **Hold the Gathering**\n"
        "❌ — **Skip this moon's Gathering**\n\n"
        f"Voting closes {discord_expiry_timestamp(times['vote_close'])}. Verified members may vote, and reacting to both options will cancel out your vote."
    )
    message = await channel.send(content)
    await add_vote_reactions(message, medicine=False, include_vote=True)
    async with data_lock:
        cycle = data.setdefault("gathering_cycles", {}).setdefault(cycle_key, {})
        cycle.update({"vote_posted": True, "vote_message_id": message.id, "forced_must_happen": False})
        save_data(data)
    return True


async def finalize_gathering_vote(cycle_key, medicine=False):
    store_key = "medicine_gathering_cycles" if medicine else "gathering_cycles"
    skip_key = "last_medicine_gathering_skipped" if medicine else "last_gathering_skipped"
    history_key = "medicine_gathering_history" if medicine else "gathering_history"
    async with data_lock:
        cycle = copy.deepcopy(data.setdefault(store_key, {}).get(cycle_key, {}))
    if not cycle or cycle.get("result_finalized"):
        return False

    message = await fetch_gathering_vote_message(cycle, medicine=medicine)
    if message is None:
        print(f"Could not finalize {'Medicine Cat ' if medicine else ''}Gathering vote: vote message unavailable.")
        return False

    guild = gathering_guild()
    if guild is None:
        return False

    required_roles = (
        {MEDICINE_CAT_ROLE_ID, MEDICINE_CAT_APPRENTICE_ROLE_ID}
        if medicine
        else {MEMBER_ROLE_ID}
    )
    yes_ids = await reaction_user_ids(message, "✅", guild, required_role_ids=required_roles)
    no_ids = await reaction_user_ids(message, "❌", guild, required_role_ids=required_roles)
    double_ids = yes_ids.intersection(no_ids)
    yes_ids -= double_ids
    no_ids -= double_ids
    yes_votes = len(yes_ids)
    no_votes = len(no_ids)

    # A Gathering is the default. It is skipped only when NO has an actual majority.
    approved = no_votes <= yes_votes
    star_ids = set()
    if medicine:
        star_ids = await reaction_user_ids(message, "⭐", guild)

    channel = await gathering_channel(medicine=medicine)
    if channel is None:
        return False

    if approved:
        async with data_lock:
            saved = data.setdefault(store_key, {}).setdefault(cycle_key, {})
            saved.update({
                "result_finalized": True,
                "result": "approved",
                "approved": True,
                "yes_votes": yes_votes,
                "no_votes": no_votes,
                "double_votes_ignored": len(double_ids),
                "starclan_volunteer_ids": sorted(star_ids),
                "result_finalized_at": datetime.now(TZ).isoformat()
            })
            data[skip_key] = False
            data.setdefault(history_key, []).append({
                "cycle": cycle_key,
                "result": "approved",
                "yes_votes": yes_votes,
                "no_votes": no_votes,
                "recorded_at": datetime.now(TZ).isoformat()
            })
            data[history_key] = data[history_key][-24:]
            save_data(data)
        event_url = await ensure_discord_gathering_event(cycle_key, medicine=medicine)
        if medicine:
            volunteer_text = (
                " ".join(f"<@{user_id}>" for user_id in sorted(star_ids))
                if star_ids else
                "No StarClan volunteers have reacted yet; interested players can still use ⭐ on the original message."
            )
            result_text = (
                f"🌙 **The Medicine Cat Gathering Will Go Ahead!**\n\n"
                f"**Medicine-team vote:** ✅ {yes_votes} • ❌ {no_votes}\n"
                + (f"**Ignored double-votes:** {len(double_ids)}\n" if double_ids else "") +
                "\nThe medicine cats and apprentices will meet on the second Thursday of the month.\n\n"
                f"⭐ **StarClan volunteers:** {volunteer_text}"
            )
        else:
            result_text = (
                f"🌕 **The Gathering Will Go Ahead!**\n\n"
                f"✅ **Hold the Gathering:** {yes_votes}\n"
                f"❌ **Skip the Gathering:** {no_votes}\n"
                + (f"⚪ **Ignored double-votes:** {len(double_ids)}\n" if double_ids else "") +
                "\nThe skies have given the Clans no reason to remain apart. The Gathering will take place on the **last Thursday of the month**."
            )
        if event_url:
            result_text += f"\n\n📅 **Discord Event:** {event_url}"
        else:
            result_text += "\n\n⚠️ I could not create the Discord Scheduled Event yet. The bot will keep retrying; make sure it has **Manage Events** permission."
        await channel.send(result_text)
        return True

    outcome = choose_gathering_cancellation(cycle)
    async with data_lock:
        saved = data.setdefault(store_key, {}).setdefault(cycle_key, {})
        saved.update({
            "result_finalized": True,
            "result": "skipped",
            "approved": False,
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "double_votes_ignored": len(double_ids),
            "starclan_volunteer_ids": sorted(star_ids),
            "cancellation_outcome_key": outcome["key"],
            "result_finalized_at": datetime.now(TZ).isoformat()
        })
        data[skip_key] = True
        data.setdefault(history_key, []).append({
            "cycle": cycle_key,
            "result": "skipped",
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "cancellation_outcome_key": outcome["key"],
            "recorded_at": datetime.now(TZ).isoformat()
        })
        data[history_key] = data[history_key][-24:]
        save_data(data)

    if medicine:
        result_text = medicine_cancellation_message(outcome, yes_votes, no_votes)
    else:
        tally = (
            f"📊 **Gathering Vote:** ✅ {yes_votes} • ❌ {no_votes}"
            + (f" • {len(double_ids)} double-vote(s) ignored" if double_ids else "")
        )
        result_text = tally + "\n\n" + outcome["text"]
    await channel.send(result_text)
    return True


async def current_medicine_star_volunteers(cycle_key):
    async with data_lock:
        cycle = copy.deepcopy(data.setdefault("medicine_gathering_cycles", {}).get(cycle_key, {}))
    message = await fetch_gathering_vote_message(cycle, medicine=True)
    guild = gathering_guild()
    if message is None or guild is None:
        return set(cycle.get("starclan_volunteer_ids", []) or [])
    return await reaction_user_ids(message, "⭐", guild)


async def send_gathering_reminder(cycle_key, times, medicine=False):
    channel = await gathering_channel(medicine=medicine)
    if channel is None:
        return False
    store_key = "medicine_gathering_cycles" if medicine else "gathering_cycles"
    async with data_lock:
        cycle = copy.deepcopy(data.setdefault(store_key, {}).get(cycle_key, {}))
    if not cycle.get("approved") or cycle.get("reminder_sent"):
        return False

    event_url = cycle.get("scheduled_event_url")
    if medicine:
        volunteers = await current_medicine_star_volunteers(cycle_key)
        volunteer_text = (
            " ".join(f"<@{user_id}>" for user_id in sorted(volunteers))
            if volunteers else
            "No StarClan volunteers have signed up yet."
        )
        content = (
            f"<@&{MEDICINE_CAT_ROLE_ID}> <@&{MEDICINE_CAT_APPRENTICE_ROLE_ID}> <@&{STARCLAN_GATHERING_VOLUNTEER_ROLE_ID}>\n"
            "🌙 **The Medicine Cat Gathering is Tomorrow!**\n\n"
            "Tomorrow night, the medicine cats and their apprentices will gather beneath the moon to exchange news and seek StarClan's guidance.\n\n"
            f"⭐ **StarClan volunteers:** {volunteer_text}"
        )
    else:
        content = (
            f"<@&{MEMBER_ROLE_ID}>\n"
            "🌕 **The Gathering is Tomorrow!**\n\n"
            "The moon is nearly full. Tomorrow night, the Clans will gather beneath the stars once again.\n\n"
            "Decide which of your cats will be attending, and prepare for news, reunions, rivalries, gossip, and whatever chaos the night may bring!"
        )
    if event_url:
        content += f"\n\n📅 {event_url}"
    await channel.send(content)
    async with data_lock:
        saved = data.setdefault(store_key, {}).setdefault(cycle_key, {})
        saved["reminder_sent"] = True
        saved["reminder_sent_at"] = datetime.now(TZ).isoformat()
        if medicine:
            saved["starclan_volunteer_ids"] = sorted(volunteers)
        save_data(data)
    return True


async def process_one_gathering_system(now, medicine=False):
    cycle, times, cycle_key = await initialize_gathering_cycle(now, medicine=medicine)
    store_key = "medicine_gathering_cycles" if medicine else "gathering_cycles"

    # Do not create stale announcements for a month whose event has already ended.
    if now >= times["end"]:
        if not cycle.get("closed"):
            async with data_lock:
                saved = data.setdefault(store_key, {}).setdefault(cycle_key, {})
                saved["closed"] = True
                saved["closed_at"] = now.isoformat()
                save_data(data)
        return

    if now >= times["vote_open"] and now < times["start"] and not cycle.get("vote_posted"):
        await post_gathering_vote(cycle_key, times, medicine=medicine)
        async with data_lock:
            cycle = copy.deepcopy(data.setdefault(store_key, {}).get(cycle_key, {}))

    if now >= times["vote_close"] and now < times["start"] and cycle.get("vote_posted") and not cycle.get("result_finalized"):
        await finalize_gathering_vote(cycle_key, medicine=medicine)
        async with data_lock:
            cycle = copy.deepcopy(data.setdefault(store_key, {}).get(cycle_key, {}))

    # If an approved event could not be created earlier, keep retrying safely.
    if cycle.get("approved") and not cycle.get("scheduled_event_id") and now < times["start"]:
        await ensure_discord_gathering_event(cycle_key, medicine=medicine)
        async with data_lock:
            cycle = copy.deepcopy(data.setdefault(store_key, {}).get(cycle_key, {}))

    if now >= times["reminder"] and now < times["start"] and cycle.get("approved") and not cycle.get("reminder_sent"):
        await send_gathering_reminder(cycle_key, times, medicine=medicine)


@tasks.loop(minutes=30)
async def gathering_scheduler():
    now = datetime.now(TZ)
    async with gathering_cycle_lock:
        await process_one_gathering_system(now, medicine=False)
        await process_one_gathering_system(now, medicine=True)


# ─────────────────────────────
# RULES VERIFICATION / ONBOARDING
# ─────────────────────────────

async def get_rules_guild():
    if len(bot.guilds) == 1:
        return bot.guilds[0]
    for guild in bot.guilds:
        if guild.get_role(MEMBER_ROLE_ID) and guild.get_role(NEW_MEMBER_ROLE_ID):
            return guild
    return None


@bot.event
async def on_member_join(member: discord.Member):
    """Immediately point new members to the exact rules verification message."""
    if member.bot:
        return

    welcome_channel = bot.get_channel(VERIFICATION_INFO_CHANNEL_ID)
    if welcome_channel is None:
        try:
            welcome_channel = await bot.fetch_channel(VERIFICATION_INFO_CHANNEL_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as error:
            print(f"Could not access the verification welcome channel for new member {member.id}: {error}")
            return

    message = (
        f"👋 **Welcome to Echostone Mountain, {member.mention}!**\n\n"
        "Before you can access the rest of the server, you’ll need to verify yourself as a Member. 🐾\n\n"
        "**Here’s exactly what to do:**\n"
        f"**1.** Open the **[Rules & Verification message]({RULES_LINK})**.\n"
        "**2.** Read through the server rules completely.\n"
        "**3.** React to that message with **✅** once you’re finished.\n"
        f"**4.** The bot will automatically give you the <@&{MEMBER_ROLE_ID}> role, which unlocks the rest of the server.\n\n"
        "That’s it! Once you’ve reacted, you should be ready to explore Echostone Mountain. 🌙"
    )

    try:
        await welcome_channel.send(
            message,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
        )
        print(f"Sent verification instructions for new member {member} ({member.id}).")
    except discord.Forbidden:
        print("Could not send new-member verification instructions: bot lacks permission in the verification welcome channel.")
    except discord.HTTPException as error:
        print(f"Could not send verification instructions for {member.id}: {error}")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.message_id != RULES_VERIFICATION_MESSAGE_ID or str(payload.emoji) != "✅":
        return
    if payload.user_id == getattr(bot.user, "id", None):
        return
    guild = bot.get_guild(payload.guild_id) if payload.guild_id else None
    if guild is None:
        return
    member = payload.member or await fetch_member_by_id(guild, payload.user_id)
    if member is None or member.bot:
        return
    member_role = guild.get_role(MEMBER_ROLE_ID)
    if member_role is None:
        print("Rules verification failed: Member role could not be found.")
        return
    # Existing verified members do not change when they react.
    if member_role in member.roles:
        return
    try:
        await member.add_roles(member_role, reason="Member accepted the Echostone Mountain rules via the verification reaction.")
        print(f"Rules verification: added Member role to {member} ({member.id}).")
    except discord.Forbidden:
        print("Rules verification failed: bot lacks permission or role hierarchy to add the Member role.")
    except discord.HTTPException as error:
        print(f"Rules verification failed for {member.id}: {error}")


@tasks.loop(hours=12)
async def check_rules_onboarding():
    guild = await get_rules_guild()
    if guild is None:
        return
    member_role = guild.get_role(MEMBER_ROLE_ID)
    new_member_role = guild.get_role(NEW_MEMBER_ROLE_ID)
    if member_role is None or new_member_role is None:
        return

    verification_info_channel = bot.get_channel(VERIFICATION_INFO_CHANNEL_ID)
    if verification_info_channel is None:
        try:
            verification_info_channel = await bot.fetch_channel(VERIFICATION_INFO_CHANNEL_ID)
        except Exception:
            verification_info_channel = None

    now = datetime.now(TZ)
    changed = False
    async with data_lock:
        reminders = data.setdefault("rules_onboarding_reminders", {})
        async for member in iter_fetch_guild_members(guild):
            if member.bot or new_member_role not in member.roles or member.joined_at is None:
                continue
            joined_at = member.joined_at.astimezone(TZ)
            days_in_server = (now.date() - joined_at.date()).days
            user_key = str(member.id)
            record = reminders.setdefault(user_key, {})

            if days_in_server >= RULES_REMINDER_AFTER_DAYS and days_in_server < NEW_MEMBER_ROLE_REMOVE_AFTER_DAYS and member_role not in member.roles and not record.get("three_day_reminder_sent"):
                if verification_info_channel:
                    try:
                        await verification_info_channel.send(
                            f"{member.mention} 🐾 **Verification reminder!** You still need to read the server rules and react with ✅ on the verification message to receive the Member role.\n\n"
                            f"📜 **[Read the rules & verify here]({RULES_LINK})**",
                            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False)
                        )
                        record["three_day_reminder_sent"] = True
                        record["three_day_reminder_sent_at"] = now.isoformat()
                        changed = True
                    except discord.HTTPException as error:
                        print(f"Could not send rules reminder for {member.id}: {error}")

            if days_in_server >= NEW_MEMBER_ROLE_REMOVE_AFTER_DAYS:
                try:
                    await member.remove_roles(new_member_role, reason="7-day Echostone onboarding period completed.")
                    record["new_member_role_removed_at"] = now.isoformat()
                    changed = True
                except discord.Forbidden:
                    print("Rules onboarding failed: bot lacks permission or role hierarchy to remove the New Member role.")
                except discord.HTTPException as error:
                    print(f"Could not remove New Member role from {member.id}: {error}")

        if changed:
            save_data(data)



# ─────────────────────────────
# HUNTING PROMPT SYSTEM
# ─────────────────────────────

HUNT_CHANNELS = {1443836708494905425: {'location': 'Glacier’s Edge', 'emoji': '❄️'},
 1443836740338188389: {'location': 'Cloud Plateau', 'emoji': '❄️'},
 1443836807459377162: {'location': 'Frost Tunnels', 'emoji': '❄️'},
 1443836852317585418: {'location': 'Frozen Falls', 'emoji': '❄️'},
 1443838786285998150: {'location': 'Trout Run', 'emoji': '🌊'},
 1443839406288142457: {'location': 'Reed Marsh', 'emoji': '🌊'},
 1443839451917848677: {'location': 'Glistening Pools', 'emoji': '🌊'},
 1443839512672469115: {'location': 'Sunspirit Sands', 'emoji': '🌊'},
 1443840180837548112: {'location': 'Raptorfang Spires', 'emoji': '🦴'},
 1443840270381879410: {'location': 'Rexhead Pillars', 'emoji': '🦴'},
 1443840242258939925: {'location': 'Dustwind Flats', 'emoji': '🦴'},
 1443840299657986190: {'location': 'Dinosaur Spine', 'emoji': '🦴'},
 1443840673857146950: {'location': 'Whispering Branches', 'emoji': '🌲'},
 1443840741582438400: {'location': 'Deeproot Tangle', 'emoji': '🌲'},
 1443841769316810794: {'location': 'Sundance Pond', 'emoji': '🌲'},
 1443842326488158209: {'location': 'Toadstool Glade', 'emoji': '🍄'},
 1444902861267013756: {'location': 'The Sanctuary', 'emoji': '🐖'},
 1444903072370397317: {'location': 'Frostbite Ridge', 'emoji': '🏔️'},
 1444903464957382717: {'location': 'Neon Path', 'emoji': '🌃'},
 1444903561099088004: {'location': 'Twoleg Town', 'emoji': '🏡'}}

NO_PREY_HUNT_PROMPTS = {'Frozen Falls': ['The roar of BlizzardClan’s sacred falls drowns out every other sound, and no prey scent lingers anywhere nearby. A '
                  'single pale feather spirals slowly from somewhere above and lands at your paws. **There is nothing to hunt here, but... '
                  'is that a sign from StarClan? Probably not. You might want to keep it anyway.**',
                  'You search along the icy stones behind the falls, but find no tracks fresh enough to follow. Instead, a thin shard of '
                  'ice breaks loose overhead and lands perfectly upright in the snow before tipping over. **There is nothing to hunt here. '
                  'Still... that was oddly dramatic.**',
                  'No prey dares linger around the sacred falls, leaving only the thunder of water and the occasional groan of shifting '
                  'ice. Beneath a frozen ledge, you notice a tiny blue-grey stone polished completely smooth by the water. **There is '
                  'nothing to hunt here, but you may take the stone with you if you wish.**',
                  'You catch what sounds like a whisper beneath the pounding waterfall and turn sharply toward the hidden cavern. Nothing '
                  'is there when you look, only dripping water and your own reflection trembling across the ice. **There is nothing to '
                  'hunt here. Maybe the mountain is simply playing tricks on you.**',
                  'Fresh pawprints appear in the snow near the falls, but they abruptly stop several tail-lengths from the water with no '
                  'obvious trail leading away. They are too blurred by frost to identify. **There is nothing to hunt here, though you may '
                  'want to remember what you found.**',
                  'A thin beam of sunlight slips through the ice and throws a strange rainbow across the cavern wall. For only a moment, '
                  'the colours seem almost shaped like a cat before the light shifts and the illusion disappears. **There is nothing to '
                  'hunt here. StarClan probably has better things to do... probably.**'],
 'Sunspirit Sands': ['Warm sand shifts beneath your paws while the water laps peacefully against the shore. There are no prey trails to '
                     'follow, but a perfectly intact shell gleams beside the tide line as though somebody placed it there. **Sunspirit '
                     'Sands is for resting, not hunting, but the shell is yours if you want it.**',
                     'You wander along the empty beach without finding so much as a mouse track. A smooth piece of driftwood has washed '
                     'ashore instead, twisted into a shape that looks suspiciously like a curled cat if you squint hard enough. **There is '
                     'nothing to hunt here, but perhaps it would make an interesting keepsake.**',
                     'The sand holds no fresh prey scent, only the overlapping pawprints of TorrentClan cats who have visited before you. '
                     'Among them is one tiny set of tracks leading toward the water and disappearing at the shoreline. **There is nothing '
                     'to hunt here. Maybe somebody went for a swim... hopefully.**',
                     'A wave rolls farther up the beach than the others and leaves something glittering behind. It is only a tiny piece of '
                     'polished sea glass, dulled smooth enough that it cannot cut your paws. **There is nothing to hunt here, but you may '
                     'take your strangely shiny treasure.**',
                     'You find no prey whatsoever, but a little mound of sand near the water looks suspiciously deliberate. One swipe of '
                     'your paw reveals three shells tucked underneath as though another cat had hidden them there. **Sunspirit Sands is '
                     'for resting, not hunting. Whether you disturb this mysterious shell stash is entirely up to you.**',
                     'A warm breeze carries the distant call of a bird over the water, followed by a single feather drifting onto the '
                     'beach beside you. It is damp at the tip but otherwise untouched. **There is nothing to hunt here, though perhaps the '
                     'feather deserves a place in somebody’s nest.**'],
 'Dinosaur Spine': ['Ancient bone, mineral-rich stone, and FossilClan’s water source surround you, but there are no prey trails worth '
                    'following here. Something glimmers between two old fossils: a tiny crystal loosened from the ridge. **This sacred '
                    'place is not a hunting ground, but you may take the crystal if it feels right.**',
                    'You find no prey among the ancient bones, but your paw brushes against a small fossil fragment half-buried in the '
                    'dust. Its shape resembles a tiny claw, though whether it actually belonged to anything interesting is impossible to '
                    'tell. **There is nothing to hunt here. FossilClan would probably still think this is pretty cool.**',
                    'A gust whistles through the Dinosaur Spine and produces a low, hollow note from somewhere inside the rocks. For a '
                    'heartbeat it sounds almost like a distant roar before fading back into ordinary wind. **There is nothing to hunt '
                    'here. Definitely just the wind. Probably.**',
                    'No prey scent breaks through the mineral-rich air. Instead, sunlight catches a vein of crystal in the ridge and sends '
                    'a bright flash directly across your eyes. When you look again, one loose shard has fallen beside your paws. **There '
                    'is nothing to hunt here, but you have found a small crystal.**',
                    'While crossing between the old bones, you notice several pebbles arranged in a rough circle around one tiny fossil. '
                    'It could easily be coincidence... or perhaps another FossilClan cat placed them there moons ago. **There is nothing '
                    'to hunt here, but maybe leave the little arrangement undisturbed.**',
                    'The ridge remains completely quiet until a pebble suddenly tumbles from somewhere above and lands beside an enormous '
                    'ancient bone. Nothing follows it. **There is nothing to hunt here, though the Dinosaur Spirits apparently have '
                    'excellent timing when it comes to making things ominous.**'],
 'Toadstool Glade': ['The overwhelming scent of damp earth and fungi smothers every prey trail before you can follow it. Instead, you '
                     'notice a tiny mushroom growing in an almost perfect ring of moss. **Hunting is impossible here, but you might want '
                     'to remember where you saw this strange little fairy circle.**',
                     'No prey ventures close to the towering mushrooms, but a single drop of water falls from one enormous cap and lands '
                     'directly between your ears. **There is nothing to hunt here. The Glade has instead chosen violence in the smallest '
                     'possible form.**',
                     'You search beneath the towering fungi and find nothing edible, but something pale gleams in the moss. It is a small '
                     'feather dusted with spores, untouched except for the damp forest floor beneath it. **There is nothing to hunt here, '
                     'but you may take the feather if you are confident it is safe.**',
                     'A cluster of tiny mushrooms releases a faint puff of harmless-looking spores when a falling twig strikes the ground '
                     'beside them. They sparkle briefly in a shaft of light before disappearing into the air. **There is nothing to hunt '
                     'here. Maybe... do not stick your face directly into that.**',
                     'The Glade is completely devoid of prey, but one enormous toadstool has collected a shallow pool of rainwater in the '
                     'centre of its cap. Your reflection stares back at you from above in a strangely distorted little mirror. **Hunting '
                     'is impossible here, but apparently the forest has provided free self-reflection.**',
                     'You hear something rustle behind one of the towering mushrooms and immediately prepare yourself, only for a pinecone '
                     'to roll slowly into view and stop at your paws. Nothing follows it. **There is nothing to hunt here. Whatever caused '
                     'that is either completely harmless or extremely committed to being mysterious.**']}

HUNT_TABLES = {'Glacier’s Edge': [(27, 'prey', ['Pika', 'Mouse', 'Vole', 'Shrew']),
                    (25, 'prey', ['Cutthroat Trout', 'Mountain Whitefish']),
                    (15, 'prey', ['Snowshoe Hare']),
                    (10, 'prey', ['Ptarmigan']),
                    (8, 'prey', ['Bull Trout']),
                    (6, 'prey', ['Marmot']),
                    (4, 'prey', ['Golden Eagle']),
                    (2, 'prey', ['Mountain Goat']),
                    (2, 'threat', 'Cougar'),
                    (1, 'threat', 'Bear')],
 'Frost Tunnels': [(30, 'prey', ['Mouse']),
                   (20, 'prey', ['Pika']),
                   (20, 'prey', ['Salamander']),
                   (15, 'prey', ['Bat']),
                   (8, 'prey', ['Rat']),
                   (4, 'threat', 'Wolverine'),
                   (3, 'threat', 'Dark Forest Cat')],
 'Cloud Plateau': [(20, 'prey', ['Mouse', 'Shrew']),
                   (18, 'prey', ['Vole', 'Pika']),
                   (16, 'prey', ['Red Squirrel']),
                   (14, 'prey', ['Snowshoe Hare']),
                   (13, 'prey', ['Ptarmigan']),
                   (10, 'prey', ['Magpie']),
                   (5, 'prey', ['Caribou Scraps']),
                   (2, 'prey', ['Canada Goose']),
                   (1, 'threat', 'Cougar'),
                   (1, 'threat', 'Bear')],
 'Trout Run': [(30, 'prey', ['Trout', 'Perch', 'Arctic Char']),
               (20, 'prey', ['Minnows']),
               (18, 'prey', ['Frog']),
               (12, 'prey', ['Mouse', 'Squirrel']),
               (10, 'prey', ['Crayfish']),
               (3, 'prey', ['Kingfisher']),
               (3, 'prey', ['Duckling']),
               (3, 'threat', 'Otter'),
               (1, 'threat', 'Bear')],
 'Reed Marsh': [(20, 'prey', ['Frog']),
                (18, 'prey', ['Perch']),
                (12, 'prey', ['Water Vole']),
                (11, 'prey', ['Walleye']),
                (10, 'prey', ['Loon']),
                (9, 'prey', ['Duck']),
                (8, 'prey', ['Catfish']),
                (6, 'prey', ['Mink']),
                (4, 'prey', ['Muskrat']),
                (2, 'prey', ['Beaver'])],
 'Glistening Pools': [(20, 'prey', ['Minnow', 'Mouse']),
                      (18, 'prey', ['Frog']),
                      (15, 'prey', ['Duck']),
                      (13, 'prey', ['Coot']),
                      (12, 'prey', ['Loon']),
                      (10, 'prey', ['Rat']),
                      (5, 'prey', ['Heron']),
                      (5, 'shared', ['Canada Goose', 'Canada Goose']),
                      (2, 'threat', 'Otter')],
 'Raptorfang Spires': [(25, 'prey', ['Pika', 'Vole', 'Rock Wren']),
                       (20, 'prey', ['Squirrel', 'Chipmunk']),
                       (18, 'prey', ['Crow']),
                       (17, 'prey', ['Garter Snake', 'Frog']),
                       (10, 'prey', ['Snowshoe Hare']),
                       (8, 'prey', ['Golden Eagle']),
                       (2, 'threat', 'Cougar')],
 'Rexhead Pillars': [(30, 'prey', ['Ptarmigan', 'Rock Pigeon']),
                     (25, 'prey', ['Sparrow', 'Robin', 'Blue Jay']),
                     (20, 'prey', ['Squirrel', 'Chipmunk']),
                     (12, 'prey', ['Crow']),
                     (5, 'shared', ['Red-tailed Hawk', 'Red-tailed Hawk']),
                     (5, 'shared', ['Peregrine Falcon', 'Peregrine Falcon']),
                     (3, 'prey', ['Mountain Goat'])],
 'Dustwind Flats': [(25, 'prey', ['Mouse', 'Vole', 'Common Shrew']),
                    (20, 'prey', ['Red Squirrel', 'Chipmunk']),
                    (18, 'prey', ['Blue Grouse']),
                    (12, 'prey', ['Snowshoe Hare']),
                    (10, 'prey', ['Pika']),
                    (8, 'prey', ['Garter Snake', 'Spotted Salamander']),
                    (5, 'prey', ['Nighthawk']),
                    (2, 'shared', ['Weasel', 'Weasel'])],
 'Whispering Branches': [(30, 'prey', ['Squirrel', 'Chipmunk']),
                         (25, 'prey', ['Sparrow', 'Robin', 'Blue Jay', 'Woodpecker', 'Starling']),
                         (20, 'prey', ['Nestling Birds']),
                         (10, 'prey', ['Crow']),
                         (5, 'shared', ['Red-tailed Hawk', 'Red-tailed Hawk']),
                         (5, 'shared', ['Owl', 'Owl']),
                         (5, 'shared', ['Vulture', 'Vulture'])],
 'Deeproot Tangle': [(25, 'prey', ['Minnow', 'Frog']),
                     (20, 'prey', ['Water Vole']),
                     (15, 'prey', ['Red-winged Blackbird']),
                     (10, 'prey', ['Duck', 'Garter Snake']),
                     (10, 'prey', ['Turtle']),
                     (5, 'prey', ['Heron']),
                     (10, 'shared', ['Canada Goose', 'Canada Goose']),
                     (5, 'threat', 'Otter')],
 'Sundance Pond': [(25, 'prey', ['Minnow', 'Frog']),
                   (20, 'prey', ['Duck']),
                   (15, 'prey', ['Water Vole']),
                   (10, 'prey', ['Red-winged Blackbird']),
                   (10, 'prey', ['Garter Snake']),
                   (7, 'prey', ['Turtle']),
                   (5, 'prey', ['Rat']),
                   (3, 'prey', ['Heron']),
                   (3, 'shared', ['Canada Goose', 'Canada Goose']),
                   (2, 'threat', 'Otter')],
 'Frostbite Ridge': [(60, 'prey', ['Gull', 'Pigeon', 'Starling']),
                     (30, 'prey', ['Sparrow', 'Finch', 'Lark']),
                     (5, 'prey', ['Eagle']),
                     (2, 'threat', 'Owl'),
                     (2, 'threat', 'Extreme Wind'),
                     (1, 'threat', 'Sheer Drop')],
 'The Sanctuary': [(70, 'prey', ['Mouse']), (30, 'prey', ['Barn Rat'])],
 'Neon Path': [(50, 'prey', ['Rat']),
               (30, 'prey', ['Mouse']),
               (10, 'prey', ['Skunk']),
               (5, 'shared', ['Raccoon', 'Raccoon']),
               (3, 'threat', 'Dog'),
               (2, 'threat', 'Twoleg Monster')],
 'Twoleg Town': [(30, 'prey', ['Mouse']),
                 (30, 'prey', ['Sparrow', 'Pigeon']),
                 (30, 'prey', ['Squirrel', 'Chipmunk']),
                 (5, 'threat', 'Raccoon'),
                 (3, 'threat', 'Dog'),
                 (2, 'threat', 'Twoleg Monster')]}

HUNT_PROMPTS = {('Glacier’s Edge', 'Pika'): ['A pika emerges from between frost-covered stones with a mouthful of dry grass, pausing to carefully rearrange its bundle. **Roll to catch it, +1 '
                              'because it is distracted!**',
                              'A pika slips while jumping onto a frost-coated rock and slides backward toward you. **Roll to catch it, +2 because it lost its footing!**'],
 ('Glacier’s Edge', 'Mouse'): ['A mouse scurries across a thin patch of snow and stops beside frozen grass to dig desperately for seeds. **Roll to catch it!**'],
 ('Glacier’s Edge', 'Vole'): ['A vole noses along the edge of a snowbank, leaving a tiny trail between exposed stones. **Roll to catch it!**'],
 ('Glacier’s Edge', 'Shrew'): ['A shrew zigzags between frost-covered stones with its nose pressed to the ground. **Roll to catch it, +1 because it is distracted by its '
                               'search!**'],
 ('Glacier’s Edge', 'Cutthroat Trout'): ['A cutthroat trout holds in a clear pocket beside a submerged stone, red-orange markings flashing beneath the icy water. **Roll to catch '
                                         'it!**'],
 ('Glacier’s Edge', 'Mountain Whitefish'): ['A mountain whitefish glides through a calmer seam of current below the frozen bank. **Roll to catch it!**'],
 ('Glacier’s Edge', 'Snowshoe Hare'): ['A hare crouches beside a snow-covered boulder, relying so heavily on its white coat that it has not realized you spotted it. **Roll to '
                                       'catch it, +1 because it thinks it is hidden!**',
                                       'A hare launches over several icy rocks but lands badly on the last one and skids across the frost. **Roll to catch it, +2 because its '
                                       'footing failed!**'],
 ('Glacier’s Edge', 'Ptarmigan'): ['A ptarmigan scratches beneath crusted snow for food, pale feathers blending almost seamlessly into the frozen ground. **Roll to catch it, -1 '
                                   'because its camouflage is excellent!**',
                                   'A gust presses the ptarmigan low against the snow and prevents an immediate takeoff. **Roll to catch it, +1 because the wind is working '
                                   'against it!**'],
 ('Glacier’s Edge', 'Bull Trout'): ['A thick bull trout circles through one of the deeper pools, occasionally rising beneath the surface before disappearing again. **Roll to '
                                    'catch it, -2 because it is staying deep!**',
                                    'A large trout surges after a smaller fish and briefly drives itself into the shallows near your paws. **Roll to catch it, +2 because its own '
                                    'hunt brought it close!**'],
 ('Glacier’s Edge', 'Marmot'): ['A chunky marmot waddles between two boulders carrying an enormous bundle of dried vegetation. **Roll to catch it, +1 because its load is slowing '
                                'it down!**',
                                'A marmot digs enthusiastically at its burrow entrance, throwing dirt and snow behind itself without looking around. **Roll to catch it, +2 '
                                'because it is completely distracted!**'],
 ('Glacier’s Edge', 'Golden Eagle'): ['A golden eagle lands heavily on an exposed ledge, wings spreading wide as it steadies itself above the icy stream. **Roll to hunt it! '
                                      'Hunting party required: 4+ cats, combined roll over 50.**',
                                      'A golden eagle wrestles with prey already trapped beneath one talon. **Roll to hunt it, +1 because it is distracted! Hunting party '
                                      'required: 4+ cats, combined roll over 50.**'],
 ('Glacier’s Edge', 'Mountain Goat'): ['A young mountain goat stands apart from its herd on a broad ledge, scraping one hoof against the ice while searching for vegetation. '
                                       '**Roll to hunt it! Hunting party required: 6+ cats, combined roll over 80.**',
                                       'A mountain goat lowers its head to lick minerals from exposed stone, giving the patrol a rare opportunity to approach unnoticed. **Roll to '
                                       'hunt it, +1 because it is distracted! Hunting party required: 6+ cats, combined roll over 80.**'],
 ('Frost Tunnels', 'Mouse'): ['Tiny claws scrape somewhere beyond the darkness before a mouse emerges beside a dripping wall, whiskers twitching as it investigates the stone. '
                              '**Roll to catch it!**',
                              'A mouse bolts across the tunnel and slips on a patch of frost, scrambling wildly for traction. **Roll to catch it, +2 because it lost its '
                              'footing!**'],
 ('Frost Tunnels', 'Pika'): ['A pika appears on a low shelf of stone, pausing beside a crack while its ears twitch toward every echo. **Roll to catch it!**'],
 ('Frost Tunnels', 'Salamander'): ['A salamander crawls slowly across a damp patch of stone beside meltwater. **Roll to catch it!**'],
 ('Frost Tunnels', 'Bat'): ['A bat drops from the cavern ceiling and sweeps low through the tunnel before climbing again. **Roll to catch it, -1 because it is airborne!**',
                            'A bat recognizes you as a threat and shoots toward the highest part of the cavern. **Roll to catch it, -2 because it is actively escaping!**'],
 ('Frost Tunnels', 'Rat'): ['A large rat emerges from a crevice with its whiskers spread and teeth already visible. **Roll to catch it, -1 because it will fight back!**',
                            'A rat is busy gnawing something against the cave wall and fails to notice you entering the passage. **Roll to catch it, +2 because you caught it '
                            'completely unaware!**'],
 ('Cloud Plateau', 'Mouse'): ['A mouse scurries over windswept stone before stopping beside a crust of old snow to dig for seeds. **Roll to catch it!**',
                              'A sudden gust sends loose snow flying and startles the mouse out of hiding. It freezes rather than runs. **Roll to catch it, +2 because you caught '
                              'it by surprise!**'],
 ('Cloud Plateau', 'Shrew'): ['A shrew zigzags through sparse grass with its nose pressed to the ground, searching so intensely that it nearly crosses your paws. **Roll to catch '
                              'it, +1 because it is distracted!**',
                              'A gust sends grit and snow across the shrew’s face, causing it to stop and shake itself violently. **Roll to catch it, +2 because it is '
                              'distracted!**'],
 ('Cloud Plateau', 'Vole'): ['A round vole emerges from beneath the snow and sits chewing on a dry blade of grass. **Roll to catch it!**'],
 ('Cloud Plateau', 'Pika'): ['A pika hops between wind-scoured stones and pauses beside a shallow crevice. **Roll to catch it!**'],
 ('Cloud Plateau', 'Red Squirrel'): ['A red squirrel races across the open plateau carrying a cone, tail streaming behind it in the wind. **Roll to catch it, +1 because its cargo '
                                     'is slowing it down!**'],
 ('Cloud Plateau', 'Snowshoe Hare'): ['A snowshoe hare crouches beside a patch of pale stone, trusting its coat to hide it in the snow. **Roll to catch it, +1 because it has not '
                                      'realized you spotted it!**'],
 ('Cloud Plateau', 'Ptarmigan'): ['A ptarmigan scratches through windblown snow for seeds, pale feathers nearly vanishing against the plateau. **Roll to catch it, -1 because its '
                                  'camouflage is excellent!**'],
 ('Cloud Plateau', 'Magpie'): ['A magpie lands beside a bright scrap caught between two stones and immediately becomes fascinated with it. **Roll to catch it, +1 because it is '
                               'distracted!**'],
 ('Cloud Plateau', 'Caribou Scraps'): ['A trail of old caribou scraps lies half-buried in the snow, likely left behind by a larger predator. **No roll is needed to take a small '
                                       'usable scrap, but stay alert.**'],
 ('Cloud Plateau', 'Canada Goose'): ['A Canada goose stands stubbornly on the open plateau with its neck stretched high against the wind. **Roll to catch it, -1 because it is '
                                     'alert!**'],
 ('Trout Run', 'Trout'): ['A trout holds steady behind a half-submerged rock where the rapids briefly weaken, tail flicking constantly against the current. **Roll to catch it!**',
                          'A trout drifts into a shallow pocket between stones while searching for food beneath the surface. **Roll to catch it, +2 because the current '
                          'temporarily boxed it in!**'],
 ('Trout Run', 'Perch'): ['A perch cruises beside a submerged branch where the river slows slightly around the wood. **Roll to catch it!**',
                          'A perch becomes momentarily trapped between two rocks as the current presses against its side. **Roll to catch it, +2 because its movement is '
                          'restricted!**'],
 ('Trout Run', 'Arctic Char'): ['An Arctic char flashes pale beneath the rapids as it fights steadily upstream against the current. **Roll to catch it!**'],
 ('Trout Run', 'Minnows'): ['A school of minnows gathers in a calmer pocket near the bank, flashing silver between the stones. **Roll to catch them!**'],
 ('Trout Run', 'Frog'): ['A frog clings to a slick stone at the river’s edge, watching insects over the rapids. **Roll to catch it!**'],
 ('Trout Run', 'Mouse'): ['A mouse creeps along the riverbank roots searching for seeds above the spray. **Roll to catch it!**'],
 ('Trout Run', 'Squirrel'): ['A squirrel pauses on a low root above the water to gnaw at something between its paws. **Roll to catch it, +1 because it is distracted!**'],
 ('Trout Run', 'Crayfish'): ['A crayfish crawls from beneath a submerged stone into the shallows, claws raised defensively. **Roll to catch it!**'],
 ('Trout Run', 'Kingfisher'): ['A kingfisher perches low over the rapids, completely focused on the fish below. **Roll to catch it, +1 because it is distracted!**'],
 ('Trout Run', 'Duckling'): ['A duckling paddles through a protected eddy close to shore, tiny feet churning beneath the surface. **Roll to catch it!**'],
 ('Reed Marsh', 'Frog'): ['A frog sits half-submerged in thick mud, croaking loudly enough to betray exactly where it is hiding. **Roll to catch it!**',
                          'A frog tries to leap from a slick reed root but slides backward into the muck. **Roll to catch it, +2 because it botched its escape!**'],
 ('Reed Marsh', 'Perch'): ['A perch darts between submerged reeds in water barely deep enough to cover its back. **Roll to catch it!**',
                           'A perch becomes trapped momentarily in a dense patch of underwater weeds. **Roll to catch it, +2 because its fins are tangled!**'],
 ('Reed Marsh', 'Water Vole'): ['A water vole paddles between reed stems with a mouthful of wet vegetation. **Roll to catch it, +1 because it is burdened!**'],
 ('Reed Marsh', 'Walleye'): ['A walleye glides through a darker pocket of marsh water where the reeds briefly open. **Roll to catch it!**'],
 ('Reed Marsh', 'Loon'): ['A loon drifts between the reeds, dipping its head beneath the surface to search for fish. **Roll to catch it, +1 because it is distracted!**'],
 ('Reed Marsh', 'Duck'): ['A duck noses through floating plants near the muddy bank. **Roll to catch it, +1 because it is feeding!**'],
 ('Reed Marsh', 'Catfish'): ['A catfish noses along the muddy bottom, whisker-like barbels stirring the silt. **Roll to catch it, -1 because the water is murky!**'],
 ('Reed Marsh', 'Mink'): ['A mink slips between the reeds like flowing water, appearing only briefly before vanishing into cover again. **Roll to catch it, -2 because it is '
                          'exceptionally quick!**',
                          'A mink bursts from the reeds directly in front of you, just as surprised to see the patrol as you are to see it. **Roll to catch it, +2 because you '
                          'caught it at close range!**'],
 ('Reed Marsh', 'Muskrat'): ['A muskrat emerges from the reeds carrying a mouthful of wet vegetation and pauses beside the water. **Roll to hunt it! Hunting party required: 3+ '
                             'cats, combined roll over 25.**',
                             'A muskrat struggles to haul an oversized bundle of plants through thick mud. **Roll to hunt it, +2 because it is heavily slowed! Hunting party '
                             'required: 3+ cats, combined roll over 25.**'],
 ('Reed Marsh', 'Beaver'): ['A massive beaver gnaws steadily on a fallen branch beside its dam, sending wood chips into the water. **Roll to hunt it! Hunting party required: 5+ '
                            'cats, combined roll over 60.**',
                            'A beaver slips while dragging a branch down the muddy slope and lands awkwardly at the water’s edge. **Roll to hunt it, +2 because it is briefly off '
                            'balance! Hunting party required: 5+ cats, combined roll over 60.**'],
 ('Glistening Pools', 'Minnow'): ['A glittering school of minnows twists beneath the clear surface, scales flashing whenever sunlight reaches the pond. **Roll to catch them!**',
                                  'Several minnows become trapped in a tiny sun-warmed shallows between stones. **Roll to catch them, +2 because deeper water is cut off!**'],
 ('Glistening Pools', 'Mouse'): ['A mouse scurries through exposed roots beside the pool and stops to pry at a seed lodged beneath the bark. **Roll to catch it!**',
                                 'A mouse lowers its head to drink from the perfectly still water. **Roll to catch it, +1 because it is distracted!**'],
 ('Glistening Pools', 'Frog'): ['A frog rests on a smooth stone at the edge of the clear pool. **Roll to catch it!**'],
 ('Glistening Pools', 'Duck'): ['A duck paddles lazily through the clear water and begins preening near the bank. **Roll to catch it, +1 because it is distracted!**'],
 ('Glistening Pools', 'Coot'): ['A coot paddles across the pool toward a clump of floating plants. **Roll to catch it!**'],
 ('Glistening Pools', 'Loon'): ['A loon dives beneath the glassy surface and reappears closer to shore than expected. **Roll to catch it, +1 because you know where it '
                                'surfaced!**'],
 ('Glistening Pools', 'Rat'): ['A rat darts from the reeds carrying something stolen from the shoreline. **Roll to catch it, -1 because it already has momentum!**',
                               'A rat slips on the muddy bank and slides several paw-lengths toward the pond. **Roll to catch it, +2 because it lost its footing!**'],
 ('Glistening Pools', 'Heron'): ['A heron stands perfectly still in the shallows, staring down at fish moving between its legs. **Roll to hunt it! Hunting party required: 3+ '
                                 'cats, combined roll over 25.**',
                                 'One long leg slips unexpectedly on a submerged stone and the heron flaps wildly for balance. **Roll to hunt it, +2 because it is off balance! '
                                 'Hunting party required: 3+ cats, combined roll over 25.**'],
 ('Glistening Pools', 'Canada Goose'): ['A Canada goose floats near shore and begins hissing the moment it notices you. **Roll to catch it, -2 because it is alert and '
                                        'aggressive!**',
                                        'A goose slips while climbing onto a muddy stone and spreads both wings for balance. **Roll to catch it, +2 because it has been caught '
                                        'awkwardly!**'],
 ('Raptorfang Spires', 'Pika'): ['A pika squeezes from a crack in one towering spire and pauses on a ledge barely wider than its body. **Roll to catch it, -1 because there is '
                                 'very little room to pounce!**',
                                 'Loose gravel slips beneath the pika’s hind feet and sends it scrambling wildly to keep from sliding farther. **Roll to catch it, +2 because it '
                                 'lost its footing!**'],
 ('Raptorfang Spires', 'Vole'): ['A vole scurries between loose stones at the base of a spire, pausing to sniff into every crack it passes. **Roll to catch it!**',
                                 'A vole digs enthusiastically beneath the red dust with its head almost completely buried. **Roll to catch it, +2 because it cannot see you!**'],
 ('Raptorfang Spires', 'Rock Wren'): ['A rock wren hops between narrow ledges, pecking at insects in the cracks. **Roll to catch it, -1 because the broken stone gives it plenty '
                                      'of escape routes!**'],
 ('Raptorfang Spires', 'Squirrel'): ['A squirrel scrambles over a warm stone shelf carrying a seed in its mouth. **Roll to catch it, +1 because it is burdened!**'],
 ('Raptorfang Spires', 'Chipmunk'): ['A chipmunk pokes from a crack with both cheeks full and pauses on the exposed stone. **Roll to catch it, +1 because its food is slowing it '
                                     'down!**'],
 ('Raptorfang Spires', 'Crow'): ['A crow stalks along the top of a spire, head tilted as it watches the gorge below. **Roll to catch it, -1 because it is alert!**'],
 ('Raptorfang Spires', 'Garter Snake'): ['A garter snake warms itself on a sunlit slab between two spires. **Roll to catch it!**'],
 ('Raptorfang Spires', 'Frog'): ['A frog remains completely still beneath the shade of a pillar, apparently relying on the darkness for safety. **Roll to catch it!**'],
 ('Raptorfang Spires', 'Snowshoe Hare'): ['A snowshoe hare races between the bases of the towering spires, using each pillar to break your line of sight. **Roll to catch it, -2 '
                                          'because the terrain gives it endless turns!**',
                                          'A hare lands awkwardly after jumping between rocks and skids over loose gravel. **Roll to catch it, +2 because its footing failed!**'],
 ('Raptorfang Spires', 'Golden Eagle'): ['A golden eagle rests on the crown of a spire, enormous wings folded tightly while it watches the gorge below. **Roll to hunt it! Hunting '
                                         'party required: 4+ cats, combined roll over 50.**',
                                         'A gorge wind catches the eagle during landing and forces it to stumble sideways across the ledge. **Roll to hunt it, +2 because it is '
                                         'temporarily off balance! Hunting party required: 4+ cats, combined roll over 50.**'],
 ('Rexhead Pillars', 'Ptarmigan'): ['A ptarmigan scratches around a broad ledge, scattering dust and tiny pebbles behind itself as it searches for food. **Roll to catch it!**',
                                    'A ptarmigan catches one foot in a shallow crack and stumbles forward before pulling free. **Roll to catch it, +2 because it lost its '
                                    'balance!**'],
 ('Rexhead Pillars', 'Rock Pigeon'): ['A rock pigeon struts along the pillar edge, bobbing its head importantly with every step. **Roll to catch it!**',
                                      'A pigeon pecks at scattered seeds caught in a shallow depression in the stone. **Roll to catch it, +1 because it is eating!**'],
 ('Rexhead Pillars', 'Sparrow'): ['A sparrow hops over the warm stone searching for tiny seeds caught in cracks. **Roll to catch it!**'],
 ('Rexhead Pillars', 'Robin'): ['A robin lands on a broad ledge and begins pecking through grit near a patch of scrub. **Roll to catch it!**'],
 ('Rexhead Pillars', 'Blue Jay'): ['A blue jay lands noisily on the pillar and becomes distracted scolding another bird across the gap. **Roll to catch it, +1 because its '
                                   'attention is elsewhere!**'],
 ('Rexhead Pillars', 'Squirrel'): ['A squirrel races along a broad ledge with a seed clenched between its teeth. **Roll to catch it, +1 because it is carrying food!**'],
 ('Rexhead Pillars', 'Chipmunk'): ['A chipmunk stops beside a shallow crack to sort seeds between its paws. **Roll to catch it, +1 because it is distracted!**'],
 ('Rexhead Pillars', 'Crow'): ['A crow stands at the edge of a pillar watching everything below with unsettling patience. **Roll to catch it, -1 because it is extremely '
                               'observant!**'],
 ('Rexhead Pillars', 'Red-tailed Hawk'): ['A red-tailed hawk rests on a pillar overlooking the valley, talons wrapped firmly around a rough patch of stone. **Roll to catch it, -1 '
                                          'because it is alert and dangerous!**'],
 ('Rexhead Pillars', 'Peregrine Falcon'): ['A peregrine falcon streaks between the pillars and lands farther along the ridge in a blur of feathers. **Roll to catch it, -2 because '
                                           'its speed is incredible!**'],
 ('Rexhead Pillars', 'Mountain Goat'): ['The goat lowers its head to lick minerals from the warm stone, paying no attention to the cats approaching behind it. **Roll to hunt it, '
                                        '+1 because it is distracted! Hunting party required: 6+ cats, combined roll over 80.**'],
 ('Dustwind Flats', 'Mouse'): ['A mouse scurries across dusty ground and stops beneath a tumbleweed to nose through loose seeds trapped below it. **Roll to catch it!**',
                               'A mouse bursts from beneath a tumbleweed almost directly under your paws and freezes in surprise. **Roll to catch it, +2 because you startled it '
                               'at close range!**'],
 ('Dustwind Flats', 'Vole'): ['A vole waddles between stones carrying dry grass in its mouth, the bundle trailing behind it through the dust. **Roll to catch it, +1 because it is '
                              'burdened!**'],
 ('Dustwind Flats', 'Common Shrew'): ['A common shrew zigzags through brittle scrub with its nose pressed to the ground. **Roll to catch it, +1 because it is distracted!**'],
 ('Dustwind Flats', 'Red Squirrel'): ['A red squirrel races between low patches of scrub with its tail held high above the dust. **Roll to catch it!**'],
 ('Dustwind Flats', 'Chipmunk'): ['A chipmunk digs beneath a tumbleweed with its back toward you. **Roll to catch it, +2 because it cannot see you!**'],
 ('Dustwind Flats', 'Blue Grouse'): ['A blue grouse picks through dry vegetation in the open flats. **Roll to catch it!**'],
 ('Dustwind Flats', 'Snowshoe Hare'): ['A snowshoe hare bolts through the open flats toward a patch of scrub. **Roll to catch it, -1 because it already has a head start!**'],
 ('Dustwind Flats', 'Pika'): ['A pika slips between warm stones and pauses with a mouthful of dried grass. **Roll to catch it, +1 because it is burdened!**'],
 ('Dustwind Flats', 'Garter Snake'): ['A garter snake lies stretched across a sun-warmed strip of stone. **Roll to catch it!**'],
 ('Dustwind Flats', 'Spotted Salamander'): ['A spotted salamander crawls slowly across a damp log sheltered beneath tangled roots. **Roll to catch it!**',
                                            'A falling leaf lands directly over the salamander, causing it to wriggle awkwardly out from underneath. **Roll to catch it, +1 '
                                            'because it has been startled!**'],
 ('Dustwind Flats', 'Nighthawk'): ['A nighthawk swoops low across the flats before curving back toward the same patch of ground. **Roll to catch it, -1 because it remains '
                                   'airborne!**',
                                   'A sudden gust forces the bird into an unexpectedly low landing. **Roll to catch it, +2 because it is briefly grounded!**'],
 ('Dustwind Flats', 'Weasel'): ['A weasel slips through the tumbleweeds with its long body held low to the ground, following a scent across the flats. **Roll to hunt it! Hunting '
                                'party required: 4+ cats, combined roll over 50.**',
                                'A rolling tumbleweed collides with the weasel and sends it scrambling sideways in surprise. **Roll to hunt it, +2 because it has been startled! '
                                'Hunting party required: 4+ cats, combined roll over 50.**'],
 ('Whispering Branches', 'Squirrel'): ['A squirrel digs furiously through the deep pine-needle carpet, throwing little sprays of brown needles behind its tail while searching for '
                                       'a buried meal. **Roll to catch it!**',
                                       'A squirrel misjudges a jump between two low branches and catches the second branch awkwardly with its front paws. **Roll to catch it, +2 '
                                       'because it is scrambling to recover!**'],
 ('Whispering Branches', 'Chipmunk'): ['A chipmunk darts along a fallen branch with both cheeks packed full, pausing briefly whenever another forest sound reaches its ears. '
                                       '**Roll to catch it, +1 because its food is slowing it down!**',
                                       'A falling pinecone lands beside the chipmunk and startles it directly toward your paws. **Roll to catch it, +2 because it fled the wrong '
                                       'way!**'],
 ('Whispering Branches', 'Sparrow'): ['A sparrow hops through fallen needles, tossing tiny pieces of forest litter aside while searching for food beneath them. **Roll to catch '
                                      'it!**'],
 ('Whispering Branches', 'Robin'): ['A robin pulls at something beneath the pine needles with its back turned toward you. **Roll to catch it, +1 because it is distracted!**'],
 ('Whispering Branches', 'Blue Jay'): ['A blue jay lands on a low branch and begins loudly scolding another bird deeper in the forest. **Roll to catch it, +1 because it is '
                                       'distracted!**'],
 ('Whispering Branches', 'Woodpecker'): ['A woodpecker clings low on a spruce trunk, hammering at the bark so loudly it masks your approach. **Roll to catch it, +1 because it '
                                         'cannot hear you clearly!**'],
 ('Whispering Branches', 'Starling'): ['A starling drops to the forest floor to peck rapidly through the needles. **Roll to catch it!**'],
 ('Whispering Branches', 'Nestling Birds'): ['A low nest hidden between dense spruce branches holds several nestlings, their tiny calls giving away the nest. **Roll to catch one, '
                                             '+1 because they cannot fly yet!**'],
 ('Whispering Branches', 'Crow'): ['A crow watches from a low branch, head cocked toward every movement below. **Roll to catch it, -1 because it is extremely alert!**'],
 ('Whispering Branches', 'Red-tailed Hawk'): ['A red-tailed hawk rests on a heavy branch overlooking the forest floor. **Roll to hunt it! Hunting party required: 4+ cats, '
                                              'combined roll over 40.**'],
 ('Whispering Branches', 'Owl'): ['An owl lowers its head toward prey moving far below, unaware of the patrol approaching through the branches behind it. **Roll to hunt it, +1 '
                                  'because it is distracted! Hunting party required: 4+ cats, combined roll over 40.**'],
 ('Whispering Branches', 'Vulture'): ['A huge vulture hunches on a heavy spruce branch, broad wings held slightly away from its body while it surveys the forest below. **Roll to '
                                      'hunt it! Hunting party required: 4+ cats, combined roll over 50.**',
                                      'A vulture is occupied tearing at old carrion beneath the trees, burying its head deep into the remains between bites. **Roll to hunt it, +1 '
                                      'because it is feeding! Hunting party required: 4+ cats, combined roll over 50.**'],
 ('Deeproot Tangle', 'Minnow'): ['A school of minnows gathers in a shallow pocket of clear water trapped between two massive roots, scales flickering whenever sunlight reaches '
                                 'them. **Roll to catch them!**'],
 ('Deeproot Tangle', 'Frog'): ['A frog crouches on a damp root above a shallow pool, watching insects between the leaves. **Roll to catch it!**'],
 ('Deeproot Tangle', 'Water Vole'): ['A water vole squeezes between two roots carrying a mouthful of mossy vegetation. **Roll to catch it, +1 because it is burdened!**'],
 ('Deeproot Tangle', 'Red-winged Blackbird'): ['A red-winged blackbird clings to a reed between the roots, bright shoulder patch flashing as it calls. **Roll to catch it!**'],
 ('Deeproot Tangle', 'Duck'): ['A duck pushes through a root-choked pool with its head down, searching for food. **Roll to catch it, +1 because it is distracted!**'],
 ('Deeproot Tangle', 'Garter Snake'): ['A garter snake threads between warm exposed roots and pauses in a patch of sunlight. **Roll to catch it!**'],
 ('Deeproot Tangle', 'Turtle'): ['A turtle drags itself onto a broad damp root to bask, moving painfully slowly. **Roll to catch it, +2 because it is slow on land!**'],
 ('Deeproot Tangle', 'Heron'): ['A heron stands between the massive roots with its beak angled toward the water. **Roll to hunt it! Hunting party required: 3+ cats, combined roll '
                                'over 25.**'],
 ('Deeproot Tangle', 'Canada Goose'): ['A Canada goose forces its way through a root-choked pool, occasionally bumping its broad body against the wood as it searches for plants. '
                                       '**Roll to catch it!**',
                                       'A slippery root sends the goose stumbling sideways into shallow water, wings flaring in surprise. **Roll to catch it, +2 because it has '
                                       'lost its footing!**'],
 ('Sundance Pond', 'Minnow'): ['Minnows glitter beneath a warm patch of sunlight near the clear bank, their tiny bodies flashing every time they change direction. **Roll to catch '
                               'them!**',
                               'One minnow becomes trapped between a stone and the muddy bank. **Roll to catch it, +2 because its escape route is limited!**'],
 ('Sundance Pond', 'Frog'): ['A frog stretches across a sun-warmed stone beside the pond, hind legs extended comfortably behind it. **Roll to catch it!**',
                             'A frog lands badly on a slick stone and slides backward into the shallows. **Roll to catch it, +2 because its landing failed!**'],
 ('Sundance Pond', 'Duck'): ['A duck paddles lazily through a patch of golden sunlight, leaving a soft V-shaped trail behind it across the pond. **Roll to catch it!**'],
 ('Sundance Pond', 'Water Vole'): ['A water vole emerges beside the pond with a mouthful of plants and pauses on the muddy bank. **Roll to catch it, +1 because it is burdened!**'],
 ('Sundance Pond', 'Red-winged Blackbird'): ['A red-winged blackbird lands on a reed above the pond, attention fixed on insects below. **Roll to catch it, +1 because it is '
                                             'distracted!**'],
 ('Sundance Pond', 'Garter Snake'): ['A garter snake coils loosely on a sun-warmed patch beside the pond. **Roll to catch it!**'],
 ('Sundance Pond', 'Turtle'): ['A turtle basks on a low stone at the waterline. **Roll to catch it, +2 because it is slow on land!**'],
 ('Sundance Pond', 'Rat'): ['A rat races through the reed bed carrying something stolen from the shoreline. **Roll to catch it, -1 because it is already moving quickly!**',
                            'A rat slips on the muddy shoreline and slides several paw-lengths toward the water. **Roll to catch it, +2 because it lost its footing!**'],
 ('Sundance Pond', 'Heron'): ['A heron stands perfectly still in the pond, long neck angled down toward fish moving beneath its feet. **Roll to hunt it! Hunting party required: '
                              '3+ cats, combined roll over 25.**',
                              'A slick submerged stone causes the heron to stumble and flap violently for balance. **Roll to hunt it, +2 because it is off balance! Hunting party '
                              'required: 3+ cats, combined roll over 25.**'],
 ('Sundance Pond', 'Canada Goose'): ['A Canada goose glides toward shore, broad body leaving ripples across the otherwise calm pond. **Roll to catch it!**',
                                     'A goose slips while climbing onto the muddy bank and throws both wings outward to keep from falling. **Roll to catch it, +2 because it is '
                                     'off balance!**'],
 ('Frostbite Ridge', 'Gull'): ['A gull swoops out of the cliffside wind and lands on a broad slab of stone, immediately wrestling with a scrap of food that keeps trying to blow '
                               'away. **Roll to catch it, +1 because it is distracted!**'],
 ('Frostbite Ridge', 'Pigeon'): ['A pigeon huddles against the sheltered side of a boulder, feathers puffed into a round ball as it escapes the worst of the mountain wind. **Roll '
                                 'to catch it!**'],
 ('Frostbite Ridge', 'Starling'): ['A starling lands among the wind-scoured rocks and begins pecking rapidly at something caught in a crack. **Roll to catch it, +1 because it is '
                                   'distracted!**'],
 ('Frostbite Ridge', 'Sparrow'): ['A sparrow drops into a sheltered pocket between stones and starts searching for seeds. **Roll to catch it!**'],
 ('Frostbite Ridge', 'Finch'): ['A finch clings to a low scrub branch bending in the ridge wind. **Roll to catch it, -1 because the gusts make its movement unpredictable!**'],
 ('Frostbite Ridge', 'Lark'): ['A lark lands on open stone after fighting the wind and pauses to recover. **Roll to catch it, +1 because it is briefly grounded!**'],
 ('Frostbite Ridge', 'Eagle'): ['A massive eagle settles onto an exposed outcrop, broad wings folding slowly while its sharp gaze remains fixed on the rapids below. **Roll to '
                                'hunt it! Hunting party required: 4+ cats, combined roll over 50.**'],
 ('The Sanctuary', 'Mouse'): ['A fat mouse waddles through spilled grain with both cheeks packed so full that its head looks nearly square. It has apparently forgotten predators '
                              'exist. **Roll to catch it, +2 because it is distracted and burdened!**',
                              'A mouse has fallen asleep in a warm pile of hay with half a seed still tucked between its paws. Its whiskers twitch peacefully in its sleep. **Roll '
                              'to catch it, +2 because it is literally asleep!**',
                              'Two mice squeak furiously at one another over a single grain kernel while an entire pile of grain sits beside them. **Choose one and roll to catch '
                              'it, +2 because they are busy arguing!**'],
 ('The Sanctuary', 'Barn Rat'): ['A barn rat becomes preoccupied stealing food directly from a smaller mouse, chasing the unfortunate rodent away from its meal. **Roll to catch '
                                 'it, +2 because it is distracted by its robbery!**',
                                 'A rat trots across the aisle carrying a broad piece of vegetable peel that keeps dragging between its front paws. **Roll to catch it, +1 because '
                                 'its food is slowing it down!**'],
 ('Neon Path', 'Rat'): ['A rat tears into a discarded twoleg meal beside an overflowing dumpster, grease coating its whiskers while it rips at the wrapping. **Roll to catch it, '
                        '+1 because it is distracted!**',
                        'A rat darts from beneath a dumpster carrying something wrapped in shiny paper. **Roll to catch it, -1 because it already has a strong head start!**'],
 ('Neon Path', 'Mouse'): ['A mouse darts from beneath a curb and pauses beside a dropped crumb glowing beneath the neon light. **Roll to catch it!**'],
 ('Neon Path', 'Skunk'): ['A skunk slips on wet concrete while climbing onto a pile of rubbish and scrambles wildly to regain its footing. **Roll to catch it, +2 because it is '
                          'off balance!**'],
 ('Neon Path', 'Raccoon'): ['A raccoon digs noisily through an overturned garbage bin, scattering wrappers and scraps across the pavement with both front paws. **Roll to hunt it! '
                            'Hunting party required: 4+ cats, combined roll over 45.**',
                            'A metal trash lid crashes down behind the raccoon and startles it into slipping sideways across the pavement. **Roll to hunt it, +2 because it is '
                            'briefly disoriented! Hunting party required: 4+ cats, combined roll over 45.**'],
 ('Twoleg Town', 'Mouse'): ['A mouse scurries beneath a garden fence and stops beside an overgrown flowerbed, nosing through fallen seeds beneath the leaves. **Roll to catch '
                            'it!**',
                            'A mouse discovers spilled birdseed beneath a feeder and begins stuffing its cheeks as quickly as possible. **Roll to catch it, +1 because it is '
                            'distracted!**'],
 ('Twoleg Town', 'Sparrow'): ['A sparrow hops along the top of a wooden fence, occasionally dropping into the garden to peck through scattered seed. **Roll to catch it, -1 '
                              'because it can take flight easily!**',
                              'A sparrow splashes enthusiastically in a shallow twoleg birdbath, throwing droplets over its wings and completely soaking itself. **Roll to catch '
                              'it, +2 because it is thoroughly distracted!**'],
 ('Twoleg Town', 'Pigeon'): ['A pigeon struts across a garden path beneath a feeder, pecking at scattered seed. **Roll to catch it!**'],
 ('Twoleg Town', 'Squirrel'): ['A squirrel hangs from a garden feeder while stuffing its mouth with stolen seed. **Roll to catch it, +1 because it is distracted!**'],
 ('Twoleg Town', 'Chipmunk'): ['A chipmunk sits upright beneath a garden bench, carefully sorting several seeds between its front paws. **Roll to catch it!**',
                               'A chipmunk becomes absorbed digging beneath a flowerpot, spraying loose soil behind itself without looking around. **Roll to catch it, +2 because '
                               'it is completely distracted!**']}

HUNT_THREATS = {('Glacier’s Edge', 'Cougar'): 'A tawny shape appears silently among the rocks above you. The cougar lowers itself and begins descending the ridge. **Roll 1d10 to flee. 3–10:** '
                               'you escape unharmed. **2:** your paws skid and you painfully twist or scrape one. **1:** the cougar closes the distance, **roll 1d6 for injury '
                               'severity.**',
 ('Glacier’s Edge', 'Bear'): 'A deep grunt cuts through the mountain wind as a bear lumbers onto the hunting ground, drawn by the scent of prey. **Drop your prey and roll 1d10. '
                             '3–10:** you escape. **2:** you suffer a minor bruise or twisted limb. **1:** the bear or dangerous escape catches you badly, **roll 1d6 for '
                             'severity.**',
 ('Frost Tunnels', 'Wolverine'): 'A low growl rolls through the passage before a stocky wolverine pushes into view, blocking much of the narrow tunnel. **Roll 1d10 to retreat. '
                                 '3–10:** you escape. **2:** you scrape or wrench yourself squeezing through the rocks. **1:** the wolverine catches you, **roll 1d6 for injury '
                                 'severity.**',
 ('Frost Tunnels', 'Dark Forest Cat'): 'A shadow moves against the direction of the cave light. A cat-shaped figure waits farther down the tunnel, but its scent is wrong and its '
                                       'eyes catch light that is not there. **Head home and roll 1d10. 3–10:** you escape safely. **2:** you suffer a minor injury fleeing blindly '
                                       'through the tunnels. **1:** something worse happens before you escape, **roll 1d6 for injury severity.**',
 ('Cloud Plateau', 'Cougar'): 'A cougar appears on a shelf above the open plateau, watching the patrol before beginning a silent descent. **Roll 1d10 to retreat. 3–10:** you '
                              'escape unharmed. **2:** you slip on wind-scoured stone and suffer a minor injury. **1:** the cougar closes the distance, **roll 1d6 for injury '
                              'severity.**',
 ('Cloud Plateau', 'Bear'): 'A bear pushes onto the plateau from behind a bank of stone, nose lifted toward the scent of prey. **Drop your prey and roll 1d10 to retreat. 3–10:** '
                            'you escape safely. **2:** you twist or scrape a limb in the rush. **1:** the escape goes badly, **roll 1d6 for injury severity.**',
 ('Trout Run', 'Otter'): 'A sleek head surfaces between the rapids before the otter climbs onto a wet rock and notices you. **Roll 1d10 to retreat. 3–10:** you escape. **2:** you '
                         'receive a shallow bite, scrape, or twisted paw. **1:** the otter catches you or the escape goes badly, **roll 1d6 for injury severity.**',
 ('Trout Run', 'Bear'): 'A bear crashes through the riverbank brush, clearly interested in the exact stretch of water you are hunting. **Drop your prey and roll 1d10. 3–10:** you '
                        'flee safely. **2:** you twist a limb or take a painful scrape escaping over the rocks. **1:** the bear closes the distance, **roll 1d6 for injury '
                        'severity.**',
 ('Glistening Pools', 'Otter'): 'Ripples cross the pool before an otter surfaces close to shore and immediately begins moving toward you. **Roll 1d10 to retreat. 3–10:** you '
                                'escape. **2:** you suffer a shallow bite, scrape, or fall. **1:** the encounter causes a serious injury, **roll 1d6 for severity.**',
 ('Raptorfang Spires', 'Cougar'): 'A cougar’s face appears silently between two stone shelves above the patrol before its body follows, paws making almost no sound. **Roll 1d10 '
                                  'to retreat. 3–10:** you escape. **2:** you wrench a paw or scrape yourself descending too quickly. **1:** the cougar closes the distance, '
                                  '**roll 1d6 for injury severity.**',
 ('Deeproot Tangle', 'Otter'): 'An otter appears in one of the root pools and moves through the tangled water with frightening ease, quickly closing the distance. **Roll 1d10 to '
                               'retreat. 3–10:** you escape. **2:** you scrape or twist a paw scrambling through the roots. **1:** the otter or desperate escape causes a serious '
                               'injury, **roll 1d6 for severity.**',
 ('Sundance Pond', 'Otter'): 'The calm surface suddenly breaks as an otter appears much closer to shore than expected and turns toward the patrol. **Roll 1d10 to retreat. 3–10:** '
                             'you escape. **2:** you suffer a shallow bite, scrape, or twisted paw. **1:** the encounter causes a serious injury, **roll 1d6 for severity.**',
 ('Frostbite Ridge', 'Owl'): 'A silent shadow sweeps over the ridge before an owl drops onto a ledge behind you, enormous eyes already fixed on the patrol. **Roll 1d10 to flee. '
                             '3–10:** you escape unharmed. **2:** a talon clips you, leaving a shallow scratch. **1:** the owl lands a much stronger strike, **roll 1d6 for injury '
                             'severity.**',
 ('Frostbite Ridge', 'Extreme Wind'): 'The air suddenly roars and a brutal crosswind slams into the exposed ridge hard enough to send loose stones tumbling over the edge. **Roll '
                                      '1d10 to reach shelter. 3–10:** you brace safely. **2:** you slip and painfully twist a paw. **1:** the gust throws you dangerously against '
                                      'the rocks or toward the edge, **roll 1d6 for injury severity.**',
 ('Frostbite Ridge', 'Sheer Drop'): 'Stone crumbles unexpectedly beneath your hind paws near the cliff edge, sending fragments rattling toward the rapids far below. **Roll 1d10 '
                                    'to scramble back. 3–10:** you recover safely. **2:** you scrape yourself badly pulling onto solid ground. **1:** your fall or near-fall '
                                    'causes a serious injury, **roll 1d6 for severity.**',
 ('Neon Path', 'Dog'): 'Barking explodes from behind a nearby building before a loose dog rounds the corner at a run, claws scraping frantically against the concrete. **Roll 1d10 '
                       'to flee. 3–10:** you get away. **2:** you twist a paw or suffer a shallow nip during the chase. **1:** the dog catches up, **roll 1d6 for injury '
                       'severity.**',
 ('Neon Path', 'Twoleg Monster'): 'Bright lights sweep suddenly over the pavement as a monster turns into the plaza far closer than anyone expected. **Roll 1d10 to get clear. '
                                  '3–10:** you escape safely. **2:** you painfully wrench a paw during the frantic dodge. **1:** the escape goes badly, **roll 1d6 for injury '
                                  'severity.**',
 ('Twoleg Town', 'Raccoon'): 'A garbage lid shifts beside you and a raccoon rises from behind the bin, bristling when it realizes you are blocking the path back to the fence. '
                             '**Roll 1d10 to retreat. 3–10:** you escape. **2:** it catches you with a shallow scratch or bite. **1:** the raccoon attacks properly, **roll 1d6 '
                             'for injury severity.**',
 ('Twoleg Town', 'Dog'): 'A garden gate bangs open and a barking dog charges into the yard, paws tearing across the grass toward you. **Roll 1d10 to flee. 3–10:** you escape '
                         'unharmed. **2:** you twist a paw or receive a shallow nip. **1:** the dog catches you before you clear the yard, **roll 1d6 for injury severity.**',
 ('Twoleg Town', 'Twoleg Monster'): 'A monster suddenly turns onto the street while you are crossing, lights glaring and engine roaring far too close. **Roll 1d10 to reach '
                                    'safety. 3–10:** you clear the road. **2:** you wrench a paw against the curb. **1:** the escape goes badly, **roll 1d6 for injury severity.**'}

HUNT_SHARED_THREATS = {('Glistening Pools', 'Canada Goose'): 'A goose charges from the water with its neck stretched forward and wings beating violently. **Roll 1d10 to escape. 3–10:** you retreat '
                                       'safely. **2:** you suffer a shallow wound or bruising. **1:** the goose lands a serious strike, **roll 1d6 for severity.**',
 ('Rexhead Pillars', 'Red-tailed Hawk'): 'A hawk drops suddenly from a pillar above, talons stretched as it sweeps low over the patrol. **Roll 1d10 to evade it. 3–10:** you '
                                         'escape unharmed. **2:** a talon leaves a shallow scratch. **1:** the hawk lands a serious hit, **roll 1d6 for injury severity.**',
 ('Rexhead Pillars', 'Peregrine Falcon'): 'A blur tears through the air between the pillars and a peregrine lashes past far closer than expected. **Roll 1d10 to evade it. 3–10:** '
                                          'you duck clear. **2:** its talons graze you. **1:** the strike lands badly, **roll 1d6 for injury severity.**',
 ('Dustwind Flats', 'Weasel'): 'A weasel bursts from the scrub and charges rather than retreating, forcing the patrol to abandon the hunt. **Roll 1d10 to disengage. 3–10:** you '
                               'escape unharmed. **2:** you receive a shallow bite or scratch. **1:** the weasel catches you badly, **roll 1d6 for injury severity.**',
 ('Whispering Branches', 'Red-tailed Hawk'): 'A hawk drops suddenly through the canopy with talons stretched forward, furious that you wandered beneath its perch. **Roll 1d10 to '
                                             'retreat. 3–10:** you escape unharmed. **2:** a talon leaves a shallow scratch. **1:** the hawk lands a serious strike, **roll 1d6 '
                                             'for injury severity.**',
 ('Whispering Branches', 'Owl'): 'An enormous owl launches silently from the dark canopy and sweeps low between the trees. **Roll 1d10 to flee. 3–10:** you reach thicker cover. '
                                 '**2:** a talon clips your shoulder or flank. **1:** the owl catches you properly, **roll 1d6 for injury severity.**',
 ('Whispering Branches', 'Vulture'): 'A huge vulture drops heavily from the branches and spreads its wings, blocking the easiest route through the forest. **Roll 1d10 to get '
                                     'clear. 3–10:** you escape. **2:** you take a minor beak or claw wound. **1:** the encounter causes a serious injury, **roll 1d6 for '
                                     'severity.**',
 ('Deeproot Tangle', 'Canada Goose'): 'A furious goose bursts through the reeds with wings spread and immediately charges the patrol. **Roll 1d10 to retreat. 3–10:** you escape '
                                      'unharmed. **2:** a wing or beak leaves bruising or a shallow wound. **1:** the goose lands a serious hit, **roll 1d6 for severity.**',
 ('Sundance Pond', 'Canada Goose'): 'A furious goose charges from the pond with its wings spread wide, hissing loud enough to carry across the water. **Roll 1d10 to retreat. '
                                    '3–10:** you escape. **2:** you receive minor bruising or a shallow wound. **1:** the goose lands a serious strike, **roll 1d6 for severity.**',
 ('Neon Path', 'Raccoon'): 'A raccoon rises from behind a dumpster much closer than expected and bristles when it realizes the patrol is blocking its escape. **Roll 1d10 to '
                           'disengage. 3–10:** you escape unharmed. **2:** it catches you with a shallow scratch or bite. **1:** the raccoon lands a serious attack, **roll 1d6 '
                           'for injury severity.**'}

REED_MARSH_BEAVER_FAIL_THREAT = 'The beaver wheels around with shocking speed and charges through the shallows instead of retreating. **Roll 1d10 to escape. 3–10:** the patrol gets clear. **2:** you receive a shallow bite, bruise, or painful fall. **1:** the beaver lands a serious attack, **roll 1d6 for injury severity.**'

AMBIENT_HUNT_HAZARDS = {1443842326488158209: {'name': 'Spore Sickness',
                       'chance': 2.0,
                       'cooldown_hours': 24,
                       'message': 'A strange **puffing sound** ripples through the Glade. Before you can figure out where it came from, several towering mushrooms around you '
                                  'erupt at once, releasing thick clouds of spores that roll across the ground and swallow you in a dusty haze. Your eyes sting, your throat '
                                  'burns, and suddenly getting out of here feels much more important than finding prey. **There is nothing to hunt here... but you may have just '
                                  'breathed in something nasty.**\n'
                                  '\n'
                                  '🍄 **SPORE SICKNESS CHECK!**\n'
                                  '\n'
                                  'Roll **1d10** to see whether you escaped the cloud unharmed!\n'
                                  '\n'
                                  '**3–10:** You stumble into fresh air coughing and sneezing, but otherwise seem fine.\n'
                                  '\n'
                                  '**2:** You inhaled enough spores to contract **Spore Sickness.**\n'
                                  '\n'
                                  '**1:** You took a particularly heavy dose of spores. You contract **Spore Sickness** and must **roll 1d6 for severity.**\n'
                                  '\n'
                                  '**Head back to camp and report to a Medicine Cat!**'},
 1443836852317585418: {'name': 'Falling Ice',
                       'chance': 2.0,
                       'cooldown_hours': 24,
                       'message': 'A sharp **crack** cuts through the roar of Frozen Falls. High above, a heavy sheet of ice tears loose from the frozen ledge and drops toward '
                                  'the cats below, exploding against the stone in a spray of glittering shards.\n'
                                  '\n'
                                  '🧊 **FALLING ICE CHECK!**\n'
                                  '\n'
                                  'Roll **1d10** to get clear!\n'
                                  '\n'
                                  '**3–10:** You throw yourself out of the way before the ice crashes down and escape unharmed.\n'
                                  '\n'
                                  '**2:** A smaller shard clips you during the scramble, leaving a bruise or shallow cut.\n'
                                  '\n'
                                  '**1:** The falling ice or frantic escape catches you badly. **Roll 1d6 for injury severity.**\n'
                                  '\n'
                                  '**If injured, head back to camp and report to a Medicine Cat!**'}}


def validate_hunt_tables():
    """Fail loudly on startup/import if a hunting chance table stops totaling 100%."""
    for location, entries in HUNT_TABLES.items():
        total = sum(entry[0] for entry in entries)
        if total != 100:
            raise ValueError(f"Hunt table for {location} totals {total}%, expected 100%.")


validate_hunt_tables()


def hunt_fallback_prompt(location, species):
    """Safety fallback for a species whose prompt pool is accidentally missing."""
    party_rules = {
        "Golden Eagle": (4, 50), "Eagle": (4, 50), "Red-tailed Hawk": (4, 40),
        "Owl": (4, 40), "Vulture": (4, 50), "Mountain Goat": (6, 80),
        "Muskrat": (3, 25), "Beaver": (5, 60), "Heron": (3, 25),
        "Raccoon": (4, 45), "Weasel": (4, 50),
    }
    if species == "Caribou Scraps":
        return "Old caribou scraps lie half-buried nearby. **There is no chase this time, but the usable scraps may be taken if the area seems safe.**"
    if species in party_rules:
        cats, combined = party_rules[species]
        return f"A {species.lower()} appears in {location}, presenting a difficult but possible hunt. **Roll to hunt it! Hunting party required: {cats}+ cats, combined roll over {combined}.**"
    plural = species in {"Minnows", "Nestling Birds"}
    pronoun = "them" if plural else "it"
    article = "" if plural else ("an " if species[:1].lower() in "aeiou" else "a ")
    subject = species.lower() if plural else article + species.lower()
    return f"You spot {subject} moving through {location}. **Roll to catch {pronoun}!**"


def choose_hunt_result(location):
    if location in NO_PREY_HUNT_PROMPTS:
        return {"kind": "flavour", "text": random.choice(NO_PREY_HUNT_PROMPTS[location])}

    entries = HUNT_TABLES.get(location)
    if not entries:
        return {"kind": "error", "text": "No hunting table is configured for this location."}

    roll = random.uniform(0, 100)
    running = 0
    chosen = entries[-1]
    for entry in entries:
        running += entry[0]
        if roll <= running:
            chosen = entry
            break

    _weight, kind, payload = chosen

    if kind == "threat":
        return {"kind": "threat", "text": HUNT_THREATS[(location, payload)]}

    species = random.choice(payload)

    if kind == "shared" and random.random() < 0.5:
        threat_text = HUNT_SHARED_THREATS.get((location, species))
        if threat_text:
            return {"kind": "threat", "species": species, "text": threat_text}

    prompts = HUNT_PROMPTS.get((location, species), [])
    prompt = random.choice(prompts) if prompts else hunt_fallback_prompt(location, species)

    if location == "Reed Marsh" and species == "Beaver":
        prompt += f"\n\n**If the beaver hunt fails:** {REED_MARSH_BEAVER_FAIL_THREAT}"

    return {"kind": "prey", "species": species, "text": prompt}


@bot.tree.command(
    name="hunt",
    description="Search for prey using the hunting table for the channel you are currently in."
)
async def hunt_command(interaction: discord.Interaction):
    channel_info = HUNT_CHANNELS.get(interaction.channel_id)
    if not channel_info:
        await interaction.response.send_message(
            "❌ `/hunt` only works inside Echostone Mountain's designated hunting and territory channels.",
            ephemeral=True
        )
        return

    location = channel_info["location"]
    result = choose_hunt_result(location)

    if result["kind"] == "error":
        await interaction.response.send_message(result["text"], ephemeral=True)
        return

    header_icon = "⚠️" if result["kind"] == "threat" else channel_info["emoji"]
    await interaction.response.send_message(
        f"{header_icon} **Hunt — {location}**\n\n{result['text']}",
        allowed_mentions=discord.AllowedMentions.none()
    )


def _parse_hunt_timestamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=TZ)
        return parsed.astimezone(TZ)
    except (TypeError, ValueError):
        return None


async def _hunt_channel_had_recent_human_activity(channel, since):
    async for message in channel.history(limit=100, after=since):
        if not getattr(message.author, "bot", False):
            return True
    return False


# Process-local guard for ambient hazard checks. This intentionally is not
# persisted to Supabase: recording every routine hourly check would otherwise
# upload CODY's entire bot_data payload even when nothing happened.
_ambient_hazard_last_checked_memory = {}


@tasks.loop(hours=1)
async def ambient_hunt_hazards():
    """Rare ambient hazards in special non-hunting locations, only after recent RP activity."""
    now = datetime.now(TZ)
    since = now - timedelta(hours=1)
    hour_key = now.strftime("%Y-%m-%dT%H")

    for channel_id, hazard in AMBIENT_HUNT_HAZARDS.items():
        key = str(channel_id)

        async with data_lock:
            last_triggered = _parse_hunt_timestamp(
                data.setdefault("ambient_hazard_last_triggered", {}).get(key)
            )

        # Prevent duplicate checks while this CODY process is running without
        # writing routine hourly timestamps to Supabase. A Railway restart can
        # therefore allow at most one extra rare roll in that hour.
        if _ambient_hazard_last_checked_memory.get(key) == hour_key:
            continue

        channel = bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(channel_id)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException) as error:
                print(f"Ambient hunt hazard could not access channel {channel_id}: {error}")
                continue

        try:
            recent_activity = await _hunt_channel_had_recent_human_activity(channel, since)
        except discord.Forbidden:
            print(f"Ambient hunt hazard needs Read Message History in channel {channel_id}.")
            continue
        except discord.HTTPException as error:
            print(f"Ambient hunt hazard history check failed in channel {channel_id}: {error}")
            continue
        except Exception as error:
            print(f"Ambient hunt hazard unexpected history error in channel {channel_id}: {error}")
            continue

        # Mark this hour as checked only in memory. No database write is needed
        # unless a hazard actually triggers.
        _ambient_hazard_last_checked_memory[key] = hour_key

        if not recent_activity:
            continue

        cooldown = timedelta(hours=float(hazard.get("cooldown_hours", 24)))
        if last_triggered and now - last_triggered < cooldown:
            continue

        if random.random() * 100 >= float(hazard.get("chance", 2.0)):
            continue

        try:
            await channel.send(
                hazard["message"],
                allowed_mentions=discord.AllowedMentions.none()
            )
        except discord.Forbidden:
            print(f"Ambient hunt hazard cannot send messages in channel {channel_id}.")
            continue
        except discord.HTTPException as error:
            print(f"Ambient hunt hazard send failed in channel {channel_id}: {error}")
            continue

        async with data_lock:
            data.setdefault("ambient_hazard_last_triggered", {})[key] = now.isoformat()
            save_data(data)

        print(f"Triggered ambient hunt hazard {hazard.get('name')} in {channel_id}.")


@ambient_hunt_hazards.before_loop
async def before_ambient_hunt_hazards():
    await bot.wait_until_ready()

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

    if not severe_weather_report.is_running():
        severe_weather_report.start()

    if not gathering_scheduler.is_running():
        gathering_scheduler.start()

    try:
        await migrate_active_quests_to_monthly_schedule()
    except Exception as error:
        print(f"Monthly quest schedule migration failed: {error}")

    # Apply the Aug. 28 quest updates to already-active quests instead of waiting
    # until the next first-of-the-month reset.
    try:
        async with data_lock:
            broadened_quests = broaden_current_hunting_quests_once()
            rollout_role_quests = ensure_role_quest_rollout_once()
            if broadened_quests or rollout_role_quests:
                save_data(data)

        quest_channel = bot.get_channel(QUEST_CHANNEL_ID)
        if quest_channel and broadened_quests:
            lines = ["🎯 **Hunting Quest Update**", "Active hunting quests have been broadened so they no longer depend on one exact prey species spawning.", ""]
            for group, old_title, new_quest in broadened_quests:
                lines.extend([clan_mention(group), f"~~{old_title}~~ → **{new_quest.get('title', 'Broad Hunting Quest')}**", new_quest.get("objective", ""), ""])
            await send_long_message(quest_channel, "\n".join(lines))

        if quest_channel and rollout_role_quests:
            blocks = [format_role_quest_block(quest, index=index, total=len(rollout_role_quests)) for index, quest in enumerate(rollout_role_quests, start=1)]
            await send_long_message(quest_channel, "🌟 **New Optional Role-Specific Quest!**\n\n" + "\n\n".join(blocks))
    except Exception as error:
        print(f"Aug. 28 quest update migration failed: {error}")

    if not monthly_quest_report.is_running():
        monthly_quest_report.start()

    if not quest_reminders.is_running():
        quest_reminders.start()

    if not check_hiatuses.is_running():
        check_hiatuses.start()

    if not check_membership_milestones.is_running():
        check_membership_milestones.start()

    if not check_activity_reminders.is_running():
        check_activity_reminders.start()

    if not check_rules_onboarding.is_running():
        check_rules_onboarding.start()

    if not ambient_hunt_hazards.is_running():
        ambient_hunt_hazards.start()

    try:
        await asyncio.wait_for(
            update_honour_tracker_message(),
            timeout=HONOUR_DISCORD_TIMEOUT_SECONDS
        )
        print("Honour Role tracker is up to date.")
    except Exception as error:
        print(f"Honour Role tracker update failed: {error}")

    # Once /allegiance add or /allegiance refresh has initialized the boards,
    # reconcile them again on every restart without creating duplicate legacy boards.
    if data.get("allegiance_message_ids"):
        result = await refresh_allegiances_safely("bot startup")
        if result.get("errors"):
            print(f"Allegiance startup refresh had {len(result['errors'])} error(s).")
        else:
            print("Allegiance boards are up to date.")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"Slash command error: {error}")

    try:
        await safe_respond(
            interaction,
            "Something went wrong while running that command. Check the Railway logs for the exact error.",
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

@bot.tree.command(name="revertmoon", description="Staff only. Revert to the saved state before the last moon advance")
@app_commands.describe(
    confirm="Type YES to confirm you want to revert the last moon advance"
)
async def revertmoon(interaction: discord.Interaction, confirm: str):
    if not await staff_command_check(interaction):
        return

    if confirm != "YES":
        await interaction.response.send_message(
            "⚠️ This will restore the bot to the saved state before the last moon advance.\n"
            "Run `/revertmoon confirm: YES` if you are sure.",
            ephemeral=True
        )
        return

    async with data_lock:
        snapshot = data.get("last_moon_snapshot")

        if not snapshot:
            await interaction.response.send_message(
                "❌ No moon snapshot was found. I can only revert a moon after `/advancemoon` has saved a snapshot.",
                ephemeral=True
            )
            return

        current_moon = data.get("moon", "Unknown")
        snapshot_moon = snapshot.get("moon", "Unknown")

        data.clear()
        data.update(copy.deepcopy(snapshot))

        # Keep a copy so you do not lose the ability to inspect/revert info immediately
        data["last_moon_snapshot"] = snapshot

        save_data(data)

    await interaction.response.send_message(
        f"↩️ Moon reverted successfully.\n"
        f"Restored from **Moon {current_moon}** back to **Moon {snapshot_moon}**.",
        ephemeral=True
    )

prophecy_group = app_commands.Group(
    name="prophecy",
    description="Prophecy commands"
)


@prophecy_group.command(name="post", description="Staff only. Post a custom prophecy or omen")
@app_commands.describe(
    text="The custom prophecy or omen to post"
)
async def prophecy_post(interaction: discord.Interaction, text: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        data["active_prophecy"] = text
        save_data(data)

    message = (
        f"{prophecy_role_mentions()}\n"
        "🌙 **A prophecy has been received...**\n\n"
        f"{text}"
    )

    channel = bot.get_channel(REPORT_CHANNEL_ID)

    if channel:
        await send_long_message(channel, message)
        await interaction.response.send_message(
            "🌙 Custom prophecy posted and saved as the active prophecy.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Could not find the report channel.",
            ephemeral=True
        )


@prophecy_group.command(name="pause", description="Staff only. Pause new monthly prophecy rolls")
@app_commands.describe(
    current_prophecy="Optional. Save this as the prophecy to keep showing while paused."
)
async def prophecy_pause(interaction: discord.Interaction, current_prophecy: str = None):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        data["prophecies_paused"] = True

        if current_prophecy:
            data["active_prophecy"] = current_prophecy
        else:
            get_saved_active_prophecy()

        active_prophecy = data.get("active_prophecy")
        save_data(data)

    if active_prophecy:
        await interaction.response.send_message(
            f"🌙 Prophecy rolls are now paused. The active prophecy will remain:\n\n{active_prophecy}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "🌙 Prophecy rolls are now paused. No active prophecy was found, so no new prophecy will roll until `/prophecy unpause` is used.",
            ephemeral=True
        )


@prophecy_group.command(name="unpause", description="Staff only. Resume new monthly prophecy rolls")
async def prophecy_unpause(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        data["prophecies_paused"] = False
        save_data(data)

    await interaction.response.send_message(
        "🌙 Prophecy rolls are no longer paused. The next moon report can roll a new prophecy.",
        ephemeral=True
    )


@prophecy_group.command(name="status", description="Staff only. Check whether prophecy rolls are paused")
async def prophecy_status(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    paused = data.get("prophecies_paused", False)
    active_prophecy = data.get("active_prophecy") or "None saved."
    status_text = "Paused" if paused else "Rolling normally"

    await interaction.response.send_message(
        f"🌙 **Prophecy Status:** {status_text}\n"
        f"**Active Prophecy:** {active_prophecy}",
        ephemeral=True
    )


@bot.tree.command(name="advancemoon", description="Advance the moon manually")
async def advance_moon(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer()

    report = await run_moon_update()
    story_message = await build_clan_report_text(report)
    age_message = await build_age_report_text(report)

    age_channel = bot.get_channel(AGE_REPORT_CHANNEL_ID)
    story_channel = bot.get_channel(REPORT_CHANNEL_ID)

    if age_channel:
        await send_long_message(
            age_channel,
            "@everyone 🌙 A moon has passed over Echostone Mountain. Every living cat turns one moon older unless their age is frozen.\n\n" + age_message
        )

    if story_channel:
        await send_long_message(
            story_channel,
            "@everyone 🌙 A moon has been manually advanced across the Clans...\n\n" + story_message
        )

    await refresh_allegiances_safely("manual moon advance")
    await interaction.followup.send("🌙 Moon advanced manually. Age records and story updates were sent to their separate channels.")

# ─────────────────────────────
# /BOTINFO
# ─────────────────────────────

@bot.tree.command(name="botinfo", description="View a full guide to all major bot commands")
async def botinfo(interaction: discord.Interaction):
    message = (
        "📘 **ECHOSTONE MOUNTAIN BOT GUIDE** 📘\n\n"

        "🌙 **Moon / System Commands**\n"
        "`/moon` — View the current moon, season, and clan status\n"
        "`/moontest [Moon Number]` — Staff only. Preview what a future moon report would look like without saving changes\n"
        "`/advancemoon` — Staff only. Manually advances one moon and posts the report\n"
        "`/resetmoon` — Staff only. Resets moon count and adjusts living cat ages\n"
        "`/weatherreport` — Manually post or view this week's weather report\n"
        "`/setweather` — Staff only. Manually set custom weather\n"
        "`/severeweather trigger` — Staff only. Trigger a custom event and choose primary/secondary groups, locations, modifiers, and duration\n"
        "`/severeweather roll` — Staff only. Run the weekly severe-weather roll early\n"
        "`/severeweather active` — View current severe-weather effects\n"
        "`/severeweather modifier` — Check the severe-weather modifier for a territory/location\n"
        "`/severeweather end` — Staff only. End an active event early\n"
        "`/severeweather aurora` — Staff only. Trigger the Northern Lights and Spirit Veil\n"
        "`/prophecy post` — Staff only. Post a custom prophecy or omen\n`/prophecy pause` — Staff only. Pause new monthly prophecy rolls and keep the active prophecy\n`/prophecy unpause` — Staff only. Resume new monthly prophecy rolls\n"
        "`/revertmoon` — Staff only. Reverts to the saved state before the last moon advance\n\n"

        "📜 **Quest / Gathering Commands**\n"
        "`/quest force` — Quest manager only. Clear and force-post replacement quests while keeping the monthly first-of-the-month schedule\n"
        "`/quest progress` — View current monthly quest status, contributors, and exactly how much prey is still needed\n`/quest catch [Cat] [Prey]` — Record a hunting-quest catch; the OC's first contribution earns a Connection Token\n`/quest contribute [Cat]` — Record your OC as a contributor to a non-hunting monthly quest\n`/quest perks` — View all Connection Perks and token costs\n`/quest redeemperk [Cat] [Perk]` — Spend Connection Tokens on a permanent perk badge\n`/quest track [Cat] [Prey]` — Great Tracker perk: once per moon, choose a specific prey encounter\n`/quest complete [Clan]` — Staff only. Complete a quest and award success tokens to registered contributors\n`/quest role` — View the current optional role-specific quests\n`/quest rolecomplete [Cat] [Quest Number]` — Staff only. Complete role quest 1 or 2 with an eligible OC and award a random personal reward\n`/quest rolereroll [Quest Number]` — Staff only. Replace role quest 1 or 2\n`/quest usebonus [Cat] [Bonus]` — Staff only. Mark a saved one-use quest bonus as spent after the roll/activity\n`/resetquest [Clan/Outsider/All]` — Staff only. Replace one or all active quests/events while keeping the current due date\n"
        "`/gatheringreport [ClanName]` — Generate a Clan-specific report including recent promotions, deaths, injuries, quest results, and major story changes\n"
        "`Automatic Gatherings` — The full Gathering runs on the last Thursday; the Medicine Cat Gathering runs on the second Thursday. Votes open 7 days early and close after 3 days. Neither Gathering may be skipped two months in a row.\n"
        "`/rollhelp` — Helps calculate whether an OC caught their prey using their roll, modifiers, and required hunting number\n\n"

        "🐾 **General Member Commands**\n"
        "`/catinfo [Name]` — View full details about a cat\n"
        "`/oclist [User]` — Public OC list grouped by player, including each living OC's hunger\n"
        "`/ocowner [Cat]` — Find which Discord user owns a specific OC\n"
        "`/cats [Clan]` — View all cats by clan or all clans\n"
        "`/clan [ClanName]` — View one clan roster\n"
        "`/cattinder [Name] [Clan]` — Find age-appropriate romance options\n"
        "`/question` — Random OC question prompt system\n"
        "`/hunt` — In a designated territory channel, randomly find prey or a local threat using that location’s prey table; no location argument needed\n"
        "`/needsmentor` — View apprentices and medicine cat apprentices who do not currently have mentors\n"
        "`/upcomingceremonies [Clan]` — View eligible kits, apprentices, and elder candidates for all Clans or one Clan\n\n"

        "📜 **Plot Commands**\n"
        "`/plot member` — Add or update an existing cat on the plot roster\n"
        "`/plot remove` — Remove a cat from the plot roster\n"
        "`/plot roster` — Show all assigned Clan and Outsider plot members\n\n"
        
        "🍽️ **Feeding / Hunger Commands**\n"
        "`/feed cat [Name]` — Feed an OC normal prey and raise their hunger level by 1\n"
        "`/feed cat [Name] [Large Prey]` — Feed an OC large prey and raise their hunger level by 2\n"
        "`/feed reset [Name]` — Staff only. Reset one OC's hunger back to Satisfied with a fresh timer\n"
        "`/feed resetclan [Clan]` — Staff only. Reset every living cat in a Clan or Outsider group back to Satisfied with a fresh timer\n"
        "`/feed hunger [Clan]` — Check which cats in a Clan are Starving, Hungry, or Satisfied\n"
        "Well Fed lasts 2 weeks before dropping to Full. Full lasts 2 weeks before dropping to Satisfied. Satisfied lasts 30 days before Hungry, and Hungry lasts 30 days before Starving.\n"
        "Hunger affects hunting rolls: Starving -2, Hungry -1, Satisfied no change, Full +1, Well Fed +2.\n\n"

        "🛠️ **Staff Cat Management**\n"
        "`/cat add` — Add a new living cat\n"
        "`/cat adddead` — Add a dead cat to records\n"
        "`/cat delete` — Permanently delete a cat\n"
        "`/cat rename` — Rename a cat and update all references\n"
        "`/cat rank` — Change rank manually\n"
        "`/cat age` — Set exact age\n"
        "`/cat markdead` — Mark a living cat as dead\n"
        "`/changeclan` — Staff only. Move a cat to a different Clan or to/from Outsider\n"
        "`/cat delayceremony` — Delay automatic rank-up ceremonies\n"
        "`/cat tinderhide` — Hide/unhide a cat from Cat Tinder\n"
        "`/freezecat` — Staff only. Freeze or unfreeze a cat's age and/or hunger, either indefinitely or for a set number of days\n"
        "`/frozenlist` — Staff only. View all cats with active age or hunger freezes\n\n"
        "`/cat clearhistorymoon` — Delete cat history entries from a specific moon\n\n"

        "🐾 **NPC Commands**\n"
        "`/npc add` — Staff only. Add a new living NPC cat that appears on Clan/Outsider rosters\n"
        "`/npc adddead` — Staff only. Add an NPC who is already deceased and choose StarClan, Dark Forest, or Unknown Residence\n"
        "`/allegiance addnpc [Cat]` — Staff only. Add an NPC to Allegiances without a player mention or character-sheet link\n"
        "`/npc convert` — Staff only. Change an existing cat into an NPC\n"
        "`/npc markdead` — Staff only. Mark a living NPC dead and choose their afterlife\n"
        "NPCs age every moon and can use normal rank, rename, relationship, and death records, but their hunger does not decay.\n\n"

        "🌫️ **Outsider Group Commands**\n"
        "`/outsidergroup add [Name]` — Staff only. Add a persistent Outsider group\n"
        "`/outsidergroup assign [Cat] [Group]` — Staff only. Assign or move an existing Outsider to a saved group\n"
        "`/outsidergroup change [Cat] [Group]` — Staff only. Move an Outsider from one group to another\n"
        "`/outsidergroup rename [Group] [New Name]` — Staff only. Rename a group and automatically update every cat in it\n"
        "`/outsidergroup delete [Group]` — Staff only. Delete a group; cats in it become unaffiliated\n"
        "`/outsidergroup list` — View all available Outsider groups\n\n"

        "📚 **Allegiance Commands**\n"
        "`/allegiance add [Cat] [User] [Character Sheet]` — Staff only. Link an existing tracker cat to their player and sheet; the bot places them in the correct living/deceased allegiance section automatically\n"
        "`/allegiance remove [Cat]` — Staff only. Remove a cat from the automated allegiance boards without deleting their tracker record\n"
        "`/allegiance refresh` — Staff only. Rebuild all 4 Clan, Outsider, and deceased allegiance channels from the current tracker\n"
        "Player can be entered by Discord display name or username; no User ID is required.\n\n"

        "🏅 **Honour Role Commands**\n"
        "`/honour role [Cat] [Role]` — Staff only. Name an eligible Warrior or Apprentice to a Clan Honour Role\n"
        "`/honour remove [Cat]` — Staff only. Remove a cat's current Honour Role and reopen the position\n"
        "`/honour tracker` — Staff only. Refresh the single Honour Role availability tracker message\n\n"

        "♾️ **Permanent Condition Commands**\n"
        "`/condition add [Cat] [Status]` — Staff only. Add a permanent status such as Blind, Wobbly, Paralyzed, or Has ADHD\n"
        "`/condition remove [Cat] [Status]` — Staff only. Remove one permanent status\n"
        "`/condition clear [Cat]` — Staff only. Remove every permanent status from a cat\n\n"

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
        "🌙 **Hiatus Commands**\n"
        "`/hiatus add [user_id] [days]` — Staff only. Add a hiatus, remove Member, and add the Hiatus role\n"
        "`/hiatus edit [user_id] [days]` — Staff only. Change how long a current hiatus lasts from today\n"
        "`/hiatus end [user_id]` — Staff only. Manually remove someone from hiatus, restore Member, and remove Hiatus\n"
        "`/hiatus all` — Staff only. View everyone currently on hiatus and how many days remain\n\n"

        "💭 **OC Question System**\n"
        "• `/question` works in any channel\n"
        "• Maximum 2 uses per Toronto calendar day\n"
        "• Pulls randomly from your massive OC question list\n"
        "• Prevents repeats until all questions are used\n"
        "• Includes personality prompts, silly hypotheticals, and “most likely to” questions\n\n"

        "📌 **Important Notes**\n"
        "• Most staff commands only work in the designated bot command channel\n"
        "• Quests automatically post on the 1st of every month at 9 AM, with reminders at 14 days, 7 days, and 3 days remaining\n"
        "• Normal weather updates post weekly\n"
        "• Severe weather rolls automatically every Monday at 4 PM Toronto time unless staff already triggered/rolled an event that week\n"
        "• Each Clan or populated Outsider group has a 20% weekly disaster chance, primary disasters are limited to once per calendar month, and there cannot be two fully quiet severe-weather weeks in a row\n"
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
hiatus_group = app_commands.Group(name="hiatus", description="Manage member hiatuses")
honour_group = app_commands.Group(name="honour", description="Manage Clan Honour Roles")
condition_group = app_commands.Group(name="condition", description="Manage permanent cat status conditions")
plot_group = app_commands.Group(name="plot", description="Manage plot-member records")
npc_group = app_commands.Group(name="npc", description="Manage NPC cat records")
outsider_group = app_commands.Group(name="outsidergroup", description="Manage Outsider groups")
allegiance_group = app_commands.Group(name="allegiance", description="Manage automated allegiance boards")


@allegiance_group.command(name="add", description="Link a cat to their player and character sheet")
@app_commands.describe(
    cat_name="Existing cat in the tracker",
    user="Player display name or Discord username",
    character_sheet="Link to the cat's character form/sheet"
)
@app_commands.autocomplete(user=allegiance_user_autocomplete)
async def allegiance_add_command(
    interaction: discord.Interaction,
    cat_name: str,
    user: str,
    character_sheet: str
):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    member, member_error = await resolve_allegiance_member(interaction.guild, user)
    if member_error:
        await interaction.edit_original_response(content=f"❌ {member_error}")
        return

    sheet_url = str(character_sheet or "").strip()
    if not (sheet_url.startswith("https://") or sheet_url.startswith("http://")):
        await interaction.edit_original_response(
            content="❌ Character sheet must be a full `http://` or `https://` link."
        )
        return

    async with data_lock:
        cats = data.get("cats", {})
        if cat_name not in cats:
            await interaction.edit_original_response(
                content=f"❌ Cat **{cat_name}** was not found. Add them to the cat tracker first."
            )
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)

        placement_problem = allegiance_record_problem(cat_name, cat)
        if placement_problem:
            await interaction.edit_original_response(
                content=(
                    f"❌ I cannot place **{cat_name}** on Allegiances because their tracker record is invalid.\n"
                    f"`{placement_problem}`\n"
                    "Check `/catinfo` and correct their Clan/rank first."
                )
            )
            return

        if bool(cat.get("is_npc", False)):
            await interaction.edit_original_response(
                content=f"❌ **{cat_name}** is an NPC. Use `/allegiance addnpc` instead; NPCs do not need a player or character sheet."
            )
            return

        cat["allegiance_npc"] = False
        cat["allegiance_owner_id"] = str(member.id)
        cat["allegiance_owner_name"] = member.display_name
        cat["oc_owner_id"] = str(member.id)
        cat["oc_owner_name"] = member.display_name
        cat["character_sheet_url"] = sheet_url
        save_data(data)

    result = await refresh_allegiances_safely("/allegiance add", force=True)
    error_note = ""
    if result.get("errors"):
        error_note = "\n⚠️ The record saved, but one or more allegiance channels could not be updated. Send the error to the bot owner."

    destination = "the deceased allegiances" if cat_is_dead(cat) else (
        "the Outsider allegiances" if allegiance_tracker_clan(cat) == "Outsider" else f"{allegiance_tracker_clan(cat)} allegiances"
    )
    await interaction.edit_original_response(
        content=(
            f"✅ **{cat_name}** is linked to {member.mention} and their character sheet.\n"
            f"They were placed automatically in **{destination}** based on their tracker record."
            f"{error_note}"
        )
    )


@allegiance_group.command(name="addnpc", description="Add an NPC to the automated allegiance boards")
@app_commands.describe(cat_name="Existing NPC cat in the tracker")
async def allegiance_addnpc_command(interaction: discord.Interaction, cat_name: str):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    async with data_lock:
        cats = data.get("cats", {})
        if cat_name not in cats:
            await interaction.edit_original_response(
                content=f"❌ NPC **{cat_name}** was not found. Add them to the cat tracker first with `/npc add` or `/npc adddead`."
            )
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)

        placement_problem = allegiance_record_problem(cat_name, cat)
        if placement_problem:
            await interaction.edit_original_response(
                content=(
                    f"❌ I cannot place **{cat_name}** on Allegiances because their tracker record is invalid.\n"
                    f"`{placement_problem}`\n"
                    "Check `/catinfo` and correct their Clan/rank first."
                )
            )
            return

        if not bool(cat.get("is_npc", False)):
            await interaction.edit_original_response(
                content=f"❌ **{cat_name}** is not marked as an NPC. Use `/allegiance add` for regular OCs."
            )
            return

        cat["allegiance_npc"] = True
        # NPC allegiance entries intentionally have no player mention or sheet link,
        # and NPCs are never counted on the player OC list.
        cat["allegiance_owner_id"] = None
        cat["allegiance_owner_name"] = None
        cat["oc_owner_id"] = None
        cat["oc_owner_name"] = None
        cat["character_sheet_url"] = None
        save_data(data)

    result = await refresh_allegiances_safely("/allegiance addnpc", force=True)
    error_note = ""
    if result.get("errors"):
        error_note = "\n⚠️ The NPC was saved, but one or more allegiance channels could not be updated. Send the error to the bot owner."

    destination = "the deceased allegiances" if cat_is_dead(cat) else (
        "the Outsider allegiances" if allegiance_tracker_clan(cat) == "Outsider" else f"{allegiance_tracker_clan(cat)} allegiances"
    )
    await interaction.edit_original_response(
        content=(
            f"✅ **{display_cat_name(cat_name, cat)}** was added to **{destination}**.\n"
            "NPC allegiance entries show only the NPC's name, with no player mention or character-sheet link."
            f"{error_note}"
        )
    )


@allegiance_group.command(name="remove", description="Remove a cat from the automated allegiance boards")
@app_commands.describe(cat_name="Cat to unlink from allegiances")
async def allegiance_remove_command(interaction: discord.Interaction, cat_name: str):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    async with data_lock:
        cats = data.get("cats", {})
        if cat_name not in cats:
            await interaction.edit_original_response(content="❌ Cat not found.")
            return

        cat = cats[cat_name]
        if (
            not allegiance_is_linked(cat)
            and not cat.get("allegiance_owner_id")
            and not cat.get("character_sheet_url")
            and not cat.get("allegiance_npc")
        ):
            await interaction.edit_original_response(
                content=f"❌ **{cat_name}** is not currently linked to the allegiance boards."
            )
            return

        # Preserve player ownership for /oclist even when the character is
        # temporarily unpublished from the automated allegiance boards.
        if not cat.get("oc_owner_id") and cat.get("allegiance_owner_id"):
            cat["oc_owner_id"] = str(cat.get("allegiance_owner_id"))
        if not cat.get("oc_owner_name") and cat.get("allegiance_owner_name"):
            cat["oc_owner_name"] = cat.get("allegiance_owner_name")

        cat["allegiance_owner_id"] = None
        cat["allegiance_owner_name"] = None
        cat["character_sheet_url"] = None
        cat["allegiance_npc"] = False
        save_data(data)

    result = await refresh_allegiances_safely("/allegiance remove", force=True)
    error_note = ""
    if result.get("errors"):
        error_note = " One or more allegiance channels could not be refreshed."

    await interaction.edit_original_response(
        content=f"🧹 **{cat_name}** was removed from the automated allegiance boards.{error_note}"
    )


@allegiance_group.command(name="refresh", description="Rebuild all living and deceased allegiance boards")
async def allegiance_refresh_command(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    result = await refresh_allegiances_safely("/allegiance refresh", force=True)

    if result.get("errors"):
        await interaction.edit_original_response(
            content=(
                f"⚠️ Refreshed **{result.get('updated', 0)}/6** allegiance channels. "
                "At least one channel could not be accessed or updated."
            )
        )
        return

    await interaction.edit_original_response(
        content="✅ All **6 allegiance channels** were rebuilt from the current cat tracker."
    )


@outsider_group.command(name="add", description="Add a new Outsider group")
@app_commands.describe(name="Name of the new Outsider group")
async def outsider_group_add_command(interaction: discord.Interaction, name: str):
    if not await staff_command_check(interaction):
        return

    clean_name = name.strip()
    if not clean_name:
        await interaction.response.send_message(
            "❌ Outsider group name cannot be blank.",
            ephemeral=True
        )
        return

    if len(clean_name) > 80:
        await interaction.response.send_message(
            "❌ Keep Outsider group names to 80 characters or fewer.",
            ephemeral=True
        )
        return

    async with data_lock:
        existing = get_outsider_groups()
        if any(group.casefold() == clean_name.casefold() for group in existing):
            matched = next(group for group in existing if group.casefold() == clean_name.casefold())
            await interaction.response.send_message(
                f"❌ **{matched}** already exists as an Outsider group.",
                ephemeral=True
            )
            return

        # This also un-retires a previously deleted built-in group with the same name.
        activate_outsider_group_name(clean_name)
        save_data(data)

    await interaction.response.send_message(
        f"🌫️ Added **{clean_name}** as a new Outsider group. It can now be selected when adding Outsider cats or NPCs."
    )


async def change_outsider_cat_group(interaction, cat_name, group, command_label):
    """Shared implementation for /outsidergroup assign and /outsidergroup change."""
    resolved_group = resolve_outsider_group(group)
    if resolved_group is None:
        await interaction.response.send_message(
            "❌ That Outsider group does not exist. Add it first with `/outsidergroup add`.",
            ephemeral=True
        )
        return

    async with data_lock:
        cats = data.get("cats", {})
        if cat_name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = cats[cat_name]
        if cat.get("clan") != "Outsider":
            await interaction.response.send_message(
                f"❌ **{cat_name}** is not recorded as an Outsider.",
                ephemeral=True
            )
            return

        if cat.get("rank") == "Kittypet":
            await interaction.response.send_message(
                "❌ Kittypets cannot be assigned to an Outsider group.",
                ephemeral=True
            )
            return

        old_group = str(cat.get("faction") or "").strip() or None
        if old_group and old_group.casefold() == resolved_group.casefold():
            await interaction.response.send_message(
                f"ℹ️ **{cat_name}** is already part of **{resolved_group}**.",
                ephemeral=True
            )
            return

        cat["faction"] = resolved_group
        add_history(cat, f"Outsider group changed from {old_group or 'None'} to {resolved_group}")
        save_data(data)

    await interaction.response.send_message(
        f"🌫️ **{cat_name}** moved from **{old_group or 'Unaffiliated'}** to **{resolved_group}**."
    )
    await refresh_allegiances_safely(command_label)


@outsider_group.command(name="assign", description="Assign or move an Outsider cat to a saved group")
@app_commands.describe(cat_name="Existing Outsider cat", group="Outsider group")
@app_commands.autocomplete(group=outsider_group_autocomplete)
async def outsider_group_assign_command(
    interaction: discord.Interaction,
    cat_name: str,
    group: str
):
    if not await staff_command_check(interaction):
        return
    await change_outsider_cat_group(interaction, cat_name, group, "/outsidergroup assign")


@outsider_group.command(name="change", description="Move an Outsider cat from one group to another")
@app_commands.describe(cat_name="Existing Outsider cat", group="New Outsider group")
@app_commands.autocomplete(group=outsider_group_autocomplete)
async def outsider_group_change_command(
    interaction: discord.Interaction,
    cat_name: str,
    group: str
):
    if not await staff_command_check(interaction):
        return
    await change_outsider_cat_group(interaction, cat_name, group, "/outsidergroup change")


@outsider_group.command(name="rename", description="Rename an Outsider group and update all cats in it")
@app_commands.describe(group="Existing Outsider group", new_name="New name for the group")
@app_commands.autocomplete(group=outsider_group_autocomplete)
async def outsider_group_rename_command(
    interaction: discord.Interaction,
    group: str,
    new_name: str
):
    if not await staff_command_check(interaction):
        return

    resolved_group = resolve_outsider_group(group)
    if resolved_group is None:
        await interaction.response.send_message(
            "❌ That Outsider group does not exist.",
            ephemeral=True
        )
        return

    clean_new_name = str(new_name or "").strip()
    if not clean_new_name:
        await interaction.response.send_message(
            "❌ The new group name cannot be blank.",
            ephemeral=True
        )
        return
    if len(clean_new_name) > 80:
        await interaction.response.send_message(
            "❌ Keep Outsider group names to 80 characters or fewer.",
            ephemeral=True
        )
        return
    if resolved_group.casefold() == clean_new_name.casefold():
        await interaction.response.send_message(
            f"ℹ️ **{resolved_group}** already has that name.",
            ephemeral=True
        )
        return

    existing = get_outsider_groups()
    duplicate = next(
        (value for value in existing if value.casefold() == clean_new_name.casefold()),
        None
    )
    if duplicate:
        await interaction.response.send_message(
            f"❌ **{duplicate}** already exists. Use `/outsidergroup change` to move individual cats into it instead.",
            ephemeral=True
        )
        return

    async with data_lock:
        affected = rename_outsider_group_records(resolved_group, clean_new_name)
        save_data(data)

    await interaction.response.send_message(
        f"✏️ Renamed **{resolved_group}** to **{clean_new_name}**. "
        f"Updated **{affected}** cat{'s' if affected != 1 else ''} automatically."
    )
    await refresh_allegiances_safely("Outsider group rename", force=True)


@outsider_group.command(name="delete", description="Delete an Outsider group and make its cats unaffiliated")
@app_commands.describe(group="Outsider group to delete")
@app_commands.autocomplete(group=outsider_group_autocomplete)
async def outsider_group_delete_command(
    interaction: discord.Interaction,
    group: str
):
    if not await staff_command_check(interaction):
        return

    resolved_group = resolve_outsider_group(group)
    if resolved_group is None:
        await interaction.response.send_message(
            "❌ That Outsider group does not exist.",
            ephemeral=True
        )
        return

    async with data_lock:
        affected = delete_outsider_group_records(resolved_group)
        save_data(data)

    if affected:
        cat_note = (
            f" **{affected}** cat{'s were' if affected != 1 else ' was'} made unaffiliated. "
            "You can move them into another group with `/outsidergroup change`."
        )
    else:
        cat_note = " No cats were assigned to it."

    await interaction.response.send_message(
        f"🗑️ Deleted the Outsider group **{resolved_group}**.{cat_note}"
    )
    await refresh_allegiances_safely("Outsider group deletion", force=True)


@outsider_group.command(name="list", description="List all available Outsider groups")
async def outsider_group_list_command(interaction: discord.Interaction):
    groups = get_outsider_groups()
    await interaction.response.send_message(
        "🌫️ **Outsider Groups**\n" + "\n".join(f"• {group}" for group in groups),
        ephemeral=True
    )


@npc_group.command(name="add", description="Add a new NPC cat")
@app_commands.describe(
    name="NPC cat name",
    age="Age in moons",
    clan="Select Clan or Outsider",
    rank="Select rank",
    faction="Optional Outsider faction"
)
@app_commands.choices(clan=CLAN_CHOICES, rank=RANK_CHOICES)
@app_commands.autocomplete(faction=outsider_group_autocomplete)
async def npc_add_command(
    interaction: discord.Interaction,
    name: str,
    age: int,
    clan: app_commands.Choice[str],
    rank: app_commands.Choice[str],
    faction: str = None
):
    if not await staff_command_check(interaction):
        return

    if age < 0:
        await interaction.response.send_message("❌ Age cannot be negative.", ephemeral=True)
        return

    faction_value = resolve_outsider_group(faction) if faction else None
    if faction and faction_value is None:
        await interaction.response.send_message(
            "❌ That Outsider group does not exist. Add it first with `/outsidergroup add`.",
            ephemeral=True
        )
        return

    validation_error = validate_cat_rank(clan.value, rank.value, faction_value)
    if validation_error:
        await interaction.response.send_message(validation_error, ephemeral=True)
        return

    async with data_lock:
        if name in data.get("cats", {}):
            await interaction.response.send_message(
                "❌ That cat already exists. Use `/npc convert` to turn an existing cat into an NPC.",
                ephemeral=True
            )
            return

        data.setdefault("cats", {})[name] = {
            "clan": clan.value,
            "age": age,
            "rank": rank.value,
            "faction": faction_value,
            "status": "Alive",
            "afterlife": None,
            "death_moon": None,
            "born_moon": max(0, data.get("moon", 0) - age),
            "history": [f"Moon {data.get('moon', 0)}: Added to records as an NPC {rank.value}"],
            "exclude_from_tinder": False,
            "is_npc": True,
            "hunger_level": "Satisfied",
            "last_fed": None,
            "last_hunger_update": None
        }
        save_data(data)

    await interaction.response.send_message(
        f"🐾 Added **{name} (NPC)** to **{clan.value}** as **{rank.value}** at **{age} moons**."
    )


@npc_group.command(name="adddead", description="Add an NPC cat who is already dead")
@app_commands.describe(
    name="NPC cat name",
    age="Age at death in moons",
    clan="Clan they belonged to, or Outsider",
    rank="Rank at death",
    afterlife="Afterlife destination",
    group="Optional Outsider group",
    cause="Optional cause of death"
)
@app_commands.choices(clan=CLAN_CHOICES, rank=RANK_CHOICES, afterlife=AFTERLIFE_CHOICES)
@app_commands.autocomplete(group=outsider_group_autocomplete)
async def npc_adddead_command(
    interaction: discord.Interaction,
    name: str,
    age: int,
    clan: app_commands.Choice[str],
    rank: app_commands.Choice[str],
    afterlife: app_commands.Choice[str],
    group: str = None,
    cause: str = None
):
    if not await staff_command_check(interaction):
        return

    if age < 0:
        await interaction.response.send_message("❌ Age cannot be negative.", ephemeral=True)
        return

    group_value = resolve_outsider_group(group) if group else None
    if group and group_value is None:
        await interaction.response.send_message(
            "❌ That Outsider group does not exist. Add it first with `/outsidergroup add`.",
            ephemeral=True
        )
        return

    validation_error = validate_cat_rank(clan.value, rank.value, group_value)
    if validation_error:
        await interaction.response.send_message(validation_error, ephemeral=True)
        return

    async with data_lock:
        cats = data.setdefault("cats", {})
        if name in cats:
            await interaction.response.send_message(
                "❌ That cat already exists. If they are a living NPC, use `/npc markdead` instead.",
                ephemeral=True
            )
            return

        history_text = f"Moon {data.get('moon', 0)}: Added to records as a deceased NPC. Died as {rank.value}"
        if cause:
            history_text += f" from {cause}"
        history_text += f" and went to {afterlife.value}."

        cats[name] = {
            "clan": clan.value,
            "age": age,
            "rank": rank.value,
            "faction": group_value,
            "status": "Dead",
            "afterlife": afterlife.value,
            "death_moon": "Before records",
            "cause_of_death": cause,
            "born_moon": None,
            "history": [history_text],
            "exclude_from_tinder": True,
            "is_npc": True,
            "hunger_level": "Satisfied",
            "last_fed": None,
            "last_hunger_update": None
        }
        save_data(data)

    group_line = f"\n🌫️ Outsider Group: {group_value}" if group_value else ""
    cause_line = f"\n🩸 Cause of Death: {cause}" if cause else ""
    await interaction.response.send_message(
        f"💀 Added deceased NPC **{name} (NPC)**\n"
        f"⛺ Clan: {clan.value}\n"
        f"⚔ Rank at death: {rank.value}\n"
        f"🌙 Age at death: {age} moons\n"
        f"🌌 Afterlife: {afterlife.value}"
        f"{group_line}{cause_line}"
    )


@npc_group.command(name="convert", description="Change an existing cat into an NPC")
@app_commands.describe(cat_name="Existing cat to mark as an NPC")
async def npc_convert_command(interaction: discord.Interaction, cat_name: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})
        if cat_name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)

        if cat.get("is_npc"):
            await interaction.response.send_message(
                f"❌ **{cat_name}** is already an NPC.",
                ephemeral=True
            )
            return

        cat["is_npc"] = True
        add_history(cat, "Changed to NPC status")
        save_data(data)

    await interaction.response.send_message(
        f"🐾 **{cat_name}** is now marked as **{cat_name} (NPC)** on rosters. Their hunger will no longer decay."
    )
    await refresh_allegiances_safely("NPC conversion")


@npc_group.command(name="markdead", description="Mark an NPC as dead and choose their afterlife")
@app_commands.describe(
    cat_name="NPC cat name",
    afterlife="Afterlife destination",
    cause="Optional cause of death"
)
@app_commands.choices(afterlife=AFTERLIFE_CHOICES)
async def npc_markdead_command(
    interaction: discord.Interaction,
    cat_name: str,
    afterlife: app_commands.Choice[str],
    cause: str = None
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})
        if cat_name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)

        if not cat.get("is_npc"):
            await interaction.response.send_message(
                f"❌ **{cat_name}** is not marked as an NPC. Use `/cat markdead` for regular OCs.",
                ephemeral=True
            )
            return

        if cat_is_dead(cat):
            await interaction.response.send_message(
                f"❌ **{cat_name} (NPC)** is already deceased.",
                ephemeral=True
            )
            return

        had_honour_role = bool(cat.get("honour_role"))
        cat["status"] = "Dead"
        cat["afterlife"] = afterlife.value
        cat["death_moon"] = data.get("moon", 0)
        cat["cause_of_death"] = cause

        if cause:
            add_history(cat, f"Died from {cause} and went to {afterlife.value}")
        else:
            add_history(cat, f"Died and went to {afterlife.value}")

        save_data(data)

    await interaction.response.send_message(
        f"💀 **{cat_name} (NPC)** has died and gone to **{afterlife.value}**."
    )

    channel = bot.get_channel(DEATH_ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        death_message = (
            f"💀 **Death Announcement**\n"
            f"**{cat_name} (NPC)** has died and now walks in **{afterlife.value}**."
        )
        if cause:
            death_message += f"\n**Cause of Death:** {cause}"
        await channel.send(death_message)

    if had_honour_role:
        try:
            await update_honour_tracker_message()
        except Exception as error:
            print(f"Could not update Honour Role tracker after NPC death: {error}")

    await refresh_allegiances_safely("NPC death")


@plot_group.command(name="member", description="Add or update an existing cat as a plot member")
@app_commands.describe(
    cat_name="The existing cat to add to the plot roster",
    member_type="Choose whether this is a Clan cat or an Outsider",
    outsider_group="Required for Outsiders: The Murmur or Other"
)
@app_commands.choices(
    member_type=PLOT_MEMBER_TYPE_CHOICES,
    outsider_group=PLOT_OUTSIDER_GROUP_CHOICES
)
async def plot_member_command(
    interaction: discord.Interaction,
    cat_name: str,
    member_type: app_commands.Choice[str],
    outsider_group: app_commands.Choice[str] = None
):
    if not await plot_command_check(interaction):
        return

    await interaction.response.defer()

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name not in cats:
            await interaction.edit_original_response(
                content=f"❌ Cat '{cat_name}' was not found. Add them to the bot first."
            )
            return

        cat = cats[cat_name]
        saved_clan = cat.get("clan")
        selected_type = member_type.value

        if selected_type == "Clan":
            if saved_clan not in CLAN_NAMES_ONLY:
                await interaction.edit_original_response(
                    content=f"❌ **{cat_name}** is recorded as an Outsider. Choose **Outsider** instead."
                )
                return

            if outsider_group is not None:
                await interaction.edit_original_response(
                    content="❌ The Murmur/Other option is only used when the member type is Outsider."
                )
                return

            new_record = {
                "member_type": "Clan",
                "clan": saved_clan,
                "outsider_group": None,
                "added_at": datetime.now(TZ).isoformat(),
                "added_by": str(interaction.user.id)
            }
            display_group = saved_clan

        else:
            if saved_clan != "Outsider":
                await interaction.edit_original_response(
                    content=f"❌ **{cat_name}** is recorded in **{saved_clan}**. Choose **Clan** instead."
                )
                return

            if outsider_group is None:
                await interaction.edit_original_response(
                    content="❌ Choose whether this Outsider belongs under **The Murmur** or **Other**."
                )
                return

            new_record = {
                "member_type": "Outsider",
                "clan": "Outsider",
                "outsider_group": outsider_group.value,
                "added_at": datetime.now(TZ).isoformat(),
                "added_by": str(interaction.user.id)
            }
            display_group = "The Murmur" if outsider_group.value == "Murmur" else "Other Outsiders"

        plot_members = data.setdefault("plot_members", {})
        old_record = plot_members.get(cat_name)

        if old_record:
            old_type = old_record.get("member_type")
            old_group = old_record.get("outsider_group") or old_record.get("clan")
            new_group = new_record.get("outsider_group") or new_record.get("clan")

            if old_type == selected_type and old_group == new_group:
                await interaction.edit_original_response(
                    content=f"❌ **{cat_name}** is already listed under **{display_group}** on the plot roster."
                )
                return

        plot_members[cat_name] = new_record
        save_data(data)

    action = "updated on" if old_record else "added to"
    await interaction.edit_original_response(
        content=f"📜 **{cat_name}** has been {action} the plot roster under **{display_group}**."
    )


@plot_group.command(name="remove", description="Remove a cat from the plot-member roster")
@app_commands.describe(cat_name="The cat to remove from the plot roster")
async def plot_remove_command(interaction: discord.Interaction, cat_name: str):
    if not await plot_command_check(interaction):
        return

    await interaction.response.defer()

    async with data_lock:
        plot_members = data.setdefault("plot_members", {})

        if cat_name not in plot_members:
            await interaction.edit_original_response(
                content=f"❌ **{cat_name}** is not currently on the plot roster."
            )
            return

        del plot_members[cat_name]
        save_data(data)

    await interaction.edit_original_response(
        content=f"🧹 **{cat_name}** has been removed from the plot roster."
    )


@plot_group.command(name="roster", description="Show every cat assigned as a plot member")
async def plot_roster_command(interaction: discord.Interaction):
    if not await plot_command_check(interaction):
        return

    await interaction.response.defer()

    async with data_lock:
        cats = copy.deepcopy(data.get("cats", {}))
        plot_members = copy.deepcopy(data.setdefault("plot_members", {}))

    clan_groups = {clan: [] for clan in CLAN_NAMES_ONLY}
    murmur_members = []
    other_outsiders = []
    missing_records = []

    for cat_name, record in plot_members.items():
        cat = cats.get(cat_name)

        if not cat:
            missing_records.append(cat_name)
            continue

        rank = cat.get("rank", "Unknown Rank")
        member_type = record.get("member_type")

        if member_type == "Clan":
            clan = cat.get("clan")
            if clan in clan_groups:
                clan_groups[clan].append((cat_name, rank))
            else:
                missing_records.append(cat_name)
        elif record.get("outsider_group") == "Murmur":
            murmur_members.append((cat_name, rank))
        else:
            other_outsiders.append((cat_name, rank))

    lines = ["# 📜 Echostone Mountain Plot Roster"]
    total_members = 0

    for clan in CLAN_NAMES_ONLY:
        members = sorted(clan_groups[clan], key=lambda item: item[0].casefold())
        total_members += len(members)
        lines.extend(["", f"## {clan}"])
        if members:
            lines.extend(f"• **{name}** — {rank}" for name, rank in members)
        else:
            lines.append("*No plot members assigned.*")

    murmur_members.sort(key=lambda item: item[0].casefold())
    other_outsiders.sort(key=lambda item: item[0].casefold())
    total_members += len(murmur_members) + len(other_outsiders)

    lines.extend(["", "## Outsiders", "### The Murmur"])
    if murmur_members:
        lines.extend(f"• **{name}** — {rank}" for name, rank in murmur_members)
    else:
        lines.append("*No plot members assigned.*")

    lines.extend(["", "### Other"])
    if other_outsiders:
        lines.extend(f"• **{name}** — {rank}" for name, rank in other_outsiders)
    else:
        lines.append("*No plot members assigned.*")

    lines.extend(["", f"**Total Plot Members:** {total_members}"])

    if missing_records:
        lines.extend([
            "",
            "-# These saved plot records no longer match an existing cat: "
            + ", ".join(sorted(missing_records, key=str.casefold))
        ])

    message = "\n".join(lines)
    chunks = []

    while len(message) > 1900:
        split_at = message.rfind("\n", 0, 1900)
        if split_at == -1:
            split_at = 1900
        chunks.append(message[:split_at])
        message = message[split_at:].lstrip()

    chunks.append(message)
    await interaction.edit_original_response(content=chunks[0])

    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@condition_group.command(name="add", description="Add a permanent status condition to a cat")
@app_commands.describe(
    cat_name="The cat receiving the permanent status",
    condition="The exact status to display, such as Blind, Wobbly, or Has ADHD"
)
async def condition_add_command(
    interaction: discord.Interaction,
    cat_name: str,
    condition: str
):
    if not await staff_command_check(interaction):
        return

    clean_condition = condition.strip()

    if not clean_condition:
        await interaction.response.send_message(
            "❌ The permanent status cannot be blank.",
            ephemeral=True
        )
        return

    if len(clean_condition) > 100:
        await interaction.response.send_message(
            "❌ Keep the permanent status to 100 characters or fewer.",
            ephemeral=True
        )
        return

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name not in cats:
            await interaction.response.send_message(
                f"❌ Cat '{cat_name}' was not found.",
                ephemeral=True
            )
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)
        conditions = normalize_permanent_conditions(cat)

        if any(saved.casefold() == clean_condition.casefold() for saved in conditions):
            await interaction.response.send_message(
                f"❌ **{cat_name}** already has **{clean_condition}** listed as a permanent status.",
                ephemeral=True
            )
            return

        conditions.append(clean_condition)
        cat["permanent_conditions"] = conditions
        save_data(data)

    await interaction.response.send_message(
        f"♾️ Added **{clean_condition}** as a permanent status for **{cat_name}**."
    )


@condition_group.command(name="remove", description="Remove one permanent status condition from a cat")
@app_commands.describe(
    cat_name="The cat whose permanent status should be removed",
    condition="The status to remove"
)
async def condition_remove_command(
    interaction: discord.Interaction,
    cat_name: str,
    condition: str
):
    if not await staff_command_check(interaction):
        return

    clean_condition = condition.strip()

    if not clean_condition:
        await interaction.response.send_message(
            "❌ Enter the permanent status you want to remove.",
            ephemeral=True
        )
        return

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name not in cats:
            await interaction.response.send_message(
                f"❌ Cat '{cat_name}' was not found.",
                ephemeral=True
            )
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)
        conditions = normalize_permanent_conditions(cat)
        matching_condition = next(
            (saved for saved in conditions if saved.casefold() == clean_condition.casefold()),
            None
        )

        if matching_condition is None:
            current_text = ", ".join(conditions) if conditions else "None"
            await interaction.response.send_message(
                f"❌ **{cat_name}** does not have **{clean_condition}** listed.\n"
                f"**Current permanent status:** {current_text}",
                ephemeral=True
            )
            return

        cat["permanent_conditions"] = [
            saved for saved in conditions
            if saved.casefold() != matching_condition.casefold()
        ]
        save_data(data)

    await interaction.response.send_message(
        f"🧹 Removed **{matching_condition}** from **{cat_name}**'s permanent status."
    )


@condition_group.command(name="clear", description="Remove every permanent status condition from a cat")
@app_commands.describe(cat_name="The cat whose permanent statuses should all be cleared")
async def condition_clear_command(interaction: discord.Interaction, cat_name: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name not in cats:
            await interaction.response.send_message(
                f"❌ Cat '{cat_name}' was not found.",
                ephemeral=True
            )
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)
        conditions = normalize_permanent_conditions(cat)

        if not conditions:
            await interaction.response.send_message(
                f"❌ **{cat_name}** has no permanent status conditions to clear.",
                ephemeral=True
            )
            return

        removed_text = ", ".join(conditions)
        cat["permanent_conditions"] = []
        save_data(data)

    await interaction.response.send_message(
        f"🧹 Cleared all permanent statuses from **{cat_name}**.\n"
        f"**Removed:** {removed_text}"
    )


@honour_group.command(name="role", description="Give an eligible cat a Clan Honour Role")
@app_commands.describe(
    cat_name="The cat receiving the Honour Role",
    role="Choose Sentinel, Scout, or Mediator"
)
@app_commands.choices(role=HONOUR_ROLE_CHOICES)
async def honour_role_command(
    interaction: discord.Interaction,
    cat_name: str,
    role: app_commands.Choice[str]
):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    role_category = role.value

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name not in cats:
            await interaction.edit_original_response(
                content=f"❌ Cat '{cat_name}' was not found."
            )
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)

        if cat_is_dead(cat):
            await interaction.edit_original_response(
                content="❌ Dead cats cannot receive an Honour Role."
            )
            return

        clan_name = cat.get("clan")
        rank = cat.get("rank")

        if clan_name not in CLAN_NAMES_ONLY:
            await interaction.edit_original_response(
                content="❌ Honour Roles are only available to cats in BlizzardClan, TorrentClan, FossilClan, or SpruceClan."
            )
            return

        if rank not in ["Warrior", "Apprentice"]:
            await interaction.edit_original_response(
                content=f"❌ Only Warriors and Apprentices may receive Honour Roles. **{cat_name}** is currently a **{rank}**."
            )
            return

        if rank == "Apprentice" and role_category == "Sentinel":
            await interaction.edit_original_response(
                content="❌ Apprentices cannot become Sentinels. Apprentices may become Scouts or Mediator Apprentices."
            )
            return

        existing_role = cat.get("honour_role")

        if existing_role:
            await interaction.edit_original_response(
                content=f"❌ **{cat_name}** already holds the Honour Role **{existing_role}**. Use `/honour remove` before assigning a different one."
            )
            return

        current_holders = honour_role_holders(clan_name, role_category)
        role_limit = HONOUR_ROLE_LIMITS[role_category]

        if len(current_holders) >= role_limit:
            holder_text = ", ".join(current_holders) if current_holders else "Unknown"
            await interaction.edit_original_response(
                content=(
                    f"❌ **{clan_name}** already has the maximum of **{role_limit} {role_category}s**.\n"
                    f"**Current holders:** {holder_text}"
                )
            )
            return

        display_role = (
            "Mediator Apprentice"
            if rank == "Apprentice" and role_category == "Mediator"
            else role_category
        )

        cat["honour_role"] = display_role
        add_history(cat, f"Earned the Honour Role {display_role}")
        save_data(data)

    await interaction.edit_original_response(
        content=(
            f"🏅 **{cat_name}** is now **{display_role}** of **{clan_name}**.\n"
            "Updating the Honour Role tracker and announcement..."
        )
    )

    tracker_updated = True
    announcement_sent = True

    try:
        await asyncio.wait_for(
            update_honour_tracker_message(),
            timeout=HONOUR_DISCORD_TIMEOUT_SECONDS
        )
    except Exception as error:
        tracker_updated = False
        print(f"Could not update Honour Role tracker: {type(error).__name__}: {error}")

    try:
        announcement_sent = await asyncio.wait_for(
            announce_new_honour_role(
                cat_name=cat_name,
                clan_name=clan_name,
                display_role=display_role,
                role_category=role_category
            ),
            timeout=HONOUR_DISCORD_TIMEOUT_SECONDS
        )
    except Exception as error:
        announcement_sent = False
        print(f"Could not post Honour Role announcement: {type(error).__name__}: {error}")

    response_lines = [
        f"🏅 **{cat_name}** is now **{display_role}** of **{clan_name}**."
    ]

    if tracker_updated:
        response_lines.append("✅ The Honour Role tracker was updated.")
    else:
        response_lines.append("⚠️ The role was saved, but the tracker update timed out or failed. Check the Railway logs and channel permissions.")

    if announcement_sent:
        response_lines.append("✅ The Honour Role announcement was posted.")
    else:
        response_lines.append("⚠️ The role was saved, but the announcement timed out or failed. Check the Railway logs and channel permissions.")

    await interaction.edit_original_response(content="\n".join(response_lines))


@honour_group.command(name="remove", description="Remove a cat's current Honour Role")
@app_commands.describe(cat_name="The cat whose Honour Role should be removed")
async def honour_remove_command(interaction: discord.Interaction, cat_name: str):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name not in cats:
            await interaction.followup.send(
                f"❌ Cat '{cat_name}' was not found.",
                ephemeral=True
            )
            return

        cat = cats[cat_name]
        old_role = cat.get("honour_role")

        if not old_role:
            await interaction.followup.send(
                f"❌ **{cat_name}** does not currently hold an Honour Role.",
                ephemeral=True
            )
            return

        cat["honour_role"] = None
        add_history(cat, f"Honour Role {old_role} removed")
        save_data(data)

    try:
        await asyncio.wait_for(
            update_honour_tracker_message(),
            timeout=HONOUR_DISCORD_TIMEOUT_SECONDS
        )
        tracker_line = "✅ The Honour Role tracker was updated."
    except Exception as error:
        print(f"Could not update Honour Role tracker: {error}")
        tracker_line = "⚠️ The role was removed, but the tracker could not be updated."

    await interaction.followup.send(
        f"🧹 Removed **{old_role}** from **{cat_name}**.\n{tracker_line}",
        ephemeral=True
    )


@honour_group.command(name="tracker", description="Refresh the Honour Role availability tracker")
async def honour_tracker_command(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    try:
        tracker_message = await asyncio.wait_for(
            update_honour_tracker_message(),
            timeout=HONOUR_DISCORD_TIMEOUT_SECONDS
        )
    except Exception as error:
        await interaction.followup.send(
            f"❌ The Honour Role tracker could not be updated: {error}",
            ephemeral=True
        )
        return

    await interaction.followup.send(
        f"✅ Honour Role tracker updated: {tracker_message.jump_url}",
        ephemeral=True
    )


@hiatus_group.command(name="add", description="Add a hiatus using a raw Discord user ID")
@app_commands.describe(
    user_id="Raw Discord user ID from /raw-format",
    days="How many days the hiatus lasts"
)
async def hiatus_add(interaction: discord.Interaction, user_id: str, days: int):
    if not await staff_command_check(interaction):
        return

    if days < 1:
        await interaction.response.send_message("Hiatus must be at least 1 day.", ephemeral=True)
        return

    end_date = datetime.now(TZ) + timedelta(days=days)
    guild_id = interaction.guild.id if interaction.guild else None

    async with data_lock:
        data.setdefault("hiatuses", {})
        data["hiatuses"][user_id] = {
            "days": days,
            "start_date": datetime.now(TZ).date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "guild_id": guild_id
        }

        save_data(data)

    role_success, role_message = await update_hiatus_roles(interaction.guild, user_id, on_hiatus=True)

    response = (
        f"🌙 <@{user_id}> has been placed on hiatus for **{days} day(s)**.\n"
        f"They are set to return on **{end_date.strftime('%B %d, %Y')}**."
    )

    if role_success:
        response += f"\n✅ {role_message}"
    else:
        response += f"\n⚠️ Hiatus was saved, but roles were not changed: {role_message}"

    await interaction.response.send_message(response)


@hiatus_group.command(name="end", description="Manually end a hiatus using a raw Discord user ID")
@app_commands.describe(user_id="Raw Discord user ID from /raw-format")
async def hiatus_end(interaction: discord.Interaction, user_id: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        data.setdefault("hiatuses", {})

        if user_id not in data["hiatuses"]:
            await interaction.response.send_message(
                f"<@{user_id}> is not currently listed as on hiatus.",
                ephemeral=True
            )
            return

        del data["hiatuses"][user_id]
        save_data(data)

    role_success, role_message = await update_hiatus_roles(interaction.guild, user_id, on_hiatus=False)

    response = f"✅ <@{user_id}> has been manually removed from hiatus."

    if role_success:
        response += f"\n✅ {role_message}"
    else:
        response += f"\n⚠️ Hiatus was ended, but roles were not changed: {role_message}"

    await interaction.response.send_message(response)

@hiatus_group.command(name="all", description="View everyone currently on hiatus")
async def hiatus_all(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    today = datetime.now(TZ).date()

    async with data_lock:
        data.setdefault("hiatuses", {})
        hiatuses = data["hiatuses"]

        if not hiatuses:
            await interaction.response.send_message(
                "✅ No one is currently on hiatus.",
                ephemeral=True
            )
            return

        lines = ["🌙 **Current Hiatus List**", ""]

        for user_id, info in hiatuses.items():
            end_date = datetime.fromisoformat(info["end_date"]).date()
            days_left = max(0, (end_date - today).days)

            if days_left == 0:
                days_text = "ends today"
            elif days_left == 1:
                days_text = "1 day left"
            else:
                days_text = f"{days_left} days left"

            lines.append(
                f"• <@{user_id}> — **{days_text}** "
                f"(returns **{end_date.strftime('%B %d, %Y')}**)"
            )

    await interaction.response.send_message("\n".join(lines)[:1900])

@hiatus_group.command(name="edit", description="Edit how long a current hiatus lasts")
@app_commands.describe(
    user_id="Raw Discord user ID from /raw-format",
    days="New total number of days from today"
)
async def hiatus_edit(interaction: discord.Interaction, user_id: str, days: int):
    if not await staff_command_check(interaction):
        return

    if days < 1:
        await interaction.response.send_message("Hiatus must be at least 1 day.", ephemeral=True)
        return

    async with data_lock:
        data.setdefault("hiatuses", {})

        if user_id not in data["hiatuses"]:
            await interaction.response.send_message(
                f"<@{user_id}> is not currently listed as on hiatus.",
                ephemeral=True
            )
            return

        end_date = datetime.now(TZ) + timedelta(days=days)

        data["hiatuses"][user_id]["days"] = days
        data["hiatuses"][user_id]["end_date"] = end_date.date().isoformat()

        save_data(data)

    await interaction.response.send_message(
        f"✏️ <@{user_id}>'s hiatus has been updated to **{days} day(s)** from today.\n"
        f"They are now set to return on **{end_date.strftime('%B %d, %Y')}**."
    )


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
@app_commands.choices(clan=CLAN_CHOICES, rank=RANK_CHOICES)
@app_commands.autocomplete(faction=outsider_group_autocomplete)
async def cat_add(
    interaction: discord.Interaction,
    name: str,
    age: int,
    clan: app_commands.Choice[str],
    rank: app_commands.Choice[str],
    faction: str = None
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name in data["cats"]:
            await interaction.response.send_message("That cat already exists.", ephemeral=True)
            return

        faction_value = resolve_outsider_group(faction) if faction else None

        if faction and faction_value is None:
            await interaction.response.send_message(
                "❌ That Outsider group does not exist. Add it first with `/outsidergroup add`.",
                ephemeral=True
            )
            return

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

    honour_role_changed = False
    honour_role_note = None

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

        current_honour_role = cat.get("honour_role")

        if current_honour_role:
            if rank.value == "Warrior" and current_honour_role == "Mediator Apprentice":
                cat["honour_role"] = "Mediator"
                honour_role_changed = True
                honour_role_note = "Their Mediator Apprentice title was updated to Mediator."
                add_history(cat, "Mediator Apprentice title advanced to Mediator")

            elif rank.value == "Apprentice" and current_honour_role == "Mediator":
                cat["honour_role"] = "Mediator Apprentice"
                honour_role_changed = True
                honour_role_note = "Their Mediator title was updated to Mediator Apprentice."
                add_history(cat, "Mediator title changed to Mediator Apprentice")

            elif rank.value not in ["Warrior", "Apprentice"] or (
                rank.value == "Apprentice" and current_honour_role == "Sentinel"
            ):
                cat["honour_role"] = None
                honour_role_changed = True
                honour_role_note = f"Their Honour Role **{current_honour_role}** was removed because the new rank is not eligible."
                add_history(cat, f"Honour Role {current_honour_role} removed after rank change")

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

    response = f"⚔ **{name}** is now **{rank.value}**."

    if honour_role_note:
        response += f"\n🏅 {honour_role_note}"

    await interaction.response.send_message(response)

    if honour_role_changed:
        try:
            await update_honour_tracker_message()
        except Exception as error:
            print(f"Could not update Honour Role tracker after rank change: {error}")

    await refresh_allegiances_safely("cat rank change")


@bot.tree.command(
    name="changeclan",
    description="Change a cat's Clan or move them to/from Outsider."
)
@app_commands.describe(
    cat_name="Name of the cat",
    new_clan="The new Clan or Outsider",
    new_rank="Optional new rank. If left blank, the bot will keep or safely adjust the rank."
)
@app_commands.choices(
    new_clan=CLAN_CHOICES,
    new_rank=RANK_CHOICES
)
async def changeclan(
    interaction: discord.Interaction,
    cat_name: str,
    new_clan: app_commands.Choice[str],
    new_rank: app_commands.Choice[str] = None
):
    if not await staff_command_check(interaction):
        return

    honour_role_removed = None

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name not in cats:
            await interaction.response.send_message(
                f"❌ Cat '{cat_name}' was not found.",
                ephemeral=True
            )
            return

        cat = cats[cat_name]
        prepare_cat_record(cat_name, cat)

        old_clan = cat.get("clan", "Unknown Clan")
        old_rank = cat.get("rank", "Unknown Rank")
        selected_clan = new_clan.value

        selected_rank = new_rank.value if new_rank else old_rank
        rank_note = None

        # If no rank is provided, keep the current rank when possible.
        # If the current rank does not work in the new Clan type, choose a safe default.
        if new_rank is None:
            if selected_clan == "Outsider" and selected_rank in CLAN_RANKS:
                selected_rank = "Loner"
                rank_note = "Rank was automatically changed to Loner because Outsiders cannot use Clan ranks."

            elif selected_clan != "Outsider" and selected_rank in OUTSIDER_RANKS:
                selected_rank = "Warrior"
                rank_note = "Rank was automatically changed to Warrior because Clan cats cannot use Outsider ranks."

        validation_error = validate_cat_rank(selected_clan, selected_rank, cat.get("faction"))

        # Moving into a Clan clears faction first, then validates again.
        if validation_error and selected_clan != "Outsider":
            cat["faction"] = None
            validation_error = validate_cat_rank(selected_clan, selected_rank, cat.get("faction"))

        if validation_error:
            await interaction.response.send_message(validation_error, ephemeral=True)
            return

        old_mentor = cat.get("mentor")

        # If the cat changes Clan or stops being an apprentice, clear mentor links cleanly.
        if old_mentor and (old_clan != selected_clan or selected_rank not in ["Apprentice", "Medicine Cat Apprentice"]):
            if old_mentor in cats:
                mentor_cat = cats[old_mentor]

                if cat_name in mentor_cat.get("apprentices", []):
                    mentor_cat["apprentices"].remove(cat_name)

                add_history(mentor_cat, f"No longer mentoring {cat_name} after Clan/rank change")

            cat["mentor"] = None

        # If the cat is no longer in a Clan, clear Clan-specific apprentice lists.
        if selected_clan == "Outsider":
            cat["apprentices"] = []

        # Clan cats cannot keep outsider factions.
        if selected_clan != "Outsider":
            cat["faction"] = None

        if old_clan != selected_clan and cat.get("honour_role"):
            honour_role_removed = cat.get("honour_role")
            cat["honour_role"] = None
            add_history(cat, f"Honour Role {honour_role_removed} removed after leaving {old_clan}")

        cat["clan"] = selected_clan
        cat["rank"] = selected_rank

        add_history(cat, f"Clan changed from {old_clan} to {selected_clan}")

        if old_rank != selected_rank:
            add_history(cat, f"Rank changed to {selected_rank}")

        save_data(data)

    response_lines = [
        f"⛺ **{cat_name}** has been moved.",
        f"**Old Clan:** {old_clan}",
        f"**New Clan:** {selected_clan}",
        f"**Rank:** {old_rank} → {selected_rank}"
    ]

    if rank_note:
        response_lines.append(f"-# {rank_note}")

    if honour_role_removed:
        response_lines.append(
            f"🏅 Their Honour Role **{honour_role_removed}** was removed because Honour Roles belong to the Clan where they were earned."
        )

    await interaction.response.send_message("\n".join(response_lines))

    if honour_role_removed:
        try:
            await update_honour_tracker_message()
        except Exception as error:
            print(f"Could not update Honour Role tracker after Clan change: {error}")

    await refresh_allegiances_safely("Clan change")

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

        plot_members = data.setdefault("plot_members", {})
        if old_name in plot_members:
            plot_members[new_name] = plot_members.pop(old_name)

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
    await refresh_allegiances_safely("cat rename")


@cat_group.command(name="markdead", description="Mark a cat as dead")
@app_commands.describe(
    name="Cat name",
    afterlife="Afterlife destination",
    cause="Optional cause of death"
)
@app_commands.choices(afterlife=AFTERLIFE_CHOICES)
async def cat_markdead(
    interaction: discord.Interaction,
    name: str,
    afterlife: app_commands.Choice[str],
    cause: str = None
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = data["cats"][name]
        had_honour_role = bool(cat.get("honour_role"))
        cat["status"] = "Dead"
        cat["afterlife"] = afterlife.value
        cat["death_moon"] = data["moon"]
        cat["cause_of_death"] = cause

        if cause:
            add_history(cat, f"Died from {cause} and went to {afterlife.value}")
        else:
            add_history(cat, f"Died and went to {afterlife.value}")

        save_data(data)

    await interaction.response.send_message(
        f"💀 **{name}** has been sent to **{afterlife.value}**."
    )

    channel = bot.get_channel(DEATH_ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        death_message = (
            f"💀 **Death Announcement**\n"
            f"**{name}** has died and now walks in **{afterlife.value}**."
        )

        if cause:
            death_message += f"\n**Cause of Death:** {cause}"

        await channel.send(death_message)

    if had_honour_role:
        try:
            await update_honour_tracker_message()
        except Exception as error:
            print(f"Could not update Honour Role tracker after death: {error}")

    await refresh_allegiances_safely("cat death")


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

    had_honour_role = False

    async with data_lock:
        if name not in data["cats"]:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        had_honour_role = bool(data["cats"][name].get("honour_role"))

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
        data.setdefault("plot_members", {}).pop(name, None)
        save_data(data)

    await interaction.response.send_message(
        f"🗑 Deleted **{name}** permanently and removed related records."
    )

    if had_honour_role:
        try:
            await update_honour_tracker_message()
        except Exception as error:
            print(f"Could not update Honour Role tracker after deleting cat: {error}")

    await refresh_allegiances_safely("cat deletion")


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

@cat_group.command(name="clearhistorymoon", description="Delete cat history entries from a specific moon")
@app_commands.describe(
    moon="The moon number to delete history entries from",
    cat_name="Optional. Leave blank to clear this moon from all cats."
)
async def cat_clear_history_moon(
    interaction: discord.Interaction,
    moon: int,
    cat_name: str = None
):
    if not await staff_command_check(interaction):
        return

    if moon < 0:
        await interaction.response.send_message(
            "Moon number must be 0 or higher.",
            ephemeral=True
        )
        return

    prefix = f"Moon {moon}:"

    async with data_lock:
        cats = data.get("cats", {})

        if cat_name:
            if cat_name not in cats:
                await interaction.response.send_message(
                    f"Cat not found: **{cat_name}**",
                    ephemeral=True
                )
                return

            cat = cats[cat_name]
            old_count = len(cat.get("history", []))

            cat["history"] = [
                entry for entry in cat.get("history", [])
                if not entry.startswith(prefix)
            ]

            removed_count = old_count - len(cat["history"])
            save_data(data)

            await interaction.response.send_message(
                f"🧹 Removed **{removed_count}** history entr{'y' if removed_count == 1 else 'ies'} from **{cat_name}** for **Moon {moon}**.",
                ephemeral=True
            )
            return

        total_removed = 0
        affected_cats = 0

        for name, cat in cats.items():
            old_count = len(cat.get("history", []))

            cat["history"] = [
                entry for entry in cat.get("history", [])
                if not entry.startswith(prefix)
            ]

            removed_count = old_count - len(cat["history"])

            if removed_count > 0:
                total_removed += removed_count
                affected_cats += 1

        save_data(data)

    await interaction.response.send_message(
        f"🧹 Removed **{total_removed}** history entr{'y' if total_removed == 1 else 'ies'} from **Moon {moon}** across **{affected_cats}** cat{'s' if affected_cats != 1 else ''}.",
        ephemeral=True
    )


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

        original_severity = severity
        role_quest_reduction_applied = False
        try:
            saved_reductions = int(cat.get("role_quest_injury_reduction_charges", 0) or 0)
        except (TypeError, ValueError):
            saved_reductions = 0

        if saved_reductions > 0:
            severity = max(1, severity - 1)
            cat["role_quest_injury_reduction_charges"] = saved_reductions - 1
            role_quest_reduction_applied = severity < original_severity

        cat["injury"] = {
            "type": injury,
            "severity": severity,
            "moon": injury_moon,
            "last_recovery_update": datetime.now(TZ).isoformat()
        }

        add_history(cat, f"Injured/ill: {injury} | Severity {severity}/10 | Moon {injury_moon}")
        save_data(data)

    reduction_note = ""
    if role_quest_reduction_applied:
        reduction_note = f"\n🌟 Role Quest reward applied: severity reduced from **{original_severity}** to **{severity}**."

    await interaction.response.send_message(
        f"🩹 **{name}** now has **{injury}**.\n"
        f"Severity: **{severity}/10, {severity_label(severity)}**\n"
        f"Injury Moon: **Moon {injury_moon}**"
        f"{reduction_note}"
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

                add_unique_name(old_mentor_cat, "past_apprentices", apprentice)
                add_unique_name(app_cat, "previous_mentors", clean_old_mentor)

        app_cat["mentor"] = mentor

        remove_from_list(app_cat, "previous_mentors", mentor)
        remove_from_list(app_cat, "previous_mentors", f"{mentor} (PAST)")
        remove_from_list(app_cat, "previous_mentors", f"{mentor} (Past)")

        mentor_cat.setdefault("apprentices", [])
        if not list_has_name(mentor_cat["apprentices"], apprentice):
            mentor_cat["apprentices"].append(apprentice)

        remove_from_list(mentor_cat, "past_apprentices", apprentice)
        remove_from_list(mentor_cat, "past_apprentices", f"{apprentice} (PAST)")
        remove_from_list(mentor_cat, "past_apprentices", f"{apprentice} (Past)")

        add_history(app_cat, f"Assigned {mentor} as mentor")
        add_history(mentor_cat, f"Became mentor to {apprentice}")

        save_data(data)

    await interaction.response.send_message(f"🐾 **{mentor}** is now mentoring **{apprentice}**.")
    await refresh_allegiances_safely("mentor assignment")


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

        prepare_cat_record(name, cat)
        prepare_cat_record(mentor, mentor_cat)

        current_mentor = cat.get("mentor")
        if current_mentor and name_matches(current_mentor, mentor):
            await interaction.response.send_message(
                f"🐾 **{mentor}** is already **{name}**'s current mentor.",
                ephemeral=True
            )
            return

        added_previous_mentor = add_unique_name(cat, "previous_mentors", mentor)
        added_past_apprentice = add_unique_name(mentor_cat, "past_apprentices", name)

        if not added_previous_mentor and not added_past_apprentice:
            await interaction.response.send_message(
                f"🐾 **{mentor}** is already listed as **{name}**'s previous mentor.",
                ephemeral=True
            )
            return

        cat["previous_mentors"] = dedupe_name_list(cat.get("previous_mentors", []))
        mentor_cat["past_apprentices"] = dedupe_name_list(mentor_cat.get("past_apprentices", []))

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
        remove_from_list(app_cat, "previous_mentors", f"{mentor} (Past)")

        # Remove apprentice from mentor's lists
        remove_from_list(mentor_cat, "apprentices", apprentice)
        remove_from_list(mentor_cat, "past_apprentices", apprentice)
        remove_from_list(mentor_cat, "past_apprentices", f"{apprentice} (PAST)")
        remove_from_list(mentor_cat, "past_apprentices", f"{apprentice} (Past)")

        # Remove old mentor history from both cats
        remove_mentor_history_between(app_cat, mentor)
        remove_mentor_history_between(mentor_cat, apprentice)

        save_data(data)

    await interaction.response.send_message(
        f"🧹 Removed mentor records between **{apprentice}** and **{mentor}**."
    )
    await refresh_allegiances_safely("mentor removal")


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
    """Post the normal weekly weather on Sundays at 10 AM Toronto time."""
    now = datetime.now(TZ)

    if now.weekday() != 6 or now.hour != 10:
        return

    this_week = severe_week_key(now)

    async with data_lock:
        if data.get("last_weather_week") == this_week:
            return

        details = generate_weekly_weather_details()
        details["week"] = this_week
        data["last_weather_week"] = this_week
        data["current_weather"] = details
        save_data(data)

    channel = bot.get_channel(WEATHER_CHANNEL_ID)
    if channel:
        await channel.send(
            content=f"<@&{WEATHER_REPORT_ROLE_ID}>",
            embed=discord.Embed(
                description=details["report"],
                color=discord.Color.blue()
            )
        )


severeweather_group = app_commands.Group(
    name="severeweather",
    description="Severe weather and environmental event commands"
)


@severeweather_group.command(
    name="trigger",
    description="Staff only. Trigger a custom severe weather event for one or more groups."
)
@app_commands.describe(
    event_name="Event name, such as Severe Thunderstorms or Fire at Whispering Branches",
    primary_targets="Comma-separated Clan or Outsider group names. You can also type All Clans, All Outsiders, or Everyone.",
    primary_modifier="Primary roll modifier, such as -2 or -6",
    location="Primary affected location. Use Entire Territory for a territory-wide event.",
    primary_effect_type="Whether the primary modifier affects hunting, fishing, both, or neither",
    secondary_targets="Optional comma-separated groups on the outer edge of the event",
    secondary_modifier="Secondary modifier. Default is -1.",
    secondary_location="Location affected for secondary targets",
    secondary_effect_type="Whether the secondary modifier affects hunting, fishing, both, or neither",
    duration_days="How many days the effects last. Default is 7.",
    override_month_limit="Allow a primary target that already had a disaster this month",
    description="Optional plot description. The bot will never invent injuries or destroyed supplies."
)
@app_commands.choices(
    primary_effect_type=SEVERE_EFFECT_TYPE_CHOICES,
    secondary_effect_type=SEVERE_EFFECT_TYPE_CHOICES
)
async def severeweather_trigger_command(
    interaction: discord.Interaction,
    event_name: str,
    primary_targets: str,
    primary_modifier: int,
    location: str = "Entire Territory",
    primary_effect_type: app_commands.Choice[str] = None,
    secondary_targets: str = None,
    secondary_modifier: int = -1,
    secondary_location: str = "Entire Territory",
    secondary_effect_type: app_commands.Choice[str] = None,
    duration_days: int = SEVERE_WEATHER_DURATION_DAYS,
    override_month_limit: bool = False,
    description: str = None
):
    if not await staff_command_check(interaction):
        return

    if not event_name.strip():
        await interaction.response.send_message(
            "❌ Event name cannot be blank.",
            ephemeral=True
        )
        return

    if primary_modifier < -10 or primary_modifier > 0:
        await interaction.response.send_message(
            "❌ Primary modifier must be between **-10 and 0**.",
            ephemeral=True
        )
        return

    if secondary_modifier < -10 or secondary_modifier > 0:
        await interaction.response.send_message(
            "❌ Secondary modifier must be between **-10 and 0**.",
            ephemeral=True
        )
        return

    if duration_days < 1 or duration_days > 30:
        await interaction.response.send_message(
            "❌ Duration must be between **1 and 30 days**.",
            ephemeral=True
        )
        return

    try:
        primary_entities = parse_severe_targets(
            primary_targets,
            include_empty_outsider=True
        )
        secondary_entities = parse_severe_targets(
            secondary_targets,
            include_empty_outsider=True
        ) if secondary_targets else []
    except ValueError as error:
        await interaction.response.send_message(
            f"❌ {error}",
            ephemeral=True
        )
        return

    if not primary_entities:
        await interaction.response.send_message(
            "❌ Choose at least one primary target.",
            ephemeral=True
        )
        return

    primary_keys = {entity["key"] for entity in primary_entities}
    secondary_entities = [
        entity for entity in secondary_entities
        if entity["key"] not in primary_keys
    ]

    primary_type = (
        primary_effect_type.value
        if primary_effect_type
        else "hunting"
    )
    secondary_type = (
        secondary_effect_type.value
        if secondary_effect_type
        else "hunting"
    )

    await interaction.response.defer(ephemeral=True)
    now = datetime.now(TZ)
    week = severe_week_key(now)

    async with data_lock:
        cleanup_expired_severe_weather(now)

        if not override_month_limit:
            blocked = [
                entity["label"]
                for entity in primary_entities
                if severe_has_monthly_hit(entity["key"], now)
            ]

            if blocked:
                await interaction.edit_original_response(
                    content=(
                        "❌ These primary targets already had a disaster this calendar month: "
                        f"**{', '.join(blocked)}**.\n"
                        "Use `override_month_limit: True` only when plot requires another event."
                    )
                )
                return

        event_record = build_manual_severe_event(
            event_name=event_name,
            description=description,
            primary_entities=primary_entities,
            primary_location=location,
            primary_modifier=primary_modifier,
            primary_effect_type=primary_type,
            secondary_entities=secondary_entities,
            secondary_location=secondary_location,
            secondary_modifier=secondary_modifier,
            secondary_effect_type=secondary_type,
            duration_days=duration_days,
            now=now
        )

        data.setdefault("active_severe_weather", []).append(event_record)

        for entity in primary_entities:
            record_severe_primary_hit(
                entity,
                event_record["event_key"],
                now
            )

        data["severe_weather_quiet_streak"] = 0
        data["last_severe_weather_week"] = week
        data.setdefault("severe_weather_week_results", {})[week] = {
            "had_primary": True,
            "manual": True,
            "forced": False,
            "checked_at": now.isoformat()
        }
        prune_severe_week_results()
        save_data(data)

    posted = await post_severe_weather_events([event_record], forced=False)

    primary_text = ", ".join(entity["label"] for entity in primary_entities)
    secondary_text = ", ".join(entity["label"] for entity in secondary_entities)

    response = (
        f"⚠️ Custom severe weather event **{event_record['name']}** created.\n"
        f"**Event ID:** `{event_record['id']}`\n"
        f"**Primary:** {primary_text}"
    )

    if secondary_text:
        response += f"\n**Secondary:** {secondary_text}"

    if override_month_limit:
        response += "\n⚠️ Monthly disaster limit was overridden for this plot event."

    response += (
        "\n✅ The automatic severe-weather roll for this ISO week is now considered handled."
        if posted
        else "\n⚠️ Event was saved, but the weather announcement could not be posted."
    )

    await interaction.edit_original_response(content=response)


@severeweather_group.command(
    name="roll",
    description="Staff only. Run this week's automatic severe-weather roll early."
)
async def severeweather_roll_command(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    result = await run_automatic_severe_weather(mark_week=True)

    if result.get("already_handled"):
        await interaction.edit_original_response(
            content=(
                "🌦️ This week's severe-weather check is already handled. "
                "A manual event or the Monday automatic roll has already been recorded."
            )
        )
        return

    events = result.get("events", [])

    if events:
        posted = await post_severe_weather_events(
            events,
            forced=result.get("forced", False)
        )
        await interaction.edit_original_response(
            content=(
                f"⚠️ Severe-weather roll completed with **{len(events)} event(s)**."
                + (" The alert was posted." if posted else " The events were saved, but the alert could not be posted.")
            )
        )
    else:
        aurora_triggered = await trigger_northern_lights(manual=False)
        message = (
            "🌤️ Severe-weather roll completed. No primary disasters triggered this week."
        )
        if aurora_triggered:
            message += "\n🌌 The Northern Lights triggered instead as a separate celestial phenomenon."
        await interaction.edit_original_response(content=message)


@severeweather_group.command(
    name="active",
    description="View currently active severe-weather effects and the Northern Lights."
)
async def severeweather_active_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    now = datetime.now(TZ)

    async with data_lock:
        changed = cleanup_expired_severe_weather(now)
        if changed:
            save_data(data)

        active = copy.deepcopy(data.get("active_severe_weather", []))
        aurora_until = data.get("aurora_active_until")

    if not active and not aurora_until:
        await interaction.edit_original_response(
            content="🌤️ There are no active severe-weather effects right now."
        )
        return

    lines = ["⚠️ **Active Severe Weather**", ""]

    for event in active:
        lines.append(
            f"`{event.get('id', '?')}` {event.get('emoji', '⚠️')} **{event.get('name', 'Severe Weather')}**"
        )

        primary = event_primary_targets(event)
        secondary = event_secondary_targets(event)

        if primary:
            lines.append(f"Primary: {', '.join(primary)}")
        if secondary:
            lines.append(f"Outer edge: {', '.join(secondary)}")

        try:
            expires = datetime.fromisoformat(event.get("expires_at"))
            lines.append(
                f"Expires: {discord_expiry_timestamp(expires)}"
            )
        except Exception:
            pass

        for effect in event.get("effects", []):
            modifier_text = format_severe_modifier(
                effect.get("modifier", 0),
                effect.get("type", "hunting")
            )
            lines.append(
                f"• {effect.get('target')} / {effect.get('location', 'Entire Territory')}: {modifier_text}"
            )

        lines.append("")

    if aurora_until:
        try:
            aurora_expires = datetime.fromisoformat(aurora_until)
            if aurora_expires > now:
                lines.extend([
                    "🌌 **Northern Lights / Spirit Veil Active**",
                    f"Until {discord_expiry_timestamp(aurora_expires)}",
                    "No prey modifier. StarClan and Dark Forest spirits may walk the living lands in spirit form.",
                    ""
                ])
        except Exception:
            pass

    message = "\n".join(lines).strip()
    chunks = []

    while len(message) > 1900:
        split_at = message.rfind("\n", 0, 1900)
        if split_at == -1:
            split_at = 1900
        chunks.append(message[:split_at])
        message = message[split_at:].lstrip()

    chunks.append(message)

    await interaction.edit_original_response(content=chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=True)


@severeweather_group.command(
    name="modifier",
    description="Check the active severe-weather modifier for a territory and roll type."
)
@app_commands.describe(
    target="Clan or Outsider group name",
    location="Exact hunting location, such as Trout Run or Whispering Branches",
    roll_type="Hunting or fishing"
)
@app_commands.choices(roll_type=SEVERE_ROLL_TYPE_CHOICES)
async def severeweather_modifier_command(
    interaction: discord.Interaction,
    target: str,
    location: str,
    roll_type: app_commands.Choice[str]
):
    target_entity = resolve_severe_target_name(target)

    if not target_entity:
        await interaction.response.send_message(
            "❌ Target not found. Use a Clan name or saved Outsider group name.",
            ephemeral=True
        )
        return

    modifier, matches = severe_weather_modifier_for(
        target_entity["label"],
        location,
        roll_type.value
    )

    if not matches:
        await interaction.response.send_message(
            f"🌤️ No active severe-weather **{roll_type.value}** modifier applies to "
            f"**{target_entity['label']}** at **{location}**.",
            ephemeral=True
        )
        return

    match_lines = [
        f"• {match['event']} ({match['location']}): {match['modifier']:+d}"
        for match in matches
    ]

    await interaction.response.send_message(
        f"⚠️ **Severe Weather Modifier**\n"
        f"**Target:** {target_entity['label']}\n"
        f"**Location:** {location}\n"
        f"**Roll Type:** {roll_type.value.title()}\n"
        f"**Modifier to use:** {modifier:+d}\n\n"
        + "\n".join(match_lines)
        + "\n\nSevere-weather penalties do not stack with each other. Use the strongest applicable severe penalty.",
        ephemeral=True
    )



@severeweather_group.command(
    name="effect",
    description="Staff only. Add another custom location/modifier to an active severe-weather event."
)
@app_commands.describe(
    event_id="Event ID shown by /severeweather active",
    target="Clan or Outsider group name",
    location="Affected location, such as Trout Run or Whispering Branches",
    modifier="Roll modifier, from -10 to 0",
    effect_type="Hunting, fishing, both, or no roll modifier",
    primary="True makes this a primary disaster hit; False makes it a secondary/spillover effect",
    override_month_limit="Allow a new primary target that already had a disaster this month",
    note="Optional explanation for this location-specific effect"
)
@app_commands.choices(effect_type=SEVERE_EFFECT_TYPE_CHOICES)
async def severeweather_effect_command(
    interaction: discord.Interaction,
    event_id: str,
    target: str,
    location: str,
    modifier: int,
    effect_type: app_commands.Choice[str],
    primary: bool = False,
    override_month_limit: bool = False,
    note: str = None
):
    if not await staff_command_check(interaction):
        return

    if modifier < -10 or modifier > 0:
        await interaction.response.send_message(
            "❌ Modifier must be between **-10 and 0**.",
            ephemeral=True
        )
        return

    entity = resolve_severe_target_name(target)
    if not entity:
        await interaction.response.send_message(
            "❌ Target not found. Use a Clan name or saved Outsider group name.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    now = datetime.now(TZ)
    week = severe_week_key(now)

    async with data_lock:
        cleanup_expired_severe_weather(now)
        active = data.setdefault("active_severe_weather", [])
        event_record = next(
            (
                event for event in active
                if str(event.get("id", "")).casefold() == event_id.strip().casefold()
            ),
            None
        )

        if event_record is None:
            await interaction.edit_original_response(
                content="❌ Active severe-weather event not found."
            )
            return

        already_primary = any(
            effect.get("entity_key") == entity["key"] and effect.get("primary")
            for effect in event_record.get("effects", [])
        )

        if primary and not already_primary:
            if severe_has_monthly_hit(entity["key"], now) and not override_month_limit:
                await interaction.edit_original_response(
                    content=(
                        f"❌ **{entity['label']}** already had a primary disaster this month. "
                        "Use `override_month_limit: True` only if plot requires another."
                    )
                )
                return

            record_severe_primary_hit(
                entity,
                event_record.get("event_key", severe_event_key_from_name(event_record.get("name"))),
                now
            )

        event_record.setdefault("effects", []).append({
            "entity_key": entity["key"],
            "target": entity["label"],
            "kind": entity["kind"],
            "primary": bool(primary),
            "location": location.strip() or "Entire Territory",
            "modifier": modifier,
            "type": effect_type.value,
            "note": note.strip() if note else "Staff-set location-specific severe weather effect."
        })

        if primary:
            data["severe_weather_quiet_streak"] = 0
            data["last_severe_weather_week"] = week
            data.setdefault("severe_weather_week_results", {})[week] = {
                "had_primary": True,
                "manual": True,
                "forced": False,
                "checked_at": now.isoformat()
            }
            prune_severe_week_results()

        save_data(data)

    channel = bot.get_channel(WEATHER_CHANNEL_ID)
    if channel:
        update_message = (
            f"<@&{WEATHER_REPORT_ROLE_ID}>\n"
            f"⚠️ **SEVERE WEATHER UPDATE - {event_record.get('name', 'Weather Event')}**\n\n"
            f"**{entity['label']} - {'DIRECT HIT' if primary else 'OUTER EDGE'}**\n"
            f"• **{location.strip() or 'Entire Territory'}:** "
            f"{format_severe_modifier(modifier, effect_type.value)}\n"
            f"{note.strip() if note else 'Staff-set location-specific effect.'}\n\n"
            "No automatic injuries, deaths, destroyed herbs, or destroyed dens are created by this update."
        )
        await send_long_message(channel, update_message)

    await interaction.edit_original_response(
        content=(
            f"✅ Added the new effect to `{event_record.get('id')}`.\n"
            f"**{entity['label']} / {location.strip() or 'Entire Territory'}:** "
            f"{format_severe_modifier(modifier, effect_type.value)}"
        )
    )


@severeweather_group.command(
    name="end",
    description="Staff only. End one active severe-weather event early."
)
@app_commands.describe(event_id="Event ID shown by /severeweather active")
async def severeweather_end_command(
    interaction: discord.Interaction,
    event_id: str
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        active = data.setdefault("active_severe_weather", [])
        matching = next(
            (
                event for event in active
                if str(event.get("id", "")).casefold() == event_id.strip().casefold()
            ),
            None
        )

        if matching is None:
            await interaction.response.send_message(
                "❌ Active severe-weather event not found.",
                ephemeral=True
            )
            return

        data["active_severe_weather"] = [
            event for event in active
            if event is not matching
        ]
        save_data(data)

    await interaction.response.send_message(
        f"✅ Ended **{matching.get('name', 'Severe Weather')}** early.\n"
        "Its monthly disaster history remains recorded so the automatic system will not immediately replace it.",
        ephemeral=True
    )


@severeweather_group.command(
    name="aurora",
    description="Staff only. Trigger the Northern Lights and open the Spirit Veil."
)
async def severeweather_aurora_command(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    triggered = await trigger_northern_lights(manual=True)

    if triggered:
        await interaction.edit_original_response(
            content=(
                "🌌 Northern Lights triggered. The Spirit Veil is open for 7 days, "
                "with no hunting or fishing penalty."
            )
        )
    else:
        await interaction.edit_original_response(
            content="⚠️ The Northern Lights could not be posted."
        )


@tasks.loop(minutes=15)
async def severe_weather_report():
    """Automatic severe-weather roll every Monday at 4 PM Toronto time."""
    now = datetime.now(TZ)

    if now.weekday() != 0:
        return

    if now.hour != SEVERE_WEATHER_AUTO_HOUR:
        return

    if now.minute < SEVERE_WEATHER_AUTO_MINUTE:
        return

    week = severe_week_key(now)

    async with data_lock:
        if data.get("last_severe_weather_week") == week:
            return

    result = await run_automatic_severe_weather(mark_week=True)
    events = result.get("events", [])

    if events:
        await post_severe_weather_events(
            events,
            forced=result.get("forced", False)
        )
        return

    # Northern Lights are a separate, non-disaster phenomenon. They never
    # consume a Clan/group's monthly disaster slot and never reset the
    # no-two-quiet-weeks safeguard.
    await trigger_northern_lights(manual=False)


# ─────────────────────────────
# ─────────────────────────────
# QUEST SYSTEM
# ─────────────────────────────

QUEST_CHANNEL_ID = 1441502516591202394
QUEST_FORCE_ROLE_ID = 1441507932369063957
# Quests run from the first day of one month until the first day of the next.
# Reward/penalty effects still last 14 real-life days unless their own text says otherwise.
QUEST_EFFECT_DURATION_DAYS = 14
QUEST_FORCE_SKIP_DAYS = 5
QUEST_SCHEDULE_HOUR = 9
QUEST_SCHEDULE_MINUTE = 0
QUEST_SYSTEM_VERSION = "v4_tuesday_weighted_events"  # kept for database compatibility

CLAN_ROLE_IDS = {
    "BlizzardClan": 1445529729309605978,
    "TorrentClan": 1445529635780563034,
    "SpruceClan": 1445530840170758225,
    "FossilClan": 1445529918518591559,
    "Outsider": 1445530928083505294
}

QUEST_CATEGORY_WEIGHTS = {
    "hunting": 35,
    "social": 20,
    "herb_patrol": 20,
    "crisis": 10,
    "wild_attack": 15
}

QUEST_CATEGORY_LABELS = {
    "hunting": "Hunting Quest",
    "social": "Social Quest",
    "herb_patrol": "Herb Patrol",
    "crisis": "Sickness / Crisis Event",
    "wild_attack": "Wild Animal Event"
}

QUEST_CATEGORY_ICONS = {
    "hunting": "🎯",
    "social": "💬",
    "herb_patrol": "🌿",
    "crisis": "🩺",
    "wild_attack": "🐾"
}

QUEST_NO_REPEAT_CATEGORIES = {
    "social",
    "herb_patrol",
    "crisis"
}

PREDATOR_RULES = {
    "a wolf": {"name": "Wolf", "hp": 60, "min_cats": 3},
    "a beaver": {"name": "Beaver", "hp": 30, "min_cats": 2},
    "a fox": {"name": "Fox", "hp": 40, "min_cats": 2},
    "a badger": {"name": "Badger", "hp": 50, "min_cats": 2},
    "wild dogs": {"name": "Wild Dogs Pack", "hp": 80, "min_cats": 4},
    "a bear": {"name": "Bear", "hp": 80, "min_cats": 4}
}

QUEST_GROUP_ORDER = [
    "BlizzardClan",
    "TorrentClan",
    "FossilClan",
    "SpruceClan",
    "Outsider"
]


def clan_mention(group):
    role_id = CLAN_ROLE_IDS.get(group)

    if not role_id:
        return group

    return f"<@&{role_id}>"


def has_role_id(interaction: discord.Interaction, role_id: int):
    if not hasattr(interaction.user, "roles"):
        return False

    return any(role.id == role_id for role in interaction.user.roles)


async def quest_force_check(interaction: discord.Interaction):
    if not has_role_id(interaction, QUEST_FORCE_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to force new quests.",
            ephemeral=True
        )
        return False

    return True


def ensure_quest_category_tracking():
    data.setdefault("last_quest_categories_v2", {})
    active_quests = data.get("active_quests_v2", {})

    for group, quest in active_quests.items():
        if not quest:
            continue

        category = quest.get("category")
        if category and group not in data["last_quest_categories_v2"]:
            data["last_quest_categories_v2"][group] = category


def category_can_repeat_for_group(group, category):
    if category not in QUEST_NO_REPEAT_CATEGORIES:
        return True

    previous_category = data.get("last_quest_categories_v2", {}).get(group)
    return previous_category != category


def predator_rule_text(animal):
    rules = PREDATOR_RULES.get(animal)

    if not rules:
        return (
            "**Predator Instructions:** Each cat rolls a **d20** each patrol cycle. "
            "Add the patrol's rolls together until the threat is chased away. "
            "Each full cycle where the threat is not beaten adds **+1 injury degree** to every participating cat."
        )

    return (
        f"**Predator Instructions:** **{rules['name']} — {rules['hp']} HP.** "
        f"Minimum patrol: **{rules['min_cats']}+ cats**. Each cat rolls a **d20** each patrol cycle. "
        f"Add the patrol's rolls together and subtract that total from the predator's HP. "
        f"Each full cycle where the predator is not beaten adds **+1 injury degree** to every participating cat. "
        f"For example, if it takes 6 cycles to drive it off, each participating cat receives a **level 6 injury**."
    )


def predator_display_name(animal):
    rules = PREDATOR_RULES.get(animal)
    return rules.get("name", animal.title()) if rules else animal.title()


def reset_legacy_quest_data_if_needed():
    data.setdefault("active_quests_v2", {})
    data.setdefault("used_quests_v2", {})
    data.setdefault("quest_effects_v2", {})
    data.setdefault("quest_history_v2", [])
    data.setdefault("quest_reminders_sent_v2", {})
    data.setdefault("last_quest_categories_v2", {})
    data.setdefault("active_role_quest", None)
    data.setdefault("active_role_quests", [])
    data.setdefault("role_quest_history", [])
    data.setdefault("used_role_quests", [])
    data.setdefault("used_role_quest_roles", [])
    data.setdefault("used_role_quests_by_role", {})

    # Migrate the Aug. 28 single role quest into the new two-slot list without
    # changing the currently active August prompt. September 1 and later cycles
    # automatically generate two role quests.
    if not isinstance(data.get("active_role_quests"), list):
        data["active_role_quests"] = []
    if not data["active_role_quests"] and isinstance(data.get("active_role_quest"), dict):
        data["active_role_quests"] = [data["active_role_quest"]]

    if data.get("quest_system_version") == QUEST_SYSTEM_VERSION:
        ensure_quest_category_tracking()
        return

    for old_key in [
        "active_quests",
        "quest_results",
        "quest_modifiers",
        "used_quests",
        "quest_reminders_sent",
        "last_quest_period",
        "active_quests_v2",
        "used_quests_v2",
        "quest_effects_v2",
        "quest_history_v2",
        "quest_reminders_sent_v2",
        "last_quest_period_v2",
        "last_quest_categories_v2"
    ]:
        data.pop(old_key, None)

    data["quest_system_version"] = QUEST_SYSTEM_VERSION
    data["active_quests_v2"] = {}
    data["used_quests_v2"] = {}
    data["quest_effects_v2"] = {}
    data["quest_history_v2"] = []
    data["quest_reminders_sent_v2"] = {}
    data["last_quest_period_v2"] = None
    data["last_quest_categories_v2"] = {}


QUEST_LORE = {
    "BlizzardClan": {
        "camp": "the Hollow of Teeth",
        "home_detail": "beneath the Frozen Teeth, where cold stone, snow tunnels, and open ridges shape every patrol",
        "sites": [
            {"name": "Glacier's Edge", "channel": "❄️-glaciers-edge", "prey": "pika", "bonus": "pika", "danger": "slick ice shelves and loose stones above the drop"},
            {"name": "Frost Tunnels", "channel": "❄️-frost-tunnels", "prey": "mice", "bonus": "mice", "danger": "black ice, cramped turns, and echoes that confuse pawsteps"},
            {"name": "Cloud Plateau", "channel": "❄️-cloud-plateau", "prey": "snowshoe hares", "bonus": "hares", "danger": "hard wind and open ground with little cover"},
            {"name": "Glacier's Edge", "channel": "❄️-glaciers-edge", "prey": "ptarmigan", "bonus": "birds", "danger": "white feathers hidden against snow and ice"},
            {"name": "Frost Tunnels", "channel": "❄️-frost-tunnels", "prey": "bats", "bonus": "tunnel prey", "danger": "silent wings flashing through the dark"},
            {"name": "Cloud Plateau", "channel": "❄️-cloud-plateau", "prey": "voles", "bonus": "small prey", "danger": "burrows hidden beneath thin crusted snow"}
        ],
        "herbs": ["juniper berries", "cobwebs", "moss for cold dens", "thyme", "coltsfoot", "chervil", "dock leaves", "burdock root"],
        "social_places": ["Frozen Falls", "Cloud Plateau", "the warrior shelf", "the apprentice den", "the nursery crevice", "the Frost Tunnels mouth"],
        "sicknesses": [
            "white cough moving through the cold dens",
            "chill-sickness after a bitter night wind",
            "paw soreness from frozen stone",
            "frost-cracked pads after a rough patrol",
            "a shivering fever spreading between shared nests"
        ],
        "crises": [
            "an avalanche rumbling down near Glacier's Edge",
            "a tunnel roof shedding ice inside Frost Tunnels",
            "a whiteout trapping patrol scents on Cloud Plateau"
        ],
        "wild_animals": ["a wolf", "a fox", "wild dogs", "a badger", "a bear"]
    },
    "TorrentClan": {
        "camp": "the Island",
        "home_detail": "where water guards the camp, reeds twist through the marsh, and fish flash beneath the current",
        "sites": [
            {"name": "Trout Run", "channel": "🌊-trout-run", "prey": "trout", "bonus": "fish", "danger": "fast rapids and slick stepping stones"},
            {"name": "Trout Run", "channel": "🌊-trout-run", "prey": "perch", "bonus": "fish", "danger": "silver flashes beneath rushing water"},
            {"name": "Reedmarsh", "channel": "🌊-reed-marsh", "prey": "frogs", "bonus": "amphibians", "danger": "mud that grabs at every paw"},
            {"name": "Reedmarsh", "channel": "🌊-reed-marsh", "prey": "water voles", "bonus": "marsh prey", "danger": "reed tunnels and slippery banks"},
            {"name": "Glistening Pools", "channel": "🌊-glistening-pools", "prey": "minnows", "bonus": "small fish", "danger": "bright glare on the water and darting schools"},
            {"name": "Glistening Pools", "channel": "🌊-glistening-pools", "prey": "ducks", "bonus": "water birds", "danger": "open banks, splashing wings, and loud alarm calls"}
        ],
        "herbs": ["willow bark", "watermint", "moss for wet dens", "cobwebs", "coltsfoot", "dock leaves", "burdock root", "catmint"],
        "social_places": ["Sunspirit Sands", "the Island", "Trout Run", "Glistening Pools", "Reedmarsh", "the willow roots"],
        "sicknesses": [
            "white cough spreading after damp nights",
            "bellyaches from questionable marsh water",
            "chill after soaked nests",
            "mud-fever in cats who worked too long in Reedmarsh",
            "coughing fits after cold rain"
        ],
        "crises": [
            "floodwater rising around the Island",
            "a sudden rush of water tearing through Reedmarsh",
            "a storm surge washing over low trails"
        ],
        "wild_animals": ["a beaver", "a fox", "wild dogs", "a badger", "a bear"]
    },
    "FossilClan": {
        "camp": "the Red Rock",
        "home_detail": "among warm stone, old fossils, crystal-lit walls, and exposed hunting flats",
        "sites": [
            {"name": "Dustwind Flats", "channel": "🦴-dustwind-flats", "prey": "mice", "bonus": "small prey", "danger": "open stone, tumbleweeds, and shifting dust"},
            {"name": "Dustwind Flats", "channel": "🦴-dustwind-flats", "prey": "voles", "bonus": "small prey", "danger": "flatland trails and sudden gusts"},
            {"name": "Raptorfang Spires", "channel": "🦴-raptorfang-spires", "prey": "pika", "bonus": "rock prey", "danger": "thin pillars and dizzying drops"},
            {"name": "Rexhead Pillars", "channel": "🦴-rexhead-pillars", "prey": "rock pigeons", "bonus": "birds", "danger": "wide ledges and bold leaps"},
            {"name": "Dustwind Flats", "channel": "🦴-dustwind-flats", "prey": "garter snakes", "bonus": "reptiles", "danger": "sun-warmed coils beneath brush"},
            {"name": "Rexhead Pillars", "channel": "🦴-rexhead-pillars", "prey": "ptarmigan", "bonus": "birds", "danger": "camouflage against pale stone"}
        ],
        "herbs": ["dry herbs", "cobwebs", "yarrow", "chervil", "dock leaves", "burdock root", "thyme", "marigold"],
        "social_places": ["Dinosaur Spine", "the Red Rock", "Raptorfang Spires", "Rexhead Pillars", "Dustwind Flats", "the crystal-lit wall"],
        "sicknesses": [
            "dust cough after dry winds",
            "white cough moving through shaded stone dens",
            "heat-sickness after a sun-heavy patrol",
            "sore throats from dusty air",
            "a fever that leaves cats sluggish on warm rock"
        ],
        "crises": [
            "a rockslide near Raptorfang Spires",
            "a dust storm swallowing the Flats",
            "loose stones cracking away from Rexhead Pillars"
        ],
        "wild_animals": ["a fox", "a badger", "a wolf", "wild dogs", "a bear"]
    },
    "SpruceClan": {
        "camp": "the Shadow Hearth",
        "home_detail": "beneath interlocked spruce branches, deep roots, hidden ponds, and mushroom-dark shade",
        "sites": [
            {"name": "Whispering Branches", "channel": "🌲-whispering-branches", "prey": "squirrels", "bonus": "tree prey", "danger": "high branches and chattering warnings"},
            {"name": "Whispering Branches", "channel": "🌲-whispering-branches", "prey": "sparrows", "bonus": "birds", "danger": "dense canopy and fluttering panic"},
            {"name": "Deeproot Tangle", "channel": "🌲-deeproot-tangle", "prey": "water voles", "bonus": "root prey", "danger": "twisting roots and hidden pockets of water"},
            {"name": "Sundance Pond", "channel": "🌲-sundance-pond", "prey": "frogs", "bonus": "amphibians", "danger": "sun-dappled banks and slippery stones"},
            {"name": "Sundance Pond", "channel": "🌲-sundance-pond", "prey": "minnows", "bonus": "small water prey", "danger": "clear water that reveals every shadow"},
            {"name": "Deeproot Tangle", "channel": "🌲-deeproot-tangle", "prey": "garter snakes", "bonus": "reptiles", "danger": "sunlit roots and sudden movement"}
        ],
        "herbs": ["safe mushrooms", "medicinal moss", "cobwebs", "thyme", "dock leaves", "burdock root", "chervil", "marigold"],
        "social_places": ["the Shadow Hearth", "Whispering Branches", "Sundance Pond", "Toadstool Glade", "Deeproot Tangle", "the nursery roots"],
        "sicknesses": [
            "spore sickness near the damp roots",
            "white cough spreading through shaded dens",
            "bellyaches after bad mushroom scents drifted through camp",
            "a moss-damp fever",
            "sneezing fits after pollen gathered under the branches"
        ],
        "crises": [
            "a rotten tree cracking down near Deeproot Tangle",
            "toxic mushrooms appearing near a patrol path",
            "Sundance Pond flooding into the roots after heavy rain"
        ],
        "wild_animals": ["a badger", "a fox", "wild dogs", "a wolf", "a bear"]
    },
    "Outsider": {
        "camp": "the borderlands beyond Clan rule",
        "home_detail": "between barns, cliffs, neon signs, old fences, twoleg streets, and half-hidden shelters",
        "sites": [
            {"name": "The Sanctuary", "channel": "🐖-the-sanctuary", "prey": "mice", "bonus": "barn prey", "danger": "careless prey and curious barn animals"},
            {"name": "The Sanctuary", "channel": "🐖-the-sanctuary", "prey": "barn rats", "bonus": "barn prey", "danger": "bold rats near feed stores"},
            {"name": "Frostbite Ridge", "channel": "🧊-frostbite-ridge", "prey": "gulls", "bonus": "cliff birds", "danger": "sheer drops and brutal wind"},
            {"name": "The Neon Path", "channel": "🥡-neon-path", "prey": "rats", "bonus": "city prey", "danger": "hard stone, dogs, and rival rogues"},
            {"name": "The Twoleg Town", "channel": "🏡-twoleg-town", "prey": "sparrows", "bonus": "town birds", "danger": "fences, gardens, and watching kittypets"},
            {"name": "The Neon Path", "channel": "🥡-neon-path", "prey": "mice", "bonus": "city prey", "danger": "dumpster scents and sudden twoleg noise"}
        ],
        "herbs": ["catmint", "cobwebs", "dock leaves", "burdock root", "marigold", "moss for hidden shelters", "chervil", "thyme"],
        "social_places": ["The Sanctuary", "The Neon Path", "The Twoleg Town", "Frostbite Ridge", "the neutral borders", "an abandoned shed"],
        "sicknesses": [
            "white cough passing between shared shelters",
            "bellyaches from bad twoleg scraps",
            "infected scratches after alley fights",
            "chill from sleeping without shelter",
            "a fever moving through crowded hiding places"
        ],
        "crises": [
            "twolegs clearing out a familiar shelter",
            "floodwater filling an alley hideout",
            "a fence collapse cutting off a safe route"
        ],
        "wild_animals": ["wild dogs", "a fox", "a badger", "a beaver", "a wolf"]
    }
}

HUNTING_SCENARIOS = [
    "Fresh Trail Rush",
    "Dawn Patrol Catch",
    "Dusk Ambush",
    "Two-Patrol Team Hunt",
    "Silent Steps Challenge",
    "Fresh-Kill Pile Rescue",
    "Weather Window",
    "Mentor-Led Hunt",
    "Tracking Test",
    "Fast Paws Trial",
    "Patient Hunter Trial",
    "Moonlit Hunt"
]

SOCIAL_SCENARIOS = [
    ("Story Time", "Gather for stories, old memories, exaggerated legends, and the kind of dramatic retelling that gets funnier every time another cat adds details."),
    ("Truth or Dare", "A playful camp scene where cats can trade harmless truths, silly dares, dramatic confessions, and chaotic little challenges without turning it mean."),
    ("Campfire Confessions", "A quieter scene for cats to admit worries, hopes, awkward feelings, strange dreams, or secrets they have been carrying around."),
    ("Shared Meal Gossip", "Bring prey, share tongues, and let conversations drift between gentle bonding, funny gossip, and dramatic camp opinions."),
    ("Tall Tales Night", "Cats compete to tell the most ridiculous, spooky, heroic, or obviously fake story while everyone else reacts."),
    ("Friendly Challenge Night", "Cats set up small contests, games, dares, races, or silly tests of pride that can build bonds or spark harmless rivalry."),
    ("Rivalry Reset", "Cats with tension are nudged into the same space to compete, talk, apologize, or at least stop glaring long enough to make a scene interesting."),
    ("Moonlit Bonding", "Under moonlight, cats gather somewhere scenic to talk, joke, share old fears, and remember that they are not surviving the mountain alone."),
    ("Apprentice Dare Night", "Apprentices and younger warriors get a chance to be loud, bold, silly, brave, and maybe a little too confident while older cats supervise."),
    ("Secret Swap", "Cats exchange harmless secrets, rumours, dreams, crush theories, or embarrassing stories, creating a scene full of personality and reactions.")
]

HERB_PATROL_SCENARIOS = [
    "Medicine Store Restock",
    "Emergency Herb Search",
    "Moss and Cobweb Sweep",
    "Rare Herb Patrol",
    "Damp Den Prevention",
    "After-Storm Supply Check",
    "Healer Errand",
    "Apprentice Herb Lesson"
]


def make_quest_id(group, category, number):
    return f"{group.lower().replace(' ', '-')}-{category}-{number:02d}"


def broad_hunting_target(site):
    """Turn species-specific prey into broad goals that are less dependent on prey-bot RNG."""
    prey = str(site.get("prey", "")).casefold()
    bonus = str(site.get("bonus", "")).casefold()
    combined = f"{prey} {bonus}"

    bird_words = ["bird", "sparrow", "pigeon", "ptarmigan", "gull", "duck"]
    fish_words = ["fish", "trout", "perch", "minnow"]

    if any(word in combined for word in bird_words):
        return "birds"
    if any(word in combined for word in fish_words):
        return "fish"
    return "small prey"


def hunting_reward_for(group, amount, target):
    modifier = 2 if amount >= 5 else 1
    reward_text = f"If completed, {group} earns **{format_modifier(modifier)} to all {target} hunting rolls** for the next 2 real-life weeks."
    effect = {"kind": "hunting", "target": target, "modifier": modifier}

    failure_text = f"If failed, there is a chance {group} suffers **-1 to all {target} hunting rolls** for the next 2 real-life weeks because the prey route was disturbed."
    penalty = {"kind": "hunting", "target": target, "modifier": -1, "chance": 0.4}

    return reward_text, failure_text, effect, penalty


def build_quest_database():
    quest_db = {}

    for group, lore in QUEST_LORE.items():
        quest_db[group] = {
            "hunting": [],
            "social": [],
            "herb_patrol": [],
            "crisis": [],
            "wild_attack": []
        }

        # Hunting goals intentionally use broad prey categories instead of exact
        # species. This keeps the monthly quest attainable even when the separate
        # prey-trigger bot does not happen to spawn one specific animal.
        hunt_amounts = [3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4]
        for index, style_title in enumerate(HUNTING_SCENARIOS):
            site = lore["sites"][index % len(lore["sites"])]
            amount = hunt_amounts[index % len(hunt_amounts)]
            broad_target = broad_hunting_target(site)
            reward_text, failure_text, effect, penalty = hunting_reward_for(group, amount, broad_target)

            quest_db[group]["hunting"].append({
                "id": make_quest_id(group, "hunting", index + 1),
                "category": "hunting",
                "broad_hunting": True,
                "hunt_required": amount,
                "hunt_target": broad_target,
                "hunt_site": site["name"],
                "hunt_catches": [],
                "title": f"{style_title}: Catch {amount} {broad_target.title()}",
                "objective": f"Catch **{amount} {broad_target}** at **{site['name']}**. Any prey that fits the category counts.",
                "description": (
                    f"Travel to **{site['name']}** ({site['channel']}) where {site['danger']} make the patrol feel alive. "
                    f"The prey goal is deliberately broad so the patrol can use whatever fitting prey actually appears instead of waiting on one exact species."
                ),
                "reward_text": reward_text,
                "failure_text": failure_text,
                "success_result": f"For the next **2 real-life weeks**, {group} gets **{format_modifier(effect['modifier'])} to all {broad_target} hunting rolls**.",
                "failure_result": f"For the next **2 real-life weeks**, {group} has **-1 to all {broad_target} hunting rolls** because the failed hunt scattered prey signs.",
                "effect": effect,
                "penalty": penalty
            })

        for index, (style_title, style_description) in enumerate(SOCIAL_SCENARIOS):
            place = lore["social_places"][index % len(lore["social_places"])]
            quest_db[group]["social"].append({
                "id": make_quest_id(group, "social", index + 1),
                "category": "social",
                "title": f"{place} {style_title}",
                "objective": f"Complete a group roleplay scene focused on **{style_title.lower()}** at or around **{place}**.",
                "description": (
                    f"{style_description} Keep it character-driven and fun, with enough room for jokes, bonding, tension, or small heartfelt moments. "
                    f"The scene should include a few different characters interacting meaningfully."
                ),
                "reward_text": f"If completed, {group} gains a **morale boost** for the next 2 real-life weeks. Social scenes, teamwork, and training can feel a little smoother.",
                "failure_text": f"If skipped, there is no harsh mechanical punishment, but {group}'s camp may feel quieter, tense, or disconnected for the next 2 real-life weeks.",
                "success_result": f"For the next **2 real-life weeks**, {group} has a **morale boost**. Teamwork, bonding, training, and tense conversations may go a little smoother.",
                "failure_result": f"For the next **2 real-life weeks**, {group}'s morale is a little strained. Staff may flavour scenes with tension, awkward silence, or short tempers.",
                "effect": {"kind": "morale", "target": "group morale", "modifier": 1},
                "penalty": {"kind": "morale", "target": "group morale", "modifier": -1}
            })

        for index, style_title in enumerate(HERB_PATROL_SCENARIOS):
            herb = lore["herbs"][index % len(lore["herbs"])]
            place = lore["social_places"][index % len(lore["social_places"])]
            quest_db[group]["herb_patrol"].append({
                "id": make_quest_id(group, "herb_patrol", index + 1),
                "category": "herb_patrol",
                "title": f"{style_title}: {herb.title()}",
                "objective": f"Gather or refresh **{herb}** near **{place}**.",
                "description": (
                    f"Medicine supplies need attention around **{lore['camp']}**, {lore['home_detail']}. "
                    f"This can be a healer-led patrol, a medicine cat lesson, a resource scene, or a small group errand with room for complications."
                ),
                "reward_text": f"If completed, {group}'s medicine stores improve. Staff may apply **-1 severity** to one fitting new illness/injury treatment scene during the next 2 real-life weeks.",
                "failure_text": f"If failed, medicine supplies are strained. Staff may apply **+1 severity** to one fitting new illness/injury situation during the next 2 real-life weeks.",
                "success_result": f"For the next **2 real-life weeks**, {group}'s medicine stores are stronger. Staff may apply **-1 severity** to one fitting illness or injury treatment scene.",
                "failure_result": f"For the next **2 real-life weeks**, {group}'s medicine supplies are strained. Staff may apply **+1 severity** to one fitting illness or injury situation.",
                "effect": {"kind": "herbs", "target": herb, "modifier": 1},
                "penalty": {"kind": "herb strain", "target": herb, "modifier": -1}
            })

        crisis_number = 1
        for sickness in lore["sicknesses"]:
            quest_db[group]["crisis"].append({
                "id": make_quest_id(group, "crisis", crisis_number),
                "category": "crisis",
                "title": f"No Regular Quest: {sickness.title()}",
                "objective": f"There is **no regular quest** this cycle. Instead, roleplay how {group} responds to **{sickness}**.",
                "description": (
                    f"Cats may choose to roll a sickness severity from **1-5** if they want their OC affected. Medicine cats, healers, leaders, and clanmates can organize treatments, comfort scenes, den cleaning, or herb patrols. "
                    f"This is a story event first, not a punishment."
                ),
                "reward_text": f"If the outbreak response is completed, staff may apply **-1 severity** to one fitting sickness treatment or mark the outbreak contained.",
                "failure_text": f"If ignored, the sickness may linger. Staff may apply **+1 severity** to one fitting new sickness case during the next 2 real-life weeks.",
                "success_result": f"{group}'s outbreak response helped. Staff may apply **-1 severity** to one fitting sickness treatment or mark the illness contained.",
                "failure_result": f"{group}'s outbreak was not fully contained. Staff may apply **+1 severity** to one fitting new sickness case during the next 2 real-life weeks.",
                "effect": {"kind": "outbreak contained", "target": sickness, "modifier": 1},
                "penalty": {"kind": "outbreak strain", "target": sickness, "modifier": -1}
            })
            crisis_number += 1

        for crisis in lore["crises"]:
            quest_db[group]["crisis"].append({
                "id": make_quest_id(group, "crisis", crisis_number),
                "category": "crisis",
                "title": f"No Regular Quest: {crisis.title()}",
                "objective": f"There is **no regular quest** this cycle. Instead, roleplay how {group} handles **{crisis}**.",
                "description": (
                    f"Cats involved may roll for injury if they want danger in the scene, using the existing **1-5 severity scale** for this event. "
                    f"Patrols can rescue trapped cats, reinforce camp, check borders, gather herbs, or simply react to the aftermath."
                ),
                "reward_text": f"If the crisis response is completed, {group} stabilizes quickly and staff may grant a small scene advantage for rescue, recovery, or patrol safety.",
                "failure_text": f"If ignored, the crisis leaves damage behind. Staff may apply **+1 severity** to one fitting injury or add a temporary patrol complication.",
                "success_result": f"{group} handled the crisis. Staff may grant a small scene advantage for rescue, recovery, or patrol safety during the next 2 real-life weeks.",
                "failure_result": f"{group}'s crisis left damage behind. Staff may apply **+1 severity** to one fitting injury or add a temporary patrol complication.",
                "effect": {"kind": "crisis response", "target": crisis, "modifier": 1},
                "penalty": {"kind": "crisis damage", "target": crisis, "modifier": -1}
            })
            crisis_number += 1

        for index in range(8):
            animal = lore["wild_animals"][index % len(lore["wild_animals"])]
            site = lore["sites"][index % len(lore["sites"])]
            predator_name = predator_display_name(animal)
            quest_db[group]["wild_attack"].append({
                "id": make_quest_id(group, "wild_attack", index + 1),
                "category": "wild_attack",
                "title": f"Drive Off {predator_name} at {site['name']}",
                "objective": f"Chase away **{predator_name}** near **{site['name']}** before it settles into the territory.",
                "description": (
                    f"The threat has been spotted around **{site['name']}** ({site['channel']}). Cats can confront it, distract it, track it away, protect vulnerable Clanmates, or call for backup.\n\n"
                    f"{predator_rule_text(animal)}"
                ),
                "reward_text": f"If completed, {group} secures the area and earns **+1 to all hunting rolls** for the next 2 real-life weeks because prey can return safely.",
                "failure_text": f"If failed, the threat lingers. Staff may apply **-1 to all hunting rolls** for {group}. Injury degree follows the predator instructions above.",
                "success_result": f"For the next **2 real-life weeks**, {group} gets **+1 to all hunting rolls** because the territory feels safer again.",
                "failure_result": f"For the next **2 real-life weeks**, {group} has **-1 to all hunting rolls** while the threat lingers. Injury degree follows the predator instructions from the event.",
                "effect": {"kind": "hunting", "target": "all hunting rolls", "modifier": 1},
                "penalty": {"kind": "hunting", "target": "all hunting rolls", "modifier": -1}
            })

    return quest_db


QUEST_DATABASE = build_quest_database()


def validate_quest_database():
    required_categories = set(QUEST_CATEGORY_WEIGHTS.keys())

    for group, categories in QUEST_DATABASE.items():
        missing = required_categories - set(categories.keys())

        if missing:
            raise RuntimeError(f"{group} quest database is missing categories: {', '.join(sorted(missing))}.")

        for category in required_categories:
            if len(categories.get(category, [])) < 5:
                raise RuntimeError(f"{group} {category} quest count is too low for varied quest rolls.")


validate_quest_database()


def get_quest_expiry_iso():
    return (datetime.now(TZ) + timedelta(days=QUEST_EFFECT_DURATION_DAYS)).isoformat()


def clean_expired_quest_effects():
    data.setdefault("quest_effects_v2", {})
    now = datetime.now(TZ)

    for group, effects in list(data["quest_effects_v2"].items()):
        active_effects = []

        for effect in effects:
            expires_at = effect.get("expires_at")

            if not expires_at:
                active_effects.append(effect)
                continue

            try:
                expiry = datetime.fromisoformat(expires_at)
            except Exception:
                continue

            if expiry > now:
                active_effects.append(effect)

        if active_effects:
            data["quest_effects_v2"][group] = active_effects
        else:
            data["quest_effects_v2"].pop(group, None)


def choose_quest_category(group=None):
    categories = []
    weights = []

    for category, weight in QUEST_CATEGORY_WEIGHTS.items():
        if group and not category_can_repeat_for_group(group, category):
            continue

        categories.append(category)
        weights.append(weight)

    if not categories:
        categories = list(QUEST_CATEGORY_WEIGHTS.keys())
        weights = [QUEST_CATEGORY_WEIGHTS[category] for category in categories]

    return random.choices(categories, weights=weights, k=1)[0]


def select_new_quest(group, preferred_category=None):
    reset_legacy_quest_data_if_needed()
    data.setdefault("used_quests_v2", {})
    data.setdefault("last_quest_categories_v2", {})
    data["used_quests_v2"].setdefault(group, {})

    if preferred_category and category_can_repeat_for_group(group, preferred_category):
        category = preferred_category
    elif preferred_category and preferred_category not in QUEST_NO_REPEAT_CATEGORIES:
        category = preferred_category
    else:
        category = choose_quest_category(group)

    previous_category = data["last_quest_categories_v2"].get(group)
    data["used_quests_v2"][group].setdefault(category, [])

    used_ids = data["used_quests_v2"][group][category]
    quest_pool = QUEST_DATABASE[group][category]

    available = [quest for quest in quest_pool if quest["id"] not in used_ids]

    if not available:
        used_ids.clear()
        available = quest_pool.copy()

    quest = copy.deepcopy(random.choice(available))
    used_ids.append(quest["id"])

    issued_at = datetime.now(TZ)
    due_at = next_regular_quest_cycle(issued_at)

    quest["group"] = group
    quest["status"] = "Pending"
    quest["issued_at"] = issued_at.isoformat()
    quest["due_at"] = due_at.isoformat()
    quest["previous_category"] = previous_category

    data["last_quest_categories_v2"][group] = category

    return quest


def add_quest_effect(group, effect, source_title, result_text):
    if not effect:
        return

    data.setdefault("quest_effects_v2", {})
    data["quest_effects_v2"].setdefault(group, [])

    saved_effect = copy.deepcopy(effect)
    saved_effect["source"] = source_title
    saved_effect["summary"] = result_text
    saved_effect["expires_at"] = get_quest_expiry_iso()

    data["quest_effects_v2"][group].append(saved_effect)


def apply_quest_success(group, quest):
    effect = quest.get("effect", {})
    title = quest.get("title", "Quest")
    result_text = quest.get("success_result")

    if not result_text:
        category = quest.get("category")
        if category == "hunting":
            target = effect.get("target", "fitting prey")
            modifier = effect.get("modifier", 1)
            result_text = f"For the next **2 real-life weeks**, {group} gets **{format_modifier(modifier)} to all {target} hunting rolls**."
        else:
            result_text = f"For the next **2 real-life weeks**, {group} gains the listed quest reward."

    add_quest_effect(group, effect, title, result_text)
    return result_text


def apply_quest_failure(group, quest):
    penalty = quest.get("penalty", {})
    title = quest.get("title", "Quest")

    if quest.get("category") == "hunting":
        chance = penalty.get("chance", 0.4)

        if random.random() > chance:
            return "No lasting penalty this time. The hunt failed, but prey routes were not disrupted enough to affect future rolls."

    result_text = quest.get("failure_result")

    if not result_text:
        target = penalty.get("target", "the quest area")
        modifier = penalty.get("modifier", -1)
        result_text = f"For the next **2 real-life weeks**, {group} has **{format_modifier(modifier)} involving {target}**."

    add_quest_effect(group, penalty, title, result_text)
    return result_text


def complete_pending_failures():
    data.setdefault("active_quests_v2", {})
    data.setdefault("quest_history_v2", [])

    failed_results = []

    for group, quest in list(data["active_quests_v2"].items()):
        if not quest or quest.get("status") != "Pending":
            continue

        penalty_text = apply_quest_failure(group, quest)
        quest["status"] = "Failed"
        quest["failed_at"] = datetime.now(TZ).isoformat()
        quest["failure_result"] = penalty_text

        data["quest_history_v2"].append(copy.deepcopy(quest))

        failed_results.append({
            "group": group,
            "title": quest.get("title", "Unknown Quest"),
            "category": quest.get("category", "quest"),
            "penalty": penalty_text
        })

    return failed_results


ROLE_QUEST_DOUBLE_START = date(2026, 9, 1)

ROLE_QUEST_PROMPTS = [
    # Kits — all 20 cycle before any Kit prompt repeats.
    {"id": "kit-great-escape", "role": "Kits", "eligible_ranks": ["Kit"], "title": "The Great Escape", "objective": "Sneak out of the nursery or wander farther from your caretaker than you were supposed to, only to be discovered by another Clanmate."},
    {"id": "kit-important-mission", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Very Important Mission", "objective": "Invent an extremely serious task for yourself and convince at least one other cat that it absolutely must be completed."},
    {"id": "kit-warrior-training", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Warrior Training! Probably!", "objective": "Challenge another kit, apprentice, or very patient adult to a pretend battle and show off your finest imaginary warrior moves."},
    {"id": "kit-treasure-hunter", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Treasure Hunter", "objective": "Find an interesting feather, stone, shell, flower, bone, stick, or other harmless object and proudly bring your treasure back to camp."},
    {"id": "kit-questions", "role": "Kits", "eligible_ranks": ["Kit"], "title": "What Does This Do?", "objective": "Ask a Clanmate far too many questions about their rank, duties, scars, skills, or something else you find fascinating."},
    {"id": "kit-best-nest", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Best Nest Ever", "objective": "Attempt to improve your nest with moss, feathers, leaves, flowers, or completely unnecessary decorations."},
    {"id": "kit-tiny-hunter", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Tiny Hunter", "objective": "Stalk a leaf, bug, feather, tail, pinecone, or other harmless target as though the survival of the entire Clan depends upon catching it."},
    {"id": "kit-catch-me", "role": "Kits", "eligible_ranks": ["Kit"], "title": "You Can't Catch Me!", "objective": "Start a game of chase with another kit or willing Clanmate around camp."},
    {"id": "kit-council", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Kit Council", "objective": "Gather another kit or two and hold a very serious meeting about an extremely unserious problem."},
    {"id": "kit-new-friend", "role": "Kits", "eligible_ranks": ["Kit"], "title": "New Best Friend", "objective": "Approach a Clanmate you do not usually interact with and decide that today is the perfect day to become friends."},
    {"id": "kit-gossip", "role": "Kits", "eligible_ranks": ["Kit"], "title": "I Heard Something!", "objective": "Overhear a piece of Clan gossip and ask somebody about it, regardless of whether you understood it correctly."},
    {"id": "kit-floor-lava", "role": "Kits", "eligible_ranks": ["Kit"], "title": "The Floor Is Lava", "objective": "Create a game involving jumping between rocks, roots, nests, logs, or other safe objects without touching the imaginary danger below."},
    {"id": "kit-explorer", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Brave Little Explorer", "objective": "Explore somewhere in camp you normally ignore and investigate everything interesting you find there."},
    {"id": "kit-future-legend", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Future Clan Legend", "objective": "Tell somebody exactly what kind of incredible warrior, healer, leader, or otherwise legendary cat you are going to become someday."},
    {"id": "kit-gift", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Gift Delivery", "objective": "Find or make a tiny gift and give it to another Clanmate for whatever reason seems important to you."},
    {"id": "kit-copycat", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Copycat", "objective": "Choose an older Clanmate you admire and spend part of a scene attempting to imitate the way they walk, speak, hunt, groom, or behave."},
    {"id": "kit-accused", "role": "Kits", "eligible_ranks": ["Kit"], "title": "The Accused", "objective": "Blame another kit, apprentice, sibling, imaginary creature, or suspicious-looking object for a harmless bit of mischief."},
    {"id": "kit-hideout", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Secret Hideout", "objective": "Find or create a little hiding place in camp and invite somebody you trust to see it."},
    {"id": "kit-scary-story", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Very Scary Story", "objective": "Try to scare another kit or Clanmate with the most frightening story you can invent."},
    {"id": "kit-cuddle", "role": "Kits", "eligible_ranks": ["Kit"], "title": "Emergency Cuddle", "objective": "Decide somebody looks lonely, grumpy, cold, tired, or otherwise in desperate need of kit companionship and go bother them affectionately."},

    # Apprentices — all 20 cycle before any Apprentice prompt repeats.
    {"id": "app-moss", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Fresh Moss Run", "objective": "Gather fresh moss or bedding for a Clan den and bring it back to camp."},
    {"id": "app-lesson", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Ask for a Lesson", "objective": "Ask a mentor or experienced warrior to teach or review one useful Clan skill in RP."},
    {"id": "app-elder", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Elder Errand", "objective": "Help an Elder with prey, bedding, grooming, or another small everyday task."},
    {"id": "app-practice", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Practice Makes Progress", "objective": "Roleplay a short training session focused on hunting, tracking, climbing, swimming, or battle practice."},
    {"id": "app-race", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Race You There!", "objective": "Challenge another apprentice or willing Clanmate to a friendly race somewhere safe within the territory."},
    {"id": "app-challenge", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Choose My Challenge", "objective": "Ask another cat to give you a small training challenge, then attempt whatever they come up with."},
    {"id": "app-tour-guide", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Territory Tour Guide", "objective": "Visit a familiar landmark with another Clanmate and tell them what you know about the area, correctly or otherwise."},
    {"id": "app-hunt-experiment", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Hunting Experiment", "objective": "Try a hunting technique you do not normally use, even if the attempt turns out embarrassingly badly."},
    {"id": "app-rivalry", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Friendly Rivalry", "objective": "Challenge another apprentice to a harmless competition involving hunting, tracking, climbing, swimming, balance, speed, or another skill."},
    {"id": "app-patrol", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Patrol Tagalong", "objective": "Join or organize a short patrol and make yourself useful along the way."},
    {"id": "app-learn-elders", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Learn From Your Elders", "objective": "Ask an Elder about something that happened before you were born and see what story you get."},
    {"id": "app-showoff", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Show-Off Season", "objective": "Attempt to impress another Clanmate with one of your skills. Whether you actually succeed is completely optional."},
    {"id": "app-wrong-turn", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Wrong Turn", "objective": "Take the slightly less familiar route during a training trip and explore somewhere you do not usually visit."},
    {"id": "app-picnic", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Apprentice Picnic", "objective": "Share prey with another apprentice somewhere outside the apprentice den and spend some time talking about anything except training."},
    {"id": "app-skill-swap", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Secret Skill Swap", "objective": "Teach another apprentice something you are good at and have them teach you something in return."},
    {"id": "app-mentor-thanks", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Mentor Appreciation", "objective": "Do something small and thoughtful for your mentor, whether that means bringing them prey, gathering moss, leaving them a gift, or simply thanking them."},
    {"id": "app-camp-challenge", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Camp Challenge", "objective": "Find something around camp that needs doing and complete it before somebody has to ask you."},
    {"id": "app-shadow-specialist", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Shadow a Specialist", "objective": "Spend some time with a healer, Preymaster, Pathfinder, River Guardian, Digger, Sporekeeper, or another specialized Clanmate and learn something about what they do."},
    {"id": "app-dare", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Dare Accepted", "objective": "Let another apprentice give you a harmless dare and attempt it in RP."},
    {"id": "app-future-warrior", "role": "Apprentices", "eligible_ranks": ["Apprentice"], "title": "Future Warrior Talk", "objective": "Talk with another cat about the warrior you hope to become, what you are excited about, and what still makes you nervous."},

    # Warriors — all 20 cycle before any Warrior prompt repeats.
    {"id": "warrior-border", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Mark the Borders", "objective": "Take part in a border patrol and refresh at least one stretch of scent markers."},
    {"id": "warrior-checkin", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Clanmate Check-In", "objective": "Notice a Clanmate who is alone, stressed, or bored and start a meaningful conversation with them."},
    {"id": "warrior-den", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Camp Upkeep", "objective": "Repair, clean, reinforce, or gather materials for one of the Clan's dens."},
    {"id": "warrior-share", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Share the Catch", "objective": "Bring prey back to camp and deliberately share a meal or conversation with another Clanmate."},
    {"id": "warrior-scenic", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Take the Scenic Route", "objective": "Patrol a part of the territory you have not visited recently and see what has changed."},
    {"id": "warrior-apprentice-ambush", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Apprentice Ambush", "objective": "Offer an apprentice an unexpected mini-training session, challenge, or bit of practical advice."},
    {"id": "warrior-hunt-company", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Hunt With Company", "objective": "Invite another Clanmate hunting and use the trip as an excuse to catch up."},
    {"id": "warrior-border-talk", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Border Conversation", "objective": "Encounter a cat from another Clan near a border and have a peaceful, awkward, suspicious, funny, or tense conversation without starting a fight."},
    {"id": "warrior-new-tricks", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Old Skills, New Tricks", "objective": "Ask another warrior to show you a technique they use differently from you and give it a try yourself."},
    {"id": "warrior-therapist", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Unofficial Camp Therapist", "objective": "Listen to another Clanmate complain about something and offer whatever advice your character considers helpful."},
    {"id": "warrior-bring-someone", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Bring Someone Along", "objective": "Notice a younger, quieter, or less involved Clanmate and invite them to accompany you on a simple task."},
    {"id": "warrior-detour", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Patrol Detour", "objective": "While travelling through the territory, investigate an unusual scent, sound, track, object, or harmless disturbance."},
    {"id": "warrior-stranger-meal", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Meal With a Stranger", "objective": "Share prey with a Clanmate your character rarely speaks to and actually get to know them."},
    {"id": "warrior-competition", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Warrior Competition", "objective": "Challenge another warrior to a friendly contest of speed, strength, tracking, climbing, swimming, hunting, or another Clan skill."},
    {"id": "warrior-improvement", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "The Camp Improvement Project", "objective": "Decide something around camp could clearly be better and recruit somebody to help you fix, move, reinforce, decorate, or reorganize it."},
    {"id": "warrior-long-way", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Take the Long Way Home", "objective": "After finishing a patrol or hunt, linger somewhere scenic with another Clanmate instead of immediately returning to camp."},
    {"id": "warrior-babysitter", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Unexpected Babysitter", "objective": "Spend some time entertaining, supervising, teaching, or being relentlessly questioned by one or more kits."},
    {"id": "warrior-scar-story", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Story Behind the Scar", "objective": "Ask another warrior about one of their scars, quirks, habits, possessions, or memorable experiences and trade a story of your own."},
    {"id": "warrior-intervention", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Friendly Intervention", "objective": "Catch a Clanmate doing something foolish, reckless, stubborn, or suspicious and decide whether to stop them, help them, or make the situation considerably worse."},
    {"id": "warrior-make-day", "role": "Warriors", "eligible_ranks": ["Warrior"], "title": "Make Someone's Day", "objective": "Do one small thing specifically to cheer up another Clanmate, whether that means bringing them prey, inviting them somewhere, complimenting them, teasing them affectionately, or simply keeping them company."},

    # Elders — all 20 cycle before any Elder prompt repeats.
    {"id": "elder-gossip", "role": "Elders", "eligible_ranks": ["Elder"], "title": "A Little Clan Gossip", "objective": "Start a harmless gossip session, dramatic retelling, or opinionated conversation about recent Clan life."},
    {"id": "elder-story", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Old Story, New Ears", "objective": "Tell a younger cat a story from the past, whether it is wise, ridiculous, or suspiciously exaggerated."},
    {"id": "elder-advice", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Unsolicited Wisdom", "objective": "Give a younger Clanmate advice about something they are dealing with, useful or otherwise."},
    {"id": "elder-gamejudge", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Official Judge", "objective": "Get roped into judging a kit or apprentice game, contest, story, or petty disagreement."},
    {"id": "elder-back-day", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Back In My Day", "objective": "Explain to somebody how apprentices, warriors, prey, weather, patrols, or basically anything else were apparently much tougher in your day."},
    {"id": "elder-favourite", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Favourite Child", "objective": "Declare one younger Clanmate your favourite for the day and make absolutely no effort to hide your bias."},
    {"id": "elder-snack-tax", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Snack Tax", "objective": "Convince another Clanmate that whatever prey they brought you looks considerably better than the prey already sitting nearby."},
    {"id": "elder-matchmaker", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Matchmaker", "objective": "Offer completely unsolicited romantic observations, matchmaking attempts, or relationship advice to another Clanmate."},
    {"id": "elder-investigation", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Elder Investigation Bureau", "objective": "Notice something mildly suspicious around camp and launch an unnecessary investigation into it."},
    {"id": "elder-everything", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Tell Me Everything", "objective": "Corner an apprentice or warrior returning from patrol and demand all the interesting details."},
    {"id": "elder-absolutely-not", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Absolutely Not", "objective": "Find something younger cats are doing and loudly explain why you think it is a terrible idea."},
    {"id": "elder-kit-duty", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Kit Entertainment Duty", "objective": "Tell kits a story, teach them a game, answer their endless questions, or encourage an amount of mischief you definitely should not."},
    {"id": "elder-childhood-story", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Embarrassing Childhood Story", "objective": "Tell somebody an embarrassing story about a warrior, leader, healer, or other respected Clanmate from when they were younger."},
    {"id": "elder-good-old-days", "role": "Elders", "eligible_ranks": ["Elder"], "title": "The Good Old Days", "objective": "Visit a familiar part of camp or the territory with another Clanmate and reminisce about something that happened there long ago."},
    {"id": "elder-nap", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Expert Nap Location", "objective": "Find somewhere unusually comfortable to nap and defend your new favourite sleeping spot from anybody questioning it."},
    {"id": "elder-orders", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Elder's Orders", "objective": "Ask a younger Clanmate to fetch, move, bring, fix, or investigate something for you, then supervise with unnecessary seriousness."},
    {"id": "elder-rebellion", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Tiny Rebellion", "objective": "Ignore a perfectly reasonable suggestion because you are old enough to know exactly what you are doing, thank you very much."},
    {"id": "elder-pick-side", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Pick a Side", "objective": "Insert yourself into a harmless disagreement between two Clanmates and passionately support whichever side you find funniest."},
    {"id": "elder-life-advice", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Life Advice Nobody Requested", "objective": "Tell another cat what you would have done in their situation, preferably with enough confidence to suggest there is absolutely no alternative."},
    {"id": "elder-legacy", "role": "Elders", "eligible_ranks": ["Elder"], "title": "Legacy Lesson", "objective": "Teach a younger Clanmate something you genuinely want remembered after you are gone, whether it is a skill, story, tradition, joke, location, or piece of wisdom."},

    # Existing specialist/leadership/nursery pools stay in rotation too.
    {"id": "med-sort", "role": "Medicine Team", "eligible_ranks": ["Medicine Cat", "Medicine Cat Apprentice", "Healer"], "title": "Herb Shelf Check", "objective": "Sort, count, replace, or discuss the condition of the Clan's herb stores."},
    {"id": "med-checkup", "role": "Medicine Team", "eligible_ranks": ["Medicine Cat", "Medicine Cat Apprentice", "Healer"], "title": "Routine Check-In", "objective": "Check on a Clanmate's health, recovery, stress, or general wellbeing in a casual medical RP."},
    {"id": "med-teach", "role": "Medicine Team", "eligible_ranks": ["Medicine Cat", "Medicine Cat Apprentice", "Healer"], "title": "Teach One Herb", "objective": "Teach another cat one useful herb fact, treatment tip, or piece of medical knowledge."},
    {"id": "med-moss", "role": "Medicine Team", "eligible_ranks": ["Medicine Cat", "Medicine Cat Apprentice", "Healer"], "title": "Medicine Den Refresh", "objective": "Refresh moss, nests, water, cobwebs, or another basic medicine-den supply."},
    {"id": "lead-patrol", "role": "Leadership", "eligible_ranks": ["Leader", "Deputy"], "title": "Patrol Planning", "objective": "Roleplay assigning, discussing, or adjusting a patrol based on what the Clan currently needs."},
    {"id": "lead-checkin", "role": "Leadership", "eligible_ranks": ["Leader", "Deputy"], "title": "Open Ears", "objective": "Check in with a Clanmate you do not usually speak to and hear what is on their mind."},
    {"id": "lead-camp", "role": "Leadership", "eligible_ranks": ["Leader", "Deputy"], "title": "Camp Walkthrough", "objective": "Inspect camp, notice one small problem, and talk with another cat about fixing or improving it."},
    {"id": "mid-teach", "role": "Midranks", "eligible_ranks": ["Preymaster", "Pathfinder", "Digger", "Sporekeeper", "River Guardian"], "title": "Pass It On", "objective": "Use your specialty in RP to teach, advise, or demonstrate something to another Clanmate."},
    {"id": "mid-duty", "role": "Midranks", "eligible_ranks": ["Preymaster", "Pathfinder", "Digger", "Sporekeeper", "River Guardian"], "title": "Specialist Duty", "objective": "Complete a casual scene centered on your midrank's normal Clan responsibility."},
    {"id": "mid-help", "role": "Midranks", "eligible_ranks": ["Preymaster", "Pathfinder", "Digger", "Sporekeeper", "River Guardian"], "title": "Specialist Assist", "objective": "Use your role's skills to help another patrol or Clanmate with a small everyday problem."},
    {"id": "nursery-bedding", "role": "Queens and Den Dads", "eligible_ranks": ["Queen", "Den Dad"], "title": "Nest Refresh", "objective": "Refresh nursery bedding or organize a small nursery chore while interacting with another cat."},
    {"id": "nursery-entertain", "role": "Queens and Den Dads", "eligible_ranks": ["Queen", "Den Dad"], "title": "Keep Them Busy", "objective": "Entertain, distract, teach, or settle a restless kit in a casual nursery scene."},
    {"id": "nursery-checkin", "role": "Queens and Den Dads", "eligible_ranks": ["Queen", "Den Dad"], "title": "Nursery Check-In", "objective": "Share a quiet conversation with another nursery cat about kits, Clan life, or how everyone is coping."}
]

ROLE_QUEST_REWARD_WEIGHTS = {
    "full_hunger": 10,
    "hunting_bonus": 8,
    "injury_reduction": 8,
    "hunger_pause": 6,
    "lucky_paw": 10,
    "curious_trinket": 8,
    "bonus_catch": 8,
    "clan_recognition": 8,
    "beautiful_find": 8,
    "well_rested": 8,
    "first_pick": 7,
    "someone_thought": 7,
    "skill_practice": 8,
    "nest_upgrade": 7,
    "starclan_blessing": 2,
    "secret_spot": 6,
    "social_butterfly": 6,
    "mystery_reward": 4
}

ROLE_QUEST_TRINKETS = [
    "an unusual blue-grey feather", "a perfectly smooth striped stone", "a clean shed tooth",
    "a tiny spiral shell", "a rounded piece of harmless Twoleg glass", "a strangely shaped pinecone",
    "an old bell with no collar attached", "a tiny metal button", "a pale bone polished by weather",
    "a crooked twig shaped suspiciously like a tiny antler"
]
ROLE_QUEST_BEAUTIFUL_FINDS = [
    "a spray of tiny wildflowers", "a cluster of colourful leaves", "a stone threaded with sparkling mineral",
    "a nearly perfect feather", "a small piece of naturally shed antler", "a bright patch of soft moss",
    "a smooth shell with pearly colour", "a little bundle of lavender", "a glossy seed pod", "a sun-bleached piece of driftwood"
]
ROLE_QUEST_GIFTS = [
    "a blue jay feather", "a particularly soft tuft of moss", "a tiny white flower", "a polished pebble",
    "a shell", "a bright leaf", "a neat little pinecone", "a small prey feather", "a sprig of lavender"
]
ROLE_QUEST_NEST_UPGRADES = [
    "soft rabbit fur", "fresh pine needles", "particularly fluffy moss", "a feather lining",
    "sprigs of lavender", "smooth stones around the edge", "a little collection of shells",
    "soft dry leaves", "a woven ring of long grass"
]
ROLE_QUEST_SECRET_SPOTS = {
    "BlizzardClan": [
        "a sun-warmed hollow tucked between two pale rocks", "a sheltered ledge where the wind barely reaches",
        "a tiny meltwater pool hidden behind an ice shelf", "an abandoned burrow overlooking the snow"
    ],
    "TorrentClan": [
        "a quiet pool hidden behind a wall of reeds", "a sunny patch of sand above the usual waterline",
        "a sheltered willow-root nook beside the river", "a tiny stream channel full of smooth stones"
    ],
    "FossilClan": [
        "a warm stone shelf hidden between two pillars", "a pocket of wildflowers protected from the wind",
        "a shallow fossil-lined hollow", "a strange old Twoleg object half-buried in the dust"
    ],
    "SpruceClan": [
        "a tiny clearing where sunlight reaches the forest floor", "an abandoned burrow beneath tangled roots",
        "a patch of wildflowers beside a hidden trickle of water", "an excellent flat napping rock beneath the spruce canopy"
    ]
}
ROLE_QUEST_PREY = {
    "BlizzardClan": ["mouse", "pika", "vole", "ptarmigan", "small snowshoe hare"],
    "TorrentClan": ["trout", "perch", "frog", "water vole", "fat minnow"],
    "FossilClan": ["mouse", "vole", "pika", "rock pigeon", "ptarmigan"],
    "SpruceClan": ["squirrel", "sparrow", "water vole", "frog", "minnow"]
}
ROLE_QUEST_TITLES_BY_ROLE = {
    "Kits": ["Tiny Menace", "Camp Favourite"],
    "Apprentices": ["Helpful Paw", "Promising Paw"],
    "Warriors": ["Reliable Clanmate", "Helpful Paw"],
    "Elders": ["Elder Approved", "Clan Treasure"],
    "Medicine Team": ["Gentle Paws", "Herb-Scented Hero"],
    "Leadership": ["Steady Paw", "Camp Favourite"],
    "Midranks": ["Specialist Star", "Reliable Clanmate"],
    "Queens and Den Dads": ["Nursery Favourite", "Helpful Paw"]
}


def role_quest_role_names():
    names = []
    for quest in ROLE_QUEST_PROMPTS:
        role = quest["role"]
        if role not in names:
            names.append(role)
    return names


def migrate_role_quest_usage_tracking():
    data.setdefault("used_role_quests", [])
    data.setdefault("used_role_quest_roles", [])
    data.setdefault("used_role_quests_by_role", {})
    by_id = {quest["id"]: quest for quest in ROLE_QUEST_PROMPTS}
    for quest_id in data.get("used_role_quests", []) or []:
        quest = by_id.get(quest_id)
        if not quest:
            continue
        used_for_role = data["used_role_quests_by_role"].setdefault(quest["role"], [])
        if quest_id not in used_for_role:
            used_for_role.append(quest_id)


def choose_role_quest_roles(count):
    migrate_role_quest_usage_tracking()
    roles = role_quest_role_names()
    selected = []
    used = list(data.get("used_role_quest_roles", []) or [])

    while len(selected) < count and roles:
        available = [role for role in roles if role not in used and role not in selected]
        if not available:
            # The role-category cycle is complete. Start a new category cycle, but
            # do not give both monthly slots to the same role.
            used = []
            data["used_role_quest_roles"] = []
            available = [role for role in roles if role not in selected]
        if not available:
            break
        chosen = random.choice(available)
        selected.append(chosen)
        used.append(chosen)
        data["used_role_quest_roles"] = used.copy()

    return selected


def select_new_role_quest_for_role(role, due_at=None):
    migrate_role_quest_usage_tracking()
    prompts = [quest for quest in ROLE_QUEST_PROMPTS if quest["role"] == role]
    used = data["used_role_quests_by_role"].setdefault(role, [])
    available = [quest for quest in prompts if quest["id"] not in set(used)]
    if not available:
        used.clear()
        available = prompts.copy()

    quest = copy.deepcopy(random.choice(available))
    used.append(quest["id"])
    if quest["id"] not in data["used_role_quests"]:
        data["used_role_quests"].append(quest["id"])
    issued_at = datetime.now(TZ)
    due_at = due_at or next_regular_quest_cycle(issued_at)
    quest.update({"status": "Pending", "issued_at": issued_at.isoformat(), "due_at": due_at.isoformat()})
    return quest


def select_new_role_quests(count=2, due_at=None):
    roles = choose_role_quest_roles(count)
    return [select_new_role_quest_for_role(role, due_at=due_at) for role in roles]


def select_new_role_quest(due_at=None, exclude_roles=None):
    """Choose one replacement role quest without wasting another role's rotation slot."""
    migrate_role_quest_usage_tracking()
    exclude_roles = set(exclude_roles or [])
    roles = role_quest_role_names()
    used_roles = list(data.get("used_role_quest_roles", []) or [])

    # Prefer a role that has not appeared yet in the current role-category cycle,
    # while never duplicating the other active monthly role quest.
    available = [
        role for role in roles
        if role not in exclude_roles and role not in used_roles
    ]

    if not available:
        # If every allowed role has already been used in this category cycle, reroll
        # among allowed roles without clearing the main monthly rotation. This keeps
        # a staff reroll from accidentally consuming or resetting unrelated roles.
        available = [role for role in roles if role not in exclude_roles]

    if not available:
        available = roles.copy()

    role = random.choice(available)
    if role not in used_roles:
        used_roles.append(role)
        data["used_role_quest_roles"] = used_roles

    return select_new_role_quest_for_role(role, due_at=due_at)


def get_active_role_quests():
    raw = data.get("active_role_quests", [])
    if not isinstance(raw, list):
        raw = []
    if not raw and isinstance(data.get("active_role_quest"), dict):
        raw = [data["active_role_quest"]]
        data["active_role_quests"] = raw
    return raw


def set_active_role_quests(quests):
    data["active_role_quests"] = list(quests or [])
    data["active_role_quest"] = data["active_role_quests"][0] if data["active_role_quests"] else None


def archive_role_quest(quest, reason="Expired"):
    if not quest or quest.get("status") == "Completed":
        return
    data.setdefault("role_quest_history", [])
    archived = copy.deepcopy(quest)
    archived["status"] = reason
    archived["ended_at"] = datetime.now(TZ).isoformat()
    archived["result"] = "No penalty. Role-specific quests are always optional."
    data["role_quest_history"].append(archived)
    data["role_quest_history"] = data["role_quest_history"][-120:]


def archive_active_role_quests(reason="Expired"):
    for quest in list(get_active_role_quests()):
        archive_role_quest(quest, reason=reason)


def archive_active_role_quest(reason="Expired"):
    # Backward-compatible wrapper for older call sites.
    archive_active_role_quests(reason=reason)


def format_role_quest_block(quest, index=None, total=None):
    if not quest:
        return ""
    ranks = ", ".join(quest.get("eligible_ranks", []))
    slot_text = f" #{index}" if index is not None and (total or 0) > 1 else ""
    return "\n".join([
        "━━━━━━━━━━━━━━━",
        f"🌟 **OPTIONAL ROLE-SPECIFIC QUEST{slot_text}**",
        f"### {quest.get('role', 'Clan Cats')}: {quest.get('title', 'Role Quest')}",
        f"**Eligible ranks:** {ranks}",
        quest.get("objective", "Complete a casual Clan-life RP prompt."),
        "",
        "Any eligible living OC from **any Clan** may complete this quest.",
        "🎁 **Reward:** The OC who completes it receives one random personal reward, keeps their quest streak moving, and may earn extra milestone rewards at 3, 5, and 10 completions.",
        "🍀 Rewards range from hunger/roll bonuses and injury protection to trinkets, prey, nest upgrades, temporary titles, secret spots, gifts, skill practice, Connection Tokens, rare StarClan luck, and mystery rewards.",
        "💚 **Optional:** Nothing bad happens if nobody completes this quest."
    ])


def role_quest_cat_is_eligible(cat, quest):
    if str(cat.get("status", "Alive")).casefold() == "dead":
        return False
    if cat.get("clan") not in CLAN_NAMES_ONLY:
        return False
    return cat.get("rank") in set(quest.get("eligible_ranks", []))


def add_role_quest_collectible(cat, item, source, category="Keepsake"):
    cat.setdefault("role_quest_collectibles", [])
    cat["role_quest_collectibles"].append({
        "item": item,
        "category": category,
        "source": source,
        "moon": int(data.get("moon", 0)),
        "earned_at": datetime.now(TZ).isoformat()
    })
    cat["role_quest_collectibles"] = cat["role_quest_collectibles"][-40:]


def role_quest_random_prey(cat):
    return random.choice(ROLE_QUEST_PREY.get(cat.get("clan"), ["mouse", "vole", "small bird"]))


def infer_role_quest_skill(quest):
    text = f"{quest.get('title', '')} {quest.get('objective', '')}".casefold()
    checks = [
        (["hunt", "prey", "stalk"], "Hunting Practice"),
        (["battle", "fight", "strength"], "Fighting Practice"),
        (["race", "speed", "chase"], "Speed Practice"),
        (["track", "patrol", "border", "scent"], "Tracking Practice"),
        (["swim", "fish", "water"], "Swimming/Fishing Practice"),
        (["climb", "ledge"], "Climbing/Balance Practice"),
        (["herb", "medicine", "health"], "Medicine Practice"),
        (["teach", "lesson", "story", "advice"], "Teaching/Social Practice")
    ]
    for keywords, label in checks:
        if any(keyword in text for keyword in keywords):
            return label
    return "General Clan Skill Practice"


def apply_mystery_role_quest_reward(cat_name, cat, quest):
    source = quest.get("title", "Role Quest")
    outcomes = ["round_rock", "rare_feather", "large_prey", "lucky", "nest", "title", "beautiful"]
    outcome = random.choice(outcomes)
    if outcome == "round_rock":
        item = "a strangely round rock"
        add_role_quest_collectible(cat, item, source, category="Mystery Reward")
        return f"🎁 **MYSTERY REWARD!** {cat_name} has found... **{item}**. It appears to serve absolutely no purpose. It is theirs now."
    if outcome == "rare_feather":
        item = random.choice(["an immaculate owl feather", "a shimmering magpie feather", "a huge raven feather", "a pale hawk feather"])
        add_role_quest_collectible(cat, item, source, category="Mystery Reward")
        return f"🎁 **MYSTERY REWARD!** {cat_name} found **{item}** and may keep, gift, or decorate with it."
    if outcome == "large_prey":
        prey = role_quest_random_prey(cat)
        cat.setdefault("role_quest_bonus_catches", []).append({"prey": f"especially large {prey}", "moon": int(data.get("moon", 0)), "source": source})
        cat["role_quest_bonus_catches"] = cat["role_quest_bonus_catches"][-20:]
        return f"🎁 **MYSTERY REWARD!** {cat_name} comes across an **especially large {prey}** to bring back to camp."
    if outcome == "lucky":
        cat["role_quest_lucky_paw_charges"] = int(cat.get("role_quest_lucky_paw_charges", 0) or 0) + 1
        return f"🎁 **MYSTERY REWARD!** {cat_name} gains **Lucky Paw**, worth **+1 on one future hunting attempt**."
    if outcome == "nest":
        item = random.choice(ROLE_QUEST_NEST_UPGRADES)
        cat.setdefault("role_quest_nest_upgrades", []).append({"item": item, "moon": int(data.get("moon", 0)), "source": source})
        cat["role_quest_nest_upgrades"] = cat["role_quest_nest_upgrades"][-20:]
        return f"🎁 **MYSTERY REWARD!** {cat_name} earns a nest upgrade: **{item}**."
    if outcome == "title":
        title = random.choice(ROLE_QUEST_TITLES_BY_ROLE.get(quest.get("role"), ["Camp Favourite"]))
        cat["role_quest_title"] = {"title": title, "expires_moon": int(data.get("moon", 0)) + 1, "source": source}
        return f"🎁 **MYSTERY REWARD!** {cat_name} gains the temporary reputation title **{title}** for roughly one moon."
    item = random.choice(ROLE_QUEST_BEAUTIFUL_FINDS)
    add_role_quest_collectible(cat, item, source, category="Mystery Reward")
    return f"🎁 **MYSTERY REWARD!** {cat_name} discovers **{item}**."


def apply_role_quest_reward(cat_name, cat, quest):
    reward_names = list(ROLE_QUEST_REWARD_WEIGHTS.keys())
    reward = random.choices(
        reward_names,
        weights=[ROLE_QUEST_REWARD_WEIGHTS[name] for name in reward_names],
        k=1
    )[0]
    now = datetime.now(TZ)
    source = quest.get("title", "Role Quest")

    if reward == "full_hunger":
        old_hunger = get_hunger_status(cat)
        cat["hunger_level"] = "Full"
        cat["last_fed"] = now.isoformat()
        cat["last_hunger_update"] = now.isoformat()
        text = f"🍽️ **Full Belly:** {cat_name}'s hunger was set from **{old_hunger}** to **Full**."
    elif reward == "hunting_bonus":
        cat["role_quest_hunting_bonus"] = {"modifier": 2, "moon": int(data.get("moon", 0)), "source": source}
        text = f"🎯 **Hunter's Edge:** {cat_name} gets **+2 to hunting rolls** for the remainder of **Moon {data.get('moon', 0)}**."
    elif reward == "injury_reduction":
        cat["role_quest_injury_reduction_charges"] = int(cat.get("role_quest_injury_reduction_charges", 0) or 0) + 1
        text = f"🩹 **Protective Luck:** The next injury or illness {cat_name} receives is automatically **1 severity lower** (minimum 1)."
    elif reward == "hunger_pause":
        pause_until = now + timedelta(days=7)
        existing_until = role_quest_hunger_pause_remaining(cat, now)
        if existing_until and existing_until > pause_until:
            pause_until = existing_until
        cat["role_quest_hunger_pause_until"] = pause_until.isoformat()
        text = f"🌙 **Rested Stomach:** {cat_name}'s hunger decay is paused for **7 days**, until {discord_expiry_timestamp(pause_until)}."
    elif reward == "lucky_paw":
        cat["role_quest_lucky_paw_charges"] = int(cat.get("role_quest_lucky_paw_charges", 0) or 0) + 1
        text = f"🍀 **Lucky Paw:** {cat_name} banks a one-use **+1 bonus on a future hunting attempt**."
    elif reward == "curious_trinket":
        item = random.choice(ROLE_QUEST_TRINKETS)
        add_role_quest_collectible(cat, item, source, category="Curious Trinket")
        text = f"🪶 **Curious Trinket:** While finishing the quest, {cat_name} finds **{item}**. It has been added to their quest keepsakes."
    elif reward == "bonus_catch":
        prey = role_quest_random_prey(cat)
        cat.setdefault("role_quest_bonus_catches", []).append({"prey": prey, "moon": int(data.get("moon", 0)), "source": source})
        cat["role_quest_bonus_catches"] = cat["role_quest_bonus_catches"][-20:]
        text = f"🐭 **Bonus Catch:** On the way home, {cat_name} comes across **a {prey}** and automatically brings it back to camp."
    elif reward == "clan_recognition":
        title = random.choice(ROLE_QUEST_TITLES_BY_ROLE.get(quest.get("role"), ["Camp Favourite"]))
        cat["role_quest_title"] = {"title": title, "expires_moon": int(data.get("moon", 0)) + 1, "source": source}
        cat.setdefault("role_quest_accomplishments", []).append(f"Moon {data.get('moon', 0)}: earned the temporary title {title}")
        text = f"⭐ **Clan Recognition:** {cat_name}'s helpfulness earns them the temporary reputation tag **{title}** for roughly one moon."
    elif reward == "beautiful_find":
        item = random.choice(ROLE_QUEST_BEAUTIFUL_FINDS)
        add_role_quest_collectible(cat, item, source, category="Beautiful Find")
        text = f"🌿 **A Beautiful Find:** {cat_name} discovers **{item}** to keep, decorate with, or give away in RP."
    elif reward == "well_rested":
        cat["role_quest_well_rested_charges"] = int(cat.get("role_quest_well_rested_charges", 0) or 0) + 1
        label = "Actually Took a Nap" if quest.get("role") == "Kits" else "Well Rested"
        text = f"💤 **{label}:** {cat_name} banks a one-use **+1 bonus for a future hunting, fishing, or similar physical roll**."
    elif reward == "first_pick":
        prey = role_quest_random_prey(cat)
        cat.setdefault("role_quest_bonus_catches", []).append({"prey": f"first-pick {prey}", "moon": int(data.get("moon", 0)), "source": source})
        cat["role_quest_bonus_catches"] = cat["role_quest_bonus_catches"][-20:]
        text = f"🍖 **First Pick:** For helping around camp, {cat_name} gets first choice of the fresh-kill pile and claims **an especially nice {prey}**."
    elif reward == "someone_thought":
        item = random.choice(ROLE_QUEST_GIFTS)
        add_role_quest_collectible(cat, item, source, category="Anonymous Gift")
        text = f"💌 **Someone Thought of You:** {cat_name} returns to their nest to find **{item}** tucked carefully beside their bedding. Whoever left it did not stick around to take credit."
    elif reward == "skill_practice":
        skill = infer_role_quest_skill(quest)
        skills = cat.setdefault("role_quest_skill_progress", {})
        skill_gain = 2 if cat_has_connection_perk(cat, "quick-study") else 1
        skills[skill] = int(skills.get(skill, 0) or 0) + skill_gain
        if skill_gain == 2:
            text = f"🐾 **Skill Practice + Quick Study:** {cat_name} gains **+2 {skill} points** from what they practised during the quest."
        else:
            text = f"🐾 **Skill Practice:** {cat_name} gains **+1 {skill} point** from what they practised during the quest. These are deliberately tiny RP progress markers, not large roll boosts."
    elif reward == "nest_upgrade":
        item = random.choice(ROLE_QUEST_NEST_UPGRADES)
        cat.setdefault("role_quest_nest_upgrades", []).append({"item": item, "moon": int(data.get("moon", 0)), "source": source})
        cat["role_quest_nest_upgrades"] = cat["role_quest_nest_upgrades"][-20:]
        text = f"🪺 **Nest Upgrade:** {cat_name}'s sleeping space gains **{item}**."
    elif reward == "starclan_blessing":
        cat["role_quest_starclan_luck_charges"] = int(cat.get("role_quest_starclan_luck_charges", 0) or 0) + 1
        text = f"🌙 **StarClan's Little Blessing — Rare:** Nothing speaks to {cat_name}, and no prophecy comes. For reasons they cannot quite explain, today simply feels lucky. They bank **+1 on one future hunting or fishing roll**."
    elif reward == "secret_spot":
        spot = random.choice(ROLE_QUEST_SECRET_SPOTS.get(cat.get("clan"), ["a quiet hidden hollow they had never noticed before"]))
        cat.setdefault("role_quest_secret_spots", []).append({"spot": spot, "moon": int(data.get("moon", 0)), "source": source})
        cat["role_quest_secret_spots"] = cat["role_quest_secret_spots"][-12:]
        text = f"🗺️ **Secret Spot Discovered:** {cat_name} finds **{spot}**. It is now theirs to reuse as an RP location whenever they want."
    elif reward == "social_butterfly":
        cat["role_quest_connection_tokens"] = int(cat.get("role_quest_connection_tokens", 0) or 0) + 1
        text = f"🤝 **Social Butterfly:** {cat_name} earns a **Connection Token** for creating RP with another character. They now have **{cat['role_quest_connection_tokens']}**."
    else:
        text = apply_mystery_role_quest_reward(cat_name, cat, quest)

    # Quest streaks are attached to the OC and never create a penalty. Since the
    # monthly role prompts are not assigned to an OC in advance, the streak tracks
    # completed role quests rather than resetting somebody for simply sitting one out.
    cat["role_quest_streak"] = int(cat.get("role_quest_streak", 0) or 0) + 1
    cat["role_quest_total_completed"] = int(cat.get("role_quest_total_completed", 0) or 0) + 1
    milestones = cat.setdefault("role_quest_streak_milestones", [])
    streak = cat["role_quest_streak"]
    milestone_text = None
    if streak >= 10 and 10 not in milestones:
        milestones.append(10)
        cat["role_quest_starclan_luck_charges"] = int(cat.get("role_quest_starclan_luck_charges", 0) or 0) + 1
        special_item = "a small moon-pale stone kept as a Quest Legend keepsake"
        add_role_quest_collectible(cat, special_item, source, category="10-Quest Milestone")
        cat.setdefault("role_quest_accomplishments", []).append("Completed 10 role-specific quests")
        milestone_text = f"🌟 **10-Quest Milestone:** {cat_name} earns a special **Quest Legend** accomplishment, {special_item}, and one StarClan luck charge."
    elif streak >= 5 and 5 not in milestones:
        milestones.append(5)
        milestone_text = "🌟 **5-Quest Streak:** Uncommon bonus unlocked! " + apply_mystery_role_quest_reward(cat_name, cat, quest)
    elif streak >= 3 and 3 not in milestones:
        milestones.append(3)
        cat["role_quest_lucky_paw_charges"] = int(cat.get("role_quest_lucky_paw_charges", 0) or 0) + 1
        milestone_text = f"🌟 **3-Quest Streak:** {cat_name} earns an extra **Lucky Paw** charge."

    cat.setdefault("role_quest_accomplishments", []).append(f"Moon {data.get('moon', 0)}: completed {source}")
    cat["role_quest_accomplishments"] = cat["role_quest_accomplishments"][-40:]
    add_history(cat, f"Completed optional role quest: {source}")

    if milestone_text:
        text += "\n" + milestone_text
    return text


def format_quest_block(group, quest):
    category = quest.get("category", "quest")
    icon = QUEST_CATEGORY_ICONS.get(category, "📜")
    category_label = QUEST_CATEGORY_LABELS.get(category, "Quest")

    lines = [
        "━━━━━━━━━━━━━━━",
        clan_mention(group),
        f"**{group.upper()} QUEST**",
        f"{icon} **{category_label}: {quest['title']}**",
        "",
        quest["objective"],
        quest["description"],
        "",
        f"✅ **If Completed:** {quest['reward_text']}",
        f"⚠️ **If Failed/Ignored:** {quest['failure_text']}"
    ]

    return "\n".join(lines)


def build_quest_announcement(due_at=None, apply_failures=True, forced=False, skipped_schedule=None):
    reset_legacy_quest_data_if_needed()
    clean_expired_quest_effects()

    issued_at = datetime.now(TZ)

    if due_at is None:
        due_at = next_regular_quest_cycle(issued_at)

    if apply_failures:
        failed_results = complete_pending_failures()
    else:
        failed_results = []
        data.setdefault("quest_history_v2", [])

        for old_group, old_quest in list(data.get("active_quests_v2", {}).items()):
            if not old_quest:
                continue

            archived_quest = copy.deepcopy(old_quest)
            archived_quest["status"] = "Cleared"
            archived_quest["cleared_at"] = issued_at.isoformat()
            archived_quest["clear_reason"] = "Replaced by forced quest cycle. No failure penalty was applied."
            archived_quest.setdefault("group", old_group)
            data["quest_history_v2"].append(archived_quest)

    data["active_quests_v2"] = {}

    if forced:
        lines = [
            "🌙 **New quests have been forced...**",
            "",
            "The current active quests have been cleared and replaced. No failure penalties were applied for the cleared quests.",
            f"These replacement quests are due by **{due_at.strftime('%B %d, %Y')}**, keeping the regular first-of-the-month quest schedule intact.",
            ""
        ]

        if skipped_schedule:
            lines.extend([
                f"Because this reset happened within **{QUEST_FORCE_SKIP_DAYS} days** of the next scheduled quest cycle, the **{skipped_schedule.strftime('%B %d, %Y')}** automatic reset will be skipped.",
                ""
            ])
    else:
        lines = [
            "🌙 **A new month of quests begins...**",
            "",
            "New quests and story events are now available for every Clan and the Outsiders! Each set stays active for the full month, until the next first-of-the-month reset.",
            f"These quests are due by **{due_at.strftime('%B %d, %Y')}**.",
            "",
            "Quest roll chances: **35% Hunting**, **20% Social**, **20% Herb Patrol**, **10% Sickness/Crisis**, **15% Wild Animal Event**. Social, herb patrol, and sickness/crisis events will not repeat twice in a row for the same group.",
            ""
        ]

    if failed_results:
        lines.extend([
            "━━━━━━━━━━━━━━━",
            "⚠️ **PREVIOUS QUEST CONSEQUENCES**"
        ])

        for result in failed_results:
            lines.extend([
                f"{clan_mention(result['group'])}",
                f"Previous Quest/Event Failed: **{result['title']}**",
                f"Consequence: {result['penalty']}",
                ""
            ])

    for group in QUEST_GROUP_ORDER:
        quest = select_new_quest(group)
        quest["issued_at"] = issued_at.isoformat()
        quest["due_at"] = due_at.isoformat()
        data["active_quests_v2"][group] = quest
        lines.append(format_quest_block(group, quest))

    # Starting September 1, 2026, two different role categories receive optional
    # prompts each month. The role-category cycle and each role's prompt pool both
    # exhaust themselves before repeating. August keeps its original single quest.
    archive_active_role_quests("Cleared" if forced else "Expired")
    role_count = 2 if issued_at.date() >= ROLE_QUEST_DOUBLE_START else 1
    role_quests = select_new_role_quests(count=role_count, due_at=due_at)
    set_active_role_quests(role_quests)
    for index, role_quest in enumerate(role_quests, start=1):
        lines.extend(["", format_role_quest_block(role_quest, index=index, total=len(role_quests))])

    return "\n".join(lines)


def build_quest_reminder(days_remaining):
    reset_legacy_quest_data_if_needed()

    lines = [
        f"⏳ **Quest Reminder: {days_remaining} days remaining!**",
        "",
        "The current monthly quest cycle is still active. Complete your group's quest or story event before the next first-of-the-month reset to earn the reward and avoid possible consequences.",
        ""
    ]

    for group in QUEST_GROUP_ORDER:
        quest = data.get("active_quests_v2", {}).get(group)

        if not quest or quest.get("status") != "Pending":
            continue

        lines.extend([
            "━━━━━━━━━━━━━━━",
            clan_mention(group),
            f"**{quest.get('title', 'Current Quest')}**",
            f"Category: **{QUEST_CATEGORY_LABELS.get(quest.get('category'), 'Quest')}**",
            quest.get("objective", "Complete the current quest."),
            ""
        ])

    role_quests = [quest for quest in get_active_role_quests() if quest and quest.get("status") == "Pending"]
    for index, role_quest in enumerate(role_quests, start=1):
        lines.extend(["", format_role_quest_block(role_quest, index=index, total=len(role_quests)), ""])

    return "\n".join(lines)


async def send_quest_announcement(channel, message):
    await send_long_message(channel, message)


@tasks.loop(minutes=30)
async def quest_reminders():
    now = datetime.now(TZ)

    if now.hour != QUEST_SCHEDULE_HOUR:
        return

    async with data_lock:
        reset_legacy_quest_data_if_needed()

        active = data.get("active_quests_v2", {})
        pending = [quest for quest in active.values() if quest and quest.get("status") == "Pending"]

        if not pending:
            return

        try:
            first_due = min(datetime.fromisoformat(quest["due_at"]) for quest in pending if quest.get("due_at"))
        except Exception:
            return

        days_remaining = (first_due.date() - now.date()).days

        if days_remaining not in [14, 7, 3]:
            return

        reminder_key = f"{first_due.date().isoformat()}-{days_remaining}"
        data.setdefault("quest_reminders_sent_v2", {})

        if data["quest_reminders_sent_v2"].get(reminder_key):
            return

        data["quest_reminders_sent_v2"][reminder_key] = True
        message = build_quest_reminder(days_remaining)
        save_data(data)

    channel = bot.get_channel(QUEST_CHANNEL_ID)

    if channel:
        await send_long_message(channel, message)


def quest_period_key(dt):
    return f"{dt.year}-{dt.month:02d}"


def is_regular_quest_cycle(dt):
    """The automatic quest reset happens on the first of every month."""
    return dt.day == 1


def next_regular_quest_cycle(after_time):
    """Return the next first-of-the-month quest reset at 9 AM Toronto time."""
    this_month_start = datetime(
        after_time.year,
        after_time.month,
        1,
        QUEST_SCHEDULE_HOUR,
        QUEST_SCHEDULE_MINUTE,
        tzinfo=TZ
    )

    if this_month_start > after_time:
        return this_month_start

    if after_time.month == 12:
        next_year = after_time.year + 1
        next_month = 1
    else:
        next_year = after_time.year
        next_month = after_time.month + 1

    return datetime(
        next_year,
        next_month,
        1,
        QUEST_SCHEDULE_HOUR,
        QUEST_SCHEDULE_MINUTE,
        tzinfo=TZ
    )


def broaden_current_hunting_quests_once():
    """Replace already-active species-specific hunting quests with broad equivalents once."""
    if data.get("broad_hunting_quest_migration_v1"):
        return []
    reset_legacy_quest_data_if_needed()
    changed = []
    for group, old_quest in list(data.get("active_quests_v2", {}).items()):
        if not old_quest or old_quest.get("status") != "Pending":
            continue
        if old_quest.get("category") != "hunting" or old_quest.get("broad_hunting"):
            continue
        due_at = old_quest.get("due_at")
        issued_at = old_quest.get("issued_at")
        old_title = old_quest.get("title", "Old Hunting Quest")
        new_quest = select_new_quest(group, preferred_category="hunting")
        if due_at:
            new_quest["due_at"] = due_at
        if issued_at:
            new_quest["issued_at"] = issued_at
        new_quest["migrated_from"] = old_title
        data["active_quests_v2"][group] = new_quest
        changed.append((group, old_title, copy.deepcopy(new_quest)))
    data["broad_hunting_quest_migration_v1"] = True
    return changed


def ensure_role_quest_rollout_once():
    """Introduce role quests once without changing August into a two-quest cycle early."""
    if data.get("role_quest_rollout_v1"):
        return []
    reset_legacy_quest_data_if_needed()
    data["role_quest_rollout_v1"] = True
    if get_active_role_quests():
        return []
    due_at = get_current_quest_cycle_due_at()
    count = 2 if datetime.now(TZ).date() >= ROLE_QUEST_DOUBLE_START else 1
    quests = select_new_role_quests(count=count, due_at=due_at)
    set_active_role_quests(quests)
    return copy.deepcopy(quests)


async def migrate_active_quests_to_monthly_schedule():
    """One-time migration so already-active 2-week quests become due next month instead of on an old Tuesday."""
    async with data_lock:
        if data.get("monthly_quest_schedule_migrated_v1"):
            return

        reset_legacy_quest_data_if_needed()
        next_due = next_regular_quest_cycle(datetime.now(TZ))
        changed = False

        for quest in data.get("active_quests_v2", {}).values():
            if not quest or quest.get("status") != "Pending":
                continue
            quest["due_at"] = next_due.isoformat()
            changed = True

        for quest in get_active_role_quests():
            if not quest or quest.get("status") != "Pending":
                continue
            quest["due_at"] = next_due.isoformat()
            changed = True

        data["quest_reminders_sent_v2"] = {}
        data["monthly_quest_schedule_migrated_v1"] = True
        save_data(data)

        if changed:
            print(f"Migrated active quests to the monthly schedule. New due date: {next_due.isoformat()}")


def forced_quest_due_date(now):
    next_cycle = next_regular_quest_cycle(now)
    days_until_next_cycle = (next_cycle.date() - now.date()).days

    if days_until_next_cycle <= QUEST_FORCE_SKIP_DAYS:
        skipped_cycle = next_cycle
        due_at = next_regular_quest_cycle(skipped_cycle + timedelta(seconds=1))
        return due_at, skipped_cycle

    return next_cycle, None


@tasks.loop(minutes=30)
async def monthly_quest_report():
    now = datetime.now(TZ)

    if now.hour != QUEST_SCHEDULE_HOUR:
        return

    if not is_regular_quest_cycle(now):
        return

    quest_period = quest_period_key(now)

    async with data_lock:
        reset_legacy_quest_data_if_needed()

        if data.get("last_quest_period_v2") == quest_period:
            return

        due_at = next_regular_quest_cycle(now)
        data["last_quest_period_v2"] = quest_period
        data["quest_reminders_sent_v2"] = {}
        message = build_quest_announcement(due_at=due_at)
        save_data(data)

    channel = bot.get_channel(QUEST_CHANNEL_ID)

    if channel:
        await send_quest_announcement(channel, message)



# Numerical progress tracking for monthly hunting quests. Older active hunting
# quests are upgraded lazily so a deployment does not wipe the current moon.
QUEST_PREY_CATEGORIES = {
    "birds": {
        "bird", "birds", "sparrow", "sparrows", "pigeon", "pigeons", "rock pigeon", "rock pigeons",
        "ptarmigan", "ptarmigans", "starling", "starlings", "gull", "gulls", "finch", "finches",
        "lark", "larks", "robin", "robins", "blue jay", "blue jays", "woodpecker", "woodpeckers",
        "crow", "crows", "magpie", "magpies", "rock wren", "rock wrens", "red-winged blackbird", "red-winged blackbirds",
        "blackbird", "blackbirds", "nestling bird", "nestling birds", "duck", "ducks", "duckling", "ducklings", "loon", "loons",
        "coot", "coots", "kingfisher", "kingfishers", "heron", "herons", "canada goose",
        "canada geese", "goose", "geese", "nighthawk", "nighthawks", "owl", "owls", "vulture",
        "vultures", "hawk", "hawks", "red-tailed hawk", "red-tailed hawks", "peregrine falcon",
        "peregrine falcons", "falcon", "falcons", "golden eagle", "golden eagles", "eagle", "eagles"
    },
    "fish": {
        "fish", "trout", "trouts", "cutthroat trout", "bull trout", "perch", "arctic char", "char",
        "mountain whitefish", "whitefish", "minnow", "minnows", "walleye", "walleyes", "catfish"
    },
    "small prey": {
        "small prey", "mouse", "mice", "vole", "voles", "water vole", "water voles", "shrew", "shrews",
        "common shrew", "common shrews", "pika", "pikas", "squirrel", "squirrels", "red squirrel",
        "red squirrels", "chipmunk", "chipmunks", "snowshoe hare", "snowshoe hares", "hare", "hares",
        "marmot", "marmots", "frog", "frogs", "bat", "bats", "salamander", "salamanders", "spotted salamander",
        "spotted salamanders", "garter snake", "garter snakes", "snake", "snakes", "turtle", "turtles",
        "crayfish", "rat", "rats", "barn rat", "barn rats"
    }
}


def normalize_quest_prey_name(prey):
    clean = re.sub(r"\s+", " ", str(prey or "").strip().casefold().replace("’", "'"))
    for article in ("a ", "an ", "the "):
        if clean.startswith(article):
            clean = clean[len(article):].strip()
            break
    return clean


def classify_quest_prey(prey):
    clean = normalize_quest_prey_name(prey)
    for category, names in QUEST_PREY_CATEGORIES.items():
        if clean in names:
            return category
    return None


def ensure_hunting_quest_progress(quest):
    if not isinstance(quest, dict) or quest.get("category") != "hunting":
        return None

    try:
        required = int(quest.get("hunt_required", 0) or 0)
    except (TypeError, ValueError):
        required = 0

    if required <= 0:
        objective = str(quest.get("objective") or "")
        match = re.search(r"Catch\s+\*\*(\d+)", objective, flags=re.IGNORECASE)
        if not match:
            match = re.search(r"Catch\s+(\d+)", str(quest.get("title") or ""), flags=re.IGNORECASE)
        required = int(match.group(1)) if match else 1
        quest["hunt_required"] = required

    target = str(quest.get("hunt_target") or quest.get("effect", {}).get("target") or "small prey").strip().casefold()
    if target not in QUEST_PREY_CATEGORIES:
        target = "small prey"
    quest["hunt_target"] = target

    site = str(quest.get("hunt_site") or "").strip()
    if not site:
        objective = str(quest.get("objective") or "")
        site_match = re.search(r"at\s+\*\*([^*]+)\*\*", objective, flags=re.IGNORECASE)
        if site_match:
            site = site_match.group(1).strip()
            quest["hunt_site"] = site

    catches = quest.get("hunt_catches")
    if not isinstance(catches, list):
        catches = []
        quest["hunt_catches"] = catches

    return required, target, catches


def hunt_location_key(name):
    clean = str(name or "").casefold().replace("’", "'").strip()
    clean = re.sub(r"[^a-z0-9]+", "", clean)
    if clean.startswith("the"):
        clean = clean[3:]
    return clean


def hunting_quest_channel_id(quest):
    progress = ensure_hunting_quest_progress(quest)
    if not progress:
        return None
    site_key = hunt_location_key(quest.get("hunt_site"))
    if not site_key:
        return None
    for channel_id, info in HUNT_CHANNELS.items():
        if hunt_location_key(info.get("location")) == site_key:
            return channel_id
    return None


def hunting_quest_contributor_counts(quest):
    progress = ensure_hunting_quest_progress(quest)
    counts = {}
    if not progress:
        return counts
    for catch in progress[2]:
        if not isinstance(catch, dict):
            continue
        cat_name = str(catch.get("cat") or "").strip()
        if cat_name:
            counts[cat_name] = counts.get(cat_name, 0) + 1
    return counts


def hunting_quest_progress_bar(current, required, width=10):
    if required <= 0:
        return "░" * width
    filled = min(width, max(0, round((current / required) * width)))
    return "█" * filled + "░" * (width - filled)


def award_hunting_quest_contributor_history(group, quest, final_cat_name=None):
    if quest.get("hunt_contributor_history_awarded"):
        return

    progress = ensure_hunting_quest_progress(quest)
    if not progress:
        return
    required, target, catches = progress
    counts = hunting_quest_contributor_counts(quest)
    if not counts:
        quest["hunt_contributor_history_awarded"] = True
        return

    sole_contributor = len(counts) == 1
    for cat_name, count in counts.items():
        cat = data.get("cats", {}).get(cat_name)
        if not isinstance(cat, dict):
            continue
        prepare_cat_record(cat_name, cat)
        catch_word = "catch" if count == 1 else "catches"
        if final_cat_name == cat_name and sole_contributor and count >= required:
            entry = (
                f"Quest Champion — single-pawedly completed {group}'s monthly hunting quest "
                f"with all {required} {target} catches"
            )
        elif final_cat_name == cat_name:
            entry = (
                f"Quest Finisher — landed the final catch that completed {group}'s monthly hunting quest "
                f"({count} {catch_word} contributed)"
            )
        else:
            entry = (
                f"Quest Hunter — helped complete {group}'s monthly hunting quest "
                f"({count} {catch_word} contributed)"
            )
        add_history(cat, entry)

    quest["hunt_contributor_history_awarded"] = True


def format_hunting_quest_progress(group, quest):
    progress = ensure_hunting_quest_progress(quest)
    if not progress:
        return None
    required, target, catches = progress
    current = min(len(catches), required)
    remaining = max(0, required - current)
    counts = hunting_quest_contributor_counts(quest)
    contributors = ", ".join(
        f"**{name}** ×{count}" for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
    ) or "Nobody yet"
    status = quest.get("status", "Pending")
    return (
        f"### {group}: {quest.get('title', 'Hunting Quest')}\n"
        f"**Status:** {status}\n"
        f"**Target:** {required} {target}\n"
        f"**Progress:** **{current}/{required}** caught • **{remaining} remaining**\n"
        f"`{hunting_quest_progress_bar(current, required)}`\n"
        f"**Contributors:** {contributors}"
    )



# ─────────────────────────────
# CONNECTION TOKENS + PERKS
# ─────────────────────────────
# Monthly Clan/Outsider quests award one Connection Token the first time an OC
# is registered as a contributor, then one more to every registered contributor
# if that quest is successfully completed. This is deliberately per-quest, not
# per catch/message, so the currency cannot be farmed by repeating one action.

CONNECTION_PERKS_LESSER = [
    {"key": "friendly-face", "name": "Friendly Face", "emoji": "🙂", "cost": 2, "effect": "Cats around camp tend to begin with a warmer, more favourable impression of this OC. It never forces another player's reaction."},
    {"key": "gentle-paws", "name": "Gentle Paws", "emoji": "🫶", "cost": 2, "effect": "Known for being especially comforting and careful with upset, frightened, injured, young, or elderly cats."},
    {"key": "good-listener", "name": "Good Listener", "emoji": "👂", "cost": 2, "effect": "Has a reputation for listening without immediately judging; Clanmates may be more inclined to confide in them."},
    {"key": "peacemaker", "name": "Peacemaker", "emoji": "🕊️", "cost": 2, "effect": "Known for cooling down everyday disagreements and helping cats find common ground."},
    {"key": "camp-comedian", "name": "Camp Comedian", "emoji": "😂", "cost": 2, "effect": "Has a reputation for making Clanmates laugh and lightening the mood around camp."},
    {"key": "heartthrob", "name": "Heartthrob", "emoji": "💘", "cost": 2, "effect": "Known for being particularly charming or attractive. Other players may choose for their OCs to notice or develop a crush; attraction is never automatic."},
    {"key": "kit-favourite", "name": "Kit Favourite", "emoji": "🐾", "cost": 2, "effect": "Kits tend to warm up to this OC quickly and may seek them out for games, stories, or attention."},
    {"key": "elder-approved", "name": "Elder Approved", "emoji": "🌿", "cost": 2, "effect": "Has earned a reputation among elders for being respectful, useful, patient, or pleasantly entertaining."},
    {"key": "reliable-paw", "name": "Reliable Paw", "emoji": "✅", "cost": 2, "effect": "Clanmates generally know this OC as someone who follows through when they offer to help."},
    {"key": "natural-teacher", "name": "Natural Teacher", "emoji": "📚", "cost": 2, "effect": "Known for being patient and approachable when showing another cat how to do something."},
    {"key": "storyteller", "name": "Storyteller", "emoji": "📖", "cost": 2, "effect": "Has become known around camp for entertaining, memorable, dramatic, or ridiculous stories."},
    {"key": "gift-giver", "name": "Gift Giver", "emoji": "🎁", "cost": 2, "effect": "Known for remembering others and leaving thoughtful little prey, feathers, flowers, stones, moss, or trinkets."},
    {"key": "calm-presence", "name": "Calm Presence", "emoji": "🌙", "cost": 2, "effect": "Their company tends to feel grounding during ordinary stressful or emotional moments."},
    {"key": "bright-spirit", "name": "Bright Spirit", "emoji": "☀️", "cost": 2, "effect": "Has a cheerful reputation and tends to lift the mood when they arrive."},
    {"key": "welcoming-soul", "name": "Welcoming Soul", "emoji": "🏡", "cost": 2, "effect": "Especially good at making newcomers, found cats, visitors, or awkward Clanmates feel included."},
    {"key": "trustworthy", "name": "Trustworthy", "emoji": "🤝", "cost": 2, "effect": "Has built a reputation for discretion and reliability; cats may be more comfortable trusting them with small responsibilities or personal matters."},
    {"key": "good-sport", "name": "Good Sport", "emoji": "🏅", "cost": 2, "effect": "Known for taking jokes, losses, friendly rivalries, and competitions in stride without becoming a sore loser."},
    {"key": "camp-helper", "name": "Camp Helper", "emoji": "🪹", "cost": 2, "effect": "Frequently noticed lending a paw with the small unglamorous jobs that keep camp running."},
    {"key": "curious-mind", "name": "Curious Mind", "emoji": "🔎", "cost": 2, "effect": "Known for asking questions, investigating odd little details, and genuinely wanting to learn."},
    {"key": "easy-company", "name": "Easy Company", "emoji": "🌼", "cost": 2, "effect": "Has a reputation as an easygoing cat to share a patrol, meal, walk, or quiet afternoon with."},
]

CONNECTION_PERKS_GREATER = [
    {"key": "imposing-figure", "name": "Imposing Figure", "emoji": "⚔️", "cost": 5, "effect": "An intimidating presence. Gain +1 to battle rolls. Other OCs may reasonably find them more threatening, but no player's reaction is forced."},
    {"key": "excellent-hunter", "name": "Excellent Hunter", "emoji": "🎯", "cost": 5, "requires_detail": "the OC's second hunting specialty", "effect": "Choose a second hunting specialty in addition to the OC's normal one. The chosen specialty is saved with the badge on /catinfo."},
    {"key": "great-tracker", "name": "Great Tracker", "emoji": "🐾", "cost": 5, "effect": "Once per moon, use /quest track in a hunting channel to choose one specific prey species that actually lives there instead of receiving a random /hunt result."},
    {"key": "swift-paws", "name": "Swift Paws", "emoji": "💨", "cost": 5, "effect": "Gain +1 to chase and escape rolls where raw speed is the deciding factor."},
    {"key": "sure-footed", "name": "Sure-Footed", "emoji": "🪨", "cost": 5, "effect": "Gain +1 to climbing, balance, and dangerous-footing rolls."},
    {"key": "strong-swimmer", "name": "Strong Swimmer", "emoji": "🌊", "cost": 5, "effect": "Gain +1 to swimming and water-navigation rolls."},
    {"key": "keen-nose", "name": "Keen Nose", "emoji": "👃", "cost": 5, "effect": "Gain +1 to scenting and tracking rolls when following a trail."},
    {"key": "eagle-eye", "name": "Eagle Eye", "emoji": "👁️", "cost": 5, "effect": "Gain +1 to spotting, searching, and visually locating something hidden or distant."},
    {"key": "guardian", "name": "Guardian", "emoji": "🛡️", "cost": 5, "effect": "Gain +1 to a battle roll when the action is specifically being taken to defend another cat from immediate harm."},
    {"key": "ambush-expert", "name": "Ambush Expert", "emoji": "🌑", "cost": 5, "effect": "Gain +1 to a hunting roll when CODY's prey prompt explicitly says the prey is distracted, asleep, unaware, or cannot see the hunter."},
    {"key": "fishers-instinct", "name": "Fisher's Instinct", "emoji": "🐟", "cost": 5, "effect": "Gain +1 to fishing rolls."},
    {"key": "survivalist", "name": "Survivalist", "emoji": "🌲", "cost": 5, "effect": "Gain +1 to rolls made specifically to flee or disengage from predator/threat encounters."},
    {"key": "weatherwise", "name": "Weatherwise", "emoji": "⛈️", "cost": 5, "effect": "Reduce one severe-weather hunting or fishing penalty affecting this OC by 1 point. This cannot turn a penalty into a bonus."},
    {"key": "iron-stomach", "name": "Iron Stomach", "emoji": "🍖", "cost": 5, "effect": "Hunger penalties to physical hunting/fishing rolls are treated as 1 point less severe for this OC, to a minimum penalty of 0."},
    {"key": "quick-study", "name": "Quick Study", "emoji": "🧠", "cost": 5, "effect": "Whenever the role-quest Skill Practice reward is rolled, this OC gains +2 practice points instead of +1."},
    {"key": "battle-instinct", "name": "Battle Instinct", "emoji": "🔥", "cost": 5, "effect": "Once per moon, reroll one failed battle roll and keep the second result."},
    {"key": "lucky-break", "name": "Lucky Break", "emoji": "🍀", "cost": 5, "effect": "Once per moon, add +1 to one non-medical physical roll of the player's choice."},
    {"key": "trailblazer", "name": "Trailblazer", "emoji": "🗺️", "cost": 5, "effect": "Gain +1 to pathfinding, navigation, and finding-safe-route rolls."},
    {"key": "natural-leader", "name": "Natural Leader", "emoji": "⭐", "cost": 5, "effect": "Has a strong reputation for taking charge when things become uncertain. Cats may look to them for direction, but this grants no formal Clan authority."},
    {"key": "famous-face", "name": "Famous Face", "emoji": "✨", "cost": 5, "effect": "Their reputation has spread beyond their immediate circle. Clanmates and cats met at Gatherings may plausibly recognize them by name or reputation; recognition is never forced."},
]

CONNECTION_PERKS = {perk["key"]: perk for perk in CONNECTION_PERKS_LESSER + CONNECTION_PERKS_GREATER}


def normalize_connection_perk_key(value):
    clean = str(value or "").strip().casefold().replace("’", "'")
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    for key, perk in CONNECTION_PERKS.items():
        if clean in {key, normalize_connection_perk_key_name(perk["name"])}:
            return key
    return None


def normalize_connection_perk_key_name(value):
    clean = str(value or "").strip().casefold().replace("’", "'")
    return re.sub(r"[^a-z0-9]+", "-", clean).strip("-")


def cat_connection_perks(cat):
    raw = cat.get("connection_perks", [])
    if not isinstance(raw, list):
        raw = []
        cat["connection_perks"] = raw
    cleaned = []
    seen = set()
    for entry in raw:
        if isinstance(entry, str):
            key = normalize_connection_perk_key(entry)
            detail = None
            moon = None
        elif isinstance(entry, dict):
            key = normalize_connection_perk_key(entry.get("key") or entry.get("name"))
            detail = str(entry.get("detail") or "").strip() or None
            moon = entry.get("moon")
        else:
            continue
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append({"key": key, "detail": detail, "moon": moon})
    cat["connection_perks"] = cleaned
    return cleaned


def cat_has_connection_perk(cat, perk_key):
    canonical = normalize_connection_perk_key(perk_key)
    if not canonical:
        return False
    return any(entry.get("key") == canonical for entry in cat_connection_perks(cat))


def format_connection_perk_badges(cat):
    badges = []
    for entry in cat_connection_perks(cat):
        perk = CONNECTION_PERKS.get(entry.get("key"))
        if not perk:
            continue
        shown = f"{perk['emoji']} {perk['name']}"
        if entry.get("detail"):
            shown += f" ({entry['detail']})"
        badges.append(shown)
    return " • ".join(badges)


def quest_contributor_entries(quest):
    contributors = quest.get("contributors")
    if not isinstance(contributors, list):
        contributors = []
        quest["contributors"] = contributors
    return contributors


def quest_contributor_names(quest):
    names = []
    seen = set()
    for entry in quest_contributor_entries(quest):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("cat") or "").strip()
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        names.append(name)
    return names


def register_monthly_quest_contributor(group, quest, cat_name, cat, owner_id=None):
    contributors = quest_contributor_entries(quest)
    if any(str(entry.get("cat") or "").casefold() == cat_name.casefold() for entry in contributors if isinstance(entry, dict)):
        return False, int(cat.get("role_quest_connection_tokens", 0) or 0)

    contributors.append({
        "cat": cat_name,
        "owner_id": owner_id or oc_owner_id(cat),
        "joined_at": datetime.now(TZ).isoformat(),
        "contribution_token_awarded": True,
    })
    cat["role_quest_connection_tokens"] = int(cat.get("role_quest_connection_tokens", 0) or 0) + 1
    return True, cat["role_quest_connection_tokens"]


def award_monthly_quest_pass_tokens(group, quest):
    if quest.get("connection_pass_tokens_awarded"):
        return []
    awarded = []
    for cat_name in quest_contributor_names(quest):
        cat = data.get("cats", {}).get(cat_name)
        if not isinstance(cat, dict):
            continue
        prepare_cat_record(cat_name, cat)
        cat["role_quest_connection_tokens"] = int(cat.get("role_quest_connection_tokens", 0) or 0) + 1
        awarded.append(cat_name)
    quest["connection_pass_tokens_awarded"] = True
    quest["connection_pass_token_cats"] = awarded
    return awarded


def sync_hunting_contributors_for_tokens(group, quest):
    """Make hunting catches and the generic contributor list agree without double-paying."""
    progress = ensure_hunting_quest_progress(quest)
    if not progress:
        return []
    newly_awarded = []
    existing = {name.casefold() for name in quest_contributor_names(quest)}
    for catch in progress[2]:
        if not isinstance(catch, dict):
            continue
        cat_name = str(catch.get("cat") or "").strip()
        if not cat_name or cat_name.casefold() in existing:
            continue
        cat = data.get("cats", {}).get(cat_name)
        if not isinstance(cat, dict):
            continue
        prepare_cat_record(cat_name, cat)
        added, _balance = register_monthly_quest_contributor(group, quest, cat_name, cat, catch.get("owner_id"))
        if added:
            existing.add(cat_name.casefold())
            newly_awarded.append(cat_name)
    return newly_awarded


def connection_perk_catalog_text():
    lines = [
        "🏅 **CONNECTION PERKS**",
        "",
        "Earn **1 Connection Token** the first time one of your OCs contributes to their Clan/Outsider monthly quest. If that quest succeeds, every registered contributor earns **+1 more**.",
        "",
        "Redeem with `/quest redeemperk`. Redeemed perks become permanent badges on `/catinfo`.",
        "",
        "**RP rule:** reputation perks create an opening for RP, but never force another player's OC to like, trust, fear, recognize, or crush on yours.",
        "**Roll rule:** only **one Greater Perk** may modify the same roll unless staff explicitly says otherwise.",
        "",
        "## 🤍 Lesser Perks — 2 Tokens",
    ]
    for perk in CONNECTION_PERKS_LESSER:
        lines.append(f"{perk['emoji']} **{perk['name']}** — {perk['effect']}")
    lines.extend(["", "## 🌟 Greater Perks — 5 Tokens"])
    for perk in CONNECTION_PERKS_GREATER:
        lines.append(f"{perk['emoji']} **{perk['name']}** — {perk['effect']}")
    return "\n".join(lines)


quest_group = app_commands.Group(
    name="quest",
    description="Quest commands"
)



@quest_group.command(name="progress", description="View current monthly quest progress, including prey still needed")
async def quest_progress(interaction: discord.Interaction):
    async with data_lock:
        reset_legacy_quest_data_if_needed()
        blocks = []

        for group_name in QUEST_GROUP_ORDER:
            quest = data.get("active_quests_v2", {}).get(group_name)
            if not quest:
                blocks.append(f"### {group_name}\nNo active monthly quest right now.")
                continue

            if quest.get("category") == "hunting":
                block = format_hunting_quest_progress(group_name, quest)
                if block:
                    blocks.append(block)
                    continue

            contributor_names = quest_contributor_names(quest)
            contributor_text = ", ".join(f"**{name}**" for name in contributor_names) if contributor_names else "Nobody yet"
            blocks.append(
                f"### {group_name}: {quest.get('title', 'Quest')}\n"
                f"**Category:** {QUEST_CATEGORY_LABELS.get(quest.get('category'), 'Quest')}\n"
                f"**Status:** {quest.get('status', 'Pending')}\n"
                f"**Contributors:** {contributor_text}\n"
                "This quest does not use a numerical prey counter."
            )

    message = "📊 **Monthly Quest Progress**\n\n" + "\n\n━━━━━━━━━━━━━━━\n\n".join(blocks)
    chunks = split_allegiance_text(message, max_length=1850)
    await interaction.response.send_message(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@quest_group.command(name="catch", description="Record prey your OC caught toward their Clan's active hunting quest")
@app_commands.describe(
    cat_name="OC who caught the prey",
    prey="What they caught, for example mouse, trout, frog, sparrow, or vole"
)
async def quest_catch(interaction: discord.Interaction, cat_name: str, prey: str):
    completion_announcement = None

    async with data_lock:
        reset_legacy_quest_data_if_needed()
        resolved_name = resolve_cat_name_casefold(cat_name)
        if not resolved_name:
            await interaction.response.send_message(f"❌ Cat **{cat_name}** was not found.", ephemeral=True)
            return

        cat = data["cats"][resolved_name]
        prepare_cat_record(resolved_name, cat)
        if bool(cat.get("is_npc", False)):
            await interaction.response.send_message("❌ Monthly quest catch credit is for player OCs, not NPCs.", ephemeral=True)
            return
        if cat_is_dead(cat):
            await interaction.response.send_message(f"❌ **{resolved_name}** is not currently a living OC.", ephemeral=True)
            return

        owner_id = oc_owner_id(cat)
        if not is_staff(interaction) and owner_id != str(interaction.user.id):
            await interaction.response.send_message(
                f"❌ You can only record catches for your own OCs. **{resolved_name}** is not registered to you.",
                ephemeral=True
            )
            return

        group_name = cat.get("clan")
        if group_name not in QUEST_GROUP_ORDER:
            group_name = "Outsider" if group_name == "Outsider" else None
        if not group_name:
            await interaction.response.send_message(
                f"❌ I could not match **{resolved_name}** to a Clan/Outsider monthly quest.",
                ephemeral=True
            )
            return

        quest = data.get("active_quests_v2", {}).get(group_name)
        if not quest:
            await interaction.response.send_message(f"❌ **{group_name}** does not currently have an active monthly quest.", ephemeral=True)
            return
        if quest.get("category") != "hunting":
            await interaction.response.send_message(
                f"❌ **{group_name}**'s current quest is **{QUEST_CATEGORY_LABELS.get(quest.get('category'), 'not a hunting quest')}**, so prey cannot be added to it.",
                ephemeral=True
            )
            return
        if quest.get("status") != "Pending":
            await interaction.response.send_message(
                f"❌ **{group_name}**'s hunting quest is already **{quest.get('status', 'finished')}**.",
                ephemeral=True
            )
            return

        required, target, catches = ensure_hunting_quest_progress(quest)
        expected_channel_id = hunting_quest_channel_id(quest)
        if expected_channel_id and interaction.channel_id != expected_channel_id:
            site = quest.get("hunt_site") or "the quest hunting ground"
            await interaction.response.send_message(
                f"❌ This catch needs to be recorded in **{site}** so CODY knows it came from the correct quest location. "
                f"Use `/quest catch` in <#{expected_channel_id}>.",
                ephemeral=True
            )
            return

        prey_name = normalize_quest_prey_name(prey)
        prey_category = classify_quest_prey(prey_name)
        if prey_category is None:
            await interaction.response.send_message(
                f"❌ I don't recognize **{prey}** as quest-counting prey yet. This quest needs **{target}**. "
                "If it should count, staff can add that species to CODY's prey list.",
                ephemeral=True
            )
            return
        if prey_category != target:
            await interaction.response.send_message(
                f"❌ **{prey.title()}** counts as **{prey_category}**, but {group_name}'s current quest needs **{target}**.",
                ephemeral=True
            )
            return

        # Bring any catches already recorded on this still-active quest into the
        # contributor/token system once. This matters when the feature is deployed
        # in the middle of a moon and prevents earlier helpers being left out.
        sync_hunting_contributors_for_tokens(group_name, quest)

        # The first valid catch this OC contributes to this monthly quest earns
        # exactly one Connection Token. Further catches in the same quest do not.
        contribution_token_awarded, token_balance = register_monthly_quest_contributor(
            group_name, quest, resolved_name, cat, owner_id
        )

        catches.append({
            "cat": resolved_name,
            "owner_id": owner_id,
            "prey": prey_name,
            "category": prey_category,
            "recorded_by": str(interaction.user.id),
            "recorded_at": datetime.now(TZ).isoformat()
        })
        current = len(catches)
        remaining = max(0, required - current)
        quest["hunt_catches"] = catches
        data["active_quests_v2"][group_name] = quest

        completed_now = current >= required
        reward_text = None
        if completed_now:
            reward_text = apply_quest_success(group_name, quest)
            quest["status"] = "Completed"
            quest["completed_at"] = datetime.now(TZ).isoformat()
            quest["completed_by"] = resolved_name
            quest["completed_by_owner_id"] = owner_id
            quest["reward_result"] = reward_text
            # Every OC who helped this successful monthly quest earns the second token.
            pass_token_cats = award_monthly_quest_pass_tokens(group_name, quest)
            award_hunting_quest_contributor_history(group_name, quest, final_cat_name=resolved_name)
            data.setdefault("quest_history_v2", []).append(copy.deepcopy(quest))
            data["active_quests_v2"][group_name] = quest

            counts = hunting_quest_contributor_counts(quest)
            contributors = ", ".join(
                f"**{name}** ×{count}" for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
            )
            history_mark = "Quest Champion" if len(counts) == 1 and counts.get(resolved_name, 0) >= required else "Quest Finisher"
            completion_announcement = (
                "🎯 **HUNTING QUEST COMPLETE!**\n"
                f"{clan_mention(group_name)}\n\n"
                f"**{group_name}: {quest.get('title', 'Hunting Quest')}**\n"
                f"The final **{prey_name}** was caught by **{resolved_name}**!\n"
                f"**Progress:** {required}/{required} {target} caught ✅\n"
                f"**Quest Hunters:** {contributors}\n\n"
                f"🏆 **{resolved_name}** earned the **{history_mark}** mark in their OC history for completing the hunt.\n"
                + (f"🤝 **Quest Success:** {', '.join(pass_token_cats)} each earned **+1 Connection Token** for the quest passing.\n" if pass_token_cats else "")
                + f"🎁 **Reward:** {reward_text}"
            )

        save_data(data)

    if completion_announcement:
        channel = bot.get_channel(QUEST_CHANNEL_ID)
        if channel:
            await send_long_message(channel, completion_announcement)
        token_note = " You also earned **+1 Connection Token** for contributing." if contribution_token_awarded else ""
        await interaction.response.send_message(
            f"✅ **{resolved_name}** recorded **{prey_name}** and completed **{group_name}'s hunting quest!** 🎉{token_note}",
            ephemeral=True
        )
    else:
        token_note = (
            f" 🤝 First contribution recorded: **+1 Connection Token** (balance: **{token_balance}**)."
            if contribution_token_awarded else ""
        )
        await interaction.response.send_message(
            f"✅ **{resolved_name}** recorded **{prey_name}** for {group_name}'s hunting quest. "
            f"Progress is now **{current}/{required}** — **{remaining} more {target}** needed.{token_note}",
            ephemeral=True
        )



@quest_group.command(name="contribute", description="Record your OC as a contributor to their current non-hunting monthly quest")
@app_commands.describe(cat_name="Your OC who contributed to the current monthly quest")
async def quest_contribute(interaction: discord.Interaction, cat_name: str):
    async with data_lock:
        reset_legacy_quest_data_if_needed()
        resolved_name = resolve_cat_name_casefold(cat_name)
        if not resolved_name:
            await interaction.response.send_message(f"❌ Cat **{cat_name}** was not found.", ephemeral=True)
            return
        cat = data["cats"][resolved_name]
        prepare_cat_record(resolved_name, cat)
        if bool(cat.get("is_npc", False)):
            await interaction.response.send_message("❌ Connection Tokens are for player OCs, not NPCs.", ephemeral=True)
            return
        if cat_is_dead(cat):
            await interaction.response.send_message(f"❌ **{resolved_name}** is not currently a living OC.", ephemeral=True)
            return
        owner_id = oc_owner_id(cat)
        if not is_staff(interaction) and owner_id != str(interaction.user.id):
            await interaction.response.send_message(
                f"❌ You can only record quest contributions for your own OCs. **{resolved_name}** is not registered to you.",
                ephemeral=True
            )
            return
        group_name = cat.get("clan")
        if group_name not in QUEST_GROUP_ORDER:
            group_name = "Outsider" if group_name == "Outsider" else None
        if not group_name:
            await interaction.response.send_message(f"❌ I could not match **{resolved_name}** to a monthly quest group.", ephemeral=True)
            return
        quest = data.get("active_quests_v2", {}).get(group_name)
        if not quest:
            await interaction.response.send_message(f"❌ **{group_name}** does not currently have an active monthly quest.", ephemeral=True)
            return
        if quest.get("status") != "Pending":
            await interaction.response.send_message(f"❌ **{group_name}**'s current quest is already **{quest.get('status', 'finished')}**.", ephemeral=True)
            return
        if quest.get("category") == "hunting":
            await interaction.response.send_message(
                "🐭 Hunting contributions are registered automatically from a valid `/quest catch`, so use that command instead.",
                ephemeral=True
            )
            return
        added, balance = register_monthly_quest_contributor(group_name, quest, resolved_name, cat, owner_id)
        if not added:
            await interaction.response.send_message(
                f"🤝 **{resolved_name}** is already registered as a contributor to this moon's **{group_name}** quest. "
                "Each OC earns the contribution token only once per monthly quest.",
                ephemeral=True
            )
            return
        data["active_quests_v2"][group_name] = quest
        save_data(data)

    await interaction.response.send_message(
        f"🤝 **Quest Contribution Recorded!**\n**{resolved_name}** helped with **{group_name}'s** current monthly quest and earned **+1 Connection Token**.\n"
        f"**Token balance:** {balance}\n\nIf the quest successfully passes, {resolved_name} will automatically earn **+1 more**.",
        ephemeral=True
    )


@quest_group.command(name="perks", description="View every Connection Token perk and its cost")
async def quest_perks(interaction: discord.Interaction):
    chunks = split_allegiance_text(connection_perk_catalog_text(), max_length=1850)
    await interaction.response.send_message(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@quest_group.command(name="redeemperk", description="Spend Connection Tokens on a permanent perk badge for your OC")
@app_commands.describe(
    cat_name="Your OC redeeming the perk",
    perk="Perk name; start typing to search",
    detail="Only needed when a perk asks you to choose something, such as Excellent Hunter's second specialty"
)
async def quest_redeem_perk(interaction: discord.Interaction, cat_name: str, perk: str, detail: str = ""):
    async with data_lock:
        resolved_name = resolve_cat_name_casefold(cat_name)
        if not resolved_name:
            await interaction.response.send_message(f"❌ Cat **{cat_name}** was not found.", ephemeral=True)
            return
        cat = data["cats"][resolved_name]
        prepare_cat_record(resolved_name, cat)
        if bool(cat.get("is_npc", False)):
            await interaction.response.send_message("❌ Connection Perks are for player OCs, not NPCs.", ephemeral=True)
            return
        if cat_is_dead(cat):
            await interaction.response.send_message(f"❌ **{resolved_name}** is not currently a living OC.", ephemeral=True)
            return
        owner_id = oc_owner_id(cat)
        if not is_staff(interaction) and owner_id != str(interaction.user.id):
            await interaction.response.send_message(
                f"❌ You can only redeem perks for your own OCs. **{resolved_name}** is not registered to you.",
                ephemeral=True
            )
            return
        perk_key = normalize_connection_perk_key(perk)
        perk_info = CONNECTION_PERKS.get(perk_key) if perk_key else None
        if not perk_info:
            await interaction.response.send_message("❌ I couldn't find that perk. Use `/quest perks` to see the full list.", ephemeral=True)
            return
        if cat_has_connection_perk(cat, perk_key):
            await interaction.response.send_message(f"❌ **{resolved_name}** already has **{perk_info['name']}**.", ephemeral=True)
            return
        required_detail = perk_info.get("requires_detail")
        clean_detail = str(detail or "").strip()
        if required_detail and not clean_detail:
            await interaction.response.send_message(
                f"❌ **{perk_info['name']}** needs one extra choice: **{required_detail}**. Run the command again and fill in `detail`.",
                ephemeral=True
            )
            return
        balance = int(cat.get("role_quest_connection_tokens", 0) or 0)
        cost = int(perk_info["cost"])
        if balance < cost:
            await interaction.response.send_message(
                f"❌ **{resolved_name}** has **{balance} Connection Token{'s' if balance != 1 else ''}**, but **{perk_info['name']}** costs **{cost}**.",
                ephemeral=True
            )
            return
        cat["role_quest_connection_tokens"] = balance - cost
        cat_connection_perks(cat).append({
            "key": perk_key,
            "detail": clean_detail or None,
            "moon": int(data.get("moon", 0)),
            "redeemed_at": datetime.now(TZ).isoformat(),
        })
        add_history(cat, f"Connection Perk — redeemed {perk_info['name']}" + (f" ({clean_detail})" if clean_detail else ""))
        save_data(data)
        remaining = cat["role_quest_connection_tokens"]

    detail_line = f"\n**Choice:** {clean_detail}" if clean_detail else ""
    await interaction.response.send_message(
        f"🏅 **PERK REDEEMED!**\n\n{perk_info['emoji']} **{resolved_name} — {perk_info['name']}**{detail_line}\n"
        f"{perk_info['effect']}\n\n💰 **Cost:** {cost} Connection Tokens • **Remaining:** {remaining}\n"
        "This badge is now permanently shown on the OC's `/catinfo` profile."
    )


@quest_redeem_perk.autocomplete("perk")
async def quest_redeem_perk_autocomplete(interaction: discord.Interaction, current: str):
    needle = str(current or "").casefold().strip()
    matches = []
    for perk in CONNECTION_PERKS_LESSER + CONNECTION_PERKS_GREATER:
        label = f"{perk['name']} — {perk['cost']} tokens"
        if not needle or needle in perk["name"].casefold() or needle in perk["effect"].casefold():
            matches.append(app_commands.Choice(name=label[:100], value=perk["key"]))
        if len(matches) >= 25:
            break
    return matches


@quest_group.command(name="track", description="Great Tracker perk: once per moon, choose a specific prey encounter in this hunting channel")
@app_commands.describe(cat_name="Your OC with the Great Tracker perk", prey="Specific prey species to track in this location")
async def quest_track(interaction: discord.Interaction, cat_name: str, prey: str):
    channel_info = HUNT_CHANNELS.get(interaction.channel_id)
    if not channel_info:
        await interaction.response.send_message("❌ `/quest track` only works inside a configured hunting/territory channel.", ephemeral=True)
        return
    location = channel_info["location"]
    if location in NO_PREY_HUNT_PROMPTS:
        await interaction.response.send_message(f"❌ **{location}** is not a prey hunting ground, so Great Tracker cannot select prey here.", ephemeral=True)
        return

    async with data_lock:
        resolved_name = resolve_cat_name_casefold(cat_name)
        if not resolved_name:
            await interaction.response.send_message(f"❌ Cat **{cat_name}** was not found.", ephemeral=True)
            return
        cat = data["cats"][resolved_name]
        prepare_cat_record(resolved_name, cat)
        owner_id = oc_owner_id(cat)
        if not is_staff(interaction) and owner_id != str(interaction.user.id):
            await interaction.response.send_message(f"❌ You can only use Great Tracker for your own OCs.", ephemeral=True)
            return
        if not cat_has_connection_perk(cat, "great-tracker"):
            await interaction.response.send_message(f"❌ **{resolved_name}** has not redeemed the **Great Tracker** perk.", ephemeral=True)
            return
        moon = int(data.get("moon", 0))
        uses = cat.setdefault("connection_perk_moon_uses", {})
        try:
            last_used_moon = int(uses.get("great-tracker", -999))
        except (TypeError, ValueError):
            last_used_moon = -999
        if last_used_moon == moon:
            await interaction.response.send_message(f"❌ **{resolved_name}** already used **Great Tracker** during Moon {moon}.", ephemeral=True)
            return

        available_species = sorted({species for (prompt_location, species) in HUNT_PROMPTS if prompt_location == location})
        requested = str(prey or "").strip().casefold()
        species = next((name for name in available_species if name.casefold() == requested), None)
        if not species:
            shown = ", ".join(available_species)
            await interaction.response.send_message(
                f"❌ **{prey}** is not available to track at **{location}**. Available prey: {shown}",
                ephemeral=True
            )
            return
        prompts = HUNT_PROMPTS.get((location, species), [])
        prompt = random.choice(prompts) if prompts else hunt_fallback_prompt(location, species)
        if location == "Reed Marsh" and species == "Beaver":
            prompt += f"\n\n**If the beaver hunt fails:** {REED_MARSH_BEAVER_FAIL_THREAT}"
        uses["great-tracker"] = moon
        cat["connection_perk_moon_uses"] = uses
        save_data(data)

    await interaction.response.send_message(
        f"🐾 **Great Tracker — {location}**\n**{resolved_name}** deliberately tracks down **{species}**. "
        f"This uses their Great Tracker attempt for **Moon {moon}**.\n\n{prompt}",
        allowed_mentions=discord.AllowedMentions.none()
    )


@quest_track.autocomplete("prey")
async def quest_track_prey_autocomplete(interaction: discord.Interaction, current: str):
    channel_info = HUNT_CHANNELS.get(interaction.channel_id)
    if not channel_info:
        return []
    location = channel_info["location"]
    needle = str(current or "").casefold().strip()
    species = sorted({name for (prompt_location, name) in HUNT_PROMPTS if prompt_location == location})
    return [
        app_commands.Choice(name=name[:100], value=name)
        for name in species if not needle or needle in name.casefold()
    ][:25]


@quest_group.command(name="force", description="Force-post a new quest cycle and keep the monthly schedule")
async def quest_force(interaction: discord.Interaction):
    if not await quest_force_check(interaction):
        return

    async with data_lock:
        reset_legacy_quest_data_if_needed()
        now = datetime.now(TZ)
        due_at, skipped_cycle = forced_quest_due_date(now)

        if skipped_cycle:
            data["last_quest_period_v2"] = quest_period_key(skipped_cycle)

        data["quest_reminders_sent_v2"] = {}
        message = build_quest_announcement(
            due_at=due_at,
            apply_failures=False,
            forced=True,
            skipped_schedule=skipped_cycle
        )
        save_data(data)

    channel = bot.get_channel(QUEST_CHANNEL_ID)

    if channel:
        await send_quest_announcement(channel, message)

        response = f"🌙 New quests forced and posted. They are due on **{due_at.strftime('%B %d, %Y')}**."
        if skipped_cycle:
            response += f" The **{skipped_cycle.strftime('%B %d, %Y')}** automatic reset will be skipped."

        await interaction.response.send_message(response, ephemeral=True)
    else:
        await interaction.response.send_message("Quest channel not found. Check QUEST_CHANNEL_ID.", ephemeral=True)


@quest_group.command(name="complete", description="Mark a Clan or Outsider quest/event as complete")
@app_commands.describe(
    group="Select the Clan or Outsider group"
)
@app_commands.choices(
    group=CLAN_CHOICES
)
async def quest_complete(
    interaction: discord.Interaction,
    group: app_commands.Choice[str]
):
    if not await staff_command_check(interaction):
        return

    selected_group = group.value

    async with data_lock:
        reset_legacy_quest_data_if_needed()

        quest = data.get("active_quests_v2", {}).get(selected_group)

        if not quest:
            await interaction.response.send_message(
                f"No active quest found for **{selected_group}**. Use `/quest force` to start a new cycle.",
                ephemeral=True
            )
            return

        if quest.get("status") == "Completed":
            await interaction.response.send_message(
                f"**{selected_group}** has already completed **{quest.get('title', 'their quest')}**.",
                ephemeral=True
            )
            return

        reward_text = apply_quest_success(selected_group, quest)
        quest["status"] = "Completed"
        quest["completed_at"] = datetime.now(TZ).isoformat()
        quest["reward_result"] = reward_text

        if quest.get("category") == "hunting":
            ensure_hunting_quest_progress(quest)
            # If this active hunt already had catches before this feature deployed,
            # migrate those hunters into the contributor list and give their one
            # contribution token before awarding the success token.
            sync_hunting_contributors_for_tokens(selected_group, quest)
            award_hunting_quest_contributor_history(selected_group, quest)

        pass_token_cats = award_monthly_quest_pass_tokens(selected_group, quest)

        data.setdefault("quest_history_v2", [])
        data["quest_history_v2"].append(copy.deepcopy(quest))
        data["active_quests_v2"][selected_group] = quest

        save_data(data)

    announcement = (
        f"✅ **Quest/Event Complete!**\n"
        f"{clan_mention(selected_group)}\n\n"
        f"**{selected_group}: {quest.get('title', 'Quest')}**\n"
        f"Category: **{QUEST_CATEGORY_LABELS.get(quest.get('category'), 'Quest')}**\n\n"
        + (f"🤝 **Quest Success:** {', '.join(pass_token_cats)} each earned **+1 Connection Token** for helping the quest pass.\n\n" if pass_token_cats else "")
        + f"🎁 **Reward:** {reward_text}"
    )

    channel = bot.get_channel(QUEST_CHANNEL_ID)

    if channel:
        await send_long_message(channel, announcement)
        await interaction.response.send_message(
            f"✅ {selected_group}'s quest/event was marked complete and the reward was posted.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Quest channel not found. The quest was saved as complete, but no announcement was posted.",
            ephemeral=True
        )


@quest_group.command(name="role", description="View the current optional role-specific quests")
async def quest_role_view(interaction: discord.Interaction):
    async with data_lock:
        reset_legacy_quest_data_if_needed()
        quests = copy.deepcopy(get_active_role_quests())
    if not quests:
        await interaction.response.send_message("🌟 There are no active role-specific quests right now.")
        return
    lines = ["🌟 **Current Optional Role-Specific Quests**"]
    for index, quest in enumerate(quests, start=1):
        lines.extend(["", format_role_quest_block(quest, index=index, total=len(quests)), f"**Status:** {quest.get('status', 'Pending')}"])
        if quest.get("completed_by"):
            lines.append(f"**Completed by:** {quest['completed_by']}")
        if quest.get("reward_result"):
            lines.append(f"**Reward:** {quest['reward_result']}")
    chunks = split_allegiance_text("\n".join(lines), max_length=1850)
    await interaction.response.send_message(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


ROLE_QUEST_SPENDABLE_CHOICES = [
    app_commands.Choice(name="Lucky Paw (+1 hunting)", value="lucky_paw"),
    app_commands.Choice(name="Well Rested (+1 physical roll)", value="well_rested"),
    app_commands.Choice(name="StarClan's Little Blessing (+1 hunting/fishing)", value="starclan_luck")
]


@quest_group.command(name="usebonus", description="Staff only. Mark a one-use role-quest bonus as spent")
@app_commands.describe(
    cat_name="OC using the saved bonus",
    bonus="Which one-use role-quest bonus was used"
)
@app_commands.choices(bonus=ROLE_QUEST_SPENDABLE_CHOICES)
async def quest_use_bonus(
    interaction: discord.Interaction,
    cat_name: str,
    bonus: app_commands.Choice[str]
):
    if not await staff_command_check(interaction):
        return

    field_map = {
        "lucky_paw": ("role_quest_lucky_paw_charges", "🍀 Lucky Paw"),
        "well_rested": ("role_quest_well_rested_charges", "💤 Well Rested"),
        "starclan_luck": ("role_quest_starclan_luck_charges", "🌙 StarClan's Little Blessing")
    }
    field, label = field_map[bonus.value]

    async with data_lock:
        resolved_name = resolve_cat_name_casefold(cat_name)
        if not resolved_name:
            await interaction.response.send_message(
                f"❌ Cat **{cat_name}** was not found.",
                ephemeral=True
            )
            return

        cat = data["cats"][resolved_name]
        prepare_cat_record(resolved_name, cat)
        charges = int(cat.get(field, 0) or 0)
        if charges <= 0:
            await interaction.response.send_message(
                f"❌ **{resolved_name}** does not have a saved **{label}** charge.",
                ephemeral=True
            )
            return

        cat[field] = charges - 1
        add_history(cat, f"Used role-quest bonus: {label}")
        save_data(data)
        remaining = cat[field]

    await interaction.response.send_message(
        f"✅ **{resolved_name}** used **{label}**. "
        f"**{remaining}** charge{'s' if remaining != 1 else ''} remaining.",
        ephemeral=True
    )


@quest_group.command(name="rolecomplete", description="Staff only. Complete one optional role quest with an eligible OC")
@app_commands.describe(
    cat_name="Eligible OC who completed the role-specific quest",
    quest_number="Which active role quest: 1 or 2 (defaults to 1)"
)
async def quest_role_complete(interaction: discord.Interaction, cat_name: str, quest_number: int = 1):
    if not await staff_command_check(interaction):
        return
    async with data_lock:
        reset_legacy_quest_data_if_needed()
        quests = get_active_role_quests()
        if not quests:
            await interaction.response.send_message("❌ There are no active role-specific quests.", ephemeral=True)
            return
        if quest_number < 1 or quest_number > len(quests):
            await interaction.response.send_message(f"❌ Choose a quest number from **1 to {len(quests)}**.", ephemeral=True)
            return
        quest = quests[quest_number - 1]
        if quest.get("status") == "Completed":
            await interaction.response.send_message(f"❌ Role quest #{quest_number} was already completed by **{quest.get('completed_by', 'another OC')}**.", ephemeral=True)
            return
        resolved_name = resolve_cat_name_casefold(cat_name)
        if not resolved_name:
            await interaction.response.send_message(f"❌ Cat **{cat_name}** was not found.", ephemeral=True)
            return
        cat = data["cats"][resolved_name]
        prepare_cat_record(resolved_name, cat)
        if bool(cat.get("is_npc", False)):
            await interaction.response.send_message("❌ Role-specific quest rewards are for player OCs, not NPCs.", ephemeral=True)
            return
        if not role_quest_cat_is_eligible(cat, quest):
            eligible = ", ".join(quest.get("eligible_ranks", []))
            await interaction.response.send_message(f"❌ **{resolved_name}** is not eligible for this quest. Eligible ranks: **{eligible}** from any Clan.", ephemeral=True)
            return
        reward_text = apply_role_quest_reward(resolved_name, cat, quest)
        quest["status"] = "Completed"
        quest["completed_at"] = datetime.now(TZ).isoformat()
        quest["completed_by"] = resolved_name
        quest["completed_by_owner_id"] = oc_owner_id(cat)
        quest["reward_result"] = reward_text
        quests[quest_number - 1] = quest
        set_active_role_quests(quests)
        data.setdefault("role_quest_history", []).append(copy.deepcopy(quest))
        data["role_quest_history"] = data["role_quest_history"][-120:]
        save_data(data)

    channel = bot.get_channel(QUEST_CHANNEL_ID)
    if channel:
        await send_long_message(channel, "🌟 **Role-Specific Quest Complete!**\n\n" + f"**{resolved_name}** completed **{quest.get('title', 'the role quest')}**.\n🎁 {reward_text}")
    await interaction.response.send_message(f"✅ Marked role quest #{quest_number} complete for **{resolved_name}** and applied their random reward.", ephemeral=True)


@quest_group.command(name="rolereroll", description="Staff only. Replace one optional role-specific quest")
@app_commands.describe(quest_number="Which active role quest to replace: 1 or 2 (defaults to 1)")
async def quest_role_reroll(interaction: discord.Interaction, quest_number: int = 1):
    if not await staff_command_check(interaction):
        return
    async with data_lock:
        reset_legacy_quest_data_if_needed()
        quests = get_active_role_quests()
        if not quests:
            await interaction.response.send_message("❌ There are no active role-specific quests.", ephemeral=True)
            return
        if quest_number < 1 or quest_number > len(quests):
            await interaction.response.send_message(f"❌ Choose a quest number from **1 to {len(quests)}**.", ephemeral=True)
            return
        due_at = get_current_quest_cycle_due_at()
        archive_role_quest(quests[quest_number - 1], "Replaced")
        other_roles = {quest.get("role") for i, quest in enumerate(quests) if i != quest_number - 1 and quest}
        replacement = select_new_role_quest(due_at=due_at, exclude_roles=other_roles)
        quests[quest_number - 1] = replacement
        set_active_role_quests(quests)
        save_data(data)
    channel = bot.get_channel(QUEST_CHANNEL_ID)
    if channel:
        await send_long_message(channel, f"🔄 **Role Quest #{quest_number} Rerolled**\n\n" + format_role_quest_block(replacement, index=quest_number, total=len(quests)))
    await interaction.response.send_message(f"✅ Posted a new optional role-specific quest in slot #{quest_number}.", ephemeral=True)


RESET_QUEST_CHOICES = [
    app_commands.Choice(name="All", value="All")
] + CLAN_CHOICES


def get_current_quest_cycle_due_at():
    reset_legacy_quest_data_if_needed()
    active_quests = data.get("active_quests_v2", {})
    due_dates = []

    for quest in active_quests.values():
        if not quest or not quest.get("due_at"):
            continue

        try:
            due_dates.append(datetime.fromisoformat(quest["due_at"]))
        except Exception:
            continue

    if due_dates:
        return min(due_dates)

    return next_regular_quest_cycle(datetime.now(TZ))


def replace_active_quest(group, due_at):
    old_quest = data.get("active_quests_v2", {}).get(group)
    new_quest = select_new_quest(group)
    new_quest["due_at"] = due_at.isoformat()
    new_quest["reset_at"] = datetime.now(TZ).isoformat()

    if old_quest:
        new_quest["replaced_quest_title"] = old_quest.get("title", "Unknown Quest")

    data.setdefault("active_quests_v2", {})
    data["active_quests_v2"][group] = new_quest

    return old_quest, new_quest


@bot.tree.command(name="resetquest", description="Staff only. Replace one group's quest/event or every active quest without changing the due date")
@app_commands.describe(
    group="Choose one Clan/Outsider group or All"
)
@app_commands.choices(group=RESET_QUEST_CHOICES)
async def resetquest(interaction: discord.Interaction, group: app_commands.Choice[str]):
    if not await staff_command_check(interaction):
        return

    selected_group = group.value

    async with data_lock:
        reset_legacy_quest_data_if_needed()
        clean_expired_quest_effects()

        due_at = get_current_quest_cycle_due_at()
        groups_to_reset = QUEST_GROUP_ORDER if selected_group == "All" else [selected_group]
        reset_results = []

        for quest_group_name in groups_to_reset:
            old_quest, new_quest = replace_active_quest(quest_group_name, due_at)
            reset_results.append((quest_group_name, old_quest, new_quest))

        save_data(data)

    lines = [
        "🔄 **Quest Reset**",
        f"The replacement quest{'s' if len(reset_results) != 1 else ''} will still be due on **{due_at.strftime('%B %d, %Y')}**, so the regular monthly first-of-the-month schedule stays intact.",
        ""
    ]

    for quest_group_name, old_quest, new_quest in reset_results:
        lines.extend([
            "━━━━━━━━━━━━━━━",
            clan_mention(quest_group_name),
            f"**{quest_group_name} replacement quest/event**"
        ])

        if old_quest:
            lines.append(f"Old Quest/Event: **{old_quest.get('title', 'Unknown Quest')}**")

        lines.append(format_quest_block(quest_group_name, new_quest))
        lines.append("")

    announcement = "\n".join(lines)
    channel = bot.get_channel(QUEST_CHANNEL_ID)

    if channel:
        await send_long_message(channel, announcement)
        await interaction.response.send_message(
            f"🔄 Reset quest{'s' if len(reset_results) != 1 else ''} for **{selected_group}** and posted the replacement.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "Quest channel not found. The replacement quest was saved, but no announcement was posted.",
            ephemeral=True
        )


# HIATUS
# ─────────────────────────────

@tasks.loop(hours=24)
async def check_hiatuses():
    today = datetime.now(TZ).date()
    ended_hiatuses = []
    ended_info = {}

    async with data_lock:
        data.setdefault("hiatuses", {})

        for user_id, info in list(data["hiatuses"].items()):
            end_date = datetime.fromisoformat(info["end_date"]).date()

            if today >= end_date:
                ended_hiatuses.append(user_id)
                ended_info[user_id] = copy.deepcopy(info)

        for user_id in ended_hiatuses:
            del data["hiatuses"][user_id]

        if ended_hiatuses:
            save_data(data)

    channel = bot.get_channel(HIATUS_CHANNEL_ID)

    for user_id in ended_hiatuses:
        guild = get_guild_for_hiatus(ended_info.get(user_id, {}))
        role_success, role_message = await update_hiatus_roles(guild, user_id, on_hiatus=False)

        if channel:
            message = f"✅ <@{user_id}> is now off hiatus!"

            if role_success:
                message += f"\n✅ {role_message}"
            else:
                message += f"\n⚠️ Roles were not changed automatically: {role_message}"

            await channel.send(message)


@tasks.loop(time=time(hour=10, minute=15, tzinfo=TZ))
async def check_membership_milestones():
    async with data_lock:
        today_key = datetime.now(TZ).date().isoformat()

        if data.get("last_membership_milestone_check") == today_key:
            return

    notices = await run_membership_milestone_check(post_to_channel=True)

    async with data_lock:
        data["last_membership_milestone_check"] = today_key
        save_data(data)

    if notices:
        print(f"Membership milestone check posted {len(notices)} notice(s).")



# ─────────────────────────────
# ACTIVITY WARNING REMINDERS
# ─────────────────────────────

def clean_discord_user_id(value):
    cleaned = str(value).strip()
    cleaned = cleaned.replace("<@", "").replace(">", "").replace("!", "")
    return cleaned


def get_activity_warning_summary(reminders, user_id):
    cleaned_user_id = clean_discord_user_id(user_id)
    sent_warnings = []
    pending_reminders = []

    for reminder_id, reminder in reminders.items():
        if str(reminder.get("target_user_id")) != cleaned_user_id:
            continue

        status = reminder.get("status", "Pending")

        if status == "Sent":
            sent_warnings.append((reminder_id, reminder))

        elif status == "Pending":
            pending_reminders.append((reminder_id, reminder))

    sent_warnings.sort(key=lambda item: item[1].get("sent_at") or item[1].get("due_at") or "")
    pending_reminders.sort(key=lambda item: item[1].get("due_at", ""))

    return {
        "was_warned_before": len(sent_warnings) > 0,
        "sent_count": len(sent_warnings),
        "pending_count": len(pending_reminders),
        "sent_warnings": sent_warnings,
        "pending_reminders": pending_reminders
    }


def format_warning_history(summary):
    sent_count = summary.get("sent_count", 0)

    if sent_count == 0:
        return "No previous completed activity warnings."

    warning_word = "warning" if sent_count == 1 else "warnings"
    return f"Warned before: Yes — {sent_count} previous completed activity {warning_word}."


@tasks.loop(minutes=30)
async def check_activity_reminders():
    now = datetime.now(TZ)
    due_reminders = []

    async with data_lock:
        data.setdefault("activity_reminders", {})

        for reminder_id, reminder in list(data["activity_reminders"].items()):
            if reminder.get("status", "Pending") != "Pending":
                continue

            due_at = reminder.get("due_at")
            if not due_at:
                continue

            try:
                due_time = datetime.fromisoformat(due_at)
            except Exception:
                reminder["status"] = "Broken"
                reminder["error"] = "Invalid due_at timestamp"
                continue

            if now >= due_time:
                reminder["status"] = "Sent"
                reminder["sent_at"] = now.isoformat()
                due_reminders.append((reminder_id, copy.deepcopy(reminder)))

        if due_reminders:
            save_data(data)

    if not due_reminders:
        return

    channel = bot.get_channel(ACTIVITY_WARNING_CHANNEL_ID)

    if not channel:
        print("Activity reminder channel was not found.")
        return

    for reminder_id, reminder in due_reminders:
        target_user_id = reminder.get("target_user_id")
        days = int(reminder.get("days", 0))
        day_word = "day" if days == 1 else "days"
        previous_warning_count = int(reminder.get("previous_warning_count", 0))
        warning_history_text = format_warning_history({"sent_count": previous_warning_count})

        await channel.send(
            f"<@{ACTIVITY_WARNING_USER_ID}> ⏳ **{days} {day_word} is up for <@{target_user_id}>.**\n"
            f"Activity warning reminder `{reminder_id}` is now due.\n"
            f"**Warning History Before This Reminder:** {warning_history_text}"
        )


activity_group = app_commands.Group(
    name="activity",
    description="Activity warning reminder commands"
)


@activity_group.command(name="reminder", description="Set an activity warning reminder for a member.")
@app_commands.describe(
    xdays="How many days until the reminder posts",
    user_id="Raw Discord user ID from /raw-format"
)
async def activity_reminder(interaction: discord.Interaction, xdays: int, user_id: str):
    if not await staff_command_check(interaction):
        return

    if xdays < 1:
        await interaction.response.send_message(
            "❌ The reminder must be at least 1 day long.",
            ephemeral=True
        )
        return

    cleaned_user_id = clean_discord_user_id(user_id)

    if not cleaned_user_id.isdigit():
        await interaction.response.send_message(
            "❌ Please use a raw Discord user ID, or a valid user mention.",
            ephemeral=True
        )
        return

    now = datetime.now(TZ)
    due_at = now + timedelta(days=xdays)

    async with data_lock:
        data.setdefault("activity_reminders", {})
        warning_summary = get_activity_warning_summary(data["activity_reminders"], cleaned_user_id)
        previous_warning_count = int(warning_summary.get("sent_count", 0))
        next_id = int(data.get("last_activity_reminder_id", 0)) + 1
        data["last_activity_reminder_id"] = next_id

        reminder_id = f"activity-{next_id}"
        data["activity_reminders"][reminder_id] = {
            "target_user_id": cleaned_user_id,
            "days": xdays,
            "created_at": now.isoformat(),
            "due_at": due_at.isoformat(),
            "created_by": str(interaction.user.id),
            "status": "Pending",
            "was_warned_before": previous_warning_count > 0,
            "previous_warning_count": previous_warning_count
        }

        save_data(data)

    day_word = "day" if xdays == 1 else "days"
    warning_history_text = format_warning_history({"sent_count": previous_warning_count})

    await interaction.response.send_message(
        f"⏳ Activity reminder set for <@{cleaned_user_id}>.\n"
        f"I will ping <@{ACTIVITY_WARNING_USER_ID}> in <#{ACTIVITY_WARNING_CHANNEL_ID}> when **{xdays} {day_word}** is up.\n"
        f"Due: **{due_at.strftime('%B %d, %Y at %I:%M %p')}** Toronto time.\n"
        f"**Warning History:** {warning_history_text}\n"
        f"Reminder ID: `{reminder_id}`",
        ephemeral=True
    )


@activity_group.command(name="list", description="View pending activity warning reminders.")
async def activity_list(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        reminders = copy.deepcopy(data.setdefault("activity_reminders", {}))

    pending = [
        (reminder_id, reminder)
        for reminder_id, reminder in reminders.items()
        if reminder.get("status", "Pending") == "Pending"
    ]

    if not pending:
        await interaction.response.send_message(
            "✅ There are no pending activity warning reminders.",
            ephemeral=True
        )
        return

    pending.sort(key=lambda item: item[1].get("due_at", ""))

    lines = ["⏳ **Pending Activity Warning Reminders**", ""]

    for reminder_id, reminder in pending[:30]:
        target_user_id = reminder.get("target_user_id")
        due_at = reminder.get("due_at")
        days = reminder.get("days", "?")
        previous_warning_count = int(reminder.get("previous_warning_count", 0))

        try:
            due_text = datetime.fromisoformat(due_at).strftime("%B %d, %Y at %I:%M %p")
        except Exception:
            due_text = "Unknown due date"

        history_text = "first warning" if previous_warning_count == 0 else f"warned before {previous_warning_count} time(s)"

        lines.append(
            f"• `{reminder_id}` — <@{target_user_id}> — **{days} day(s)** — due **{due_text}** — {history_text}"
        )

    if len(pending) > 30:
        lines.append(f"\n…and {len(pending) - 30} more pending reminder(s).")

    await interaction.response.send_message("\n".join(lines)[:1900], ephemeral=True)


@activity_group.command(name="cancel", description="Cancel a pending activity warning reminder.")
@app_commands.describe(reminder_id="Reminder ID, such as activity-1")
async def activity_cancel(interaction: discord.Interaction, reminder_id: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        data.setdefault("activity_reminders", {})
        reminder = data["activity_reminders"].get(reminder_id)

        if not reminder:
            await interaction.response.send_message(
                f"❌ Reminder `{reminder_id}` was not found.",
                ephemeral=True
            )
            return

        if reminder.get("status", "Pending") != "Pending":
            await interaction.response.send_message(
                f"❌ Reminder `{reminder_id}` is already marked as **{reminder.get('status', 'Unknown')}**.",
                ephemeral=True
            )
            return

        reminder["status"] = "Cancelled"
        reminder["cancelled_at"] = datetime.now(TZ).isoformat()
        reminder["cancelled_by"] = str(interaction.user.id)
        save_data(data)

    await interaction.response.send_message(
        f"🧹 Cancelled activity warning reminder `{reminder_id}`.",
        ephemeral=True
    )


@activity_group.command(name="end", description="End a pending activity reminder for a user who became active again.")
@app_commands.describe(
    user_id="Raw Discord user ID or mention",
    reason="Optional note, such as 'started participating again'"
)
async def activity_end(interaction: discord.Interaction, user_id: str, reason: str = None):
    if not await staff_command_check(interaction):
        return

    cleaned_user_id = clean_discord_user_id(user_id)

    if not cleaned_user_id.isdigit():
        await interaction.response.send_message(
            "❌ Please use a raw Discord user ID, or a valid user mention.",
            ephemeral=True
        )
        return

    now_iso = datetime.now(TZ).isoformat()
    ended_ids = []

    async with data_lock:
        data.setdefault("activity_reminders", {})
        summary_before = get_activity_warning_summary(data["activity_reminders"], cleaned_user_id)

        for reminder_id, reminder in data["activity_reminders"].items():
            if str(reminder.get("target_user_id")) != cleaned_user_id:
                continue

            if reminder.get("status", "Pending") != "Pending":
                continue

            reminder["status"] = "Ended"
            reminder["ended_at"] = now_iso
            reminder["ended_by"] = str(interaction.user.id)
            reminder["end_reason"] = reason or "User began participating again"
            ended_ids.append(reminder_id)

        if ended_ids:
            save_data(data)

    warning_history_text = format_warning_history(summary_before)

    if not ended_ids:
        await interaction.response.send_message(
            f"✅ No pending activity countdowns were found for <@{cleaned_user_id}>.\n"
            f"**Warning History:** {warning_history_text}",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"✅ Ended **{len(ended_ids)}** pending activity countdown(s) for <@{cleaned_user_id}> because they began participating again.\n"
        f"**Ended Reminder(s):** {', '.join(f'`{reminder_id}`' for reminder_id in ended_ids)}\n"
        f"**Warning History:** {warning_history_text}",
        ephemeral=True
    )


@activity_group.command(name="status", description="Check a user's activity warning history and pending countdowns.")
@app_commands.describe(user_id="Raw Discord user ID or mention")
async def activity_status(interaction: discord.Interaction, user_id: str):
    if not await staff_command_check(interaction):
        return

    cleaned_user_id = clean_discord_user_id(user_id)

    if not cleaned_user_id.isdigit():
        await interaction.response.send_message(
            "❌ Please use a raw Discord user ID, or a valid user mention.",
            ephemeral=True
        )
        return

    async with data_lock:
        reminders = copy.deepcopy(data.setdefault("activity_reminders", {}))

    summary = get_activity_warning_summary(reminders, cleaned_user_id)
    warning_history_text = format_warning_history(summary)

    lines = [
        f"⏳ **Activity Warning Status for <@{cleaned_user_id}>**",
        f"**Warning History:** {warning_history_text}",
        f"**Pending Countdown(s):** {summary.get('pending_count', 0)}"
    ]

    if summary.get("pending_reminders"):
        lines.append("")
        lines.append("**Pending Reminders:**")

        for reminder_id, reminder in summary["pending_reminders"][:10]:
            due_at = reminder.get("due_at")
            days = reminder.get("days", "?")

            try:
                due_text = datetime.fromisoformat(due_at).strftime("%B %d, %Y at %I:%M %p")
            except Exception:
                due_text = "Unknown due date"

            lines.append(f"• `{reminder_id}` — **{days} day(s)** — due **{due_text}**")

    await interaction.response.send_message("\n".join(lines)[:1900], ephemeral=True)


membership_group = app_commands.Group(
    name="membership",
    description="Membership milestone and OC slot commands"
)


@membership_group.command(name="check", description="Staff only. Run the 1-month and 3-month OC slot milestone check now.")
async def membership_check(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    notices = await run_membership_milestone_check(post_to_channel=True)

    async with data_lock:
        data["last_membership_milestone_check"] = datetime.now(TZ).date().isoformat()
        save_data(data)

    if notices:
        await interaction.followup.send(
            f"✅ Membership milestone check complete. Posted **{len(notices)}** milestone notice(s).",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            "✅ Membership milestone check complete. No new 1-month or 3-month milestones were due.",
            ephemeral=True
        )


@membership_group.command(name="status", description="Staff only. View stored milestone status for a member by raw Discord user ID.")
@app_commands.describe(user_id="Raw Discord user ID from /raw-format")
async def membership_status(interaction: discord.Interaction, user_id: str):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        record = data.setdefault("membership_milestones", {}).get(str(user_id), {})

    guild = interaction.guild or get_membership_guild()
    member = await fetch_member_by_id(guild, user_id) if guild else None

    if member and member.joined_at:
        days_in_server = (datetime.now(TZ).date() - member.joined_at.astimezone(TZ).date()).days
        joined_text = f"Joined **{member.joined_at.astimezone(TZ).strftime('%B %d, %Y')}** (**{days_in_server} days ago**)"
        oc_count = highest_oc_count_from_roles(member)
        oc_text = f"{oc_count} OCs" if oc_count else "No 11–20 OC role found"
    else:
        joined_text = "Member could not be found or join date is unavailable."
        oc_text = "Unknown"

    one_month = "Yes" if milestone_was_processed(record, "one_month") else "No"
    three_month = "Yes" if milestone_was_processed(record, "three_month") else "No"

    excluded_text = "No"
    if member and member_has_any_role(member, NON_RP_MILESTONE_ROLE_IDS):
        excluded_text = "Yes — ignored for automatic RP slot milestones"

    await interaction.response.send_message(
        f"🌙 **Membership Status for <@{user_id}>**\n"
        f"{joined_text}\n"
        f"Current OC Slot Role: **{oc_text}**\n"
        f"Ignored Non-RP Role: **{excluded_text}**\n"
        f"30-Day Milestone Processed: **{one_month}**\n"
        f"90-Day Milestone Processed: **{three_month}**",
        ephemeral=True
    )

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
    story_message = await build_clan_report_text(report)
    age_message = await build_age_report_text(report)

    age_channel = bot.get_channel(AGE_REPORT_CHANNEL_ID)
    story_channel = bot.get_channel(REPORT_CHANNEL_ID)

    if age_channel:
        await send_long_message(
            age_channel,
            "@everyone 🌙 A moon has passed over Echostone Mountain. Every living cat turns one moon older unless their age is frozen.\n\n" + age_message
        )

    if story_channel:
        await send_long_message(
            story_channel,
            "@everyone 🌙 A new moon has passed across the Clans...\n\n" + story_message
        )

    await refresh_allegiances_safely("automatic moon advance")

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
            shown_name = display_cat_name(name, cat)
            lines.append(f"• {shown_name} — {cat.get('age', 0)} moons{faction}")

    await interaction.response.send_message("\n".join(lines)[:1900])

@bot.tree.command(name="catinfo", description="View details about a cat")
async def catinfo(interaction: discord.Interaction, name: str):
    await interaction.response.defer()

    if name not in data.get("cats", {}):
        await interaction.edit_original_response(content="Cat not found.")
        return

    async with data_lock:
        cat = data["cats"][name]
        prepare_cat_record(name, cat)

        if process_injury_recovery(cat):
            save_data(data)

        status = cat.get("status", "Alive")
        afterlife = cat.get("afterlife") or "None"
        honour_role = cat.get("honour_role") or "None"
        permanent_conditions = normalize_permanent_conditions(cat)
        mentor = format_mentor_display(cat)
        apprentices_text = format_apprentices_display(cat)
        injury_text = format_injury(cat)
        hunger_text = format_hunger_status(cat)
        role_bonus_text = role_quest_bonus_summary(cat)
        role_collection_text = role_quest_collection_summary(cat)
        role_skill_text = role_quest_skill_summary(cat)
        role_streak = int(cat.get("role_quest_streak", 0) or 0)
        connection_perk_text = format_connection_perk_badges(cat)

        age_text = f"{cat.get('age', 0)} moons"
        age_freeze_text = freeze_remaining_text(cat, "freeze_age", "freeze_age_until")

        if age_freeze_text:
            age_text += f" (frozen {age_freeze_text})"

        hunger_freeze_text = freeze_remaining_text(cat, "freeze_hunger", "freeze_hunger_until")

        if hunger_freeze_text and "frozen" not in hunger_text.lower():
            if "(" in hunger_text and hunger_text.endswith(")"):
                hunger_text = hunger_text[:-1] + f", frozen {hunger_freeze_text})"
            else:
                hunger_text += f" (frozen {hunger_freeze_text})"

        family = cat.get("family", {})
        relationship_lines = []

        if family:
            for relation, relatives in family.items():
                if relatives:
                    relationship_lines.append(
                        f"**{relation}:** {', '.join(relatives)}"
                    )

        relationships_text = (
            "👪 **Relationships:**\n" + "\n".join(relationship_lines)
            if relationship_lines
            else "👪 **Relationships:** None"
        )

        history = dedupe_recent_history_for_display(cat.get("history", []))[-8:]
        history_text = "\n".join(format_history_entry(entry) for entry in history) if history else "No recent history."

        message = (
            f"🐾 **{name}**\n"
            f"**Clan**: {cat.get('clan')}\n"
            f"**Rank**: {cat.get('rank')}\n"
            f"**Honour Role**: {honour_role}\n"
        )

        if permanent_conditions:
            condition_label = "Permanent Condition" if len(permanent_conditions) == 1 else "Permanent Conditions"
            message += f"**{condition_label}**: {', '.join(permanent_conditions)}\n"

        if cat.get("clan") == "Outsider":
            faction = cat.get("faction") or "None"
            message += f"**Outsider Group**: {faction}\n"

        message += (
            f"**Age**: {age_text}\n"
            f"**Status**: {status}\n"
            f"**Current Health**: {injury_text}\n"
            f"**Hunger**: {hunger_text}\n"
            f"**Role Quest Bonus**: {role_bonus_text}\n"
            f"**Role Quest Streak**: {role_streak} completed\n"
            + (f"**Perks**: {connection_perk_text}\n" if connection_perk_text else "")
            + f"**Quest Keepsakes**: {role_collection_text}\n"
            f"**Quest Skill Practice**: {role_skill_text}\n"
            f"**Mentor**: {mentor}\n"
            f"**Apprentices**: {apprentices_text}\n"
            f"**Afterlife**: {afterlife}\n\n"
            f"{relationships_text}\n\n"
            f"📜 **Recent History:**\n"
            f"{history_text}"
        )

    await interaction.edit_original_response(content=message[:1900])

# ─────────────────────────────
# NEEDS MENTOR COMMAND
# ─────────────────────────────

@bot.tree.command(
    name="needsmentor",
    description="View apprentices who do not currently have mentors"
)
async def needsmentor(interaction: discord.Interaction):
    async with data_lock:
        needs_mentor = []

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            clan = cat.get("clan", "Unknown Clan")
            rank = cat.get("rank")
            age = cat.get("age", 0)
            mentor = cat.get("mentor")

            if rank in ["Apprentice", "Medicine Cat Apprentice"] and not mentor:
                needs_mentor.append((clan, rank, name, age))

    if not needs_mentor:
        await interaction.response.send_message(
            "🐾 **Apprentices Needing Mentors**\n\nEvery apprentice currently has a mentor assigned."
        )
        return

    needs_mentor.sort(key=lambda item: (item[0], item[1], item[2]))

    lines = [
        "🐾 **Apprentices Needing Mentors**",
        ""
    ]

    current_clan = None

    for clan, rank, name, age in needs_mentor:
        if clan != current_clan:
            current_clan = clan
            lines.append(f"### **{clan}**")

        icon = "🌿" if rank == "Medicine Cat Apprentice" else "🐾"

        lines.append(
            f"{icon} **{name}** — {rank}, {age} moons"
        )

    await interaction.response.send_message("\n".join(lines)[:1900])
    
# ─────────────────────────────
# FEED COMMANDS
# ─────────────────────────────

feed_group = app_commands.Group(
    name="feed",
    description="Feed cats and check Clan hunger"
)


@feed_group.command(name="cat", description="Feed an OC")
@app_commands.describe(
    name="The cat you want to feed",
    prey_size="Normal prey raises hunger by 1 level. Large prey raises hunger by 2 levels."
)
@app_commands.choices(prey_size=PREY_SIZE_CHOICES)
async def feed_cat_command(
    interaction: discord.Interaction,
    name: str,
    prey_size: app_commands.Choice[str] = None
):
    selected_prey_size = prey_size.value if prey_size else "normal"

    async with data_lock:
        cats = data.get("cats", {})

        if name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = cats[name]
        prepare_cat_record(name, cat)

        if str(cat.get("status", "Alive")).lower() == "dead":
            await interaction.response.send_message(
                "Dead cats cannot be fed.",
                ephemeral=True
            )
            return

        old_hunger, new_hunger = feed_cat(cat, selected_prey_size)

        prey_text = "large prey" if selected_prey_size == "large" else "prey"
        new_status_text = format_hunger_status(cat)

        save_data(data)

    await interaction.response.send_message(
        f"🍽️ **{name}** ate some {prey_text}!\n"
        f"**Hunger:** {old_hunger} → **{new_hunger}**\n"
        f"**Current Status:** {new_status_text}"
    )


@feed_group.command(name="reset", description="Staff only. Reset an OC's hunger to Satisfied")
@app_commands.describe(
    name="The cat whose hunger should be reset"
)
async def feed_reset_command(
    interaction: discord.Interaction,
    name: str
):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        cats = data.get("cats", {})

        if name not in cats:
            await interaction.response.send_message("Cat not found.", ephemeral=True)
            return

        cat = cats[name]
        prepare_cat_record(name, cat)

        if str(cat.get("status", "Alive")).lower() == "dead":
            await interaction.response.send_message(
                "Dead cats cannot have their hunger reset.",
                ephemeral=True
            )
            return

        old_hunger, new_hunger = reset_cat_hunger(cat)
        new_status_text = format_hunger_status(cat)

        save_data(data)

    await interaction.response.send_message(
        f"🔄 **{name}**'s hunger has been reset.\n"
        f"**Hunger:** {old_hunger} → **{new_hunger}**\n"
        f"**Current Status:** {new_status_text}"
    )


@feed_group.command(name="resetclan", description="Staff only. Reset a full Clan's hunger to Satisfied")
@app_commands.describe(
    clan="The Clan or Outsider group whose hunger should be reset"
)
@app_commands.choices(clan=CLAN_CHOICES)
async def feed_resetclan_command(
    interaction: discord.Interaction,
    clan: app_commands.Choice[str]
):
    if not await staff_command_check(interaction):
        return

    selected_clan = clan.value

    async with data_lock:
        cats = data.get("cats", {})
        reset_cats = []

        for name, cat in cats.items():
            prepare_cat_record(name, cat)

            if cat.get("clan") != selected_clan:
                continue

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            old_hunger, new_hunger = reset_cat_hunger(cat)
            reset_cats.append((name, old_hunger, new_hunger))

        if not reset_cats:
            await interaction.response.send_message(
                f"No living cats found in **{selected_clan}**.",
                ephemeral=True
            )
            return

        reset_cats.sort(key=lambda item: item[0].lower())
        save_data(data)

    lines = [
        f"🔄 **{selected_clan} hunger has been reset.**",
        f"Reset **{len(reset_cats)}** living cat{'s' if len(reset_cats) != 1 else ''} to **Satisfied**.",
        "",
        "Updated cats:"
    ]

    for name, old_hunger, new_hunger in reset_cats:
        lines.append(f"• **{name}** — {old_hunger} → {new_hunger}")

    message = "\n".join(lines)
    chunks = []
    max_length = 1900

    while len(message) > max_length:
        split_at = message.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(message[:split_at])
        message = message[split_at:].lstrip()

    chunks.append(message)

    await interaction.response.send_message(chunks[0])

    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@feed_group.command(name="hunger", description="Check which cats in a Clan need to eat")
@app_commands.describe(
    clan="The Clan or Outsider group you want to check"
)
@app_commands.choices(clan=CLAN_CHOICES)
async def feed_hunger_command(
    interaction: discord.Interaction,
    clan: app_commands.Choice[str]
):
    selected_clan = clan.value

    async with data_lock:
        cats = data.get("cats", {})
        hungry_cats = []

        for name, cat in cats.items():
            prepare_cat_record(name, cat)

            if cat.get("clan") != selected_clan:
                continue

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            hunger = get_hunger_status(cat)

            if hunger in ["Starving", "Hungry", "Satisfied"]:
                hungry_cats.append((name, hunger, cat))

        save_data(data)

    if not hungry_cats:
        await interaction.response.send_message(
            f"🍽️ **{selected_clan} Hunger Check**\n\n"
            f"Everyone in **{selected_clan}** is currently Fed or better."
        )
        return

    hungry_cats.sort(key=lambda item: HUNGER_LEVELS.index(item[1]))

    lines = [
        f"🍽️ **{selected_clan} Hunger Check**",
        "",
        "These cats should eat soon:"
    ]

    for name, hunger, cat in hungry_cats:
        status_text = format_hunger_status(cat)
        lines.append(f"• **{name}** — {status_text}")

    message = "\n".join(lines)
    chunks = []
    max_length = 1900

    while len(message) > max_length:
        split_at = message.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(message[:split_at])
        message = message[split_at:].lstrip()

    chunks.append(message)

    await interaction.response.send_message(chunks[0])

    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)

# ─────────────────────────────
# UPCOMING CEREMONIES PUBLIC COMMAND
# ─────────────────────────────

@bot.tree.command(
    name="upcomingceremonies",
    description="View ceremony-eligible cats for all Clans or one Clan"
)
@app_commands.describe(clan="Optional Clan filter")
@app_commands.choices(clan=[
    app_commands.Choice(name="All Clans", value="All"),
    *CLAN_ONLY_CHOICES
])
async def upcomingceremonies(
    interaction: discord.Interaction,
    clan: app_commands.Choice[str] = None
):
    selected_clan = clan.value if clan else "All"

    async with data_lock:
        apprentice_ready = []
        warrior_ready = []
        elder_ready = []

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            cat_clan = cat.get("clan", "Unknown Clan")

            # Upcoming Clan ceremonies only apply to the four Clans.
            if cat_clan not in CLAN_NAMES_ONLY:
                continue

            if selected_clan != "All" and cat_clan != selected_clan:
                continue

            rank = cat.get("rank")
            age = int(cat.get("age", 0) or 0)
            shown_name = display_cat_name(name, cat)

            # Older than 5 moons = 6 moons or older. Kits stay on this list until
            # staff actually changes their rank after the RP ceremony.
            if rank == "Kit" and age >= 6:
                apprentice_ready.append((cat_clan, shown_name, age))

            elif rank == "Apprentice" and age >= 11:
                warrior_ready.append((cat_clan, shown_name, age))

            elif rank in AGING_TO_ELDER_RANKS and age >= 95:
                elder_ready.append((cat_clan, shown_name, age, rank))

    def sort_key(item):
        return (item[0], item[1].casefold())

    apprentice_ready.sort(key=sort_key)
    warrior_ready.sort(key=sort_key)
    elder_ready.sort(key=sort_key)

    filter_text = "all four Clans" if selected_clan == "All" else selected_clan
    lines = [
        "🌙 **Upcoming Ceremonies**",
        "",
        f"Showing cats currently eligible for rank-related ceremonies in **{filter_text}**.",
        ""
    ]

    lines.append("### 🐾 Kits Eligible to Become Apprentices")
    if apprentice_ready:
        current_clan = None
        for cat_clan, shown_name, age in apprentice_ready:
            if selected_clan == "All" and cat_clan != current_clan:
                current_clan = cat_clan
                lines.append(f"\n**{cat_clan}**")
            lines.append(f"🐾 **{shown_name}** — {age} moons")
    else:
        lines.append("No kits are currently eligible to become apprentices.")

    lines.extend(["", "### ⚔ Apprentices Eligible for Warrior Assessments"])
    if warrior_ready:
        current_clan = None
        for cat_clan, shown_name, age in warrior_ready:
            if selected_clan == "All" and cat_clan != current_clan:
                current_clan = cat_clan
                lines.append(f"\n**{cat_clan}**")
            lines.append(f"⚔ **{shown_name}** — {age} moons")
    else:
        lines.append("No apprentices are currently eligible for warrior assessments.")

    lines.extend(["", "### 🍂 Warriors Eligible to Retire as Elders"])
    if elder_ready:
        current_clan = None
        for cat_clan, shown_name, age, rank in elder_ready:
            if selected_clan == "All" and cat_clan != current_clan:
                current_clan = cat_clan
                lines.append(f"\n**{cat_clan}**")
            lines.append(f"🍂 **{shown_name}** — {age} moons | Current Rank: {rank}")
    else:
        lines.append("No warriors are currently eligible to retire as elders.")

    message = "\n".join(lines)
    chunks = []
    while len(message) > 1900:
        split_at = message.rfind("\n", 0, 1900)
        if split_at == -1:
            split_at = 1900
        chunks.append(message[:split_at])
        message = message[split_at:].lstrip()
    chunks.append(message)

    await interaction.response.send_message(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)

# ─────────────────────────────
# FROZEN LIST COMMAND
# ─────────────────────────────

@bot.tree.command(
    name="frozenlist",
    description="View all cats with age or hunger freezes"
)
async def frozenlist(interaction: discord.Interaction):
    if not await staff_command_check(interaction):
        return

    async with data_lock:
        frozen_cats = []

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            age_freeze_text = freeze_remaining_text(
                cat,
                "freeze_age",
                "freeze_age_until"
            )

            hunger_freeze_text = freeze_remaining_text(
                cat,
                "freeze_hunger",
                "freeze_hunger_until"
            )

            if age_freeze_text or hunger_freeze_text:
                clan = cat.get("clan", "Unknown Clan")
                rank = cat.get("rank", "Unknown Rank")

                frozen_cats.append(
                    (
                        clan,
                        name,
                        rank,
                        age_freeze_text,
                        hunger_freeze_text
                    )
                )

        save_data(data)

    if not frozen_cats:
        await interaction.response.send_message(
            "❄️ **Frozen Cats**\n\nNo cats are currently frozen.",
            ephemeral=True
        )
        return

    frozen_cats.sort(key=lambda item: (item[0], item[1]))

    lines = [
        "❄️ **Frozen Cats**",
        ""
    ]

    current_clan = None

    for clan, name, rank, age_freeze_text, hunger_freeze_text in frozen_cats:
        if clan != current_clan:
            current_clan = clan
            lines.append(f"### **{clan}**")

        age_status = f"Frozen {age_freeze_text}" if age_freeze_text else "Not frozen"
        hunger_status = f"Frozen {hunger_freeze_text}" if hunger_freeze_text else "Not frozen"

        lines.append(
            f"• **{name}** — {rank}\n"
            f"  Age: {age_status}\n"
            f"  Hunger: {hunger_status}"
        )

    await interaction.response.send_message("\n".join(lines)[:1900])



        # ─────────────────────────────
        # MENTOR DISPLAY
        # ─────────────────────────────
       
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
        shown_name = display_cat_name(name, cat)
        lines.append(
            f"• {shown_name} — {cat.get('clan')} — died as {cat.get('rank')} "
            f"at {cat.get('age', 0)} moons → {cat.get('afterlife')}"
        )

    await interaction.response.send_message("\n".join(lines)[:1900])

@bot.tree.command(name="bothelp", description="View a list of member bot commands")
async def bothelp(interaction: discord.Interaction):
    message = (
        "📘 **ECHOSTONE MOUNTAIN BOT HELP** 📘\n\n"

                "🐾 **General Member Commands**\n"
        "`/catinfo [Name]` — View full details about a cat, including hunger and active role-quest bonuses\n"
        "`/oclist [User]` — Publicly view a player's OCs and each living OC's hunger\n"
        "`/ocowner [Cat]` — Find which player owns a specific OC\n"
        "`/cats [Clan]` — View all cats by clan or all clans\n"
        "`/clan [ClanName]` — View one clan roster\n"
        "`/cattinder [Name] [Clan]` — Find age-appropriate romance options\n"
        "`/question` — Random OC question prompt system\n"
        "`/hunt` — In a designated territory channel, randomly find prey or a local threat using that location’s prey table; no location argument needed\n"
        "`/needsmentor` — View apprentices and medicine cat apprentices who do not currently have mentors\n"
        "`/upcomingceremonies [Clan]` — View kits, apprentices, and older warriors eligible for ceremonies or assessments, optionally filtered by Clan\n\n"

        "🍽️ **Feeding / Hunger Commands**\n"
        "`/feed cat [Name]` — Feed an OC normal prey and raise their hunger level by 1\n"
        "`/feed cat [Name] [Large Prey]` — Feed an OC large prey and raise their hunger level by 2\n"
        "`/feed hunger [Clan]` — Check which cats in a Clan are Starving, Hungry, or Satisfied\n"
        "Hunger affects hunting rolls: Starving -2, Hungry -1, Satisfied no change, Full +1, Well Fed +2.\n\n"

        "🌦️ **Weather / World Commands**\n"
        "`/weather` or `/weatherreport` — View the current weekly weather report, if available.\n"
        "`/severeweather active` — View active severe-weather events, locations, and penalties\n"
        "`/severeweather modifier` — Check the severe-weather modifier for a specific territory/location and hunting or fishing roll\n"
        "Severe weather rolls on Mondays at 4 PM Toronto time. Primary disaster effects last 7 days unless staff sets a different duration.\n\n"
        "Rare ambient hazards can also occur at Frozen Falls and Toadstool Glade after recent RP activity; these only post a roll prompt and never apply injuries automatically.\n\n"

        "📜 **Quest / Story Commands**\n"
        "Current quests/events post on the 1st of every month at 9 AM and stay active until the next month. Hunting objectives use broad prey categories such as birds, fish, or small prey. Use `/quest progress` to see quest progress and contributors. Hunting quests use `/quest catch [Cat] [Prey]`; non-hunting quests use `/quest contribute [Cat]`. An OC earns 1 Connection Token for their first contribution to a monthly quest and another if that quest succeeds. Use `/quest perks` to view the permanent badges those tokens can buy. Reminders post with 14 days, 7 days, and 3 days remaining. The pool rolls 35% hunting, 20% social, 20% herb patrol, 10% sickness/crisis, and 15% wild animal events.\n"
        "Starting September 1, two optional role-specific quests run alongside the monthly quests, using two different role groups whenever possible. Each role cycles through all of its prompts before repeating. There is no penalty if nobody completes them. Use `/quest role` to view both. One-use Lucky Paw, Well Rested, and StarClan blessing charges are saved on `/catinfo`; staff can mark them spent with `/quest usebonus`.\n"
        "`/gatheringreport [ClanName]` — View recent story updates, quest results, injuries, rank changes, and major events for a specific Clan.\n"
        "`/rollhelp` — Helps calculate whether an OC caught their prey by adding the roll, prey modifier, specialty prey bonus, weather modifier, quest modifier, hunger modifier, and any other modifier against the OC’s required hunting number.\n\n"

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
bot.tree.add_command(hiatus_group)
bot.tree.add_command(honour_group)
bot.tree.add_command(condition_group)
bot.tree.add_command(plot_group)
bot.tree.add_command(npc_group)
bot.tree.add_command(outsider_group)
bot.tree.add_command(allegiance_group)
bot.tree.add_command(severeweather_group)
bot.tree.add_command(activity_group)
bot.tree.add_command(membership_group)
bot.tree.add_command(feed_group)
bot.tree.add_command(quest_group)
bot.tree.add_command(prophecy_group)
keep_alive()
print("Starting Discord bot. Server Members Intent is required; Message Content Intent is disabled.")
bot.run(TOKEN)
