# Product Requirements Document (PRD)
## Sentinel Access Platform
### Version 2.0 - Aligned with Complete Schema

## 1. Executive Summary
A comprehensive, API-based multi-tenant access control system that provides granular permission management from product family level down to individual field access, supporting both user and machine-to-machine authentication with JWT-based security, AI-powered features, behavioral biometrics, and approval workflows.

## 2. Product Vision
Create a flexible, scalable access control system that enables SaaS platforms to manage complex permission hierarchies while maintaining security, performance, and ease of management across multiple tenants with varying isolation requirements. The platform leverages AI and behavioral biometrics to provide predictive, adaptive, and highly secure access control.

## 3. Personas

### 3.1 Super Admin (Platform Owner)
- **Goals**: Manage all tenants, monitor system health, configure platform-wide settings, manage AI models
- **Needs**: Complete visibility and control across all tenants, AI model performance metrics
- **Pain Points**: Complex permission debugging, performance monitoring, AI false positives

### 3.2 Tenant Admin
- **Goals**: Manage users, roles, and permissions within their tenant
- **Needs**: Easy-to-use permission management, visibility into access patterns, approval workflow configuration
- **Pain Points**: Understanding permission inheritance, managing complex role hierarchies, setting up approval chains

### 3.3 Application Manager
- **Goals**: Control access to specific applications and features
- **Needs**: Granular control over app-specific permissions, field-level access management
- **Pain Points**: Coordinating permissions across multiple apps, managing three-tier field model

### 3.4 End User
- **Goals**: Access authorized resources efficiently
- **Needs**: Seamless experience, clear understanding of what they can access, quick approval processes
- **Pain Points**: Permission errors, slow page loads due to permission checks, waiting for approvals

### 3.5 Service Account (M2M)
- **Goals**: Automated access to APIs for integration
- **Needs**: Stable, predictable permissions, API key management
- **Pain Points**: Token management, permission scope limitations, credential rotation
- **Note**: Service accounts are managed as special users with `is_service_account` flag

### 3.6 Approval Manager (NEW)
- **Goals**: Manage approval workflows, review access requests, configure approval chains
- **Needs**: Clear approval queue visibility, automated escalation, audit trail
- **Pain Points**: Manual approval processes, lack of context for decisions, approval bottlenecks

### 3.7 Compliance Officer (NEW)
- **Goals**: Ensure regulatory compliance, monitor access patterns, investigate anomalies
- **Needs**: Comprehensive audit logs, compliance reports, AI-powered monitoring
- **Pain Points**: Manual compliance checks, reactive security posture, false positive management

### 3.8 Security Analyst (NEW)
- **Goals**: Monitor behavioral biometrics, investigate anomalies, manage AI models
- **Needs**: Real-time alerts, behavioral analysis tools, model performance metrics
- **Pain Points**: Alert fatigue, tuning AI models, explaining AI decisions

## 4. Core Features

### 4.1 Hierarchical Resource Management
- Product Family → Apps → Capabilities → Services
- Automatic permission inheritance down the hierarchy
- Override capability at each level
- Resource path-based wildcard matching

### 4.2 Role-Based Access Control (RBAC)
- Predefined system roles (Admin, Manager, User)
- Custom role creation with granular permissions
- Role templates for common use cases
- Role inheritance and composition
- Priority-based role conflict resolution

### 4.3 Attribute-Based Access Control (ABAC)
- Dynamic permission evaluation based on resource attributes
- Context-aware permissions (department, location, data ownership)
- Three-tier field-level permission control:
  - **Core fields**: Database columns with direct access
  - **Platform dynamic fields**: Platform-wide JSON fields
  - **Tenant-specific fields**: Tenant-customized JSON fields

### 4.4 Multi-Tenancy Support
- Flexible tenant isolation (separate DB or shared with tenant_id)
- Sub-tenant support with inherited permissions
- Tenant-specific role customization
- All database objects in `sentinel` schema namespace

### 4.5 Workflow Integration
- State-based permissions
- Role-specific actions per workflow state
- Audit trail for workflow permission changes
- Integration with approval chains

### 4.6 Approval Chain Management (NEW)
- Multi-level approval workflows
- Automatic escalation on timeout
- Conditional auto-approval rules
- Approval delegation support
- Integration with permission requests

