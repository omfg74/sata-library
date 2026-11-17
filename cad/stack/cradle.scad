// Ложемент одного диска. Печатать полом вниз.
// Передний упор не даёт диску выйти вперёд. Торец разъёма открыт:
// сзади только щёчки по 4 мм, вилка SATA и питание проходят посередине.
// Ушки лежат на нижней передней трубке и на средней поперечине.
// В пластик диска не вкручиваться: резьба диска 6-32, здесь её нет.
include <params.scad>

module drive_cradle() {
    lip_top = rail_t + cradle_lip_h;
    z_win0 = cradle_z_drive0 + 2;
    z_win1 = cradle_z_rear - rod_d / 2 - 3;
    rail_w = 12;
    tie_spread = 16;

    difference() {
        union() {
            translate([0.2, 0, 0])
                cube([basket_w - 0.4, rail_t, cradle_z_drive1]);

            for (x = [0, basket_w - basket_wall])
                translate([x, 0, 0])
                    cube([basket_wall, lip_top, cradle_z_end]);

            translate([basket_wall - 0.2, rail_t - 0.2, cradle_z_drive0 - cradle_lip_t])
                cube([basket_w - 2 * basket_wall + 0.4, cradle_lip_h + 0.2, cradle_lip_t]);

            translate([basket_wall - 0.2, rail_t - 0.2, cradle_z_drive1])
                cube([cradle_cheek + 0.2, cradle_lip_h + 0.2, cradle_cheek_t]);
            translate([basket_w - basket_wall - cradle_cheek, rail_t - 0.2, cradle_z_drive1])
                cube([cradle_cheek + 0.2, cradle_lip_h + 0.2, cradle_cheek_t]);
        }

        translate([rail_w, -0.2, z_win0])
            cube([basket_w - 2 * rail_w, rail_t + 0.4, z_win1 - z_win0]);

        for (z = [cradle_z_front, cradle_z_rear])
            for (dx = [-tie_spread / 2, tie_spread / 2])
                translate([basket_w / 2 + dx, -0.2, z])
                    rotate([-90, 0, 0])
                        cylinder(h = rail_t + 0.4, d = tie_hole);
    }
}

drive_cradle();
