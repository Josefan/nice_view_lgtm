/*
 * The Claude Code mascot on the peripheral screen.
 *
 *   idle       still, blinks now and then, taps along with key presses on this half
 *   working    thinking dots + gentle bob          (Claude is working)
 *   needs you  bounce, waving arms, "!" bubble     (Claude waits for permission/input)
 *
 * Status changes arrive as zmk_claude_status_changed (see claude/), key presses as
 * zmk_position_state_changed. All LVGL work happens in the display thread: the
 * listeners' update callbacks and an lv_timer that steps the animation.
 */

#include <zephyr/kernel.h>

#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>

#include "mascot.h"

#if IS_ENABLED(CONFIG_NICE_VIEW_LGTM_CLAUDE)
#include "../claude/claude_status.h"
#else
enum claude_status { CLAUDE_STATUS_IDLE, CLAUDE_STATUS_WORKING, CLAUDE_STATUS_NEEDS_YOU };
#endif

LV_IMG_DECLARE(mascot_idle);
LV_IMG_DECLARE(mascot_blink);
LV_IMG_DECLARE(mascot_tap_left);
LV_IMG_DECLARE(mascot_tap_right);
LV_IMG_DECLARE(mascot_work_0);
LV_IMG_DECLARE(mascot_work_1);
LV_IMG_DECLARE(mascot_work_2);
LV_IMG_DECLARE(mascot_work_3);
LV_IMG_DECLARE(mascot_need_0);
LV_IMG_DECLARE(mascot_need_1);
LV_IMG_DECLARE(mascot_need_2);
LV_IMG_DECLARE(mascot_need_3);

static const lv_image_dsc_t *const work_frames[] = {&mascot_work_0, &mascot_work_1,
                                                    &mascot_work_2, &mascot_work_3};
static const lv_image_dsc_t *const need_frames[] = {&mascot_need_0, &mascot_need_1,
                                                    &mascot_need_2, &mascot_need_3};

#define TICK_MS 150
#define TICKS_PER_FRAME 2 /* animation frames advance every 300 ms */
#define BLINK_EVERY_TICKS 27 /* ~4 s */
#define TAP_TICKS ((CONFIG_NICE_VIEW_LGTM_TAP_MS + TICK_MS - 1) / TICK_MS)
#define NEEDS_YOU_TIMEOUT_TICKS (CONFIG_NICE_VIEW_LGTM_CLAUDE_TIMEOUT_MIN * 60 * 1000 / TICK_MS)

static lv_obj_t *mascot_img;
static const void *shown_src;

static enum claude_status mode = CLAUDE_STATUS_IDLE;
static uint32_t mode_ticks;
static uint32_t tap_ticks_left;
static bool next_tap_left = true;

static void show(const lv_image_dsc_t *src) {
    if (src != shown_src) {
        lv_image_set_src(mascot_img, src);
        shown_src = src;
    }
}

static void set_mode(enum claude_status new_mode) {
    mode = new_mode;
    mode_ticks = 0;
    tap_ticks_left = 0;
}

/* Runs in the display thread (LVGL timer handler). */
static void tick(lv_timer_t *timer) {
    mode_ticks++;

    switch (mode) {
    case CLAUDE_STATUS_WORKING:
        show(work_frames[(mode_ticks / TICKS_PER_FRAME) % ARRAY_SIZE(work_frames)]);
        break;

    case CLAUDE_STATUS_NEEDS_YOU:
        if (mode_ticks >= NEEDS_YOU_TIMEOUT_TICKS) {
            set_mode(CLAUDE_STATUS_IDLE);
            show(&mascot_idle);
            break;
        }
        show(need_frames[(mode_ticks / TICKS_PER_FRAME) % ARRAY_SIZE(need_frames)]);
        break;

    case CLAUDE_STATUS_IDLE:
    default:
        if (tap_ticks_left > 0) {
            if (--tap_ticks_left == 0) {
                show(&mascot_idle);
            }
        } else {
            show(mode_ticks % BLINK_EVERY_TICKS == 0 ? &mascot_blink : &mascot_idle);
        }
        break;
    }
}

/**
 * Key presses: tap along while idle.
 *
 * The display listener only keeps the latest state, so a quick press + release could be
 * coalesced into one update. Count presses instead and react whenever the count changes.
 **/

struct mascot_key_state {
    uint32_t presses;
};

static uint32_t press_count;
static uint32_t presses_seen;

static void key_update_cb(struct mascot_key_state state) {
    if (mascot_img == NULL || state.presses == presses_seen) {
        return;
    }
    presses_seen = state.presses;

    if (mode != CLAUDE_STATUS_IDLE) {
        return;
    }

    show(next_tap_left ? &mascot_tap_left : &mascot_tap_right);
    next_tap_left = !next_tap_left;
    tap_ticks_left = TAP_TICKS;
}

static struct mascot_key_state key_get_state(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *ev =
        eh != NULL ? as_zmk_position_state_changed(eh) : NULL;
    if (ev != NULL && ev->state) {
        press_count++;
    }
    return (struct mascot_key_state){.presses = press_count};
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_mascot_keys, struct mascot_key_state, key_update_cb,
                            key_get_state)
ZMK_SUBSCRIPTION(widget_mascot_keys, zmk_position_state_changed);

/**
 * Claude status
 **/

#if IS_ENABLED(CONFIG_NICE_VIEW_LGTM_CLAUDE)

struct mascot_claude_state {
    uint8_t status;
};

static uint8_t last_status = CLAUDE_STATUS_IDLE;

static void claude_update_cb(struct mascot_claude_state state) {
    if (mascot_img == NULL || state.status == mode) {
        return;
    }
    set_mode((enum claude_status)state.status);
    tick(NULL);
}

static struct mascot_claude_state claude_get_state(const zmk_event_t *eh) {
    const struct zmk_claude_status_changed *ev =
        eh != NULL ? as_zmk_claude_status_changed(eh) : NULL;
    if (ev != NULL) {
        last_status = ev->status;
    }
    return (struct mascot_claude_state){.status = last_status};
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_mascot_claude, struct mascot_claude_state, claude_update_cb,
                            claude_get_state)
ZMK_SUBSCRIPTION(widget_mascot_claude, zmk_claude_status_changed);

#endif /* IS_ENABLED(CONFIG_NICE_VIEW_LGTM_CLAUDE) */

void mascot_init(lv_obj_t *parent) {
    mascot_img = lv_image_create(parent);
    show(&mascot_idle);
    lv_obj_align(mascot_img, LV_ALIGN_TOP_LEFT, MASCOT_X, 0);

    lv_timer_create(tick, TICK_MS, NULL);

    widget_mascot_keys_init();
#if IS_ENABLED(CONFIG_NICE_VIEW_LGTM_CLAUDE)
    widget_mascot_claude_init();
#endif
}
