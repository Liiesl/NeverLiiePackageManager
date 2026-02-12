# main.py
import argparse
import sys
from src.commands import producer, consumer, misc, script_manager, dir_registry
from src import config

def main():
    if len(sys.argv) > 1:
        potential_script = sys.argv[1]
        
        if potential_script in ("--version", "-v"):
            print(f"nlpm {config.VERSION}")
            sys.exit(0)
        
        built_in_commands = {
            "init", "list", "register",
            "publish", "install", "update",
            "cdr", "remove-dir", "cdr-init",
            "help", "--help", "-h"
        }
        
        if potential_script not in built_in_commands and not potential_script.startswith("-"):
            script_args = sys.argv[2:]
            found = script_manager.find_and_run_script([potential_script] + script_args)
    
    parser = argparse.ArgumentParser(prog="nlpm", description="NeverLiie Package Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- INIT COMMANDS --
    p_init = subparsers.add_parser("init", help="Initialize configurations")
    init_subparsers = p_init.add_subparsers(dest="subcommand", required=True)
    init_subparsers.add_parser("lib", help="Create nlpm.lib.yaml for library authors")
    init_subparsers.add_parser("script", help="Create nlpm-script.yaml for script registration")

    # -- LIST COMMANDS --
    p_list = subparsers.add_parser("list", help="List items")
    list_subparsers = p_list.add_subparsers(dest="subcommand", required=True)
    list_subparsers.add_parser("packages", help="List registry packages")
    list_subparsers.add_parser("scripts", help="List all registered global scripts")
    list_subparsers.add_parser("dirs", help="List all registered directory aliases")

    # -- REGISTER COMMANDS --
    p_reg = subparsers.add_parser("register", help="Register items")
    reg_subparsers = p_reg.add_subparsers(dest="subcommand", required=True)
    reg_subparsers.add_parser("lib", help="Register current library in registry")
    reg_subparsers.add_parser("script", help="Register script from nlpm-script.yaml")
    
    p_reg_dir = reg_subparsers.add_parser("dir", help="Register directory alias")
    p_reg_dir.add_argument("alias", help="Alias name for the directory")
    p_reg_dir.add_argument("--path", help="Directory path (default: current directory)")
    p_reg_dir.add_argument("--force", action="store_true", help="Overwrite existing alias")

    # -- STANDALONE COMMANDS --
    p_pub = subparsers.add_parser("publish", help="Publish code to registry")
    p_pub.add_argument("--force", action="store_true", help="Overwrite existing version")

    p_inst = subparsers.add_parser("install", help="Install dependencies")
    p_inst.add_argument("target", nargs="?", help="Optional: library:version")
    p_inst.add_argument("--path", help="Destination root folder (only for single install)")

    subparsers.add_parser("update", help="Update all deps in nlpm.yaml to latest")

    p_cdr = subparsers.add_parser("cdr", help="Get directory path for alias (use with shell wrapper)")
    p_cdr.add_argument("alias", help="Directory alias to look up")

    p_rm_dir = subparsers.add_parser("remove-dir", help="Remove a directory alias")
    p_rm_dir.add_argument("alias", help="Alias to remove")

    p_cdr_init = subparsers.add_parser("cdr-init", help="Output shell integration code")
    p_cdr_init.add_argument("shell", choices=["ps", "powershell", "cmd"], help="Shell type (ps, cmd)")

    args = parser.parse_args()

    # Dispatch commands
    if args.command == "init":
        if args.subcommand == "lib":
            producer.init_lib(args)
        elif args.subcommand == "script":
            script_manager.init_script(args)
    elif args.command == "list":
        if args.subcommand == "packages":
            misc.list_registry(args)
        elif args.subcommand == "scripts":
            script_manager.list_scripts(args)
        elif args.subcommand == "dirs":
            dir_registry.list_dirs(args)
    elif args.command == "register":
        if args.subcommand == "lib":
            producer.register(args)
        elif args.subcommand == "script":
            script_manager.register_script(args)
        elif args.subcommand == "dir":
            dir_registry.register_dir(args)
    elif args.command == "publish":
        producer.publish(args)
    elif args.command == "install":
        consumer.install(args)
    elif args.command == "update":
        consumer.update(args)
    elif args.command == "cdr":
        dir_registry.get_dir(args)
    elif args.command == "remove-dir":
        dir_registry.remove_dir(args)
    elif args.command == "cdr-init":
        dir_registry.init_shell(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        sys.exit(130)
