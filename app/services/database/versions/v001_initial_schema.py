"""Migration 001: Initial schema.

Creates the base tables for the application:
- allowed_chats: List of chat IDs allowed to use the bot
- action_logs: Activity log of all actions performed
- domain_permissions: Domain-level permissions
- subdomain_permissions: Subdomain-only permissions
- created_subdomains: Track subdomain creators
"""

VERSION = 1
DESCRIPTION = "Initial schema with all base tables"


async def upgrade(connection) -> None:
    """Apply migration."""
    await connection.executescript("""
        -- Allowed chats table
        CREATE TABLE IF NOT EXISTS allowed_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE NOT NULL,
            added_by TEXT NOT NULL,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            note TEXT
        );

        -- Action logs table
        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_action_logs_created_at 
        ON action_logs(created_at DESC);

        -- Domain-level permissions
        CREATE TABLE IF NOT EXISTS domain_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            domain_fqdn TEXT NOT NULL,
            can_create_subdomain BOOLEAN DEFAULT 0,
            can_delete_subdomain BOOLEAN DEFAULT 0,
            granted_by TEXT NOT NULL,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, domain_fqdn)
        );

        CREATE INDEX IF NOT EXISTS idx_domain_perm_chat 
        ON domain_permissions(chat_id);

        CREATE INDEX IF NOT EXISTS idx_domain_perm_fqdn 
        ON domain_permissions(domain_fqdn);

        -- Subdomain-only permissions
        CREATE TABLE IF NOT EXISTS subdomain_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            subdomain_fqdn TEXT NOT NULL,
            granted_by TEXT NOT NULL,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chat_id, subdomain_fqdn)
        );

        CREATE INDEX IF NOT EXISTS idx_subdomain_perm_chat 
        ON subdomain_permissions(chat_id);

        CREATE INDEX IF NOT EXISTS idx_subdomain_perm_fqdn 
        ON subdomain_permissions(subdomain_fqdn);

        -- Track subdomain creators for auto-privileges
        CREATE TABLE IF NOT EXISTS created_subdomains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subdomain_fqdn TEXT NOT NULL UNIQUE,
            created_by_chat_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_created_sub_chat 
        ON created_subdomains(created_by_chat_id);
    """)
    await connection.commit()


async def downgrade(connection) -> None:
    """Revert migration."""
    await connection.executescript("""
        DROP TABLE IF EXISTS created_subdomains;
        DROP TABLE IF EXISTS subdomain_permissions;
        DROP TABLE IF EXISTS domain_permissions;
        DROP TABLE IF EXISTS action_logs;
        DROP TABLE IF EXISTS allowed_chats;
    """)
    await connection.commit()
