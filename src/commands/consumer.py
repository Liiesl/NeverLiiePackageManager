# src/commands/consumer.py
import sys
import shutil
import logging
from pathlib import Path

from .. import config
from .. import utils
from .. import registry
from .. import storage

logger = logging.getLogger("nlpm")

def _install_single(name, version, target_root):
    """Core logic to install one lib from CAS + SQLite"""
    
    # 1. Get File Map from DB
    files_map = registry.get_package_files(name, version)
    if files_map is None:
        logger.error(f"Library {name}:{version} not found.")
        return False

    # 2. Get Import Name (NEW)
    db_import_name = registry.get_import_name(name)
    
    # Fallback if DB is empty (legacy) or not found
    import_name = db_import_name if db_import_name else name.replace("-", "_")

    final_dest = Path(target_root) / import_name

    # 2. Clean existing
    if final_dest.exists():
        shutil.rmtree(final_dest)
    final_dest.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Hydrating {len(files_map)} files for {name}:{version}...")
    
    # 3. Reconstruct from CAS
    for rel_path, file_hash in files_map.items():
        file_dest_path = final_dest / rel_path
        try:
            storage.checkout_file(file_hash, file_dest_path)
        except FileNotFoundError:
            logger.error(f"Corrupt Registry: Object {file_hash} missing")
            return False

    logger.info(f"Installed {name}:{version} into {final_dest}")
    return True

# ... install and update functions remain exactly the same as before ...
# ... just ensuring they call the updated _install_single ...

def install(args):
    # Mode 2: Specific Install
    if args.target: 
        if ":" in args.target:
            name, version = args.target.split(":", 1)
        else:
            name = args.target
            version = "latest"
        
        dest_root = args.path if args.path else "./lib"
        
        if version == "latest":
            latest = registry.get_latest_version(name)
            if not latest:
                logger.error(f"Could not find latest version for '{name}'.")
                sys.exit(1)
            version = latest

        if _install_single(name, version, dest_root):
            # Auto-save to YAML logic (unchanged)
            conf = utils.load_yaml(config.PROJECT_CONFIG_FILE) or {"dependencies": []}
            if "dependencies" not in conf: conf["dependencies"] = []

            found = False
            for dep in conf["dependencies"]:
                if dep["name"] == name:
                    dep["version"] = version
                    dep["path"] = str(dest_root)
                    found = True
                    break
            
            if not found:
                conf["dependencies"].append({
                    "name": name, 
                    "version": version, 
                    "path": str(dest_root)
                })
            
            utils.save_yaml(config.PROJECT_CONFIG_FILE, conf)
        return

    # Mode 1: Bulk Install
    conf = utils.load_yaml(config.PROJECT_CONFIG_FILE)
    if not conf or "dependencies" not in conf:
        logger.warning(f"No {config.PROJECT_CONFIG_FILE} found.")
        return

    for dep in conf["dependencies"]:
        _install_single(dep["name"], str(dep["version"]), dep["path"])

def update(args):
    conf = utils.load_yaml(config.PROJECT_CONFIG_FILE)
    if not conf or "dependencies" not in conf:
        logger.error(f"No {config.PROJECT_CONFIG_FILE} found.")
        sys.exit(1)

    updated_count = 0
    new_deps = []

    for dep in conf["dependencies"]:
        name = dep["name"]
        current_version = str(dep["version"])
        path = dep["path"]
        latest = registry.get_latest_version(name)
        
        if not latest:
            logger.warning(f"Skipping {name}: Not found in registry.")
            new_deps.append(dep)
            continue

        if latest != current_version:
            logger.info(f"Updating {name}: {current_version} -> {latest}")
            dep["version"] = latest
            updated_count += 1
            _install_single(name, latest, path)
        else:
            logger.info(f"{name} is up to date ({current_version})")
        
        new_deps.append(dep)

    conf["dependencies"] = new_deps
    utils.save_yaml(config.PROJECT_CONFIG_FILE, conf)