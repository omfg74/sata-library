// Плита Raspberry Pi 4. Только первый ярус. Плитой вниз, бобышки вверх.
// Плата 85 × 56. Отверстия по чертежу Raspberry Pi Ltd RP-008343-DS-1:
// Ø2.7 под M2.5, центры (3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)
// от угла, который напротив разъёмов USB и Ethernet. Шаг 58 × 49.
// В пластике проход 2.9 мм. Винт M2.5 сверху, гайка снизу. Стойка 6 мм.
// Разъёмы USB и Ethernet смотрят на +X, в промежуток между плитами.
include <params.scad>

module pi_plate() {
    z0 = ear_past + rod_d / 2 + ((tray_span - rod_d) - pi_w) / 2;
    x0 = (pi_tray_w - pi_l) / 2;

    difference() {
        union() {
            translate([0.2, 0, 0])
                cube([pi_tray_w - 0.4, tray_t, tray_len]);
            for (hx = [pi_inset, pi_inset + pi_pitch_x])
                for (hz = [pi_inset, pi_inset + pi_pitch_y])
                    translate([x0 + hx, tray_t, z0 + hz])
                        rotate([-90, 0, 0])
                            cylinder(h = standoff_h, d = 7);
        }

        for (z = [ear_past, ear_past + tray_span])
            for (dx = [-8, 8])
                translate([pi_tray_w / 2 + dx, -0.2, z])
                    rotate([-90, 0, 0])
                        cylinder(h = tray_t + 0.4, d = tie_hole);

        for (hx = [pi_inset, pi_inset + pi_pitch_x])
            for (hz = [pi_inset, pi_inset + pi_pitch_y])
                translate([x0 + hx, -0.2, z0 + hz])
                    rotate([-90, 0, 0])
                        cylinder(h = tray_t + standoff_h + 0.4, d = pi_hole_d);
    }
}

pi_plate();
