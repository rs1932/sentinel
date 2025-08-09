# Industry Terminology Mapping - Testing Strategy

**Version**: 1.0  
**Date**: 2025-08-09  
**Status**: Planning Phase

---

## 🎯 Testing Objectives

### Primary Goals
1. **Ensure zero breaking changes** to existing functionality
2. **Validate terminology inheritance** across multi-level hierarchies  
3. **Verify API consistency** and data integrity
4. **Confirm performance targets** are met
5. **Test UX integration** with dynamic labels

### Quality Gates
- **Test Coverage**: ≥ 90% for terminology features
- **Performance**: < 50ms additional overhead
- **Regression**: 0 breaking changes to existing functionality
- **Integration**: All admin screens work with terminology

---

## 🧪 Test Categories & Approach

### 1. Unit Tests

#### Terminology Inheritance Logic
```python
# test_terminology_inheritance.py
class TestTerminologyInheritance:
    """Test terminology inheritance between parent and child tenants"""
    
    async def test_child_inherits_parent_terminology(self):
        """Child tenant inherits parent terminology when none configured"""
        # Given: Parent tenant with maritime terminology
        parent = await create_tenant_with_terminology({
            "tenant": "Maritime Authority",
            "sub_tenant": "Port Organization"
        })
        
        # When: Child tenant created with no terminology
        child = await create_sub_tenant(parent.id, {})
        
        # Then: Child should inherit parent terminology
        terminology = child.get_effective_terminology()
        assert terminology["tenant"] == "Maritime Authority"
        assert terminology["sub_tenant"] == "Port Organization"
    
    async def test_child_overrides_parent_terminology(self):
        """Child tenant can override specific parent terms"""
        # Given: Parent with maritime, child with custom override
        parent = await create_tenant_with_terminology({
            "tenant": "Maritime Authority",
            "user": "Maritime Stakeholder"
        })
        
        child = await create_sub_tenant(parent.id, {
            "terminology_config": {
                "user": "Port Worker"  # Override just this term
            }
        })
        
        # Then: Child inherits parent but overrides specific term
        terminology = child.get_effective_terminology()
        assert terminology["tenant"] == "Maritime Authority"  # Inherited
        assert terminology["user"] == "Port Worker"  # Overridden
    
    async def test_multilevel_inheritance(self):
        """Test inheritance through 4+ levels of tenants"""
        # Given: Platform → Country → State → Organization → Branch
        platform = await create_tenant_with_terminology({
            "tenant": "Platform Entity"
        })
        
        country = await create_sub_tenant(platform.id, {
            "terminology_config": {"tenant": "National Authority"}
        })
        
        state = await create_sub_tenant(country.id, {})  # Should inherit
        
        organization = await create_sub_tenant(state.id, {
            "terminology_config": {"user": "Organization Member"}
        })
        
        branch = await create_sub_tenant(organization.id, {})  # Should inherit all
        
        # Then: Branch inherits from entire hierarchy
        terminology = branch.get_effective_terminology()
        assert terminology["tenant"] == "National Authority"  # From country
        assert terminology["user"] == "Organization Member"  # From organization
    
    async def test_no_inheritance_when_disabled(self):
        """Test terminology inheritance can be disabled"""
        parent = await create_tenant_with_terminology({
            "tenant": "Parent Term"
        })
        
        child = await create_sub_tenant(parent.id, {
            "terminology_config": {
                "tenant": "Child Term"
            },
            "inherit_parent": False
        })
        
        terminology = child.get_effective_terminology()
        assert terminology["tenant"] == "Child Term"
        assert "user" not in terminology  # No inheritance
```

