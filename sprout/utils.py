"""shared helpers for sprout."""

import os
import sys


SYSTEM_CONFIG = "/etc/treelinux/system.prc"
USER_CONFIG_DIR = "/etc/treelinux/users"
MODULE_DIR = "/etc/treelinux/modules"
BACKUP_DIR = "/var/treelinux/backups"


def find_module(name):
    """search for a .smp module recursively in module directories.
    
    searches in MODULE_DIR and its subdirectories.
    returns full path if found, None otherwise.
    """
    if not name.endswith(".smp"):
        name = name + ".smp"
    
    for root, dirs, files in os.walk(MODULE_DIR):
        if name in files:
            return os.path.join(root, name)
    return None


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


def append_to_config(config_path, block_name, items):
    """append items to a block in a config file.

    if the block doesn't exist, create it.
    """
    with open(config_path, "r") as f:
        lines = f.readlines()

    # find the block
    block_found = False
    insert_idx = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == block_name:
            block_found = True
            # find where this block ends
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                if next_stripped == "":
                    j += 1
                    continue
                if next_stripped.startswith("#"):
                    j += 1
                    continue
                if next_line.startswith("\t"):
                    j += 1
                    continue
                break
            insert_idx = j
            break

    if block_found:
        # insert items before the block ends
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if i == insert_idx - 1:
                for item in items:
                    new_lines.append(f"\t{item}\n")
        lines = new_lines
    else:
        # create new block at the end
        if lines and lines[-1].strip() != "":
            lines.append("\n")
        lines.append(f"{block_name}\n")
        for item in items:
            lines.append(f"\t{item}\n")

    with open(config_path, "w") as f:
        f.writelines(lines)
