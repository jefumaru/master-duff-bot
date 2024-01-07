# Master Duff Bot
Code that powers the "Master Duff" bot in the Mario Golf Super Rush (MGSR) Discord server

### Purposes
* Currently Master Duff is being used to calculate some basic and advanced player stats for people who play MGSR competitively in our Elo-based Ranked Ladder
* The Elo Ladder is powered by TeamUp Bot, the stats are calcuated by scraping the channel where we report the results of those matches and parsing the standardized text that the TeamUp Bot outputs
* These rankings and metrics help us decide seeding for in-server tournaments like March Madness as well as our upcoming 2nd League Season

### How to Run
* Run locally with Python 3.10.9, just `python3 master_duff.py` will log the Bot into the server, and make it live
* Auth key, not stored here, is needed to run it.  Please contact me or a Server Admin about how to get this.

### Example Record Format
This is what the JSON captures by the output of the TeamUp bot looks like:
```json
{
  "title": "Game Recorded: **1v1v1v1 MGSR**",
  "color": 16730441,
  "type": "rich",
  "description": ":trophy: [Visit the 1s leaderboard](https://teamupdiscord.com/leaderboard/server/812794920158363688/game/bWdzcg==/versus/1) :trophy:",
  "fields": [
    {
      "name": ":first_place: 1st :first_place:",
      "value": "***norris00000***\n1s Rating\n(1382 -> 1407)",
      "inline": True
    },
    {
      "name": ":first_place: 1st :first_place:",
      "value": "***speedmcdemon***\n1s Rating\n(1512 -> 1516)",
      "inline": True
    },
    {
      "name": ":third_place: 3rd :third_place:",
      "value": "***maxn301***\n1s Rating\n(1429 -> 1404)",
      "inline": True
    },
    {
      "name": ":third_place: 3rd :third_place:",
      "value": "***.grauwulf***\n1s Rating\n(1305 -> 1301)",
      "inline": True
    }
  ],
  "footer": {
    "text": "Use the `/undo-record` command to undo this recording\nUse the `/view reputation` command to view a player's feedback rating."
  },
}
```

### Going Forward
* The bot is not very interactive at the moment, but when time permits I intend to enable basic Bot-like functionality such as a command akin to "Hi Master Duff, what is my Max Elo ever attained?"
* Right now the "All-Time" stats only go as far back as Jan 20th, 2022 because the current dedictaed `elo-recording` channel was not established until then.  However, the Elo Ladder was actually first started in Dec 2021 but original the reports/records were scattered in a variety of channels.  If time permits, I'd like to add code to collect those early reports as well.
* Hitting the Discord API every time we run the Bot is wasteful, start with caching the lookups locally (maybe up to last 1-2 weeks since old records are never edited).  For now a local file will suffice, in the long-run, if time and funds permit, set up an actual quick-access tabular database for easy queries.

### Thanks
* Mrs Chippy, Founder of the MGSR Server Elo Ladder
* TeamUp Bot and its Creator
