Ragnarok – Discord Server Managing Bot 🤖⚔️

Ragnarok is a Python-powered Discord bot built by @nicemondominic
.
It combines AI (Google Gemini), server moderation, fun commands, and XP-based leveling to create a powerful all-in-one server management assistant.

📌 Features

🌟 AI-Powered Chat (Gemini integration – >ask <question>)

🛡 Moderation Tools (ban, unban, mute, purge, slowmode, lock/unlock, kick)

📈 XP & Level System (gain XP by chatting, check >rank & >leaderboard)

🎮 Fun & Games (TicTacToe, dice roll, coin flip, math solver, image ping)

📊 Server Insights (detailed analytics with >serverinfo, role lookup, avatar)

👋 Auto Welcome Messages (in #welcome channel + DM greeting)

🚫 Word Filter (delete banned words automatically)

⚡ Utility Commands (roles, set bot status, DM users, invite link)

🧩 Extensible & Modular – easy to add new commands

🛠 Installation
Requirements

Python 3.9+

discord.py (or py-cord)

google-generativeai

Other built-ins: asyncio, json, random, logging

Setup

Clone the repo:

git clone https://github.com/your-username/ragnarok-bot.git
cd ragnarok-bot


Install dependencies:

pip install -r requirements.txt


Configure your bot:

Add your bot token and command prefix in config.json

Add your Gemini API key in main.py (genai.configure(api_key="..."))

Set your owner ID in main.py

Run the bot:

python main.py

⚔️ Commands Overview
Moderation

>ban <user> [reason] – Ban a member

>unban <user_id> – Unban a member

>mute <user> [reason] / >unmute <user> – Manage user mute role

>slowmode <seconds> – Enable slowmode

>lock / >unlock – Lock or unlock a channel

>purge <number> – Delete messages (up to 100)

>kick <user> – Kick a member

>dmuser <user> <message> – Send a DM to a user

Server & Utility

>serverinfo – Detailed futuristic server analytics

>roles [@user] – Show user’s roles

>avatar [@user] – Show profile picture

>setstatus <text> – Change bot’s status (Owner only)

>invite – Get the server invite link

>about – Info about Ragnarok

AI

>ask <question> – Ask Gemini AI

Fun

>tictactoe @user – Start a TicTacToe match

>endgame – End current TicTacToe game

>roll – Roll a dice

>coinflip – Flip a coin

>math <expression> – Solve math

>imageping – Funny ping-pong response

XP & Levels

>rank [@user] – Show XP & level

>leaderboard – Top XP earners

📂 Project Info

Name: Ragnarok

Version: 3.1

Language: English

Author: @nicemondominic

📜 License

This project is open-source. Feel free to modify & improve it for your server’s needs.
