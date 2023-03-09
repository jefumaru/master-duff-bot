# Master Duff Bot
Code that powers the "Master Duff" bot in the Mario Golf Super Rush (MGSR) Discord server

### Purposes
* Currently Master Duff is being used to calculate some basic and advanced player stats for people who play MGSR competitively in our Elo-based Ranked Ladder
* The Elo Ladder is powered by TeamUp Bot, the stats are calcuated by scraping the channel where we report the results of those matches and parsing the standardized text that the TeamUp Bot outputs
* These rankings and metrics help us decide seeding for in-server tournaments like March Madness as well as our upcoming 2nd League Season

### Going Forward
* The bot is not very interactive at the moment, but when time permits I intend to enable basic Bot-like functionality such as a command akin to "Hi Master Duff, what is my Max Elo ever attained?"
* Right now the "All-Time" stats only go as far back as Jan 20th, 2022 because the current dedictaed `elo-recording` channel was not established until then.  However, the Elo Ladder was actually first started in Dec 2021 but original the reports/records were scattered in a variety of channels.  If time permits, I'd like to add code to collect those early reports as well.
* Hitting the Discord API every time we run the Bot is wasteful, start with caching the lookups locally (maybe up to last 1-2 weeks since old records are never edited).  For now a local file will suffice, in the long-run, if time and funds permit, set up an actual quick-access tabular database for easy queries.

### Thanks
* Mrs Chippy, Founder of the MGSR Server Elo Ladder
* TeamUp Bot and its Creator
