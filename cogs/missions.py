import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class MissionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.missions_file = Path('data/missions.json')
        self.missions = self.load_missions()
        self.active_missions = {}  # Store active missions by user ID
        
        # Mission types
        self.mission_types = [
            "Medical Evacuation",
            "Search and Rescue", 
            "Emergency Response",
            "Patient Transport",
            "Training Flight",
            "Helicopter Rescue",
            "Multi-Unit Response",
            "Night Operations",
            "Weather Emergency",
            "Other"
        ]
        
    def load_missions(self):
        """Load missions database"""
        try:
            if self.missions_file.exists():
                with open(self.missions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading missions: {e}")
            return []
    
    async def save_missions(self):
        """Save missions database"""
        try:
            with open(self.missions_file, 'w', encoding='utf-8') as f:
                json.dump(self.missions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving missions: {e}")

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
        return 'Student'

    @discord.app_commands.command(name="start_mission", description="Start a new EMS mission")
    @discord.app_commands.describe(description="Mission description")
    async def start_mission(
        self,
        ctx,
        mission_type: str = 
            str,
            "Type of mission",
            choices=["Medical Evacuation", "Search and Rescue", "Emergency Response", 
                    "Patient Transport", "Training Flight", "Helicopter Rescue",
                    "Multi-Unit Response", "Night Operations", "Weather Emergency", "Other"],
            required=True
        ),
        description: str = None,
        location: str = None
    ):
        """Start a new mission"""
        try:
            user_id = str(interaction.user.id)
            
            # Check if user already has an active mission
            if user_id in self.active_missions:
                await interaction.response.send_message("❌ You already have an active mission. End it first with `/end_mission`.")
                return
            
            # Create mission record
            mission = {
                'id': len(self.missions) + 1,
                'user_id': user_id,
                'username': interaction.user.display_name,
                'type': mission_type,
                'description': description or f"{mission_type} mission",
                'location': location,
                'start_time': datetime.now(timezone.utc).isoformat(),
                'end_time': None,
                'duration': None,
                'success': None,
                'status': 'Active',
                'user_rank': self.get_user_rank(interaction.user)
            }
            
            # Add to active missions
            self.active_missions[user_id] = mission
            
            # Create embed
            embed = discord.Embed(
                title="🚁 Mission Started",
                description=f"**{mission_type}** mission has been initiated",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="👤 Pilot", value=interaction.user.display_name, inline=True)
            embed.add_field(name="🎖️ Rank", value=mission['user_rank'], inline=True)
            embed.add_field(name="🆔 Mission ID", value=f"#{mission['id']}", inline=True)
            
            if description:
                embed.add_field(name="📋 Description", value=description, inline=False)
            
            if location:
                embed.add_field(name="📍 Location", value=location, inline=False)
            
            embed.add_field(
                name="⏰ Started",
                value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:F>",
                inline=False
            )
            
            embed.set_footer(text="Use /end_mission to complete this mission")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Mission started by {interaction.user} - Type: {mission_type}")
            
        except Exception as e:
            logger.error(f"Error in start_mission command: {e}")
            await interaction.response.send_message("❌ An error occurred while starting the mission.")

    @discord.app_commands.command(name="end_mission", description="End your active mission")
    @discord.app_commands.describe(description="Mission description")
    async def end_mission(
        self,
        ctx,
        success: str = 
            str,
            "Was the mission successful?",
            choices=["Yes", "No"],
            required=True
        ),
        notes: str = None
    ):
        """End an active mission"""
        try:
            user_id = str(interaction.user.id)
            
            # Check if user has an active mission
            if user_id not in self.active_missions:
                await interaction.response.send_message("❌ You don't have an active mission to end.")
                return
            
            # Get mission data
            mission = self.active_missions[user_id]
            
            # Calculate duration
            start_time = datetime.fromisoformat(mission['start_time'])
            end_time = datetime.now(timezone.utc)
            duration = end_time - start_time
            
            # Update mission record
            mission.update({
                'end_time': end_time.isoformat(),
                'duration': str(duration),
                'success': success == "Yes",
                'status': 'Completed',
                'notes': notes
            })
            
            # Move to completed missions
            self.missions.append(mission)
            del self.active_missions[user_id]
            
            # Save to file
            await self.save_missions()
            
            # Create embed
            success_color = 0x00ff00 if success == "Yes" else 0xff6b6b
            embed = discord.Embed(
                title="✅ Mission Completed" if success == "Yes" else "❌ Mission Failed",
                description=f"**{mission['type']}** mission has been completed",
                color=success_color,
                timestamp=end_time
            )
            
            embed.add_field(name="👤 Pilot", value=interaction.user.display_name, inline=True)
            embed.add_field(name="🆔 Mission ID", value=f"#{mission['id']}", inline=True)
            embed.add_field(name="✅ Success", value=success, inline=True)
            
            embed.add_field(name="⏱️ Duration", value=str(duration).split('.')[0], inline=True)
            embed.add_field(name="📍 Location", value=mission.get('location', 'Not specified'), inline=True)
            embed.add_field(name="🎖️ Rank", value=mission['user_rank'], inline=True)
            
            if mission.get('description'):
                embed.add_field(name="📋 Description", value=mission['description'], inline=False)
            
            if notes:
                embed.add_field(name="📝 Notes", value=notes, inline=False)
            
            embed.set_footer(text=f"Mission completed • Total missions: {len(self.missions)}")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Mission completed by {interaction.user} - Success: {success}")
            
        except Exception as e:
            logger.error(f"Error in end_mission command: {e}")
            await interaction.response.send_message("❌ An error occurred while ending the mission.")

    @discord.app_commands.command(name="mission_status", description="Check your current mission status")
    @discord.app_commands.describe(description="Mission description")
    async def mission_status(self, ctx):
        """Check current mission status"""
        try:
            user_id = str(interaction.user.id)
            
            if user_id not in self.active_missions:
                await interaction.response.send_message("📋 You don't have an active mission.")
                return
            
            mission = self.active_missions[user_id]
            start_time = datetime.fromisoformat(mission['start_time'])
            current_duration = datetime.now(timezone.utc) - start_time
            
            embed = discord.Embed(
                title="🚁 Active Mission Status",
                description=f"**{mission['type']}** - In Progress",
                color=0xffa500,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="🆔 Mission ID", value=f"#{mission['id']}", inline=True)
            embed.add_field(name="⏱️ Duration", value=str(current_duration).split('.')[0], inline=True)
            embed.add_field(name="🎖️ Rank", value=mission['user_rank'], inline=True)
            
            if mission.get('description'):
                embed.add_field(name="📋 Description", value=mission['description'], inline=False)
            
            if mission.get('location'):
                embed.add_field(name="📍 Location", value=mission['location'], inline=False)
            
            embed.add_field(
                name="⏰ Started",
                value=f"<t:{int(start_time.timestamp())}:R>",
                inline=False
            )
            
            embed.set_footer(text="Use /end_mission to complete this mission")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in mission_status command: {e}")
            await interaction.response.send_message("❌ An error occurred while checking mission status.")

    @discord.app_commands.command(name="mission_history", description="View your mission history")
    @discord.app_commands.describe(description="Mission description")
    async def mission_history(
        self,
        ctx,
        user: str = None
    ):
        """View mission history"""
        try:
            target_user = user if user else interaction.user
            requester_rank = self.get_user_rank(interaction.user)
            
            # Check permissions for viewing other users
            if user and requester_rank not in ['Trainer', 'Command']:
                await interaction.response.send_message("❌ You need Trainer rank or higher to view other users' mission history.")
                return
            
            # Filter missions for the target user
            user_missions = [m for m in self.missions if m['user_id'] == str(target_user.id)]
            
            if not user_missions:
                await interaction.response.send_message(f"📋 No completed missions found for {target_user.display_name}.")
                return
            
            # Calculate statistics
            total_missions = len(user_missions)
            successful_missions = sum(1 for m in user_missions if m.get('success', False))
            success_rate = (successful_missions / total_missions * 100) if total_missions > 0 else 0
            
            # Recent missions (last 10)
            recent_missions = sorted(user_missions, key=lambda x: x['start_time'], reverse=True)[:10]
            
            embed = discord.Embed(
                title=f"📊 Mission History - {target_user.display_name}",
                description=f"Flight record and statistics",
                color=0x3498db
            )
            
            embed.add_field(name="📈 Total Missions", value=str(total_missions), inline=True)
            embed.add_field(name="✅ Successful", value=str(successful_missions), inline=True)
            embed.add_field(name="📊 Success Rate", value=f"{success_rate:.1f}%", inline=True)
            
            # Mission types breakdown
            mission_types = {}
            for mission in user_missions:
                mission_type = mission['type']
                mission_types[mission_type] = mission_types.get(mission_type, 0) + 1
            
            if mission_types:
                types_text = "\n".join([f"• {mtype}: {count}" for mtype, count in sorted(mission_types.items())])
                embed.add_field(name="🎯 Mission Types", value=types_text, inline=False)
            
            # Recent missions
            if recent_missions:
                recent_text = ""
                for mission in recent_missions[:5]:
                    status_emoji = "✅" if mission.get('success', False) else "❌"
                    date = datetime.fromisoformat(mission['start_time']).strftime("%m/%d")
                    recent_text += f"{status_emoji} **{mission['type']}** - {date}\n"
                
                embed.add_field(name="🕒 Recent Missions", value=recent_text.strip(), inline=False)
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Rank: {user_missions[-1].get('user_rank', 'Unknown')}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in mission_history command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading mission history.")

    @discord.app_commands.command(name="leaderboard", description="View mission leaderboard")
    @discord.app_commands.describe(description="Mission description")
    async def leaderboard(self, ctx):
        """Display mission leaderboard"""
        try:
            if not self.missions:
                await interaction.response.send_message("📋 No missions have been completed yet.")
                return
            
            # Calculate user statistics
            user_stats = {}
            for mission in self.missions:
                user_id = mission['user_id']
                username = mission['username']
                
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'username': username,
                        'total': 0,
                        'successful': 0,
                        'rank': mission.get('user_rank', 'Unknown')
                    }
                
                user_stats[user_id]['total'] += 1
                if mission.get('success', False):
                    user_stats[user_id]['successful'] += 1
            
            # Sort by successful missions, then by total missions
            sorted_users = sorted(
                user_stats.items(),
                key=lambda x: (x[1]['successful'], x[1]['total']),
                reverse=True
            )
            
            embed = discord.Embed(
                title="🏆 EMS Mission Leaderboard",
                description="Top pilots by successful missions",
                color=0xf1c40f
            )
            
            leaderboard_text = ""
            for i, (user_id, stats) in enumerate(sorted_users[:10], 1):
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                
                if i == 1:
                    emoji = "🥇"
                elif i == 2:
                    emoji = "🥈"
                elif i == 3:
                    emoji = "🥉"
                else:
                    emoji = f"{i}."
                
                leaderboard_text += f"{emoji} **{stats['username']}**\n"
                leaderboard_text += f"   ✅ {stats['successful']}/{stats['total']} ({success_rate:.1f}%)\n"
                leaderboard_text += f"   🎖️ {stats['rank']}\n\n"
            
            embed.add_field(
                name="📊 Rankings",
                value=leaderboard_text.strip(),
                inline=False
            )
            
            embed.set_footer(text=f"Total completed missions: {len(self.missions)}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading the leaderboard.")

async def setup(bot):
    await bot.add_cog(MissionsCog(bot))
