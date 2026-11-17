// Корзина-лоток на две нижние поперечные трубки.
// Печатать полом вниз, без поддержек. К трубкам крепится хомутами.
// z = 0 — ось трубки со стороны каретки.
// z = rod_span — ось дальней трубки. Упор диска стоит перед ней.
// Торец разъёма выступает на plug_overhang к каретке, нижняя трубка его не закрывает.
include <params.scad>

tab_extra = rod_d / 2 + 4;
tie_hole = 3.6;
tie_spread = 16;
lip_h = 8;
lip_t = 2.4;
cheek = 4;
rail_w = 12;

module basket() {
    short_h = rod_gap - 1.0;
    tall_h = min(
        rail_t + drive_height + 6,
        unit_h - (rod_y0 + rod_d / 2) - 1
    );
    z_drive0 = -plug_overhang;
    z_wall0 = z_drive0 - 4;
    z_lip = z_drive0 + drive_length;
    notch = socket_d / 2 + 2;
    z0 = -tab_extra;
    z1 = rod_span + tab_extra;

    difference() {
        union() {
            // Пол чуть уже бортов, борта в него утоплены. Так нет общей грани.
            translate([0.2, 0, z0])
                cube([basket_w - 0.4, rail_t, z1 - z0]);

            for (x = [0, basket_w - basket_wall]) {
                translate([x, 0, z_wall0])
                    cube([basket_wall, short_h, z_lip - z_wall0]);
                translate([x, 0, notch])
                    cube([basket_wall, tall_h, (z_lip - notch) + lip_t]);
            }

            translate([basket_wall, rail_t - 0.2, z_lip])
                cube([basket_w - 2 * basket_wall, lip_h + 0.2, lip_t]);

            translate([basket_wall, rail_t - 0.2, z_wall0])
                cube([cheek, short_h - rail_t + 0.2, 2.4]);
            translate([basket_w - basket_wall - cheek, rail_t - 0.2, z_wall0])
                cube([cheek, short_h - rail_t + 0.2, 2.4]);
        }

        // Окно в полу: по краям остаются рейки, по торцам — ушки под хомут.
        translate([rail_w, -0.2, notch])
            cube([basket_w - 2 * rail_w, rail_t + 0.4, z_lip - notch]);

        for (z = [0, rod_span]) {
            for (x = [-tie_spread / 2, tie_spread / 2]) {
                translate([basket_w / 2 + x, -0.2, z])
                    rotate([-90, 0, 0])
                        cylinder(h = rail_t + 0.4, d = tie_hole);
            }
        }
    }
}

basket();
