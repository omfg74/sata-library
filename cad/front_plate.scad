// Передний упор. Винт M4 вдоль Z поджимает диск к задним уголкам.
// Два винта M3 снизу держат пластину на полу отсека, гайки сверху низкой полки.
// Файл кладёт деталь гайками вверх.

include <lib.scad>

module front_plate_body() {
    difference() {
        union() {
            cube([cavity_w, plate_bar_h, plate_t]);
            translate([tower_x, 0, 0])
                cube([tower_w, drive_height, plate_t]);
        }
        for (x = plate_screw_x) {
            translate([x, -0.1, plate_t / 2])
                rotate([-90, 0, 0])
                    cylinder(h = plate_bar_h + 0.2, d = m3_clear);
            translate([x, plate_bar_h - m3_nut_t, plate_t / 2])
                rotate([-90, 0, 0])
                    m3_nut();
        }
        translate([drive_width / 2, drive_height / 2, -0.1])
            cylinder(h = plate_t + 0.2, d = pusher_d);
    }
}

// +Y корпуса (гайка) становится +Z принтера.
translate([0, plate_t, 0])
    rotate([90, 0, 0])
        front_plate_body();
