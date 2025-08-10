#!/usr/bin/env python3
"""
Logistics Industry Seed Data Script

Seeds the database with realistic logistics industry test data including:
- 3 logistics company tenants (Maritime, Air Cargo, Ground)
- Industry-specific roles and permissions
- Departmental groups with role assignments
- Hierarchical resources representing logistics operations
- User accounts for testing various scenarios

Designed for testing dynamic RBAC system with real-world logistics scenarios.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

# Add backend root to Python path for imports
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import engine
from src.models import *
from src.models.resource import ResourceType
from src.utils.password import password_manager


class LogisticsDataSeeder:
    """Seed logistics industry test data for RBAC testing."""
    
    def __init__(self):
        self.engine = None
        self.created_entities = {
            "tenants": {},
            "users": {},
            "roles": {},
            "groups": {},
            "permissions": {},
            "resources": {}
        }
    
    async def initialize(self):
        """Initialize database connection."""
        self.engine = engine
    
    async def create_logistics_tenants(self, session: AsyncSession) -> Dict[str, Tenant]:
        """Create 3 logistics company tenants."""
        print("🏢 Creating logistics company tenants...")
        
        tenant_data = [
            {
                "name": "Maritime Port Operations",
                "code": "MARITIME",
                "domain": "maritime.logistics.com",
                "description": "Global port and vessel management operations",
                "industry": "Maritime Logistics",
                "headquarters": "Singapore"
            },
            {
                "name": "AirCargo Express", 
                "code": "AIRCARGO",
                "domain": "aircargo.express.com",
                "description": "International air freight and cargo handling",
                "industry": "Air Cargo",
                "headquarters": "Frankfurt"
            },
            {
                "name": "GroundLink Logistics",
                "code": "GROUNDLINK", 
                "domain": "groundlink.logistics.com",
                "description": "Warehousing and ground transportation services",
                "industry": "Ground Logistics",
                "headquarters": "Memphis"
            }
        ]
        
        tenants = {}
        for data in tenant_data:
            tenant = Tenant(
                name=data["name"],
                code=data["code"],
                type="root",
                isolation_mode="shared",
                tenant_metadata={
                    "domain": data["domain"],
                    "description": data["description"],
                    "industry": data["industry"],
                    "headquarters": data["headquarters"],
                    "currency": "USD",
                    "timezone": "UTC"
                },
                is_active=True
            )
            
            session.add(tenant)
            await session.flush()  # Get ID
            
            tenants[data["code"]] = tenant
            self.created_entities["tenants"][data["code"]] = tenant
            print(f"  ✅ Created tenant: {tenant.name} ({tenant.code})")
        
        await session.commit()
        return tenants
    
    async def create_industry_roles(self, session: AsyncSession, tenants: Dict[str, Tenant]) -> Dict[str, Dict[str, Role]]:
        """Create industry-specific roles for each tenant."""
        print("👤 Creating industry-specific roles...")
        
        role_definitions = {
            "MARITIME": [
                {"name": "Port Manager", "description": "Oversees port operations and vessel coordination", "priority": 90},
                {"name": "Vessel Coordinator", "description": "Manages vessel schedules and berth assignments", "priority": 70},
                {"name": "Customs Officer", "description": "Handles customs clearance and compliance", "priority": 80},
                {"name": "Terminal Supervisor", "description": "Supervises terminal operations and staff", "priority": 60},
                {"name": "Maritime Security", "description": "Port security and safety oversight", "priority": 75},
                {"name": "Dock Worker", "description": "Cargo handling and dock operations", "priority": 30},
            ],
            "AIRCARGO": [
                {"name": "Operations Manager", "description": "Air cargo operations oversight", "priority": 90},
                {"name": "Flight Coordinator", "description": "Flight scheduling and cargo manifest management", "priority": 75},
                {"name": "Cargo Handler", "description": "Physical cargo handling and loading", "priority": 40},
                {"name": "Security Inspector", "description": "Cargo security screening and compliance", "priority": 80},
                {"name": "Ground Services Coordinator", "description": "Ground support equipment and services", "priority": 65},
                {"name": "Freight Forwarder", "description": "Customer service and shipment coordination", "priority": 50},
            ],
            "GROUNDLINK": [
                {"name": "Warehouse Manager", "description": "Warehouse operations and inventory management", "priority": 85},
                {"name": "Logistics Coordinator", "description": "Transportation planning and route optimization", "priority": 70},
                {"name": "Fleet Manager", "description": "Vehicle fleet management and maintenance", "priority": 75},
                {"name": "Inventory Controller", "description": "Stock management and cycle counting", "priority": 60},
                {"name": "Compliance Officer", "description": "Regulatory compliance and documentation", "priority": 80},
                {"name": "Warehouse Associate", "description": "Order fulfillment and material handling", "priority": 35},
            ]
        }
        
        tenant_roles = {}
        
        for tenant_code, tenant in tenants.items():
            tenant_roles[tenant_code] = {}
            roles = role_definitions[tenant_code]
            
            for role_data in roles:
                role = Role(
                    tenant_id=tenant.id,
                    name=role_data["name"],
                    display_name=role_data["name"],
                    description=role_data["description"],
                    type=RoleType.CUSTOM,
                    priority=role_data["priority"],
                    is_assignable=True,
                    role_metadata={
                        "industry": tenant.tenant_metadata.get("industry"),
                        "department": self._get_role_department(role_data["name"]),
                        "access_level": self._get_access_level(role_data["priority"])
                    }
                )
                
                session.add(role)
                await session.flush()
                
                tenant_roles[tenant_code][role_data["name"]] = role
                self.created_entities["roles"][f"{tenant_code}_{role_data['name']}"] = role
                print(f"  ✅ Created role: {role.name} for {tenant.name}")
        
        await session.commit()
        return tenant_roles
    
    def _get_role_department(self, role_name: str) -> str:
        """Determine department based on role name."""
        department_mapping = {
            "Manager": "Management",
            "Coordinator": "Operations", 
            "Officer": "Compliance",
            "Security": "Security",
            "Supervisor": "Operations",
            "Worker": "Operations",
            "Handler": "Operations",
            "Inspector": "Security",
            "Forwarder": "Customer Service",
            "Controller": "Operations",
            "Associate": "Operations"
        }
        
        for key, dept in department_mapping.items():
            if key.lower() in role_name.lower():
                return dept
        
        return "General"
    
    def _get_access_level(self, priority: int) -> str:
        """Determine access level based on role priority."""
        if priority >= 80:
            return "high"
        elif priority >= 60:
            return "medium"
        else:
            return "standard"
    
    async def create_departmental_groups(self, session: AsyncSession, tenants: Dict[str, Tenant]) -> Dict[str, Dict[str, Group]]:
        """Create departmental groups for each tenant."""
        print("👥 Creating departmental groups...")
        
        departments = [
            {"name": "Management", "description": "Senior management and executive staff"},
            {"name": "Operations", "description": "Day-to-day operational staff"},
            {"name": "Security", "description": "Security and compliance personnel"},
            {"name": "Customer Service", "description": "Customer-facing staff"},
            {"name": "Compliance", "description": "Regulatory compliance team"}
        ]
        
        tenant_groups = {}
        
        for tenant_code, tenant in tenants.items():
            tenant_groups[tenant_code] = {}
            
            for dept_data in departments:
                group = Group(
                    tenant_id=tenant.id,
                    name=dept_data["name"],
                    display_name=f"{dept_data['name']} - {tenant.name}",
                    description=dept_data["description"],
                    group_metadata={
                        "department_type": dept_data["name"].lower(),
                        "tenant_industry": tenant.tenant_metadata.get("industry")
                    },
                    is_active=True
                )
                
                session.add(group)
                await session.flush()
                
                tenant_groups[tenant_code][dept_data["name"]] = group
                self.created_entities["groups"][f"{tenant_code}_{dept_data['name']}"] = group
                print(f"  ✅ Created group: {group.name}")
        
        await session.commit()
        return tenant_groups
    
    async def create_logistics_resources(self, session: AsyncSession, tenants: Dict[str, Tenant]) -> Dict[str, Dict[str, Resource]]:
        """Create hierarchical resources representing logistics operations."""
        print("📦 Creating logistics resource hierarchy...")
        
        resource_hierarchies = {
            "MARITIME": {
                "app": {"name": "Port Management System", "code": "PMS"},
                "capabilities": [
                    {"name": "Vessel Operations", "code": "VESSEL_OPS", "services": [
                        {"name": "Berth Assignment", "code": "BERTH_ASSIGN"},
                        {"name": "Cargo Manifest", "code": "CARGO_MANIFEST"},
                        {"name": "Customs Processing", "code": "CUSTOMS_PROC"}
                    ]},
                    {"name": "Terminal Management", "code": "TERMINAL_MGMT", "services": [
                        {"name": "Equipment Tracking", "code": "EQUIP_TRACK"},
                        {"name": "Worker Scheduling", "code": "WORKER_SCHED"}
                    ]}
                ]
            },
            "AIRCARGO": {
                "app": {"name": "Air Cargo System", "code": "ACS"},
                "capabilities": [
                    {"name": "Flight Operations", "code": "FLIGHT_OPS", "services": [
                        {"name": "Cargo Loading", "code": "CARGO_LOAD"},
                        {"name": "Flight Planning", "code": "FLIGHT_PLAN"},
                        {"name": "Security Screening", "code": "SEC_SCREEN"}
                    ]},
                    {"name": "Ground Services", "code": "GROUND_SVCS", "services": [
                        {"name": "GSE Management", "code": "GSE_MGMT"},
                        {"name": "Fuel Services", "code": "FUEL_SVCS"}
                    ]}
                ]
            },
            "GROUNDLINK": {
                "app": {"name": "Ground Operations", "code": "GROUND_OPS"},
                "capabilities": [
                    {"name": "Warehouse Management", "code": "WMS", "services": [
                        {"name": "Inventory Tracking", "code": "INV_TRACK"},
                        {"name": "Order Fulfillment", "code": "ORDER_FULFILL"},
                        {"name": "Quality Control", "code": "QC"}
                    ]},
                    {"name": "Fleet Management", "code": "FLEET_MGMT", "services": [
                        {"name": "Vehicle Tracking", "code": "VEH_TRACK"},
                        {"name": "Route Optimization", "code": "ROUTE_OPT"}
                    ]}
                ]
            }
        }
        
        tenant_resources = {}
        
        # First create the Product Family (shared)
        product_family = Resource(
            tenant_id=list(tenants.values())[0].id,  # Use first tenant for product family
            type=ResourceType.PRODUCT_FAMILY,
            name="Logistics Platform",
            code="LOGISTICS_PLATFORM",
            attributes={"description": "Comprehensive logistics management platform"},
            is_active=True,
            path="/pf/"
        )
        session.add(product_family)
        await session.flush()
        product_family.path = f"/{product_family.id}/"
        
        print(f"  ✅ Created product family: {product_family.name}")
        
        for tenant_code, tenant in tenants.items():
            tenant_resources[tenant_code] = {"product_family": product_family}
            hierarchy = resource_hierarchies[tenant_code]
            
            # Create App
            app = Resource(
                tenant_id=tenant.id,
                type=ResourceType.APP,
                name=hierarchy["app"]["name"],
                code=hierarchy["app"]["code"],
                parent_id=product_family.id,
                path=f"{product_family.path}{uuid.uuid4()}/",
                attributes={"tenant_industry": tenant.tenant_metadata.get("industry")},
                is_active=True
            )
            session.add(app)
            await session.flush()
            app.path = f"{product_family.path}{app.id}/"
            
            tenant_resources[tenant_code]["app"] = app
            print(f"  ✅ Created app: {app.name}")
            
            # Create Capabilities and Services
            for cap_data in hierarchy["capabilities"]:
                capability = Resource(
                    tenant_id=tenant.id,
                    type=ResourceType.CAPABILITY,
                    name=cap_data["name"],
                    code=cap_data["code"],
                    parent_id=app.id,
                    path=f"{app.path}{uuid.uuid4()}/",
                    attributes={"capability_type": cap_data["code"].lower()},
                    is_active=True
                )
                session.add(capability)
                await session.flush()
                capability.path = f"{app.path}{capability.id}/"
                
                tenant_resources[tenant_code][cap_data["code"]] = capability
                print(f"    ✅ Created capability: {capability.name}")
                
                # Create Services
                for svc_data in cap_data["services"]:
                    service = Resource(
                        tenant_id=tenant.id,
                        type=ResourceType.SERVICE,
                        name=svc_data["name"],
                        code=svc_data["code"],
                        parent_id=capability.id,
                        path=f"{capability.path}{uuid.uuid4()}/",
                        attributes={"service_type": svc_data["code"].lower()},
                        is_active=True
                    )
                    session.add(service)
                    await session.flush()
                    service.path = f"{capability.path}{service.id}/"
                    
                    tenant_resources[tenant_code][svc_data["code"]] = service
                    print(f"      ✅ Created service: {service.name}")
        
        await session.commit()
        return tenant_resources
    
    async def create_permissions_and_assign_roles(self, session: AsyncSession, 
                                                 tenants: Dict[str, Tenant], 
                                                 tenant_roles: Dict[str, Dict[str, Role]],
                                                 tenant_resources: Dict[str, Dict[str, Resource]]):
        """Create permissions and assign them to roles based on access patterns."""
        print("🔐 Creating permissions and role assignments...")
        
        # Permission templates for different resource types
        permission_templates = {
            "management": ["create", "read", "update", "delete"],
            "operations": ["create", "read", "update"],  
            "security": ["read", "update"],
            "standard": ["read"]
        }
        
        for tenant_code, tenant in tenants.items():
            roles = tenant_roles[tenant_code]
            resources = tenant_resources[tenant_code]
            
            # Create permissions for each resource
            for resource_key, resource in resources.items():
                if resource_key == "product_family":
                    continue  # Skip product family for tenant-specific permissions
                
                # Determine which roles should have access to this resource
                role_permissions = self._get_role_permissions_for_resource(resource, roles)
                
                for role_name, permission_level in role_permissions.items():
                    if role_name not in roles:
                        continue
                    
                    role = roles[role_name]
                    actions = permission_templates[permission_level]
                    
                    # Create permission
                    permission = Permission(
                        tenant_id=tenant.id,
                        name=f"{resource.code}_{permission_level}",
                        resource_type=resource.type,
                        resource_id=resource.id,
                        resource_path=resource.path,
                        actions=actions,
                        conditions={
                            "tenant_isolation": True,
                            "time_based": False
                        },
                        field_permissions={
                            "sensitive_fields": permission_level in ["management", "security"]
                        },
                        is_active=True
                    )
                    
                    session.add(permission)
                    await session.flush()
                    
                    # Create role-permission assignment
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                        granted_at=datetime.now(timezone.utc)
                    )
                    
                    session.add(role_permission)
                    
                    print(f"    ✅ Assigned {permission_level} permission on {resource.name} to {role_name}")
        
        await session.commit()
    
    def _get_role_permissions_for_resource(self, resource: Resource, roles: Dict[str, Role]) -> Dict[str, str]:
        """Determine which roles should have what level of access to a resource."""
        resource_code = resource.code.lower()
        permissions = {}
        
        # Management roles get full access
        for role_name in roles.keys():
            role_name_lower = role_name.lower()
            
            if "manager" in role_name_lower:
                permissions[role_name] = "management"
            elif "coordinator" in role_name_lower or "supervisor" in role_name_lower:
                permissions[role_name] = "operations"
            elif "officer" in role_name_lower or "security" in role_name_lower or "inspector" in role_name_lower:
                permissions[role_name] = "security"
            else:
                permissions[role_name] = "standard"
        
        # Resource-specific access patterns
        if "security" in resource_code or "customs" in resource_code:
            # Only security roles get full access to security resources
            filtered_permissions = {}
            for role_name, level in permissions.items():
                if "security" in role_name.lower() or "officer" in role_name.lower() or "inspector" in role_name.lower():
                    filtered_permissions[role_name] = level
                elif "manager" in role_name.lower():
                    filtered_permissions[role_name] = "security"  # Managers get read/update
            permissions = filtered_permissions
        
        return permissions
    
    async def assign_roles_to_groups(self, session: AsyncSession, 
                                   tenant_roles: Dict[str, Dict[str, Role]], 
                                   tenant_groups: Dict[str, Dict[str, Group]]):
        """Assign roles to appropriate departmental groups."""
        print("🔗 Assigning roles to departmental groups...")
        
        role_to_group_mapping = {
            "Manager": "Management",
            "Coordinator": "Operations",
            "Supervisor": "Operations", 
            "Officer": "Compliance",
            "Security": "Security",
            "Inspector": "Security",
            "Worker": "Operations",
            "Handler": "Operations",
            "Forwarder": "Customer Service",
            "Controller": "Operations",
            "Associate": "Operations"
        }
        
        for tenant_code in tenant_roles.keys():
            roles = tenant_roles[tenant_code]
            groups = tenant_groups[tenant_code]
            
            for role_name, role in roles.items():
                # Find appropriate group for this role
                group_name = None
                for role_key, group_key in role_to_group_mapping.items():
                    if role_key.lower() in role_name.lower():
                        group_name = group_key
                        break
                
                if group_name and group_name in groups:
                    group = groups[group_name]
                    
                    # Create group-role assignment
                    group_role = GroupRole(
                        group_id=group.id,
                        role_id=role.id,
                        granted_at=datetime.now(timezone.utc)
                    )
                    
                    session.add(group_role)
                    print(f"    ✅ Assigned {role_name} to {group_name} group in {tenant_code}")
        
        await session.commit()
    
    async def create_test_users(self, session: AsyncSession, 
                               tenants: Dict[str, Tenant],
                               tenant_roles: Dict[str, Dict[str, Role]],
                               tenant_groups: Dict[str, Dict[str, Group]]):
        """Create test users for each tenant with realistic assignments."""
        print("👨‍💼 Creating test users...")
        
        # Test user templates for each tenant
        user_templates = {
            "MARITIME": [
                {"email": "port.manager@maritime.com", "name": "Sarah Thompson", "role": "Port Manager", "groups": ["Management"]},
                {"email": "vessel.coord@maritime.com", "name": "Marcus Chen", "role": "Vessel Coordinator", "groups": ["Operations"]},
                {"email": "customs.officer@maritime.com", "name": "Ahmed Hassan", "role": "Customs Officer", "groups": ["Compliance", "Security"]},
                {"email": "dock.worker@maritime.com", "name": "Jose Rodriguez", "role": "Dock Worker", "groups": ["Operations"]}
            ],
            "AIRCARGO": [
                {"email": "ops.manager@aircargo.com", "name": "Lisa Wagner", "role": "Operations Manager", "groups": ["Management"]},
                {"email": "flight.coord@aircargo.com", "name": "David Kim", "role": "Flight Coordinator", "groups": ["Operations"]},
                {"email": "security.inspector@aircargo.com", "name": "Emma Johnson", "role": "Security Inspector", "groups": ["Security"]},
                {"email": "cargo.handler@aircargo.com", "name": "Carlos Mendez", "role": "Cargo Handler", "groups": ["Operations"]}
            ],
            "GROUNDLINK": [
                {"email": "warehouse.mgr@groundlink.com", "name": "Michael O'Connor", "role": "Warehouse Manager", "groups": ["Management"]},
                {"email": "logistics.coord@groundlink.com", "name": "Priya Patel", "role": "Logistics Coordinator", "groups": ["Operations"]},
                {"email": "compliance.officer@groundlink.com", "name": "Jennifer Lee", "role": "Compliance Officer", "groups": ["Compliance"]},
                {"email": "warehouse.associate@groundlink.com", "name": "Robert Johnson", "role": "Warehouse Associate", "groups": ["Operations"]}
            ]
        }
        
        default_password = "LogisticsTest2024!"
        hashed_password = password_manager.hash_password(default_password)
        
        for tenant_code, tenant in tenants.items():
            users_data = user_templates[tenant_code]
            roles = tenant_roles[tenant_code]
            groups = tenant_groups[tenant_code]
            
            for user_data in users_data:
                # Create user
                user = User(
                    tenant_id=tenant.id,
                    email=user_data["email"],
                    username=user_data["email"].split("@")[0],
                    password_hash=hashed_password,
                    is_active=True,
                    attributes={
                        "first_name": user_data["name"].split()[0],
                        "last_name": user_data["name"].split()[-1],
                        "display_name": user_data["name"],
                        "email_verified": True,
                        "department": self._get_role_department(user_data["role"]),
                        "test_account": True,
                        "default_password": default_password
                    }
                )
                
                session.add(user)
                await session.flush()
                
                # Assign role
                if user_data["role"] in roles:
                    role = roles[user_data["role"]]
                    user_role = UserRole(
                        user_id=user.id,
                        role_id=role.id,
                        granted_at=datetime.now(timezone.utc),
                        is_active=True
                    )
                    session.add(user_role)
                
                # Assign to groups
                for group_name in user_data["groups"]:
                    if group_name in groups:
                        group = groups[group_name]
                        user_group = UserGroup(
                            user_id=user.id,
                            group_id=group.id,
                            added_at=datetime.now(timezone.utc)
                        )
                        session.add(user_group)
                
                self.created_entities["users"][f"{tenant_code}_{user_data['email']}"] = user
                display_name = user.attributes.get("display_name", user.email)
                print(f"    ✅ Created user: {display_name} ({user.email}) - {user_data['role']}")
        
        await session.commit()
        print(f"\n🔑 All test users created with password: {default_password}")
    
    async def generate_summary_report(self, session: AsyncSession):
        """Generate a summary report of seeded data."""
        print("\n" + "="*60)
        print("📊 LOGISTICS INDUSTRY SEED DATA SUMMARY")
        print("="*60)
        
        # Count statistics
        stats = {}
        for entity_type in ["tenants", "users", "roles", "groups", "permissions", "resources"]:
            table_name = f"sentinel.{entity_type}"
            if entity_type == "permissions":
                table_name = "sentinel.permissions"
            
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            stats[entity_type] = result.scalar()
        
        print(f"\n📈 Entity Counts:")
        for entity_type, count in stats.items():
            print(f"  {entity_type.title()}: {count}")
        
        print(f"\n🏢 Tenants Created:")
        for tenant_code, tenant in self.created_entities["tenants"].items():
            print(f"  {tenant.name} ({tenant.code}) - {tenant.tenant_metadata.get('industry', 'Unknown')}")
        
        print(f"\n👥 Sample Users (Password: LogisticsTest2024!):")
        sample_users = list(self.created_entities["users"].values())[:6]
        for user in sample_users:
            display_name = user.attributes.get("display_name", user.email)
            print(f"  {user.email} - {display_name}")
        
        print(f"\n📦 Resource Hierarchy:")
        print("  Logistics Platform (Product Family)")
        for tenant_code in ["MARITIME", "AIRCARGO", "GROUNDLINK"]:
            tenant = self.created_entities["tenants"][tenant_code]
            print(f"    └── {tenant.name}")
            print(f"        ├── Port/Cargo/Warehouse Management")
            print(f"        │   ├── Operations Capability")
            print(f"        │   └── Management Services")
        
        print(f"\n🔐 RBAC Configuration:")
        print("  ✅ Role-based permissions assigned")
        print("  ✅ Group-based role inheritance configured")
        print("  ✅ Resource-level access control implemented")
        print("  ✅ Industry-specific permission patterns applied")
        
        print(f"\n🧪 Testing Scenarios Enabled:")
        print("  • Cross-tenant permission isolation")
        print("  • Role hierarchy and inheritance") 
        print("  • Group-based access patterns")
        print("  • Resource-level granular permissions")
        print("  • Industry-specific workflow testing")
        
        print(f"\n✅ Database seeding completed successfully!")
        print("Ready for dynamic RBAC testing with realistic logistics scenarios.")
    
    async def run_seeding(self):
        """Run the complete seeding process."""
        print("🌱 Starting logistics industry data seeding...")
        
        await self.initialize()
        
        async with AsyncSession(self.engine) as session:
            try:
                # Create tenants
                tenants = await self.create_logistics_tenants(session)
                
                # Create roles 
                tenant_roles = await self.create_industry_roles(session, tenants)
                
                # Create groups
                tenant_groups = await self.create_departmental_groups(session, tenants)
                
                # Create resources
                tenant_resources = await self.create_logistics_resources(session, tenants)
                
                # Create permissions and assign to roles
                await self.create_permissions_and_assign_roles(session, tenants, tenant_roles, tenant_resources)
                
                # Assign roles to groups
                await self.assign_roles_to_groups(session, tenant_roles, tenant_groups)
                
                # Create test users
                await self.create_test_users(session, tenants, tenant_roles, tenant_groups)
                
                # Generate summary
                await self.generate_summary_report(session)
                
            except Exception as e:
                print(f"❌ Error during seeding: {e}")
                await session.rollback()
                raise
        
        await self.engine.dispose()


async def main():
    """Main entry point for seeding logistics data."""
    print("=" * 60)
    print("🌱 LOGISTICS INDUSTRY DATA SEEDER")
    print("=" * 60)
    
    seeder = LogisticsDataSeeder()
    await seeder.run_seeding()


if __name__ == "__main__":
    # Check database environment
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    asyncio.run(main())