import discord
from discord.ext import commands
import json
import os
import datetime
import asyncio
import random
import logging
import re
import google.generativeai as genai

# ====== Logging ======
logging.basicConfig(filename="debug.log", level=logging.INFO, format="%(asctime)s %(message)s")
print = lambda *args, **kwargs: (logging.info(" ".join(map(str, args))), __builtins__.print(*args, **kwargs))

# ====== Config Files ======
with open("config.json") as f:
    config = json.load(f)

with open("info.json") as f:
    info = json.load(f)

prefix = config["prefix"]
owner_id = owner_discord_id_put_here #ownerid

# ====== Bot Setup ======
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
genai.configure(api_key="gemini_api_put_here")
model = genai.GenerativeModel("gemini-1.5-flash")


import discord
from discord.ext import commands

xp_file = "xp.json"

# ---------------------------
# LOAD OR CREATE XP FILE
# ---------------------------
if os.path.exists(xp_file):
    with open(xp_file, "r") as f:
        try:
            xp_data = json.load(f)
        except json.JSONDecodeError:
            xp_data = {}
else:
    xp_data = {}
    with open(xp_file, "w") as f:
        json.dump(xp_data, f, indent=4)

def save_xp():
    with open(xp_file, "w") as f:
        json.dump(xp_data, f, indent=4)

# ---------------------------
# XP SYSTEM
# ---------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)

    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "level": 1}

    # Add XP
    xp_data[user_id]["xp"] += 5
    xp = xp_data[user_id]["xp"]
    level = xp_data[user_id]["level"]

    print(f"[DEBUG] {message.author} now has {xp} XP (Level {level})")  # Debug print

    # Check level up
    if xp >= level * 100:
        xp_data[user_id]["level"] += 1
        xp_data[user_id]["xp"] = 0
        await message.channel.send(
            f"🎉 {message.author.mention} leveled up to **Level {xp_data[user_id]['level']}**!"
        )
        print(f"[DEBUG] {message.author} leveled up to {xp_data[user_id]['level']}")  # Debug print

    save_xp()  # Always save XP changes
    print(f"[DEBUG] XP data saved to {xp_file}")  # Debug print

    # VERY IMPORTANT: Allow commands to work
    await bot.process_commands(message)

