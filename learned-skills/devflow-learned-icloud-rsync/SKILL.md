# iCloud Drive + rsync: Pitfalls & Safe Deploy Pattern

## Trigger

Use when:
- Deploying via rsync FROM an iCloud Drive path (`~/Library/Mobile Documents/com~apple~CloudDocs/...`)
- rsync shows "file has vanished" warnings for macOS/iOS system paths
- Server accumulates unexpected directories: `System/`, `Library/`, `Applications/`, `home/`, `etc/`

## The Problem

iCloud Drive uses **placeholder files** — files listed in the directory that are "evicted" to iCloud and not locally present. When rsync scans the source directory, it briefly sees these placeholders in the file listing but they disappear before rsync can transfer them.

This causes:
1. `"file has vanished"` warnings in rsync output (exit code 24 — not a fatal error)
2. If rsync ran previously and the placeholders were momentarily local, system files may have been uploaded to the server

**Exit code 24 = safe to ignore** (files vanished during transfer, not a sync failure).

## Safe rsync from iCloud Drive

```bash
# Use sshpass for non-interactive auth
sshpass -p 'password' rsync -az --delete \
  --exclude='.next' \
  --exclude='node_modules' \
  --exclude='data' \
  --exclude='.git' \
  "/Users/user/Library/Mobile Documents/com~apple~CloudDocs/path/to/project/" \
  user@server:/path/on/server/
```

Key points:
- Use **absolute path** (not `./`) to avoid symlink resolution surprises
- Use `-az` not `-avz` (verbose mode floods output with vanished warnings)
- Separate the rsync and SSH commands with `;` not `&&` — exit code 24 is non-fatal

## Cleanup: Remove Accidentally Uploaded System Dirs

If the server has macOS system directories under the project path:

```bash
# Check for junk directories
ssh user@server "ls /path/to/project/"
# Bad signs: System/, Library/, Applications/, Users/, home/, etc/

# Delete them (careful — verify these aren't real project dirs first)
ssh user@server "rm -rf /path/to/project/System /path/to/project/Library /path/to/project/Applications /path/to/project/home /path/to/project/etc /path/to/project/Users"
```

## Targeted Rsync for Changed Files Only

When the full rsync is slow (cleaning up junk), upload only changed files:

```bash
# Upload specific files without --delete
sshpass -p 'pass' rsync -az --checksum \
  local/file1.tsx \
  local/file2.png \
  user@server:/remote/path/

# Use --checksum to force comparison by content, not timestamp
# (timestamps can differ between iCloud-synced files and server)
```
