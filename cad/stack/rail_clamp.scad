// Хомут Т-стыка: боковая трубка и конец поперечины.
// Подошвой вниз, каналы сверху. Порог под каналом 1.6 мм, прорезь уже трубки.
// В STL левый и правый — печатать файл дважды на ярус (четыре стыка).
// Ложемент на трубку не запирает отдельной клипсой: у него свои отверстия под хомут.
include <params.scad>

module rail_clamp() {
    ch = socket_d;
    floor_y = foot;
    stop_x = clamp_dx + rod_d / 2 + rail_end_gap;
    pocket = 16;
    tall = 12;
    low = cradle_y - 0.4;
    x0 = clamp_dx - ch / 2 - 1.6;
    z0 = 2;

    difference() {
        union() {
            translate([x0, 0, z0])
                cube([ch + 3.2, tall, 22]);
            translate([stop_x - 0.2, 0, clamp_cz - ch / 2 - 1.6])
                cube([pocket + 1.8, low, ch + 3.2]);
        }

        translate([clamp_dx - ch / 2, floor_y, 0])
            cube([ch, tall, 28]);
        translate([stop_x, floor_y, clamp_cz - ch / 2])
            cube([pocket + 2, tall, ch]);

        translate([clamp_dx - ch / 2, -0.2, clamp_cz - tie_w / 2])
            cube([ch, floor_y + 1.4, tie_w]);
        translate([stop_x + pocket / 2 - tie_w / 2, -0.2, clamp_cz - ch / 2])
            cube([tie_w, floor_y + 1.4, ch]);
    }
}

rail_clamp();
translate([64, 0, 0])
    mirror([1, 0, 0])
        rail_clamp();
