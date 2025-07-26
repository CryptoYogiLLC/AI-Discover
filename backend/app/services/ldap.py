"""LDAP/Active Directory authentication service"""

import asyncio
from typing import Optional, Dict, Any, List
from functools import lru_cache
import ldap3
from ldap3 import Server, Connection, ALL, NTLM, SIMPLE
from ldap3.core.exceptions import LDAPException
from structlog import get_logger

from app.core.config import settings
from app.models.user import UserRole

logger = get_logger()


class LDAPService:
    """Service for LDAP/Active Directory authentication and user management"""

    def __init__(self):
        self.server_url = settings.LDAP_SERVER_URL
        self.base_dn = settings.LDAP_BASE_DN
        self.bind_dn = settings.LDAP_BIND_DN
        self.bind_password = settings.LDAP_BIND_PASSWORD
        self.user_search_filter = (
            settings.LDAP_USER_SEARCH_FILTER or "(sAMAccountName={username})"
        )
        self.group_search_filter = (
            settings.LDAP_GROUP_SEARCH_FILTER or "(member={user_dn})"
        )
        self.use_ssl = settings.LDAP_USE_SSL
        self.use_tls = settings.LDAP_USE_TLS
        self.auth_type = settings.LDAP_AUTH_TYPE  # SIMPLE or NTLM

        # Role mapping from LDAP groups to application roles
        self.role_mapping = {
            settings.LDAP_ADMIN_GROUP: UserRole.ADMIN,
            settings.LDAP_COLLABORATOR_GROUP: UserRole.COLLABORATOR,
            settings.LDAP_VIEWER_GROUP: UserRole.VIEWER,
        }

        self._server = None

    @property
    def server(self) -> Server:
        """Get or create LDAP server instance"""
        if not self._server:
            self._server = Server(
                self.server_url, use_ssl=self.use_ssl, get_info=ALL, connect_timeout=10
            )
        return self._server

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user against LDAP/AD

        Args:
            username: Username or email
            password: User password

        Returns:
            User information dict if authentication successful, None otherwise
        """
        try:
            # Run LDAP operations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._authenticate_user_sync, username, password
            )
        except Exception as e:
            logger.error("LDAP authentication error", error=str(e), username=username)
            return None

    def _authenticate_user_sync(
        self, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Synchronous LDAP authentication"""
        conn = None
        try:
            # First, bind with service account to search for user
            if self.auth_type == "NTLM":
                conn = Connection(
                    self.server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    authentication=NTLM,
                    auto_bind=True,
                )
            else:
                conn = Connection(
                    self.server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    authentication=SIMPLE,
                    auto_bind=True,
                )

            # Search for user
            search_filter = self.user_search_filter.format(username=username)
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                attributes=["*"],
            )

            if not conn.entries:
                logger.warning("User not found in LDAP", username=username)
                return None

            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn

            # Rebind to close service account connection
            conn.unbind()

            # Try to bind with user credentials
            if self.auth_type == "NTLM":
                user_conn = Connection(
                    self.server,
                    user=(
                        f"{settings.LDAP_DOMAIN}\\{username}"
                        if settings.LDAP_DOMAIN
                        else username
                    ),
                    password=password,
                    authentication=NTLM,
                    auto_bind=True,
                )
            else:
                user_conn = Connection(
                    self.server,
                    user=user_dn,
                    password=password,
                    authentication=SIMPLE,
                    auto_bind=True,
                )

            # If bind successful, get user info and groups
            user_info = self._extract_user_info(user_entry)
            user_info["ldap_dn"] = user_dn

            # Get user groups and determine role
            groups = self._get_user_groups(user_dn)
            user_info["groups"] = groups
            user_info["role"] = self._determine_user_role(groups)

            user_conn.unbind()

            logger.info(
                "LDAP authentication successful",
                username=username,
                role=user_info["role"],
            )
            return user_info

        except LDAPException as e:
            logger.error(
                "LDAP exception during authentication", error=str(e), username=username
            )
            return None
        finally:
            if conn and conn.bound:
                conn.unbind()

    def _extract_user_info(self, ldap_entry) -> Dict[str, Any]:
        """Extract user information from LDAP entry"""

        def get_attr(entry, attr_name, default=None):
            """Safely get attribute value from LDAP entry"""
            value = entry.get(attr_name)
            if value and hasattr(value, "value"):
                return value.value
            return default

        return {
            "username": get_attr(ldap_entry, "sAMAccountName")
            or get_attr(ldap_entry, "uid"),
            "email": get_attr(ldap_entry, "mail")
            or get_attr(ldap_entry, "userPrincipalName"),
            "full_name": get_attr(ldap_entry, "displayName")
            or get_attr(ldap_entry, "cn"),
            "first_name": get_attr(ldap_entry, "givenName"),
            "last_name": get_attr(ldap_entry, "sn"),
            "department": get_attr(ldap_entry, "department"),
            "title": get_attr(ldap_entry, "title"),
        }

    def _get_user_groups(self, user_dn: str) -> List[str]:
        """Get list of groups user belongs to"""
        groups = []
        conn = None
        try:
            # Bind with service account
            conn = Connection(
                self.server,
                user=self.bind_dn,
                password=self.bind_password,
                authentication=SIMPLE if self.auth_type == "SIMPLE" else NTLM,
                auto_bind=True,
            )

            # Search for groups
            search_filter = self.group_search_filter.format(user_dn=user_dn)
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                attributes=["cn"],
            )

            for entry in conn.entries:
                if hasattr(entry, "cn") and entry.cn:
                    groups.append(str(entry.cn))

            conn.unbind()

        except LDAPException as e:
            logger.error("Error getting user groups", error=str(e), user_dn=user_dn)
        finally:
            if conn and conn.bound:
                conn.unbind()

        return groups

    def _determine_user_role(self, groups: List[str]) -> UserRole:
        """Determine user role based on LDAP group membership"""
        # Check groups in order of privilege (highest to lowest)
        for group_name, role in sorted(
            self.role_mapping.items(),
            key=lambda x: [
                UserRole.ADMIN,
                UserRole.COLLABORATOR,
                UserRole.VIEWER,
            ].index(x[1]),
        ):
            if group_name and group_name in groups:
                return role

        # Default to viewer role
        return UserRole.VIEWER

    async def sync_user_groups(self, username: str) -> Optional[UserRole]:
        """
        Sync user groups from LDAP and return updated role

        Args:
            username: Username to sync

        Returns:
            Updated user role or None if sync failed
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._sync_user_groups_sync, username
            )
        except Exception as e:
            logger.error("Error syncing user groups", error=str(e), username=username)
            return None

    def _sync_user_groups_sync(self, username: str) -> Optional[UserRole]:
        """Synchronous group sync operation"""
        conn = None
        try:
            # Bind with service account
            conn = Connection(
                self.server,
                user=self.bind_dn,
                password=self.bind_password,
                authentication=SIMPLE if self.auth_type == "SIMPLE" else NTLM,
                auto_bind=True,
            )

            # Find user
            search_filter = self.user_search_filter.format(username=username)
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                attributes=["distinguishedName"],
            )

            if not conn.entries:
                return None

            user_dn = conn.entries[0].entry_dn
            groups = self._get_user_groups(user_dn)
            role = self._determine_user_role(groups)

            conn.unbind()
            return role

        except LDAPException as e:
            logger.error("Error in group sync", error=str(e), username=username)
            return None
        finally:
            if conn and conn.bound:
                conn.unbind()

    async def test_connection(self) -> bool:
        """Test LDAP connection with service account"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._test_connection_sync)
        except Exception as e:
            logger.error("LDAP connection test failed", error=str(e))
            return False

    def _test_connection_sync(self) -> bool:
        """Synchronous connection test"""
        conn = None
        try:
            conn = Connection(
                self.server,
                user=self.bind_dn,
                password=self.bind_password,
                authentication=SIMPLE if self.auth_type == "SIMPLE" else NTLM,
                auto_bind=True,
            )

            # Try a simple search
            conn.search(
                search_base=self.base_dn,
                search_filter="(objectClass=*)",
                search_scope=ldap3.BASE,
                attributes=["*"],
            )

            conn.unbind()
            logger.info("LDAP connection test successful")
            return True

        except LDAPException as e:
            logger.error("LDAP connection test failed", error=str(e))
            return False
        finally:
            if conn and conn.bound:
                conn.unbind()


@lru_cache()
def get_ldap_service() -> LDAPService:
    """Get singleton LDAP service instance"""
    return LDAPService()
