# sprout

the treelinux package and configuration manager.

prototype implementation in python 3. final version will be rewritten in go.

## status

phase 1 — core parser and cli skeleton.

### done
- `.prc` file parser (list blocks, key-value blocks, includes)
- include resolution with circular reference detection
- cli entry point with all planned commands

### next
- `sprout apply` — apply system.prc to live system
- `sprout diff` — preview changes
- backup and rollback system
- apk integration (install/remove/upgrade)
- .smp module runtime
- doas privilege escalation

## project structure

```
sprout/
├── sprout/          — core library
│   ├── __main__.py  — entry point
│   ├── cli.py       — argument parsing
│   ├── parser.py    — .prc file parser
│   └── utils.py     — shared helpers
├── lib/sprout/      — micropython library for .smp modules
├── tests/           — test suite
├── examples/        — example .prc config files
└── modules/         — sample .smp modules
```

## quick start

```bash
python -m sprout --help
python -m sprout install neovim
python tests/test_parser.py
```

## license

gpl v3
