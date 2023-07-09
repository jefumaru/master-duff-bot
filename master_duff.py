from dateutil.relativedelta import relativedelta
from datetime import datetime, timezone

import discord
import json

# Script Config
SHOW_OPPONENT_STATS_FOR = None
MSG_LIMIT = None

# Channel IDs
RECORDING_CHANNEL = 933895315373838416

# Player Historical Account Name Changes
## If a player changes their nickname, they do not need listed here
## However if they change their actual Discord account name, they need
## added here so that the pre/post account name change stats map to same person
ACCOUNT_ALIAS_LOOKUP = {
    "blue toad": "bt",
    "bt2946": "bt",
    "coos_does_things": "coos",
    "sdreb3421": "dr. ebick",
    "dr.ebick": "dr. ebick",
    "drolo253": "drolo",
    "drolo253": "drolo",
    "fat bowser": "fat biddybuddy",
    "\\ud835\\udcd5\\ud835\\udcfb\\ud835\\udcf8\\ud835\\udcfc\\ud835\\udcfd\\ud835\\udd02 \\ud835\\udcdc\\ud835\\udcf8\\ud835\\udcf8\\ud835\\udcf7": "frosty moon",
    "kairi (uncertified player)": "goldy",
    "saru": "goosebumps",
    "graveyard420woo": "graveyard",
    "**henry**": "henry",
    "*henry*": "henry",
    "__henry__": "henry",
    "henry8388": "henry",
    "henry9095": "henry",
    "lc9514": "lc",
    "lesinge": "le singe",
    "lesinge\\ud83d\\udc12": "le singe",
    "[t\\u00e4hl] lesinge\\ud83d\\udc12": "le singe",
    "lucifurs friend": "lucifursfriend",
    "mastah[jedi]kush": "mastahkush",
    "doctahkush": "mastahkush",
    "jefumaru": "maru",
    "manmaru": "maru",
    "norris00000": "norris",
    "onetrueed": "me, ed",
    "miyong1986": "ladymiyong",
    "deputy mi-neighbor-guy": "neighbor-guy",
    "ironfist68": "poolguy68",
    "mi-neighbor-guy": "neighbor-guy",
    "shawn2sh\\u00f8t": "shawn2shot",
    "shawn2strk": "shawn2shot",
    "slickssb": "slick",
    "slickssbu": "slick",
    "sturgeonhunter0.75 (mjscott)": "sturgeonhunter0.75",
    "theyosh": "thatoneguy",
    "tyoshig19": "thatoneguy",
    "theodore vellum": "theodorevellum",
    "willskit4": "will",
    "willzilla": "will",
    "\\ud83c\\udfbcwill\\u2666i\\u2666am\\u26f3": "will",
    "\\u0561\\u0268\\u057c\\u0236\\u025b\\u0280": "winter"
}

# Strings that appear in Non-Success Recording cases
TEAMUP_SUPPORT_MSG = "Visit the Team Up Discord Support Server"
RECORD_UNDO_MSG = "Result Removed"

# Output skeletons
TSV_LINE = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}"
PER_PLAYER_TSV_LINE = "{}\t{}\t{}\t{}\t{}\t{}"

# Stat Calculation Helpers
ELITE_LEVEL_ELO = 1500
PRO_LEVEL_ELO = 1400
ONE_MONTH_AGO = datetime.now(timezone.utc) + relativedelta(months = -1)
THREE_MONTHS_AGO = datetime.now(timezone.utc) + relativedelta(months = -3)

