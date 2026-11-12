// Короткий ложемент-калибр. Диск кладётся к борту X=0 и на пол Y=0,
// задней плоскостью к Z=0. Линейки торчат назад, к наблюдателю.
// Длинная риска каждые 10 мм, короткая каждые 5. Ноль — угол пола и борта.
// Это измерение, а не посадочный размер разъёма.

include <params.scad>

gauge_len = 32;
ruler = 16;
tick = 0.9;

module x_ticks() {
    for (i = [0:5:100]) {
        translate([i, -0.2, -ruler])
            cube([0.8, tick + 0.2, (i % 10) == 0 ? 10 : 5]);
    }
}

module y_ticks() {
    for (i = [0:5:25]) {
        translate([-wall - tick, i, -ruler])
            cube([tick + 0.2, 0.8, (i % 10) == 0 ? 10 : 5]);
    }
}

module gauge() {
    union() {
        difference() {
            union() {
                translate([-wall, -floor_t, -ruler])
                    cube([outer_w, floor_t, ruler + gauge_len]);
                translate([-wall, -floor_t, -ruler])
                    cube([wall, floor_t + wall_h, ruler + gauge_len]);
                translate([cavity_w, -floor_t, 0])
                    cube([wall, floor_t + wall_h, gauge_len]);
            }
            translate([0, 0, -0.02])
                cube([cavity_w, wall_h + 1, gauge_len + 0.04]);
        }
        x_ticks();
        y_ticks();
    }
}

gauge();
