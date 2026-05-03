"""
.prc file parser.

parses treelinux declarative config files into structured dicts.

format:
    # comments start with #
    block_name
        item1
        item2
        key value

    include other.prc
"""

import os


class ParseError(Exception):
    """raised on .prc syntax errors."""
    pass


def parse(filepath):
    """parse a single .prc file and return a config dict.

    returns:
        {
            "blocks": {
                "packages": ["firefox", "neovim"],
                "services": ["enable networking"],
                "user": {"name": "john", "shell": "zsh"},
                "dotfiles": ["~/.zshrc"],
            },
            "includes": ["networking.prc"],
        }
    """
    blocks = {}
    includes = []
    current_block = None

    with open(filepath, "r") as f:
        for lineno, raw_line in enumerate(f, 1):
            line = raw_line.rstrip("\n\r")

            # skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # include directive (allowed at any level)
            if stripped.startswith("include "):
                includes.append(stripped[8:].strip())
                continue

            # tab-indented line = block item
            if line.startswith("\t"):
                if current_block is None:
                    raise ParseError(
                        f"{filepath}:{lineno}: indented line outside of block"
                    )
                item = stripped
                if not item:
                    raise ParseError(
                        f"{filepath}:{lineno}: empty indented line"
                    )
                # check if it's a key-value pair (contains space but not only space)
                parts = item.split(" ", 1)
                if len(parts) == 2 and _is_kv_pair(current_block, parts[0]):
                    if not isinstance(blocks[current_block], dict):
                        blocks[current_block] = {}
                    blocks[current_block][parts[0]] = parts[1]
                else:
                    # simple list item
                    if not isinstance(blocks.get(current_block), list):
                        blocks[current_block] = []
                    blocks[current_block].append(item)
                continue

            # non-indented, non-include = block header
            if current_block is not None:
                if current_block not in blocks:
                    blocks[current_block] = []
            current_block = stripped
            if current_block in blocks:
                raise ParseError(
                    f"{filepath}:{lineno}: duplicate block '{current_block}'"
                )
            blocks[current_block] = []

    # finalize last block if empty
    if current_block is not None and current_block not in blocks:
        blocks[current_block] = []

    return {"blocks": blocks, "includes": includes}


def _is_kv_pair(block_name, key):
    """check if a block uses key-value pairs."""
    kv_blocks = {"user", "dotfiles"}
    return block_name in kv_blocks


def resolve_includes(config, base_path, include_dirs=None):
    """resolve and merge included .prc files into the config.

    include_dirs: list of directories to search for includes.
                  defaults to /etc/treelinux/modules/ and the dir of base_path.
    """
    if include_dirs is None:
        include_dirs = ["/etc/treelinux/modules", os.path.dirname(base_path)]

    resolved = set()
    _resolve_recursive(config, base_path, include_dirs, resolved)
    return config


def _resolve_recursive(config, base_path, include_dirs, resolved):
    """recursively resolve includes, detecting circular references."""
    abs_base = os.path.abspath(base_path)
    if abs_base in resolved:
        return
    resolved.add(abs_base)

    for include_name in config["includes"]:
        found = _find_include(include_name, include_dirs)
        if found is None:
            raise ParseError(
                f"cannot find include '{include_name}' in {include_dirs}"
            )
        included = parse(found)
        _merge_configs(config, included)
        _resolve_recursive(included, found, include_dirs, resolved)


def _find_include(name, include_dirs):
    """find an include file in the search dirs."""
    for d in include_dirs:
        path = os.path.join(d, name)
        if os.path.isfile(path):
            return path
    return None


def _merge_configs(base, other):
    """merge 'other' config into 'base'."""
    for block_name, block_data in other["blocks"].items():
        if block_name not in base["blocks"]:
            base["blocks"][block_name] = block_data
            continue

        existing = base["blocks"][block_name]
        if isinstance(block_data, list) and isinstance(existing, list):
            # merge lists, deduplicate
            for item in block_data:
                if item not in existing:
                    existing.append(item)
        elif isinstance(block_data, dict) and isinstance(existing, dict):
            existing.update(block_data)
        else:
            # type mismatch — last wins
            base["blocks"][block_name] = block_data
