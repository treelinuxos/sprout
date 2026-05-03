"""
user config management — per-user .prc files.

each user has their own config in /etc/treelinux/users/<name>.prc.
users can edit their own file freely, but installing packages or
enabling services requires doas.
"""

import os
import sys

from sprout import utils


def create_user_config(username, packages=None, shell=None):
    """create a new user config file.

    username: the username.
    packages: optional list of initial packages.
    shell: optional shell preference.
    """
    utils.require_root("create user config")
    utils.ensure_dirs()

    path = utils.user_config(username)
    if os.path.isfile(path):
        print(f"! user config already exists: {path}")
        sys.exit(1)

    with open(path, "w") as f:
        f.write(f"# {username}'s config\n")
        f.write("\n")

        if packages:
            f.write("packages\n")
            for pkg in packages:
                f.write(f"\t{pkg}\n")
            f.write("\n")

        if shell:
            f.write("user\n")
            f.write(f"\tname {username}\n")
            f.write(f"\tshell {shell}\n")
            f.write("\n")

    print(f"  created user config: {path}")


def get_user_config(username):
    """get a user's config path.

    users can read their own config without root.
    """
    path = utils.user_config(username)
    if not os.path.isfile(path):
        return None
    return path


def list_user_configs():
    """list all user config files.

    returns a list of (username, path) tuples.
    """
    if not os.path.isdir(utils.USER_CONFIG_DIR):
        return []

    configs = []
    for f in os.listdir(utils.USER_CONFIG_DIR):
        if f.endswith(".prc"):
            username = f[:-4]
            configs.append((username, os.path.join(utils.USER_CONFIG_DIR, f)))
    return sorted(configs)


def remove_user_config(username):
    """remove a user config file."""
    utils.require_root("remove user config")

    path = utils.user_config(username)
    if not os.path.isfile(path):
        print(f"! no user config for: {username}")
        sys.exit(1)

    os.unlink(path)
    print(f"  removed: {path}")


def add_to_user_config(username, block_name, items):
    """add items to a block in a user's config.

    username: the username.
    block_name: the block (packages, dotfiles, etc).
    items: list of items to add.
    """
    path = get_user_config(username)
    if path is None:
        print(f"! no user config for: {username}")
        sys.exit(1)

    # check permission — user can only edit their own config
    current_user = os.environ.get("USER", os.environ.get("LOGNAME", ""))
    if username != current_user and not utils.is_root():
        print(f"! cannot edit {username}'s config — requires root", file=sys.stderr)
        sys.exit(1)

    with open(path, "r") as f:
        lines = f.readlines()

    # find the block
    block_found = False
    insert_idx = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == block_name:
            block_found = True
            j = i + 1
            while j < len(lines):
                next_stripped = lines[j].strip()
                if next_stripped == "":
                    j += 1
                    continue
                if next_stripped.startswith("#"):
                    j += 1
                    continue
                if lines[j].startswith("\t"):
                    j += 1
                    continue
                break
            insert_idx = j
            break

    if block_found:
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if i == insert_idx - 1:
                for item in items:
                    new_lines.append(f"\t{item}\n")
        lines = new_lines
    else:
        if lines and lines[-1].strip() != "":
            lines.append("\n")
        lines.append(f"{block_name}\n")
        for item in items:
            lines.append(f"\t{item}\n")

    with open(path, "w") as f:
        f.writelines(lines)

    print(f"  added to {username}'s {block_name}: {', '.join(items)}")


def remove_from_user_config(username, block_name, items):
    """remove items from a block in a user's config."""
    path = get_user_config(username)
    if path is None:
        print(f"! no user config for: {username}")
        sys.exit(1)

    current_user = os.environ.get("USER", os.environ.get("LOGNAME", ""))
    if username != current_user and not utils.is_root():
        print(f"! cannot edit {username}'s config — requires root", file=sys.stderr)
        sys.exit(1)

    with open(path, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if stripped == block_name:
            in_block = True
            new_lines.append(line)
            continue

        if in_block and line.startswith("\t"):
            if stripped in items:
                continue  # skip this line (removing it)
            new_lines.append(line)
        else:
            if in_block:
                in_block = False
            new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    print(f"  removed from {username}'s {block_name}: {', '.join(items)}")
