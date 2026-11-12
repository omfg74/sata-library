// Отсек одного диска 3.5".
// X = 0 у борта-упора, Y = 0 на полу, Z = 0 на задней плоскости диска, +Z к передней.
// Задняя сторона открыта: разъём приезжает с −Z. Уголки задают заднюю плоскость,
// передний винт поджимает диск к ним.

include <params.scad>

module bay() {
    difference() {
        union() {
            translate([-wall, -floor_t, 0])
                cube([outer_w, floor_t, body_z]);
            translate([-wall, -floor_t, 0])
                cube([wall, floor_t + wall_h, body_z]);
            translate([cavity_w, -floor_t, 0])
                cube([wall, floor_t + wall_h, body_z]);
            // Уголок на всю высоту печатается вместе со стеной. 4 мм от борта —
            // ставка, что разъём дальше; это проверяет калибр.
            translate([-wall, 0, -lip_t])
                cube([wall + nib, drive_height, lip_t + 0.02]);
            translate([drive_width - nib, 0, -lip_t])
                cube([nib + side_clearance + wall, drive_height, lip_t + 0.02]);
        }
        for (x = [-wall / 2, cavity_w + wall / 2]) {
            translate([x, wall_h - 12, strap_z])
                rotate([-90, 0, 0])
                    cylinder(h = 14, d = m3_pilot);
        }
        for (x = plate_screw_x) {
            translate([x, -floor_t - 0.1, plate_screw_z])
                rotate([-90, 0, 0])
                    cylinder(h = floor_t + 0.2, d = m3_clear);
        }
    }
}

bay();
