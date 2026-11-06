#pragma once

#include <lvgl.h>
#include "util.h"

/* Frames are 100x68 native; they sit in the area below the SIG row
 * (portrait y 48..148, i.e. native x 12..112). */
#define MASCOT_X 12

void mascot_init(lv_obj_t *parent);
