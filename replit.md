# EMS Training Discord Bot

## Overview

This is a comprehensive Discord bot designed for Emergency Medical Services (EMS) flight training. The bot provides emergency alert detection, AI-powered help systems, document management, mission logging, scheduled reminders, and rank management features for EMS training programs.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Python-based Discord bot using discord.py library
- **Architecture Pattern**: Modular cog-based architecture with separate feature modules
- **Web Server**: Flask server for health monitoring and status display
- **Logging**: Comprehensive logging system with file and console output

### Data Storage
- **Primary Storage**: JSON file-based storage system
- **Data Files**: 
  - `documents.json` - Document management
  - `ems_knowledge.json` - Knowledge base for help system
  - `missions.json` - Mission logging data
  - `reminders.json` - Scheduled reminders
  - `users.json` - User rank and profile data

### Bot Framework
- **Discord.py**: Modern Python Discord API wrapper
- **Command System**: Hybrid prefix (`!`) and slash command support
- **Intents**: Message content and member intents enabled for full functionality

## Key Components

### 1. Alerts System (`cogs/alerts.py`)
- **Purpose**: Emergency alert detection and response coordination
- **Features**: 
  - Emergency keyword detection in messages
  - Nearest airport lookup functionality
  - GeoFS integration for flight simulation mapping
  - Real-time emergency response protocols

### 2. Help System (`cogs/help_system.py`)
- **Purpose**: AI-powered knowledge base for EMS procedures
- **Features**:
  - Searchable knowledge base with emergency procedures
  - Keyword-based content matching
  - Comprehensive EMS training materials
  - Interactive help commands

### 3. Document Management (`cogs/documents.py`)
- **Purpose**: Secure document sharing and management
- **Features**:
  - Rank-based access control (Student/Trainer/Command)
  - Document upload and retrieval system
  - Categorized document organization

### 4. Mission Logging (`cogs/missions.py`)
- **Purpose**: Flight mission tracking and logging
- **Features**:
  - Multiple mission types (Medical Evacuation, Search & Rescue, etc.)
  - Active mission tracking
  - Mission history and analytics
  - Training flight documentation

### 5. Rank Management (`cogs/ranks.py`)
- **Purpose**: User hierarchy and permissions management
- **Features**:
  - Three-tier rank system (Student/Trainer/Command)
  - Permission-based feature access
  - Role color coding and descriptions

### 6. Reminders System (`cogs/reminders.py`)
- **Purpose**: Scheduled notifications and training reminders
- **Features**:
  - Automated reminder scheduling
  - Training session notifications
  - Rank-based reminder permissions

### 7. Keep-Alive Service (`keep_alive.py`)
- **Purpose**: Health monitoring and uptime management
- **Features**:
  - Web dashboard showing bot status
  - Health check endpoint for monitoring
  - Service status visualization

## Data Flow

### User Interaction Flow
1. User sends command or message to Discord
2. Bot processes command through appropriate cog
3. Data validation and permission checks performed
4. JSON files updated if necessary
5. Response sent back to Discord channel

### Emergency Alert Flow
1. Message scanned for emergency keywords
2. Alert triggered if keywords detected
3. Nearest airports calculated and displayed
4. Emergency procedures retrieved from knowledge base
5. Response coordination initiated

### Knowledge Base Query Flow
1. User submits help query
2. Query processed against knowledge base
3. Relevant procedures and tips retrieved
4. Formatted response with actionable information
5. Follow-up options provided

## External Dependencies

### Required Python Packages
- `discord.py` - Discord API interaction
- `flask` - Web server for health monitoring
- `aiohttp` - Asynchronous HTTP requests
- `aiofiles` - Asynchronous file operations
- `python-dotenv` - Environment variable management

### Optional Integrations
- Airport database API (currently mocked)
- Weather services integration
- GeoFS flight simulator integration
- Real-time aircraft tracking services

## Deployment Strategy

### Environment Setup
- Requires Discord bot token in environment variables
- Data directory created automatically on startup
- JSON files initialized if not present

### Scalability Considerations
- File-based storage suitable for small to medium deployments
- Easy migration path to database systems (Postgres compatible)
- Modular cog system allows for easy feature additions

### Monitoring and Maintenance
- Built-in health check endpoint at `/health`
- Comprehensive logging to both file and console
- Web dashboard for service status monitoring
- Automatic data persistence for all user interactions

### Security Features
- Rank-based access control throughout system
- Permission validation for sensitive operations
- Secure file handling for document management
- Environment-based configuration for sensitive data

The architecture prioritizes reliability, maintainability, and extensibility while providing comprehensive EMS training functionality through Discord's platform.