#!/bin/sh
# Claude Code hook: claude_kbd_hook.sh working|needs|idle
# Records the status synchronously (keeps hook order), then sends it in the
# background so the hook returns immediately. Never fails.
dir="$HOME/.claude/claude-kbd"
mkdir -p "$dir" && printf '%s' "$1" > "$dir/state"
uv="$(command -v uv || echo "$HOME/.local/bin/uv")"
( "$uv" run --quiet --script "$(dirname "$0")/claude_kbd.py" --from-state </dev/null >/dev/null 2>&1 & )
exit 0
