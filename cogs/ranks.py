import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class RanksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users_file = Path('data/users.json')
        self.users_data = self.load_users()
        
        # Rank hierarchy
        self.ranks = {
            'Student': {
                'level': 1,
                'color': 0x95a5a6,
                'permissions': ['basic_commands'],
                'description': 'Basic EMS trainee'
            },
            'Trainer': {
                'level': 2,
                'color': 0x3498db,
                'permissions': ['basic_commands', 'upload_docs', 'schedule_reminders', 'view_all_missions'],
                'description': 'Certified EMS instructor'
            },
            'Command': {
                'level': 3,
                'color': 0xe74c3c,
                'permissions': ['all'],
                'description': 'EMS command staff'
            }
        }
        
    def load_users(self):
        """Load users database"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return {}
    
    async def save_users(self):
        """Save users database"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def get_user_rank(self, user_id):
        """Get user's current rank"""
        user_data = self.users_data.get(str(user_id), {})
        return user_data.get('rank', 'Student')

    def can_promote(self, promoter_rank, target_rank, new_rank):
        """Check if user can promote another user"""
        promoter_level = self.ranks.get(promoter_rank, {}).get('level', 0)
        target_level = self.ranks.get(target_rank, {}).get('level', 0)
        new_level = self.ranks.get(new_rank, {}).get('level', 0)
        
        # Must be higher rank than target and new rank
        return promoter_level > target_level and promoter_level > new_level

    @discord.app_commands.command(name="promote", description="Promote a user to a higher rank (Command only)")
    async def promote(
        self,
        ctx,
        user: str,
        rank: str = 
            str,
            "New rank",
            choices=["Student", "Trainer", "Command"],
            required=True
        )
    ):
        """Promote a user to a higher rank"""
        try:
            # Check if user is trying to promote themselves
            if user.id == interaction.user.id:
                await interaction.response.send_message("❌ You cannot promote yourself.")
                return
            
            # Get current ranks
            promoter_rank = self.get_user_rank(interaction.user.id)
            current_rank = self.get_user_rank(user.id)
            
            # Check permissions
            if not self.can_promote(promoter_rank, current_rank, rank):
                await interaction.response.send_message("❌ You don't have permission to make this promotion.")
                return
            
            # Check if already at that rank
            if current_rank == rank:
                await interaction.response.send_message(f"❌ {user.display_name} is already at {rank} rank.")
                return
            
            # Check if this is actually a promotion
            current_level = self.ranks.get(current_rank, {}).get('level', 0)
            new_level = self.ranks.get(rank, {}).get('level', 0)
            
            if new_level <= current_level:
                await interaction.response.send_message("❌ Use `/demote` to lower someone's rank.")
                return
            
            # Update user data
            user_id = str(user.id)
            if user_id not in self.users_data:
                self.users_data[user_id] = {}
            
            self.users_data[user_id].update({
                'rank': rank,
                'promoted_by': str(interaction.user.id),
                'promoted_at': datetime.now(timezone.utc).isoformat(),
                'previous_rank': current_rank
            })
            
            await self.save_users()
            
            # Create promotion embed
            rank_info = self.ranks[rank]
            embed = discord.Embed(
                title="🎖️ Promotion Notification",
                description=f"**{user.display_name}** has been promoted!",
                color=rank_info['color'],
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="👤 User", value=user.mention, inline=True)
            embed.add_field(name="📈 Previous Rank", value=current_rank, inline=True)
            embed.add_field(name="🎯 New Rank", value=rank, inline=True)
            embed.add_field(name="📋 Description", value=rank_info['description'], inline=False)
            embed.add_field(name="👨‍💼 Promoted By", value=interaction.user.display_name, inline=True)
            
            # Add permissions info
            permissions = rank_info.get('permissions', [])
            if permissions:
                perm_text = "• " + "\n• ".join(permissions) if permissions != ['all'] else "• All permissions"
                embed.add_field(name="🔑 New Permissions", value=perm_text, inline=False)
            
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="Congratulations on your promotion!")
            
            await interaction.response.send_message(embed=embed)
            
            # Send DM to promoted user
            try:
                dm_embed = discord.Embed(
                    title="🎉 Congratulations!",
                    description=f"You have been promoted to **{rank}** rank in {interaction.guild.name}!",
                    color=rank_info['color']
                )
                dm_embed.add_field(name="New Rank", value=rank, inline=True)
                dm_embed.add_field(name="Promoted By", value=interaction.user.display_name, inline=True)
                await user.send(embed=dm_embed)
            except:
                pass  # Ignore if can't send DM
            
            logger.info(f"{user.display_name} promoted to {rank} by {interaction.user.display_name}")
            
        except Exception as e:
            logger.error(f"Error in promote command: {e}")
            await interaction.response.send_message("❌ An error occurred while processing the promotion.")

    @discord.app_commands.command(name="demote", description="Demote a user to a lower rank (Command only)")
    async def demote(
        self,
        ctx,
        user: str,
        rank: str = 
            str,
            "New rank",
            choices=["Student", "Trainer"],
            required=True
        ),
        reason: str = None
    ):
        """Demote a user to a lower rank"""
        try:
            # Check if user is trying to demote themselves
            if user.id == interaction.user.id:
                await interaction.response.send_message("❌ You cannot demote yourself.")
                return
            
            # Get current ranks
            demoter_rank = self.get_user_rank(interaction.user.id)
            current_rank = self.get_user_rank(user.id)
            
            # Check permissions (only Command can demote)
            if demoter_rank != 'Command':
                await interaction.response.send_message("❌ Only Command rank can demote users.")
                return
            
            # Check if already at that rank
            if current_rank == rank:
                await interaction.response.send_message(f"❌ {user.display_name} is already at {rank} rank.")
                return
            
            # Check if this is actually a demotion
            current_level = self.ranks.get(current_rank, {}).get('level', 0)
            new_level = self.ranks.get(rank, {}).get('level', 0)
            
            if new_level >= current_level:
                await interaction.response.send_message("❌ Use `/promote` to raise someone's rank.")
                return
            
            # Update user data
            user_id = str(user.id)
            if user_id not in self.users_data:
                self.users_data[user_id] = {}
            
            self.users_data[user_id].update({
                'rank': rank,
                'demoted_by': str(interaction.user.id),
                'demoted_at': datetime.now(timezone.utc).isoformat(),
                'previous_rank': current_rank,
                'demotion_reason': reason
            })
            
            await self.save_users()
            
            # Create demotion embed
            rank_info = self.ranks[rank]
            embed = discord.Embed(
                title="📉 Rank Change Notification",
                description=f"**{user.display_name}** has been demoted.",
                color=0xff6b6b,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="👤 User", value=user.mention, inline=True)
            embed.add_field(name="📉 Previous Rank", value=current_rank, inline=True)
            embed.add_field(name="🎯 New Rank", value=rank, inline=True)
            
            if reason:
                embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            embed.add_field(name="👨‍💼 Demoted By", value=interaction.user.display_name, inline=True)
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            # Send DM to demoted user
            try:
                dm_embed = discord.Embed(
                    title="📉 Rank Change Notice",
                    description=f"Your rank has been changed to **{rank}** in {interaction.guild.name}.",
                    color=0xff6b6b
                )
                dm_embed.add_field(name="New Rank", value=rank, inline=True)
                if reason:
                    dm_embed.add_field(name="Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except:
                pass  # Ignore if can't send DM
            
            logger.info(f"{user.display_name} demoted to {rank} by {interaction.user.display_name}")
            
        except Exception as e:
            logger.error(f"Error in demote command: {e}")
            await interaction.response.send_message("❌ An error occurred while processing the demotion.")

    @discord.app_commands.command(name="rank", description="Check your or another user's rank")
    @discord.app_commands.describe(user="User to promote")
    async def check_rank(
        self,
        ctx,
        user: str = None
    ):
        """Check user's current rank"""
        try:
            target_user = user if user else interaction.user
            user_rank = self.get_user_rank(target_user.id)
            rank_info = self.ranks.get(user_rank, {})
            
            embed = discord.Embed(
                title=f"🎖️ Rank Information",
                description=f"Rank details for **{target_user.display_name}**",
                color=rank_info.get('color', 0x95a5a6),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="👤 User", value=target_user.mention, inline=True)
            embed.add_field(name="🎯 Current Rank", value=user_rank, inline=True)
            embed.add_field(name="📊 Level", value=str(rank_info.get('level', 1)), inline=True)
            embed.add_field(name="📋 Description", value=rank_info.get('description', 'No description'), inline=False)
            
            # Show permissions
            permissions = rank_info.get('permissions', [])
            if permissions:
                perm_text = "• " + "\n• ".join(permissions) if permissions != ['all'] else "• All permissions"
                embed.add_field(name="🔑 Permissions", value=perm_text, inline=False)
            
            # Show promotion history if available
            user_data = self.users_data.get(str(target_user.id), {})
            if 'promoted_at' in user_data:
                promoted_at = datetime.fromisoformat(user_data['promoted_at'])
                promoter = self.bot.get_user(int(user_data.get('promoted_by', 0)))
                promoter_name = promoter.display_name if promoter else "Unknown"
                
                embed.add_field(
                    name="📈 Last Promotion",
                    value=f"<t:{int(promoted_at.timestamp())}:R> by {promoter_name}",
                    inline=False
                )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in check_rank command: {e}")
            await interaction.response.send_message("❌ An error occurred while checking rank.")

    @discord.app_commands.command(name="ranks", description="View all available ranks")
    @discord.app_commands.describe(user="User to promote")
    async def view_ranks(self, ctx):
        """Display all available ranks and their information"""
        try:
            embed = discord.Embed(
                title="🎖️ EMS Training Ranks",
                description="Available ranks and their permissions",
                color=0x3498db
            )
            
            for rank_name, rank_info in self.ranks.items():
                permissions = rank_info.get('permissions', [])
                perm_text = "• " + "\n• ".join(permissions) if permissions != ['all'] else "• All permissions"
                
                field_value = f"**Level:** {rank_info['level']}\n"
                field_value += f"**Description:** {rank_info['description']}\n"
                field_value += f"**Permissions:**\n{perm_text}"
                
                embed.add_field(
                    name=f"{rank_name} Rank",
                    value=field_value,
                    inline=False
                )
            
            # Count users by rank
            rank_counts = {}
            for user_data in self.users_data.values():
                rank = user_data.get('rank', 'Student')
                rank_counts[rank] = rank_counts.get(rank, 0) + 1
            
            if rank_counts:
                counts_text = "\n".join([f"• {rank}: {count} user{'s' if count != 1 else ''}" 
                                       for rank, count in sorted(rank_counts.items())])
                embed.add_field(name="👥 Current Distribution", value=counts_text, inline=False)
            
            embed.set_footer(text="Contact Command staff for rank changes")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in view_ranks command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading ranks.")

    @discord.app_commands.command(name="staff", description="View current staff members")
    @discord.app_commands.describe(user="User to promote")
    async def view_staff(self, ctx):
        """Display current staff members"""
        try:
            embed = discord.Embed(
                title="👨‍💼 EMS Training Staff",
                description="Current trainers and command staff",
                color=0xe74c3c
            )
            
            # Group users by rank
            staff_by_rank = {'Command': [], 'Trainer': []}
            
            for user_id, user_data in self.users_data.items():
                rank = user_data.get('rank', 'Student')
                if rank in ['Command', 'Trainer']:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        staff_by_rank[rank].append(user)
            
            # Add Command staff
            if staff_by_rank['Command']:
                command_list = "\n".join([f"• {user.display_name}" for user in staff_by_rank['Command']])
                embed.add_field(name="🔴 Command Staff", value=command_list, inline=False)
            
            # Add Trainers
            if staff_by_rank['Trainer']:
                trainer_list = "\n".join([f"• {user.display_name}" for user in staff_by_rank['Trainer']])
                embed.add_field(name="🔵 Trainers", value=trainer_list, inline=False)
            
            if not staff_by_rank['Command'] and not staff_by_rank['Trainer']:
                embed.description = "No staff members found."
            
            embed.set_footer(text="Contact staff for assistance with training")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in view_staff command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading staff.")

async def setup(bot):
    await bot.add_cog(RanksCog(bot))
