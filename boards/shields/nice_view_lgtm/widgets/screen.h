#pragma once

#include <lvgl.h>
#include <zephyr/kernel.h>
#include "util.h"
#include "layer.h"

struct zmk_widget_screen {
    sys_snode_t node;
    lv_obj_t *obj;
    uint8_t cbuf[CANVAS_BUF_SIZE];       /* top: SIG + battery */
    uint8_t cbuf2[CANVAS_BUF_SIZE];      /* bottom: BT profiles */
    uint8_t cbuf3[LAYER_CANVAS_BUF_SIZE]; /* middle: layer name */
    struct status_state state;
};

int zmk_widget_screen_init(struct zmk_widget_screen *widget, lv_obj_t *parent);
lv_obj_t *zmk_widget_screen_obj(struct zmk_widget_screen *widget);
