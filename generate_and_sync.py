#!/usr/bin/env python3
import sys
import os
from cal_generator import generate_full_year_planner
from sync_to_remarkable import RemarkableSync

def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    
    print(f"Generating planner for {year}...")
    generate_full_year_planner(year)
    print(f"✓ Generation complete!")
    
    password = os.getenv('REMARKABLE_PASSWORD')
    host = os.getenv('REMARKABLE_HOST')
    
    if password and host:
        print(f"\nSyncing to reMarkable at {host}...")
        sync = RemarkableSync(host=host, password=password)
        success = sync.upload_directory(f"{year}_Planner", fail_on_error=False)
        
        if success:
            print(f"✓ Sync complete!")
        else:
            print(f"⚠ Sync skipped - reMarkable not reachable")
            print(f"PDFs saved to planner_{year}/ for manual sync later")
    else:
        print("\nSkipping reMarkable sync (credentials not configured)")
        print(f"PDFs saved to planner_{year}/")

if __name__ == "__main__":
    main()