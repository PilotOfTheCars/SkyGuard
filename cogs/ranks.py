import discord from discord.ext import commands import json import logging from pathlib import Path from datetime import datetime

logger = logging.getLogger(name)

class RanksCog(commands.Cog): def init(self, bot): self.bot = bot self.users = {}

# Define rank structure
    self.rank_hierarchy = {
        "Student": 1,
        "Trainee": 2,
        "Certified Responder": 3,
        "Trainer": 4,
        "Senior Trainer": 5,
        "Command Support": 6,
        "Command Staff": 7,
        "Deputy Command": 8,
        "Acting Commander": 9,
        "Commander": 10,
        "Executive Commander": 11,
        "EMS CEO": 12
    }

    self.rank_colors = {
        "Student": 0x3498db,  # Blue
        "Trainee": 0x6ab04c,
        "Certified Responder": 0x2ecc71,
        "Trainer": 0xf39c12,  # Orange
        "Senior Trainer": 0xf1c40f,
        "Command Support": 0x1abc9c,
        "Command Staff": 0x9b59b6,
        "Deputy Command": 0x8e44ad,
        "Acting Commander": 0xe67e22,
        "Commander": 0xe74c3c,  # Red
        "Executive Commander": 0xc0392b,
        "EMS CEO": 0x000000  # Black
    }

    self.rank_tiers = {
        "Student": "Student Tier",
        "Trainee": "Student Tier",
        "Certified Responder": "Student Tier",
        "Trainer": "Trainer Tier",
        "Senior Trainer": "Trainer Tier",
        "Command Support": "Command Tier",
        "Command Staff": "Command Tier",
        "Deputy Command": "Command Tier",
        "Acting Commander": "Command Tier",
        "Commander": "Command Tier",
        "Executive Commander": "Command Tier",
        "EMS CEO": "Command Tier"
    }

    self.rank_descriptions = {
        "Student": "Basic participant in the EMS program",
        "Trainee": "Active learner undergoing training",
        "Certified Responder": "Completed basic EMS training",
        "Trainer": "Leads training sessions and supports students",
        "Senior Trainer": "Highly experienced trainer",
        "Command Support": "Assists command and manages logistics",
        "Command Staff": "Key decision-making personnel",
        "Deputy Command": "Second in command",
        "Acting Commander": "Temporary group leader",
        "Commander": "Official leader of the group",
        "Executive Commander": "Executive oversight of command tier",
        "EMS CEO": "Founder and overall head of the EMS Group"
    }

    self.load_users()

def load_users(self):
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
    try:
        Path('data').mkdir(exist_ok=True)
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

def get_user_rank(self, user_id):
    return self.users.get(str(user_id), {}).get('rank', 'Student')

def can_promote(self, promoter_rank, new_rank):
    return self.rank_hierarchy.get(promoter_rank, 0) >= 10 and self.rank_hierarchy.get(new_rank, 0) < self.rank_hierarchy.get(promoter_rank, 0)

