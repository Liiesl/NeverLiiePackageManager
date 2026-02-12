# src/commands/script_manager.py
"""
Script management for NLPM.

This module handles global scripts that can be executed from anywhere.
Scripts are stored as .nlps files in ~/.nlpm/scripts/

All .nlps files are NLPS language code - YAML configs are transpiled to NLPS during registration.

Design: 
- Windows: Uses subprocess.run() for proper terminal control and I/O handling
- Unix: Uses os.exec* to replace the nlpm process entirely

This gives scripts full terminal control, perfect for TUI apps, servers, and any command.
"""

import os
import sys
import subprocess
from pathlib import Path
from .. import config
from ..utils import load_yaml, save_yaml, logger
from ..nlps import run_script as run_nlps_script


def init_script(args):
    """Create nlpm-script.yaml template for script registration."""
    if Path(config.SCRIPT_CONFIG_FILE).exists():
        logger.warning(f"{config.SCRIPT_CONFIG_FILE} already exists.")
        return
    
    template = {
        "name": "my-script",
        "description": "A short description of what this script does",
        "command": "echo 'Hello from NLPM script!'",
        "cwd": str(Path.cwd()),
        "env": {}
    }
    
    save_yaml(config.SCRIPT_CONFIG_FILE, template)
    logger.info(f"Created {config.SCRIPT_CONFIG_FILE}")
    logger.info("Edit it, then run: nlpm register script")


def transpile_to_nlps(script_data: dict) -> str:
    """Transpile YAML script configuration to NLPS language code."""
    name = script_data.get("name", "script")
    description = script_data.get("description", f"Script: {name}")
    command = script_data.get("command", "")
    cwd = script_data.get("cwd", str(Path.cwd()))
    env = script_data.get("env", {})
    
    # Escape backslashes for Windows paths in NLPS strings
    cwd_escaped = cwd.replace("\\", "/")
    
    lines = [f"# {description}"]
    
    # Add environment variables
    for key, value in env.items():
        # Escape backslashes in values too
        value_escaped = str(value).replace("\\", "/")
        lines.append(f"${key} = \"{value_escaped}\"")
    
    # Add cd command (use forward slashes for cross-platform compatibility)
    lines.append(f'cd "{cwd_escaped}"')
    
    # Add the main command
    lines.append(f'run {command}')
    
    return "\n".join(lines)


def register_script(args):
    """Register a script from nlpm-script.yaml to global scripts directory."""
    script_config_path = Path(config.SCRIPT_CONFIG_FILE)
    
    if not script_config_path.exists():
        logger.error(f"{config.SCRIPT_CONFIG_FILE} not found. Run 'nlpm init script' first.")
        return
    
    script_data = load_yaml(script_config_path)
    if not script_data:
        logger.error(f"Failed to parse {config.SCRIPT_CONFIG_FILE}")
        return
    
    # Validate required fields
    name = script_data.get("name")
    
    if not name:
        logger.error("Script 'name' is required in config")
        return
    
    # Ensure scripts directory exists
    config.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for reserved names (built-in commands)
    reserved_commands = {
        "init", "list", "register", "publish", "install", "update",
        "cdr", "remove-dir", "cdr-init", "help", "--help", "-h"
    }
    
    if name in reserved_commands:
        logger.error(f"Script name '{name}' is reserved. Choose a different name.")
        return
    
    script_file = config.SCRIPTS_DIR / f"{name}.nlps"
    
    # Check if using advanced NLPS script or simple command
    nlps_script_path = script_data.get("script")
    
    if nlps_script_path:
        # Advanced: Copy the NLPS file
        nlps_file = Path(nlps_script_path)
        if not nlps_file.is_absolute():
            nlps_file = Path.cwd() / nlps_file
        
        if not nlps_file.exists():
            logger.error(f"NLPS script file not found: {nlps_script_path}")
            return
        
        try:
            import shutil
            shutil.copy2(nlps_file, script_file)
            logger.info(f"Registered NLPS script '{name}' -> {script_file}")
        except Exception as e:
            logger.error(f"Failed to copy NLPS script: {e}")
            return
    else:
        # Simple: Transpile to NLPS
        command = script_data.get("command")
        if not command:
            logger.error("Script 'command' is required when 'script' field is not set")
            return
        
        # Auto-generate absolute cwd
        cwd = script_data.get("cwd")
        if cwd:
            cwd_path = Path(cwd)
            if not cwd_path.is_absolute():
                script_data["cwd"] = str(Path.cwd() / cwd_path)
        else:
            script_data["cwd"] = str(Path.cwd().resolve())
        
        # Transpile to NLPS code
        nlps_code = transpile_to_nlps(script_data)
        
        try:
            script_file.write_text(nlps_code, encoding='utf-8')
            logger.info(f"Registered script '{name}' (transpiled to NLPS) -> {script_file}")
        except Exception as e:
            logger.error(f"Failed to write NLPS script: {e}")
            return
    
    logger.info(f"Run with: nlpm {name}")


def list_scripts(args):
    """List all registered global scripts."""
    if not config.SCRIPTS_DIR.exists():
        logger.info("No scripts registered yet.")
        return
    
    scripts = list(config.SCRIPTS_DIR.glob("*.nlps"))
    
    if not scripts:
        logger.info("No scripts registered yet.")
        return
    
    print("Registered Scripts:")
    print("-" * 50)
    
    for script_file in sorted(scripts):
        # All .nlps files in scripts directory are NLPS language code
        content = script_file.read_text(encoding='utf-8', errors='ignore')
        name = script_file.stem
        
        # Extract first line comment if any
        first_line = content.strip().split('\n')[0] if content.strip() else ''
        if first_line.startswith('#'):
            desc = first_line[1:].strip()
        else:
            desc = "NLPS script"
        
        # Show first run command as preview
        cmd_preview = "NLPS code"
        for line in content.split('\n'):
            if line.strip().startswith('run '):
                cmd_preview = line.strip()[4:]  # Remove 'run '
                break
        
        print(f"  {name}")
        print(f"    Description: {desc}")
        print(f"    Preview: {cmd_preview}")
        print()


def find_and_run_script(args_list):
    """
    Attempt to find and run a script by name.
    
    All scripts in ~/.nlpm/scripts/ are NLPS language code.
    
    Args:
        args_list: List of command line arguments (first item is script name)
    
    Returns:
        bool: True if script was found and executed (exits the process)
              False if script not found
    """
    if not args_list:
        return False
    
    script_name = args_list[0]
    extra_args = args_list[1:] if len(args_list) > 1 else None
    
    script_file = config.SCRIPTS_DIR / f"{script_name}.nlps"
    
    if script_file.exists():
        # All scripts are NLPS language code
        exit_code = run_nlps_script(str(script_file), extra_args)
        sys.exit(exit_code)
    
    return False
