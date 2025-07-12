import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MissionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.missions = {}
        self.active_missions = {}
        self.rank_hierarchy = {
            "Student": 1,
            "Trainer": 2,
            "Command": 3
        }
        self.load_missions()
        
    def load_missions(self):
        """Load missions database"""
        try:
            missions_file = Path('data/missions.json')
            if missions_file.exists():
                with open(missions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.missions = data.get('missions', {})
                    self.active_missions = data.get('active_missions', {})
            else:
                self.missions = {}
                self.active_missions = {}
                self.save_missions()
        except Exception as e:
            logger.error(f"Error loading missions: {e}")
            self.missions = {}
            self.active_missions = {}
    
    async def save_missions(self):
        """Save missions database"""
        try:
            Path('data').mkdir(exist_ok=True)
            data = {
                'missions': self.missions,
                'active_missions': self.active_missions
            }
            with open('data/missions.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving missions: {e}")
    
    def get_user_rank(self, user):
        """Get user's rank"""
        role_names = [role.name.lower() for role in user.roles]
        
        if any(name in role_names for name in ['command', 'commander', 'chief']):
            return "Command"
        elif any(name in role_names for name in ['trainer', 'instructor', 'teacher']):
            return "Trainer"
        else:
            return "Student"

    @discord.app_commands.command(name="start_mission", description="Start a new EMS mission")
    @discord.app_commands.describe(
        mission_type="Type of mission",
        location="Mission location",
        description="Mission description"
    )
    @discord.app_commands.choices(mission_type=[
        discord.app_commands.Choice(name="Medical Evacuation", value="Medical Evacuation"),
        discord.app_commands.Choice(name="Search and Rescue", value="Search and Rescue"), 
        discord.app_commands.Choice(name="Emergency Response", value="Emergency Response"),
        discord.app_commands.Choice(name="Patient Transport", value="Patient Transport"),
        discord.app_commands.Choice(name="Training Flight", value="Training Flight"),
        discord.app_commands.Choice(name="Helicopter Rescue", value="Helicopter Rescue"),
        discord.app_commands.Choice(name="Multi-Unit Response", value="Multi-Unit Response"),
        discord.app_commands.Choice(name="Night Operations", value="Night Operations"),
        discord.app_commands.Choice(name="Weather Emergency", value="Weather Emergency"),
        discord.app_commands.Choice(name="Other", value="Other")
    ])
    async def start_mission(
        self,
        interaction: discord.Interaction,
        mission_type: str,
        location: str,
        description: str = "No description provided"
    ):
        """Start a new mission"""
        try:
            user_id = str(interaction.user.id)
            
            # Check if user already has active mission
            if user_id in self.active_missions:
                await interaction.response.send_message("❌ You already have an active mission. End it first with `/end_mission`.")
                return
            
            # Create mission
            mission_id = len(self.missions) + 1
            mission = {
                'id': mission_id,
                'user_id': user_id,
                'user_name': interaction.user.display_name,
                'type': mission_type,
                'location': location,
                'description': description,
                'start_time': datetime.now(timezone.utc).isoformat(),
                'end_time': None,
                'success': None,
                'notes': None
            }
            
            self.missions[str(mission_id)] = mission
            self.active_missions[user_id] = mission_id
            await self.save_missions()
            
            embed = discord.Embed(
                title="🚁 Mission Started",
                description=f"**{mission_type}** mission has begun",
                color=0x00ff00
            )
            embed.add_field(name="Mission ID", value=str(mission_id), inline=True)
            embed.add_field(name="Location", value=location, inline=True)
            embed.add_field(name="Pilot", value=interaction.user.display_name, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Started", value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:R>", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in start_mission command: {e}")
            await interaction.response.send_message("❌ An error occurred while starting the mission.")

    @discord.app_commands.command(name="end_mission", description="End your active mission")
    @discord.app_commands.describe(
        success="Was the mission successful?",
        notes="Additional mission notes"
    )
    @discord.app_commands.choices(success=[
        discord.app_commands.Choice(name="Successful", value="true"),
        discord.app_commands.Choice(name="Unsuccessful", value="false"),
        discord.app_commands.Choice(name="Partial Success", value="partial")
    ])
    async def end_mission(
        self,
        interaction: discord.Interaction,
        success: str,
        notes: str = None
    ):
        """End an active mission"""
        try:
            user_id = str(interaction.user.id)
            
            # Check if user has active mission
            if user_id not in self.active_missions:
                await interaction.response.send_message("❌ You don't have any active missions.")
                return
            
            mission_id = self.active_missions[user_id]
            mission = self.missions[str(mission_id)]
            
            # Update mission
            mission['end_time'] = datetime.now(timezone.utc).isoformat()
            mission['success'] = success
            mission['notes'] = notes
            
            # Remove from active missions
            del self.active_missions[user_id]
            await self.save_missions()
            
            # Calculate duration
            start_time = datetime.fromisoformat(mission['start_time'].replace('Z', '+00:00'))
            end_time = datetime.now(timezone.utc)
            duration = end_time - start_time
            
            success_emoji = "✅" if success == "true" else "⚠️" if success == "partial" else "❌"
            success_text = "Successful" if success == "true" else "Partial Success" if success == "partial" else "Unsuccessful"
            
            embed = discord.Embed(
                title=f"{success_emoji} Mission Completed",
                description=f"**{mission['type']}** mission ended",
                color=0x00ff00 if success == "true" else 0xffa500 if success == "partial" else 0xff0000
            )
            embed.add_field(name="Mission ID", value=str(mission_id), inline=True)
            embed.add_field(name="Location", value=mission['location'], inline=True)
            embed.add_field(name="Duration", value=f"{duration.seconds // 60} minutes", inline=True)
            embed.add_field(name="Status", value=success_text, inline=True)
            embed.add_field(name="Pilot", value=interaction.user.display_name, inline=True)
            if notes:
                embed.add_field(name="Notes", value=notes, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in end_mission command: {e}")
            await interaction.response.send_message("❌ An error occurred while ending the mission.")

    @commands.command(name="mission_status")
    async def mission_status(self, ctx):
        """Check current mission status"""
        try:
            user_id = str(ctx.author.id)
            
            if user_id not in self.active_missions:
                await ctx.send("📭 You don't have any active missions.")
                return
            
            mission_id = self.active_missions[user_id]
            mission = self.missions[str(mission_id)]
            
            start_time = datetime.fromisoformat(mission['start_time'].replace('Z', '+00:00'))
            duration = datetime.now(timezone.utc) - start_time
            
            embed = discord.Embed(
                title="🚁 Active Mission Status",
                description=f"**{mission['type']}** in progress",
                color=0x3498db
            )
            embed.add_field(name="Mission ID", value=str(mission_id), inline=True)
            embed.add_field(name="Location", value=mission['location'], inline=True)
            embed.add_field(name="Duration", value=f"{duration.seconds // 60} minutes", inline=True)
            embed.add_field(name="Description", value=mission['description'], inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in mission_status command: {e}")
            await ctx.send("❌ An error occurred while checking mission status.")

    @commands.command(name="mission_history")
    async def mission_history(self, ctx, user: str = None):
        """View mission history"""
        try:
            target_user = ctx.author if user is None else None
            
            # Filter missions
            user_missions = []
            for mission in self.missions.values():
                if user is None:
                    if mission['user_id'] == str(ctx.author.id):
                        user_missions.append(mission)
                else:
                    if user.lower() in mission['user_name'].lower():
                        user_missions.append(mission)
            
            if not user_missions:
                await ctx.send("📋 No mission history found.")
                return
            
            # Sort by start time (newest first)
            user_missions.sort(key=lambda x: x['start_time'], reverse=True)
            
            embed = discord.Embed(
                title="📋 Mission History",
                description=f"Recent missions for {target_user.display_name if target_user else user}",
                color=0x3498db
            )
            
            for mission in user_missions[:5]:  # Show last 5 missions
                success_emoji = "✅" if mission.get('success') == "true" else "⚠️" if mission.get('success') == "partial" else "❌" if mission.get('success') == "false" else "🔄"
                
                start_time = datetime.fromisoformat(mission['start_time'].replace('Z', '+00:00'))
                if mission.get('end_time'):
                    end_time = datetime.fromisoformat(mission['end_time'].replace('Z', '+00:00'))
                    duration = end_time - start_time
                    duration_text = f"{duration.seconds // 60} minutes"
                else:
                    duration_text = "In progress"
                
                embed.add_field(
                    name=f"{success_emoji} {mission['type']} (#{mission['id']})",
                    value=f"**Location:** {mission['location']}\n**Duration:** {duration_text}\n**Date:** <t:{int(start_time.timestamp())}:d>",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in mission_history command: {e}")
            await ctx.send("❌ An error occurred while loading mission history.")

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """Display mission leaderboard"""
        try:
            # Calculate stats
            user_stats = {}
            for mission in self.missions.values():
                user_id = mission['user_id']
                user_name = mission['user_name']
                
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'name': user_name,
                        'total': 0,
                        'successful': 0,
                        'unsuccessful': 0,
                        'partial': 0
                    }
                
                user_stats[user_id]['total'] += 1
                
                success = mission.get('success')
                if success == "true":
                    user_stats[user_id]['successful'] += 1
                elif success == "false":
                    user_stats[user_id]['unsuccessful'] += 1
                elif success == "partial":
                    user_stats[user_id]['partial'] += 1
            
            if not user_stats:
                await ctx.send("📊 No mission data available for leaderboard.")
                return
            
            # Sort by total missions
            sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['total'], reverse=True)
            
            embed = discord.Embed(
                title="🏆 Mission Leaderboard",
                description="Top pilots by mission count",
                color=0xffd700
            )
            
            for i, (user_id, stats) in enumerate(sorted_users[:10], 1):
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                
                embed.add_field(
                    name=f"{i}. {stats['name']}",
                    value=f"**Total:** {stats['total']} missions\n"
                          f"**Success Rate:** {success_rate:.1f}%\n"
                          f"✅ {stats['successful']} | ⚠️ {stats['partial']} | ❌ {stats['unsuccessful']}",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await ctx.send("❌ An error occurred while loading leaderboard.")

async def setup(bot):
    await bot.add_cog(MissionsCog(bot))