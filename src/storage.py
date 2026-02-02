# src/storage.py
import shutil
from pathlib import Path
from . import config
from . import utils

def init_store():
    """Ensures the store directory exists."""
    config.STORE_DIR.mkdir(parents=True, exist_ok=True)

def get_object_path(file_hash):
    """
    Returns the path where a file with a specific hash should be stored.
    We use sharding (first 2 chars) to avoid one folder having million files.
    e.g. store/e3/b0c44298fc1c149...
    """
    prefix = file_hash[:2]
    rest = file_hash[2:]
    return config.STORE_DIR / prefix / rest

def add_file(source_path):
    """
    Hashes the file at source_path.
    Copies it to the global store if not already present.
    Returns: The hash (string)
    """
    init_store()
    
    file_hash = utils.compute_sha256(source_path)
    dest_path = get_object_path(file_hash)
    
    if dest_path.exists():
        # Dedup! It's already there.
        return file_hash
    
    # Ensure shard directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy to store
    shutil.copy2(source_path, dest_path)
    return file_hash

def checkout_file(file_hash, dest_path):
    """
    Copies a file from the global store to dest_path.
    """
    obj_path = get_object_path(file_hash)
    
    if not obj_path.exists():
        raise FileNotFoundError(f"Object {file_hash} missing from store.")
    
    # Ensure destination directory structure exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(obj_path, dest_path)