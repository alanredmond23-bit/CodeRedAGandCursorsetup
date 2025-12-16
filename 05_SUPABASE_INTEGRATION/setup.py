#!/usr/bin/env python3
"""
Supabase Database Setup Script
Purpose: Automated migration and setup for legal discovery database
Version: 1.0.0
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handle database migrations and setup"""

    def __init__(self, connection_string: str):
        """Initialize with Supabase connection string"""
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            logger.info("✓ Database connection established")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to connect to database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("✓ Database connection closed")

    def run_sql_file(self, file_path: Path) -> bool:
        """Execute SQL from a file"""
        try:
            logger.info(f"Running: {file_path.name}")

            with open(file_path, 'r') as f:
                sql_content = f.read()

            # Execute SQL
            self.cursor.execute(sql_content)

            logger.info(f"✓ Completed: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to execute {file_path.name}: {e}")
            return False

    def run_migrations(self, migrations_dir: Path) -> bool:
        """Run all migration files in order"""
        try:
            # Get all SQL files in migrations directory
            migration_files = sorted(migrations_dir.glob("*.sql"))

            if not migration_files:
                logger.warning("No migration files found")
                return False

            logger.info(f"Found {len(migration_files)} migration file(s)")

            for migration_file in migration_files:
                if not self.run_sql_file(migration_file):
                    logger.error(f"Migration failed at: {migration_file.name}")
                    return False

            logger.info("✓ All migrations completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def run_schema_files(self, schema_dir: Path) -> bool:
        """Run schema files in order"""
        schema_files = [
            "0001-legal-discovery-schema.sql",
            "0002-vector-embeddings.sql",
            "0003-cost-tracking.sql",
            "0004-audit-trail.sql",
            "0005-privilege-management.sql",
            "0006-rag-indexes.sql"
        ]

        logger.info("Running schema files...")

        for filename in schema_files:
            file_path = schema_dir / filename
            if not file_path.exists():
                logger.error(f"Schema file not found: {filename}")
                return False

            if not self.run_sql_file(file_path):
                return False

        logger.info("✓ All schema files executed successfully")
        return True

    def run_functions(self, functions_dir: Path) -> bool:
        """Run function definition files"""
        try:
            function_files = sorted(functions_dir.glob("*.sql"))

            if not function_files:
                logger.warning("No function files found")
                return True

            logger.info(f"Running {len(function_files)} function file(s)")

            for function_file in function_files:
                if not self.run_sql_file(function_file):
                    logger.warning(f"Function file failed: {function_file.name}")

            logger.info("✓ Function files executed")
            return True

        except Exception as e:
            logger.error(f"Failed to run functions: {e}")
            return False

    def verify_setup(self) -> bool:
        """Verify database setup"""
        try:
            logger.info("Verifying database setup...")

            # Check extensions
            self.cursor.execute("""
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm')
            """)
            extensions = self.cursor.fetchall()
            logger.info(f"Extensions installed: {len(extensions)}")
            for ext in extensions:
                logger.info(f"  - {ext[0]} v{ext[1]}")

            # Check tables
            self.cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            table_count = self.cursor.fetchone()[0]
            logger.info(f"Tables created: {table_count}")

            # Check indexes
            self.cursor.execute("""
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'public'
            """)
            index_count = self.cursor.fetchone()[0]
            logger.info(f"Indexes created: {index_count}")

            # Check functions
            self.cursor.execute("""
                SELECT COUNT(*)
                FROM pg_proc
                WHERE pronamespace = 'public'::regnamespace
            """)
            function_count = self.cursor.fetchone()[0]
            logger.info(f"Functions created: {function_count}")

            logger.info("✓ Database verification complete")
            return True

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def create_sample_data(self) -> bool:
        """Create sample organization and user"""
        try:
            logger.info("Creating sample data...")

            # Create organization
            self.cursor.execute("""
                INSERT INTO organizations (name, type, email)
                VALUES ('Sample Law Firm', 'law_firm', 'admin@example.com')
                ON CONFLICT DO NOTHING
                RETURNING id
            """)

            result = self.cursor.fetchone()
            if result:
                org_id = result[0]
                logger.info(f"✓ Created organization: {org_id}")

                # Create admin user
                self.cursor.execute("""
                    INSERT INTO users (
                        organization_id,
                        email,
                        full_name,
                        role,
                        hourly_rate
                    )
                    VALUES (%s, 'admin@example.com', 'System Admin', 'super_admin', 200.00)
                    ON CONFLICT (email) DO NOTHING
                    RETURNING id
                """, (org_id,))

                user_result = self.cursor.fetchone()
                if user_result:
                    logger.info(f"✓ Created admin user: {user_result[0]}")

            return True

        except Exception as e:
            logger.error(f"Failed to create sample data: {e}")
            return False


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Setup Supabase database for legal discovery'
    )
    parser.add_argument(
        '--connection-string',
        required=True,
        help='PostgreSQL connection string'
    )
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory containing SQL files'
    )
    parser.add_argument(
        '--skip-sample-data',
        action='store_true',
        help='Skip creating sample data'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing setup'
    )

    args = parser.parse_args()

    # Setup paths
    base_dir = Path(args.base_dir)
    migrations_dir = base_dir / "migrations"
    functions_dir = base_dir / "functions"

    # Initialize setup
    setup = DatabaseSetup(args.connection_string)

    try:
        # Connect to database
        if not setup.connect():
            sys.exit(1)

        if args.verify_only:
            # Just verify
            if setup.verify_setup():
                logger.info("✓ Verification successful")
                sys.exit(0)
            else:
                logger.error("✗ Verification failed")
                sys.exit(1)

        # Run full setup
        logger.info("=" * 60)
        logger.info("STARTING DATABASE SETUP")
        logger.info("=" * 60)

        # Run schema files
        if not setup.run_schema_files(base_dir):
            logger.error("Schema setup failed")
            sys.exit(1)

        # Run functions
        if not setup.run_functions(functions_dir):
            logger.warning("Some functions may have failed")

        # Create sample data
        if not args.skip_sample_data:
            if not setup.create_sample_data():
                logger.warning("Sample data creation failed")

        # Verify setup
        if not setup.verify_setup():
            logger.error("Verification failed")
            sys.exit(1)

        logger.info("=" * 60)
        logger.info("DATABASE SETUP COMPLETE")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next Steps:")
        logger.info("  1. Review embedding configurations in 'embedding_configs' table")
        logger.info("  2. Configure privilege detection rules for your organization")
        logger.info("  3. Set up case budgets")
        logger.info("  4. Import documents and run embedding jobs")
        logger.info("")
        logger.info("Maintenance Commands:")
        logger.info("  - Weekly: SELECT perform_table_maintenance();")
        logger.info("  - Daily: SELECT refresh_all_materialized_views();")
        logger.info("  - Hourly: SELECT cleanup_query_cache();")
        logger.info("")

    except KeyboardInterrupt:
        logger.warning("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)
    finally:
        setup.disconnect()


if __name__ == "__main__":
    main()
