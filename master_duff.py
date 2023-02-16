import discord
import json
import os

RECORDING_CHANNEL = 933895315373838416
TEAMUP_SUPPORT_MSG = "Visit the Team Up Discord Support Server"
RECORD_UNDO_MSG = "Result Removed"

ACCOUNT_ALIAS_LOOKUP = {
    "Blue Toad": "BT",
    "drolo253": "Drolo",
    "Drolo253": "Drolo",
    "Fat Bowser": "Fat BiddyBuddy",
    "\\ud835\\udcd5\\ud835\\udcfb\\ud835\\udcf8\\ud835\\udcfc\\ud835\\udcfd\\ud835\\udd02 \\ud835\\udcdc\\ud835\\udcf8\\ud835\\udcf8\\ud835\\udcf7": "Frosty Moon",
    "Kairi (Uncertified Player)": "Goldy",
    "*Henry*": "**Henry**",
    "__Henry__": "**Henry**",
    "LeSinge\\ud83d\\udc12": "LeSinge",
    "[T\\u00e4hl] LeSinge\\ud83d\\udc12": "LeSinge",
    "Lucifurs friend": "LucifursFriend",
    "DoctahKush": "MastahKush",
    "Deputy MI-NEIGHBOR-GUY": "NEIGHBOR-GUY",
    "MI-NEIGHBOR-GUY": "NEIGHBOR-GUY",
    "Shawn2Sh\u00f8t": "Shawn2Shot",
    "Shawn2Strk": "Shawn2Shot",
    "SturgeonHunter0.75 (mjScott)": "SturgeonHunter0.75",
    "ThatOneGuy": "TheYosh",
    "\\ud83c\\udfbcWILL\\u2666I\\u2666AM\\u26f3": "Will",
    "\\u0561\\u0268\\u057c\\u0236\\u025b\\u0280": "winter"
}

bot_intents = discord.Intents.default()
bot_intents.message_content = True
client = discord.Client(intents=bot_intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await produceStats()

@client.event
async def on_message(message):
    if message.author.display_name != "manmaru":
        return

    print(message.content)
    if message.content.startswith('Are you Master Duff'):
        await message.channel.send('Yes, indeed I am')

async def produceStats():
    elo_channel = client.get_channel(RECORDING_CHANNEL)
    elo_stats = {}
    need_to_undo_count = 0

    print("Fetching messages...")
    async for message in elo_channel.history(limit = 1000):
        if len(message.embeds) == 0:
            continue

        elo_info = message.embeds[0].to_dict()
        if "fields" not in elo_info.keys():
            continue

        try:
            first_item_name = elo_info["fields"][0]["name"]
        except Exception:
            first_item_name = ""

        if first_item_name == TEAMUP_SUPPORT_MSG:
            continue

        if first_item_name == RECORD_UNDO_MSG:
            need_to_undo_count += 1
            continue

        if need_to_undo_count > 0:
            # Skip a record that has been marked as undone
            need_to_undo_count -= 1
            continue

        time_stamp = message.created_at
        record_stats = evaluateRecord(elo_info["fields"])
        if record_stats is None:
            continue

        for player_account in record_stats.keys():
            record = record_stats[player_account]
            before_elo = record["before_elo"]
            if player_account not in elo_stats.keys():
                elo_stats[player_account] = {
                    "wins": 0,
                    "losses": 0,
                    "ties": 0,
                    "max_elo": before_elo,
                    "min_elo": before_elo,
                    "first_round": time_stamp,
                    "last_round": time_stamp,
                }

            elo_stats[player_account]["wins"] += len(record["wins"])
            elo_stats[player_account]["losses"] += len(record["losses"])
            elo_stats[player_account]["ties"] += len(record["ties"])

            # Messages are scanned in descending order
            elo_stats[player_account]["first_round"] = time_stamp

            after_elo = record["after_elo"]
            if before_elo > elo_stats[player_account]["max_elo"]:
                elo_stats[player_account]["max_elo"] = before_elo
            if after_elo > elo_stats[player_account]["max_elo"]:
                elo_stats[player_account]["max_elo"] = after_elo

            if before_elo < elo_stats[player_account]["min_elo"]:
                elo_stats[player_account]["min_elo"] = before_elo
            if after_elo < elo_stats[player_account]["min_elo"]:
                elo_stats[player_account]["min_elo"] = after_elo

    print("")
    sorted_players = sorted(elo_stats.keys(), key=str.lower)
    for player in sorted_players:
        player_stats = elo_stats[player]
        total_matches = player_stats["wins"] + player_stats["losses"] + player_stats["ties"]
        adjusted_wins = player_stats["wins"] + (0.5 * player_stats["ties"])
        win_percentage = 1.0 * adjusted_wins / total_matches
        if win_percentage == 1.0:
            display_pct = "1.000"
        else:
            rounded_pct = round(win_percentage, 3)
            display_pct = ("{0:.3f}".format(rounded_pct))[1:]

        output = "{}: Matchups={}, {}-{}-{}, PCT={}, MaxElo={}, MinElo={}, FirstRound={}, LastRound={}".format(
            player,
            total_matches,
            player_stats["wins"],
            player_stats["losses"],
            player_stats["ties"],
            display_pct,
            player_stats["max_elo"],
            player_stats["min_elo"],
            player_stats["first_round"].strftime("%Y-%m-%d"),
            player_stats["last_round"].strftime("%Y-%m-%d"),
        )
        print(output)
    
def evaluateRecord(record_fields):
    record_count = len(record_fields)
    parsed_records = []
    record_stats = {}
    try:
        for single_record in record_fields:
            record_entry = {}
            value_parts = single_record["value"].split("\n")
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
                if player_placement < record_placement:
                    record_stats[player_account]["wins"].append(record_player)
                elif player_placement == record_placement:
                    record_stats[player_account]["ties"].append(record_player)
                else:
                    record_stats[player_account]["losses"].append(record_player)

        return record_stats
    except Exception:
        print(json.dumps(record_fields))
        return None

def normalizeAccountName(account_name):
    sanitized_name = json.dumps(account_name).replace("\"", "")
    if sanitized_name in ACCOUNT_ALIAS_LOOKUP:
        return ACCOUNT_ALIAS_LOOKUP[sanitized_name]

    return account_name

client.run('the-key')
