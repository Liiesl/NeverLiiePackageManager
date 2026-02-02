# src/commands/script_manager.py
"""
Script management for NLPM.

This module handles global scripts that can be executed from anywhere.
Scripts are stored as .nlps files in ~/.nlpm/scripts/

Current implementation: .nlps files are YAML configs
Future: .nlps will be a custom scripting language

Design: Uses os.exec* to replace nlpm process entirely, giving scripts
full terminal control. Perfect for TUI apps, servers, and any command.
"""

import os
import sys
import shlex
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
    Execute a registered script with proper terminal control.
    
    On Windows: Uses 'start /b /wait' for synchronous execution without
    creating new console window. Avoids async process issues with os.exec*.
    
    On Unix: Uses os.exec* to replace the process entirely.
    
    Args:
        script_name: Name of the script to run
        extra_args: Additional command line arguments to pass to the script
    
    Note:
        This function does NOT return - it either exits with the script's
        exit code (Windows) or replaces the process (Unix).
    """
    script_file = config.SCRIPTS_DIR / f"{script_name}.nlps"
    
    if not script_file.exists():
        logger.error(f"Script '{script_name}' not found.")
        logger.info(f"Run 'nlpm list-scripts' to see available scripts")
        sys.exit(1)
    
    script_data = load_yaml(script_file)
    if not script_data:
        logger.error(f"Failed to parse script file: {script_file}")
        sys.exit(1)
    
    command = script_data.get("command")
    if not command:
        logger.error(f"No command specified in script: {script_name}")
        sys.exit(1)
    
    # Get working directory (always absolute from registration)
    cwd = script_data.get("cwd")
    cwd_path = Path(cwd) if cwd else Path.cwd()
    
    # Ensure directory exists
    if not cwd_path.exists():
        logger.error(f"Working directory does not exist: {cwd_path}")
        sys.exit(1)
    
    # Apply environment variables
    script_env = script_data.get("env", {})
    if script_env:
        os.environ.update(script_env)
    
    # Add extra arguments if provided
    if extra_args:
        command = f"{command} {' '.join(extra_args)}"
    
    if os.name == 'nt':  # Windows
        # On Windows, os.exec* doesn't work properly - creates async child process
        # and returns early, causing the shell prompt to appear before output.
        # Use os.spawnv with cmd.exe for proper shell command handling.
        # This should allow better Ctrl+C propagation than subprocess wrappers.
        
        # Change to working directory first
        os.chdir(cwd_path)
        
        # Use cmd.exe /c to run the command through shell
        # This handles shell built-ins like 'echo', 'dir', etc.
        cmd_path = os.environ.get('COMSPEC', 'cmd.exe')
        args = [cmd_path, '/c', command]
        
        try:
            # os.spawnv with P_WAIT waits for child to complete
            # P_WAIT = 0 (wait for process to finish)
            exit_code = os.spawnv(os.P_WAIT, cmd_path, args)
            sys.exit(exit_code)
        except KeyboardInterrupt:
            # Handle Ctrl+C cleanly - exit code 130 (SIGINT)
            sys.exit(130)
        except FileNotFoundError:
            logger.error(f"Command interpreter not found: {cmd_path}")
            sys.exit(127)
        except Exception as e:
            logger.error(f"Failed to execute: {e}")
            sys.exit(1)
    else:
        # Unix: Use os.exec* to replace process entirely
        os.chdir(cwd_path)
        args = shlex.split(command)
        os.execvp(args[0], args)


def find_and_run_script(args_list):
    """
    Attempt to find and run a script by name.
    
    If script is found, this function NEVER RETURNS - it replaces
    the nlpm process with the script using os.exec*.
    
    Args:
        args_list: List of command line arguments (first item is script name)
    
    Returns:
        bool: True if script was found and exec'd (function never returns in this case)
              False if script not found
    """
    if not args_list:
        return False
    
    script_name = args_list[0]
    extra_args = args_list[1:] if len(args_list) > 1 else None
    
    script_file = config.SCRIPTS_DIR / f"{script_name}.nlps"
    
    if script_file.exists():
        # This NEVER returns - replaces process with script
        run_script(script_name, extra_args)
        # Code below this line is unreachable
    
    return False
