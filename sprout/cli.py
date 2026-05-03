"""sprout cli — argument parsing and command dispatch."""

import sys

from sprout.parser import parse, ParseError
from sprout import utils


def run(args):
    """main entry point for sprout cli."""
    if not args:
        _show_usage()
        sys.exit(1)

    command = args[0]

    if command == "--help":
        _show_help()
        sys.exit(0)
    elif command == "--tui":
        _show_tui_notice()
        sys.exit(0)
    elif command == "install":
        _cmd_install(args[1:])
    elif command == "remove":
        _cmd_remove(args[1:])
    elif command == "upgrade":
        _cmd_upgrade(args[1:])
    elif command == "update":
        _cmd_update(args[1:])
    elif command == "apply":
        _cmd_apply(args[1:])
    elif command == "diff":
        _cmd_diff(args[1:])
    elif command == "search":
        _cmd_search(args[1:])
    elif command == "run":
        _cmd_run(args[1:])
    elif command == "user":
        _cmd_user(args[1:])
    elif command == "info":
        _cmd_info(args[1:])
    elif command == "rollback":
        _cmd_rollback(args[1:])
    else:
        print(f"sprout: unknown command '{command}'", file=sys.stderr)
        print("  use 'sprout --help' for help", file=sys.stderr)
        sys.exit(1)


def _show_usage():
    print("sprout: no command given")
    print("  use 'sprout --help' for help")
    print("  use 'sprout --tui' for interactive mode")


def _show_help():
    print("sprout — the treelinux package and configuration manager")
    print()
    print("usage: sprout <command> [options]")
    print()
    print("commands:")
    print("  install <pkg>      install a package and add to system.prc")
    print("  remove <pkg>       remove a package")
    print("  upgrade <pkg>      upgrade a specific package")
    print("  update             safe update all packages")
    print("  update --force     full update (user accepts risk)")
    print("  apply              apply system.prc to the live system")
    print("  diff               preview what would change")
    print("  search <query>     search official package and module repo")
    print("  run <script.smp>   run a module script manually")
    print("  user               manage users")
    print("  info               show installed packages")
    print("  rollback           restore from a backup")
    print("  --tui              launch tui interface")
    print("  --help             show this help")


def _show_tui_notice():
    from sprout.tui import run
    run()


# ---- command stubs ----

def _cmd_install(args):
    if not args:
        print("sprout install: no package specified", file=sys.stderr)
        sys.exit(1)
    from sprout.packages import install, ApkError
    try:
        install(args)
    except ApkError as e:
        print(f"! install failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_remove(args):
    if not args:
        print("sprout remove: no package specified", file=sys.stderr)
        sys.exit(1)
    from sprout.packages import remove, ApkError
    try:
        remove(args)
    except ApkError as e:
        print(f"! remove failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_upgrade(args):
    if not args:
        print("sprout upgrade: no package specified", file=sys.stderr)
        sys.exit(1)
    from sprout.packages import upgrade, ApkError
    try:
        upgrade(args[0] if len(args) == 1 else args)
    except ApkError as e:
        print(f"! upgrade failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_update(args):
    from sprout.packages import upgrade, sync, ApkError
    from sprout.backup import backup, _find_config_files
    from sprout import utils
    force = "--force" in args
    try:
        # backup before updating
        utils.ensure_dirs()
        backup(
            _find_config_files(),
            description="pre-update backup",
        )
        if force:
            print("  force update — upgrading all packages...")
            upgrade()
        else:
            print("  safe update — syncing package database...")
            sync()
            upgrade()
    except ApkError as e:
        print(f"! update failed: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_search(args):
    if not args:
        print("sprout search: no query specified", file=sys.stderr)
        sys.exit(1)
    from sprout.packages import search
    results = search(args[0])
    if not results:
        print(f"  no results for '{args[0]}'")
    else:
        print(f"  results for '{args[0]}':")
        for pkg in results:
            print(f"    {pkg}")


def _cmd_info(args):
    from sprout.packages import list_installed, info as pkg_info
    if args:
        # show info about a specific package
        result = pkg_info(args[0])
        if result is None:
            print(f"  package not found: {args[0]}")
        else:
            print(result)
    else:
        # list all installed
        installed = list_installed()
        print(f"  {len(installed)} installed packages:")
        for pkg in installed:
            print(f"    {pkg}")


def _cmd_run(args):
    if not args:
        print("sprout run: no script specified", file=sys.stderr)
        sys.exit(1)
    from sprout.runner import run_module
    run_module(args[0])


def _cmd_user(args):
    from sprout.users import (
        create_user_config,
        list_user_configs,
        remove_user_config,
        add_to_user_config,
        remove_from_user_config,
        get_user_config,
    )

    if not args:
        # list all users
        configs = list_user_configs()
        if not configs:
            print("  no user configs found")
        else:
            print("user configs:")
            for username, path in configs:
                print(f"  {username} — {path}")
        return

    subcmd = args[0]

    if subcmd == "create":
        if len(args) < 2:
            print("sprout user create <username>", file=sys.stderr)
            sys.exit(1)
        create_user_config(args[1])
    elif subcmd == "remove":
        if len(args) < 2:
            print("sprout user remove <username>", file=sys.stderr)
            sys.exit(1)
        remove_user_config(args[1])
    elif subcmd == "list":
        configs = list_user_configs()
        if not configs:
            print("  no user configs found")
        else:
            for username, path in configs:
                print(f"  {username} — {path}")
    elif subcmd == "add":
        if len(args) < 4:
            print("sprout user add <username> <block> <item>", file=sys.stderr)
            sys.exit(1)
        add_to_user_config(args[1], args[2], args[3:])
    elif subcmd == "remove-item":
        if len(args) < 4:
            print("sprout user remove-item <username> <block> <item>", file=sys.stderr)
            sys.exit(1)
        remove_from_user_config(args[1], args[2], args[3:])
    else:
        print(f"sprout user: unknown subcommand '{subcmd}'", file=sys.stderr)
        sys.exit(1)


def _cmd_info(args):
    print("[todo] info")


def _cmd_rollback(args):
    print("[todo] rollback")
