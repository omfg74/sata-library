// Уголок 1U. В файле левый и правый — печатать этот STL дважды, получится четыре угла.
// Полом вниз. Трубка вдвигается с торца гнезда и притягивается хомутом к внешней стенке.
// Прорезь хомута узкая, само гнездо закрытое: нижняя трубка несёт корзины.
include <params.scad>

module bore_along_x(length, radius) {
    rotate([0, 90, 0]) {
        cylinder(h = length, r = radius);
        linear_extrude(length)
            polygon([[-radius, 0], [radius, 0], [0, radius * 1.15]]);
    }
}

module bore_along_z(length, radius) {
    cylinder(h = length, r = radius);
    linear_extrude(length)
        polygon([[-radius, 0], [radius, 0], [0, radius * 1.15]]);
}

module corner_solid() {
    difference() {
        cube([post_x, unit_h, post_z]);

        // Верх, вдоль ширины стойки. Открыто на торец +X.
        translate([post_x - socket_depth, top_axis_y, axis_inset])
            bore_along_x(socket_depth + 0.2, socket_r);
        translate([
            post_x - socket_depth / 2 - tie_w / 2,
            top_axis_y - socket_r,
            axis_inset - socket_r
        ])
            cube([tie_w, unit_h, socket_d]);

        // Верх, вдоль глубины. Открыто на торец +Z.
        translate([axis_inset, top_axis_y, depth_z0])
            bore_along_z(socket_depth + 0.2, socket_r);
        translate([
            axis_inset - socket_r,
            top_axis_y - socket_r,
            depth_z0 + socket_depth / 2 - tie_w / 2
        ])
            cube([socket_d, unit_h, tie_w]);

        // Низ, вдоль ширины.
        translate([post_x - socket_depth, bottom_axis_y, axis_inset])
            bore_along_x(socket_depth + 0.2, socket_r);
        translate([
            post_x - socket_depth / 2 - tie_w / 2,
            -0.2,
            axis_inset - socket_r
        ])
            cube([tie_w, bottom_axis_y + socket_r, socket_d]);

        // Низ, вдоль глубины.
        translate([axis_inset, bottom_axis_y, depth_z0])
            bore_along_z(socket_depth + 0.2, socket_r);
        translate([
            axis_inset - socket_r,
            -0.2,
            depth_z0 + socket_depth / 2 - tie_w / 2
        ])
            cube([socket_d, bottom_axis_y + socket_r, tie_w]);
    }
}

corner_solid();
translate([post_x * 2 + 8, 0, 0])
    mirror([1, 0, 0])
        corner_solid();