#### Terminology Service Tests
```python
# test_terminology_service.py
class TestTerminologyService:
    """Test terminology service layer functionality"""
    
    async def test_get_terminology_with_caching(self):
        """Test terminology retrieval with caching"""
        service = TerminologyService(db)
        
        # First call should hit database
        terminology1 = await service.get_terminology(tenant_id)
        
        # Second call should hit cache
        terminology2 = await service.get_terminology(tenant_id)
        
        assert terminology1 == terminology2
        # Verify cache was used (mock database to ensure no second call)
    
    async def test_cache_invalidation_on_update(self):
        """Test cache is invalidated when terminology updated"""
        service = TerminologyService(db)
        
        # Cache terminology
        await service.get_terminology(tenant_id)
        
        # Update terminology
        await service.update_terminology(tenant_id, {"tenant": "New Term"})
        
        # Verify cache was invalidated and new term returned
        terminology = await service.get_terminology(tenant_id)
        assert terminology["tenant"] == "New Term"
    
    async def test_bulk_apply_to_children(self):
        """Test applying terminology to multiple child tenants"""
        # Given: Parent with 3 children
        parent = await create_tenant()
        children = [await create_sub_tenant(parent.id) for _ in range(3)]
        
        # When: Apply terminology to all children
        new_terminology = {"tenant": "Bulk Applied Term"}
        await service.apply_to_children(parent.id, new_terminology)
        
        # Then: All children should have new terminology
        for child in children:
            terminology = await service.get_terminology(child.id)
            assert terminology["tenant"] == "Bulk Applied Term"
```

### 2. API Integration Tests

#### Terminology CRUD Endpoints
```python
# test_terminology_api.py
class TestTerminologyAPI:
    """Test terminology API endpoints"""
    
    async def test_get_terminology_endpoint(self):
        """Test GET /tenants/{id}/terminology"""
        # Given: Tenant with terminology
        tenant = await create_tenant_with_terminology({
            "tenant": "Maritime Authority"
        })
        
        # When: GET terminology
        response = await client.get(f"/api/v1/tenants/{tenant.id}/terminology")
        
        # Then: Returns terminology with metadata
        assert response.status_code == 200
        data = response.json()
        assert data["terminology"]["tenant"] == "Maritime Authority"
        assert data["tenant_id"] == str(tenant.id)
        assert data["is_inherited"] is False
    
    async def test_update_terminology_endpoint(self):
        """Test PUT /tenants/{id}/terminology"""
        tenant = await create_tenant()
        
        # When: Update terminology
        new_terminology = {
            "terminology": {"tenant": "Updated Term"},
            "inherit_parent": False
        }
        response = await client.put(
            f"/api/v1/tenants/{tenant.id}/terminology",
            json=new_terminology
        )
        
        # Then: Terminology is updated
        assert response.status_code == 200
        
        # Verify in database
        get_response = await client.get(f"/api/v1/tenants/{tenant.id}/terminology")
        data = get_response.json()
        assert data["terminology"]["tenant"] == "Updated Term"
    
    async def test_reset_terminology_endpoint(self):
        """Test DELETE /tenants/{id}/terminology (reset)"""
        # Given: Child tenant with custom terminology
        parent = await create_tenant_with_terminology({"tenant": "Parent Term"})
        child = await create_sub_tenant(parent.id, {
            "terminology_config": {"tenant": "Child Term"}
        })
        
        # When: Reset child terminology
        response = await client.delete(f"/api/v1/tenants/{child.id}/terminology")
        assert response.status_code == 204
        
        # Then: Child inherits from parent again
        get_response = await client.get(f"/api/v1/tenants/{child.id}/terminology")
        data = get_response.json()
        assert data["terminology"]["tenant"] == "Parent Term"
        assert data["is_inherited"] is True
    
    async def test_terminology_in_tenant_patch(self):
        """Test terminology update via existing PATCH endpoint"""
        tenant = await create_tenant()
        
        # When: Update tenant with terminology in settings
        patch_data = {
            "settings": {
                "terminology_config": {"tenant": "PATCH Updated Term"}
            }
        }
        response = await client.patch(f"/api/v1/tenants/{tenant.id}", json=patch_data)
        assert response.status_code == 200
        
        # Then: Terminology is updated
        get_response = await client.get(f"/api/v1/tenants/{tenant.id}/terminology")
        data = get_response.json()
        assert data["terminology"]["tenant"] == "PATCH Updated Term"
```

