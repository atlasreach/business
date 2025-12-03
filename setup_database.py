#!/usr/bin/env python3
"""
Create Supabase tables for Instagram Carousel Editor workflow
Uses SQLAlchemy with DIRECT_URL for schema changes
"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env.local')

# Get the direct connection URL (for schema changes)
direct_url = os.getenv('DIRECT_URL')

# Create engine
engine = create_engine(direct_url)

# Define all table creation SQL
tables = {
    "instagram_carousels": """
        CREATE TABLE IF NOT EXISTS instagram_carousels (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            post_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            caption TEXT,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            posted_at TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT NOW(),
            image_count INTEGER DEFAULT 0,
            raw_data JSONB
        );
    """,

    "carousel_images": """
        CREATE TABLE IF NOT EXISTS carousel_images (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            carousel_id UUID REFERENCES instagram_carousels(id) ON DELETE CASCADE,
            image_url TEXT NOT NULL,
            image_order INTEGER NOT NULL,
            local_path TEXT,
            width INTEGER,
            height INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """,

    "edit_tests": """
        CREATE TABLE IF NOT EXISTS edit_tests (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            carousel_id UUID REFERENCES instagram_carousels(id) ON DELETE CASCADE,
            image_id UUID REFERENCES carousel_images(id) ON DELETE CASCADE,
            edit_prompt TEXT NOT NULL,
            nanabana_result_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,
            approved_at TIMESTAMP,
            notes TEXT,
            CONSTRAINT status_check CHECK (status IN ('pending', 'processing', 'completed', 'approved', 'rejected'))
        );
    """,

    "comfyui_batches": """
        CREATE TABLE IF NOT EXISTS comfyui_batches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            edit_test_id UUID REFERENCES edit_tests(id) ON DELETE CASCADE,
            carousel_id UUID REFERENCES instagram_carousels(id) ON DELETE CASCADE,
            status TEXT DEFAULT 'queued',
            images_to_process JSONB,
            completed_images JSONB,
            workflow_name TEXT DEFAULT 'OpenPose Workflow 3',
            created_at TIMESTAMP DEFAULT NOW(),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            CONSTRAINT batch_status_check CHECK (status IN ('queued', 'processing', 'completed', 'failed'))
        );
    """
}

# Define indexes
indexes = [
    "CREATE INDEX IF NOT EXISTS idx_carousels_username ON instagram_carousels(username);",
    "CREATE INDEX IF NOT EXISTS idx_carousels_posted_at ON instagram_carousels(posted_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_images_carousel_id ON carousel_images(carousel_id);",
    "CREATE INDEX IF NOT EXISTS idx_edit_tests_status ON edit_tests(status);",
    "CREATE INDEX IF NOT EXISTS idx_edit_tests_carousel_id ON edit_tests(carousel_id);",
    "CREATE INDEX IF NOT EXISTS idx_comfyui_batches_status ON comfyui_batches(status);"
]

def setup_database():
    """Create all tables and indexes"""

    print("🔧 Setting up Supabase database...\n")

    try:
        with engine.connect() as conn:
            # Create tables
            print("📊 Creating tables:")
            for table_name, create_sql in tables.items():
                conn.execute(text(create_sql))
                conn.commit()
                print(f"  ✓ {table_name}")

            # Create indexes
            print("\n🔍 Creating indexes:")
            for index_sql in indexes:
                conn.execute(text(index_sql))
                conn.commit()
                print(f"  ✓ Index created")

            print("\n✅ Database setup complete!")
            print("\n📋 Tables created:")
            print("  - instagram_carousels (stores scraped carousel data)")
            print("  - carousel_images (individual images from carousels)")
            print("  - edit_tests (NanaBanana test results & approval status)")
            print("  - comfyui_batches (batch processing jobs)")

            # Verify tables exist
            print("\n🔍 Verifying tables...")
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('instagram_carousels', 'carousel_images', 'edit_tests', 'comfyui_batches')
                ORDER BY table_name;
            """))

            verified_tables = [row[0] for row in result.fetchall()]
            print(f"  Found {len(verified_tables)} tables: {', '.join(verified_tables)}")

            return True

    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_database()

    if success:
        print("\n🎉 Ready to go! Next steps:")
        print("  1. Run: python import_instagram_data.py")
        print("  2. Run: python app.py (to start the web interface)")
    else:
        print("\n⚠️  Setup failed. Please check the error messages above.")
