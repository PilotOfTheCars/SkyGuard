import discord
from discord.ext import commands
import json
import re
import asyncio
import logging
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class AlertsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emergency_keywords = [
            'mayday', 'engine failure', 'crash', 'emergency landing',
            'fuel emergency', 'engine failure', 'instrument failure',
            'medical emergency', 'pan-pan', 'emergency descent',
            'lost comms', 'hydraulic failure', 'fire', 'emergency'
        ]
        
    async def get_nearest_airports(self, lat, lon, limit=3):
        """Get nearest airports to given coordinates"""
        try:
            # Mock airport data - in production, use a real airport database API
            airports = [
                {
                    'name': 'Primary Regional Airport',
                    'distance': '12.3 NM',
                    'runways': '09/27 (8000ft), 15/33 (6500ft)'
                },
                {
                    'name': 'Secondary Municipal',  
                    'distance': '18.7 NM',
                    'runways': '12/30 (5000ft)'
                },
                {
                    'name': 'Emergency Strip',
                    'distance': '25.1 NM', 
                    'runways': '05/23 (3500ft)'
                }
            ]
            return airports[:limit]
        except Exception as e:
            logger.error(f"Error fetching airports: {e}")
            return []

    def create_geofs_link(self, lat=None, lon=None):
        """Create GeoFS map link"""
        base_url = "https://www.geo-fs.com/geofs.php?v=3.9"
        if lat and lon:
            return f"{base_url}&lat={lat}&lon={lon}&zoom=10"
        return base_url

    async def create_alert_embed(self, message, emergency_type):
        """Create emergency alert embed"""
        # Extract mock flight data - in production, integrate with actual flight tracking
        callsign = "EMS-001"
        geofs_id = "12345"
        airspace = "Regional Control"
        country = "United States"
        aircraft = "Cessna 172"
        coordinates = "40.7128°N, 74.0060°W"
        heading = "270°"
        altitude = "3,500 ft"
        airspeed = "85 kts"
        vertical_speed = "-500 ft/min"
        status = "EMERGENCY"
        
        # Get nearest airports
        airports = await self.get_nearest_airports(40.7128, -74.0060)
        
        embed = discord.Embed(
            title="🚨 EMERGENCY RESPONSE ALERT 🚨",
            description=f"**{emergency_type.upper()} DETECTED**",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="✈️ Aircraft Information",
            value=f"**Callsign:** {callsign}\n"
                  f"**GeoFS ID:** {geofs_id}\n"
                  f"**Aircraft:** {aircraft}",
            inline=True
        )
        
        embed.add_field(
            name="📍 Location & Status",
            value=f"**Airspace:** {airspace}\n"
                  f"**Country:** {country}\n"
                  f"**Status:** {status}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Flight Data",
            value=f"**Coordinates:** {coordinates}\n"
                  f"**Heading:** {heading}\n"
                  f"**Altitude:** {altitude}\n"
                  f"**Airspeed:** {airspeed}\n"
                  f"**Vertical Speed:** {vertical_speed}",
            inline=False
        )
        
        # Add nearest airports
        if airports:
            airport_text = ""
            for i, airport in enumerate(airports, 1):
                airport_text += f"**{i}.** {airport['name']}\n"
                airport_text += f"   Distance: {airport['distance']}\n"
                airport_text += f"   Runways: {airport['runways']}\n\n"
            
            embed.add_field(
                name="🛬 Nearest Airports",
                value=airport_text.strip(),
                inline=False
            )
        
        # Add map link
        map_link = self.create_geofs_link(40.7128, -74.0060)
        embed.add_field(
            name="🗺️ GeoFS Map",
            value=f"[**Click here to view on GeoFS map**]({map_link})",
            inline=False
        )
        
        embed.add_field(
            name="📨 Alert Trigger",
            value=f"**Source:** Discord Message\n**Content:** ```{message.content[:400]}```",
            inline=False
        )
        
        embed.set_footer(text="EMS Training Bot | Emergency Response System")
        
        return embed

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for emergency keywords in messages"""
        if message.author.bot:
            return
            
        content = message.content.lower()
        
        # Check for emergency keywords
        detected_emergency = None
        for keyword in self.emergency_keywords:
            if keyword in content:
                detected_emergency = keyword
                break
                
        if detected_emergency:
            try:
                # Create alert embed
                embed = await self.create_alert_embed(message, detected_emergency)
                
                # Send alert to the same channel
                alert_message = await message.channel.send(
                    content="@everyone 🚨 **EMERGENCY RESPONSE ALERT** 🚨",
                    embed=embed
                )
                
                # Add reaction to original message
                await message.add_reaction("🚨")
                
                # Pin the alert message
                try:
                    await alert_message.pin()
                except:
                    pass  # Ignore if can't pin
                    
                logger.info(f"Emergency alert triggered by {message.author} for keyword: {detected_emergency}")
                
            except Exception as e:
                logger.error(f"Error creating emergency alert: {e}")

    @commands.command(name="test_alert")
    @commands.has_permissions(administrator=True)
    async def test_alert(self, ctx, *, emergency_type="engine failure"):
        """Test the emergency alert system (Admin only)"""
        try:
            embed = await self.create_alert_embed(ctx.message, emergency_type)
            await ctx.send(
                content="🧪 **TEST ALERT** 🧪 (This is a test)",
                embed=embed
            )
        except Exception as e:
            await ctx.send(f"❌ Error creating test alert: {e}")

    @discord.app_commands.command(name="emergency_info", description="Get information about emergency procedures")
    async def emergency_info(self, interaction: discord.Interaction):
        """Provide emergency procedure information"""
        embed = discord.Embed(
            title="🚨 Emergency Procedures",
            description="Essential emergency response information for EMS flights",
            color=0xff6b6b
        )
        
        embed.add_field(
            name="📢 Emergency Declarations",
            value="• **MAYDAY** - Life-threatening emergency\n"
                  "• **PAN-PAN** - Urgent but not life-threatening\n"
                  "• Squawk 7700 for emergency\n"
                  "• Squawk 7600 for communication failure",
            inline=False
        )
        
        embed.add_field(
            name="🛬 Emergency Landing Priorities",
            value="1. Maintain aircraft control\n"
                  "2. Find suitable landing site\n"
                  "3. Communicate emergency to ATC\n"
                  "4. Execute emergency landing procedures",
            inline=False
        )
        
        embed.add_field(
            name="📞 Communication",
            value="• State nature of emergency clearly\n"
                  "• Provide position and intentions\n"
                  "• Request assistance as needed\n"
                  "• Maintain communication with ATC",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AlertsCog(bot))
