import os
import time
import json
import uuid
from flask import current_app, Response

# For tracking file changes and notifying clients
file_changes = {"last_update": time.time(), "clients": 0}

def get_filtered_files():
    """Get filtered lists of MP3 and MP4 files"""
    mp3_dir = current_app.config["OUTPUT_DIR_MP3"]
    mp4_dir = current_app.config["OUTPUT_DIR_MP4"]
    
    # Get all files in the directories
    all_mp3_files = os.listdir(mp3_dir)
    all_mp4_files = os.listdir(mp4_dir)
    
    # Filter by extension
    mp3_files = sorted([f for f in all_mp3_files if f.lower().endswith('.mp3')])
    mp4_files = sorted([f for f in all_mp4_files if f.lower().endswith('.mp4')])
    
    return mp3_files, mp4_files

def notify_clients():
    """Update the last_update timestamp to notify clients of a change"""
    file_changes["last_update"] = time.time()

def handle_event_stream(active_downloads):
    """Handles SSE event streaming"""
    # Register this client
    client_id = uuid.uuid4()
    file_changes["clients"] += 1
    
    try:
        # Initial data
        mp3_files, mp4_files = get_filtered_files()
        
        data = {
            "mp3_files": mp3_files,
            "mp4_files": mp4_files,
            "active_downloads": {k: v for k, v in active_downloads.items() if v["status"] == "downloading"},
            "type": "initial"
        }
        
        yield f"data: {json.dumps(data)}\n\n"
        
        # Keep track of last update time for this client
        last_update = time.time()
        
        # Stream updates
        while True:
            # Sleep to prevent high CPU usage
            time.sleep(0.3)
            
            # Check if there are updates
            if file_changes["last_update"] > last_update:
                mp3_files, mp4_files = get_filtered_files()
                
                data = {
                    "mp3_files": mp3_files,
                    "mp4_files": mp4_files,
                    "active_downloads": {k: v for k, v in active_downloads.items() if v["status"] == "downloading"},
                    "type": "update"
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                last_update = time.time()
                
            # Keep the heartbeat
            if time.time() - last_update > 15:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                last_update = time.time()
    except Exception as e:
        print(f"SSE Error: {e}")
    finally:
        # Un-register this client
        file_changes["clients"] -= 1

def get_files_response(active_downloads):
    """Get a JSON response with file lists for polling"""
    mp3_files, mp4_files = get_filtered_files()
    
    return {
        "mp3_files": mp3_files,
        "mp4_files": mp4_files,
        "active_downloads": {k: v for k, v in active_downloads.items() if v["status"] == "downloading"},
        "type": "update"
    }