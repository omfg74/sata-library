// Стойка 1U: четыре уголка, восемь трубок, корзины, одна клипса концевика.
// Трубки здесь только для сборки. Печатаются уголок, корзина и клипса.
include <params.scad>
use <corner.scad>
use <basket.scad>
use <endstop_clip.scad>

width_rod = frame_w - 4;
depth_rod = frame_depth - 2 * depth_z0;
need = rail_t + drive_height;

echo(str("Каркас, мм: ", frame_w, " x ", unit_h, " x ", frame_depth));
echo(str("Трубка по ширине, мм: ", width_rod, "  по глубине, мм: ", depth_rod));
echo(str("Зазор между трубками, мм: ", rod_gap, "  диску с полом нужно ", need));
if (rod_gap < need)
    echo("Трубка толстая для этого юнита: полу корзины не хватает места.");
if (frame_w > opening_w)
    echo("Каркас шире просвета между направляющими.");

module rod_x(length) {
    rotate([0, 90, 0])
        cylinder(h = length, d = rod_d);
}

module rod_z(length) {
    cylinder(h = length, d = rod_d);
}

module frame_corners() {
    corner_solid();
    translate([frame_w, 0, 0])
        mirror([1, 0, 0])
            corner_solid();
    translate([0, 0, frame_depth])
        mirror([0, 0, 1])
            corner_solid();
    translate([frame_w, 0, frame_depth])
        mirror([1, 0, 0])
            mirror([0, 0, 1])
                corner_solid();
}

module frame_rods() {
    for (y = [rod_y0, rod_y1]) {
        translate([2, y, axis_inset])
            rod_x(width_rod);
        translate([2, y, frame_depth - axis_inset])
            rod_x(width_rod);
        translate([axis_inset, y, depth_z0])
            rod_z(depth_rod);
        translate([frame_w - axis_inset, y, depth_z0])
            rod_z(depth_rod);
    }
}

module baskets() {
    for (i = [0 : bay_count - 1]) {
        translate([
            post_x + 0.6 + i * (basket_w + bay_gap),
            rod_y0 + rod_d / 2,
            axis_inset
        ])
            basket();
    }
}

module drives() {
    for (i = [0 : bay_count - 1]) {
        translate([
            post_x + 0.6 + i * (basket_w + bay_gap) + basket_wall + basket_clear / 2,
            rod_y0 + rod_d / 2 + rail_t,
            axis_inset - plug_overhang
        ])
            cube([drive_width, drive_height, drive_length]);
    }
}

color([0.72, 0.70, 0.64])
    frame_corners();
color([0.55, 0.58, 0.62])
    frame_rods();
color([0.38, 0.56, 0.74])
    baskets();
color([0.16, 0.17, 0.19, 0.45])
    drives();
color([0.84, 0.46, 0.24])
    translate([frame_w - axis_inset, rod_y1, depth_z0 + 28])
        rotate([0, -90, 0])
            endstop_clip();
