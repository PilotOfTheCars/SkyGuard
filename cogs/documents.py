import discord
from discord.ext import commands
import json
import logging
from pathlib import Path
import aiofiles
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.documents_file = Path('data/documents.json')
        self.documents = self.load_documents()
        
        # Rank hierarchy for access control
        self.rank_hierarchy = {
            'Student': 1,
            'Trainer': 2, 
            'Command': 3
        }
        
    def load_documents(self):
        """Load documents database"""
        try:
            if self.documents_file.exists():
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
    
    async def save_documents(self):
        """Save documents database"""
        try:
            async with aiofiles.open(self.documents_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self.documents, indent=2))
        except Exception as e:
            logger.error(f"Error saving documents: {e}")

    def get_user_rank(self, user):
        """Get user's rank from roles"""
        # Load user data to get rank
        try:
            users_file = Path('data/users.json')
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                    user_data = users_data.get(str(user.id), {})
                    return user_data.get('rank', 'Student')
        except:
            pass
        
        # Fallback to role-based detection
        if user.guild_permissions.administrator:
            return 'Command'
        
        role_names = [role.name.lower() for role in user.roles]
        if 'command' in role_names:
            return 'Command'
        elif 'trainer' in role_names:
            return 'Trainer'
        else:
            return 'Student'

    def can_access_document(self, user_rank, doc_visibility):
        """Check if user can access document based on rank"""
        user_level = self.rank_hierarchy.get(user_rank, 0)
        required_level = self.rank_hierarchy.get(doc_visibility, 1)
        return user_level >= required_level

    @discord.app_commands.command(name="docs", description="View available training documents")
    @discord.app_commands.describe(search="Search documents by keyword")
    async def docs(
        self,
        interaction: discord.Interaction,
        search: str = None
    ):
        """Display available documents based on user rank"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Filter documents by access level
            accessible_docs = []
            for doc in self.documents:
                if self.can_access_document(user_rank, doc.get('visibility', 'Student')):
                    if not search or search.lower() in doc.get('name', '').lower() or search.lower() in doc.get('description', '').lower():
                        accessible_docs.append(doc)
            
            if not accessible_docs:
                embed = discord.Embed(
                    title="📁 No Documents Available",
                    description="No documents found matching your search or access level.",
                    color=0xffa500
                )
                if search:
                    embed.add_field(
                        name="🔍 Search Term", 
                        value=f"`{search}`", 
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="📚 Training Documents",
                    description=f"Documents available for rank: **{user_rank}**",
                    color=0x3498db
                )
                
                if search:
                    embed.description += f"\nSearch: `{search}`"
                
                # Group documents by category
                categories = {}
                for doc in accessible_docs:
                    category = doc.get('category', 'General')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(doc)
                
                for category, docs in categories.items():
                    doc_list = ""
                    for doc in docs[:5]:  # Limit to 5 docs per category
                        doc_list += f"📄 **{doc['name']}**\n"
                        doc_list += f"   *{doc.get('description', 'No description')}*\n"
                        doc_list += f"   📊 {doc.get('visibility', 'Student')} level\n\n"
                    
                    embed.add_field(
                        name=f"📂 {category}",
                        value=doc_list.strip(),
                        inline=False
                    )
            
            embed.add_field(
                name="ℹ️ Your Access Level",
                value=f"**{user_rank}** - You can access {user_rank}, and lower level documents",
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
            
            # Handle file attachment
            if ctx.message and ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                
                # Create uploads directory
                uploads_dir = Path('uploads')
                uploads_dir.mkdir(exist_ok=True)
                
                # Save file
                file_path = uploads_dir / f"{document['id']}_{attachment.filename}"
                await attachment.save(file_path)
                document['file_path'] = str(file_path)
            
            # Add to documents list
            self.documents.append(document)
            await self.save_documents()
            
            embed = discord.Embed(
                title="✅ Document Uploaded Successfully",
                description=f"Document **{name}** has been added to the training library.",
                color=0x00ff00
            )
            
            embed.add_field(name="📄 Name", value=name, inline=True)
            embed.add_field(name="📊 Visibility", value=visibility, inline=True)
            embed.add_field(name="📂 Category", value=category, inline=True)
            embed.add_field(name="📝 Description", value=description, inline=False)
            
            if url:
                embed.add_field(name="🔗 URL", value=url, inline=False)
            
            embed.set_footer(text=f"Uploaded by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Document '{name}' uploaded by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in upload_doc command: {e}")
            await interaction.response.send_message("❌ An error occurred while uploading the document.")

    @discord.app_commands.command(name="remove_doc", description="Remove a training document (Command only)")
    async def remove_doc(
        self,
        ctx,
        doc_id: str
    ):
        """Remove a training document"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Check permissions (Command only)
            if self.rank_hierarchy.get(user_rank, 0) < 3:
                await interaction.response.send_message("❌ You need Command rank to remove documents.")
                return
            
            # Find document
            doc_index = None
            for i, doc in enumerate(self.documents):
                if doc['id'] == doc_id:
                    doc_index = i
                    break
            
            if doc_index is None:
                await interaction.response.send_message(f"❌ Document with ID {doc_id} not found.")
                return
            
            # Remove file if it exists
            removed_doc = self.documents[doc_index]
            if removed_doc.get('file_path') and Path(removed_doc['file_path']).exists():
                try:
                    os.remove(removed_doc['file_path'])
                except:
                    pass
            
            # Remove from list
            self.documents.pop(doc_index)
            await self.save_documents()
            
            embed = discord.Embed(
                title="🗑️ Document Removed",
                description=f"Document **{removed_doc['name']}** has been removed from the library.",
                color=0xff6b6b
            )
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Document '{removed_doc['name']}' removed by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error in remove_doc command: {e}")
            await interaction.response.send_message("❌ An error occurred while removing the document.")

    @discord.app_commands.command(name="doc_categories", description="View document categories")
    @discord.app_commands.describe(name="Document name")
    async def doc_categories(self, ctx):
        """Display available document categories"""
        try:
            user_rank = self.get_user_rank(interaction.user)
            
            # Get accessible documents
            accessible_docs = [
                doc for doc in self.documents 
                if self.can_access_document(user_rank, doc.get('visibility', 'Student'))
            ]
            
            # Count documents by category
            categories = {}
            for doc in accessible_docs:
                category = doc.get('category', 'General')
                categories[category] = categories.get(category, 0) + 1
            
            if not categories:
                await interaction.response.send_message("📁 No document categories available for your rank.")
                return
            
            embed = discord.Embed(
                title="📂 Document Categories",
                description=f"Available categories for rank: **{user_rank}**",
                color=0x9b59b6
            )
            
            for category, count in sorted(categories.items()):
                embed.add_field(
                    name=f"📁 {category}",
                    value=f"{count} document{'s' if count != 1 else ''}",
                    inline=True
                )
            
            embed.set_footer(text="Use /docs search:<category> to filter by category")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in doc_categories command: {e}")
            await interaction.response.send_message("❌ An error occurred while loading categories.")

async def setup(bot):
    await bot.add_cog(DocumentsCog(bot))
