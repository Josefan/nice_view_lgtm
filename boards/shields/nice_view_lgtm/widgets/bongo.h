#pragma once

#include <lvgl.h>
#include "util.h"

/* Frames are 98x68 native; centred in the free area below the battery bar
 * (portrait y 49..147, i.e. native x 13..111). */
#define BONGO_X 13

void bongo_init(lv_obj_t *parent);
