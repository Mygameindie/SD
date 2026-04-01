import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import io

# --- CONFIGURATION ---
ALLOWED_GUILDS = [1459863187393482833, 1477721787952267347]
STAFF_ROLES = ["Tester (Computer)","Tester (Mobile)","Tester (Console)", "War Manager", "Co Clan Leader", "Absolute Solver"]
HIGH_STAFF_ROLES = ["Co Clan Leader", "Absolute Solver"]

# Channel IDs
ANNOUNCE_CHANNEL_ID = 1469909170827431946
FFLAGS_CHANNEL_ID = 1479112752231485521
BOOST_CHANNEL_ID = 1471061838228885534
WELCOME_CHANNEL_ID = 1459888304236400660
LEAVE_CHANNEL_ID = 1459892472585912362

# Role & Assets
CREW_ROLE_ID = 1459865077904834642
CLAN_NAME = "𝚂𝚠𝚎𝚎𝚝 𝙳𝚎า𝚍𝚕𝚢 -𝚂𝙳"
BOOST_EMOJI = "<:Discord_Server_Boots:1470836031770071264>"
GIF_DIVIDER = "https://cdn.discordapp.com/attachments/1327188364885102594/1443075988580995203/fixedbulletlines.gif"
WELCOME_IMAGE_URL = "https://media.discordapp.net/attachments/1164236504248373261/1459897587263082619/FB_IMG_1767695135543.jpg"
LEAVE_IMAGE_URL = "https://media.discordapp.net/attachments/1164236504248373261/1459898135051501568/b37c22c1ac1b62fd268df84a2083824f_4269240152242148133.jpg"

ILLEGAL_KEYWORDS = ["hitbox", "expander", "wallhack", "noclip", "walkspeed", "jumppower", "xray", "fly", "reach", "physics", "hitbody", "gravity", "RenderRate", "SenderRate", "hipheight"]

RANKS = ["Rank 3", "Rank 2", "Rank 1", "Rank 0"]
TIERS = ["High", "Mid", "Low"]
STAGES = ["Strong", "Stable", "Weak"]

ROLES_MAP = {
    "Rank 3": 1459871112572702874, "Rank 2": 1459871429100310655, "Rank 1": 1459871619005677609, "Rank 0": 1460252877741232128,
    "High": 1459872253146693692, "Mid": 1459872249271287808, "Low": 1459872242237177990,
    "Strong": 1460096227784917256, "Stable": 1460096346886242530, "Weak": 1460095836120944793
}

# Visual config for rank-based embed colors and slot medals
RANK_COLORS = {
    "Rank 3": 0xFFD700,  # Gold
    "Rank 2": 0xC0C0C0,  # Silver
    "Rank 1": 0xCD7F32,  # Bronze
    "Rank 0": 0x2B2D31,  # Default dark
}
SLOT_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def get_member_stats(member: discord.Member):
    """Extract rank/tier/stage from a member's roles."""
    r, t, s = "None", "None", "None"
    for role in member.roles:
        if role.name in RANKS: r = role.name
        elif role.name in TIERS: t = role.name
        elif role.name in STAGES: s = role.name
    return r, t, s


# --- UI COMPONENTS ---

