import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.documents = []
        self.rank_hierarchy = {
            "Student": 1,
            "Trainer": 2, 
            "Command": 3
        }
        self.load_documents()
        
    def load_documents(self):
        """Load documents database"""
        try:
            docs_file = Path('data/documents.json')
            if docs_file.exists():
                with open(docs_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            else:
                self.documents = []
                self.save_documents()
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.documents = []
    
    async def save_documents(self):
        """Save documents database"""
        try:
            Path('data').mkdir(exist_ok=True)
            with open('data/documents.json', 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
    
    def get_user_rank(self, user):
        """Get user's rank from roles"""
        # Check for rank roles
        role_names = [role.name.lower() for role in user.roles]
        
        if any(name in role_names for name in ['command', 'commander', 'chief']):
            return "Command"
        elif any(name in role_names for name in ['trainer', 'instructor', 'teacher']):
            return "Trainer"
        else:
            return "Student"
    
    def can_access_document(self, user_rank, doc_visibility):
        """Check if user can access document based on rank"""
        user_level = self.rank_hierarchy.get(user_rank, 1)
        doc_level = self.rank_hierarchy.get(doc_visibility, 1)
        return user_level >= doc_level

    @discord.app_commands.command(name="docs", description="Display available training documents")
    @discord.app_commands.describe(search="Search for specific documents")
    async def docs(self, interaction: discord.Interaction, search: str = None):
        """Display available documents based on user rank"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Filter documents by access level
            accessible_docs = []
            for doc in self.documents:
                if self.can_access_document(user_rank, doc.get('visibility', 'Student')):
                    if search is None or search.lower() in doc['name'].lower() or search.lower() in doc.get('description', '').lower():
                        accessible_docs.append(doc)
            
            if not accessible_docs:
                embed = discord.Embed(
                    title="📁 No Documents Found",
                    description="No documents available for your access level" + (f" matching '{search}'" if search else ""),
                    color=0xffa500
                )
            else:
                embed = discord.Embed(
                    title="📚 Training Documents",
                    description=f"Available documents for **{user_rank}** rank" + (f" | Search: '{search}'" if search else ""),
                    color=0x3498db
                )
                
                # Group by category
                categories = {}
                for doc in accessible_docs[:10]:  # Limit to 10 docs
                    category = doc.get('category', 'General')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(doc)
                
                for category, docs in categories.items():
                    doc_list = ""
                    for doc in docs:
                        doc_list += f"**{doc['name']}** ({doc.get('visibility', 'Student')})\n"
                        doc_list += f"└ {doc.get('description', 'No description')}\n"
                        if doc.get('url'):
                            doc_list += f"└ [View Document]({doc['url']})\n"
                        doc_list += "\n"
                    
                    embed.add_field(
                        name=f"📖 {category}",
                        value=doc_list[:1000] + ("..." if len(doc_list) > 1000 else ""),
                        inline=False
                    )
            
            embed.add_field(
                name="ℹ️ Your Access Level",
                value=f"**{user_rank}** - You can access {user_rank} and lower level documents",
                inline=False
            )
            
            embed.set_footer(text="Use /upload_doc to add new documents (Trainer+ only)")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in docs command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading documents.")

    @discord.app_commands.command(name="upload_doc", description="Upload a new training document (Trainer+ only)")
    @discord.app_commands.describe(
        name="Document name",
        description="Document description", 
        visibility="Who can access this document",
        category="Document category",
        url="Document URL or file link"
    )
    @discord.app_commands.choices(visibility=[
        discord.app_commands.Choice(name="Student", value="Student"),
        discord.app_commands.Choice(name="Trainer", value="Trainer"),
        discord.app_commands.Choice(name="Command", value="Command")
    ])
    async def upload_doc(
        self,
        interaction: discord.Interaction,
        name: str,
        description: str,
        visibility: str,
        category: str = "General",
        url: str = None
    ):
        """Upload a new training document"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Check permissions (Trainer+ only)
            if self.rank_hierarchy.get(user_rank, 0) < 2:
                await interaction.response.send_message("❌ You need Trainer rank or higher to upload documents.")
                return
            
            # Check if document name already exists
            existing_doc = next((doc for doc in self.documents if doc['name'].lower() == name.lower()), None)
            if existing_doc:
                await interaction.response.send_message(f"❌ A document named '{name}' already exists.")
                return
            
            # Create document entry
            document = {
                'id': len(self.documents) + 1,
                'name': name,
                'description': description,
                'visibility': visibility,
                'category': category,
                'url': url,
                'uploaded_by': str(interaction.user.id),
                'uploaded_at': datetime.utcnow().isoformat(),
                'file_path': None
            }
            
            self.documents.append(document)
            await self.save_documents()
            
            embed = discord.Embed(
                title="✅ Document Uploaded",
                description=f"Successfully uploaded **{name}**",
                color=0x00ff00
            )
            embed.add_field(name="Category", value=category, inline=True)
            embed.add_field(name="Visibility", value=visibility, inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            if url:
                embed.add_field(name="URL", value=url, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in upload_doc command: {e}")
            await interaction.response.send_message("❌ An error occurred while uploading the document.")

    @commands.command(name="remove_doc")
    async def remove_doc(self, ctx, doc_id: str):
        """Remove a training document"""
        try:
            user_rank = self.get_user_rank(ctx.author)
            
            # Check permissions (Trainer+ only)
            if self.rank_hierarchy.get(user_rank, 0) < 2:
                await ctx.send("❌ You need Trainer rank or higher to remove documents.")
                return
            
            # Find document
            doc_to_remove = None
            for i, doc in enumerate(self.documents):
                if str(doc['id']) == doc_id or doc['name'].lower() == doc_id.lower():
                    doc_to_remove = (i, doc)
                    break
            
            if not doc_to_remove:
                await ctx.send(f"❌ Document '{doc_id}' not found.")
                return
            
            index, doc = doc_to_remove
            self.documents.pop(index)
            await self.save_documents()
            
            await ctx.send(f"✅ Removed document: **{doc['name']}**")
            
        except Exception as e:
            logger.error(f"Error in remove_doc command: {e}")
            await ctx.send("❌ An error occurred while removing the document.")

    @commands.command(name="doc_categories")
    async def doc_categories(self, ctx):
        """Display available document categories"""
        try:
            if not self.documents:
                await ctx.send("📁 No documents available.")
                return
            
            categories = {}
            for doc in self.documents:
                category = doc.get('category', 'General')
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            embed = discord.Embed(
                title="📂 Document Categories",
                description="Available document categories",
                color=0x3498db
            )
            
            for category, count in categories.items():
                embed.add_field(
                    name=f"📖 {category}",
                    value=f"{count} document(s)",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in doc_categories command: {e}")
            await ctx.send("❌ An error occurred while loading categories.")

async def setup(bot):
    await bot.add_cog(DocumentsCog(bot))