"""
backup system — config backup and rollback.

every time sprout makes a change it backs up the config:
    /var/treelinux/backups/YYYY-MM-DD/system.prc.zip

each backup contains:
    system.prc          — root config
    users/              — per-user configs (if they exist)
    metadata.json       — timestamp, version, what changed
"""

import json
import os
import shutil
import sys
import zipfile
from datetime import datetime

from sprout import utils


BACKUP_FORMAT_VERSION = "1"


class BackupError(Exception):
    """raised when a backup or rollback operation fails."""
    pass


def backup(config_paths, description="", backup_dir=None):
    """backup the given config files.

    config_paths: list of paths to backup (e.g. [system.prc, users/])
    description: short note about what changed
    backup_dir: override backup dir (for testing)

    returns the backup directory path.
    """
    bdir = backup_dir or utils.BACKUP_DIR
    os.makedirs(bdir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    backup_root = os.path.join(bdir, date_str)

    # avoid overwriting — append counter if needed
    counter = 1
    while os.path.exists(backup_root):
        backup_root = os.path.join(bdir, f"{date_str}-{counter}")
        counter += 1

    os.makedirs(backup_root, exist_ok=True)

    zip_path = os.path.join(backup_root, "system.prc.zip")

    metadata = {
        "format_version": BACKUP_FORMAT_VERSION,
        "timestamp": datetime.now().isoformat(),
        "date": date_str,
        "description": description,
        "files": [],
    }

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in config_paths:
                if not os.path.exists(path):
                    continue
                if os.path.isfile(path):
                    zf.write(path, os.path.basename(path))
                    metadata["files"].append(path)
                elif os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        for f in files:
                            full = os.path.join(root, f)
                            arcname = os.path.relpath(full, os.path.dirname(path))
                            zf.write(full, arcname)
                            metadata["files"].append(full)

        # write metadata
        meta_path = os.path.join(backup_root, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"  backed up to {backup_root}")
        return backup_root

    except Exception as e:
        # clean up on failure
        if os.path.exists(backup_root):
            shutil.rmtree(backup_root)
        raise BackupError(f"backup failed: {e}")


def list_backups(backup_dir=None):
    """list all available backups, newest first.

    returns a list of dicts:
        [{"dir": "...", "date": "...", "description": "...", "files": [...]}, ...]
    """
    bdir = backup_dir or utils.BACKUP_DIR
    if not os.path.isdir(bdir):
        return []

    backups = []
    for entry in sorted(os.listdir(bdir), reverse=True):
        backup_path = os.path.join(bdir, entry)
        if not os.path.isdir(backup_path):
            continue
        meta_path = os.path.join(backup_path, "metadata.json")
        if not os.path.isfile(meta_path):
            continue
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
            backups.append({
                "dir": backup_path,
                "date": meta.get("date", "unknown"),
                "timestamp": meta.get("timestamp", "unknown"),
                "description": meta.get("description", ""),
                "files": meta.get("files", []),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    return backups


def rollback(target=None, force=False, backup_dir=None, system_config=None,
             user_config_dir=None):
    """restore from a backup.

    target: path to a specific backup dir, or None for latest.
    force: skip confirmation prompt.
    backup_dir, system_config, user_config_dir: override for testing.
    """
    bdir = backup_dir or utils.BACKUP_DIR
    sys_conf = system_config or utils.SYSTEM_CONFIG
    usr_dir = user_config_dir or utils.USER_CONFIG_DIR

    backups = list_backups(backup_dir=bdir)
    if not backups:
        print("no backups found")
        sys.exit(1)

    if target is None:
        target = backups[0]["dir"]
    else:
        found = False
        for b in backups:
            if b["dir"] == target:
                found = True
                break
        if not found:
            print(f"backup not found: {target}")
            sys.exit(1)

    zip_path = os.path.join(target, "system.prc.zip")
    if not os.path.isfile(zip_path):
        print(f"no zip found in backup: {target}")
        sys.exit(1)

    if not force:
        print(f"rollback to {target}?")
        print("  this will overwrite:")
        print(f"    {sys_conf}")
        if os.path.isdir(usr_dir):
            for f in os.listdir(usr_dir):
                print(f"    {os.path.join(usr_dir, f)}")
        print("  [y] yes  [n] no")
        answer = input("  > ").strip().lower()
        if answer != "y":
            print("  rollback cancelled")
            return

    # backup current configs before overwriting
    backup(
        _find_config_files(sys_conf, usr_dir),
        description="pre-rollback backup",
        backup_dir=bdir,
    )

    # extract and restore
    extract_dir = os.path.join(bdir, ".rollback_extract")
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

        zip_names = zf.namelist()
        for name in zip_names:
            src = os.path.join(extract_dir, name)
            if not os.path.isfile(src):
                continue

            if name == "system.prc":
                dest = sys_conf
            elif name.startswith("users/"):
                dest = os.path.join(usr_dir, name[6:])
            else:
                continue

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            print(f"  restored: {dest}")
            os.unlink(src)

    # clean up extract dir
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

    print("  rollback complete")


def cleanup(max_age_days=30, backup_dir=None):
    """remove backups older than max_age_days.

    keeps at least 3 backups regardless of age.
    """
    bdir = backup_dir or utils.BACKUP_DIR

    backups = list_backups(backup_dir=bdir)
    if len(backups) <= 3:
        print("  keeping all backups (minimum 3)")
        return

    removed = 0
    cutoff = datetime.now()
    cutoff = cutoff.replace(day=cutoff.day - max_age_days)

    for b in backups:
        try:
            backup_date = datetime.fromisoformat(b["timestamp"])
            if backup_date < cutoff and len(backups) - removed > 3:
                shutil.rmtree(b["dir"])
                removed += 1
                print(f"  removed old backup: {b['dir']}")
        except (ValueError, KeyError):
            continue

    if removed > 0:
        print(f"  cleaned up {removed} old backup(s)")
    else:
        print("  nothing to clean up")


def _find_config_files(system_config=None, user_config_dir=None):
    """find all config files to backup."""
    sys_conf = system_config or utils.SYSTEM_CONFIG
    usr_dir = user_config_dir or utils.USER_CONFIG_DIR
    paths = []
    if os.path.isfile(sys_conf):
        paths.append(sys_conf)
    if os.path.isdir(usr_dir):
        for f in os.listdir(usr_dir):
            if f.endswith(".prc"):
                paths.append(os.path.join(usr_dir, f))
    return paths
