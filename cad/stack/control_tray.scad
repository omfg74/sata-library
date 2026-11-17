// Лоток контрольной платы. Только первый ярус, рядом с сата-лотком.
// Плита вниз, бобышки вверх. Плата 100 × 100, M3 в (4, 4), (96, 4), (4, 96), (96, 96).
// Правый край — сторона антенны ESP32: борта там нет, полигон под антенной не на плате.
// Стойка 6 мм, винт M3 сверху, гайка снизу. Плату не ставить стоймя.
include <params.scad>

module ctrl_tray() {
    z0 = ear_past + rod_d / 2 + ((tray_span - rod_d) - ctrl_w) / 2;
    x0 = (ctrl_tray_w - ctrl_l) / 2;

    difference() {
        union() {
            translate([0.2, 0, 0])
                cube([ctrl_tray_w - 0.4, tray_t, tray_len]);
            for (hx = [4, 96], hz = [4, 96])
                translate([x0 + hx, tray_t, z0 + hz])
                    rotate([-90, 0, 0])
                        cylinder(h = standoff_h, d = 8);
        }

        for (z = [ear_past, ear_past + tray_span])
            for (dx = [-8, 8])
                translate([ctrl_tray_w / 2 + dx, -0.2, z])
                    rotate([-90, 0, 0])
                        cylinder(h = tray_t + 0.4, d = tie_hole);

        for (hx = [4, 96], hz = [4, 96])
            translate([x0 + hx, -0.2, z0 + hz])
                rotate([-90, 0, 0])
                    cylinder(h = tray_t + standoff_h + 0.4, d = m3_clear);
    }
}

ctrl_tray();
