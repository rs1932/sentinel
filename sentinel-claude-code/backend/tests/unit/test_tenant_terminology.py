import pytest
from datetime import datetime
from uuid import uuid4

from src.models.tenant import Tenant, TenantType


class TestTenantTerminology:
    """Test terminology methods on Tenant model"""
    
    def test_get_terminology_config_empty(self):
        """Test getting terminology config when none is set"""
        tenant = Tenant(name="Test Tenant", code="TEST", type=TenantType.ROOT)
        
        config = tenant.get_terminology_config()
        assert config == {}
    
    def test_set_terminology_config(self):
        """Test setting terminology configuration"""
        tenant = Tenant(name="Test Tenant", code="TEST", type=TenantType.ROOT)
        
        terminology = {
            "tenant": "Maritime Authority",
            "user": "Maritime Stakeholder"
        }
        
        tenant.set_terminology_config(terminology)
        
        # Check terminology is stored
        stored_config = tenant.get_terminology_config()
        assert stored_config == terminology
        
        # Check metadata is created
        assert "terminology_metadata" in tenant.settings
        metadata = tenant.settings["terminology_metadata"]
        assert metadata["is_inherited"] is False
        assert "last_updated" in metadata
    
    def test_get_default_terminology(self):
        """Test default terminology contains all required keys"""
        tenant = Tenant(name="Test Tenant", code="TEST", type=TenantType.ROOT)
        
        default_terms = tenant._get_default_terminology()
        
        # Check core entity terms
        required_terms = [
            "tenant", "sub_tenant", "user", "role", 
            "permission", "resource", "group"
        ]
        
        for term in required_terms:
            assert term in default_terms
            assert isinstance(default_terms[term], str)
            assert len(default_terms[term]) > 0
        
        # Check some specific values
        assert default_terms["tenant"] == "Tenant"
        assert default_terms["user"] == "User"
        assert default_terms["create_tenant"] == "Create Tenant"
    
    def test_effective_terminology_no_parents(self):
        """Test effective terminology for tenant with no parents"""
        tenant = Tenant(name="Test Tenant", code="TEST", type=TenantType.ROOT)
        
        # Set custom terminology
        custom_terminology = {
            "tenant": "Maritime Authority",
            "user": "Maritime Stakeholder"
        }
        tenant.set_terminology_config(custom_terminology)
        
        effective = tenant.get_effective_terminology()
        
        # Should contain both default and custom terms
        assert effective["tenant"] == "Maritime Authority"  # Custom
        assert effective["user"] == "Maritime Stakeholder"  # Custom
        assert effective["role"] == "Role"  # Default (not overridden)
    
    def test_terminology_inheritance_single_level(self):
        """Test terminology inheritance from parent to child"""
        # Create parent with terminology
        parent = Tenant(
            name="Parent Tenant", 
            code="PARENT", 
            type=TenantType.ROOT,
            id=uuid4()
        )
        parent_terminology = {
            "tenant": "Maritime Authority",
            "user": "Maritime Stakeholder"
        }
        parent.set_terminology_config(parent_terminology)
        
        # Create child without terminology
        child = Tenant(
            name="Child Tenant",
            code="CHILD", 
            type=TenantType.SUB_TENANT,
            parent_tenant_id=parent.id,
            id=uuid4()
        )
        child.parent = parent  # Set relationship
        
        # Child should inherit parent terminology
        child_effective = child.get_effective_terminology()
        assert child_effective["tenant"] == "Maritime Authority"
        assert child_effective["user"] == "Maritime Stakeholder"
        assert child_effective["role"] == "Role"  # Default term
    
    def test_terminology_inheritance_with_override(self):
        """Test child can override specific parent terms"""
        # Create parent with terminology
        parent = Tenant(
            name="Parent Tenant",
            code="PARENT",
            type=TenantType.ROOT,
            id=uuid4()
        )
        parent_terminology = {
            "tenant": "Maritime Authority",
            "user": "Maritime Stakeholder",
            "role": "Stakeholder Type"
        }
        parent.set_terminology_config(parent_terminology)
        
        # Create child with partial override
        child = Tenant(
            name="Child Tenant",
            code="CHILD",
            type=TenantType.SUB_TENANT,
            parent_tenant_id=parent.id,
            id=uuid4()
        )
        child.parent = parent
        
        child_terminology = {
            "user": "Port Worker"  # Override just this term
        }
        child.set_terminology_config(child_terminology)
        
        # Check effective terminology
        child_effective = child.get_effective_terminology()
        assert child_effective["tenant"] == "Maritime Authority"  # From parent
        assert child_effective["user"] == "Port Worker"  # Overridden by child
        assert child_effective["role"] == "Stakeholder Type"  # From parent
    
    def test_terminology_inheritance_multi_level(self):
        """Test terminology inheritance through multiple levels"""
        # Create 3-level hierarchy
        grandparent = Tenant(
            name="Grandparent", 
            code="GP", 
            type=TenantType.ROOT,
            id=uuid4()
        )
        grandparent.set_terminology_config({"tenant": "Platform Entity"})
        
        parent = Tenant(
            name="Parent",
            code="P", 
            type=TenantType.SUB_TENANT,
            parent_tenant_id=grandparent.id,
            id=uuid4()
        )
        parent.parent = grandparent
        parent.set_terminology_config({"user": "System User"})
        
        child = Tenant(
            name="Child",
            code="C",
            type=TenantType.SUB_TENANT, 
            parent_tenant_id=parent.id,
            id=uuid4()
        )
        child.parent = parent
        child.set_terminology_config({"role": "Custom Role"})
        
        # Set up complete hierarchy chain
        parent.parent = grandparent
        child.parent = parent
        
        # Child should inherit from entire hierarchy
        child_effective = child.get_effective_terminology()
        assert child_effective["tenant"] == "Platform Entity"  # From grandparent
        assert child_effective["user"] == "System User"  # From parent
        assert child_effective["role"] == "Custom Role"  # From child
        assert child_effective["permission"] == "Permission"  # Default
    
    def test_get_terminology_with_metadata(self):
        """Test terminology metadata generation"""
        # Parent with terminology
        parent = Tenant(
            name="Parent",
            code="PARENT",
            type=TenantType.ROOT,
            id=uuid4()
        )
        parent.set_terminology_config({"tenant": "Authority"})
        
        # Child without terminology (should inherit)
        child = Tenant(
            name="Child",
            code="CHILD",
            type=TenantType.SUB_TENANT,
            parent_tenant_id=parent.id,
            id=uuid4()
        )
        child.parent = parent
        
        metadata = child.get_terminology_with_metadata()
        
        assert metadata["is_inherited"] is True
        assert metadata["inherited_from"] == parent.id
        assert metadata["local_config"] == {}
        assert metadata["terminology"]["tenant"] == "Authority"
        
        # Now add local configuration
        child.set_terminology_config({"user": "Local User"})
        metadata = child.get_terminology_with_metadata()
        
        assert metadata["is_inherited"] is False
        assert metadata["inherited_from"] is None
        assert metadata["local_config"]["user"] == "Local User"
    
    def test_clear_terminology_config(self):
        """Test clearing terminology configuration"""
        tenant = Tenant(name="Test Tenant", code="TEST", type=TenantType.ROOT)
        
        # Set terminology
        tenant.set_terminology_config({"tenant": "Custom Term"})
        assert tenant.get_terminology_config() != {}
        
        # Clear terminology
        tenant.clear_terminology_config()
        assert tenant.get_terminology_config() == {}
        
        # Settings should not contain terminology keys
        if tenant.settings:
            assert "terminology_config" not in tenant.settings
            assert "terminology_metadata" not in tenant.settings
    
    def test_settings_initialization(self):
        """Test terminology works when settings is initially None"""
        tenant = Tenant(name="Test Tenant", code="TEST", type=TenantType.ROOT)
        tenant.settings = None  # Simulate uninitialized settings
        
        # Should handle None settings gracefully
        config = tenant.get_terminology_config()
        assert config == {}
        
        # Setting terminology should initialize settings
        tenant.set_terminology_config({"tenant": "Test Authority"})
        assert tenant.settings is not None
        assert tenant.get_terminology_config()["tenant"] == "Test Authority"
    
    def test_apply_terminology_to_children(self):
        """Test applying terminology to child tenants"""
        # Create parent with children
        parent = Tenant(
            name="Parent",
            code="PARENT", 
            type=TenantType.ROOT,
            id=uuid4()
        )
        
        child1 = Tenant(
            name="Child 1",
            code="CHILD1",
            type=TenantType.SUB_TENANT,
            parent_tenant_id=parent.id,
            id=uuid4()
        )
        child1.parent = parent
        
        child2 = Tenant(
            name="Child 2", 
            code="CHILD2",
            type=TenantType.SUB_TENANT,
            parent_tenant_id=parent.id,
            id=uuid4()
        )
        child2.parent = parent
        
        # Mock the sub_tenants relationship
        parent.sub_tenants = [child1, child2]
        
        # Apply terminology to children
        terminology = {"tenant": "Applied Authority"}
        parent.apply_terminology_to_children(terminology, recursive=False)
        
        # Both children should have the applied terminology
        assert child1.get_terminology_config()["tenant"] == "Applied Authority"
        assert child2.get_terminology_config()["tenant"] == "Applied Authority"
        
        # Check metadata was set
        child1_metadata = child1.settings["terminology_metadata"]
        assert child1_metadata["applied_from_parent"] == parent.id
        assert "applied_at" in child1_metadata


class TestTerminologyValidation:
    """Test terminology validation logic"""
    
    def test_valid_terminology_keys(self):
        """Test that terminology accepts valid string keys and values"""
        tenant = Tenant(name="Test", code="TEST", type=TenantType.ROOT)
        
        valid_terminology = {
            "tenant": "Valid Authority",
            "user": "Valid User",
            "custom_term": "Valid Custom Term"
        }
        
        # Should not raise any errors
        tenant.set_terminology_config(valid_terminology)
        assert tenant.get_terminology_config() == valid_terminology
    
    def test_terminology_preserves_existing_settings(self):
        """Test that setting terminology preserves other settings"""
        tenant = Tenant(name="Test", code="TEST", type=TenantType.ROOT)
        
        # Set some existing settings
        tenant.settings = {
            "existing_setting": "preserved_value",
            "another_setting": {"nested": "data"}
        }
        
        # Add terminology
        tenant.set_terminology_config({"tenant": "Authority"})
        
        # Existing settings should be preserved
        assert tenant.settings["existing_setting"] == "preserved_value"
        assert tenant.settings["another_setting"]["nested"] == "data"
        assert tenant.settings["terminology_config"]["tenant"] == "Authority"