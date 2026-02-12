import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

# ===== CONFIGURATION =====
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
WELCOME_CHANNEL_NAME = "welcome"  # Channel name for welcome messages

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ===== AUTO-REPLY KEYWORDS =====
AUTO_REPLIES = {
    "hello tempest": "Hello there! 👋 How can I help?",
    "thank you tempest": "You're welcome! 😊",
    "good bot": "Aww, thanks! ❤️",
    "bad bot": "I'll try harder next time... 😢"
}

# ===== EVENTS =====
@bot.event
async def on_ready():
    print(f"✅ Tempest is online as {bot.user}")
    await bot.tree.sync()  # Sync slash commands globally

@bot.event
async def on_member_join(member):
    """Send welcome message to new members"""
    welcome_channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)
    
    embed = discord.Embed(
        title="🎉 Welcome to the server!",
        description=f"Hello {member.mention}, welcome to **{member.guild.name}**!",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="💡 Tip", value="Use `/help` to see what I can do!")
    
    if welcome_channel:
        await welcome_channel.send(embed=embed)
    else:
        # Fallback: send via DM
        try:
            await member.send(f"Welcome to **{member.guild.name}**! 😊")
        except discord.Forbidden:
            pass  # DMs disabled

@bot.event
async def on_message(message):
    """Handle auto-replies"""
    if message.author.bot:
        return
    
    # Check for keyword triggers (case-insensitive)
    content_lower = message.content.lower()
    for trigger, reply in AUTO_REPLIES.items():
        if trigger in content_lower:
            await message.reply(reply)
            break
    
    await bot.process_commands(message)

# ===== SLASH COMMANDS =====
@bot.tree.command(name="start", description="Start interacting with Tempest")
async def start(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ Tempest Bot",
        description="Hello! I'm Tempest, your friendly server assistant.\nUse `/help` to see available commands.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Tempest Commands",
        color=discord.Color.blurple()
    )
    embed.add_field(
        name="💬 General",
        value="`/start` - Start using the bot\n`/help` - Show this menu",
        inline=False
    )
    embed.add_field(
        name="📣 Broadcast (Admin)",
        value="`/broadcast [message]` - Send announcement to all channels",
        inline=False
    )
    embed.add_field(
        name="🛡️ Moderation (Admin)",
        value="`/kick [@user] [reason]`\n`/ban [@user] [reason]`\n`/warn [@user] [reason]`",
        inline=False
    )
    embed.set_footer(text="Tempest Bot • Made with ❤️")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="broadcast", description="Broadcast a message to all text channels (Admin only)")
@app_commands.describe(message="Message to broadcast")
async def broadcast(interaction: discord.Interaction, message: str):
    if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need admin permissions to use this command.", ephemeral=True)
        return
    
    await interaction.response.send_message("📢 Broadcasting message...", ephemeral=True)
    
    success_count = 0
    for channel in interaction.guild.text_channels:
        if channel.permissions_for(interaction.guild.me).send_messages:
            try:
                embed = discord.Embed(
                    title="📣 Server Announcement",
                    description=message,
                    color=discord.Color.gold()
                )
                embed.set_footer(text=f"Sent by {interaction.user.display_name}")
                await channel.send(embed=embed)
                success_count += 1
                await asyncio.sleep(0.5)  # Rate limit prevention
            except:
                continue
    
    await interaction.followup.send(f"✅ Broadcast complete! Message sent to {success_count} channels.", ephemeral=True)

# ===== MODERATION COMMANDS =====
@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="Member to kick", reason="Reason for kicking")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ You don't have permission to kick members.", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role and interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You can't kick someone with equal or higher role.", ephemeral=True)
        return
    
    try:
        await member.kick(reason=f"{reason} | By {interaction.user}")
        await interaction.response.send_message(f"✅ {member.mention} has been kicked.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to kick this user.", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="Member to ban", reason="Reason for banning")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ You don't have permission to ban members.", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role and interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You can't ban someone with equal or higher role.", ephemeral=True)
        return
    
    try:
        await member.ban(reason=f"{reason} | By {interaction.user}", delete_message_days=0)
        await interaction.response.send_message(f"✅ {member.mention} has been banned.\n**Reason:** {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to ban this user.", ephemeral=True)

@bot.tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="Member to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ You don't have permission to warn members.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="⚠️ Warning Issued",
        description=f"You have been warned in **{interaction.guild.name}**",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Moderator", value=interaction.user.mention)
    
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass  # DMs disabled
    
    await interaction.response.send_message(f"✅ {member.mention} has been warned.\n**Reason:** {reason}")

# ===== RUN BOT =====
if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN not found in .env file")
    bot.run(BOT_TOKEN)