import discord
from discord.ext import commands, tasks
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders_file = Path('data/reminders.json')
        self.reminders = self.load_reminders()
        self.reminder_check.start()
        
    def load_reminders(self):
        """Load reminders database"""
        try:
            if self.reminders_file.exists():
                with open(self.reminders_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading reminders: {e}")
            return []
    
    async def save_reminders(self):
        """Save reminders database"""
        try:
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")

    def get_user_rank(self, user):
        """Get user's rank"""
        try:
            users_file = Path('data/users.json')
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                    user_data = users_data.get(str(user.id), {})
                    return user_data.get('rank', 'Student')
        except:
            pass
        
        # Check admin permissions
        if user.guild_permissions.administrator:
            return 'Command'
        return 'Student'

    @discord.app_commands.command(name="schedule", description="Schedule a reminder message (Trainer+ only)")
    async def schedule(
        self,
        ctx,
        message: str,
        time: str,
        channel: str = None,
        repeat: str = 
            str,
            "Repeat interval",
            choices=["None", "Daily", "Weekly", "Monthly"],
            required=False
        ) = "None"
    ):
        """Schedule a reminder message"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Check permissions (Trainer+ only)
            if user_rank not in ['Trainer', 'Command']:
                await interaction.response.send_message("❌ You need Trainer rank or higher to schedule reminders.")
                return
            
            # Parse time
            try:
                reminder_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
                reminder_time = reminder_time.replace(tzinfo=timezone.utc)
            except ValueError:
                await interaction.response.send_message("❌ Invalid time format. Use: YYYY-MM-DD HH:MM (UTC)")
                return
            
            # Check if time is in the future
            if reminder_time <= datetime.now(timezone.utc):
                await interaction.response.send_message("❌ Reminder time must be in the future.")
                return
            
            # Set default channel
            target_channel = channel if channel else interaction.channel
            
            # Create reminder
            reminder = {
                'id': len(self.reminders) + 1,
                'message': message,
                'scheduled_time': reminder_time.isoformat(),
                'channel_id': target_channel.id,
                'guild_id': interaction.guild.id,
                'created_by': str(interaction.user.id),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'repeat': repeat,
                'sent': False,
                'active': True
            }
            
            self.reminders.append(reminder)
            await self.save_reminders()
            
            embed = discord.Embed(
                title="⏰ Reminder Scheduled",
                description="Your reminder has been successfully scheduled",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="📝 Message", value=message, inline=False)
            embed.add_field(name="📅 Scheduled Time", value=f"<t:{int(reminder_time.timestamp())}:F>", inline=True)
            embed.add_field(name="📺 Channel", value=target_channel.mention, inline=True)
            embed.add_field(name="🔄 Repeat", value=repeat, inline=True)
            embed.add_field(name="🆔 Reminder ID", value=f"#{reminder['id']}", inline=True)
            embed.add_field(name="⏱️ Time Until", value=f"<t:{int(reminder_time.timestamp())}:R>", inline=True)
            
            embed.set_footer(text=f"Created by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Reminder scheduled by {interaction.user} for {reminder_time}")
            
        except Exception as e:
            logger.error(f"Error in schedule command: {e}")
            await interaction.response.send_message("❌ An error occurred while scheduling the reminder.")

    @discord.app_commands.command(name="reminders", description="View scheduled reminders")
    @discord.app_commands.describe(message="The reminder message")
    async def view_reminders(self, ctx):
        """View all scheduled reminders"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Filter reminders based on permissions
            if user_rank in ['Trainer', 'Command']:
                # Trainers can see all reminders
                visible_reminders = [r for r in self.reminders if r.get('active', True)]
            else:
                # Students can only see their own
                visible_reminders = [
                    r for r in self.reminders 
                    if r.get('created_by') == str(interaction.user.id) and r.get('active', True)
                ]
            
            if not visible_reminders:
                await interaction.response.send_message("📅 No active reminders found.")
                return
            
            # Sort by scheduled time
            visible_reminders.sort(key=lambda x: x['scheduled_time'])
            
            embed = discord.Embed(
                title="📅 Scheduled Reminders",
                description=f"Active reminders ({len(visible_reminders)} total)",
                color=0x3498db
            )
            
            for reminder in visible_reminders[:10]:  # Show max 10 reminders
                scheduled_time = datetime.fromisoformat(reminder['scheduled_time'])
                creator = self.bot.get_user(int(reminder['created_by']))
                creator_name = creator.display_name if creator else "Unknown"
                
                channel = self.bot.get_channel(reminder['channel_id'])
                channel_name = channel.name if channel else "Unknown Channel"
                
                field_value = f"📝 {reminder['message'][:100]}{'...' if len(reminder['message']) > 100 else ''}\n"
                field_value += f"📺 #{channel_name}\n"
                field_value += f"🔄 {reminder.get('repeat', 'None')}\n"
                field_value += f"👤 {creator_name}\n"
                field_value += f"⏰ <t:{int(scheduled_time.timestamp())}:R>"
                
                embed.add_field(
                    name=f"🆔 #{reminder['id']} - <t:{int(scheduled_time.timestamp())}:f>",
                    value=field_value,
                    inline=False
                )
            
            if len(visible_reminders) > 10:
                embed.set_footer(text=f"Showing 10 of {len(visible_reminders)} reminders")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in view_reminders command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading reminders.")

    @discord.app_commands.command(name="cancel_reminder", description="Cancel a scheduled reminder")
    @discord.app_commands.describe(message="The reminder message")
    async def cancel_reminder(
        self,
        ctx,
        reminder_id: str
    ):
        """Cancel a scheduled reminder"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Find reminder
            reminder = None
            for r in self.reminders:
                if r['id'] == reminder_id:
                    reminder = r
                    break
            
            if not reminder:
                await interaction.response.send_message(f"❌ Reminder #{reminder_id} not found.")
                return
            
            # Check permissions
            if (reminder['created_by'] != str(interaction.user.id) and 
                user_rank not in ['Trainer', 'Command']):
                await interaction.response.send_message("❌ You can only cancel your own reminders.")
                return
            
            # Check if already sent or cancelled
            if not reminder.get('active', True):
                await interaction.response.send_message(f"❌ Reminder #{reminder_id} is already cancelled.")
                return
            
            # Cancel reminder
            reminder['active'] = False
            reminder['cancelled_at'] = datetime.now(timezone.utc).isoformat()
            reminder['cancelled_by'] = str(interaction.user.id)
            
            await self.save_reminders()
            
            embed = discord.Embed(
                title="🗑️ Reminder Cancelled",
                description=f"Reminder #{reminder_id} has been cancelled",
                color=0xff6b6b
            )
            
            embed.add_field(name="📝 Message", value=reminder['message'], inline=False)
            
            scheduled_time = datetime.fromisoformat(reminder['scheduled_time'])
            embed.add_field(
                name="📅 Was Scheduled For",
                value=f"<t:{int(scheduled_time.timestamp())}:F>",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Reminder #{reminder_id} cancelled by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in cancel_reminder command: {e}")
            await interaction.response.send_message("❌ An error occurred while cancelling the reminder.")

    @tasks.loop(minutes=1)
    async def reminder_check(self):
        """Check for reminders that need to be sent"""
        try:
            current_time = datetime.now(timezone.utc)
            
            for reminder in self.reminders:
                if (reminder.get('active', True) and 
                    not reminder.get('sent', False)):
                    
                    scheduled_time = datetime.fromisoformat(reminder['scheduled_time'])
                    
                    # Check if it's time to send
                    if current_time >= scheduled_time:
                        await self.send_reminder(reminder)
            
        except Exception as e:
            logger.error(f"Error in reminder check: {e}")

    async def send_reminder(self, reminder):
        """Send a reminder message"""
        try:
            channel = self.bot.get_channel(reminder['channel_id'])
            if not channel:
                logger.warning(f"Channel {reminder['channel_id']} not found for reminder {reminder['id']}")
                return
            
            creator = self.bot.get_user(int(reminder['created_by']))
            creator_name = creator.display_name if creator else "Unknown"
            
            embed = discord.Embed(
                title="⏰ Scheduled Reminder",
                description=reminder['message'],
                color=0xf39c12,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.set_footer(text=f"Scheduled by {creator_name}")
            
            await channel.send(embed=embed)
            
            # Mark as sent
            reminder['sent'] = True
            reminder['sent_at'] = datetime.now(timezone.utc).isoformat()
            
            # Handle repeating reminders
            repeat_type = reminder.get('repeat', 'None')
            if repeat_type != 'None':
                await self.schedule_repeat(reminder, repeat_type)
            else:
                reminder['active'] = False
            
            await self.save_reminders()
            logger.info(f"Reminder {reminder['id']} sent to {channel.name}")
            
        except Exception as e:
            logger.error(f"Error sending reminder {reminder['id']}: {e}")

    async def schedule_repeat(self, reminder, repeat_type):
        """Schedule the next occurrence of a repeating reminder"""
        try:
            scheduled_time = datetime.fromisoformat(reminder['scheduled_time'])
            
            # Calculate next occurrence
            if repeat_type == 'Daily':
                next_time = scheduled_time.replace(day=scheduled_time.day + 1)
            elif repeat_type == 'Weekly':
                next_time = scheduled_time.replace(day=scheduled_time.day + 7)
            elif repeat_type == 'Monthly':
                if scheduled_time.month == 12:
                    next_time = scheduled_time.replace(year=scheduled_time.year + 1, month=1)
                else:
                    next_time = scheduled_time.replace(month=scheduled_time.month + 1)
            else:
                return
            
            # Create new reminder
            new_reminder = reminder.copy()
            new_reminder.update({
                'id': len(self.reminders) + 1,
                'scheduled_time': next_time.isoformat(),
                'sent': False,
                'active': True
            })
            
            self.reminders.append(new_reminder)
            logger.info(f"Repeat reminder scheduled for {next_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling repeat reminder: {e}")

    @reminder_check.before_loop
    async def before_reminder_check(self):
        """Wait for bot to be ready before starting reminder check"""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
