import os
from flask import Flask
from threading import Thread
import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# ===== KEEP-ALIVE WEB SERVER (prevents Replit sleep) =====
app = Flask('')

@app.route('/')
def home():
    return "Tempest is online! ✅"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ===========================================================

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Auto-reply keywords
AUTO_REPLIES = {
    "hello tempest": "Hello there! 👋 How can I help?",
    "thank you tempest": "You're welcome! 😊",
    "good bot": "Aww, thanks! ❤️",
    "bad bot": "I'll try harder next time... 😢"
}

@bot.event
async def on_ready():
    print(f"✅ Tempest is online as {bot.user}")
    await bot.tree.sync()

@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="welcome")
    embed = discord.Embed(
        title="🎉 Welcome to the server!",
        description=f"Hello {member.mention}, welcome to **{member.guild.name}**!",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="💡 Tip", value="Use `/help` to see what I can do!")
    
    if welcome_channel:
        await welcome_channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    content_lower = message.content.lower()
    for trigger, reply in AUTO_REPLIES.items():
        if trigger in content_lower:
            await message.reply(reply)
            break
    
    await bot.process_commands(message)

# ===== COMMANDS =====
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
    embed = discord.Embed(title="📚 Tempest Commands", color=discord.Color.blurple())
    embed.add_field(name="💬 General", value="`/start` - Start using the bot\n`/help` - Show this menu", inline=False)
    embed.add_field(name="📣 Broadcast (Admin)", value="`/broadcast [message]` - Send announcement", inline=False)
    embed.add_field(name="🛡️ Moderation (Admin)", value="`/kick`, `/ban`, `/warn`", inline=False)
    embed.set_footer(text="Tempest Bot • Made with ❤️")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="broadcast", description="Broadcast a message (Admin only)")
@app_commands.describe(message="Message to broadcast")
async def broadcast(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        return
    
    await interaction.response.send_message("📢 Broadcasting...", ephemeral=True)
    success = 0
    for channel in interaction.guild.text_channels:
        if channel.permissions_for(interaction.guild.me).send_messages:
            try:
                embed = discord.Embed(title="📣 Announcement", description=message, color=discord.Color.gold())
                embed.set_footer(text=f"By {interaction.user}")
                await channel.send(embed=embed)
                success += 1
                await asyncio.sleep(0.5)
            except:
                continue
    await interaction.followup.send(f"✅ Sent to {success} channels!", ephemeral=True)

@bot.tree.command(name="kick", description="Kick a member")
@app_commands.describe(member="Member to kick", reason="Reason")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ No permission!", ephemeral=True)
        return
    try:
        await member.kick(reason=f"{reason} | By {interaction.user}")
        await interaction.response.send_message(f"✅ Kicked {member.mention}\n**Reason:** {reason}")
    except:
        await interaction.response.send_message("❌ Failed to kick", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.describe(member="Member to ban", reason="Reason")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ No permission!", ephemeral=True)
        return
    try:
        await member.ban(reason=f"{reason} | By {interaction.user}")
        await interaction.response.send_message(f"✅ Banned {member.mention}\n**Reason:** {reason}")
    except:
        await interaction.response.send_message("❌ Failed to ban", ephemeral=True)

@bot.tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="Member to warn", reason="Reason")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ No permission!", ephemeral=True)
        return
    try:
        await member.send(f"⚠️ You were warned in **{interaction.guild.name}**\n**Reason:** {reason}\n**By:** {interaction.user}")
    except:
        pass
    await interaction.response.send_message(f"✅ Warned {member.mention}\n**Reason:** {reason}")

# ===== START BOT =====
if __name__ == "__main__":
    keep_alive()  # Start web server first
    
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise ValueError("❌ DISCORD_TOKEN not set in Secrets!")
    
    bot.run(TOKEN)