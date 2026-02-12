# src/commands/dir_registry.py
"""
Directory alias registry for the cdr command.

This module handles registering directory aliases and retrieving them.
The actual 'cd' is done by a shell function wrapping nlpm cdr output.
"""

import json
import sys
from pathlib import Path
from .. import config
from ..utils import logger


def _load_registry():
    """Load the directory registry from JSON file."""
    if not config.CDR_REGISTRY_FILE.exists():
        return {}
    
    try:
        with open(config.CDR_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load directory registry: {e}")
        return {}


def _save_registry(registry):
    """Save the directory registry to JSON file."""
    try:
        config.NLPM_HOME.mkdir(parents=True, exist_ok=True)
        with open(config.CDR_REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        logger.error(f"Failed to save directory registry: {e}")
        return False


def get_dir(args):
    """
    Get directory path for an alias.
    Outputs the path to stdout (for shell wrapper to use).
    Exits with error code 1 if alias not found or directory doesn't exist.
    """
    alias = args.alias
    registry = _load_registry()
    
    if alias not in registry:
        logger.error(f"Alias not found: '{alias}'")
        print(f"Run 'nlpm list dirs' to see registered aliases", file=sys.stderr)
        sys.exit(1)
    
    path = registry[alias]
    path_obj = Path(path)
    
    # Validate directory still exists
    if not path_obj.exists():
        logger.error(f"Directory no longer exists: {path}")
        print(f"Alias '{alias}' points to a non-existent directory", file=sys.stderr)
        print(f"Remove it with: nlpm remove-dir {alias}", file=sys.stderr)
        sys.exit(1)
    
    if not path_obj.is_dir():
        logger.error(f"Path is not a directory: {path}")
        sys.exit(1)
    
    # Output the path (for shell wrapper to capture)
    print(path)


def register_dir(args):
    """
    Register current directory or specified path with an alias.
    Prompts for --force if alias already exists.
    """
    alias = args.alias
    
    # Use specified path or current directory
    if args.path:
        path = Path(args.path).resolve()
    else:
        path = Path.cwd().resolve()
    
    # Validate path
    if not path.exists():
        logger.error(f"Directory does not exist: {path}")
        sys.exit(1)
    
    if not path.is_dir():
        logger.error(f"Path is not a directory: {path}")
        sys.exit(1)
    
    registry = _load_registry()
    
    # Check if alias already exists
    if alias in registry and not args.force:
        existing_path = registry[alias]
        print(f"Alias '{alias}' already registered:")
        print(f"  Current: {existing_path}")
        print(f"  New:     {path}")
        print(f"\nUse --force to overwrite:")
        print(f"  nlpm register dir --force {alias}")
        sys.exit(1)
    
    # Register the alias
    registry[alias] = str(path)
    
    if _save_registry(registry):
        action = "Updated" if alias in registry and args.force else "Registered"
        logger.info(f"{action} '{alias}' → {path}")
    else:
        sys.exit(1)


def remove_dir(args):
    """Remove a registered alias."""
    alias = args.alias
    registry = _load_registry()
    
    if alias not in registry:
        logger.error(f"Alias not found: '{alias}'")
        sys.exit(1)
    
    removed_path = registry.pop(alias)
    
    if _save_registry(registry):
        logger.info(f"Removed '{alias}' → {removed_path}")
    else:
        sys.exit(1)


def list_dirs(args):
    """List all registered directory aliases."""
    registry = _load_registry()
    
    if not registry:
        print("No directories registered.")
        print(f"Register one with: nlpm register dir <alias>")
        return
    
    print("Registered Directories:")
    print("-" * 60)
    
    # Sort by alias name
    for alias in sorted(registry.keys()):
        path = registry[alias]
        path_obj = Path(path)
        
        # Check if directory still exists
        status = "[OK]" if path_obj.exists() and path_obj.is_dir() else "[MISSING]"
        
        print(f"  {alias:<15} {status} {path}")
    
    print("-" * 60)
    print(f"\nUse: nlpm cdr <alias>")
    print(f"Or add to your shell: eval \"$(nlpm cdr-init [ps|cmd])\"")


def init_shell(args):
    """
    Output shell integration code for cdr command.
    User adds 'eval "$(nlpm cdr-init bash)"' to their shell config.
    """
    shell = args.shell.lower()
    
    if shell in ('powershell', 'ps'):
        _print_powershell_init()
    elif shell == 'cmd':
        _print_cmd_init()
    else:
        logger.error(f"Unsupported shell: {shell}")
        print(f"Supported shells: ps, cmd", file=sys.stderr)
        sys.exit(1)


def _print_powershell_init():
    """Print PowerShell function for cdr."""
    print('''# nlpm cdr PowerShell integration
# Add to your PowerShell profile: Invoke-Expression (& { (nlpm cdr-init ps | Out-String) })

function global:cdr {
    param([string]$Alias)
    
    if (-not $Alias) {
        Write-Error "Usage: cdr <alias>"
        return
    }
    
    $path = nlpm cdr $Alias 2>&1
    if ($LASTEXITCODE -eq 0) {
        Set-Location $path
    } else {
        Write-Error $path
    }
}

# Optional: Add tab completion
Register-ArgumentCompleter -CommandName cdr -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
    
    $registryPath = Join-Path $env:USERPROFILE ".nlpm\\cdr_registry.json"
    if (Test-Path $registryPath) {
        $registry = Get-Content $registryPath | ConvertFrom-Json
        $registry.PSObject.Properties.Name | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $registry.$_)
        }
    }
}''')


def _print_cmd_init():
    """Print CMD batch file for cdr."""
    print('''@echo off
REM nlpm cdr CMD integration
REM Save this to a file and run it, or use: for /f "tokens=*" %%a in ('nlpm cdr-init cmd') do @%%a
REM Better: Create a cdr.bat file with the following content:

REM cdr.bat - Save to a folder in your PATH
@echo off
setlocal EnableDelayedExpansion

if "%~1"=="" (
    echo Usage: cdr ^<alias^>
    exit /b 1
)

for /f "tokens=*" %%a in ('nlpm cdr %1') do (
    cd /d "%%a"
    exit /b 0
)

exit /b 1''')
    
    print('''
# Alternative: Add this function to your environment
# (Run this in CMD:)
doskey cdr=for /f "tokens=*" %a in ('nlpm cdr $1') do @cd /d "%a"''')
