# Beget Manager Bot

Telegram bot for managing domains and DNS records on Beget hosting through their API.

## Features

- 🌐 **Domain Management**: View and manage your Beget domains
- 📝 **Subdomain Management**: Create and delete subdomains
- 🔧 **DNS Records Management**: 
  - View all DNS records (A, AAAA, MX, TXT, CNAME, NS)
  - Add, modify, and delete A records
  - Add and delete TXT records
- 👥 **Access Control**: Admin-controlled user access system
- 📊 **Activity Logging**: Track all actions performed through the bot

## Prerequisites

- Docker and Docker Compose installed
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Beget hosting account with API access
- Your Telegram Chat ID

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd beget-manager
```

### 2. Create Configuration File

Copy the example environment file:

```bash
cp .env.example .env
```

### 3. Configure Environment Variables

Edit the `.env` file with your credentials:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here

# Beget API Credentials
BEGET_LOGIN=your_beget_login
BEGET_PASSWORD=your_beget_password

# Optional Settings
LOG_LEVEL=INFO
```

#### Getting Your Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the token provided by BotFather
5. Paste it into `TELEGRAM_BOT_TOKEN` in your `.env` file

#### Finding Your Chat ID

There are several ways to get your Telegram Chat ID:

**Method 1: Using @userinfobot**
1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Start the bot by clicking "Start" or sending `/start`
3. The bot will immediately respond with your user information, including your Chat ID
4. Copy the number shown as "Id" (it may be negative for groups)
5. Paste it into `ADMIN_CHAT_ID` in your `.env` file

**Method 2: Using @getidsbot**
1. In chrome go to `https://api.telegram.org/bot{our_bot_token}/getUpdates`
2. Start the bot
3. Update the browser tab page
4. Copy and paste "chat"."id" into your `.env` file

#### Beget API Credentials

1. Log in to your [Beget control panel](https://cp.beget.com/)
2. Use your Beget account login and password
3. These are the same credentials you use to access the Beget control panel

### 4. Deploy with Docker

Build and start the bot:

```bash
docker-compose up -d
```

Check if the bot is running:

```bash
docker-compose ps
```

View logs:

```bash
docker-compose logs -f
```

### 5. Stop the Bot

```bash
docker-compose down
```

## Usage

### Initial Setup

1. Open Telegram and find your bot (by the username you created with BotFather)
2. Send `/start` command to begin

### For Admin User

As the admin (the user whose Chat ID is set in `ADMIN_CHAT_ID`), you have access to all features:

#### Managing User Access

1. Open the bot and send `/start`
2. Click "Admin Panel" button
3. Click "Manage Chats" to view, add, or remove allowed users

**Adding New Users:**
1. In Admin Panel → "Manage Chats" → "Add Chat"
2. Enter the Chat ID of the user you want to add
3. You can get their Chat ID by:
   - Asking them to use [@userinfobot](https://t.me/userinfobot)
   - Having them send a message to your bot and checking logs (unauthorized access will show their Chat ID)
4. Add an optional note to identify the user (e.g., "John Doe - Developer")

**Removing Users:**
1. In Admin Panel → "Manage Chats"
2. Click on the chat you want to remove
3. Confirm removal

#### Viewing Activity Logs

1. Open Admin Panel
2. Click "View Logs" to see recent actions performed through the bot

### Domain Management

#### View Domains

1. Send `/start` to the bot
2. Click "Domains" to see all your Beget domains

#### Manage Subdomains

1. Select a domain from the list
2. Click "Subdomains"
3. You can:
   - View all existing subdomains
   - Add new subdomain: Click "Add Subdomain" and follow prompts
   - Delete subdomain: Click on subdomain → "Delete"

#### DNS Records Management

1. Select a domain from the list
2. Click "DNS Records"
3. Options available:
   - **View All**: See all DNS records (A, AAAA, MX, TXT, CNAME, NS)
   - **A Records**: Manage A records (IP addresses)
     - Add new A record
     - Change existing A record IP
     - Delete A record
   - **TXT Records**: Manage TXT records
     - Add new TXT record (for SPF, DKIM, verification, etc.)
     - View and delete existing TXT records

### For Regular Users

Users who have been added to the allowed chats list can:
- View domains
- Manage subdomains
- Manage DNS records

They cannot:
- Access Admin Panel
- Add or remove users
- View activity logs

## File Structure

```
beget-manager/
├── app/
│   ├── bot/              # Bot initialization and middlewares
│   ├── modules/          # Feature modules (admin, domains)
│   ├── services/         # Business logic (Beget API, Database)
│   ├── utils/            # Helper utilities
│   ├── config.py         # Configuration management
│   └── main.py           # Application entry point
├── data/                 # SQLite database (created automatically)
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Example environment configuration
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker image definition
└── requirements.txt      # Python dependencies
```

## Database

The bot uses SQLite database stored in `./data/bot.db`. The database is automatically created on first run with the following tables:

- `allowed_chats`: List of Chat IDs allowed to use the bot
- `action_logs`: Activity log of all actions performed

The database is persisted through Docker volumes, so your data is safe across container restarts.

## Troubleshooting

### Bot doesn't respond

1. Check if the container is running:
   ```bash
   docker-compose ps
   ```

2. Check logs for errors:
   ```bash
   docker-compose logs -f
   ```

3. Verify your bot token is correct in `.env`

### "Unauthorized access" error

This means your Chat ID is not in the allowed list or doesn't match the `ADMIN_CHAT_ID`:

1. Check the logs to see your actual Chat ID:
   ```bash
   docker logs beget-manager-bot | grep "Unauthorized"
   ```

2. Update `ADMIN_CHAT_ID` in `.env` with the correct value

3. Restart the bot:
   ```bash
   docker-compose restart
   ```

### Beget API errors

1. Verify your Beget credentials in `.env` are correct
2. Check if you have API access enabled in your Beget account
3. Check logs for specific API error messages:
   ```bash
   docker-compose logs -f
   ```

### Database issues

If you need to reset the database:

```bash
# Stop the bot
docker-compose down

# Remove the database
rm -rf data/

# Start the bot (it will create a new database)
docker-compose up -d
```

**Note:** This will delete all user access records and logs.

## Updating

To update the bot to a new version:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- The `.env.example` file is safe to commit (it contains no real credentials)
- Regularly check the activity logs to monitor bot usage
- Only add trusted users to the allowed chats list
- Your Beget API credentials give full access to your hosting account - keep them secure

## Tech Stack

- **Python 3.11**
- **aiogram 3.4.1** - Telegram Bot framework
- **aiohttp 3.9.3** - Async HTTP client for Beget API
- **aiosqlite 0.19.0** - Async SQLite database
- **pydantic 2.x** - Settings and data validation
- **Docker & Docker Compose** - Containerization

## Support

If you encounter any issues or have questions, please:
1. Check the logs: `docker-compose logs -f`
2. Review this README carefully
3. Open an issue in the repository

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
