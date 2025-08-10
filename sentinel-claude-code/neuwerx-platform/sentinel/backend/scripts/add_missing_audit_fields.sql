-- =================================================================
-- Add Missing Audit Fields to Relationship Tables
-- 
-- This script adds the missing created_at and updated_at fields
-- to relationship tables that are inconsistent with audit standards.
--
-- Tables to update:
-- - user_groups: Add created_at, updated_at
-- - group_roles: Add created_at, updated_at  
-- - role_permissions: Add created_at, updated_at
-- - token_blacklist: Add created_at, updated_at (if missing)
-- - refresh_tokens: Add updated_at (if missing)
-- - permission_cache: Add created_at, updated_at (if missing)
--
-- Date: 2025-08-08
-- =================================================================

-- Start transaction
BEGIN;

-- Add missing audit fields to user_groups table
DO $$
BEGIN
    -- Add created_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'user_groups' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE sentinel.user_groups 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set created_at to added_at for existing records
        UPDATE sentinel.user_groups 
        SET created_at = COALESCE(added_at, CURRENT_TIMESTAMP) 
        WHERE created_at IS NULL;
        
        RAISE NOTICE 'Added created_at column to user_groups table';
    END IF;
    
    -- Add updated_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'user_groups' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE sentinel.user_groups 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set updated_at to created_at for existing records
        UPDATE sentinel.user_groups 
        SET updated_at = COALESCE(created_at, added_at, CURRENT_TIMESTAMP) 
        WHERE updated_at IS NULL;
        
        RAISE NOTICE 'Added updated_at column to user_groups table';
    END IF;
END$$;

-- Add missing audit fields to group_roles table  
DO $$
BEGIN
    -- Add created_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'group_roles' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE sentinel.group_roles 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set created_at to granted_at for existing records
        UPDATE sentinel.group_roles 
        SET created_at = COALESCE(granted_at, CURRENT_TIMESTAMP) 
        WHERE created_at IS NULL;
        
        RAISE NOTICE 'Added created_at column to group_roles table';
    END IF;
    
    -- Add updated_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'group_roles' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE sentinel.group_roles 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set updated_at to created_at for existing records
        UPDATE sentinel.group_roles 
        SET updated_at = COALESCE(created_at, granted_at, CURRENT_TIMESTAMP) 
        WHERE updated_at IS NULL;
        
        RAISE NOTICE 'Added updated_at column to group_roles table';
    END IF;
END$$;

-- Add missing audit fields to role_permissions table
DO $$
BEGIN
    -- Add created_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'role_permissions' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE sentinel.role_permissions 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set created_at to granted_at for existing records
        UPDATE sentinel.role_permissions 
        SET created_at = COALESCE(granted_at, CURRENT_TIMESTAMP) 
        WHERE created_at IS NULL;
        
        RAISE NOTICE 'Added created_at column to role_permissions table';
    END IF;
    
    -- Add updated_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'role_permissions' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE sentinel.role_permissions 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set updated_at to created_at for existing records
        UPDATE sentinel.role_permissions 
        SET updated_at = COALESCE(created_at, granted_at, CURRENT_TIMESTAMP) 
        WHERE updated_at IS NULL;
        
        RAISE NOTICE 'Added updated_at column to role_permissions table';
    END IF;
END$$;

-- Add missing audit fields to user_roles table (add created_at, updated_at if missing)
DO $$
BEGIN
    -- Add created_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'user_roles' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE sentinel.user_roles 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set created_at to granted_at for existing records
        UPDATE sentinel.user_roles 
        SET created_at = COALESCE(granted_at, CURRENT_TIMESTAMP) 
        WHERE created_at IS NULL;
        
        RAISE NOTICE 'Added created_at column to user_roles table';
    END IF;
    
    -- Add updated_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'user_roles' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE sentinel.user_roles 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set updated_at to created_at for existing records
        UPDATE sentinel.user_roles 
        SET updated_at = COALESCE(created_at, granted_at, CURRENT_TIMESTAMP) 
        WHERE updated_at IS NULL;
        
        RAISE NOTICE 'Added updated_at column to user_roles table';
    END IF;
END$$;

-- Add missing audit fields to token_blacklist table
DO $$
BEGIN
    -- Add created_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'token_blacklist' 
        AND column_name = 'created_at'
    ) THEN
        ALTER TABLE sentinel.token_blacklist 
        ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set created_at to revoked_at for existing records
        UPDATE sentinel.token_blacklist 
        SET created_at = COALESCE(revoked_at, CURRENT_TIMESTAMP) 
        WHERE created_at IS NULL;
        
        RAISE NOTICE 'Added created_at column to token_blacklist table';
    END IF;
    
    -- Add updated_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'token_blacklist' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE sentinel.token_blacklist 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set updated_at to created_at for existing records
        UPDATE sentinel.token_blacklist 
        SET updated_at = COALESCE(created_at, revoked_at, CURRENT_TIMESTAMP) 
        WHERE updated_at IS NULL;
        
        RAISE NOTICE 'Added updated_at column to token_blacklist table';
    END IF;
END$$;

