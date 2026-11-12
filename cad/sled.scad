// Жёсткие салазки под покупной разъём SATA. Окно по центру — черновик,
// его двигать после калибра. Фаска смотрит на диск (+Z в сборке).
// Четыре отверстия M3 — к будущей каретке. Это примерка руками, не слепой стык.

include <params.scad>

module sled() {
    wx = (sled_w - sled_window_w) / 2;
    wy = (sled_h - sled_window_h) / 2;
    difference() {
        cube([sled_w, sled_h, sled_t]);
        translate([wx, wy, -0.1])
            cube([sled_window_w, sled_window_h, sled_t + 0.2]);
        hull() {
            translate([wx, wy, sled_t - 3.2])
                cube([sled_window_w, sled_window_h, 0.1]);
            translate([wx - 3.5, wy - 3.5, sled_t - 0.1])
                cube([sled_window_w + 7, sled_window_h + 7, 0.1]);
        }
        for (x = [sled_hole_inset, sled_w - sled_hole_inset]) {
            for (y = [sled_hole_inset, sled_h - sled_hole_inset]) {
                translate([x, y, -0.1])
                    cylinder(h = sled_t + 0.2, d = m3_clear);
            }
        }
    }
}

sled();
