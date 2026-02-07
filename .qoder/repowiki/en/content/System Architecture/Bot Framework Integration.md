# Bot Framework Integration

<cite>
**Referenced Files in This Document**
- [main.py](file://app/main.py)
- [bot.py](file://app/bot/bot.py)
- [config.py](file://app/config.py)
- [auth.py](file://app/bot/middlewares/auth.py)
- [logging.py](file://app/bot/middlewares/logging.py)
- [common.py](file://app/bot/keyboards/common.py)
- [router.py](file://app/modules/admin/router.py)
- [router.py](file://app/modules/domains/router.py)
- [states.py](file://app/modules/admin/states.py)
- [states.py](file://app/modules/domains/states.py)
- [connection.py](file://app/services/database/connection.py)
- [chats.py](file://app/services/database/chats.py)
- [logs.py](file://app/services/database/logs.py)
- [.env.example](file://.env.example)
- [requirements.txt](file://requirements.txt)
- [Dockerfile](file://Dockerfile)
- [docker-compose.yml](file://docker-compose.yml)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the Telegram bot framework integration built on AIogram 3.4.1. It covers the complete initialization and lifecycle of the bot, including configuration via environment variables, database setup, middleware registration, and handler orchestration. It also documents memory storage usage, state management patterns, and the relationship between the entry point and the bot initialization function.

## Project Structure
The bot is organized around a modular structure:
- Entry point initializes configuration and starts the polling loop.
- Bot initialization sets up logging, database, repositories, middleware, and base handlers.
- Feature modules register their own routers and states.
- Middleware enforces authentication and logging.
- Database services manage SQLite connections and repositories.

```mermaid
graph TB
subgraph "Entry Point"
M["app/main.py"]
end
subgraph "Bot Initialization"
B["app/bot/bot.py"]
C["app/config.py"]
end
subgraph "Middlewares"
AM["app/bot/middlewares/auth.py"]
LM["app/bot/middlewares/logging.py"]
end
subgraph "Feature Modules"
AR["app/modules/admin/router.py"]
DR["app/modules/domains/router.py"]
AS["app/modules/admin/states.py"]
DS["app/modules/domains/states.py"]
end
subgraph "Keyboards"
CK["app/bot/keyboards/common.py"]
end
subgraph "Database Services"
DB["app/services/database/connection.py"]
CR["app/services/database/chats.py"]
LR["app/services/database/logs.py"]
end
M --> B
B --> C
B --> AM
B --> LM
B --> AR
B --> DR
B --> CK
B --> DB
B --> CR
B --> LR
AR --> AS
DR --> DS
```

**Diagram sources**
- [main.py](file://app/main.py#L10-L29)
- [bot.py](file://app/bot/bot.py#L18-L82)
- [config.py](file://app/config.py#L8-L51)
- [auth.py](file://app/bot/middlewares/auth.py#L10-L45)
- [logging.py](file://app/bot/middlewares/logging.py#L12-L75)
- [router.py](file://app/modules/admin/router.py#L19-L61)
- [router.py](file://app/modules/domains/router.py#L22-L52)
- [states.py](file://app/modules/admin/states.py#L6-L11)
- [states.py](file://app/modules/domains/states.py#L6-L20)
- [common.py](file://app/bot/keyboards/common.py#L7-L26)
- [connection.py](file://app/services/database/connection.py#L7-L58)
- [chats.py](file://app/services/database/chats.py#L20-L78)
- [logs.py](file://app/services/database/logs.py#L22-L89)

**Section sources**
- [main.py](file://app/main.py#L1-L30)
- [bot.py](file://app/bot/bot.py#L1-L83)
- [config.py](file://app/config.py#L1-L52)

## Core Components
- Entry point: Initializes settings, creates bot and dispatcher, starts polling, and ensures cleanup.
- Bot initialization: Loads settings, configures logging, connects to the database, registers middlewares and routers, and defines base handlers.
- Configuration: Uses Pydantic settings with environment variables and a cached settings instance.
- Database: SQLite managed via aiosqlite with repositories for allowed chats and logs.
- Middlewares: Authentication middleware checks allowed chats and admin privileges; logging middleware records actions and notifies admins.
- Feature routers: Admin and domains modules register their own handlers and states.
- Keyboards: Shared inline keyboards for menus and navigation.

**Section sources**
- [main.py](file://app/main.py#L10-L29)
- [bot.py](file://app/bot/bot.py#L18-L82)
- [config.py](file://app/config.py#L8-L51)
- [connection.py](file://app/services/database/connection.py#L7-L58)
- [chats.py](file://app/services/database/chats.py#L20-L78)
- [logs.py](file://app/services/database/logs.py#L22-L89)
- [auth.py](file://app/bot/middlewares/auth.py#L10-L45)
- [logging.py](file://app/bot/middlewares/logging.py#L12-L75)
- [router.py](file://app/modules/admin/router.py#L19-L61)
- [router.py](file://app/modules/domains/router.py#L22-L52)
- [common.py](file://app/bot/keyboards/common.py#L7-L26)

## Architecture Overview
The bot follows a layered architecture:
- Application entry point orchestrates startup and shutdown.
- Bot initialization composes configuration, database, repositories, middlewares, and routers.
- Dispatching routes messages and callbacks to appropriate handlers.
- State machines manage multi-step operations.
- Repositories encapsulate persistence logic.

```mermaid
sequenceDiagram
participant EP as "Entry Point<br/>app/main.py"
participant SI as "setup_bot<br/>app/bot/bot.py"
participant CFG as "Settings<br/>app/config.py"
participant DB as "Database<br/>app/services/database/connection.py"
participant MW1 as "Auth Middleware<br/>app/bot/middlewares/auth.py"
participant MW2 as "Logging Middleware<br/>app/bot/middlewares/logging.py"
participant ADM as "Admin Router<br/>app/modules/admin/router.py"
participant DOM as "Domains Router<br/>app/modules/domains/router.py"
EP->>EP : "init_settings()"
EP->>SI : "await setup_bot()"
SI->>CFG : "get_settings()"
SI->>SI : "configure logging"
SI->>DB : "Database(path)"
SI->>DB : "await connect()"
SI->>SI : "create repos (Chats, Logs)"
SI->>SI : "setup_admin_deps()"
SI->>SI : "Bot(token)"
SI->>SI : "Dispatcher(storage=MemoryStorage)"
SI->>MW1 : "register middleware"
SI->>MW2 : "register middleware"
SI->>ADM : "include_router"
SI->>DOM : "include_router"
SI->>SI : "register base handlers (/start, menu, cancel)"
SI-->>EP : "return bot, dp, db"
EP->>EP : "dp.start_polling(bot)"
EP->>DB : "await disconnect()"
EP->>EP : "bot.session.close()"
```

**Diagram sources**
- [main.py](file://app/main.py#L10-L29)
- [bot.py](file://app/bot/bot.py#L18-L82)
- [config.py](file://app/config.py#L37-L51)
- [connection.py](file://app/services/database/connection.py#L14-L25)
- [auth.py](file://app/bot/middlewares/auth.py#L17-L45)
- [logging.py](file://app/bot/middlewares/logging.py#L20-L75)
- [router.py](file://app/modules/admin/router.py#L32-L41)
- [router.py](file://app/modules/domains/router.py#L22-L52)

## Detailed Component Analysis

### Entry Point and Lifecycle
- The entry point initializes settings, constructs the bot and dispatcher via the setup function, starts long polling, and ensures database and session cleanup on shutdown.
- The lifecycle is straightforward: startup, run until interrupted, then teardown.

```mermaid
flowchart TD
Start(["Process Start"]) --> InitSettings["Call init_settings()"]
InitSettings --> SetupBot["await setup_bot()"]
SetupBot --> Polling["dp.start_polling(bot)"]
Polling --> Running{"Running"}
Running --> Shutdown["On exit: db.disconnect(), bot.session.close()"]
Shutdown --> End(["Process Exit"])
```

**Diagram sources**
- [main.py](file://app/main.py#L10-L29)

**Section sources**
- [main.py](file://app/main.py#L10-L29)

### Bot Initialization and setup_bot
- Loads settings and configures logging with level from environment.
- Establishes a SQLite database connection and initializes schema.
- Creates repositories for chats and logs and injects dependencies into the admin module.
- Instantiates Bot and Dispatcher with MemoryStorage for state persistence.
- Registers middlewares for authentication and logging.
- Includes admin and domains routers.
- Registers base handlers for /start, main menu navigation, and cancellation.

```mermaid
flowchart TD
A["setup_bot()"] --> B["get_settings()"]
B --> C["logging.basicConfig(level, format)"]
C --> D["Database(db_path)"]
D --> E["await db.connect()"]
E --> F["ChatsRepository(db), LogsRepository(db)"]
F --> G["setup_admin_deps(chats_repo, logs_repo, admin_chat_id)"]
G --> H["Bot(token)"]
H --> I["Dispatcher(storage=MemoryStorage)"]
I --> J["AuthMiddleware(chats_repo, admin_chat_id)"]
J --> K["LoggingMiddleware(logs_repo, bot, admin_chat_id)"]
K --> L["dp.include_router(admin_router)"]
L --> M["dp.include_router(domains_router)"]
M --> N["Register base handlers (/start, menu, cancel)"]
N --> O["Return bot, dp, db"]
```

**Diagram sources**
- [bot.py](file://app/bot/bot.py#L18-L82)
- [config.py](file://app/config.py#L37-L51)
- [connection.py](file://app/services/database/connection.py#L14-L25)
- [auth.py](file://app/bot/middlewares/auth.py#L13-L15)
- [logging.py](file://app/bot/middlewares/logging.py#L15-L18)
- [router.py](file://app/modules/admin/router.py#L32-L41)
- [router.py](file://app/modules/domains/router.py#L22-L52)

**Section sources**
- [bot.py](file://app/bot/bot.py#L18-L82)

### Configuration Management (get_settings)
- Settings are loaded from environment variables using Pydantic settings with a dedicated .env file.
- Provides defaults for optional fields and computed paths for the database.
- Exposes a cached getter and an initialization function for eager loading.

```mermaid
classDiagram
class Settings {
+telegram_bot_token : str
+admin_chat_id : int
+beget_login : str
+beget_password : str
+log_level : str
+data_dir : Path
+db_path : Path
}
class ConfigModule {
+get_settings() Settings
+init_settings() Settings
+settings : Settings
}
ConfigModule --> Settings : "loads from .env"
```

**Diagram sources**
- [config.py](file://app/config.py#L8-L51)

**Section sources**
- [config.py](file://app/config.py#L8-L51)
- [.env.example](file://.env.example#L1-L11)

### Database and Repositories
- Database manages SQLite connection, schema initialization, and exposes a shared connection.
- ChatsRepository handles allowed chats with CRUD operations and existence checks.
- LogsRepository persists action logs and supports recent and per-chat queries.

```mermaid
classDiagram
class Database {
-db_path : Path
-_connection : aiosqlite.Connection
+connect() void
+disconnect() void
+connection : aiosqlite.Connection
-_init_schema() void
}
class ChatsRepository {
-db : Database
+get_all() AllowedChat[]
+get_chat_ids() set~int~
+is_allowed(chat_id) bool
+add(chat_id, added_by, note) bool
+remove(chat_id) bool
}
class LogsRepository {
-db : Database
+add(chat_id, user_id, username, action, details) void
+get_recent(limit) ActionLog[]
+get_by_chat(chat_id, limit) ActionLog[]
}
Database <.. ChatsRepository : "uses"
Database <.. LogsRepository : "uses"
```

**Diagram sources**
- [connection.py](file://app/services/database/connection.py#L7-L58)
- [chats.py](file://app/services/database/chats.py#L20-L78)
- [logs.py](file://app/services/database/logs.py#L22-L89)

**Section sources**
- [connection.py](file://app/services/database/connection.py#L7-L58)
- [chats.py](file://app/services/database/chats.py#L20-L78)
- [logs.py](file://app/services/database/logs.py#L22-L89)

### Middlewares
- Authentication middleware checks admin privileges and allowed chats, injecting an is_admin flag into handler data.
- Logging middleware captures user actions, writes logs, and sends notifications to the admin chat.

```mermaid
classDiagram
class AuthMiddleware {
-chats_repo : ChatsRepository
-admin_chat_id : int
+__call__(handler, event, data) Any
}
class LoggingMiddleware {
-logs_repo : LogsRepository
-bot : Bot
-admin_chat_id : int
+__call__(handler, event, data) Any
}
AuthMiddleware --> ChatsRepository : "uses"
LoggingMiddleware --> LogsRepository : "uses"
LoggingMiddleware --> Bot : "uses"
```

**Diagram sources**
- [auth.py](file://app/bot/middlewares/auth.py#L10-L45)
- [logging.py](file://app/bot/middlewares/logging.py#L12-L75)

**Section sources**
- [auth.py](file://app/bot/middlewares/auth.py#L10-L45)
- [logging.py](file://app/bot/middlewares/logging.py#L12-L75)

### Base Handlers and Navigation
- /start handler responds with a welcome message and displays the main menu, conditionally showing admin options.
- Main menu navigation uses callback data to refresh the message with the appropriate keyboard.
- Cancel handler clears the current state and returns to the main menu.

```mermaid
sequenceDiagram
participant U as "User"
participant DP as "Dispatcher"
participant H1 as "cmd_start"
participant H2 as "main_menu"
participant H3 as "cancel_action"
U->>DP : "Message '/start'"
DP->>H1 : "invoke"
H1-->>U : "Welcome + main menu"
U->>DP : "Callback 'menu : main'"
DP->>H2 : "invoke"
H2-->>U : "Edit to main menu"
U->>DP : "Callback 'cancel'"
DP->>H3 : "invoke"
H3-->>U : "Clear state + main menu"
```

**Diagram sources**
- [bot.py](file://app/bot/bot.py#L54-L80)
- [common.py](file://app/bot/keyboards/common.py#L7-L17)

**Section sources**
- [bot.py](file://app/bot/bot.py#L54-L80)
- [common.py](file://app/bot/keyboards/common.py#L7-L17)

### Feature Modules: Admin and Domains
- Admin router:
  - Registers admin-only handlers and filters.
  - Manages allowed chats, logs viewing, and state-driven workflows.
  - Uses AdminStates for multi-step operations.
- Domains router:
  - Integrates with Beget API clients for domains and DNS operations.
  - Implements state machines for subdomain and DNS management.
  - Handles errors gracefully and updates UI via callback editing.

```mermaid
graph TB
subgraph "Admin Module"
AR["admin/router.py"]
AS["admin/states.py"]
end
subgraph "Domains Module"
DR["domains/router.py"]
DS["domains/states.py"]
end
AR --> AS
DR --> DS
```

**Diagram sources**
- [router.py](file://app/modules/admin/router.py#L19-L61)
- [states.py](file://app/modules/admin/states.py#L6-L11)
- [router.py](file://app/modules/domains/router.py#L22-L52)
- [states.py](file://app/modules/domains/states.py#L6-L20)

**Section sources**
- [router.py](file://app/modules/admin/router.py#L19-L61)
- [states.py](file://app/modules/admin/states.py#L6-L11)
- [router.py](file://app/modules/domains/router.py#L22-L52)
- [states.py](file://app/modules/domains/states.py#L6-L20)

### Memory Storage and State Management
- Dispatcher uses MemoryStorage, persisting FSM state in memory for the lifetime of the process.
- State groups are defined per module to manage multi-step flows:
  - AdminStates: chat management workflows.
  - SubdomainStates and DnsStates: domains and DNS operations.
- Handlers use state transitions and data updates to guide users through operations.

```mermaid
stateDiagram-v2
[*] --> Idle
Idle --> WaitingInput : "set_state(...)"
WaitingInput --> Processing : "receive input"
Processing --> Idle : "clear() or next state"
Processing --> WaitingInput : "validation failed"
```

**Diagram sources**
- [bot.py](file://app/bot/bot.py#L41-L41)
- [states.py](file://app/modules/admin/states.py#L6-L11)
- [states.py](file://app/modules/domains/states.py#L6-L20)

**Section sources**
- [bot.py](file://app/bot/bot.py#L41-L41)
- [states.py](file://app/modules/admin/states.py#L6-L11)
- [states.py](file://app/modules/domains/states.py#L6-L20)

## Dependency Analysis
- External dependencies pinned in requirements: AIogram 3.4.1, aiohttp, aiosqlite, pydantic and pydantic-settings.
- Environment-driven configuration via .env.example.
- Containerization with Docker and docker-compose mounting persistent data volume.

```mermaid
graph TB
RQ["requirements.txt"] --> AG["aiogram==3.4.1"]
RQ --> AH["aiohttp==3.9.3"]
RQ --> AS["aiosqlite==0.19.0"]
RQ --> PD["pydantic>=2.4.1,<2.6"]
RQ --> PS["pydantic-settings>=2.1.0"]
DC["docker-compose.yml"] --> ENV[".env mounted"]
DC --> VOL["./data:/app/data"]
DK["Dockerfile"] --> CMD["CMD python -m app.main"]
```

**Diagram sources**
- [requirements.txt](file://requirements.txt#L1-L6)
- [docker-compose.yml](file://docker-compose.yml#L1-L14)
- [Dockerfile](file://Dockerfile#L1-L17)

**Section sources**
- [requirements.txt](file://requirements.txt#L1-L6)
- [docker-compose.yml](file://docker-compose.yml#L1-L14)
- [Dockerfile](file://Dockerfile#L1-L17)

## Performance Considerations
- MemoryStorage is lightweight but not suitable for multi-instance deployments; consider Redis-backed storage for scaling.
- Database operations are synchronous in handlers; batch or cache where appropriate.
- Logging middleware performs database writes and admin notifications; ensure admin chat availability to avoid blocking.
- Long polling is efficient for moderate traffic; monitor memory usage and consider rate limits.

## Troubleshooting Guide
- Missing environment variables:
  - Ensure TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, BEGET_LOGIN, BEGET_PASSWORD, and LOG_LEVEL are set in .env.
- Database connectivity:
  - Verify data directory permissions and path resolution; the database file is created under data/bot.db.
- Authentication failures:
  - Confirm the user’s chat ID is present in allowed chats or matches ADMIN_CHAT_ID.
- Handler not triggered:
  - Check middleware filters and callback data correctness.
- State not clearing:
  - Ensure cancel handlers call state.clear() and update UI accordingly.

**Section sources**
- [.env.example](file://.env.example#L1-L11)
- [connection.py](file://app/services/database/connection.py#L14-L19)
- [auth.py](file://app/bot/middlewares/auth.py#L34-L42)
- [bot.py](file://app/bot/bot.py#L72-L80)

## Conclusion
The bot integrates AIogram 3.4.1 with a clean initialization flow, robust configuration, and modular feature routers. Memory storage suits single-instance deployments, while middlewares and repositories provide extensible foundations for authentication, logging, and persistence. The entry point and setup function coordinate startup and shutdown reliably, ensuring a smooth operational lifecycle.

## Appendices
- Practical configuration steps:
  - Copy .env.example to .env and fill in credentials.
  - Build and run with Docker Compose; data persists in ./data.
- Error handling tips:
  - Wrap external API calls in try/except blocks and notify users appropriately.
  - Use state.clear() after exceptions to reset user workflows.