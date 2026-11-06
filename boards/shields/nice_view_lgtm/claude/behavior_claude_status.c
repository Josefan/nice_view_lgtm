/*
 * &cl_stat <status>: raises zmk_claude_status_changed.
 *
 * Global locality: when the central invokes it (see claude_relay.c) ZMK also
 * runs it on every split peripheral, which is how the status reaches the
 * right half's screen.
 */

#define DT_DRV_COMPAT zmk_behavior_claude_status

#include <zephyr/device.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include "claude_status.h"

#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)

static int on_pressed(struct zmk_behavior_binding *binding,
                      struct zmk_behavior_binding_event event) {
    if (binding->param1 > CLAUDE_STATUS_NEEDS_YOU) {
        LOG_WRN("Unknown Claude status %d", binding->param1);
        return -EINVAL;
    }

    raise_zmk_claude_status_changed(
        (struct zmk_claude_status_changed){.status = (uint8_t)binding->param1});
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_released(struct zmk_behavior_binding *binding,
                       struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api behavior_claude_status_driver_api = {
    .binding_pressed = on_pressed,
    .binding_released = on_released,
    .locality = BEHAVIOR_LOCALITY_GLOBAL,
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL,
                        CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &behavior_claude_status_driver_api);

#endif /* DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) */
