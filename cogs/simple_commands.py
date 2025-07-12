import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SimpleCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_slash_commands()
        
    def setup_slash_commands(self):
        """Setup slash commands manually"""
        @self.bot.tree.command(name="help_ems", description="Get help with EMS commands")
        async def help_ems(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🚁 EMS Training Bot Commands",
                description="Available commands for EMS flight training",
                color=0x3498db
            )
            
            embed.add_field(
                name="📢 Alert System",
                value="• Type emergency keywords (mayday, engine failure, crash) to trigger alerts\n"
                      "• `/emergency_info` - Emergency procedures guide",
                inline=False
            )
            
            embed.add_field(
                name="🧠 Help System", 
                value="• `/ask_ems <question>` - Ask EMS questions\n"
                      "• `/ems_topics` - Browse knowledge topics\n"
                      "• `/emergency_guide` - Quick emergency guide",
                inline=False
            )
            
            embed.add_field(
                name="📁 Document System",
                value="• `/docs` - View training documents\n"
                      "• `/upload_doc` - Upload document (Trainer+)\n"
                      "• `/doc_categories` - View categories",
                inline=False
            )
            
            embed.add_field(
                name="🛫 Mission System",
                value="• `/start_mission <type>` - Start new mission\n"
                      "• `/end_mission <success>` - End mission\n"
                      "• `/mission_status` - Check current mission\n"
                      "• `/mission_history` - View history\n"
                      "• `/leaderboard` - Mission leaderboard",
                inline=False
            )
            
            embed.add_field(
                name="🎖️ Rank System",
                value="• `/rank [user]` - Check rank\n"
                      "• `/promote <user> <rank>` - Promote user (Command)\n"
                      "• `/ranks` - View all ranks\n"
                      "• `/staff` - View staff members",
                inline=False
            )
            
            embed.add_field(
                name="⏰ Reminders",
                value="• `/schedule <message> <time>` - Schedule reminder (Trainer+)\n"
                      "• `/reminders` - View scheduled reminders\n"
                      "• `/cancel_reminder <id>` - Cancel reminder",
                inline=False
            )
            
            embed.set_footer(text="EMS Training Bot | Emergency Medical Services Flight Training")
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name="status", description="Check bot status")
        async def status(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🤖 Bot Status",
                description="EMS Training Bot is online and operational",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="🔧 Features Available", value="✅ Emergency Alerts\n✅ AI Help System\n✅ Document Management\n✅ Mission Logging\n✅ Rank System\n✅ Reminders", inline=True)
            embed.add_field(name="📊 Server", value=f"Guilds: {len(self.bot.guilds)}\nLatency: {round(self.bot.latency * 1000)}ms", inline=True)
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SimpleCommandsCog(bot))