class RankSelectView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=120)
        self.member = member
        self.rank = None
        self.tier = None
        self.stage = None

    def _status_text(self):
        rank = f"`{self.rank}`" if self.rank else "❓ Not selected"
        tier = f"`{self.tier}`" if self.tier else "❓ Not selected"
        stage = f"`{self.stage}`" if self.stage else "❓ Not selected"
        return (
            f"**Managing roles for {self.member.display_name}**\n"
            f"Rank: {rank}  |  Tier: {tier}  |  Stage: {stage}\n\n"
            f"Select all three, then click **Update Roles**."
        )

    @discord.ui.select(placeholder="Step 1: Select Rank", options=[discord.SelectOption(label=k) for k in RANKS])
    async def select_rank(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.rank = select.values[0]
        await interaction.response.edit_message(content=self._status_text(), view=self)

    @discord.ui.select(placeholder="Step 2: Select Tier", options=[discord.SelectOption(label=k) for k in TIERS])
    async def select_tier(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.tier = select.values[0]
        await interaction.response.edit_message(content=self._status_text(), view=self)

    @discord.ui.select(placeholder="Step 3: Select Stage", options=[discord.SelectOption(label=k) for k in STAGES])
    async def select_stage(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.stage = select.values[0]
        await interaction.response.edit_message(content=self._status_text(), view=self)

    @discord.ui.button(label="Update Roles", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not all([self.rank, self.tier, self.stage]):
            return await interaction.response.send_message("❌ Please select all three categories first!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        category_ids = set(ROLES_MAP.values())
        to_remove = [role for role in self.member.roles if role.id in category_ids or role.name.lower() == "testlist"]

        to_add = []
        crew_role = interaction.guild.get_role(CREW_ROLE_ID)
        if crew_role: to_add.append(crew_role)

        for selection in [self.rank, self.tier, self.stage]:
            rid = ROLES_MAP.get(selection)
            if rid:
                r_obj = interaction.guild.get_role(rid)
                if r_obj: to_add.append(r_obj)

        try:
            if to_remove: await self.member.remove_roles(*to_remove)
            await self.member.add_roles(*to_add)

            # Auto-sync leaderboard if this player is in the top 10
            for entry in bot.leaderboard_data:
                if entry.get("discord_id") == self.member.id:
                    entry["stats"] = f"{self.rank} | {self.tier} | {self.stage}"
                    entry["display_name"] = self.member.display_name
                    bot.save_data()
                    break

            await interaction.followup.send(
                content=f"✅ **Roles Updated!**\n{self.member.mention} → `{self.rank} | {self.tier} | {self.stage}`",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ **Error:** {e}", ephemeral=True)


# --- BOT CORE ---

class SDBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.data_file = "leaderboard_data.json"
        self.leaderboard_data = []
        self.leaderboard_msg = None
        self.leaderboard_msg_id = None
        self.leaderboard_channel_id = None

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    saved = json.load(f)
                # Support old format (plain list) and new format (dict with players key)
                if isinstance(saved, list):
                    self.leaderboard_data = saved
                else:
                    self.leaderboard_data = saved.get("players", [])
                    self.leaderboard_msg_id = saved.get("msg_id")
                    self.leaderboard_channel_id = saved.get("channel_id")
                return
            except:
                pass
        self.leaderboard_data = [
            {"rank": i + 1, "discord_id": None, "roblox_id": None, "display_name": "VACANT", "stats": "None"}
            for i in range(10)
        ]

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump({
                "players": self.leaderboard_data,
                "msg_id": self.leaderboard_msg_id,
                "channel_id": self.leaderboard_channel_id
            }, f, indent=4)

    async def setup_hook(self):
        self.load_data()
        self.update_leaderboard_task.start()
        await self.tree.sync()

    @tasks.loop(seconds=30)
    async def update_leaderboard_task(self):
        # Restore leaderboard message reference after restart
        if not self.leaderboard_msg and self.leaderboard_msg_id and self.leaderboard_channel_id:
            chan = self.get_channel(self.leaderboard_channel_id)
            if chan:
                try:
                    self.leaderboard_msg = await chan.fetch_message(self.leaderboard_msg_id)
                except:
                    self.leaderboard_msg_id = None
                    self.leaderboard_channel_id = None

        if self.leaderboard_msg:
            try:
                embeds = await self.create_leaderboard_embeds()
                await self.leaderboard_msg.edit(embeds=embeds)
            except:
                pass

    async def create_leaderboard_embeds(self):
        embeds = []
        for p in self.leaderboard_data:
            slot = p["rank"]
            medal = SLOT_MEDALS.get(slot, f"#{slot}")
            rank_name = p["stats"].split(" | ")[0] if p.get("stats") and p["stats"] != "None" else None
            color = RANK_COLORS.get(rank_name, 0x2B2D31)
            embed = discord.Embed(color=color)
            if p.get("discord_id"):
                profile_url = f"https://www.roblox.com/users/{p['roblox_id']}/profile"
                embed.description = (
                    f"### {medal} TOP #{slot}\n"
                    f"**Player:** {p['display_name']}\n"
                    f"**Stats:** `{p['stats']}`\n"
                    f"🔗 [Roblox Profile]({profile_url})"
                )
            else:
                embed.description = (
                    f"### {medal} TOP #{slot}\n"
                    f"**VACANT**\n"
                    f"*Waiting for a challenger...*"
                )
            embed.set_image(url=GIF_DIVIDER)
            embeds.append(embed)
        return embeds


bot = SDBot()


# --- EVENTS ---

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and monitoring {CLAN_NAME}.")
    await bot.change_presence(activity=discord.Game(name=CLAN_NAME))
    for guild in bot.guilds:
        try:
            if guild.id not in ALLOWED_GUILDS: await guild.leave()
        except:
            pass

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="⚔️ Welcome The New Member", description=f"{member.mention} Has joined **{CLAN_NAME}**!", color=0x2ecc71)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=WELCOME_IMAGE_URL)
        await channel.send(content=f"Welcome {member.mention}! 🌿", embed=embed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LEAVE_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="💀 Someone Has left the clan!", description=f"{member.mention} has left **{CLAN_NAME}**", color=0xe74c3c)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=LEAVE_IMAGE_URL)
        await channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        channel = bot.get_channel(BOOST_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title=f"{BOOST_EMOJI} SERVER BOOSTED!", description=f"A huge thank you to {after.mention}!\nYou have just boosted **{CLAN_NAME}**.", color=0xff73fa)
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(content=f"Attention @everyone, we have a new booster!", embed=embed)


# --- COMMANDS ---

@bot.command(name="scan")
async def scan(ctx):
    if not (isinstance(ctx.channel, discord.DMChannel) or ctx.channel.id == FFLAGS_CHANNEL_ID): return
    content = ""
    if ctx.message.attachments:
        att = ctx.message.attachments[0]
        if att.filename.endswith(('.json', '.txt')): content = (await att.read()).decode('utf-8')
    else:
        content = ctx.message.content[len("!scan"):].strip().strip('`').replace('json', '', 1)

    if not content: return await ctx.send("❌ Error: Provide text or file.")
    try:
        data = json.loads(content)
        cleaned, removed = {}, []
        for k, v in data.items():
            if any(kw in k.lower() for kw in ILLEGAL_KEYWORDS): removed.append(k)
            else: cleaned[k] = v
        if not removed: await ctx.send("✅ All flags legal.")
        else:
            out = io.StringIO(json.dumps(cleaned, indent=4))
            await ctx.send(f"⚠️ Found {len(removed)} illegal flags.", file=discord.File(out, "fixed_flags.json"))
    except: await ctx.send("❌ Invalid format.")


@bot.tree.command(name="addrank", description="Assign Rank/Tier/Stage roles to a member")
@app_commands.checks.has_any_role(*STAFF_ROLES)
async def addrank(interaction: discord.Interaction, member: discord.Member):
    view = RankSelectView(member)
    await interaction.response.send_message(view._status_text(), view=view, ephemeral=True)


@bot.tree.command(name="removerank", description="Remove all rank/tier/stage roles from a member")
@app_commands.checks.has_any_role(*STAFF_ROLES)
async def removerank(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    category_ids = set(ROLES_MAP.values())
    to_remove = [role for role in member.roles if role.id in category_ids or role.name.lower() == "testlist"]
    if not to_remove:
        return await interaction.followup.send(f"❌ {member.display_name} has no rank roles to remove.", ephemeral=True)
    try:
        await member.remove_roles(*to_remove)
        await interaction.followup.send(f"✅ Removed all rank roles from {member.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


@bot.tree.command(name="rank", description="View a player's current rank and stats")
async def rank_cmd(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    r, t, s = get_member_stats(target)
    color = RANK_COLORS.get(r, 0x2B2D31)

    # Check if the player is in the top 10
    top_slot = next((e["rank"] for e in bot.leaderboard_data if e.get("discord_id") == target.id), None)

    embed = discord.Embed(title=f"⚔️ Player Stats — {target.display_name}", color=color)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Rank", value=f"`{r}`", inline=True)
    embed.add_field(name="Tier", value=f"`{t}`", inline=True)
    embed.add_field(name="Stage", value=f"`{s}`", inline=True)
    if top_slot:
        medal = SLOT_MEDALS.get(top_slot, f"#{top_slot}")
        embed.add_field(name="Leaderboard", value=f"{medal} Top #{top_slot}", inline=False)
    embed.set_image(url=GIF_DIVIDER)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="top", description="View the current top 10 leaderboard")
async def top_cmd(interaction: discord.Interaction):
    embeds = await bot.create_leaderboard_embeds()
    await interaction.response.send_message(embeds=embeds, ephemeral=True)


@bot.tree.command(name="edit_top", description="Manually edit a leaderboard slot")
@app_commands.checks.has_any_role(*HIGH_STAFF_ROLES)
async def edit_top(interaction: discord.Interaction, slot: int, member: discord.Member, roblox_id: str):
    if not (1 <= slot <= 10):
        return await interaction.response.send_message("❌ Slot must be between 1 and 10.", ephemeral=True)
    r, t, s = get_member_stats(member)
    bot.leaderboard_data[slot - 1] = {
        "rank": slot,
        "discord_id": member.id,
        "display_name": member.display_name,
        "roblox_id": roblox_id.strip(),
        "stats": f"{r} | {t} | {s}"
    }
    bot.save_data()
    await interaction.response.send_message(
        f"✅ Slot #{slot} → **{member.display_name}** (`{r} | {t} | {s}`)", ephemeral=True
    )


@bot.tree.command(name="clear_top", description="Clear a leaderboard slot")
@app_commands.checks.has_any_role(*HIGH_STAFF_ROLES)
async def clear_top(interaction: discord.Interaction, slot: int):
    if not (1 <= slot <= 10):
        return await interaction.response.send_message("❌ Slot must be between 1 and 10.", ephemeral=True)
    bot.leaderboard_data[slot - 1] = {"rank": slot, "discord_id": None, "roblox_id": None, "display_name": "VACANT", "stats": "None"}
    bot.save_data()
    await interaction.response.send_message(f"✅ Slot #{slot} cleared.", ephemeral=True)


@bot.tree.command(name="top_post", description="Post the leaderboard to the announcement channel")
@app_commands.checks.has_any_role(*HIGH_STAFF_ROLES)
async def top_post(interaction: discord.Interaction):
    chan = bot.get_channel(ANNOUNCE_CHANNEL_ID)
    if not chan:
        return await interaction.response.send_message("❌ Announcement channel not found.", ephemeral=True)
    embeds = await bot.create_leaderboard_embeds()
    bot.leaderboard_msg = await chan.send(embeds=embeds)
    bot.leaderboard_msg_id = bot.leaderboard_msg.id
    bot.leaderboard_channel_id = chan.id
    bot.save_data()
    await interaction.response.send_message("✅ Leaderboard posted and will auto-update every 30s.", ephemeral=True)


try:
    bot.run('')
except Exception as e:
    print(f"FAILED TO START: {e}")
