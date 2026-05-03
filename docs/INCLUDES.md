# .prc Includes

The .prc format supports including other config files for modular configuration.

## Usage

```prc
# main system.prc
packages
	neovim
include desktop.prc
include networking.prc
```

```prc
# desktop.prc
packages
	firefox
	flwm
```

## Include Search Path

Includes are searched in:
1. `/etc/treelinux/modules/`
2. Directory of the parent .prc file

## Circular Detection

Circular includes are detected and will raise a `ParseError`.

## Merging Rules

- Lists are merged (deduplicated)
- Dicts are merged (last wins for conflicts)
- Nested includes are resolved recursively
