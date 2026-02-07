"""Callback data constants and helpers.

Telegram limits callback_data to 64 bytes. This module provides:
1. Short prefixes for callback_data
2. Helpers for encoding/decoding callback data
3. State helpers for storing context that doesn't fit in callback_data
"""

# ============ DOMAINS MODULE ============

# Domain navigation (format: prefix:id)
CB_DOMAIN = "d"           # d:123 - view domain menu
CB_DOMAINS_PAGE = "dp"    # dp:2 - domains list page 2

# Subdomain navigation
CB_SUBDOMAINS = "ss"      # ss:123:domain.com - list subdomains
CB_SUBDOMAIN = "s"        # s:456 - view subdomain actions
CB_ADD_SUB = "as"         # as:123 - add subdomain to domain
CB_DEL_SUB = "ds"         # ds:456 - delete subdomain
CB_DO_DEL_SUB = "dds"     # dds:456 - confirm delete subdomain
CB_BACK_SUBS = "bs"       # bs:123 - back to subdomains list

# DNS navigation
CB_DNS = "dn"             # dn:domain.com - DNS menu
CB_DNS_VIEW = "dnv"       # dnv:domain.com - view all DNS
CB_DNS_A = "dna"          # dna:domain.com - A records list
CB_DNS_TXT = "dnt"        # dnt:domain.com - TXT records list
CB_SUBDNS = "sdn"         # sdn:456 - subdomain DNS menu

# A record actions
CB_ADD_A = "aa"           # aa:domain.com - add A record
CB_EDIT_A = "ea"          # ea:123 - edit A record (id from state)
CB_CHANGE_A = "ca"        # ca:123 - change A record IP
CB_DELETE_A = "da"        # da:123 - delete A record
CB_DO_DELETE_A = "dda"    # dda:123 - confirm delete A

# TXT record actions
CB_ADD_TXT = "at"         # at:domain.com - add TXT record
CB_TXT_RECORD = "tr"      # tr:123:0 - view TXT record at index
CB_DELETE_TXT = "dt"      # dt:123:0 - delete TXT record

# ============ ADMIN MODULE ============

# Chat management
CB_ADMIN_CHATS = "ac"     # ac - list chats
CB_ADMIN_CHAT = "ach"     # ach:123 - view chat actions
CB_ADMIN_ADD_CHAT = "aac" # aac - add chat
CB_ADMIN_REMOVE = "arc"   # arc:123 - remove chat
CB_ADMIN_CONFIRM_RM = "acr"  # acr:123 - confirm remove

# Permissions
CB_PERM_DOMAINS = "pd"    # pd - domains for permissions
CB_PERM_DOMAIN = "pdo"    # pdo:domain.com - domain items
CB_PERM_ITEM = "pi"       # pi:d:domain.com or pi:s:sub.domain.com
CB_PERM_GRANT = "pg"      # pg:d:domain.com - grant access
CB_PERM_CANCEL_GRANT = "pcg"  # pcg:d:domain.com - cancel grant
CB_PERM_USER = "pu"       # pu:d:domain.com:123 - user actions
CB_PERM_REVOKE = "pr"     # pr:d:domain.com:123 - revoke
CB_PERM_DO_REVOKE = "pdr" # pdr:d:domain.com:123 - confirm revoke

# Permission flow steps
CB_PERM_DNS = "pdn"       # pdn:domain.com:1:0 - DNS perms step
CB_PERM_SUB = "ps"        # ps:domain.com:1:0 - subdomain perms step
CB_PERM_SUBDNS = "psd"    # psd:sub.domain.com:1:0 - subdomain DNS
CB_PERM_SUBDEL = "psl"    # psl:sub.domain.com:1 - subdomain delete

# User permissions view
CB_PERM_USERS = "pus"     # pus - list users
CB_PERM_VIEWUSER = "pvu"  # pvu:123 - view user permissions

# Logs
CB_ADMIN_LOGS = "al"      # al - view logs

# ============ MENU ============

CB_MENU_MAIN = "mm"       # mm - main menu
CB_MENU_DOMAINS = "md"    # md - domains menu
CB_MENU_ADMIN = "ma"      # ma - admin menu
CB_CANCEL = "x"           # x - cancel action
CB_NOOP = "_"             # _ - no operation (for placeholders)

# Back to subdomains
CB_BACK_DOMAIN = "bd"     # bd:123 - back to domain menu


def shorten_fqdn(fqdn: str, max_len: int = 30) -> str:
    """Shorten FQDN if too long for callback_data.
    
    Keeps the important parts: subdomain prefix and TLD.
    Example: very-long-subdomain.example.com -> very-lo...ple.com
    """
    if len(fqdn) <= max_len:
        return fqdn
    
    # Keep first 12 and last 12 chars
    return f"{fqdn[:12]}...{fqdn[-12:]}"