#### API Schema Validation
```python
class TestTerminologySchemas:
    """Test Pydantic schema validation"""
    
    def test_terminology_response_schema(self):
        """Test terminology response schema validation"""
        from src.schemas.terminology import TerminologyResponse
        
        data = {
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
            "terminology": {"tenant": "Test Term"},
            "is_inherited": True,
            "inherited_from": "parent-id",
            "last_updated": "2025-08-09T10:00:00Z"
        }
        
        # Should validate successfully
        response = TerminologyResponse(**data)
        assert response.terminology["tenant"] == "Test Term"
    
    def test_terminology_update_schema(self):
        """Test terminology update request schema"""
        from src.schemas.terminology import TerminologyUpdate
        
        data = {
            "terminology": {"tenant": "Updated Term"},
            "inherit_parent": False,
            "apply_to_children": True
        }
        
        update = TerminologyUpdate(**data)
        assert update.terminology["tenant"] == "Updated Term"
        assert update.inherit_parent is False
```

### 3. Performance Tests

#### Terminology Lookup Performance
```python
# test_terminology_performance.py
class TestTerminologyPerformance:
    """Test terminology system performance"""
    
    async def test_terminology_lookup_overhead(self):
        """Measure terminology lookup overhead"""
        # Given: Tenant with terminology
        tenant = await create_tenant_with_terminology(large_terminology_config)
        
        # Measure baseline tenant fetch
        start_time = time.time()
        for _ in range(100):
            await service.get_tenant(tenant.id)
        baseline_time = time.time() - start_time
        
        # Measure with terminology lookup
        start_time = time.time()
        for _ in range(100):
            await service.get_terminology(tenant.id)
        terminology_time = time.time() - start_time
        
        # Assert: < 50ms additional overhead per lookup
        overhead_per_lookup = (terminology_time - baseline_time) / 100
        assert overhead_per_lookup < 0.05  # 50ms
    
    async def test_cache_performance(self):
        """Test terminology cache hit performance"""
        tenant = await create_tenant_with_terminology()
        service = TerminologyService(db)
        
        # Prime cache
        await service.get_terminology(tenant.id)
        
        # Measure cache hits
        start_time = time.time()
        for _ in range(1000):
            await service.get_terminology(tenant.id)
        cache_time = time.time() - start_time
        
        # Cache hits should be < 1ms each
        time_per_lookup = cache_time / 1000
        assert time_per_lookup < 0.001  # 1ms
    
    async def test_memory_usage(self):
        """Test terminology cache memory usage"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create 1000 tenants with terminology
        service = TerminologyService(db)
        for i in range(1000):
            tenant = await create_tenant_with_terminology({
                f"term_{j}": f"value_{j}" for j in range(20)  # 20 terms each
            })
            await service.get_terminology(tenant.id)  # Cache it
        
        final_memory = process.memory_info().rss
        memory_used = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Should use < 10MB for 1000 cached terminologies
        assert memory_used < 10
```

#### Concurrent Access Tests
```python
class TestTerminologyConcurrency:
    """Test terminology system under concurrent access"""
    
    async def test_concurrent_terminology_reads(self):
        """Test concurrent terminology reads"""
        tenant = await create_tenant_with_terminology()
        service = TerminologyService(db)
        
        # Concurrent reads should not interfere
        async def read_terminology():
            return await service.get_terminology(tenant.id)
        
        # Run 50 concurrent reads
        results = await asyncio.gather(*[
            read_terminology() for _ in range(50)
        ])
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
    
    async def test_concurrent_terminology_updates(self):
        """Test concurrent terminology updates"""
        tenant = await create_tenant()
        service = TerminologyService(db)
        
        # Concurrent updates should be handled safely
        async def update_terminology(term_value):
            await service.update_terminology(tenant.id, {"tenant": f"Term_{term_value}"})
        
        # Run concurrent updates
        await asyncio.gather(*[
            update_terminology(i) for i in range(10)
        ])
        
        # Final state should be consistent (one of the updates should win)
        final_terminology = await service.get_terminology(tenant.id)
        assert final_terminology["tenant"].startswith("Term_")
```

