# src/commands/producer.py
import sys
import os
import logging
from pathlib import Path

from .. import config
from .. import utils
from .. import registry
from .. import storage

logger = logging.getLogger("nlpm")

def init_lib(args):
    """Creates a template nlpm.lib.yaml"""
    if os.path.exists(config.LIB_CONFIG_FILE):
        logger.error(f"{config.LIB_CONFIG_FILE} already exists.")
        return

    data = {
        "name": "my-library",
        "version": "0.1.0",
        "description": "A short description",
        "language": "python",    # <--- NEW
        "framework": "none",     # <--- NEW
        "author": "Your Name",   # <--- NEW
        "license": "MIT",        # <--- NEW
        "keywords": ["tag1"],    # <--- NEW
        "source_dir": "./src", 
        "import_name": "my_library" 
    }
    utils.save_yaml(config.LIB_CONFIG_FILE, data)
    logger.info(f"Created {config.LIB_CONFIG_FILE} with metadata fields.")

def register(args):
    """Reserves or updates the library metadata in the registry."""
    conf = utils.load_yaml(config.LIB_CONFIG_FILE)
    if not conf:
        logger.error(f"No {config.LIB_CONFIG_FILE} found.")
        sys.exit(1)

    name = conf.get("name")
    
    # Metadata extraction
    metadata = {
        "import_name": conf.get("import_name", name.replace("-", "_")),
        "description": conf.get("description", ""),
        "language": conf.get("language", ""),
        "framework": conf.get("framework", ""),
        "author": conf.get("author", ""),
        "license": conf.get("license", ""),
        "keywords": ",".join(conf.get("keywords", [])) if isinstance(conf.get("keywords"), list) else conf.get("keywords", "")
    }

    # Pass metadata dictionary to registry
    success = registry.register_library(name, **metadata)
    
    if success:
        logger.info(f"Registered/Updated '{name}' (Language: {metadata['language']}, Framework: {metadata['framework']}).")
    else:
        logger.error(f"Failed to register '{name}'.")

def publish(args):
    """Publishes the current version using CAS + SQLite"""
    conf = utils.load_yaml(config.LIB_CONFIG_FILE)
    if not conf:
        logger.error(f"No {config.LIB_CONFIG_FILE} found.")
        sys.exit(1)

    name = conf.get("name")
    version = str(conf.get("version"))
    source_dir = Path(conf.get("source_dir", ".")).resolve()
    
    # 1. Validation
    if not registry.library_exists(name):
        logger.error(f"Library '{name}' is not registered. Run 'nlpm register' first.")
        sys.exit(1)

    if not source_dir.exists():
        logger.error(f"Source directory '{source_dir}' does not exist.")
        sys.exit(1)

    # 2. Hashing (CAS)
    file_map = {} 
    ignore_list = ['.git', '__pycache__', 'node_modules', '.DS_Store', 'nlpm.lib.yaml']

    logger.info(f"Hashing files from {source_dir}...")
    
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if not utils.should_ignore(d, ignore_list)]
        for filename in files:
            if utils.should_ignore(filename, ignore_list):
                continue
            
            abs_path = Path(root) / filename
            rel_path = abs_path.relative_to(source_dir)
            
            # Add to Global CAS (Disk)
            file_hash = storage.add_file(abs_path)
            
            # Map path to hash
            file_map[str(rel_path).replace("\\", "/")] = file_hash

    # 3. Update Registry (SQLite)
    try:
        registry.publish_version(name, version, file_map)
        logger.info(f"Published '{name}' v{version} with {len(file_map)} files.")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)