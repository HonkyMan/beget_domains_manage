# Service Layer Pattern

<cite>
**Referenced Files in This Document**
- [app/main.py](file://app/main.py)
- [app/config.py](file://app/config.py)
- [app/bot/bot.py](file://app/bot/bot.py)
- [app/services/beget/__init__.py](file://app/services/beget/__init__.py)
- [app/services/beget/client.py](file://app/services/beget/client.py)
- [app/services/beget/domains.py](file://app/services/beget/domains.py)
- [app/services/beget/dns.py](file://app/services/beget/dns.py)
- [app/services/beget/types.py](file://app/services/beget/types.py)
- [app/services/database/__init__.py](file://app/services/database/__init__.py)
- [app/services/database/connection.py](file://app/services/database/connection.py)
- [app/services/database/chats.py](file://app/services/database/chats.py)
- [app/services/database/logs.py](file://app/services/database/logs.py)
- [app/modules/admin/router.py](file://app/modules/admin/router.py)
- [app/modules/domains/router.py](file://app/modules/domains/router.py)
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

## Introduction
This document explains the service layer pattern implemented in the application, focusing on how business logic is abstracted from presentation and data access layers. It covers:
- The Beget API service layer with centralized client access and specialized services for domains and DNS operations
- The repository pattern for database operations, including ChatsRepository and LogsRepository
- Service abstractions that separate business logic from presentation and data access
- Examples of service method implementations, error handling strategies, and the relationship between services and repositories
- Service dependency injection, asynchronous operation patterns, and separation of concerns

## Project Structure
The application follows a layered architecture:
- Presentation layer: Aiogram routers and handlers in modules
- Service layer: Beget API services and database repositories
- Data access layer: Database connection manager and repositories
- Configuration and entry point: Settings loading and bot setup

```mermaid
graph TB
subgraph "Presentation Layer"
AdminRouter["Admin Router<br/>app/modules/admin/router.py"]
DomainsRouter["Domains Router<br/>app/modules/domains/router.py"]
end
subgraph "Service Layer"
BegetServices["Beget Services<br/>app/services/beget/*"]
DbServices["Database Repositories<br/>app/services/database/*"]
end
subgraph "Data Access Layer"
Database["Database Manager<br/>app/services/database/connection.py"]
end
Config["Configuration<br/>app/config.py"]
Main["Entry Point<br/>app/main.py"]
BotSetup["Bot Setup<br/>app/bot/bot.py"]
Main --> BotSetup
BotSetup --> AdminRouter
BotSetup --> DomainsRouter
BotSetup --> DbServices
AdminRouter --> DbServices
DomainsRouter --> BegetServices
DbServices --> Database
```

**Diagram sources**
- [app/main.py](file://app/main.py#L10-L26)
- [app/bot/bot.py](file://app/bot/bot.py#L18-L83)
- [app/modules/admin/router.py](file://app/modules/admin/router.py#L1-L222)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L1-L718)
- [app/services/database/connection.py](file://app/services/database/connection.py#L7-L32)
- [app/services/beget/client.py](file://app/services/beget/client.py#L21-L49)

**Section sources**
- [app/main.py](file://app/main.py#L10-L26)
- [app/bot/bot.py](file://app/bot/bot.py#L18-L83)
- [app/config.py](file://app/config.py#L8-L51)

## Core Components
- Beget API client and services:
  - Centralized HTTP client for Beget API requests
  - Domain management service
  - DNS management service
  - Strongly typed models for API responses and domain/DNS data
- Database services and repositories:
  - Database connection manager with schema initialization
  - Repository for allowed chats
  - Repository for action logs
- Dependency injection:
  - Admin module dependency container
  - Router-level service instantiation for Beget operations

Key implementation references:
- Beget client and error handling: [BegetApiError](file://app/services/beget/client.py#L13-L18), [BegetClient.request](file://app/services/beget/client.py#L70-L121)
- Domain service methods: [DomainsService.get_domains](file://app/services/beget/domains.py#L13-L23), [DomainsService.get_subdomains](file://app/services/beget/domains.py#L25-L41), [DomainsService.add_subdomain](file://app/services/beget/domains.py#L43-L49), [DomainsService.delete_subdomain](file://app/services/beget/domains.py#L51-L57)
- DNS service methods: [DnsService.get_dns_data](file://app/services/beget/dns.py#L14-L77), [DnsService.change_records](file://app/services/beget/dns.py#L79-L99), [DnsService.add_a_record](file://app/services/beget/dns.py#L101-L109), [DnsService.update_a_record](file://app/services/beget/dns.py#L111-L121), [DnsService.delete_a_record](file://app/services/beget/dns.py#L123-L132), [DnsService.add_txt_record](file://app/services/beget/dns.py#L134-L140), [DnsService.delete_txt_record](file://app/services/beget/dns.py#L142-L151)
- Domain/DNS models: [Domain](file://app/services/beget/types.py#L14-L26), [Subdomain](file://app/services/beget/types.py#L21-L26), [DnsRecord](file://app/services/beget/types.py#L28-L33), [DnsData](file://app/services/beget/types.py#L35-L58)
- Database connection and schema: [Database.connect](file://app/services/database/connection.py#L14-L19), [Database._init_schema](file://app/services/database/connection.py#L34-L57)
- Chats repository methods: [ChatsRepository.get_all](file://app/services/database/chats.py#L26-L41), [ChatsRepository.get_chat_ids](file://app/services/database/chats.py#L43-L49), [ChatsRepository.is_allowed](file://app/services/database/chats.py#L51-L57), [ChatsRepository.add](file://app/services/database/chats.py#L59-L69), [ChatsRepository.remove](file://app/services/database/chats.py#L71-L78)
- Logs repository methods: [LogsRepository.add](file://app/services/database/logs.py#L28-L44), [LogsRepository.get_recent](file://app/services/database/logs.py#L46-L64), [LogsRepository.get_by_chat](file://app/services/database/logs.py#L66-L89)
- Dependency injection in admin module: [AdminDeps](file://app/modules/admin/router.py#L22-L29), [setup_admin_deps](file://app/modules/admin/router.py#L32-L41)
- Router-level service instantiation: [Domains router async with client](file://app/modules/domains/router.py#L35-L36), [DNS router async with client](file://app/modules/domains/router.py#L364-L366)

**Section sources**
- [app/services/beget/client.py](file://app/services/beget/client.py#L13-L135)
- [app/services/beget/domains.py](file://app/services/beget/domains.py#L7-L58)
- [app/services/beget/dns.py](file://app/services/beget/dns.py#L8-L152)
- [app/services/beget/types.py](file://app/services/beget/types.py#L6-L59)
- [app/services/database/connection.py](file://app/services/database/connection.py#L7-L59)
- [app/services/database/chats.py](file://app/services/database/chats.py#L20-L79)
- [app/services/database/logs.py](file://app/services/database/logs.py#L22-L90)
- [app/modules/admin/router.py](file://app/modules/admin/router.py#L22-L41)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L35-L36)

## Architecture Overview
The system enforces separation of concerns:
- Presentation layer (routers) orchestrates user interactions and delegates business logic to services
- Service layer encapsulates Beget API operations and domain-specific logic
- Repository layer abstracts database operations behind typed entities
- Configuration and dependency injection ensure clean initialization and wiring

```mermaid
graph TB
User["Telegram User"]
Handler["Aiogram Handler<br/>modules/* router"]
Service["Service Layer<br/>Beget Services / Repositories"]
Api["External API<br/>Beget"]
Repo["Repository Layer<br/>SQL Operations"]
DB["Database<br/>SQLite"]
User --> Handler
Handler --> Service
Service --> Api
Service --> Repo
Repo --> DB
```

**Diagram sources**
- [app/modules/admin/router.py](file://app/modules/admin/router.py#L74-L150)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L28-L52)
- [app/services/beget/client.py](file://app/services/beget/client.py#L70-L121)
- [app/services/database/chats.py](file://app/services/database/chats.py#L26-L41)
- [app/services/database/logs.py](file://app/services/database/logs.py#L28-L44)
- [app/services/database/connection.py](file://app/services/database/connection.py#L14-L19)

## Detailed Component Analysis

### Beget API Service Layer
The Beget service layer provides:
- Centralized HTTP client with async context management and robust error handling
- Domain service for listing domains, subdomains, and performing CRUD-like operations
- DNS service for fetching DNS data, building typed models, and updating records atomically

```mermaid
classDiagram
class BegetClient {
+str login
+str password
+ClientTimeout timeout
+session aiohttp.ClientSession
+request(endpoint, params) Any
-_build_url(endpoint, params) str
-_extract_error_messages(errors) str
}
class DomainsService {
+client BegetClient
+get_domains() Domain[]
+get_subdomains(domain_id) Subdomain[]
+add_subdomain(domain_id, subdomain) bool
+delete_subdomain(subdomain_id) bool
}
class DnsService {
+client BegetClient
+get_dns_data(fqdn) DnsData
+change_records(fqdn, records) bool
+add_a_record(fqdn, ip) bool
+update_a_record(fqdn, old_ip, new_ip) bool
+delete_a_record(fqdn, ip) bool
+add_txt_record(fqdn, value) bool
+delete_txt_record(fqdn, value) bool
}
class Domain {
+int id
+str fqdn
}
class Subdomain {
+int id
+str fqdn
}
class DnsRecord {
+str value
+int priority
}
class DnsData {
+str fqdn
+str[] dns_ip
+str[] dns
+DnsRecord[] a
+DnsRecord[] aaaa
+DnsRecord[] mx
+DnsRecord[] txt
+DnsRecord[] cname
+DnsRecord[] ns
}
DomainsService --> BegetClient : "uses"
DnsService --> BegetClient : "uses"
DomainsService --> Domain : "returns"
DomainsService --> Subdomain : "returns"
DnsService --> DnsData : "returns"
DnsService --> DnsRecord : "composes"
```

**Diagram sources**
- [app/services/beget/client.py](file://app/services/beget/client.py#L21-L135)
- [app/services/beget/domains.py](file://app/services/beget/domains.py#L7-L58)
- [app/services/beget/dns.py](file://app/services/beget/dns.py#L8-L152)
- [app/services/beget/types.py](file://app/services/beget/types.py#L14-L58)

**Section sources**
- [app/services/beget/client.py](file://app/services/beget/client.py#L21-L135)
- [app/services/beget/domains.py](file://app/services/beget/domains.py#L7-L58)
- [app/services/beget/dns.py](file://app/services/beget/dns.py#L8-L152)
- [app/services/beget/types.py](file://app/services/beget/types.py#L6-L59)

### Repository Pattern Implementation
Repositories encapsulate database operations behind typed entities:
- ChatsRepository manages allowed chats with CRUD-like operations
- LogsRepository persists and retrieves action logs with filtering and pagination

```mermaid
classDiagram
class Database {
+Path db_path
+connect() None
+disconnect() None
+connection aiosqlite.Connection
}
class AllowedChat {
+int id
+int chat_id
+str added_by
+datetime added_at
+str|None note
}
class ActionLog {
+int id
+int chat_id
+int|None user_id
+str|None username
+str action
+str|None details
+datetime created_at
}
class ChatsRepository {
+db Database
+get_all() AllowedChat[]
+get_chat_ids() set~int~
+is_allowed(chat_id) bool
+add(chat_id, added_by, note) bool
+remove(chat_id) bool
}
class LogsRepository {
+db Database
+add(chat_id, action, user_id, username, details) None
+get_recent(limit) ActionLog[]
+get_by_chat(chat_id, limit) ActionLog[]
}
ChatsRepository --> Database : "uses"
LogsRepository --> Database : "uses"
ChatsRepository --> AllowedChat : "returns"
LogsRepository --> ActionLog : "returns"
```

**Diagram sources**
- [app/services/database/connection.py](file://app/services/database/connection.py#L7-L59)
- [app/services/database/chats.py](file://app/services/database/chats.py#L9-L79)
- [app/services/database/logs.py](file://app/services/database/logs.py#L9-L90)

**Section sources**
- [app/services/database/connection.py](file://app/services/database/connection.py#L7-L59)
- [app/services/database/chats.py](file://app/services/database/chats.py#L20-L79)
- [app/services/database/logs.py](file://app/services/database/logs.py#L22-L90)

### Service Abstraction and Separation of Concerns
- Presentation layer (routers) handles user events and delegates to services
- Service layer isolates business logic and external API integrations
- Repository layer abstracts persistence concerns
- Configuration and dependency injection keep initialization centralized

Examples of service method implementations:
- Domain listing: [DomainsService.get_domains](file://app/services/beget/domains.py#L13-L23)
- Subdomain filtering and CRUD: [DomainsService.get_subdomains](file://app/services/beget/domains.py#L25-L41), [DomainsService.add_subdomain](file://app/services/beget/domains.py#L43-L49), [DomainsService.delete_subdomain](file://app/services/beget/domains.py#L51-L57)
- DNS record retrieval and updates: [DnsService.get_dns_data](file://app/services/beget/dns.py#L14-L77), [DnsService.change_records](file://app/services/beget/dns.py#L79-L99), [DnsService.add_a_record](file://app/services/beget/dns.py#L101-L109), [DnsService.update_a_record](file://app/services/beget/dns.py#L111-L121), [DnsService.delete_a_record](file://app/services/beget/dns.py#L123-L132), [DnsService.add_txt_record](file://app/services/beget/dns.py#L134-L140), [DnsService.delete_txt_record](file://app/services/beget/dns.py#L142-L151)
- Repository operations: [ChatsRepository.add](file://app/services/database/chats.py#L59-L69), [ChatsRepository.remove](file://app/services/database/chats.py#L71-L78), [LogsRepository.add](file://app/services/database/logs.py#L28-L44)

**Section sources**
- [app/services/beget/domains.py](file://app/services/beget/domains.py#L13-L57)
- [app/services/beget/dns.py](file://app/services/beget/dns.py#L14-L151)
- [app/services/database/chats.py](file://app/services/database/chats.py#L59-L78)
- [app/services/database/logs.py](file://app/services/database/logs.py#L28-L44)

### Asynchronous Operation Patterns
- Async HTTP client with context manager for session lifecycle
- Async database operations with typed row factory
- Handlers in routers orchestrate async service calls

```mermaid
sequenceDiagram
participant User as "Telegram User"
participant Router as "Domains Router"
participant Settings as "Settings"
participant Client as "BegetClient"
participant DomSvc as "DomainsService"
participant API as "Beget API"
User->>Router : "Callback / Command"
Router->>Settings : "get_settings()"
Router->>Client : "async with BegetClient(login, password)"
Router->>DomSvc : "DomainsService(client)"
DomSvc->>Client : "request('domain/getList')"
Client->>API : "GET /api/domain/getList"
API-->>Client : "JSON response"
Client-->>DomSvc : "Parsed answer"
DomSvc-->>Router : "list of Domain"
Router-->>User : "Rendered keyboard / message"
```

**Diagram sources**
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L33-L41)
- [app/services/beget/client.py](file://app/services/beget/client.py#L33-L42)
- [app/services/beget/domains.py](file://app/services/beget/domains.py#L13-L23)

**Section sources**
- [app/services/beget/client.py](file://app/services/beget/client.py#L33-L42)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L33-L41)

### Error Handling Strategies
- Centralized API error type with structured error extraction
- Robust request handling with timeout and response parsing
- Graceful error propagation to handlers for user feedback

```mermaid
flowchart TD
Start(["API Request"]) --> BuildUrl["Build URL with auth params"]
BuildUrl --> MakeReq["HTTP GET via session"]
MakeReq --> RespHeaders["Read headers"]
RespHeaders --> ParseJson["Parse JSON or fallback text"]
ParseJson --> HasTopLevelError{"Top-level status error?"}
HasTopLevelError --> |Yes| RaiseTop["Raise BegetApiError with extracted messages"]
HasTopLevelError --> |No| CheckNested{"Answer has status error?"}
CheckNested --> |Yes| RaiseNested["Raise BegetApiError with extracted messages"]
CheckNested --> |No| ReturnAnswer["Return answer payload"]
ParseJson --> Timeout{"Timeout?"}
Timeout --> |Yes| RaiseTimeout["Raise BegetApiError with timeout message"]
Timeout --> |No| Continue["Continue"]
RaiseTop --> End(["Error"])
RaiseNested --> End
RaiseTimeout --> End
ReturnAnswer --> End(["Success"])
```

**Diagram sources**
- [app/services/beget/client.py](file://app/services/beget/client.py#L70-L121)

**Section sources**
- [app/services/beget/client.py](file://app/services/beget/client.py#L13-L18)
- [app/services/beget/client.py](file://app/services/beget/client.py#L70-L121)

### Relationship Between Services and Repositories
- Admin module handlers depend on injected repositories for allowed chats and logs
- Domain/DNS routers instantiate services per request using the configured client
- Repositories depend on the shared Database connection manager

```mermaid
graph TB
AdminHandler["Admin Handler<br/>modules/admin/router.py"]
DomainsHandler["Domains Handler<br/>modules/domains/router.py"]
ChatsRepo["ChatsRepository"]
LogsRepo["LogsRepository"]
DomainsSvc["DomainsService"]
DnsSvc["DnsService"]
BegetClient["BegetClient"]
DB["Database"]
AdminHandler --> ChatsRepo
AdminHandler --> LogsRepo
DomainsHandler --> DomainsSvc
DomainsHandler --> DnsSvc
DomainsSvc --> BegetClient
DnsSvc --> BegetClient
ChatsRepo --> DB
LogsRepo --> DB
```

**Diagram sources**
- [app/modules/admin/router.py](file://app/modules/admin/router.py#L7-L29)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L35-L36)
- [app/services/beget/domains.py](file://app/services/beget/domains.py#L10-L11)
- [app/services/beget/dns.py](file://app/services/beget/dns.py#L11-L12)
- [app/services/database/chats.py](file://app/services/database/chats.py#L23-L24)
- [app/services/database/logs.py](file://app/services/database/logs.py#L25-L26)

**Section sources**
- [app/modules/admin/router.py](file://app/modules/admin/router.py#L7-L29)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L35-L36)
- [app/services/beget/domains.py](file://app/services/beget/domains.py#L10-L11)
- [app/services/beget/dns.py](file://app/services/beget/dns.py#L11-L12)
- [app/services/database/chats.py](file://app/services/database/chats.py#L23-L24)
- [app/services/database/logs.py](file://app/services/database/logs.py#L25-L26)

## Dependency Analysis
- Module-level dependencies:
  - Admin router depends on repositories and admin chat ID
  - Domains router depends on Beget services and settings
- Service-level dependencies:
  - DomainsService and DnsService depend on BegetClient
  - Repositories depend on Database
- Initialization dependencies:
  - Bot setup creates repositories and injects them into admin router
  - Entry point initializes settings and starts polling

```mermaid
graph TB
Main["app/main.py"]
Bot["app/bot/bot.py"]
Admin["app/modules/admin/router.py"]
Domains["app/modules/domains/router.py"]
BegetInit["app/services/beget/__init__.py"]
DbInit["app/services/database/__init__.py"]
Config["app/config.py"]
Main --> Bot
Bot --> Admin
Bot --> Domains
Domains --> BegetInit
Admin --> DbInit
Bot --> DbInit
Bot --> Config
```

**Diagram sources**
- [app/main.py](file://app/main.py#L10-L26)
- [app/bot/bot.py](file://app/bot/bot.py#L18-L83)
- [app/modules/admin/router.py](file://app/modules/admin/router.py#L9-L16)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L7-L8)
- [app/services/beget/__init__.py](file://app/services/beget/__init__.py#L1-L7)
- [app/services/database/__init__.py](file://app/services/database/__init__.py#L1-L7)
- [app/config.py](file://app/config.py#L37-L51)

**Section sources**
- [app/main.py](file://app/main.py#L10-L26)
- [app/bot/bot.py](file://app/bot/bot.py#L18-L83)
- [app/modules/admin/router.py](file://app/modules/admin/router.py#L9-L16)
- [app/modules/domains/router.py](file://app/modules/domains/router.py#L7-L8)
- [app/services/beget/__init__.py](file://app/services/beget/__init__.py#L1-L7)
- [app/services/database/__init__.py](file://app/services/database/__init__.py#L1-L7)
- [app/config.py](file://app/config.py#L37-L51)

## Performance Considerations
- Asynchronous I/O: Both HTTP and database operations are async, minimizing blocking and improving throughput under concurrent load
- Minimal parsing overhead: The Beget client parses responses once and raises structured errors early
- Efficient queries: Repositories use parameterized statements and targeted selects to reduce overhead
- Connection lifecycle: Async context managers ensure sessions and connections are properly managed

## Troubleshooting Guide
Common issues and resolutions:
- API authentication failures:
  - Verify Beget credentials in environment variables and ensure correct login/password
  - Review BegetApiError messages and extracted error texts
  - Check request URLs logged with masked passwords for debugging
  - Reference: [BegetApiError](file://app/services/beget/client.py#L13-L18), [BegetClient.request](file://app/services/beget/client.py#L70-L121)
- Network timeouts:
  - Adjust timeout settings if the API is slow to respond
  - Inspect timeout error messages raised during requests
  - Reference: [BegetClient.request timeout handling](file://app/services/beget/client.py#L118-L120)
- Database connectivity:
  - Ensure database path exists and is writable
  - Confirm schema initialization ran successfully
  - Reference: [Database.connect](file://app/services/database/connection.py#L14-L19), [Database._init_schema](file://app/services/database/connection.py#L34-L57)
- Repository operations:
  - Add operations return booleans indicating success/failure; handle duplicates gracefully
  - Remove operations return row counts; confirm deletions by checking returned values
  - Reference: [ChatsRepository.add](file://app/services/database/chats.py#L59-L69), [ChatsRepository.remove](file://app/services/database/chats.py#L71-L78), [LogsRepository.add](file://app/services/database/logs.py#L28-L44)

**Section sources**
- [app/services/beget/client.py](file://app/services/beget/client.py#L13-L18)
- [app/services/beget/client.py](file://app/services/beget/client.py#L70-L121)
- [app/services/database/connection.py](file://app/services/database/connection.py#L14-L19)
- [app/services/database/connection.py](file://app/services/database/connection.py#L34-L57)
- [app/services/database/chats.py](file://app/services/database/chats.py#L59-L69)
- [app/services/database/chats.py](file://app/services/database/chats.py#L71-L78)
- [app/services/database/logs.py](file://app/services/database/logs.py#L28-L44)

## Conclusion
The service layer pattern in this application cleanly separates concerns:
- Presentation layer focuses on user interactions
- Service layer encapsulates business logic and external integrations
- Repository layer abstracts persistence
- Dependency injection and async patterns improve maintainability and testability

This design enables straightforward testing of services and repositories independently, while keeping presentation logic minimal and focused on routing and UI composition.