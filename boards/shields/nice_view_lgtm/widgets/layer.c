#include <zephyr/kernel.h>
#include <string.h>
#include "layer.h"

/*
 * Draws the layer name in big letters, reading top-to-bottom on the portrait strip.
 *
 * Text drawn upright in native orientation would read bottom-to-top (portrait top is
 * the native right edge), so the finished canvas is turned 180 degrees.
 */
static void rotate_layer_canvas(lv_obj_t *canvas) {
    static uint8_t tmp[LAYER_CANVAS_BUF_SIZE];
    uint8_t *buf = lv_canvas_get_draw_buf(canvas)->data;
    const int32_t stride = lv_draw_buf_width_to_stride(LAYER_CANVAS_W, CANVAS_COLOR_FORMAT);
    const size_t size = (size_t)stride * LAYER_CANVAS_H;

    memcpy(tmp, buf, size);
    lv_draw_sw_rotate(tmp, buf, LAYER_CANVAS_W, LAYER_CANVAS_H, stride, stride,
                      LV_DISPLAY_ROTATION_180, CANVAS_COLOR_FORMAT);
}

void draw_layer_status(lv_obj_t *canvas, const struct status_state *state) {
    char text[8] = {};

    if (state->layer_label == NULL || state->layer_label[0] == '\0') {
        snprintf(text, sizeof(text), "L%d", state->layer_index);
    } else {
        strncpy(text, state->layer_label, sizeof(text) - 1);
        to_uppercase(text);
    }

    // Montserrat 28 fits ~4 wide capitals in 100 px, 24 fits ~5
    const lv_font_t *font = strlen(text) <= 4 ? &lv_font_montserrat_28 : &lv_font_montserrat_24;

    lv_draw_label_dsc_t label_dsc;
    init_label_dsc(&label_dsc, LVGL_FOREGROUND, font, LV_TEXT_ALIGN_CENTER);

    fill_background(canvas);
    int32_t y = (LAYER_CANVAS_H - lv_font_get_line_height(font)) / 2;
    canvas_draw_text(canvas, 0, y, LAYER_CANVAS_W, &label_dsc, text);

    rotate_layer_canvas(canvas);
}
