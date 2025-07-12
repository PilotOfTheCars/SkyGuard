import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
# Only enable message content intent if we have proper permissions
# intents.message_content = True

class EMSBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
    async def setup_hook(self):
        """Load all cogs when bot starts"""
        try:
            # Ensure data directory exists
            Path('data').mkdir(exist_ok=True)
            
            # Load cogs
            cogs = [
                'cogs.alerts',
                'cogs.help_system',
                'cogs.simple_commands'
                # Temporarily disabled until syntax fixes:
                # 'cogs.documents',
                # 'cogs.missions', 
                # 'cogs.reminders',
                # 'cogs.ranks'
            ]
            
            for cog in cogs:
                try:
                    await self.load_extension(cog)
                    logger.info(f"Loaded cog: {cog}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog}: {e}")
                    
            # Sync slash commands
            await self.tree.sync()
            logger.info("Slash commands synced")
            
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="EMS flights | /help"
        )
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("❌ An error occurred while processing your command.")

# Initialize and run bot
async def main():
    """Main function to run the bot"""
    bot = EMSBot()
    
    try:
        # Import keep_alive to start Flask server
        from keep_alive import keep_alive
        keep_alive()
        
        # Start the bot
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error("DISCORD_TOKEN not found in environment variables")
            return
            
        await bot.start(token)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
