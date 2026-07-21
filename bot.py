import os
import json
import random
import asyncio
import copy
from datetime import datetime, time, timedelta
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
HIATUS_CHANNEL_ID = 1441505660905984120
HIATUS_ROLE_ID = 1463773050242728049
MEMBER_ROLE_ID = 1441508526504808561
DEATH_ANNOUNCEMENT_CHANNEL_ID = 1441498271842304183
ACTIVITY_WARNING_CHANNEL_ID = 1500705057207746610
ACTIVITY_WARNING_USER_ID = 1440182563674132490

HONOUR_ANNOUNCEMENT_CHANNEL_ID = 1441502516591202394
HONOUR_TRACKER_CHANNEL_ID = 1441503004749594787
HONOUR_ANNOUNCEMENT_ROLE_ID = 1449118016360026253
HONOUR_DISCORD_TIMEOUT_SECONDS = 12

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
        "used_questions": [],
        "hiatuses": {},
        "membership_milestones": {},
        "activity_reminders": {},
        "last_activity_reminder_id": 0,
        "honour_tracker_message_id": None,
        "last_moon_snapshot": None
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
        # AUTOMATIC KIT → APPRENTICE
        # ─────────────────────────────

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            if cat.get("clan") == "Outsider":
                continue

            if cat.get("rank") == "Kit" and cat.get("age", 0) >= 6:
                cat["rank"] = "Apprentice"
                cat["mentor"] = None

                add_history(cat, "Rank changed to Apprentice")

                report["apprentice_news"].append(
                    f"🐾 {name} became an Apprentice."
                )

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
                if cat.get("rank") == rank
            ]

            if not ranked_cats:
                continue

            ranked_cats.sort(key=lambda item: item[1].get("age", 0), reverse=True)
            lines.append(f"**{plural_rank(rank)}**")

            for name, cat in ranked_cats:
                mentor = cat.get("mentor")
                age_text = f"{cat.get('age', 0)} moons"
                age_freeze_text = freeze_remaining_text(cat, "freeze_age", "freeze_age_until")

                if age_freeze_text:
                    age_text += f" (age frozen {age_freeze_text})"

                if rank in ["Apprentice", "Medicine Cat Apprentice"] and mentor:
                    lines.append(
                        f"• {name} - {age_text} | Mentor: {mentor}"
                    )
                else:
                    lines.append(
                        f"• {name} - {age_text}"
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
            age_text = f"{cat.get('age', 0)} moons"
            age_freeze_text = freeze_remaining_text(cat, "freeze_age", "freeze_age_until")

            if age_freeze_text:
                age_text += f" (age frozen {age_freeze_text})"

            faction = f" | {cat.get('faction')}" if cat.get("faction") else ""
            lines.append(
                f"• {name} - {cat.get('rank')} - {age_text}{faction}"
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


def generate_weekly_weather():
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

    return (
        f"{opener}\n\n"
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

    if not quest_reminders.is_running():
        quest_reminders.start()

    if not check_hiatuses.is_running():
        check_hiatuses.start()

    if not check_membership_milestones.is_running():
        check_membership_milestones.start()

    if not check_activity_reminders.is_running():
        check_activity_reminders.start()

    try:
        await asyncio.wait_for(
            update_honour_tracker_message(),
            timeout=HONOUR_DISCORD_TIMEOUT_SECONDS
        )
        print("Honour Role tracker is up to date.")
    except Exception as error:
        print(f"Honour Role tracker update failed: {error}")


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
        "`/prophecy post` — Staff only. Post a custom prophecy or omen\n`/prophecy pause` — Staff only. Pause new monthly prophecy rolls and keep the active prophecy\n`/prophecy unpause` — Staff only. Resume new monthly prophecy rolls\n"
        "`/revertmoon` — Staff only. Reverts to the saved state before the last moon advance\n\n"

        "📜 **Quest / Gathering Commands**\n"
        "`/quest force` — Quest manager only. Clear and force-post a new 2-week quest/event cycle while keeping the Tuesday schedule\n"
        "`/quest complete [Clan]` — Staff only. Mark a Clan or Outsider quest/event as complete and post the reward\n`/resetquest [Clan/Outsider/All]` — Staff only. Replace one or all active quests/events while keeping the current due date\n"
        "`/gatheringreport [ClanName]` — Generate a Clan-specific report including recent promotions, deaths, injuries, quest results, and major story changes\n"
        "`/rollhelp` — Helps calculate whether an OC caught their prey using their roll, modifiers, and required hunting number\n\n"

        "🐾 **General Member Commands**\n"
        "`/catinfo [Name]` — View full details about a cat\n"
        "`/cats [Clan]` — View all cats by clan or all clans\n"
        "`/clan [ClanName]` — View one clan roster\n"
        "`/cattinder [Name] [Clan]` — Find age-appropriate romance options\n"
        "`/question` — Random OC question prompt system\n"
        "`/needsmentor` — View apprentices and medicine cat apprentices who do not currently have mentors\n"
        "`/upcomingceremonies` — View cats eligible for apprentice ceremonies, warrior assessments, or elder retirement\n\n"
        
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
        "• Quests automatically post every other Tuesday at 9 AM\n"
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
hiatus_group = app_commands.Group(name="hiatus", description="Manage member hiatuses")
honour_group = app_commands.Group(name="honour", description="Manage Clan Honour Roles")
condition_group = app_commands.Group(name="condition", description="Manage permanent cat status conditions")


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
        save_data(data)

    await interaction.response.send_message(
        f"🗑 Deleted **{name}** permanently and removed related records."
    )

    if had_honour_role:
        try:
            await update_honour_tracker_message()
        except Exception as error:
            print(f"Could not update Honour Role tracker after deleting cat: {error}")


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
# ─────────────────────────────
# QUEST SYSTEM
# ─────────────────────────────

QUEST_CHANNEL_ID = 1441502516591202394
QUEST_FORCE_ROLE_ID = 1441507932369063957
QUEST_DURATION_DAYS = 14
QUEST_FORCE_SKIP_DAYS = 5
QUEST_SCHEDULE_HOUR = 9
QUEST_SCHEDULE_MINUTE = 0
QUEST_SCHEDULE_ANCHOR = datetime(2026, 7, 7, QUEST_SCHEDULE_HOUR, QUEST_SCHEDULE_MINUTE, tzinfo=TZ)
QUEST_SYSTEM_VERSION = "v4_tuesday_weighted_events"

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

        hunt_amounts = [3, 3, 4, 4, 5, 6, 3, 4, 5, 3, 4, 6]
        for index, style_title in enumerate(HUNTING_SCENARIOS):
            site = lore["sites"][index % len(lore["sites"])]
            amount = hunt_amounts[index % len(hunt_amounts)]
            reward_text, failure_text, effect, penalty = hunting_reward_for(group, amount, site["bonus"])

            quest_db[group]["hunting"].append({
                "id": make_quest_id(group, "hunting", index + 1),
                "category": "hunting",
                "title": f"{style_title}: Catch {amount} {site['prey'].title()}",
                "objective": f"Catch **{amount} {site['prey']}** at **{site['name']}**.",
                "description": (
                    f"Travel to **{site['name']}** ({site['channel']}) where {site['danger']} make the patrol feel alive. "
                    f"This is meant to be attainable, so the goal stays small and focused: a quick hunt, a mentor lesson, or a compact fresh-kill pile scene."
                ),
                "reward_text": reward_text,
                "failure_text": failure_text,
                "success_result": f"For the next **2 real-life weeks**, {group} gets **{format_modifier(effect['modifier'])} to all {site['bonus']} hunting rolls**.",
                "failure_result": f"For the next **2 real-life weeks**, {group} has **-1 to all {site['bonus']} hunting rolls** because the failed hunt scattered prey signs.",
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
    return (datetime.now(TZ) + timedelta(days=QUEST_DURATION_DAYS)).isoformat()


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
    due_at = issued_at + timedelta(days=QUEST_DURATION_DAYS)

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
            f"These replacement quests are due by **{due_at.strftime('%B %d, %Y')}**, keeping the regular every-other-Tuesday quest schedule intact.",
            ""
        ]

        if skipped_schedule:
            lines.extend([
                f"Because this reset happened within **{QUEST_FORCE_SKIP_DAYS} days** of the next scheduled quest cycle, the **{skipped_schedule.strftime('%B %d, %Y')}** automatic reset will be skipped.",
                ""
            ])
    else:
        lines = [
            "🌙 **A half moon has passed...**",
            "",
            "New quests and story events are now available for every Clan and the Outsiders! This cycle can bring hunting, social scenes, herb patrols, sickness/crisis events, or wild animal trouble.",
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

    return "\n".join(lines)


def build_quest_reminder(days_remaining):
    reset_legacy_quest_data_if_needed()

    lines = [
        f"⏳ **Quest Reminder: {days_remaining} days remaining!**",
        "",
        "The current quest cycle is still active. Complete your group's quest or story event before the next Tuesday reset to earn the reward and avoid possible consequences.",
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

        if days_remaining not in [7, 3]:
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
    return dt.date().isoformat()


def is_regular_quest_cycle(dt):
    cycle_time = datetime.combine(
        dt.date(),
        time(hour=QUEST_SCHEDULE_HOUR, minute=QUEST_SCHEDULE_MINUTE),
        tzinfo=TZ
    )

    if cycle_time < QUEST_SCHEDULE_ANCHOR:
        return False

    days_since_anchor = (cycle_time.date() - QUEST_SCHEDULE_ANCHOR.date()).days
    return days_since_anchor % QUEST_DURATION_DAYS == 0


def next_regular_quest_cycle(after_time):
    for days_ahead in range(0, 90):
        candidate_date = after_time.date() + timedelta(days=days_ahead)
        candidate = datetime.combine(
            candidate_date,
            time(hour=QUEST_SCHEDULE_HOUR, minute=QUEST_SCHEDULE_MINUTE),
            tzinfo=TZ
        )

        if candidate <= after_time:
            continue

        if is_regular_quest_cycle(candidate):
            return candidate

    return after_time + timedelta(days=QUEST_DURATION_DAYS)


def forced_quest_due_date(now):
    next_cycle = next_regular_quest_cycle(now)
    days_until_next_cycle = (next_cycle.date() - now.date()).days

    if days_until_next_cycle <= QUEST_FORCE_SKIP_DAYS:
        skipped_cycle = next_cycle
        due_at = next_regular_quest_cycle(skipped_cycle + timedelta(seconds=1))
        return due_at, skipped_cycle

    return next_cycle, None


@tasks.loop(minutes=30)
async def biweekly_quest_report():
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


quest_group = app_commands.Group(
    name="quest",
    description="Quest commands"
)


@quest_group.command(name="force", description="Force-post a new quest cycle and keep the regular Tuesday schedule")
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

        data.setdefault("quest_history_v2", [])
        data["quest_history_v2"].append(copy.deepcopy(quest))
        data["active_quests_v2"][selected_group] = quest

        save_data(data)

    announcement = (
        f"✅ **Quest/Event Complete!**\n"
        f"{clan_mention(selected_group)}\n\n"
        f"**{selected_group}: {quest.get('title', 'Quest')}**\n"
        f"Category: **{QUEST_CATEGORY_LABELS.get(quest.get('category'), 'Quest')}**\n\n"
        f"🎁 **Reward:** {reward_text}"
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
        f"The replacement quest{'s' if len(reset_results) != 1 else ''} will still be due on **{due_at.strftime('%B %d, %Y')}**, so the regular Tuesday 2-week schedule stays intact.",
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
            message += f"**Faction**: {faction}\n"

        message += (
            f"**Age**: {age_text}\n"
            f"**Status**: {status}\n"
            f"**Current Health**: {injury_text}\n"
            f"**Hunger**: {hunger_text}\n"
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
    description="View cats eligible for apprentice, warrior, or elder ceremonies"
)
async def upcomingceremonies(interaction: discord.Interaction):
    async with data_lock:
        apprentice_ready = []
        warrior_ready = []
        elder_ready = []

        for name, cat in data.get("cats", {}).items():
            prepare_cat_record(name, cat)

            if str(cat.get("status", "Alive")).lower() == "dead":
                continue

            clan = cat.get("clan", "Unknown Clan")
            rank = cat.get("rank")
            age = cat.get("age", 0)

            if rank == "Kit" and age >= 6:
                apprentice_ready.append((clan, name, age))

            elif rank == "Apprentice" and age >= 11:
                warrior_ready.append((clan, name, age))

            elif rank in AGING_TO_ELDER_RANKS and age >= 95:
                elder_ready.append((clan, name, age, rank))

    def sort_key(item):
        return (item[0], item[1])

    apprentice_ready.sort(key=sort_key)
    warrior_ready.sort(key=sort_key)
    elder_ready.sort(key=sort_key)

    lines = [
        "🌙 **Upcoming Ceremonies**",
        "",
        "This shows cats who are currently eligible for rank-related ceremonies.",
        ""
    ]

    lines.append("### 🐾 Kits Eligible to Become Apprentices")
    if apprentice_ready:
        current_clan = None

        for clan, name, age in apprentice_ready:
            if clan != current_clan:
                current_clan = clan
                lines.append(f"\n**{clan}**")

            lines.append(f"🐾 **{name}** — {age} moons")
    else:
        lines.append("No kits are currently eligible to become apprentices.")

    lines.append("")
    lines.append("### ⚔ Apprentices Eligible for Warrior Assessments")
    if warrior_ready:
        current_clan = None

        for clan, name, age in warrior_ready:
            if clan != current_clan:
                current_clan = clan
                lines.append(f"\n**{clan}**")

            lines.append(f"⚔ **{name}** — {age} moons")
    else:
        lines.append("No apprentices are currently eligible for warrior assessments.")

    lines.append("")
    lines.append("### 🍂 Warriors Eligible to Retire as Elders")
    if elder_ready:
        current_clan = None

        for clan, name, age, rank in elder_ready:
            if clan != current_clan:
                current_clan = clan
                lines.append(f"\n**{clan}**")

            lines.append(f"🍂 **{name}** — {age} moons | Current Rank: {rank}")
    else:
        lines.append("No warriors are currently eligible to retire as elders.")

    await interaction.response.send_message("\n".join(lines)[:1900])

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
        "`/catinfo [Name]` — View full details about a cat, including hunger status\n"
        "`/cats [Clan]` — View all cats by clan or all clans\n"
        "`/clan [ClanName]` — View one clan roster\n"
        "`/cattinder [Name] [Clan]` — Find age-appropriate romance options\n"
        "`/question` — Random OC question prompt system\n"
        "`/needsmentor` — View apprentices and medicine cat apprentices who do not currently have mentors\n"
        "`/upcomingceremonies` — View kits, apprentices, and older warriors eligible for ceremonies or assessments\n\n"

        "🍽️ **Feeding / Hunger Commands**\n"
        "`/feed cat [Name]` — Feed an OC normal prey and raise their hunger level by 1\n"
        "`/feed cat [Name] [Large Prey]` — Feed an OC large prey and raise their hunger level by 2\n"
        "`/feed hunger [Clan]` — Check which cats in a Clan are Starving, Hungry, or Satisfied\n"
        "Hunger affects hunting rolls: Starving -2, Hungry -1, Satisfied no change, Full +1, Well Fed +2.\n\n"

        "🌦️ **Weather / World Commands**\n"
        "`/weather` or `/weatherreport` — View the current weekly weather report, if available.\n\n"

        "📜 **Quest / Story Commands**\n"
        "Current quests/events post every 2 real-life weeks on Tuesdays at 9 AM. The pool rolls 35% hunting, 20% social, 20% herb patrol, 10% sickness/crisis, and 15% wild animal events.\n"
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
bot.tree.add_command(activity_group)
bot.tree.add_command(membership_group)
bot.tree.add_command(feed_group)
bot.tree.add_command(quest_group)
bot.tree.add_command(prophecy_group)
keep_alive()
print("Starting Discord bot. Server Members Intent is required; Message Content Intent is disabled.")
bot.run(TOKEN)
