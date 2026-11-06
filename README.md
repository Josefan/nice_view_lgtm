# nice_view_lgtm

Custom [nice!view](https://nicekeyboards.com/nice-view) status screens for split ZMK keyboards.
Forked from [nice-view-gem](https://github.com/M165437/nice-view-gem) (MIT).

**Left / central half**
- battery as an old-school progress bar at the top: 5 solid squares, 20% each (bolt while charging)
- connection status (USB / BT)
- active layer name in big letters, reading top-to-bottom
- BT profile selector as 5 rhombs (active one filled)

**Right / peripheral half**
- the same block battery bar, then the connection status to the central half
- the Claude Code mascot (Clawd), which
  - taps along with key presses on that half when Claude is idle,
  - shows thinking dots while Claude is **working**,
  - bounces and waves with a "!" bubble when Claude **needs you** (permission prompt).

The peripheral never learns the active layer in ZMK, so the layer name lives on the central half.

## Claude Code status

```
Claude Code hook ─► tools/claude_kbd_hook.sh ─► tools/claude_kbd.py ─► raw HID (BT or USB)
  ─► left half (claude/claude_relay.c) ─► &cl_stat behavior, run on the right half too ─► mascot
```

1. Add [zmk-raw-hid](https://github.com/zzeneg/zmk-raw-hid) to `west.yml` and the
   `raw_hid_adapter` shield to the **left** build only.
2. Install [uv](https://docs.astral.sh/uv/); `claude_kbd.py` pulls in `hidapi` by itself.
3. Check the keyboard is reachable: `tools/claude_kbd.py --probe`, then try
   `tools/claude_kbd.py working`, `needs`, `idle`.
4. Add hooks to `~/.claude/settings.json`:

   | Hook | Status |
   | --- | --- |
   | `UserPromptSubmit`, `PostToolUse` | `working` |
   | `Notification` (matcher `permission_prompt\|elicitation_dialog`) | `needs` |
   | `Stop`, `SessionEnd` | `idle` |

   Each runs `tools/claude_kbd_hook.sh <status>`, which records the status and sends it in the
   background, so hooks never slow Claude Code down or fail when the keyboard is off.

Raw HID report: `'C'`, status (0 idle, 1 working, 2 needs you), padded to 32 bytes.
An unanswered "needs you" falls back to idle after `CONFIG_NICE_VIEW_LGTM_CLAUDE_TIMEOUT_MIN`.

## Usage

Add the module to `config/west.yml`:

```yaml
manifest:
  remotes:
    - name: zmkfirmware
      url-base: https://github.com/zmkfirmware
    - name: josefan
      url-base: https://github.com/josefan
    - name: zzeneg
      url-base: https://github.com/zzeneg
  projects:
    - name: zmk
      remote: zmkfirmware
      revision: main
      import: app/west.yml
    - name: nice_view_lgtm
      remote: josefan
      revision: main
    - name: zmk-raw-hid
      remote: zzeneg
      revision: main
  self:
    path: config
```

Use `nice_view_lgtm` instead of `nice_view` in `build.yaml`:

```yaml
include:
  - board: nice_nano//zmk
    shield: corne_left nice_view_adapter nice_view_lgtm raw_hid_adapter
  - board: nice_nano//zmk
    shield: corne_right nice_view_adapter nice_view_lgtm
```

Keep layer `display-name`s at 5 characters or fewer so they fit in the big font
(4 characters use Montserrat 28, 5 use Montserrat 24).

## Options

| Option | Default | |
| --- | --- | --- |
| `CONFIG_NICE_VIEW_WIDGET_INVERTED` | `n` | Invert display colors |
| `CONFIG_NICE_VIEW_LGTM_TAP_MS` | `150` | How long the mascot's tap pose stays after a key press |
| `CONFIG_NICE_VIEW_LGTM_CLAUDE` | `y` | Claude Code status on the peripheral |
| `CONFIG_NICE_VIEW_LGTM_CLAUDE_TIMEOUT_MIN` | `10` | Minutes before an unanswered "needs you" goes back to idle |

## Changing the mascot

The sprite comes from `tools/source/clawd.png` (the 12×8 base emoji from
[ClawdMoji](https://github.com/afspies/clawdmoji), MIT). `tools/gen_mascot.py` converts it locally
(macOS `sips` → BMP → 1-bit grid) and builds every animation frame from it:

```sh
python3 -I tools/gen_mascot.py --preview   # print all frames
python3 -I tools/gen_mascot.py             # writes boards/shields/nice_view_lgtm/assets/mascot.c
```
