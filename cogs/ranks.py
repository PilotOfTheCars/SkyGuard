import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class RanksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self.rank_hierarchy = {
            "Student": 1,
            "Trainer": 2,
            "Command": 3
        }
        self.rank_colors = {
            "Student": 0x3498db,    # Blue
            "Trainer": 0xf39c12,    # Orange  
            "Command": 0xe74c3c     # Red
        }
        self.load_users()
        
    def load_users(self):
        """Load users database"""
        try:
            users_file = Path('data/users.json')
            if users_file.exists():
                with open(users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
                self.save_users()
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            self.users = {}
    
    async def save_users(self):
        """Save users database"""
        try:
            Path('data').mkdir(exist_ok=True)
            with open('data/users.json', 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def get_user_rank(self, user_id):
        """Get user's current rank"""
        return self.users.get(str(user_id), {}).get('rank', 'Student')
    
    def can_promote(self, promoter_rank, target_rank, new_rank):
        """Check if user can promote another user"""
        promoter_level = self.rank_hierarchy.get(promoter_rank, 0)
        target_level = self.rank_hierarchy.get(target_rank, 0)
        new_level = self.rank_hierarchy.get(new_rank, 0)
        
        # Must be Command rank to promote anyone
        if promoter_level < 3:
            return False
            
        # Cannot promote to same or higher rank than promoter
        if new_level >= promoter_level:
            return False
            
        return True

    @discord.app_commands.command(name="promote", description="Promote a user to a higher rank (Command only)")
    @discord.app_commands.describe(
        user="User to promote",
        new_rank="New rank"
    )
    @discord.app_commands.choices(new_rank=[
        discord.app_commands.Choice(name="Student", value="Student"),
        discord.app_commands.Choice(name="Trainer", value="Trainer"),
        discord.app_commands.Choice(name="Command", value="Command")
    ])
    async def promote(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        new_rank: str
    ):
        """Promote a user to a higher rank"""
        try:
            promoter_rank = self.get_user_rank(interaction.user.id)
            target_rank = self.get_user_rank(user.id)
            
            # Check permissions
            if not self.can_promote(promoter_rank, target_rank, new_rank):
                await interaction.response.send_message("❌ You don't have permission to make this promotion.")
                return
            
            # Update user rank
            if str(user.id) not in self.users:
                self.users[str(user.id)] = {}
            
            old_rank = self.users[str(user.id)].get('rank', 'Student')
            self.users[str(user.id)]['rank'] = new_rank
            self.users[str(user.id)]['promoted_by'] = str(interaction.user.id)
            self.users[str(user.id)]['promoted_at'] = datetime.utcnow().isoformat()
            
            await self.save_users()
            
            embed = discord.Embed(
                title="🎖️ Rank Promotion",
                description=f"**{user.display_name}** has been promoted!",
                color=self.rank_colors.get(new_rank, 0x3498db)
            )
            embed.add_field(name="Previous Rank", value=old_rank, inline=True)
            embed.add_field(name="New Rank", value=new_rank, inline=True)
            embed.add_field(name="Promoted By", value=interaction.user.display_name, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in promote command: {e}")
            await interaction.response.send_message("❌ An error occurred during promotion.")

    @discord.app_commands.command(name="demote", description="Demote a user to a lower rank (Command only)")
    @discord.app_commands.describe(
        user="User to demote",
        new_rank="New rank"
    )
    @discord.app_commands.choices(new_rank=[
        discord.app_commands.Choice(name="Student", value="Student"),
        discord.app_commands.Choice(name="Trainer", value="Trainer")
    ])
    async def demote(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        new_rank: str
    ):
        """Demote a user to a lower rank"""
        try:
            promoter_rank = self.get_user_rank(interaction.user.id)
            
            # Only Command can demote
            if self.rank_hierarchy.get(promoter_rank, 0) < 3:
                await interaction.response.send_message("❌ You need Command rank to demote users.")
                return
            
            # Update user rank
            if str(user.id) not in self.users:
                self.users[str(user.id)] = {}
            
            old_rank = self.users[str(user.id)].get('rank', 'Student')
            self.users[str(user.id)]['rank'] = new_rank
            self.users[str(user.id)]['demoted_by'] = str(interaction.user.id)
            self.users[str(user.id)]['demoted_at'] = datetime.utcnow().isoformat()
            
            await self.save_users()
            
            embed = discord.Embed(
                title="⬇️ Rank Demotion",
                description=f"**{user.display_name}** has been demoted",
                color=0xffa500
            )
            embed.add_field(name="Previous Rank", value=old_rank, inline=True)
            embed.add_field(name="New Rank", value=new_rank, inline=True)
            embed.add_field(name="Demoted By", value=interaction.user.display_name, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in demote command: {e}")
            await interaction.response.send_message("❌ An error occurred during demotion.")

    @commands.command(name="rank")
    async def check_rank(self, ctx, user: str = None):
        """Check user's current rank"""
        try:
            if user is None:
                target_user = ctx.author
            else:
                # Find user by name or mention
                target_user = None
                for member in ctx.guild.members:
                    if user.lower() in member.display_name.lower() or user in str(member):
                        target_user = member
                        break
                
                if not target_user:
                    await ctx.send(f"❌ User '{user}' not found.")
                    return
            
            rank = self.get_user_rank(target_user.id)
            
            embed = discord.Embed(
                title="🎖️ Rank Information",
                description=f"Rank details for **{target_user.display_name}**",
                color=self.rank_colors.get(rank, 0x3498db)
            )
            embed.add_field(name="Current Rank", value=rank, inline=True)
            embed.add_field(name="Level", value=self.rank_hierarchy.get(rank, 1), inline=True)
            
            # Add rank description
            descriptions = {
                "Student": "Learning EMS procedures and flight operations",
                "Trainer": "Qualified to train students and access advanced features", 
                "Command": "Full administrative access and leadership responsibilities"
            }
            embed.add_field(name="Description", value=descriptions.get(rank, "Unknown rank"), inline=False)
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in check_rank command: {e}")
            await ctx.send("❌ An error occurred while checking rank.")

    @commands.command(name="ranks")
    async def view_ranks(self, ctx):
        """Display all available ranks and their information"""
        try:
            embed = discord.Embed(
                title="🎖️ EMS Training Ranks",
                description="Available ranks in the EMS Training program",
                color=0x3498db
            )
            
            embed.add_field(
                name="👨‍🎓 Student",
                value="**Level:** 1\n"
                      "**Access:** Basic commands, training materials\n"
                      "**Description:** Learning EMS procedures and flight operations\n"
                      "**Color:** Blue",
                inline=False
            )
            
            embed.add_field(
                name="👨‍🏫 Trainer", 
                value="**Level:** 2\n"
                      "**Access:** Upload documents, schedule reminders, advanced features\n"
                      "**Description:** Qualified to train students and access trainer tools\n"
                      "**Color:** Orange",
                inline=False
            )
            
            embed.add_field(
                name="👨‍✈️ Command",
                value="**Level:** 3\n"
                      "**Access:** Full administrative control, promote/demote users\n"
                      "**Description:** Leadership role with complete system access\n" 
                      "**Color:** Red",
                inline=False
            )
            
            embed.set_footer(text="Contact Command staff for rank promotions")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in view_ranks command: {e}")
            await ctx.send("❌ An error occurred while loading ranks.")

    @commands.command(name="staff")
    async def view_staff(self, ctx):
        """Display current staff members"""
        try:
            # Get all users with Trainer+ ranks
            trainers = []
            command = []
            
            for user_id, user_data in self.users.items():
                rank = user_data.get('rank', 'Student')
                if rank == 'Trainer':
                    # Try to get member from guild
                    member = ctx.guild.get_member(int(user_id))
                    if member:
                        trainers.append(member.display_name)
                elif rank == 'Command':
                    member = ctx.guild.get_member(int(user_id))
                    if member:
                        command.append(member.display_name)
            
            embed = discord.Embed(
                title="👥 EMS Training Staff",
                description="Current training staff members",
                color=0x3498db
            )
            
            if command:
                embed.add_field(
                    name="👨‍✈️ Command Staff",
                    value="\n".join(command) or "None",
                    inline=False
                )
            
            if trainers:
                embed.add_field(
                    name="👨‍🏫 Trainers",
                    value="\n".join(trainers) or "None", 
                    inline=False
                )
            
            if not command and not trainers:
                embed.add_field(
                    name="ℹ️ No Staff Found",
                    value="No users currently have Trainer or Command ranks.",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in view_staff command: {e}")
            await ctx.send("❌ An error occurred while loading staff.")

async def setup(bot):
    await bot.add_cog(RanksCog(bot))