### 4. Regression Tests

#### Existing Functionality Tests
```python
# test_terminology_regression.py
class TestTerminologyRegression:
    """Ensure existing functionality is not broken"""
    
    async def test_existing_tenant_apis_unchanged(self):
        """Test all existing tenant API endpoints work unchanged"""
        # Test standard tenant creation
        tenant_data = {
            "name": "Test Tenant",
            "code": "TEST-TENANT",
            "type": "root"
        }
        response = await client.post("/api/v1/tenants/", json=tenant_data)
        assert response.status_code == 201
        
        tenant_id = response.json()["id"]
        
        # Test tenant retrieval
        get_response = await client.get(f"/api/v1/tenants/{tenant_id}")
        assert get_response.status_code == 200
        
        # Test tenant update
        update_data = {"name": "Updated Tenant"}
        patch_response = await client.patch(f"/api/v1/tenants/{tenant_id}", json=update_data)
        assert patch_response.status_code == 200
        
        # Test tenant hierarchy
        hierarchy_response = await client.get(f"/api/v1/tenants/{tenant_id}/hierarchy")
        assert hierarchy_response.status_code == 200
    
    async def test_existing_tenant_model_methods(self):
        """Test existing tenant model methods work unchanged"""
        # Test hierarchy methods
        tenant = await create_tenant()
        sub_tenant = await create_sub_tenant(tenant.id)
        
        hierarchy = sub_tenant.get_hierarchy()
        assert len(hierarchy) == 2
        assert hierarchy[0] == tenant
        assert hierarchy[1] == sub_tenant
        
        # Test is_sub_tenant_of
        assert sub_tenant.is_sub_tenant_of(tenant.id) is True
        
        # Test to_dict
        tenant_dict = tenant.to_dict()
        assert "id" in tenant_dict
        assert "name" in tenant_dict
        assert "code" in tenant_dict
    
    async def test_existing_database_constraints(self):
        """Test database constraints still work"""
        # Test unique code constraint
        tenant1 = await create_tenant(code="UNIQUE-CODE")
        
        with pytest.raises(Exception):  # Should raise constraint violation
            await create_tenant(code="UNIQUE-CODE")
        
        # Test parent-child cascade delete
        parent = await create_tenant()
        child = await create_sub_tenant(parent.id)
        
        await delete_tenant(parent.id)
        
        # Child should be deleted by cascade
        with pytest.raises(Exception):
            await get_tenant(child.id)
```

### 5. Frontend Integration Tests

#### UX Component Tests
```python
# test_terminology_frontend.py (using Playwright or similar)
class TestTerminologyFrontend:
    """Test terminology integration in frontend"""
    
    async def test_dynamic_labels_in_tenant_form(self):
        """Test dynamic labels appear in tenant creation form"""
        # Given: Tenant with maritime terminology
        await setup_tenant_with_maritime_terminology()
        
        # When: Admin opens tenant creation form
        await page.goto("/admin/tenants/new")
        
        # Then: Labels should use maritime terminology
        create_button = page.locator("button:has-text('Register Maritime Organization')")
        assert await create_button.is_visible()
        
        tenant_name_label = page.locator("label:has-text('Maritime Authority Name')")
        assert await tenant_name_label.is_visible()
    
    async def test_terminology_configuration_interface(self):
        """Test terminology configuration interface"""
        await setup_admin_user()
        await page.goto("/admin/tenants/{tenant_id}/terminology")
        
        # Should show terminology editor
        terminology_editor = page.locator("[data-testid='terminology-editor']")
        assert await terminology_editor.is_visible()
        
        # Should allow editing terms
        tenant_input = page.locator("input[name='tenant']")
        await tenant_input.fill("Custom Tenant Term")
        
        save_button = page.locator("button:has-text('Save Terminology')")
        await save_button.click()
        
        # Should update successfully
        success_message = page.locator(".success:has-text('Terminology updated')")
        assert await success_message.is_visible()
    
    async def test_terminology_inheritance_preview(self):
        """Test terminology inheritance preview in UI"""
        # Given: Parent with terminology, child without
        await setup_parent_child_terminology_scenario()
        
        # When: View child terminology settings
        await page.goto("/admin/tenants/{child_id}/terminology")
        
        # Then: Should show inherited terminology
        inherited_indicator = page.locator(".inherited-term")
        assert await inherited_indicator.count() > 0
        
        preview_parent_term = page.locator("text='Inherited from parent: Maritime Authority'")
        assert await preview_parent_term.is_visible()
```

