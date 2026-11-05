#include <zephyr/kernel.h>

#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>

#include "bongo.h"

LV_IMG_DECLARE(bongo_idle);
LV_IMG_DECLARE(bongo_left);
LV_IMG_DECLARE(bongo_right);

static lv_obj_t *bongo_img;
static lv_timer_t *idle_timer;
static bool next_left = true;

/*
 * The display listener only keeps the latest state, so a quick press + release could be
 * coalesced into one update. Count presses instead and react whenever the count changes.
 */
struct bongo_state {
    uint32_t presses;
};

static uint32_t press_count;
static uint32_t presses_seen;

/* Runs in the display thread (LVGL timer handler). */
static void back_to_idle(lv_timer_t *timer) {
    lv_image_set_src(bongo_img, &bongo_idle);
    lv_timer_pause(timer);
}

static void bongo_update_cb(struct bongo_state state) {
    if (bongo_img == NULL || state.presses == presses_seen) {
        return;
    }
    presses_seen = state.presses;

    // Alternate paws on every key press
    lv_image_set_src(bongo_img, next_left ? &bongo_left : &bongo_right);
    next_left = !next_left;

    lv_timer_reset(idle_timer);
    lv_timer_resume(idle_timer);
}

static struct bongo_state bongo_get_state(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *ev = eh ? as_zmk_position_state_changed(eh) : NULL;
    if (ev != NULL && ev->state) {
        press_count++;
    }
    return (struct bongo_state){.presses = press_count};
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_bongo, struct bongo_state, bongo_update_cb, bongo_get_state)
ZMK_SUBSCRIPTION(widget_bongo, zmk_position_state_changed);

void bongo_init(lv_obj_t *parent) {
    bongo_img = lv_image_create(parent);
    lv_image_set_src(bongo_img, &bongo_idle);
    lv_obj_align(bongo_img, LV_ALIGN_TOP_LEFT, BONGO_X, 0);

    idle_timer = lv_timer_create(back_to_idle, CONFIG_NICE_VIEW_LGTM_TAP_MS, NULL);
    lv_timer_pause(idle_timer);

    widget_bongo_init();
}
