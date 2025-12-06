#!/usr/bin/env python3
"""
Clear all processing batches - mark them as completed
"""
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv('.env.local')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clear_processing_batches():
    """Mark all processing batches as completed"""

    # Get all processing batches
    result = supabase.table('comfyui_batches').select('*').eq('status', 'processing').execute()
    processing_batches = result.data

    if not processing_batches:
        print("✅ No processing batches found")
        return

    print(f"Found {len(processing_batches)} processing batches\n")

    for batch in processing_batches:
        batch_id = batch['id']
        print(f"📦 Batch {batch_id}")
        print(f"   Created: {batch['created_at']}")

        # Mark as completed
        supabase.table('comfyui_batches').update({
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }).eq('id', batch_id).execute()

        print(f"   ✅ Marked as completed\n")

    print(f"✅ Cleared {len(processing_batches)} processing batches")

if __name__ == "__main__":
    clear_processing_batches()
