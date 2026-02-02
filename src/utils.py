# src/utils.py
import os
import yaml
import logging
import hashlib  # <--- NEW

# Setup Logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("nlpm")

def load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)

def compute_sha256(file_path):
    """Reads a file and returns its hex SHA-256 hash."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def should_ignore(name, patterns):
    """Helper to check if a single filename matches ignore patterns."""
    for pattern in patterns:
        if pattern in name:
            return True
    return False