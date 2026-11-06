#pragma once

#include <zephyr/kernel.h>
#include <zmk/event_manager.h>

/* Behavior device name; must stay <= 8 characters to fit the split protocol. */
#define CLAUDE_STATUS_BEHAVIOR "cl_stat"

enum claude_status {
    CLAUDE_STATUS_IDLE = 0,
    CLAUDE_STATUS_WORKING = 1,
    CLAUDE_STATUS_NEEDS_YOU = 2,
};

struct zmk_claude_status_changed {
    uint8_t status; /* enum claude_status */
};

ZMK_EVENT_DECLARE(zmk_claude_status_changed);
