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
    print("sprout: tui mode coming soon")


# ---- command stubs ----

def _cmd_install(args):
    if not args:
        print("sprout install: no package specified", file=sys.stderr)
        sys.exit(1)
    pkg = args[0]
    print(f"[todo] install {pkg}")


def _cmd_remove(args):
    if not args:
        print("sprout remove: no package specified", file=sys.stderr)
        sys.exit(1)
    pkg = args[0]
    print(f"[todo] remove {pkg}")


def _cmd_upgrade(args):
    if not args:
        print("sprout upgrade: no package specified", file=sys.stderr)
        sys.exit(1)
    pkg = args[0]
    print(f"[todo] upgrade {pkg}")


def _cmd_update(args):
    force = "--force" in args
    print(f"[todo] update (force={force})")


def _cmd_apply(args):
    print("[todo] apply")


def _cmd_diff(args):
    print("[todo] diff")


def _cmd_search(args):
    if not args:
        print("sprout search: no query specified", file=sys.stderr)
        sys.exit(1)
    query = args[0]
    print(f"[todo] search {query}")


def _cmd_run(args):
    if not args:
        print("sprout run: no script specified", file=sys.stderr)
        sys.exit(1)
    script = args[0]
    print(f"[todo] run {script}")


def _cmd_user(args):
    print("[todo] user")


def _cmd_info(args):
    print("[todo] info")


def _cmd_rollback(args):
    print("[todo] rollback")