### 6. End-to-End Tests

#### Complete Workflow Tests
```python
# test_terminology_e2e.py
class TestTerminologyEndToEnd:
    """Test complete terminology workflows end-to-end"""
    
    async def test_maritime_authority_setup_workflow(self):
        """Test complete maritime authority setup with terminology"""
        # 1. Platform admin creates maritime community
        platform_admin = await create_platform_admin()
        maritime_community = await create_tenant_with_terminology({
            "tenant": "Maritime Authority",
            "sub_tenant": "Port Organization",
            "user": "Maritime Stakeholder"
        })
        
        # 2. Community admin creates shipping organization
        community_admin = await create_community_admin(maritime_community.id)
        shipping_org = await create_sub_tenant(
            maritime_community.id,
            {"name": "Global Shipping Inc"}
        )
        
        # 3. Verify shipping org inherits maritime terminology
        terminology = await get_terminology(shipping_org.id)
        assert terminology["tenant"] == "Maritime Authority"
        assert terminology["sub_tenant"] == "Port Organization"
        
        # 4. Organization admin creates branch
        org_admin = await create_organization_admin(shipping_org.id)
        mumbai_branch = await create_sub_tenant(
            shipping_org.id, 
            {"name": "Mumbai Branch"}
        )
        
        # 5. Verify branch inherits terminology
        branch_terminology = await get_terminology(mumbai_branch.id)
        assert branch_terminology["tenant"] == "Maritime Authority"
        
        # 6. Test UI shows correct labels at each level
        await verify_ui_labels_at_all_levels([
            maritime_community, shipping_org, mumbai_branch
        ])
    
    async def test_healthcare_to_maritime_transition(self):
        """Test changing industry terminology (healthcare → maritime)"""
        # 1. Start with healthcare terminology
        tenant = await create_tenant_with_terminology({
            "tenant": "Health System",
            "user": "Healthcare Professional"
        })
        
        # 2. Change to maritime terminology
        await update_terminology(tenant.id, {
            "tenant": "Maritime Authority",
            "user": "Maritime Stakeholder"
        })
        
        # 3. Verify UI updates reflect new terminology
        await page.goto(f"/admin/tenants/{tenant.id}")
        maritime_label = page.locator("text='Maritime Authority'")
        assert await maritime_label.is_visible()
        
        healthcare_label = page.locator("text='Health System'")
        assert await healthcare_label.count() == 0
    
    async def test_terminology_performance_under_load(self):
        """Test terminology system performance under realistic load"""
        # Create realistic multi-level hierarchy
        platform = await create_platform_tenant()
        countries = [await create_country_tenant(platform.id) for _ in range(5)]
        
        organizations = []
        for country in countries:
            orgs = [await create_organization_tenant(country.id) for _ in range(10)]
            organizations.extend(orgs)
        
        branches = []
        for org in organizations:
            branch_list = [await create_branch_tenant(org.id) for _ in range(5)]
            branches.extend(branch_list)
        
        # Total: 1 platform + 5 countries + 50 orgs + 250 branches = 306 tenants
        
        # Simulate concurrent terminology lookups
        start_time = time.time()
        await asyncio.gather(*[
            get_terminology(branch.id) for branch in branches
        ])
        total_time = time.time() - start_time
        
        # Should complete all 250 lookups in < 5 seconds
        assert total_time < 5.0
        
        # Average per lookup should be < 20ms
        avg_time_per_lookup = total_time / len(branches)
        assert avg_time_per_lookup < 0.02
```

