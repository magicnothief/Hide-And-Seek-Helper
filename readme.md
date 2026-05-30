# Scrap Mechanic: Hide and Seek Mod

Welcome to the **Hide and Seek Mod** for Scrap Mechanic! This mod injects custom server rules into the game's Challenge Mode, turning any challenge map into an automated, multiplayer game of hide and seek. 

This script was made inspired by [Scrapman's](https://www.youtube.com/@scrapman), [Kan's](https://www.youtube.com/@kANGaming) and [Kosmo's](https://www.youtube.com/@darealkosmo) videos and made for them, focusing on improving hide and seek gameplay in Scrap Mechanic.

**This mod modifies the code of the game!**

---

## Features
* **Backup:** it backs up any files it modifies
* **Auto-start:** it auto starts with the map's timer.
* **Roles:** The seekers do not see the hunters names.
* **Role memory:** it remembers your last role if you reset the map (but not when you quit).
* **Hiding phase**
* **Seeking phase** 
* **Automatic Proximity Tagging:** Every 5 in-game ticks, the server calculates the exact 3D distance between all Seekers and Hiders. If a Seeker gets within 0.7 blocks/meters of a Hider, the Hider is instantly "caught". Unfortunately spudgun shooting couldn't work due to some limitations.
* **Hint time:** To prevent games from lasting forever, the mod automatically reminds hiders to make noise (or shoot spudguns) at set intervals (*surely not because sometimes they forget in the videos*). After a while, these change into verbal hints!
---

## Showcase

[Showcase video](https://va.media.tumblr.com/tumblr_tfv5lbaj6z1b37hp4_720.mp4)

## How to Install / Update

This mod uses a Python injector to place the custom logic directly into your game files. 

### The easy way

I included an executable file you can find in the [latest release](https://github.com/magicnothief/Hide-And-Seek-Helper/releases). Note that this executable is just the python script bundled into one file with PyInstaller. If you have any concerns about being a virus (Windows will flag it), give the Python file to an LLM (eg, ChatGPT) or inspect it yourself.

1. Close Scrap Mechanic if it is running.
2. Run the `sm_hideandseek_injector.exe`
3. When prompted, type or paste your **Scrap Mechanic installation path** (the folder where your game is installed via Steam), which you can find by right-clicking on the game in your library, manage, and browse local files.
4. Type **`1`** and press Enter to select **`[1] INJECT / UPDATE`**.
5. Once it says "SUCCESS", you are ready to play! You can now open Scrap Mechanic and launch **any** workshop challenge map.

### The technical way (you need python installed)

1. Close Scrap Mechanic if it is running.
2. Run the `sm_hideandseek_injector.py` script on your computer.
3. When prompted, type or paste your **Scrap Mechanic installation path** (the folder where your game is installed via Steam).
4. Type **`1`** and press Enter to select **`[1] INJECT / UPDATE`**.
5. Once it says "SUCCESS", you are ready to play! You can now open Scrap Mechanic and launch **any** workshop challenge map.

*Note: To completely remove the mod and go back to a completely normal game, run the script again and choose **`[2] UNINJECT / RESTORE`**.*

---

## How to Play

Once you load into a challenge map, the server will announce that the mod is active. Before starting, players should assign themselves to a team using chat commands.

### 1. Set Your Teams
ONLY the host can open their game chat (usually the `Enter` or `T` key) and type anyone's role:
* If you are hiding: `/role hider [username]`
* If you are seeking: `/role seeker [username]`

You also don't have to write out a full username; the script will try to match it to a person.

### 2. Start the Match
When everyone is ready, it automatically starts with the timer of the map, or the host can type `/startgame` in the chat. 

### 3. The Search & Hints
Once the hiding time ends, the Seekers can start searching. 
* Every 60 seconds, the game will tell Hiders to make a noise or fire a spudgun to give Seekers a clue.
* After 5 minutes, the game enters the "Verbal Phase", where Hiders must give a text or voice hint instead.

### 4. Winning the Game
The game ends automatically when the last hider is caught! The server will announce that all hiders are found and show the Seekers' final time in seconds.

---

## Chat Commands Reference

You can type these directly into the in-game text chat at any time:

| Command | Example | What it does |
| :--- | :--- | :--- |
| `/hhelp` | `/hhelp` | Whispers a list of all these commands to your chat box. |
| `/role [team] [username]` | `/role hider` <br> `/role seeker` | Permanently assigns a player to a specific team (hider or seeker). |
| `/startgame` | `/startgame` | Force-starts a match manually without using map buttons. (It will not sync with the map's timer) |
| `/stopgame` | `/stopgame` | Hard-stops the match and restores everyone's nametags. |
| `/found [name]` | `/found Bob` | Manually tags a Hider as caught (useful if they are glitched in a wall). |
| `/hidingtime [mins]` | `/hidingtime 3` | Changes the hiding countdown to a specific number of **minutes.** |
| `/hintinterval [secs]`| `/hintinterval 45` | Changes the regular hint reminder to fire every X **seconds.** |
| `/verbalhint [mins]` | `/verbalhint 5` | Changes the verbal hint warning to fire after X **minutes**. |
