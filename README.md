# nice_view_lgtm

Custom [nice!view](https://nicekeyboards.com/nice-view) status screens for split ZMK keyboards.
Forked from [nice-view-gem](https://github.com/M165437/nice-view-gem) (MIT).

**Left / central half**
- connection status (USB / BT)
- battery as an old-school progress bar: 5 solid squares, 20% each (bolt while charging)
- active layer name in big letters, reading top-to-bottom
- BT profile selector as 5 rhombs (active one filled)

**Right / peripheral half**
- connection status to the central half
- the same block battery bar
- a bongo cat that drums along with the keys pressed on that half

The peripheral never learns the active layer in ZMK, so the layer name lives on the central half.

## Usage

Add the module to `config/west.yml`:

```yaml
manifest:
  remotes:
    - name: zmkfirmware
      url-base: https://github.com/zmkfirmware
    - name: josefan
      url-base: https://github.com/josefan
  projects:
    - name: zmk
      remote: zmkfirmware
      revision: main
      import: app/west.yml
    - name: nice_view_lgtm
      remote: josefan
      revision: main
  self:
    path: config
```

Use `nice_view_lgtm` instead of `nice_view` in `build.yaml`:

```yaml
include:
  - board: nice_nano_v2
    shield: corne_left nice_view_adapter nice_view_lgtm
  - board: nice_nano_v2
    shield: corne_right nice_view_adapter nice_view_lgtm
```

Keep layer `display-name`s at 5 characters or fewer so they fit in the big font
(4 characters use Montserrat 28, 5 use Montserrat 24).

## Options

| Option | Default | |
| --- | --- | --- |
| `CONFIG_NICE_VIEW_WIDGET_INVERTED` | `n` | Invert display colors |
| `CONFIG_NICE_VIEW_LGTM_TAP_MS` | `150` | How long a bongo paw stays down after a key press |

## Changing the bongo cat

The frames are drawn in `tools/gen_bongo.py`. Preview them and regenerate the asset with:

```sh
python3 tools/gen_bongo.py --preview
python3 tools/gen_bongo.py   # writes boards/shields/nice_view_lgtm/assets/bongo.c
```
