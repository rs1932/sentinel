"""
User management service for Module 3
Handles all user CRUD operations and user lifecycle management
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.orm import selectinload
import uuid
import secrets
import logging

from ..models.user import User
from ..models.tenant import Tenant
from ..schemas.user import (
    UserCreate, UserUpdate, UserQuery, UserResponse, UserDetailResponse, 
    UserListResponse, UserPermissionsResponse, BulkOperationType,
    UserBulkOperation, BulkOperationResponse, PasswordChange
)
from ..utils.password import password_manager
from ..core.exceptions import (
    NotFoundError, ValidationError, ConflictError, AuthenticationError
)
from ..utils.tenant_context import get_current_tenant_id

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.password_manager = password_manager
    
    async def create_user(
        self, 
        user_data: UserCreate, 
        tenant_id: Optional[UUID] = None,
        creator_id: Optional[UUID] = None
    ) -> UserResponse:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            tenant_id: Tenant ID (from context if not provided)
            creator_id: ID of user creating this user (for audit)
            
        Returns:
            UserResponse: Created user data
        """
        # Use tenant from context if not provided
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        # Validate tenant exists and is active
        tenant = await self._get_active_tenant(tenant_id)
        
        # Check if user already exists with this email in tenant
        existing_user = await self._get_user_by_email(user_data.email, tenant_id)
        if existing_user:
            raise ConflictError(f"User with email {user_data.email} already exists in this tenant")
        
        # Check username uniqueness in tenant if provided
        if user_data.username:
            existing_username = await self._get_user_by_username(user_data.username, tenant_id)
            if existing_username:
                raise ConflictError(f"Username {user_data.username} already exists in this tenant")
        
        # Hash password if provided
        password_hash = None
        if user_data.password:
            password_hash = self.password_manager.hash_password(user_data.password)
        
        # Create user instance
        user = User(
            tenant_id=tenant_id,
            email=user_data.email.lower(),
            username=user_data.username,
            password_hash=password_hash,
            attributes=user_data.attributes or {},
            preferences=user_data.preferences or {},
            is_active=user_data.is_active,
            is_service_account=False  # Regular users are not service accounts
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"User created: {user.id} ({user.email}) in tenant {tenant_id}")
        
        # TODO: Send invitation email if send_invitation is True
        if user_data.send_invitation:
            await self._send_invitation_email(user)
        
        return UserResponse.from_orm(user)
    
    async def get_user(self, user_id: UUID, tenant_id: Optional[UUID] = None) -> UserDetailResponse:
        """
        Get user by ID with detailed information
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            UserDetailResponse: User details
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        return UserDetailResponse.from_orm(user)
    
    async def list_users(
        self, 
        query_params: UserQuery, 
        tenant_id: Optional[UUID] = None
    ) -> UserListResponse:
        """
        List users with filtering and pagination
        
        Args:
            query_params: Query parameters for filtering and pagination
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            UserListResponse: Paginated list of users
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        # Base query
        query = select(User).where(
            and_(
                User.tenant_id == tenant_id,
                User.is_service_account == False  # Only regular users
            )
        )
        
        # Apply filters
        if query_params.is_active is not None:
            query = query.where(User.is_active == query_params.is_active)
        
        if query_params.search:
            search_term = f"%{query_params.search.lower()}%"
            query = query.where(
                or_(
                    func.lower(User.email).like(search_term),
                    func.lower(User.username).like(search_term)
                )
            )
        
        # TODO: Add role and group filtering when those modules are implemented
        
        # Count total results
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_column = getattr(User, query_params.sort.value)
        if query_params.order.value == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (query_params.page - 1) * query_params.limit
        query = query.offset(offset).limit(query_params.limit)
        
        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Convert to response models
        user_responses = [UserResponse.from_orm(user) for user in users]
        
        return UserListResponse(
            items=user_responses,
            total=total,
            page=query_params.page,
            limit=query_params.limit,
            pages=(total + query_params.limit - 1) // query_params.limit
        )
    
    async def update_user(
        self, 
        user_id: UUID, 
        user_data: UserUpdate, 
        tenant_id: Optional[UUID] = None,
        updater_id: Optional[UUID] = None
    ) -> UserResponse:
        """
        Update user information
        
        Args:
            user_id: User ID to update
            user_data: Updated user data
            tenant_id: Tenant ID (from context if not provided)
            updater_id: ID of user making the update (for audit)
            
        Returns:
            UserResponse: Updated user data
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Check email uniqueness if being changed
        if user_data.email and user_data.email.lower() != user.email:
            existing_user = await self._get_user_by_email(user_data.email, tenant_id)
            if existing_user and existing_user.id != user_id:
                raise ConflictError(f"User with email {user_data.email} already exists")
        
        # Check username uniqueness if being changed
        if user_data.username and user_data.username != user.username:
            existing_username = await self._get_user_by_username(user_data.username, tenant_id)
            if existing_username and existing_username.id != user_id:
                raise ConflictError(f"Username {user_data.username} already exists")
        
        # Update fields
        update_data = {}
        if user_data.email:
            update_data['email'] = user_data.email.lower()
        if user_data.username is not None:
            update_data['username'] = user_data.username
        if user_data.attributes is not None:
            update_data['attributes'] = user_data.attributes
        if user_data.preferences is not None:
            update_data['preferences'] = user_data.preferences
        if user_data.is_active is not None:
            update_data['is_active'] = user_data.is_active
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
            )
            await self.db.commit()
        
        # Refresh user data
        await self.db.refresh(user)
        
        logger.info(f"User updated: {user_id} by {updater_id}")
        
        return UserResponse.from_orm(user)
    
    async def delete_user(
        self, 
        user_id: UUID, 
        tenant_id: Optional[UUID] = None,
        soft_delete: bool = True
    ) -> None:
        """
        Delete user (soft delete by default)
        
        Args:
            user_id: User ID to delete
            tenant_id: Tenant ID (from context if not provided)  
            soft_delete: Whether to soft delete (deactivate) or hard delete
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        if soft_delete:
            # Soft delete by deactivating
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            logger.info(f"User soft deleted: {user_id}")
        else:
            # Hard delete
            await self.db.execute(delete(User).where(User.id == user_id))
            logger.info(f"User hard deleted: {user_id}")
        
        await self.db.commit()
    
    async def change_password(
        self,
        user_id: UUID,
        password_data: PasswordChange,
        tenant_id: Optional[UUID] = None
    ) -> None:
        """
        Change user password
        
        Args:
            user_id: User ID
            password_data: Current and new password data
            tenant_id: Tenant ID (from context if not provided)
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Verify current password
        if not user.password_hash:
            raise ValidationError("User does not have password authentication enabled")
        
        if not self.password_manager.verify_password(password_data.current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Hash new password
        new_password_hash = self.password_manager.hash_password(password_data.new_password)
        
        # Update password
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=new_password_hash, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        logger.info(f"Password changed for user: {user_id}")
    
    async def admin_reset_password(
        self,
        user_id: UUID,
        new_password: str,
        tenant_id: Optional[UUID] = None,
        admin_user_id: Optional[UUID] = None
    ) -> None:
        """
        Admin password reset - doesn't require current password
        
        Args:
            user_id: User ID whose password to reset
            new_password: New password to set
            tenant_id: Tenant ID (from context if not provided)
            admin_user_id: ID of admin performing the reset
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # Hash new password
        new_password_hash = self.password_manager.hash_password(new_password)
        
        # Update password
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=new_password_hash, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        logger.info(f"Password reset by admin {admin_user_id} for user: {user_id}")
    
    async def lock_user(self, user_id: UUID, duration_minutes: int = 30, tenant_id: Optional[UUID] = None) -> None:
        """
        Lock user account for specified duration
        
        Args:
            user_id: User ID to lock
            duration_minutes: Lock duration in minutes
            tenant_id: Tenant ID (from context if not provided)
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(locked_until=locked_until, updated_at=datetime.utcnow())
        )
        await self.db.commit()
        
        logger.info(f"User locked: {user_id} until {locked_until}")
    
    async def unlock_user(self, user_id: UUID, tenant_id: Optional[UUID] = None) -> None:
        """
        Unlock user account
        
        Args:
            user_id: User ID to unlock
            tenant_id: Tenant ID (from context if not provided)
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                locked_until=None,
                failed_login_count=0,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        logger.info(f"User unlocked: {user_id}")
    
    async def bulk_operation(
        self,
        bulk_data: UserBulkOperation,
        tenant_id: Optional[UUID] = None,
        operator_id: Optional[UUID] = None
    ) -> BulkOperationResponse:
        """
        Perform bulk operations on users
        
        Args:
            bulk_data: Bulk operation data
            tenant_id: Tenant ID (from context if not provided)
            operator_id: ID of user performing operation (for audit)
            
        Returns:
            BulkOperationResponse: Operation results
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        successful = 0
        failed = 0
        failed_ids = []
        errors = []
        
        for user_id in bulk_data.user_ids:
            try:
                if bulk_data.operation == BulkOperationType.activate:
                    await self._bulk_activate_user(user_id, tenant_id)
                elif bulk_data.operation == BulkOperationType.deactivate:
                    await self._bulk_deactivate_user(user_id, tenant_id)
                elif bulk_data.operation == BulkOperationType.delete:
                    await self.delete_user(user_id, tenant_id, soft_delete=True)
                elif bulk_data.operation == BulkOperationType.assign_role:
                    # TODO: Implement when role system is available
                    raise NotImplementedError("Role assignment not yet implemented")
                elif bulk_data.operation == BulkOperationType.remove_role:
                    # TODO: Implement when role system is available
                    raise NotImplementedError("Role removal not yet implemented")
                
                successful += 1
                
            except Exception as e:
                failed += 1
                failed_ids.append(user_id)
                errors.append(f"User {user_id}: {str(e)}")
                logger.error(f"Bulk operation failed for user {user_id}: {e}")
        
        await self.db.commit()
        
        logger.info(f"Bulk operation {bulk_data.operation}: {successful} successful, {failed} failed")
        
        return BulkOperationResponse(
            operation=bulk_data.operation,
            total_requested=len(bulk_data.user_ids),
            successful=successful,
            failed=failed,
            failed_ids=failed_ids,
            errors=errors
        )
    
    async def get_user_by_email(self, email: str, tenant_id: Optional[UUID] = None) -> Optional[UserDetailResponse]:
        """
        Get user by email address
        
        Args:
            email: User email
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            Optional[UserDetailResponse]: User details if found
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_email(email, tenant_id)
        if not user:
            return None
        
        return UserDetailResponse.from_orm(user)
    
    async def get_user_permissions(self, user_id: UUID, tenant_id: Optional[UUID] = None) -> UserPermissionsResponse:
        """
        Get user permissions (placeholder for future role/permission integration)
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID (from context if not provided)
            
        Returns:
            UserPermissionsResponse: User permissions
        """
        if not tenant_id:
            tenant_id = get_current_tenant_id()
        
        user = await self._get_user_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        # TODO: Implement actual permission resolution when role system is available
        return UserPermissionsResponse(
            user_id=user_id,
            tenant_id=tenant_id,
            direct_permissions=[],
            inherited_permissions=[],
            effective_permissions=[]
        )
    
    # Private helper methods
    
    async def _get_active_tenant(self, tenant_id: UUID) -> Tenant:
        """Get active tenant by ID"""
        result = await self.db.execute(
            select(Tenant).where(
                and_(Tenant.id == tenant_id, Tenant.is_active == True)
            )
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant {tenant_id} not found or inactive")
        return tenant
    
    async def _get_user_by_id(self, user_id: UUID, tenant_id: UUID) -> Optional[User]:
        """Get user by ID and tenant"""
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.id == user_id,
                    User.tenant_id == tenant_id,
                    User.is_service_account == False
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_email(self, email: str, tenant_id: UUID) -> Optional[User]:
        """Get user by email and tenant"""
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.email == email.lower(),
                    User.tenant_id == tenant_id,
                    User.is_service_account == False
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_username(self, username: str, tenant_id: UUID) -> Optional[User]:
        """Get user by username and tenant"""
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.username == username,
                    User.tenant_id == tenant_id,
                    User.is_service_account == False
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _bulk_activate_user(self, user_id: UUID, tenant_id: UUID) -> None:
        """Activate user in bulk operation"""
        await self.db.execute(
            update(User)
            .where(and_(User.id == user_id, User.tenant_id == tenant_id))
            .values(is_active=True, updated_at=datetime.utcnow())
        )
    
    async def _bulk_deactivate_user(self, user_id: UUID, tenant_id: UUID) -> None:
        """Deactivate user in bulk operation"""
        await self.db.execute(
            update(User)
            .where(and_(User.id == user_id, User.tenant_id == tenant_id))
            .values(is_active=False, updated_at=datetime.utcnow())
        )
    
    async def _send_invitation_email(self, user: User) -> None:
        """Send invitation email to user (placeholder)"""
        # TODO: Implement email invitation system
        logger.info(f"Invitation email would be sent to {user.email}")
        pass