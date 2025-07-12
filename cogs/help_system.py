import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class HelpSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.knowledge_base = {}
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """Load EMS knowledge base from JSON file"""
        try:
            knowledge_file = Path('data/ems_knowledge.json')
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                logger.info(f"Loaded {len(self.knowledge_base)} knowledge entries")
            else:
                logger.warning("Knowledge base file not found")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")

    def search_knowledge(self, query):
        """Search the knowledge base for relevant information"""
        query_lower = query.lower()
        results = []
        query_words = query_lower.split()
        
        for category, topics in self.knowledge_base.items():
            for topic, content in topics.items():
                score = 0
                
                # Check exact keyword matches (high score)
                keywords = content.get('keywords', [])
                for keyword in keywords:
                    if keyword.lower() in query_lower:
                        score += 10
                    for word in query_words:
                        if word in keyword.lower():
                            score += 5
                
                # Check topic name matches
                if any(word in topic.lower() for word in query_words):
                    score += 8
                
                # Check description matches
                description = content.get('description', '').lower()
                for word in query_words:
                    if word in description:
                        score += 3
                
                # Check procedure text matches
                procedures = content.get('procedures', [])
                for procedure in procedures:
                    for word in query_words:
                        if word in procedure.lower():
                            score += 2
                
                if score > 0:
                    results.append({
                        'score': score,
                        'category': category,
                        'topic': topic,
                        'content': content
                    })
        
        # Sort by score and return top 3 results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:3]

    @discord.app_commands.command(name="ask_ems", description="Ask a question about EMS procedures")
    async def ask_ems(
        self, 
        interaction: discord.Interaction, 
        question: str
    ):
        """AI help system for EMS questions"""
        await interaction.response.defer()
        
        try:
            # Search knowledge base
            results = self.search_knowledge(question)
            
            if not results:
                embed = discord.Embed(
                    title="❓ No Results Found",
                    description=f"I couldn't find information about: **{question}**\n\n"
                               "Try rephrasing your question or use more specific terms.",
                    color=0xffa500
                )
                embed.add_field(
                    name="💡 Suggestions",
                    value="• Emergency procedures\n"
                          "• Landing techniques\n" 
                          "• Communication phraseology\n"
                          "• Flight operations\n"
                          "• Medical evacuation",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="🧠 EMS Knowledge Assistant",
                    description=f"Here's what I found about: **{question}**",
                    color=0x00ff00
                )
                
                for i, result in enumerate(results, 1):
                    content = result['content']
                    
                    field_value = content.get('description', 'No description available')
                    
                    # Add procedures if available
                    if 'procedures' in content:
                        field_value += "\n\n**Procedures:**\n"
                        for j, procedure in enumerate(content['procedures'], 1):
                            field_value += f"{j}. {procedure}\n"
                    
                    # Add tips if available
                    if 'tips' in content:
                        field_value += "\n**Tips:**\n"
                        for tip in content['tips']:
                            field_value += f"• {tip}\n"
                    
                    # Truncate if too long
                    if len(field_value) > 1000:
                        field_value = field_value[:997] + "..."
                    
                    embed.add_field(
                        name=f"{i}. {result['topic']} ({result['category']})",
                        value=field_value,
                        inline=False
                    )
            
            embed.set_footer(text="EMS Training Bot | Knowledge Base")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in ask_ems command: {e}")
            await interaction.followup.send("❌ An error occurred while searching the knowledge base.")

    @discord.app_commands.command(name="ems_topics", description="Browse available EMS knowledge topics")
    async def ems_topics(self, interaction: discord.Interaction):
        """List available knowledge base topics"""
        try:
            if not self.knowledge_base:
                await interaction.response.send_message("❌ Knowledge base is empty or not loaded.")
                return
                
            embed = discord.Embed(
                title="📚 Available EMS Topics",
                description="Browse through our comprehensive EMS knowledge base",
                color=0x3498db
            )
            
            for category, topics in self.knowledge_base.items():
                topic_list = "\n".join([f"• {topic}" for topic in topics.keys()])
                embed.add_field(
                    name=f"📖 {category.title()}",
                    value=topic_list[:1000] + ("..." if len(topic_list) > 1000 else ""),
                    inline=True
                )
            
            embed.set_footer(text="Use /ask_ems <question> to get detailed information")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in ems_topics command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading topics.")

    @discord.app_commands.command(name="emergency_guide", description="Quick emergency procedures guide")
    async def emergency_guide(self, interaction: discord.Interaction):
        """Provide quick emergency procedures guide"""
        embed = discord.Embed(
            title="🚨 Quick Emergency Guide",
            description="Essential emergency procedures for EMS flights",
            color=0xe74c3c
        )
        
        embed.add_field(
            name="🔥 Emergency Declarations",
            value="**MAYDAY MAYDAY MAYDAY**\n"
                  "• Life-threatening emergency\n"
                  "• Squawk 7700\n"
                  "• State nature, position, intentions\n\n"
                  "**PAN-PAN PAN-PAN PAN-PAN**\n"
                  "• Urgent situation\n"
                  "• Requires assistance but not immediate danger",
            inline=False
        )
        
        embed.add_field(
            name="🛬 Engine Failure",
            value="1. Maintain airspeed (best glide)\n"
                  "2. Find suitable landing area\n"
                  "3. Attempt restart if altitude permits\n"
                  "4. Declare emergency\n"
                  "5. Prepare for forced landing",
            inline=True
        )
        
        embed.add_field(
            name="🌩️ Weather Emergency",
            value="1. Request immediate vector around weather\n"
                  "2. Consider alternate airport\n"
                  "3. Maintain safe altitude\n"
                  "4. Use weather radar if available\n"
                  "5. Land at nearest suitable airport",
            inline=True
        )
        
        embed.add_field(
            name="📡 Communication Failure",
            value="1. Squawk 7600\n"
                  "2. Try different radio/frequency\n"
                  "3. Continue on last assigned route\n"
                  "4. Follow lost comms procedures\n"
                  "5. Announce intentions on guard frequency",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpSystemCog(bot))
