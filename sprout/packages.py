"""
apk integration — package install/remove/upgrade/list via apk.

this wraps alpine's apk package manager so sprout can manage packages
declaratively.
"""

import subprocess
import sys
import os


class ApkError(Exception):
    """raised when an apk command fails."""
    pass


def run_apk(*args, check=True, capture=True):
    """run an apk command, return the result.

    raises ApkError on failure.
    """
    cmd = ["apk"] + list(args)
    try:
        if capture:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
        else:
            result = subprocess.run(cmd, timeout=300)
        if check and result.returncode != 0:
            raise ApkError(
                f"apk failed with code {result.returncode}\n"
                f"stderr: {result.stderr.strip()}"
            )
        return result
    except FileNotFoundError:
        raise ApkError("apk not found — is this an alpine system?")
    except subprocess.TimeoutExpired:
        raise ApkError("apk timed out after 5 minutes")


def install(packages):
    """install one or more packages."""
    if isinstance(packages, str):
        packages = [packages]
    print(f"  installing: {', '.join(packages)}")
    run_apk("add", *packages, capture=False)


def remove(packages, purge=True):
    """remove one or more packages.

    purge=True also removes config files.
    """
    if isinstance(packages, str):
        packages = [packages]
    print(f"  removing: {', '.join(packages)}")
    if purge:
        run_apk("del", "--purge", *packages, capture=False)
    else:
        run_apk("del", *packages, capture=False)


def upgrade(packages=None):
    """upgrade packages.

    if packages is None, upgrade all.
    """
    if packages is None:
        print("  upgrading all packages...")
        run_apk("upgrade", capture=False)
    else:
        if isinstance(packages, str):
            packages = [packages]
        print(f"  upgrading: {', '.join(packages)}")
        run_apk("add", "--upgrade", *packages, capture=False)


def search(query, exact=False):
    """search for packages.

    returns a list of matching package names.
    """
    args = ["search"]
    if exact:
        args.append("-x")
    args.append(query)
    result = run_apk(*args)
    if not result.stdout.strip():
        return []
    return result.stdout.strip().split("\n")


def list_installed():
    """return a sorted list of installed package names."""
    result = run_apk("list", "--installed")
    if not result.stdout.strip():
        return []
    packages = []
    for line in result.stdout.strip().split("\n"):
        # apk list format: "name-version-revision"
        # names can contain hyphens, so split from the right
        parts = line.rsplit("-", 2)
        name = parts[0]
        packages.append(name)
    return sorted(packages)


def is_installed(package):
    """check if a package is installed."""
    result = run_apk("list", "--installed", package, capture=True, check=False)
    return result.returncode == 0 and package in result.stdout


def info(package):
    """get info about a package."""
    result = run_apk("info", package, check=False, capture=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def sync():
    """sync the package database."""
    print("  syncing package database...")
    run_apk("update", capture=False)
