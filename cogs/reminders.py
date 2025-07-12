import discord
from discord.ext import commands, tasks
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
import asyncio

logger = logging.getLogger(__name__)

class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}
        self.rank_hierarchy = {
            "Student": 1,
            "Trainer": 2,
            "Command": 3
        }
        self.load_reminders()
        self.reminder_check.start()
        
    def load_reminders(self):
        """Load reminders database"""
        try:
            reminders_file = Path('data/reminders.json')
            if reminders_file.exists():
                with open(reminders_file, 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
            else:
                self.reminders = {}
                self.save_reminders()
        except Exception as e:
            logger.error(f"Error loading reminders: {e}")
            self.reminders = {}
    
    async def save_reminders(self):
        """Save reminders database"""
        try:
            Path('data').mkdir(exist_ok=True)
            with open('data/reminders.json', 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")
    
    def get_user_rank(self, user):
        """Get user's rank"""
        role_names = [role.name.lower() for role in user.roles]
        
        if any(name in role_names for name in ['command', 'commander', 'chief']):
            return "Command"
        elif any(name in role_names for name in ['trainer', 'instructor', 'teacher']):
            return "Trainer"
        else:
            return "Student"

    @discord.app_commands.command(name="schedule", description="Schedule a reminder message (Trainer+ only)")
    @discord.app_commands.describe(
        message="Reminder message",
        minutes="Minutes from now to send reminder",
        repeat="Repeat interval"
    )
    @discord.app_commands.choices(repeat=[
        discord.app_commands.Choice(name="None", value="None"),
        discord.app_commands.Choice(name="Daily", value="Daily"),
        discord.app_commands.Choice(name="Weekly", value="Weekly"),
        discord.app_commands.Choice(name="Monthly", value="Monthly")
    ])
    async def schedule(
        self,
        interaction: discord.Interaction,
        message: str,
        minutes: int,
        repeat: str = "None"
    ):
        """Schedule a reminder message"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Check permissions (Trainer+ only)
            if self.rank_hierarchy.get(user_rank, 0) < 2:
                await interaction.response.send_message("❌ You need Trainer rank or higher to schedule reminders.")
                return
            
            # Calculate reminder time
            reminder_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
            
            # Create reminder
            reminder_id = len(self.reminders) + 1
            reminder = {
                'id': reminder_id,
                'message': message,
                'channel_id': str(interaction.channel.id),
                'created_by': str(interaction.user.id),
                'created_by_name': interaction.user.display_name,
                'reminder_time': reminder_time.isoformat(),
                'repeat': repeat,
                'active': True,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.reminders[str(reminder_id)] = reminder
            await self.save_reminders()
            
            embed = discord.Embed(
                title="⏰ Reminder Scheduled",
                description=f"Reminder #{reminder_id} has been scheduled",
                color=0x00ff00
            )
            embed.add_field(name="Message", value=message, inline=False)
            embed.add_field(name="Time", value=f"<t:{int(reminder_time.timestamp())}:F>", inline=True)
            embed.add_field(name="Repeat", value=repeat, inline=True)
            embed.add_field(name="Created By", value=interaction.user.display_name, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in schedule command: {e}")
            await interaction.response.send_message("❌ An error occurred while scheduling the reminder.")

    @commands.command(name="reminders")
    async def view_reminders(self, ctx):
        """View all scheduled reminders"""
        try:
            active_reminders = {k: v for k, v in self.reminders.items() if v.get('active', True)}
            
            if not active_reminders:
                await ctx.send("📅 No active reminders scheduled.")
                return
            
            embed = discord.Embed(
                title="📅 Scheduled Reminders",
                description="All active reminders",
                color=0x3498db
            )
            
            for reminder_id, reminder in list(active_reminders.items())[:10]:  # Show max 10
                reminder_time = datetime.fromisoformat(reminder['reminder_time'].replace('Z', '+00:00'))
                
                embed.add_field(
                    name=f"#{reminder['id']} | {reminder.get('repeat', 'One-time')}",
                    value=f"**Message:** {reminder['message'][:100]}...\n"
                          f"**Time:** <t:{int(reminder_time.timestamp())}:R>\n"
                          f"**Created by:** {reminder.get('created_by_name', 'Unknown')}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in view_reminders command: {e}")
            await ctx.send("❌ An error occurred while loading reminders.")

    @commands.command(name="cancel_reminder")
    async def cancel_reminder(self, ctx, reminder_id: str):
        """Cancel a scheduled reminder"""
        try:
            user_rank = self.get_user_rank(ctx.author)
            
            # Check permissions (Trainer+ only)
            if self.rank_hierarchy.get(user_rank, 0) < 2:
                await ctx.send("❌ You need Trainer rank or higher to cancel reminders.")
                return
            
            # Find reminder
            if reminder_id not in self.reminders:
                await ctx.send(f"❌ Reminder #{reminder_id} not found.")
                return
            
            reminder = self.reminders[reminder_id]
            reminder['active'] = False
            await self.save_reminders()
            
            await ctx.send(f"✅ Cancelled reminder #{reminder_id}: **{reminder['message'][:50]}...**")
            
        except Exception as e:
            logger.error(f"Error in cancel_reminder command: {e}")
            await ctx.send("❌ An error occurred while cancelling the reminder.")

    @tasks.loop(minutes=1)
    async def reminder_check(self):
        """Check for reminders that need to be sent"""
        try:
            current_time = datetime.now(timezone.utc)
            
            for reminder_id, reminder in list(self.reminders.items()):
                if not reminder.get('active', True):
                    continue
                
                reminder_time = datetime.fromisoformat(reminder['reminder_time'].replace('Z', '+00:00'))
                
                # Check if it's time to send the reminder
                if current_time >= reminder_time:
                    await self.send_reminder(reminder)
                    
                    # Handle repeat reminders
                    repeat_type = reminder.get('repeat', 'None')
                    if repeat_type != 'None':
                        await self.schedule_repeat(reminder, repeat_type)
                    else:
                        # Mark as inactive for one-time reminders
                        reminder['active'] = False
                    
                    await self.save_reminders()
                    
        except Exception as e:
            logger.error(f"Error in reminder check: {e}")

    async def send_reminder(self, reminder):
        """Send a reminder message"""
        try:
            channel = self.bot.get_channel(int(reminder['channel_id']))
            if not channel:
                logger.warning(f"Channel {reminder['channel_id']} not found for reminder {reminder['id']}")
                return
            
            embed = discord.Embed(
                title="⏰ Scheduled Reminder",
                description=reminder['message'],
                color=0xffa500
            )
            embed.add_field(name="Created By", value=reminder.get('created_by_name', 'Unknown'), inline=True)
            embed.add_field(name="Reminder ID", value=f"#{reminder['id']}", inline=True)
            
            await channel.send(content="📢 **REMINDER**", embed=embed)
            logger.info(f"Sent reminder {reminder['id']} to channel {reminder['channel_id']}")
            
        except Exception as e:
            logger.error(f"Error sending reminder {reminder.get('id', 'unknown')}: {e}")

    async def schedule_repeat(self, reminder, repeat_type):
        """Schedule the next occurrence of a repeating reminder"""
        try:
            current_time = datetime.fromisoformat(reminder['reminder_time'].replace('Z', '+00:00'))
            
            if repeat_type == 'Daily':
                next_time = current_time + timedelta(days=1)
            elif repeat_type == 'Weekly':
                next_time = current_time + timedelta(weeks=1)
            elif repeat_type == 'Monthly':
                next_time = current_time + timedelta(days=30)  # Approximate month
            else:
                return
            
            reminder['reminder_time'] = next_time.isoformat()
            
        except Exception as e:
            logger.error(f"Error scheduling repeat for reminder {reminder.get('id', 'unknown')}: {e}")

    @reminder_check.before_loop
    async def before_reminder_check(self):
        """Wait for bot to be ready before starting reminder check"""
        await self.bot.wait_until_ready()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.reminder_check.cancel()

async def setup(bot):
    await bot.add_cog(RemindersCog(bot))