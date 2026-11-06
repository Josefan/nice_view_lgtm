/*
 * Central only: turns raw HID reports from the host into &cl_stat invocations.
 *
 * Report format (first bytes of the 32 byte raw HID report):
 *   [0] = 'C' (magic), [1] = status (0 idle, 1 working, 2 needs you)
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

#include <zmk/behavior.h>
#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>
#include <raw_hid/events.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include "claude_status.h"

#define CLAUDE_REPORT_MAGIC 'C'

static atomic_t pending_status = ATOMIC_INIT(CLAUDE_STATUS_IDLE);

/* Invoke from the system work queue, not from the BT/USB callback that raised the report. */
static void relay_work_cb(struct k_work *work) {
    struct zmk_behavior_binding binding = {
        .behavior_dev = CLAUDE_STATUS_BEHAVIOR,
        .param1 = (uint32_t)atomic_get(&pending_status),
    };
    struct zmk_behavior_binding_event event = {
        .position = 0,
        .timestamp = k_uptime_get(),
#if IS_ENABLED(CONFIG_ZMK_SPLIT)
        .source = ZMK_POSITION_STATE_CHANGE_SOURCE_LOCAL,
#endif
    };

    int err = zmk_behavior_invoke_binding(&binding, event, true);
    if (err < 0) {
        LOG_ERR("Failed to invoke %s: %d", CLAUDE_STATUS_BEHAVIOR, err);
        return;
    }
    zmk_behavior_invoke_binding(&binding, event, false);
}

static K_WORK_DEFINE(relay_work, relay_work_cb);

static int raw_hid_listener(const zmk_event_t *eh) {
    const struct raw_hid_received_event *ev = as_raw_hid_received_event(eh);
    if (ev == NULL || ev->length < 2 || ev->data[0] != CLAUDE_REPORT_MAGIC) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    if (ev->data[1] > CLAUDE_STATUS_NEEDS_YOU) {
        LOG_WRN("Ignoring unknown Claude status %d", ev->data[1]);
        return ZMK_EV_EVENT_BUBBLE;
    }

    atomic_set(&pending_status, ev->data[1]);
    k_work_submit(&relay_work);
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(claude_relay, raw_hid_listener);
ZMK_SUBSCRIPTION(claude_relay, raw_hid_received_event);