---

## 📊 Test Execution Strategy

### Test Environment Setup
```yaml
# test-environment.yml
test_environments:
  unit:
    database: in-memory SQLite
    cache: fake/mock implementation
    external_services: mocked
    
  integration:
    database: PostgreSQL test instance
    cache: Redis test instance
    external_services: test stubs
    
  performance:
    database: PostgreSQL (production-like)
    cache: Redis (production-like)  
    load: simulated concurrent users
    
  e2e:
    database: PostgreSQL test instance
    frontend: full React app
    backend: full FastAPI app
    browser: Playwright automation
```

### Test Data Management
```python
# Test data fixtures
@pytest.fixture
async def maritime_tenant_hierarchy():
    """Create realistic maritime tenant hierarchy for testing"""
    platform = await create_tenant({
        "name": "Maritime Platform",
        "code": "PLATFORM",
        "type": "root",
        "terminology_config": {
            "tenant": "Maritime Entity",
            "user": "Maritime User"
        }
    })
    
    india_msw = await create_sub_tenant(platform.id, {
        "name": "India MSW",
        "code": "INDIA-MSW",
        "terminology_config": {
            "tenant": "Maritime Authority",
            "sub_tenant": "Port Organization"
        }
    })
    
    shipping_company = await create_sub_tenant(india_msw.id, {
        "name": "Global Shipping Inc",
        "code": "GSI-INDIA"
    })
    
    mumbai_branch = await create_sub_tenant(shipping_company.id, {
        "name": "GSI Mumbai Branch",
        "code": "GSI-MUMBAI"
    })
    
    return {
        "platform": platform,
        "community": india_msw,
        "organization": shipping_company,
        "branch": mumbai_branch
    }
```

### Continuous Integration

#### Test Pipeline
```yaml
# .github/workflows/terminology-tests.yml
name: Terminology Feature Tests

on:
  push:
    branches: [main, feature/terminology-mapping]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Unit Tests
        run: |
          pytest tests/unit/test_terminology* -v
          pytest tests/unit/test_tenant* -v  # Regression tests
  
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Run Integration Tests
        run: pytest tests/integration/test_terminology* -v
  
  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run Performance Tests
        run: pytest tests/performance/test_terminology* -v
        
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Setup Playwright
        run: playwright install
      - name: Run E2E Tests
        run: pytest tests/e2e/test_terminology* -v
```

---

## 📈 Success Criteria

### Test Coverage Targets
| Category | Target Coverage | Current | Status |
|----------|----------------|---------|---------|
| Unit Tests | ≥ 90% | 0% | ⚪ Not Started |
| Integration Tests | ≥ 85% | 0% | ⚪ Not Started |
| API Tests | 100% | 0% | ⚪ Not Started |
| Frontend Tests | ≥ 80% | 0% | ⚪ Not Started |

### Performance Targets
| Metric | Target | Current | Status |
|--------|--------|---------|---------|
| Terminology Lookup | < 50ms overhead | - | ⚪ Not Measured |
| Cache Hit Rate | > 95% | - | ⚪ Not Measured |
| Memory Usage | < 10MB per 1000 tenants | - | ⚪ Not Measured |
| Concurrent Users | 100 simultaneous | - | ⚪ Not Tested |

### Quality Gates
- [ ] All unit tests pass
- [ ] All integration tests pass  
- [ ] Zero regression in existing functionality
- [ ] Performance targets met
- [ ] E2E workflows complete successfully
- [ ] Test coverage targets achieved

---

## 🚧 Risk Mitigation

### Test-Related Risks
| Risk | Impact | Mitigation |
|------|---------|------------|
| Test environment differs from production | High | Use production-like test setup |
| Incomplete test coverage | High | Automated coverage reporting |
| Performance tests don't reflect reality | Medium | Load testing with realistic data |
| Frontend tests are brittle | Medium | Use stable selectors and page objects |
| Race conditions in concurrent tests | Medium | Proper test isolation and cleanup |

---

*Last Updated: 2025-08-09*