# Bot setup, allow it to read message content from channel
bot_intents = discord.Intents.default()
bot_intents.message_content = True
client = discord.Client(intents=bot_intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    # Calculuate and output stats on right after boot-up
    await produceStats()

@client.event
async def on_message(message):
    # TODO: Add actual bot interactivity someday
    if message.author.display_name != "manmaru":
        return

    if message.content.startswith('Are you Master Duff'):
        await message.channel.send('Yes, indeed I am')

async def produceStats():
    # Get Discord channel object
    elo_channel = client.get_channel(RECORDING_CHANNEL)

    # Init "stack" variable to track how many records need dropped due to undo
    need_to_undo_count = 0

    elo_stats = {}
    messages_for_stats = []

    # The below method iterates on every message in the channel
    ## "limit = None" means entire history of messages
    ## if limit is specified it will be most recent {limit} messages
    ## This is the main Discord API method we use to fetch message history
    print("Checking cache...")
    try:
        cache_file = open("mgsr_discord_elo.cache", "r")
        messages_for_stats = json.load(cache_file)[0:MSG_LIMIT]
    except:
        messages_for_stats = []

    if len(messages_for_stats) == 0:
        print("Fetching messages...")
        async for message in elo_channel.history(limit = MSG_LIMIT):

            # The text of TeamUp Elo reports comes in as an "embed" in a message, not raw text
            # That is why in Discord the text looks slightly indented with non-standard formatting
            if len(message.embeds) == 0:
                # If it's a plain message (no embeds), it is not an Elo report -- ignore it
                continue

            elo_info = message.embeds[0].to_dict()
            if "fields" not in elo_info.keys():
                continue

            try:
                # Title of first embed
                # Will be "Game Recorded: " for the Elo reports we are seeking
                first_item_name = elo_info["fields"][0]["name"]
            except Exception:
                first_item_name = ""

            if first_item_name == TEAMUP_SUPPORT_MSG:
                continue

            if first_item_name == RECORD_UNDO_MSG:
                # Bump the stack indicating subsequent report should be undone
                # Next actual Elo report will be ignored if this is greater than zero
                need_to_undo_count += 1
                continue

            if need_to_undo_count > 0:
                # Skip a record that has been marked as undone
                need_to_undo_count -= 1
                continue

            # This message is a real record which will count towards the stats
            # Insert at start of list to preserve time-descending assumption
            messages_for_stats.insert(0, {
                "embed_dict": elo_info,
                "created_time": message.created_at.timestamp(),
            })

        # TODO This is the right spot to write to the lookup cache
        # Will need to end the channel-fetch loop here, and do a second loop for evaluateRecord
        write_cache_file = open("mgsr_discord_elo.cache", "w")
        write_cache_file.write(json.dumps(messages_for_stats))
        write_cache_file.close()

    for message in messages_for_stats:
        elo_info = message["embed_dict"]

        # Process raw strings from Elo report into structured player results
        record_stats = evaluateRecord(elo_info["fields"])
        if record_stats is None:
            continue

        time_stamp = datetime.fromtimestamp(message["created_time"], tz=timezone.utc)
        for player_account in record_stats.keys():

            # Add the individual W/L/T and Elo info from a single report to the overall stats dataset
            record = record_stats[player_account]
            before_elo = record["before_elo"]
            if player_account not in elo_stats.keys():
                # Add new blank record in overall Elo dataset if this player name hasn't appeared yet
                elo_stats[player_account] = {
                    "rounds": 0,
                    "wins": [],
                    "losses": [],
                    "ties": [],
                    "max_elo_full": before_elo,
                    "max_elo_date": None,
                    "min_elo_full": before_elo,
                    "max_elo_3m": before_elo,
                    "min_elo_3m": before_elo,
                    "max_elo_1m": before_elo,
                    "min_elo_1m": before_elo,
                    "cleared_1300_date": None,
                    "cleared_1400_date": None,
                    "cleared_1500_date": None,
                    "cleared_1600_date": None,
                    "cleared_1700_date": None,
                    "first_round": time_stamp,
                    # Since message are scanned in time-descending order, this value will never need updated
                    "last_round": time_stamp,
                }

            elo_stats[player_account]["rounds"] += 1
            elo_stats[player_account]["wins"].extend(record["wins"])
            elo_stats[player_account]["losses"].extend(record["losses"])
            elo_stats[player_account]["ties"].extend(record["ties"])

            # Continually update "first_round" with current time since record messages are scanned in time-descending order
            elo_stats[player_account]["first_round"] = time_stamp

            after_elo = record["after_elo"]

            # Update 1-month min/max Elo
            if time_stamp >= ONE_MONTH_AGO:
                if before_elo > elo_stats[player_account]["max_elo_1m"]:
                    elo_stats[player_account]["max_elo_1m"] = before_elo
                if after_elo > elo_stats[player_account]["max_elo_1m"]:
                    elo_stats[player_account]["max_elo_1m"] = after_elo

                if before_elo < elo_stats[player_account]["min_elo_1m"]:
                    elo_stats[player_account]["min_elo_1m"] = before_elo
                if after_elo < elo_stats[player_account]["min_elo_1m"]:
                    elo_stats[player_account]["min_elo_1m"] = after_elo

            # Update 3-month min/max Elo
            if time_stamp >= THREE_MONTHS_AGO:
                if before_elo > elo_stats[player_account]["max_elo_3m"]:
                    elo_stats[player_account]["max_elo_3m"] = before_elo
                if after_elo > elo_stats[player_account]["max_elo_3m"]:
                    elo_stats[player_account]["max_elo_3m"] = after_elo

                if before_elo < elo_stats[player_account]["min_elo_3m"]:
                    elo_stats[player_account]["min_elo_3m"] = before_elo
                if after_elo < elo_stats[player_account]["min_elo_3m"]:
                    elo_stats[player_account]["min_elo_3m"] = after_elo

            # Update All-Time min/max Elo
            if before_elo > elo_stats[player_account]["max_elo_full"]:
                elo_stats[player_account]["max_elo_full"] = before_elo
                elo_stats[player_account]["max_elo_date"] = time_stamp
            if after_elo > elo_stats[player_account]["max_elo_full"]:
                elo_stats[player_account]["max_elo_full"] = after_elo
                elo_stats[player_account]["max_elo_date"] = time_stamp

            if before_elo < elo_stats[player_account]["min_elo_full"]:
                elo_stats[player_account]["min_elo_full"] = before_elo
            if after_elo < elo_stats[player_account]["min_elo_full"]:
                elo_stats[player_account]["min_elo_full"] = after_elo

            # Update Elo threshold-clearing timestamps
            elo_stats[player_account]["cleared_1300_date"] = getEloThresholdChange(
                before_elo,
                after_elo,
                1300,
                elo_stats[player_account]["cleared_1300_date"],
                time_stamp,
            )
            elo_stats[player_account]["cleared_1400_date"] = getEloThresholdChange(
                before_elo,
                after_elo,
                1400,
                elo_stats[player_account]["cleared_1400_date"],
                time_stamp,
            )
            elo_stats[player_account]["cleared_1500_date"] = getEloThresholdChange(
                before_elo,
                after_elo,
                1500,
                elo_stats[player_account]["cleared_1500_date"],
                time_stamp,
            )
            elo_stats[player_account]["cleared_1600_date"] = getEloThresholdChange(
                before_elo,
                after_elo,
                1600,
                elo_stats[player_account]["cleared_1600_date"],
                time_stamp,
            )
            elo_stats[player_account]["cleared_1700_date"] = getEloThresholdChange(
                before_elo,
                after_elo,
                1700,
                elo_stats[player_account]["cleared_1700_date"],
                time_stamp,
            )

    print("")

    # Add in more advanced stats, such as win rate against elite players
    full_stats = calculuateSupplementalStats(elo_stats)

    if SHOW_OPPONENT_STATS_FOR is not None and SHOW_OPPONENT_STATS_FOR in full_stats:
        # Script should output the per-oppoennt W/L/T stats for a single specific player
        outputPlayerMatchupResults(SHOW_OPPONENT_STATS_FOR, full_stats[SHOW_OPPONENT_STATS_FOR])
    else:
        # Script should output stats for all players
        outputFullStats(full_stats)

def calculuateSupplementalStats(elo_stats):
    # Get the list of players who will count as "elite" in the advanced stats
    elite_players = getPlayersByMaxEloCutoff(elo_stats, ELITE_LEVEL_ELO)

    all_players = elo_stats.keys()
    for player in all_players:
        elo_stats[player]["elite_wins"] = 0
        elo_stats[player]["elite_losses"] = 0
        elo_stats[player]["elite_ties"] = 0

        # Add a W/L/T if the opponent in question has ever reached the Elite level Elo threshold
        for win_against_player in elo_stats[player]["wins"]:
            if win_against_player in elite_players:
                elo_stats[player]["elite_wins"] += 1

        for lose_to_player in elo_stats[player]["losses"]:
            if lose_to_player in elite_players:
                elo_stats[player]["elite_losses"] += 1

        for tie_with_player in elo_stats[player]["ties"]:
            if tie_with_player in elite_players:
                elo_stats[player]["elite_ties"] += 1

    return elo_stats

def outputFullStats(elo_stats):
    # Column titles for spreadsheet-friendly TSV output
    print(TSV_LINE.format(
        "Player Account",
        "Total Rounds Played",
        "PCT",
        "Total Matchups",
        "Total Wins",
        "Total Losses",
        "Total Ties",
        "1500+ PCT",
        "Percent Matchups Against 1500+",
        "1500+ Matchups",
        "1500+ Wins",
        "1500+ Losses",
        "1500+ Ties",
        "Max Elo (All-Time)",
        "Date of Max Elo",
        "Max Elo (3 months)",
        "Max Elo (1 month)",
        "Min Elo (All-Time)",
        "Min Elo (3 months)",
        "Min Elo (1 month)",
        "First Cleared 1300",
        "First Cleared 1400",
        "First Cleared 1500",
        "First Cleared 1600",
        "First Cleared 1700",
        "First Recorded Round",
        "Last Recorded Round",
    ))

    sorted_players = sorted(elo_stats.keys(), key=str.lower)
    for player in sorted_players:
        player_stats = elo_stats[player]

        # Most of this logic is to format the "elo_stats" dataset for friendly output into spreadsheet
        win_count = len(player_stats["wins"])
        loss_count = len(player_stats["losses"])
        tie_count = len(player_stats["ties"])
        total_matches = win_count + loss_count + tie_count

        elite_win_count = player_stats["elite_wins"]
        elite_loss_count = player_stats["elite_losses"]
        elite_tie_count = player_stats["elite_ties"]
        elite_matches = elite_win_count + elite_loss_count + elite_tie_count
        elite_match_rate = round(100.0 * elite_matches / total_matches, 1)

        # The "min/max Elo" values won't be accurate for players who haven't played within the specified time period
        # So, use this to just show a blank value for a player who has no records within last N months
        show_last_3m = player_stats["last_round"] >= THREE_MONTHS_AGO
        show_last_1m = player_stats["last_round"] >= ONE_MONTH_AGO

        output = TSV_LINE.format(
            player,
            player_stats["rounds"],
            renderWinPercent(win_count, tie_count, total_matches),
            total_matches,
            win_count,
            loss_count,
            tie_count,
            renderWinPercent(elite_win_count, elite_tie_count, elite_matches),
            "{0:.1f}".format(elite_match_rate),
            elite_matches,
            elite_win_count,
            elite_loss_count,
            elite_tie_count,
            player_stats["max_elo_full"],
            renderDate(player_stats["max_elo_date"]),
            player_stats["max_elo_3m"] if show_last_3m else "",
            player_stats["max_elo_1m"] if show_last_1m else "",
            player_stats["min_elo_full"],
            player_stats["min_elo_3m"] if show_last_3m else "",
            player_stats["min_elo_1m"] if show_last_1m else "",
            renderDate(player_stats["cleared_1300_date"]),
            renderDate(player_stats["cleared_1400_date"]),
            renderDate(player_stats["cleared_1500_date"]),
            renderDate(player_stats["cleared_1600_date"]),
            renderDate(player_stats["cleared_1700_date"]),
            renderDate(player_stats["first_round"]),
            renderDate(player_stats["last_round"]),
        )
        print(output)
    
def outputPlayerMatchupResults(target_player, player_stats):
    results_per_opponent = {}
    for won_against_player in player_stats["wins"]:
        if not won_against_player in results_per_opponent:
            results_per_opponent[won_against_player] = initWinLossTieDict()

        results_per_opponent[won_against_player]["wins"] += 1

    for lost_to_player in player_stats["losses"]:
        if not lost_to_player in results_per_opponent:
            results_per_opponent[lost_to_player] = initWinLossTieDict()

        results_per_opponent[lost_to_player]["losses"] += 1

    for tied_with_player in player_stats["ties"]:
        if not tied_with_player in results_per_opponent:
            results_per_opponent[tied_with_player] = initWinLossTieDict()

        results_per_opponent[tied_with_player]["ties"] += 1

    sorted_opponents = sorted(results_per_opponent.keys(), key=str.lower)

    print("Per Opponent Stats for MGSR Player: {}".format(target_player))
    print("")

    # More simple spreadsheet-friendly TSV output format for per-opponent record stats
    print(PER_PLAYER_TSV_LINE.format(
        "Opponents",
        "Matches",
        "PCT",
        "W",
        "L",
        "T",
    ))

    for opponent_name in sorted_opponents:
        opponent_results = results_per_opponent[opponent_name]
        total_matches = opponent_results["wins"] + opponent_results["losses"] + opponent_results["ties"]

        output = PER_PLAYER_TSV_LINE.format(
            opponent_name,
            total_matches,
            renderWinPercent(opponent_results["wins"], opponent_results["ties"], total_matches),
            opponent_results["wins"],
            opponent_results["losses"],
            opponent_results["ties"],
        )
        print(output)


def evaluateRecord(record_fields):
    parsed_records = []
    record_stats = {}
    try:
        # There are one of these for each player that was in the report
        # it contains the player account name, placement, and before/after Elo
        for single_record in record_fields:
            record_entry = {}
            value_parts = single_record["value"].split("\n")

            # Sanitize the account name so we can correctly organize and attribute stats
            player_account = normalizeAccountName(value_parts[0].replace("***", ""))
            record_entry["player"] = player_account

            match_placement = single_record["name"]
            if "1st" in match_placement:
                record_entry["placement"] = 1
            elif "2nd" in match_placement:
                record_entry["placement"] = 2
            elif "3rd" in match_placement:
                record_entry["placement"] = 3
            elif "4th" in match_placement:
                record_entry["placement"] = 4

            elo_parts = value_parts[2].split(" ")
            before_elo = elo_parts[0].replace("(", "")
            after_elo = elo_parts[2].replace(")", "")
            record_entry["before_elo"] = int(before_elo)
            record_entry["after_elo"] = int(after_elo)
            parsed_records.append(record_entry)

            # Init object to evaluate the W/L/T outcome of this record
            record_stats[player_account] = {
                "placement": record_entry["placement"],
                "before_elo": record_entry["before_elo"],
                "after_elo": record_entry["after_elo"],
                "wins": [],
                "losses": [],
                "ties": [],
            }

        for player_account in record_stats.keys():
            player_placement = record_stats[player_account]["placement"]
            for record in parsed_records:
                if record["player"] == player_account:
                    continue

                record_placement = record["placement"]
                record_player = record["player"]

                # This can count both total W/L/T as well as per-opponent records
                if player_placement < record_placement:
                    record_stats[player_account]["wins"].append(record_player)
                elif player_placement == record_placement:
                    record_stats[player_account]["ties"].append(record_player)
                else:
                    record_stats[player_account]["losses"].append(record_player)

        return record_stats
    except Exception:
        return None

def normalizeAccountName(raw_name):
    account_name = raw_name.lower()
    sanitized_name = json.dumps(account_name).replace("\"", "")
    if sanitized_name in ACCOUNT_ALIAS_LOOKUP:
        return ACCOUNT_ALIAS_LOOKUP[sanitized_name]

    return account_name

def getEloThresholdChange(before_elo, after_elo, elo_threshold, current_clear_date, record_timestamp):
    # Part of the logic of this method is based on the fact that all record messages are scanned in time-descending order
    # If that assumption was ever changed, this method would also need updated

    if before_elo < elo_threshold and after_elo >= elo_threshold:
        # A threshold is being crossed in this record

        if current_clear_date is None:
            # First time (in time-descending order) this threshold was crossed
            return record_timestamp

        if record_timestamp < current_clear_date:
            # This threshold-cross happened earlier than the previously noted one
            return record_timestamp

    if before_elo >= elo_threshold:
        # Clear marked date because an earlier record was already above that threshold
        return None

    return current_clear_date

def initWinLossTieDict():
    return {
        "wins": 0,
        "losses": 0,
        "ties": 0,
    }

def renderWinPercent(win_count, tie_count, total_matches):
    # Ensure 100% win perentage is rendered as "1.000", others as 3-digit numbers like ".xyz"
    if total_matches == 0:
        return ".000"

    adjusted_wins = win_count + (0.5 * tie_count)
    win_percentage = 1.0 * adjusted_wins / total_matches
    if win_percentage == 1.0:
        return "1.000"

    rounded_pct = round(win_percentage, 3)
    return ("{0:.3f}".format(rounded_pct))[1:]

def renderDate(raw_datetime):
    if raw_datetime == "N/A":
        return "Not Enough Data"

    if raw_datetime is None:
        return ""

    return raw_datetime.strftime("%Y-%m-%d")

def getPlayersByMaxEloCutoff(stats_per_player, max_elo_cutoff):
    exceeding_players = []
    for player in stats_per_player.keys():
        if stats_per_player[player]["max_elo_full"] > max_elo_cutoff:
            exceeding_players.append(player)
    return exceeding_players

# This is the API security key which allows the MGSR server to identify this code as Master Duff
# In GitHub, this is a fake value, use the real value in the environment where the Bot is actually run
client.run('the-key')