-- Add missing updated_at field to refresh_tokens table
DO $$
BEGIN
    -- Add updated_at if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'refresh_tokens' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE sentinel.refresh_tokens 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        
        -- Set updated_at to last_used_at or created_at for existing records
        UPDATE sentinel.refresh_tokens 
        SET updated_at = COALESCE(last_used_at, created_at, CURRENT_TIMESTAMP) 
        WHERE updated_at IS NULL;
        
        RAISE NOTICE 'Added updated_at column to refresh_tokens table';
    END IF;
END$$;

-- Add missing audit fields to permission_cache table (if it exists)
DO $$
BEGIN
    -- Check if permission_cache table exists first
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'permission_cache'
    ) THEN
        -- Add created_at if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'sentinel' 
            AND table_name = 'permission_cache' 
            AND column_name = 'created_at'
        ) THEN
            ALTER TABLE sentinel.permission_cache 
            ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            
            -- Set created_at to computed_at for existing records
            UPDATE sentinel.permission_cache 
            SET created_at = COALESCE(computed_at, CURRENT_TIMESTAMP) 
            WHERE created_at IS NULL;
            
            RAISE NOTICE 'Added created_at column to permission_cache table';
        END IF;
        
        -- Add updated_at if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'sentinel' 
            AND table_name = 'permission_cache' 
            AND column_name = 'updated_at'
        ) THEN
            ALTER TABLE sentinel.permission_cache 
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            
            -- Set updated_at to created_at for existing records
            UPDATE sentinel.permission_cache 
            SET updated_at = COALESCE(created_at, computed_at, CURRENT_TIMESTAMP) 
            WHERE updated_at IS NULL;
            
            RAISE NOTICE 'Added updated_at column to permission_cache table';
        END IF;
    ELSE
        RAISE NOTICE 'permission_cache table does not exist, skipping';
    END IF;
END$$;

-- Create or recreate the updated_at trigger function if it doesn't exist
DO $$
BEGIN
    -- Create the trigger function
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'update_updated_at_column' 
        AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'sentinel')
    ) THEN
        CREATE OR REPLACE FUNCTION sentinel.update_updated_at_column()
        RETURNS TRIGGER AS $func$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $func$ language 'plpgsql';
        
        RAISE NOTICE 'Created update_updated_at_column function';
    END IF;
END$$;

-- Add update triggers for the relationship tables that now have updated_at
DO $$
BEGIN
    -- user_groups trigger
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_user_groups_updated_at'
    ) THEN
        CREATE TRIGGER update_user_groups_updated_at 
        BEFORE UPDATE ON sentinel.user_groups
        FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();
        
        RAISE NOTICE 'Created update trigger for user_groups table';
    END IF;
    
    -- group_roles trigger
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_group_roles_updated_at'
    ) THEN
        CREATE TRIGGER update_group_roles_updated_at 
        BEFORE UPDATE ON sentinel.group_roles
        FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();
        
        RAISE NOTICE 'Created update trigger for group_roles table';
    END IF;
    
    -- role_permissions trigger
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_role_permissions_updated_at'
    ) THEN
        CREATE TRIGGER update_role_permissions_updated_at 
        BEFORE UPDATE ON sentinel.role_permissions
        FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();
        
        RAISE NOTICE 'Created update trigger for role_permissions table';
    END IF;
    
    -- user_roles trigger
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_user_roles_updated_at'
    ) THEN
        CREATE TRIGGER update_user_roles_updated_at 
        BEFORE UPDATE ON sentinel.user_roles
        FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();
        
        RAISE NOTICE 'Created update trigger for user_roles table';
    END IF;
    
    -- token_blacklist trigger
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_token_blacklist_updated_at'
    ) THEN
        CREATE TRIGGER update_token_blacklist_updated_at 
        BEFORE UPDATE ON sentinel.token_blacklist
        FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();
        
        RAISE NOTICE 'Created update trigger for token_blacklist table';
    END IF;
    
    -- refresh_tokens trigger
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_refresh_tokens_updated_at'
    ) THEN
        CREATE TRIGGER update_refresh_tokens_updated_at 
        BEFORE UPDATE ON sentinel.refresh_tokens
        FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();
        
        RAISE NOTICE 'Created update trigger for refresh_tokens table';
    END IF;
    
    -- permission_cache trigger (if table exists)
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'permission_cache'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_permission_cache_updated_at'
    ) THEN
        CREATE TRIGGER update_permission_cache_updated_at 
        BEFORE UPDATE ON sentinel.permission_cache
        FOR EACH ROW EXECUTE FUNCTION sentinel.update_updated_at_column();
        
        RAISE NOTICE 'Created update trigger for permission_cache table';
    END IF;
END$$;

-- Update schema version to track this migration
DO $$
BEGIN
    -- Create schema_version table if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'sentinel' 
        AND table_name = 'schema_version'
    ) THEN
        CREATE TABLE sentinel.schema_version (
            version VARCHAR(20) PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            applied_by VARCHAR(100)
        );
        
        RAISE NOTICE 'Created schema_version table';
    END IF;
    
    -- Insert migration record
    INSERT INTO sentinel.schema_version (version, description, applied_by)
    VALUES (
        '2.0.1', 
        'Added missing audit fields (created_at, updated_at) to relationship tables and added corresponding triggers', 
        'migration_script'
    ) ON CONFLICT (version) DO NOTHING;
    
    RAISE NOTICE 'Recorded schema version 2.0.1 migration';
END$$;

-- Commit transaction
COMMIT;

RAISE NOTICE 'Migration completed successfully. All tables now have consistent audit field patterns.';