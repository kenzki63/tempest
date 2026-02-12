import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread
import asyncio

# ===== FLASK KEEP-ALIVE SERVER (Prevents Render sleep) =====
app = Flask(__name__)

@app.route('/')
def home():
    return {
        "status": "online",
        "bot": "Tempest",
        "message": "✅ Tempest is running and ready to serve!"
    }, 200

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

def run_flask():
    """Run Flask server on port 8080"""
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Start Flask in background thread"""
    t = Thread(target=run_flask, daemon=True)
    t.start()
# ===========================================================

# ===== DISCORD BOT SETUP =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ===== CONFIGURATION =====
WELCOME_CHANNEL_NAME = "welcome"  # Channel for welcome messages
AUTO_REPLIES = {
    "hello tempest": "Hello there! 👋 How can I help?",
    "hey tempest": "Hey! What's up? 😊",
    "thank you tempest": "You're welcome! ❤️",
    "thanks tempest": "Anytime! 😊",
    "good bot": "Aww, thanks! ❤️",
    "bad bot": "I'll try harder next time... 😢",
    "tempest": "Yes? I'm here! 💨",
    "ping": "Pong! 🏓",
    "help": "Use `/help` to see all my commands!"
}

# ===== EVENTS =====
@bot.event
async def on_ready():
    """Bot startup event"""
    print("=" * 50)
    print(f"✅ TEMPEST IS ONLINE")
    print(f"🤖 Bot: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🌐 Connected to {len(bot.guilds)} server(s)")
    print("=" * 50)
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@bot.event
async def on_member_join(member):
    """Send welcome message when new member joins"""
    welcome_channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)
    
    embed = discord.Embed(
        title="🎉 Welcome to the Server!",
        description=f"Hello {member.mention}, welcome to **{member.guild.name}**! 🎊",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name="💡 Getting Started",
        value="• Use `/help` to see my commands\n• Read the rules channel\n• Introduce yourself!",
        inline=False
    )
    embed.set_footer(text=f"Member #{member.guild.member_count}", icon_url=member.guild.icon.url if member.guild.icon else None)
    
    # Send to welcome channel or fallback to DM
    if welcome_channel:
        try:
            await welcome_channel.send(embed=embed)
        except:
            pass
    else:
        # Try DM as fallback
        try:
            await member.send(f"👋 Welcome to **{member.guild.name}**! Make yourself at home!")
        except discord.Forbidden:
            pass  # DMs disabled

@bot.event
async def on_message(message):
    """Handle auto-replies and process commands"""
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Check for auto-reply triggers (case-insensitive)
    content_lower = message.content.lower().strip()
    
    # Exact match or contains
    for trigger, reply in AUTO_REPLIES.items():
        if trigger in content_lower or content_lower == trigger:
            # Add reaction to show bot is responding
            try:
                await message.add_reaction("⚡")
            except:
                pass
            
            await message.channel.send(f"{message.author.mention} {reply}")
            break
    
    # Process commands
    await bot.process_commands(message)

# ===== SLASH COMMANDS =====

@bot.tree.command(name="start", description="👋 Start interacting with Tempest")
async def start(interaction: discord.Interaction):
    """Start command - introduces the bot"""
    embed = discord.Embed(
        title="✨ Welcome to Tempest!",
        description="Hello! I'm **Tempest**, your friendly server assistant. 💨",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(
        name="🚀 What I Can Do",
        value="• Auto-reply to common messages\n• Welcome new members\n• Broadcast announcements\n• Moderate the server\n• And more!",
        inline=False
    )
    embed.add_field(
        name="📚 Getting Started",
        value="Use `/help` to see all available commands!",
        inline=False
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text="Made with ❤️ by Tempest Team")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="📚 Show all available commands")
async def help_cmd(interaction: discord.Interaction):
    """Help command - lists all commands"""
    embed = discord.Embed(
        title="📚 Tempest Bot Commands",
        description="Here's everything I can do for you!",
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )
    
    # General Commands
    embed.add_field(
        name="💬 General Commands",
        value="```\n/start      - Start using the bot\n/help       - Show this menu\n```",
        inline=False
    )
    
    # Admin Commands
    embed.add_field(
        name="📣 Admin Commands",
        value="```\n/broadcast  - Send announcement to all channels\n```",
        inline=False
    )
    
    # Moderation Commands
    embed.add_field(
        name="🛡️ Moderation Commands",
        value="```\n/kick       - Kick a member\n/ban        - Ban a member\n/warn       - Warn a member\n```",
        inline=False
    )
    
    # Info
    embed.add_field(
        name="💡 Tips",
        value="• Commands with `@` require mentioning a user\n• Only admins can use moderation commands\n• I auto-reply to common phrases!",
        inline=False
    )
    
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text="Tempest Bot • Use /help for more info")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="broadcast", description="📣 Broadcast a message to all text channels (Admin only)")
@app_commands.describe(message="The announcement message to broadcast")
async def broadcast(interaction: discord.Interaction, message: str):
    """Broadcast announcement to all text channels"""
    # Permission check
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need **Administrator** permissions to use this command.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    # Send embed announcement
    embed = discord.Embed(
        title="📣 Server Announcement",
        description=message,
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Sent by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    
    # Broadcast to all text channels
    success_count = 0
    failed_count = 0
    
    for channel in interaction.guild.text_channels:
        # Check if bot has permission to send messages
        if channel.permissions_for(interaction.guild.me).send_messages:
            try:
                await channel.send(embed=embed)
                success_count += 1
                await asyncio.sleep(0.3)  # Rate limit prevention
            except:
                failed_count += 1
                continue
    
    # Send summary
    summary_embed = discord.Embed(
        title="✅ Broadcast Complete",
        description=f"Message sent to **{success_count}** channel(s)",
        color=discord.Color.green()
    )
    if failed_count > 0:
        summary_embed.add_field(name="⚠️ Failed", value=f"Could not send to {failed_count} channel(s)", inline=False)
    
    await interaction.followup.send(embed=summary_embed, ephemeral=True)

# ===== MODERATION COMMANDS =====

@bot.tree.command(name="kick", description="👢 Kick a member from the server")
@app_commands.describe(
    member="The member to kick",
    reason="Reason for kicking (optional)"
)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    """Kick a member from the server"""
    # Permission checks
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message(
            "❌ You don't have permission to kick members.",
            ephemeral=True
        )
        return
    
    if member == interaction.user:
        await interaction.response.send_message(
            "❌ You can't kick yourself!",
            ephemeral=True
        )
        return
    
    if member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
        await interaction.response.send_message(
            "❌ You can't kick someone with equal or higher role than you.",
            ephemeral=True
        )
        return
    
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I don't have permission to kick this user (role hierarchy).",
            ephemeral=True
        )
        return
    
    # Try to DM the user before kicking
    try:
        dm_embed = discord.Embed(
            title="👢 You Have Been Kicked",
            description=f"You were kicked from **{interaction.guild.name}**",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        dm_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        await member.send(embed=dm_embed)
    except:
        pass  # DM failed, continue anyway
    
    # Kick the member
    try:
        await member.kick(reason=f"{reason} | By {interaction.user}")
        
        # Success message
        embed = discord.Embed(
            title="✅ Member Kicked",
            description=f"{member.mention} has been kicked from the server.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to kick this member.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="ban", description="🔨 Ban a member from the server")
@app_commands.describe(
    member="The member to ban",
    reason="Reason for banning (optional)"
)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    """Ban a member from the server"""
    # Permission checks
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message(
            "❌ You don't have permission to ban members.",
            ephemeral=True
        )
        return
    
    if member == interaction.user:
        await interaction.response.send_message(
            "❌ You can't ban yourself!",
            ephemeral=True
        )
        return
    
    if member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
        await interaction.response.send_message(
            "❌ You can't ban someone with equal or higher role than you.",
            ephemeral=True
        )
        return
    
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I don't have permission to ban this user (role hierarchy).",
            ephemeral=True
        )
        return
    
    # Try to DM the user before banning
    try:
        dm_embed = discord.Embed(
            title="🔨 You Have Been Banned",
            description=f"You were banned from **{interaction.guild.name}**",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        dm_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        await member.send(embed=dm_embed)
    except:
        pass  # DM failed
    
    # Ban the member
    try:
        await member.ban(reason=f"{reason} | By {interaction.user}", delete_message_days=0)
        
        # Success message
        embed = discord.Embed(
            title="✅ Member Banned",
            description=f"{member.mention} has been banned from the server.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to ban this member.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="warn", description="⚠️ Warn a member")
@app_commands.describe(
    member="The member to warn",
    reason="Reason for warning"
)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    """Warn a member"""
    # Permission check
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message(
            "❌ You don't have permission to warn members.",
            ephemeral=True
        )
        return
    
    # Try to DM the user
    try:
        dm_embed = discord.Embed(
            title="⚠️ Warning",
            description=f"You have received a warning in **{interaction.guild.name}**",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        dm_embed.set_footer(text="Please follow the server rules!")
        await member.send(embed=dm_embed)
        dm_status = "✅ User notified via DM"
    except:
        dm_status = "⚠️ Could not DM user"
    
    # Public warning message
    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=f"{member.mention} has been warned.",
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    embed.add_field(name="DM Status", value=dm_status, inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

# ===== ERROR HANDLING =====
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle slash command errors"""
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
    elif isinstance(error, app_commands.errors.BotMissingPermissions):
        await interaction.response.send_message(
            "❌ I don't have the required permissions to do that.",
            ephemeral=True
        )
    elif isinstance(error, app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            f"❌ This command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
            ephemeral=True
        )
    else:
        print(f"⚠️ Command error: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ An error occurred while processing your command.",
                ephemeral=True
            )

# ===== BOT STARTUP =====
if __name__ == "__main__":
    # Start Flask keep-alive server
    keep_alive()
    print("🚀 Flask server started on port 8080")
    
    # Get bot token from environment variable
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    if not TOKEN:
        raise ValueError("❌ DISCORD_TOKEN environment variable not set!")
    
    # Run the bot
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid bot token! Check your DISCORD_TOKEN environment variable.")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")