# ---------------------------
# RANK COMMAND
# ---------------------------
@bot.command()
async def rank(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = str(member.id)
    if user_id not in xp_data:
        await ctx.send(f"{member.mention} has no XP yet.")
        return

    xp = xp_data[user_id]["xp"]
    level = xp_data[user_id]["level"]

    embed = discord.Embed(title=f"🏆 Rank for {member.name}", color=0x00FF00)
    embed.add_field(name="Level", value=str(level), inline=True)
    embed.add_field(name="XP", value=f"{xp}/{level * 100}", inline=True)
    await ctx.send(embed=embed)

# ---------------------------
# LEADERBOARD COMMAND
# ---------------------------
@bot.command()
async def leaderboard(ctx):
    if not xp_data:
        await ctx.send("No XP data available yet.")
        return

    sorted_users = sorted(xp_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
    embed = discord.Embed(title="📊 XP Leaderboard", color=0xFFD700)

    for i, (user_id, data) in enumerate(sorted_users[:10], start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.name if member else "Unknown User"
        embed.add_field(
            name=f"#{i} - {name}",
            value=f"Level {data['level']} | {data['xp']} XP",
            inline=False,
        )

    await ctx.send(embed=embed)


#tictactoe game
TTT_GAMES = {}
WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]

class TTTButton(discord.ui.Button):
    def __init__(self, index: int):
        super().__init__(label=str(index + 1), style=discord.ButtonStyle.secondary, row=index // 3)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: "TTTView" = self.view  # type: ignore

        if interaction.user.id not in (view.p1.id, view.p2.id):
            await interaction.response.send_message("This isn’t your game. 🙅", ephemeral=True)
            return

        if interaction.user.id != view.turn.id:
            await interaction.response.send_message("Not your turn!", ephemeral=True)
            return

        if view.board[self.index] is not None:
            await interaction.response.send_message("That spot is already taken.", ephemeral=True)
            return

        symbol = "❌" if interaction.user.id == view.p1.id else "⭕"
        view.board[self.index] = symbol

        self.label = symbol
        self.disabled = True
        self.style = discord.ButtonStyle.danger if symbol == "❌" else discord.ButtonStyle.success

        winner = view.check_winner()
        is_draw = view.is_draw()

        if winner or is_draw:
            view.disable_all()
            if winner:
                result_msg = f"Game over! {interaction.user.mention} wins! 🏆"
            else:
                result_msg = "It’s a draw! 🤝"

            # Add rematch button
            rematch_view = RematchView(view.ctx, view.p1, view.p2)
            TTT_GAMES.pop(view.channel_id, None)

            await interaction.response.edit_message(content=result_msg, view=rematch_view)
            return

        view.turn = view.p2 if view.turn.id == view.p1.id else view.p1
        await interaction.response.edit_message(
            content=f"TicTacToe — {view.p1.mention} (❌) vs {view.p2.mention} (⭕)\n"
                    f"**Turn:** {view.turn.mention}",
            view=view
        )

class TTTView(discord.ui.View):
    def __init__(self, ctx: commands.Context, p1: discord.Member, p2: discord.Member, *, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.p1 = p1
        self.p2 = p2
        self.turn: discord.Member = p1
        self.board: list[str | None] = [None] * 9
        self.channel_id = ctx.channel.id

        for i in range(9):
            self.add_item(TTTButton(i))

    def disable_all(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    def check_winner(self) -> bool:
        for a, b, c in WIN_LINES:
            if self.board[a] is not None and self.board[a] == self.board[b] == self.board[c]:
                return True
        return False

    def is_draw(self) -> bool:
        return all(cell is not None for cell in self.board)

    async def on_timeout(self):
        self.disable_all()
        try:
            await self.ctx.send("Game timed out ⏳")
        except Exception:
            pass
        TTT_GAMES.pop(self.channel_id, None)


# ===== Rematch Button =====
class RematchView(discord.ui.View):
    def __init__(self, ctx: commands.Context, p1: discord.Member, p2: discord.Member):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.p1 = p1
        self.p2 = p2

    @discord.ui.button(label="🔄 Rematch", style=discord.ButtonStyle.primary)
    async def rematch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message("Only the previous players can rematch!", ephemeral=True)
            return

        if self.ctx.channel.id in TTT_GAMES:
            await interaction.response.send_message("A game is already running in this channel!", ephemeral=True)
            return

        new_view = TTTView(self.ctx, self.p1, self.p2)
        TTT_GAMES[self.ctx.channel.id] = new_view
        await interaction.response.edit_message(
            content=f"TicTacToe — {self.p1.mention} (❌) vs {self.p2.mention} (⭕)\n"
                    f"**Turn:** {self.p1.mention}\nNew game started!",
            view=new_view
        )


@bot.command(name="tictactoe", aliases=["ttt"])
async def tictactoe(ctx, opponent: discord.Member):
    if opponent.bot:
        await ctx.send("You can’t play with a bot (yet) 😉")
        return
    if opponent.id == ctx.author.id:
        await ctx.send("You can’t play against yourself! 😅")
        return
    if ctx.channel.id in TTT_GAMES:
        await ctx.send("A TicTacToe game is already running in this channel. Finish it or use `>endgame`.")
        return

    view = TTTView(ctx, ctx.author, opponent)
    TTT_GAMES[ctx.channel.id] = view
    await ctx.send(
        f"TicTacToe — {ctx.author.mention} (❌) vs {opponent.mention} (⭕)\n"
        f"**Turn:** {ctx.author.mention}",
        view=view
    )

@bot.command(name="endgame")
async def endgame(ctx):
    view: TTTView | None = TTT_GAMES.get(ctx.channel.id)
    if not view:
        await ctx.send("No TicTacToe game is running in this channel.")
        return

    if ctx.author.id not in (view.p1.id, view.p2.id) and not ctx.author.guild_permissions.manage_messages:
        await ctx.send("Only the players or a moderator can end this game.")
        return

    view.disable_all()
    await ctx.send("Game ended manually. 🛑", view=view)
    TTT_GAMES.pop(ctx.channel.id, None)




# ====== Events ======
@bot.event
async def on_ready():
    print(f"The time is {datetime.datetime.now()}")
    print("Ragnarok has started by nicemondominic!")
    await bot.change_presence(activity=discord.Game(f"{len(bot.guilds)} servers | {prefix}help"))

# ====== Commands ======

# List of banned words (lowercase)
banned_words = ["myr", "myru", "myrr"]

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    # Check for banned words
    if any(word in message.content.lower() for word in banned_words):
        try:
            await message.delete()
            await message.channel.send(
                f"⚠️ {message.author.mention}, your message contained a banned word and was removed.",
            )
        except discord.Forbidden:
            print("I don't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message.")

    # Make sure other commands still work
    await bot.process_commands(message)

@bot.command()
async def ask(ctx, *, prompt: str):
    """Ask Gemini AI something."""
    async with ctx.typing():  # ✅ correct way in discord.py v2
        try:
            response = model.generate_content(prompt)
            await ctx.reply(response.text)
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

@bot.command()
async def about(ctx):
    """Tells what the bot is about."""
    embed = discord.Embed(
        title="🤖 About Ragnarok",
        description=(
            "Ragnarok is a **Gemini-powered AI bot** built for Discord servers. "
            "It combines advanced AI chat capabilities with **powerful server management tools**, "
            "offering moderation commands, automation features, and interactive AI responses — "
            "all in one bot."
        ),
        color=0x5865F2
    )
    embed.add_field(
        name="🌟 Features",
        value=(
            "- **AI Chat**: Ask anything and get instant AI-powered responses.\n"
            "- **Moderation Tools**: Ban, unban, mute, slowmode, and more.\n"
            "- **Automation**: Welcome messages, message censoring, role info, etc.\n"
            "- **Server Insights**: View detailed server statistics."
        ),
        inline=False
    )
    embed.set_footer(text="Powered by Google @nicemondominic • Made for your server's needs.")
    
    await ctx.send(embed=embed)


@bot.command()
async def imageping(ctx):
    sent = await ctx.send("Pinging...")
    latency = (sent.created_at - ctx.message.created_at).total_seconds() * 1000
    await sent.edit(content="http://madeformakers.org/wp-content/uploads/2016/01/pong.png")
    await asyncio.sleep(0.5)
    await sent.edit(content=f"Pong! Took {int(latency)}ms")
    await ctx.message.delete()

@bot.command()
async def botspeak(ctx, *, text: str):
    if ctx.author.id == owner_id:
        await ctx.send(text)
        await ctx.message.delete()

@bot.command()
async def math(ctx, *, expression: str):
    await ctx.message.delete()
    try:
        result = eval(expression)  # ⚠ Be careful if making public
        await ctx.send(f"Your answer is {result}")
    except Exception:
        await ctx.send("Invalid math expression.")

@bot.command()        
async def dmuser(ctx, user: discord.User, *, message: str):
    """Send a DM to the mentioned user."""
    try:
        await user.send(message)
        await ctx.send(f"📩 Message sent to {user.mention}")
    except discord.Forbidden:
        await ctx.send(f"❌ Cannot DM {user.mention} — they may have DMs disabled.")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

@bot.command()
async def avatar(ctx, user: discord.User = None):
    """Show the avatar of the mentioned user (or yourself if none mentioned)."""
    if user is None:
        user = ctx.author

    embed = discord.Embed(
        title=f"Avatar of {user.name}",
        color=discord.Color.teal()
    )
    embed.set_image(url=user.display_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    """Lock the current channel so only admins/mods can send messages."""
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(f"🔒 {ctx.channel.mention} has been locked. Only admins/mods can send messages.")
    await ctx.message.delete()

@lock.error
async def lock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don’t have permission to lock channels.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    """Unlock the current channel for everyone."""
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(f"🔓 {ctx.channel.mention} has been unlocked for everyone.")
    await ctx.message.delete()

@unlock.error
async def unlock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don’t have permission to unlock channels.")



@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    """Ban a member from the server."""
    try:
        await member.ban(reason=reason)
        await ctx.send(f"✅ {member.mention} has been banned. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I do not have permission to ban this member.")
    except Exception as e:
        await ctx.send(f"⚠️ An error occurred: {e}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to ban members.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member: str):
    """Unban a user by mention, ID, or username#discriminator."""
    # If member is a mention like <@1234567890>, extract the ID
    if member.startswith("<@") and member.endswith(">"):
        member = member.replace("<@", "").replace(">", "").replace("!", "")

    banned_users = [ban async for ban in ctx.guild.bans()]

    # Try matching by ID
    if member.isdigit():
        member_id = int(member)
        for ban_entry in banned_users:
            if ban_entry.user.id == member_id:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"✅ Unbanned {ban_entry.user} (ID: {member_id})")
                return

    # Try matching by username#discriminator
    if "#" in member:
        name, discriminator = member.split("#", 1)
        for ban_entry in banned_users:
            user = ban_entry.user
            if user.name == name and user.discriminator == discriminator:
                await ctx.guild.unban(user)
                await ctx.send(f"✅ Unbanned {user}")
                return

    await ctx.send(f"❌ User `{member}` not found in ban list.")


@bot.command()
async def purge(ctx, amount: int):
    allowed_roles = ['Owner', 'Co-Owner', 'Co Owner', 'Admin', 'Administrator',
                     'Moderator', 'Moderators', 'Mods', 'Admins']
    if any(r.name in allowed_roles for r in ctx.author.roles):
        if amount < 1:
            embed = discord.Embed(color=0x00FF00, description='You must provide a number between 1 and 100.')
            await ctx.send(embed=embed)
            return
        if amount > 100:
            embed = discord.Embed(color=0x00FF00, description='Cannot purge more than 100 messages.')
            await ctx.send(embed=embed)
            return
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount)
        print(f"Purged {len(deleted)} messages in {ctx.guild.name}")
        
    else:
        embed = discord.Embed(color=0x00FF00, description='You must have Owner, Admin, or Co-Owner role.')
        await ctx.send(embed=embed)

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")  # Change to your channel name
    if channel:
        embed = discord.Embed(
            title="🎉 Welcome!",
            description=f"Hey {member.mention}, welcome to **{member.guild.name}**! 🎊",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await channel.send(embed=embed)

    try:
        dm_embed = discord.Embed(
            title="👋 Welcome to the Server!",
            description=f"Hello {member.name}, we're glad to have you at **{member.guild.name}**! 🎉\n\nEnjoy your stay! 💖",
            color=discord.Color.blue()
        )
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        print(f"Could not DM {member.name}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason="No reason provided"):
    """Suspend a user by adding a Muted role."""
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

    # Create muted role if it doesn't exist
    if muted_role is None:
        muted_role = await ctx.guild.create_role(name="Muted", reason="For suspending users")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, send_messages=False, speak=False)
    
    # Apply role
    await member.add_roles(muted_role, reason=reason)
    await ctx.send(f"🚫 {member.mention} has been muted. Reason: {reason}")
    await ctx.message.delete()
    

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    """Remove suspension from a user."""
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"✅ {member.mention} has been unmuted.")
        await ctx.message.delete()
    else:
        await ctx.send(f"❌ {member.mention} is not suspended.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    """Set slowmode for the current text channel."""
    if seconds < 0 or seconds > 21600:
        await ctx.send("❌ Please provide a value between **0** and **21600** seconds.")
        return
    
    try:
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send(f"✅ Slowmode disabled in {ctx.channel.mention}.")
            await ctx.message.delete()
        else:
            await ctx.send(f"✅ Slowmode set to **{seconds} seconds** in {ctx.channel.mention}.")
            await ctx.message.delete()
    except discord.Forbidden:
        await ctx.send("❌ I don’t have permission to manage channels here.")
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to set slowmode: {e}")


@bot.command()
async def invite(ctx):
    await ctx.send(f"Here is the invite to my server requested by, {ctx.author.mention}.")
    embed = discord.Embed(color=0x008080, title='Invite to Ragnarok Server',
                          description='Ragnarok is the server owned by nicemondominic. Join for chilling!')
    embed.url = 'https://discord.gg/3xUjP7kd'
    await ctx.send(embed=embed)

@bot.command()
async def kick(ctx, member: discord.Member):
    if ctx.author.guild_permissions.kick_members:
        try:
            await member.kick()
            await ctx.send(f"Successfully kicked {member.mention}")
        except Exception:
            await ctx.send("I was unable to kick the member.")

@bot.command()
async def roles(ctx, member: discord.Member = None):
    member = member or ctx.author  # If no member is mentioned, show roles for the command user
    roles = [role.mention for role in member.roles if role != ctx.guild.default_role]

    if not roles:
        roles_display = "No roles assigned."
    else:
        roles_display = ", ".join(roles)

    embed = discord.Embed(
        title=f"Roles for {member.display_name}",
        description=roles_display,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def setstatus(ctx, *, status: str):
    if ctx.author.id == owner_id:
        await bot.change_presence(activity=discord.Game(status))
        await ctx.send(f"Set status to **{status}**")
        await ctx.message.delete()


@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild

    # Member stats
    online = len([m for m in guild.members if m.status == discord.Status.online])
    idle = len([m for m in guild.members if m.status == discord.Status.idle])
    dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
    offline = guild.member_count - (online + idle + dnd)
    humans = len([m for m in guild.members if not m.bot])
    bots = len([m for m in guild.members if m.bot])

    # Channel stats
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    private_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel) and len(c.overwrites) > 0])

    # Emojis and stickers
    emojis = len(guild.emojis)
    animated_emojis = len([e for e in guild.emojis if e.animated])
    stickers = len(guild.stickers)

    # Roles
    roles = len(guild.roles)

    # Boost info
    boost_level = guild.premium_tier
    boost_count = guild.premium_subscription_count

    # Top role holder (besides owner)
    highest_role = sorted([r for r in guild.roles if r != guild.default_role], key=lambda r: r.position, reverse=True)[0]

    # Embed design
    embed = discord.Embed(
        title=f"🛰 SERVER ANALYTICS — {guild.name}",
        description=f"Cybernetic scan complete. Displaying operational metrics for **{guild.name}**",
        color=0x00ffcc
        
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    # General Info
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="🆔 Server ID", value=str(guild.id), inline=True)
    embed.add_field(name="🌐 Region", value="India", inline=True)

    # Member Stats
    embed.add_field(name="👥 Members", value=f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}", inline=True)
    embed.add_field(name="📶 Status", value=f"🟢 Online: {online}\n🌙 Idle: {idle}\n⛔ DND: {dnd}\n⚫ Offline: {offline}", inline=True)

    # Boost Info
    embed.add_field(name="🚀 Boost Level", value=f"Level {boost_level} ({boost_count} boosts)", inline=True)

    # Channels
    embed.add_field(name="📂 Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}\n Private: {private_channels}", inline=True)

    # Emojis & Stickers
    embed.add_field(name="😄 Emojis", value=f"{emojis} total ({animated_emojis} animated)", inline=True)
    embed.add_field(name="🏷 Stickers", value=str(stickers), inline=True)

    # Roles
    embed.add_field(name="🎭 Roles", value=str(roles), inline=True)
    embed.add_field(name="💎 Highest Role", value=highest_role.mention, inline=True)

    # Description if exists
    if guild.description:
        embed.add_field(name="📜 Description", value=guild.description, inline=False)

    embed.set_footer(text="Data provided by Ragnarok AI — Cybernetic Systems Online")

    await ctx.send(embed=embed)


@bot.command(aliases=["rolldice"])
async def roll(ctx):
    roll_value = random.randint(1, 6)
    await ctx.send(f":game_die: **|** {roll_value}")

@bot.command()
async def coinflip(ctx):
    result = random.choice(["Heads!", "Tails!"])
    await ctx.send(f"We have, {result}")

@bot.command()
async def commandlist(ctx):
    embed = discord.Embed(
        title="🛠️ Ragnarok Command List",
        description="Here are all the available commands in **Ragnarok** – your Gemini-powered AI Discord bot 🚀",
        color=discord.Color.purple()
    )

    # Moderation Commands
    embed.add_field(
        name="⚔️ Moderation",
        value=(
            "`>ban <user> [reason]` – Ban a user\n"
            "`>unban <user_id>` – Unban a user\n"
             "`>mute <user> [reason]` – Mute user from sending messages\n"
             "`>unmute <user> [reason]` – unmute user \n"
            "`>unban <user_id>` – Unban a user\n"
            "`>suspend <user> [reason]` – Temporarily suspend a user\n"
            "`>slowmode <seconds>` – Set slowmode in the channel\n"
            "`>lock` – Only admin can send messages\n"
            "`>unlock` – set everyone can send messages\n"
            "`>purge <number> ` – Delete Messages\n"
            "`>kick <user> [reason]` – Kick user from Server\n"
             "`>dmuser <user>` – Send message to the mentioned user in DM\n"

            
        ),
        inline=False
    )

    # Server Info / Utility Commands
    embed.add_field(
        name="📊 Server & Utility",
        value=(
            "`>serverinfo` – Get detailed futuristic server info\n"
            "`>roles @user` – Display roles of a user\n"
            "`>commandlist` – Show this command list\n"
            "`>about` – Description about Ragnarok\n"
            "`>invite` – Invitation link of server\n"
            "`>setstatus [text]` – set status for bot\n"
            "`>avatar <user> ` – Show avatar of the mentioned user\n"
            
            
            
        ),
        inline=False
    )

    # AI & Fun Commands
    embed.add_field(
        name="🤖 AI ",
        value=(
            "`>ask <question>` – Ask Ragnarok (Gemini AI)\n"
           
        ),
        inline=False
    )
    embed.add_field(
        name="Owner",
        value=(
            "`>botspeak` – Bot messages\n"
           
        ),
        inline=False
    )

    embed.add_field(
        name="Fun",
        value=(
            "`>imageping` – Ping\n"
            "`>math` – Calculation\n"
            "`>roll` – roll a dice\n"
            "`>coinflip` – flip a coin\n"

          
            
        ),
        inline=False
    )

    embed.add_field(
    name="🎮 TicTacToe",
    value=(
        "`>tictactoe @user` — Start a game of TicTacToe with another user\n"
        "`>endgame` — Force end the current game in the channel\n"
        "Rematch 🔄 — Appears after a game ends, lets the same players restart instantly"
    ),
    inline=False
)

    # Misc / Auto
    embed.add_field(
        name="✨ Auto Features",
        value=(
            "👋 Welcome message when a user joins\n"
            "🔒 Censor Banned words\n"
            "📈 XP gain system when users chat\n"
             "`>rank` → Check your XP & Level\n"
            "`>leaderboard` → See the top players\n"
            
        ),
        inline=False
    )
 
    

    embed.set_footer(text="Ragnarok • Powered by nicemondominic")
    await ctx.send(embed=embed)




# ====== Run Bot ======
bot.run(config["token"])
