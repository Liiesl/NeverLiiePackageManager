# src/config.py
from pathlib import Path

# Base Paths
NLPM_HOME = Path.home() / ".nlpm"
# We no longer use TOWN_DIR for folders, but we keep the variable 
# if needed for legacy checks, or we just put the DB in NLPM_HOME.
REGISTRY_DB = NLPM_HOME / "registry.db"
STORE_DIR = NLPM_HOME / "store" 
SCRIPTS_DIR = NLPM_HOME / "scripts"  # Directory for global .nlps scripts

# Filenames
PROJECT_CONFIG_FILE = "nlpm.yaml"
LOCK_FILE = "nlpm.lock"
LIB_CONFIG_FILE = "nlpm.lib.yaml"
SCRIPT_CONFIG_FILE = "nlpm-script.yaml"  # Config template for script registration
SCRIPT_CONFIG_FILE = "nlpm-script.yaml"