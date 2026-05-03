"""
applier — apply system.prc to the live system.

the core command that ties everything together:
1. parse system.prc (with includes)
2. diff against live system
3. backup current config
4. install missing packages
5. prompt before removing anything
6. update system.prc to reflect actual state
"""

import os
import sys

from sprout.parser import parse, resolve_includes
from sprout.diff import diff_config, SystemState
from sprout.packages import install, remove, ApkError
from sprout.backup import backup, _find_config_files
from sprout import utils


def apply(config_path=None, interactive=True, dry_run=False):
    """apply a config file to the live system.

    config_path: path to .prc file (defaults to system.prc)
    interactive: if True, prompt before removing packages
    dry_run: if True, only show what would change
    """
    if config_path is None:
        config_path = utils.SYSTEM_CONFIG

    if not os.path.isfile(config_path):
        print(f"! config not found: {config_path}")
        sys.exit(1)

    # parse and resolve includes
    config = parse(config_path)
    config = resolve_includes(config, config_path)

    # diff
    system_state = SystemState()
    system_state.refresh()
    result = diff_config(config_path, system_state)

    to_install = result["packages"]["to_install"]
    to_remove = result["packages"]["to_remove"]

    # show summary
    if not to_install and not to_remove:
        print("  system is already in sync with config")
        return

    print(f"  changes needed for {config_path}:")

    if to_install:
        print(f"    + {len(to_install)} package(s) to install:")
        for p in to_install:
            print(f"      {p}")

    if to_remove:
        print(f"    - {len(to_remove)} package(s) to remove:")
        for p in to_remove:
            print(f"      {p}")

    print()

    if dry_run:
        print("  (dry run — no changes made)")
        return

    # backup before making changes
    utils.ensure_dirs()
    backup(
        _find_config_files(),
        description=f"pre-apply backup for {os.path.basename(config_path)}",
    )

    # install missing packages
    if to_install:
        print("installing packages...")
        try:
            install(to_install)
        except ApkError as e:
            print(f"! install failed: {e}")
            sys.exit(1)

    # handle removal
    if to_remove:
        if interactive:
            _handle_removal(to_remove, config_path)
        else:
            # non-interactive (boot mode) — just remove
            print("removing packages...")
            try:
                remove(to_remove)
            except ApkError as e:
                print(f"! remove failed: {e}")
                sys.exit(1)

    print("  apply complete")


def _handle_removal(packages, config_path):
    """interactively handle package removal.

    for each package not in config, ask the user:
    [k] keep — add it back to system.prc
    [r] remove — uninstall it
    [i] ignore — do nothing
    """
    from sprout.parser import parse as _parse

    to_remove = []
    to_add_back = []

    for pkg in packages:
        print(f"! {pkg} is installed but not in system.prc")
        print("  [k] keep    — add back to system.prc")
        print("  [r] remove  — uninstall")
        print("  [i] ignore  — do nothing")
        answer = input("  > ").strip().lower()

        if answer == "k":
            to_add_back.append(pkg)
        elif answer == "r":
            to_remove.append(pkg)
        # 'i' or anything else = ignore

    # add kept packages back to config
    if to_add_back:
        _append_to_config(config_path, "packages", to_add_back)
        print(f"  added {', '.join(to_add_back)} to system.prc")

    # remove packages
    if to_remove:
        print("removing packages...")
        try:
            remove(to_remove)
        except ApkError as e:
            print(f"! remove failed: {e}")


def _append_to_config(config_path, block_name, items):
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
            # find where this block ends (next non-indented non-empty non-comment line)
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
