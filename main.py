# main.py
import argparse
import sys
from src.commands import producer, consumer, misc, script_manager

def main():
    # Check if first argument is a registered script (before argparse kicks in)
    if len(sys.argv) > 1:
        potential_script = sys.argv[1]
        # Don't treat built-in commands or flags as script names
        built_in_commands = {
            "init-lib", "register", "publish", "install", "update", "list",
            "init-script", "register-script", "list-scripts", "help", "--help", "-h",
            "--version", "-v"
        }
        
        if potential_script not in built_in_commands and not potential_script.startswith("-"):
            # Try to run as script
            script_args = sys.argv[2:]  # Pass remaining args to script
            success, exit_code = script_manager.find_and_run_script([potential_script] + script_args)
            if success:
                sys.exit(exit_code if exit_code is not None else 0)
            # If not a script, continue to argparse (will show error)
    
    # Setup argparse for built-in commands
    parser = argparse.ArgumentParser(prog="nlpm", description="NeverLiie Package Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- PRODUCER COMMANDS --
    subparsers.add_parser("init-lib", help="Create nlpm.lib.yaml for library authors")
    subparsers.add_parser("register", help="Register current library in registry")
    
    p_pub = subparsers.add_parser("publish", help="Publish code to registry")
    p_pub.add_argument("--force", action="store_true", help="Overwrite existing version")

    # -- CONSUMER COMMANDS --
    p_inst = subparsers.add_parser("install", help="Install dependencies")
    p_inst.add_argument("target", nargs="?", help="Optional: library:version")
    p_inst.add_argument("--path", help="Destination root folder (only for single install)")

    subparsers.add_parser("update", help="Update all deps in nlpm.yaml to latest")
    subparsers.add_parser("list", help="List registry packages")

    # -- SCRIPT MANAGEMENT COMMANDS --
    subparsers.add_parser("init-script", help="Create nlpm-script.yaml for script registration")
    subparsers.add_parser("register-script", help="Register script from nlpm-script.yaml")
    subparsers.add_parser("list-scripts", help="List all registered global scripts")

    args = parser.parse_args()

    # Dispatch built-in commands
    if args.command == "init-lib":
        producer.init_lib(args)
    elif args.command == "register":
        producer.register(args)
    elif args.command == "publish":
        producer.publish(args)
    elif args.command == "install":
        consumer.install(args)
    elif args.command == "update":
        consumer.update(args)
    elif args.command == "list":
        misc.list_registry(args)
    elif args.command == "init-script":
        script_manager.init_script(args)
    elif args.command == "register-script":
        script_manager.register_script(args)
    elif args.command == "list-scripts":
        script_manager.list_scripts(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        sys.exit(130)  # Standard exit code for SIGINT