### 4.7 AI-Powered Features (ENHANCED)
- **Anomaly Detection**: Real-time behavioral analysis
- **Permission Optimization**: Usage-based recommendations
- **Natural Language Interface**: Conversational permission management
- **Predictive Access**: Pre-emptive permission provisioning
- **Compliance Monitoring**: Automated regulatory checks
- **Decision Explanations**: Transparent AI reasoning
- **Agent Communications**: Inter-agent coordination

### 4.8 Behavioral Biometrics (NEW)
- Keystroke dynamics analysis
- Mouse movement patterns
- Navigation sequence tracking
- Session-based authentication
- Continuous authentication
- Deviation scoring

### 4.9 Machine Learning Infrastructure (NEW)
- Feature store for pre-computed ML features
- Model registry and versioning
- Training job management
- A/B testing framework
- Model performance monitoring

## 5. Technical Architecture

### 5.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│                    (FastAPI - Python 3.10)                   │
│                     Modular Monolith                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   Access Control Service                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Auth API  │  │ Permission   │  │   Resource       │  │
│  │             │  │ Evaluation   │  │   Registry       │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Role API   │  │  Policy      │  │   Audit          │  │
│  │             │  │  Engine      │  │   Service        │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Group API  │  │  Approval    │  │   Cache          │  │
│  │             │  │  Chain Engine│  │   Manager        │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  AI Engine  │  │  Biometrics  │  │  Feature Store   │  │
│  │             │  │  Analyzer    │  │                  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                    Data Layer                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL  │  │    Redis     │  │   AI Models      │  │
│  │  (Sentinel  │  │   Cache      │  │   Storage        │  │
│  │   Schema)   │  │  (Optional)  │  │                  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Data Models

