#include <zephyr/kernel.h>
#include "profile.h"

#define PROFILE_COUNT 5
#define DIAMOND_RADIUS 5 /* 11 px wide */
#define DIAMOND_PITCH 13
#define DIAMOND_CENTER_Y (152 + BUFFER_OFFSET_BOTTOM)

void draw_profile_status(lv_obj_t *canvas, const struct status_state *state) {
    int first_x = (CANVAS_SIZE - (PROFILE_COUNT - 1) * DIAMOND_PITCH) / 2;

    for (int i = 0; i < PROFILE_COUNT; i++) {
        canvas_draw_diamond(canvas, first_x + i * DIAMOND_PITCH, DIAMOND_CENTER_Y,
                            DIAMOND_RADIUS, i == state->active_profile_index);
    }
}
