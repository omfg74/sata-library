// Планка сверху у задней части отсека, чтобы диск не подпрыгивал.
// Садится на торцы боковых стенок. Печать — отверстиями вверх.

include <params.scad>

module strap_body() {
    difference() {
        cube([outer_w, strap_t, strap_foot]);
        for (x = [wall / 2, outer_w - wall / 2]) {
            translate([x, -0.1, strap_foot / 2])
                rotate([-90, 0, 0])
                    cylinder(h = strap_t + 0.2, d = m3_clear);
        }
    }
}

translate([0, strap_foot, 0])
    rotate([90, 0, 0])
        strap_body();