#### Tenant Model (Enhanced)
```python
{
    "tenant_id": "uuid",
    "name": "string",
    "code": "string",  # Unique identifier like 'GSC-001'
    "type": "root|sub_tenant",
    "parent_tenant_id": "uuid|null",
    "isolation_mode": "shared|dedicated",
    "settings": {
        "max_users": "integer",
        "features": ["string"],
        "customization": {},
        "approval_required": "boolean"
    },
    "features": ["array of enabled features"],
    "metadata": {},
    "is_active": "boolean",
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

#### User Model (Unified with Service Accounts)
```python
{
    "user_id": "uuid",
    "tenant_id": "uuid",
    "email": "string",
    "username": "string|null",
    "is_service_account": "boolean",
    "service_account_key": "string|null",  # For M2M auth
    "roles": ["role_id"],
    "groups": ["group_id"],
    "attributes": {
        "department": "string",
        "location": "string",
        "custom": {}
    },
    "preferences": {},
    "last_login": "timestamp",
    "login_count": "integer",
    "failed_login_count": "integer",
    "locked_until": "timestamp|null",
    "is_active": "boolean",
    "created_at": "timestamp"
}
```

#### Role Model (Enhanced)
```python
{
    "role_id": "uuid",
    "tenant_id": "uuid",
    "name": "string",
    "display_name": "string",
    "description": "string",
    "type": "system|custom",
    "parent_role_id": "uuid|null",
    "is_assignable": "boolean",
    "priority": "integer",  # For conflict resolution
    "permissions": [
        {
            "resource_type": "string",
            "resource_id": "string|*",
            "resource_path": "string|null",  # For wildcard matching
            "actions": ["create", "read", "update", "delete"],
            "conditions": {},  # ABAC conditions
            "field_permissions": {
                "core": {},
                "platform_dynamic": {},
                "tenant_specific": {}
            }
        }
    ],
    "metadata": {},
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

#### Approval Chain Model (NEW)
```python
{
    "chain_id": "uuid",
    "tenant_id": "uuid",
    "name": "string",
    "resource_type": "string",
    "resource_pattern": "string",  # Pattern matching
    "approval_levels": [
        {
            "level": "integer",
            "approver_role": "string",
            "timeout_hours": "integer",
            "escalate_to_level": "integer|null",
            "auto_approve_conditions": {}
        }
    ],
    "auto_approve_conditions": {},  # Global conditions
    "is_active": "boolean",
    "created_at": "timestamp"
}
```

#### Behavioral Profile Model (NEW)
```python
{
    "profile_id": "uuid",
    "user_id": "uuid",
    "typical_access_hours": {
        "weekday": ["09:00", "18:00"],
        "weekend": []
    },
    "common_resources": ["resource_ids"],
    "access_frequency": {
        "daily_avg": 45,
        "weekly_avg": 225
    },
    "location_patterns": ["locations"],
    "device_fingerprints": ["fingerprints"],
    "typing_cadence": "decimal",
    "mouse_movement_pattern": "string",
    "avg_session_duration": "integer",
    "risk_baseline": "decimal",
    "last_updated": "timestamp"
}
```

## 6. API Design (Key Endpoints)

### 6.1 Core APIs
- Authentication & Token Management
- User & Service Account Management (unified)
- Role & Permission Management
- Group Management
- Resource Hierarchy Management
- Field Definition Management (three-tier)

### 6.2 Advanced APIs
- Approval Chain Configuration
- Access Request Management
- Permission Evaluation & Caching
- Audit & Compliance Reporting

### 6.3 AI & Analytics APIs
- Anomaly Detection
- Permission Optimization
- Natural Language Queries
- Predictive Access
- Behavioral Biometric Capture
- Feature Store Management
- AI Model Management
- Agent Communications

## 7. Security Considerations

### 7.1 Authentication & Authorization
- JWT with short-lived access tokens
- Refresh token rotation
- Service account API keys with rotation
- Multi-factor authentication support
- Continuous authentication via biometrics

### 7.2 Data Protection
- Encryption at rest for sensitive data
- TLS 1.3 for data in transit
- Field-level encryption for PII
- Secure key management
- GDPR compliance features

### 7.3 Threat Detection
- Real-time anomaly detection
- Behavioral analysis
- Risk scoring
- Automated threat response
- Security event correlation

## 8. Performance Requirements

### 8.1 Response Times
- Authentication: < 100ms
- Permission check: < 50ms (cached), < 200ms (uncached)
- API response: < 200ms (p95)
- Biometric analysis: < 500ms
- AI prediction: < 1000ms

### 8.2 Scalability
- 1000+ tenants
- 10,000+ users per tenant
- 1M+ permission checks/hour
- 100K+ concurrent sessions
- 10K+ approval workflows

### 8.3 Availability
- 99.9% uptime SLA
- Zero-downtime deployments
- Automatic failover
- Geographic redundancy
- Disaster recovery < 4 hours

## 9. Implementation Approach

### 9.1 Technology Stack
- **Language**: Python 3.10 (strict requirement)
- **Framework**: FastAPI (modular monolith)
- **Database**: PostgreSQL with `sentinel` schema
- **Cache**: Redis (optional, start with in-memory)
- **ML Framework**: scikit-learn, TensorFlow
- **Container**: Docker with Python 3.10
- **Orchestration**: Kubernetes

### 9.2 Development Phases
1. **Foundation**: Core infrastructure, database setup
2. **Authentication**: JWT, token management
3. **User Management**: Users and service accounts (unified)
4. **Access Control**: Roles, groups, permissions
5. **Resources**: Hierarchy, field definitions
6. **Approval Workflows**: Chains, requests, escalation
7. **AI Features**: Anomaly detection, predictions
8. **Biometrics**: Behavioral authentication
9. **Production**: Optimization, monitoring

## 10. Success Metrics

### 10.1 Technical Metrics
- API response time < 200ms (p95)
- Cache hit ratio > 90%
- Error rate < 0.1%
- AI model accuracy > 95%
- False positive rate < 5%

### 10.2 Business Metrics
- User adoption rate > 80%
- Permission request reduction by 50%
- Security incident reduction by 70%
- Time to provision access < 5 minutes
- Approval cycle time < 2 hours

### 10.3 AI Performance Metrics
- Anomaly detection precision > 0.9
- Permission prediction accuracy > 0.85
- NLP query success rate > 0.95
- Compliance automation rate > 80%
- Biometric authentication accuracy > 0.98

## 11. Compliance & Regulatory

### 11.1 Standards
- GDPR compliance
- SOX compliance
- HIPAA ready
- ISO 27001 aligned
- ISPS code compliance (maritime)

### 11.2 Audit Requirements
- Complete audit trail
- Immutable logs
- Data retention policies
- Export capabilities
- Compliance reporting

## 12. Future Enhancements

### 12.1 Phase 2 Features
- GraphQL API support
- WebAuthn/FIDO2 support
- Blockchain-based audit logs
- Quantum-resistant encryption
- Advanced ML models (transformers)

### 12.2 Integration Roadmap
- SAML/OIDC providers
- Cloud provider IAM
- Enterprise directories (AD/LDAP)
- SIEM platforms
- Identity governance platforms

## Version History
- v1.0: Initial PRD
- v2.0: Added approval chains, behavioral biometrics, unified service accounts, ML infrastructure