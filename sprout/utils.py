"""shared helpers for sprout."""

import os
import sys


SYSTEM_CONFIG = "/etc/treelinux/system.prc"
USER_CONFIG_DIR = "/etc/treelinux/users"
MODULE_DIR = "/etc/treelinux/modules"
BACKUP_DIR = "/var/treelinux/backups"


def user_config(username):
    """return the path to a user's .prc file."""
    return os.path.join(USER_CONFIG_DIR, f"{username}.prc")


def is_root():
    """check if running as root."""
    return os.geteuid() == 0


def require_root(operation):
    """exit with error if not root."""
    if not is_root():
        print(f"! {operation} requires root privileges", file=sys.stderr)
        print(f"  run with doas sprout ...", file=sys.stderr)
        sys.exit(1)


def ensure_dirs():
    """create required treelinux directories if they don't exist."""
    for d in [USER_CONFIG_DIR, MODULE_DIR, BACKUP_DIR]:
        os.makedirs(d, exist_ok=True)
