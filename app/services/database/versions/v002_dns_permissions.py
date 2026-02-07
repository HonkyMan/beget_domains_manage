"""Migration 002: Add DNS permissions.

Adds DNS edit/delete permission columns to domain and subdomain permissions.
Also adds can_delete_subdomain to subdomain_permissions.
"""

VERSION = 2
DESCRIPTION = "Add DNS edit/delete permission columns"


async def upgrade(connection) -> None:
    """Apply migration."""
    # Add columns to domain_permissions
    # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we check first
    cursor = await connection.execute("PRAGMA table_info(domain_permissions)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if "can_edit_dns" not in columns:
        await connection.execute(
            "ALTER TABLE domain_permissions ADD COLUMN can_edit_dns BOOLEAN DEFAULT 0"
        )
    
    if "can_delete_dns" not in columns:
        await connection.execute(
            "ALTER TABLE domain_permissions ADD COLUMN can_delete_dns BOOLEAN DEFAULT 0"
        )
    
    # Add columns to subdomain_permissions
    cursor = await connection.execute("PRAGMA table_info(subdomain_permissions)")
    columns = {row[1] for row in await cursor.fetchall()}
    
    if "can_edit_dns" not in columns:
        await connection.execute(
            "ALTER TABLE subdomain_permissions ADD COLUMN can_edit_dns BOOLEAN DEFAULT 0"
        )
    
    if "can_delete_dns" not in columns:
        await connection.execute(
            "ALTER TABLE subdomain_permissions ADD COLUMN can_delete_dns BOOLEAN DEFAULT 0"
        )
    
    if "can_delete_subdomain" not in columns:
        await connection.execute(
            "ALTER TABLE subdomain_permissions ADD COLUMN can_delete_subdomain BOOLEAN DEFAULT 0"
        )
    
    await connection.commit()


async def downgrade(connection) -> None:
    """Revert migration.
    
    Note: SQLite doesn't support DROP COLUMN easily.
    A full revert would require recreating tables.
    For simplicity, we leave columns in place.
    """
    pass