@discord.app_commands.command(name="promote", description="Promote a user to a higher rank")
@discord.app_commands.describe(user="User to promote", new_rank="New rank")
async def promote(self, interaction: discord.Interaction, user: discord.Member, new_rank: str):
    try:
        promoter_rank = self.get_user_rank(interaction.user.id)
        if not self.can_promote(promoter_rank, new_rank):
            await interaction.response.send_message("❌ You don't have permission to promote to this rank.", ephemeral=True)
            return

        old_rank = self.get_user_rank(user.id)
        self.users[str(user.id)] = {
            "rank": new_rank,
            "promoted_by": str(interaction.user.id),
            "promoted_at": datetime.utcnow().isoformat()
        }
        await self.save_users()

        embed = discord.Embed(title="🎖️ Promotion", color=self.rank_colors.get(new_rank, 0x3498db))
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Old Rank", value=old_rank, inline=True)
        embed.add_field(name="New Rank", value=new_rank, inline=True)
        embed.set_footer(text=f"Promoted by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        logger.error(f"Promotion failed: {e}")
        await interaction.response.send_message("❌ Failed to promote user.", ephemeral=True)

@commands.command(name="rank")
async def check_rank(self, ctx, user: discord.Member = None):
    target = user or ctx.author
    rank = self.get_user_rank(target.id)

    embed = discord.Embed(
        title=f"🎖️ {target.display_name}'s Rank",
        color=self.rank_colors.get(rank, 0x3498db)
    )
    embed.add_field(name="Rank", value=rank, inline=True)
    embed.add_field(name="Level", value=self.rank_hierarchy.get(rank, '?'), inline=True)
    embed.add_field(name="Tier", value=self.rank_tiers.get(rank, "Unknown"), inline=False)
    embed.add_field(name="Description", value=self.rank_descriptions.get(rank, "No description."), inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)

    await ctx.send(embed=embed)

@commands.command(name="ranks")
async def view_ranks(self, ctx):
    embed = discord.Embed(
        title="📜 EMS Ranks",
        description="All ranks used in the EMS Training System",
        color=0x95a5a6
    )

    for rank in self.rank_hierarchy:
        embed.add_field(
            name=f"{rank} (Level {self.rank_hierarchy[rank]})",
            value=f"**Tier:** {self.rank_tiers[rank]}\n**Description:** {self.rank_descriptions[rank]}",
            inline=False
        )

    await ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(RanksCog(bot))

import discord from discord.ext import commands import json import logging from pathlib import Path from datetime import datetime

logger = logging.getLogger(name)

class RanksCog(commands.Cog): def init(self, bot): self.bot = bot self.users = {}

# Define rank structure
    self.rank_hierarchy = {
        "Student": 1,
        "Trainee": 2,
        "Certified Responder": 3,
        "Trainer": 4,
        "Senior Trainer": 5,
        "Command Support": 6,
        "Command Staff": 7,
        "Deputy Command": 8,
        "Acting Commander": 9,
        "Commander": 10,
        "Executive Commander": 11,
        "EMS CEO": 12
    }

    self.rank_colors = {
        "Student": 0x3498db,  # Blue
        "Trainee": 0x6ab04c,
        "Certified Responder": 0x2ecc71,
        "Trainer": 0xf39c12,  # Orange
        "Senior Trainer": 0xf1c40f,
        "Command Support": 0x1abc9c,
        "Command Staff": 0x9b59b6,
        "Deputy Command": 0x8e44ad,
        "Acting Commander": 0xe67e22,
        "Commander": 0xe74c3c,  # Red
        "Executive Commander": 0xc0392b,
        "EMS CEO": 0x000000  # Black
    }

    self.rank_tiers = {
        "Student": "Student Tier",
        "Trainee": "Student Tier",
        "Certified Responder": "Student Tier",
        "Trainer": "Trainer Tier",
        "Senior Trainer": "Trainer Tier",
        "Command Support": "Command Tier",
        "Command Staff": "Command Tier",
        "Deputy Command": "Command Tier",
        "Acting Commander": "Command Tier",
        "Commander": "Command Tier",
        "Executive Commander": "Command Tier",
        "EMS CEO": "Command Tier"
    }

    self.rank_descriptions = {
        "Student": "Basic participant in the EMS program",
        "Trainee": "Active learner undergoing training",
        "Certified Responder": "Completed basic EMS training",
        "Trainer": "Leads training sessions and supports students",
        "Senior Trainer": "Highly experienced trainer",
        "Command Support": "Assists command and manages logistics",
        "Command Staff": "Key decision-making personnel",
        "Deputy Command": "Second in command",
        "Acting Commander": "Temporary group leader",
        "Commander": "Official leader of the group",
        "Executive Commander": "Executive oversight of command tier",
        "EMS CEO": "Founder and overall head of the EMS Group"
    }

    self.load_users()

def load_users(self):
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
    try:
        Path('data').mkdir(exist_ok=True)
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

def get_user_rank(self, user_id):
    return self.users.get(str(user_id), {}).get('rank', 'Student')

def can_promote(self, promoter_rank, new_rank):
    return self.rank_hierarchy.get(promoter_rank, 0) >= 10 and self.rank_hierarchy.get(new_rank, 0) < self.rank_hierarchy.get(promoter_rank, 0)

@discord.app_commands.command(name="promote", description="Promote a user to a higher rank")
@discord.app_commands.describe(user="User to promote", new_rank="New rank")
async def promote(self, interaction: discord.Interaction, user: discord.Member, new_rank: str):
    try:
        promoter_rank = self.get_user_rank(interaction.user.id)
        if not self.can_promote(promoter_rank, new_rank):
            await interaction.response.send_message("❌ You don't have permission to promote to this rank.", ephemeral=True)
            return

        old_rank = self.get_user_rank(user.id)
        self.users[str(user.id)] = {
            "rank": new_rank,
            "promoted_by": str(interaction.user.id),
            "promoted_at": datetime.utcnow().isoformat()
        }
        await self.save_users()

        embed = discord.Embed(title="🎖️ Promotion", color=self.rank_colors.get(new_rank, 0x3498db))
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Old Rank", value=old_rank, inline=True)
        embed.add_field(name="New Rank", value=new_rank, inline=True)
        embed.set_footer(text=f"Promoted by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        logger.error(f"Promotion failed: {e}")
        await interaction.response.send_message("❌ Failed to promote user.", ephemeral=True)

@commands.command(name="rank")
async def check_rank(self, ctx, user: discord.Member = None):
    target = user or ctx.author
    rank = self.get_user_rank(target.id)

    embed = discord.Embed(
        title=f"🎖️ {target.display_name}'s Rank",
        color=self.rank_colors.get(rank, 0x3498db)
    )
    embed.add_field(name="Rank", value=rank, inline=True)
    embed.add_field(name="Level", value=self.rank_hierarchy.get(rank, '?'), inline=True)
    embed.add_field(name="Tier", value=self.rank_tiers.get(rank, "Unknown"), inline=False)
    embed.add_field(name="Description", value=self.rank_descriptions.get(rank, "No description."), inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)

    await ctx.send(embed=embed)

@commands.command(name="ranks")
async def view_ranks(self, ctx):
    embed = discord.Embed(
        title="📜 EMS Ranks",
        description="All ranks used in the EMS Training System",
        color=0x95a5a6
    )

    for rank in self.rank_hierarchy:
        embed.add_field(
            name=f"{rank} (Level {self.rank_hierarchy[rank]})",
            value=f"**Tier:** {self.rank_tiers[rank]}\n**Description:** {self.rank_descriptions[rank]}",
            inline=False
        )

    await ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(RanksCog(bot))
