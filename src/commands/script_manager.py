# src/commands/script_manager.py
"""
Script management for NLPM.

This module handles global scripts that can be executed from anywhere.
Scripts are stored as .nlps files in ~/.nlpm/scripts/

Current implementation: .nlps files are YAML configs
Future: .nlps will be a custom scripting language
"""

import os
import sys
import subprocess
from pathlib import Path
from .. import config
from ..utils import load_yaml, save_yaml, logger


def init_script(args):
    """Create nlpm-script.yaml template for script registration."""
    if Path(config.SCRIPT_CONFIG_FILE).exists():
        logger.warning(f"{config.SCRIPT_CONFIG_FILE} already exists.")
        return
    
    template = {
        "name": "my-script",
        "description": "A short description of what this script does",
        "command": "echo 'Hello from NLPM script!'",
        # cwd is auto-generated as absolute path during registration
        # This tells nlpm where to cd when running the command
        "cwd": str(Path.cwd()),
        "env": {}     # Optional environment variables
    }
    
    save_yaml(config.SCRIPT_CONFIG_FILE, template)
    logger.info(f"Created {config.SCRIPT_CONFIG_FILE}")
    logger.info("Edit it, then run: nlpm register-script")


def register_script(args):
    """Register a script from nlpm-script.yaml to global scripts directory."""
    script_config_path = Path(config.SCRIPT_CONFIG_FILE)
    
    if not script_config_path.exists():
        logger.error(f"{config.SCRIPT_CONFIG_FILE} not found. Run 'nlpm init-script' first.")
        return
    
    script_data = load_yaml(script_config_path)
    if not script_data:
        logger.error(f"Failed to parse {config.SCRIPT_CONFIG_FILE}")
        return
    
    # Validate required fields
    name = script_data.get("name")
    command = script_data.get("command")
    
    if not name:
        logger.error("Script 'name' is required in config")
        return
    if not command:
        logger.error("Script 'command' is required in config")
        return
    
    # Ensure scripts directory exists
    config.SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for reserved names (built-in commands)
    reserved_commands = {
        "init-lib", "register", "publish", "install", "update", "list",
        "init-script", "register-script", "list-scripts", "help", "--help", "-h"
    }
    
    if name in reserved_commands:
        logger.error(f"Script name '{name}' is reserved. Choose a different name.")
        return
    
    # Auto-generate absolute cwd - this tells nlpm where to cd when running the command
    cwd = script_data.get("cwd")
    if cwd:
        # Convert relative path to absolute path based on current working directory
        cwd_path = Path(cwd)
        if not cwd_path.is_absolute():
            script_data["cwd"] = str(Path.cwd() / cwd_path)
    else:
        # If no cwd specified, use current working directory as absolute path
        script_data["cwd"] = str(Path.cwd().resolve())
    
    # Save as .nlps file (YAML format for now)
    script_file = config.SCRIPTS_DIR / f"{name}.nlps"
    save_yaml(script_file, script_data)
    
    logger.info(f"Registered script '{name}' -> {script_file}")
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
        script_data = load_yaml(script_file)
        if script_data:
            name = script_data.get("name", script_file.stem)
            desc = script_data.get("description", "No description")
            cmd = script_data.get("command", "N/A")
            print(f"  {name}")
            print(f"    Description: {desc}")
            print(f"    Command: {cmd}")
            print()


def run_script(script_name, extra_args=None):
    """
    Execute a registered script.
    
    Args:
        script_name: Name of the script to run
        extra_args: Additional command line arguments to pass to the script
    
    Returns:
        int: Exit code from the executed command
    """
    script_file = config.SCRIPTS_DIR / f"{script_name}.nlps"
    
    if not script_file.exists():
        logger.error(f"Script '{script_name}' not found.")
        logger.info(f"Run 'nlpm list-scripts' to see available scripts")
        return 1
    
    script_data = load_yaml(script_file)
    if not script_data:
        logger.error(f"Failed to parse script file: {script_file}")
        return 1
    
    command = script_data.get("command")
    if not command:
        logger.error(f"No command specified in script: {script_name}")
        return 1
    
    # Get working directory
    cwd = script_data.get("cwd", "./")
    cwd_path = Path(cwd)
    
    # If cwd is absolute, use it as-is; if relative, resolve from current directory
    if not cwd_path.is_absolute():
        cwd_path = Path.cwd() / cwd_path
    
    # Ensure directory exists
    if not cwd_path.exists():
        logger.error(f"Working directory does not exist: {cwd_path}")
        return 1
    
    # Get environment variables
    env = os.environ.copy()
    script_env = script_data.get("env", {})
    if script_env:
        env.update(script_env)
    
    # Add extra arguments if provided
    if extra_args:
        command = f"{command} {' '.join(extra_args)}"
    
    logger.info(f"Running script '{script_name}' in {cwd_path}")
    logger.debug(f"Command: {command}")
    
    try:
        # Execute the command
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd_path,
            env=env,
            check=False
        )
        return result.returncode
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully - user interrupted the script
        logger.info(f"\nScript '{script_name}' interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Failed to execute script: {e}")
        return 1


def find_and_run_script(args_list):
    """
    Attempt to find and run a script by name.
    
    Args:
        args_list: List of command line arguments (first item is script name)
    
    Returns:
        tuple: (success: bool, exit_code: int or None)
        - success: True if script was found and executed
        - exit_code: Exit code from script execution, or None if not found
    """
    if not args_list:
        return (False, None)
    
    script_name = args_list[0]
    extra_args = args_list[1:] if len(args_list) > 1 else None
    
    script_file = config.SCRIPTS_DIR / f"{script_name}.nlps"
    
    if script_file.exists():
        exit_code = run_script(script_name, extra_args)
        return (True, exit_code)
    
    return (False, None)
