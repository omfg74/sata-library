// Лоток сата-платы одного яруса. Плитой вниз, бобышки вверх.
// Плата 100 × 80 лежит длинной стороной поперёк яруса.
// Отверстия M3: (4, 4), (96, 4), (4, 76), (96, 76) от левого ближнего угла платы.
// Бобышка 6 мм — стойка. Винт M3 сверху, гайка снизу плиты. Резьбу не печатать.
// Ушки ложатся на заднюю нижнюю трубку и на трубку отсека.
include <params.scad>

module sata_tray() {
    z0 = ear_past + rod_d / 2 + ((tray_span - rod_d) - sata_w) / 2;
    x0 = (sata_tray_w - sata_l) / 2;

    difference() {
        union() {
            translate([0.2, 0, 0])
                cube([sata_tray_w - 0.4, tray_t, tray_len]);
            for (hx = [4, 96], hz = [4, 76])
                translate([x0 + hx, tray_t, z0 + hz])
                    rotate([-90, 0, 0])
                        cylinder(h = standoff_h, d = 8);
        }

        for (z = [ear_past, ear_past + tray_span])
            for (dx = [-8, 8])
                translate([sata_tray_w / 2 + dx, -0.2, z])
                    rotate([-90, 0, 0])
                        cylinder(h = tray_t + 0.4, d = tie_hole);

        for (hx = [4, 96], hz = [4, 76])
            translate([x0 + hx, -0.2, z0 + hz])
                rotate([-90, 0, 0])
                    cylinder(h = tray_t + standoff_h + 0.4, d = m3_clear);
    }
}

sata_tray();
