#include <zephyr/kernel.h>
#include "battery.h"

LV_IMG_DECLARE(bolt);

/*
 * Old-school progress bar: a frame with a terminal nub, filled with
 * BATTERY_SQUARES solid squares (each square = 100 / BATTERY_SQUARES %).
 */
#define BATTERY_SQUARES 5
#define SQUARE_SIZE 11
#define SQUARE_GAP 1

#define BAR_X 0
#define BAR_Y 17
#define BAR_W (2 + BATTERY_SQUARES * (SQUARE_SIZE + SQUARE_GAP) + 1) /* 63 */
#define BAR_H (2 + SQUARE_GAP * 2 + SQUARE_SIZE)                     /* 15 */

void draw_battery_status(lv_obj_t *canvas, const struct status_state *state) {
    lv_draw_rect_dsc_t fg_dsc;
    init_rect_dsc(&fg_dsc, LVGL_FOREGROUND);
    lv_draw_rect_dsc_t bg_dsc;
    init_rect_dsc(&bg_dsc, LVGL_BACKGROUND);

    // Frame
    canvas_draw_rect(canvas, BAR_X, BAR_Y, BAR_W, BAR_H, &fg_dsc);
    canvas_draw_rect(canvas, BAR_X + 1, BAR_Y + 1, BAR_W - 2, BAR_H - 2, &bg_dsc);

    // Terminal nub
    canvas_draw_rect(canvas, BAR_X + BAR_W, BAR_Y + 4, 3, BAR_H - 8, &fg_dsc);

    // Squares; any charge above zero shows at least one square
    int level = state->battery > 100 ? 100 : state->battery;
    int squares = (level * BATTERY_SQUARES + 99) / 100;

    for (int i = 0; i < squares; i++) {
        canvas_draw_rect(canvas, BAR_X + 2 + i * (SQUARE_SIZE + SQUARE_GAP), BAR_Y + 2,
                         SQUARE_SIZE, SQUARE_SIZE, &fg_dsc);
    }

    // Charging bolt in the free space of the SIG row
    if (state->charging) {
        lv_draw_image_dsc_t img_dsc;
        lv_draw_image_dsc_init(&img_dsc);
        canvas_draw_img(canvas, 32, 3, &bolt, &img_dsc);
    }
}
