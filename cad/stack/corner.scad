// Уголок яруса, 44 мм. В STL левый и правый — печатать файл дважды на ярус.
// Подошвой вниз. Капля гнезда смотрит вверх, крыша отверстия без поддержки.
// Под отверстием порог foot: иначе канал печатается жёлобом и трубка выпадает.
// Хомут через узкую прорезь тянет трубку 6 мм к внешней стенке гнезда.
// Шпилька M4 — сквозной колодец со стенками, не паз.
include <params.scad>

module bore_x(length, radius) {
    rotate([0, 90, 0]) {
        cylinder(h = length, r = radius);
        linear_extrude(length)
            polygon([[-radius, 0], [radius, 0], [0, radius * 1.15]]);
    }
}

module bore_z(length, radius) {
    cylinder(h = length, r = radius);
    linear_extrude(length)
        polygon([[-radius, 0], [radius, 0], [0, radius * 1.15]]);
}

module stack_corner() {
    difference() {
        cube([post_x, unit_h, stack_post_z]);

        translate([rod_hole_x, -0.2, rod_hole_z])
            rotate([-90, 0, 0])
                cylinder(h = unit_h + 0.4, d = m4_clear);

        // Низ, трубка по ширине. Открыто внутрь, на +X.
        translate([post_x - socket_depth, bottom_axis_y, width_axis_z])
            bore_x(socket_depth + 0.2, socket_r);
        translate([
            post_x - socket_depth / 2 - tie_w / 2,
            -0.2,
            width_axis_z - socket_r
        ])
            cube([tie_w, bottom_axis_y + socket_r + 0.4, socket_d]);

        // Верх, трубка по ширине.
        translate([post_x - socket_depth, top_axis_y, width_axis_z])
            bore_x(socket_depth + 0.2, socket_r);
        translate([
            post_x - socket_depth / 2 - tie_w / 2,
            top_axis_y - socket_r,
            width_axis_z - socket_r
        ])
            cube([tie_w, unit_h, socket_d]);

        // Низ, трубка по глубине. Открыто назад, на +Z.
        translate([depth_axis_x, bottom_axis_y, depth_bore_z])
            bore_z(socket_depth + 0.2, socket_r);
        translate([
            depth_axis_x - socket_r,
            -0.2,
            depth_bore_z + socket_depth / 2 - tie_w / 2
        ])
            cube([socket_d, bottom_axis_y + socket_r + 0.4, tie_w]);

        // Верх, трубка по глубине.
        translate([depth_axis_x, top_axis_y, depth_bore_z])
            bore_z(socket_depth + 0.2, socket_r);
        translate([
            depth_axis_x - socket_r,
            top_axis_y - socket_r,
            depth_bore_z + socket_depth / 2 - tie_w / 2
        ])
            cube([socket_d, unit_h, tie_w]);
    }
}

stack_corner();
translate([2 * post_x + 8, 0, 0])
    mirror([1, 0, 0])
        stack_corner();
