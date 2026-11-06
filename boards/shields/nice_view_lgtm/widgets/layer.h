#pragma once

#include <lvgl.h>
#include "util.h"

/*
 * The layer name lives on its own canvas kept in native (landscape) orientation,
 * so a word can run along the long axis of the screen.
 * It covers portrait y 42..142 (below the SIG row), i.e. native x 18..118.
 */
#define LAYER_CANVAS_W 100
#define LAYER_CANVAS_H SCREEN_WIDTH
#define LAYER_CANVAS_X 18
#define LAYER_CANVAS_BUF_SIZE                                                                      \
    LV_CANVAS_BUF_SIZE(LAYER_CANVAS_W, LAYER_CANVAS_H,                                             \
                       LV_COLOR_FORMAT_GET_BPP(CANVAS_COLOR_FORMAT), LV_DRAW_BUF_STRIDE_ALIGN)

struct layer_status_state {
    uint8_t index;
    const char *label;
};

void draw_layer_status(lv_obj_t *canvas, const struct status_state *state);
