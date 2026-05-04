"""sprout cli — argument parsing and command dispatch."""

import sys


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
        from sprout.tui import run as run_tui
        run_tui()
    elif command == "install":
        _cmd_install(args[1:])
    elif command == "remove":
        _cmd_remove(args[1:])
    elif command == "upgrade":
        _cmd_upgrade(args[1:])
    elif command == "update":
        _cmd_update(args[1:])
    elif command == "modules":
        _cmd_modules(args[1:])
    elif command == "apply":
        from sprout.applier import apply
        apply(interactive=(not "--non-interactive" in args[1:]))
    elif command == "diff":
        from sprout.diff import diff_config, SystemState
        config_path = args[1] if args[1:] else "/etc/treelinux/system.prc"
        state = SystemState()
        state.refresh()
        result = diff_config(config_path, state)
        print("Packages to install:", result["packages"]["to_install"])
        print("Packages to remove:", result["packages"]["to_remove"])
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
    print("  modules            reload/update modules from github")
    print("  user               manage users")
    print("  info               show installed packages")
    print("  rollback           restore from a backup")
    print("  --tui              launch tui interface")
    print("  --help             show this help")


# ---- commands ----

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
    force = "--force" in args
    try:
        backup(_find_config_files(), description="pre-update backup")
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


def _cmd_modules(args):
    """reload/update modules from github."""
    import subprocess
    import os
    
    modules_dir = "/etc/treelinux/modules"
    repo_url = "https://github.com/treelinuxos/sprout-modules.git"
    
    if os.path.isdir(os.path.join(modules_dir, ".git")):
        # update existing repo
        print(f"  updating modules in {modules_dir}...")
        try:
            subprocess.run(
                ["git", "-C", modules_dir, "pull"],
                check=True,
                timeout=60,
            )
            print("  modules updated")
        except subprocess.CalledProcessError as e:
            print(f"! update failed: {e}", file=sys.stderr)
            sys.exit(1)
    elif os.path.isdir(modules_dir) and os.listdir(modules_dir):
        # directory exists but not a git repo - remove and clone
        print(f"  reinstalling modules to {modules_dir}...")
        try:
            subprocess.run(
                ["rm", "-rf", modules_dir],
                check=True,
                timeout=30,
            )
            subprocess.run(
                ["git", "clone", repo_url, modules_dir],
                check=True,
                timeout=60,
            )
            print("  modules installed")
        except subprocess.CalledProcessError as e:
            print(f"! install failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # clone repo
        print(f"  installing modules to {modules_dir}...")
        os.makedirs(modules_dir, exist_ok=True)
        try:
            subprocess.run(
                ["git", "clone", repo_url, modules_dir],
                check=True,
                timeout=60,
            )
            print("  modules installed")
        except subprocess.CalledProcessError as e:
            print(f"! install failed: {e}", file=sys.stderr)
            sys.exit(1)

def _cmd_rollback(args):
    from sprout.backup import rollback, list_backups

    if not args:
        # show available backups
        backups = list_backups()
        if not backups:
            print("  no backups found")
        else:
            print("available backups:")
            for b in backups:
                print(f"  {b['date']} — {b['description']} ({b['dir']})")
        return

    target = args[0]
    force = "--force" in args
    rollback(target=target, force=force)
