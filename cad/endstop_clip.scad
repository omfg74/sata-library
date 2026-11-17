// Клипса концевика. Седло садится на трубку 4–8 мм и притягивается хомутом.
// Пластина 2.4 мм вынесена в сторону каретки.
// Два паза с шагом 9.5 мм — KW11-3Z и похожие микрики, винты M2.
// Корпус KW11 около 19.8 x 10.2 x 6.4 мм, отверстия 2.35–2.5 мм.
include <params.scad>

saddle_r = socket_d / 2 + 0.3;
saddle_w = 16;
plate_l = 24;
plate_t = 2.4;
plate_drop = 12;

module endstop_clip() {
    difference() {
        union() {
            translate([-saddle_w / 2, 0, 0])
                rotate([0, 90, 0])
                    cylinder(h = saddle_w, r = saddle_r + plate_t);
            // Пластина заходит в стенку седла, иначе это отдельное тело.
            translate([-plate_l / 2, -plate_drop, -(saddle_r + plate_t + plate_t)])
                cube([plate_l, plate_drop + 6, plate_t + 1.6]);
        }

        translate([-saddle_w / 2 - 0.1, 0, 0])
            rotate([0, 90, 0])
                cylinder(h = saddle_w + 0.2, r = saddle_r);
        // Нижняя корка трубки. По Z не шире отверстия, чтобы не выесть пластину.
        translate([
            -saddle_w / 2 - 0.1,
            -(saddle_r + plate_t + 1),
            -saddle_r
        ])
            cube([saddle_w + 0.2, saddle_r + plate_t + 1, saddle_r * 2]);

        translate([-tie_w / 2, 0, -(saddle_r + plate_t)])
            cube([tie_w, saddle_r + plate_t + 0.2, (saddle_r + plate_t) * 2]);

        for (x = [-switch_pitch / 2, switch_pitch / 2]) {
            translate([
                x - switch_hole_d / 2,
                -plate_drop + 3,
                -(saddle_r + plate_t + plate_t + 0.2)
            ])
                cube([switch_hole_d, 5, plate_t + 2.2]);
        }
    }
}

endstop_clip();
