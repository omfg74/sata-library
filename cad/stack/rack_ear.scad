// Ухо стойки на один юнит. Плашмя, фланец на стол.
// Пазы под винт M6 сидят на шаге EIA-310: 6.35, 22.225 и 38.1 мм от низа юнита.
// Ярус 44.0 мм короче шага 44.45, поэтому паз, а не круглое отверстие.
// В STL левое и правое. Для 2U и 3U: openscad -D ear_u=2 или два уха друг на друга.
// Тело яруса остаётся внутри просвета 450 мм. Ухо торчит вперёд, на планку стойки.
include <params.scad>

module ear_slot() {
    d = 6.4;
    span = 8;
    hull() {
        translate([0, -(span - d) / 2, 0])
            cylinder(h = ear_t + 2, d = d);
        translate([0, (span - d) / 2, 0])
            cylinder(h = ear_t + 2, d = d);
    }
}

module rack_ear(u = 1) {
    h = u * unit_h;
    w = ear_out + post_x;
    slot_x = ear_out - 8.25;

    difference() {
        cube([w, h, ear_t]);

        for (i = [0 : u - 1], dy = [6.35, 22.225, 38.1])
            translate([slot_x, i * 44.45 + dy, -1])
                ear_slot();

        for (i = [0 : u - 1], yy = [16, 30], xx = [3, post_x - 3])
            translate([ear_out + xx, i * unit_h + yy, -1])
                cylinder(h = ear_t + 2, d = tie_hole);
    }
}

u_print = is_undef(ear_u) ? 1 : ear_u;
rack_ear(u_print);
translate([2 * (ear_out + post_x) + 8, 0, 0])
    mirror([1, 0, 0])
        rack_ear(u_print);
