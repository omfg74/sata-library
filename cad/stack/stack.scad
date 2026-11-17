// Сборка для просмотра, не для печати. Ярусы: -D tiers=1|2|3.
// Диски — бруски, трубки — цилиндры, платы — пластины в лотках.
include <params.scad>
use <corner.scad>
use <cradle.scad>
use <rail_clamp.scad>
use <board_tray.scad>
use <control_tray.scad>
use <host_plate.scad>
use <rack_ear.scad>

// Самоприсваивание: -D tiers=2 подменяет значение, без -D остаётся 1.
tiers = is_undef(tiers) ? 1 : tiers;

function mm10(x) = round(x * 10) / 10;

assert(frame_w <= opening_w);
assert(cradle_z_end <= 170);
assert(tray_len <= 170);
assert(stack_post_z <= 170);
assert(bay_clear >= 90);
assert(rod_gap + 0.05 >= rail_t + drive_height);
assert(rod_gap + 0.05 >= board_stack);

echo(str("Каркас яруса, мм: ", mm10(frame_w), " x ", unit_h, " x ", mm10(stack_depth)));
echo(str("Просвет между трубками, мм: ", mm10(rod_gap)));
echo(str("Задний отсек от разъёма до трубки, мм: ", mm10(bay_clear)));
echo(str("Ложемент, мм: ", mm10(basket_w), " x ", mm10(rail_t + cradle_lip_h), " x ", mm10(cradle_z_end)));
echo(str("Лоток, мм: ", mm10(sata_tray_w), " x ", mm10(tray_t + standoff_h), " x ", mm10(tray_len)));

module cut_line(n) {
    echo(str(
        "Ярусов ", n,
        ": ширина ", mm10(width_tube_len), " мм × ", 4 * n,
        ", глубина ", mm10(depth_tube_len), " мм × ", 4 * n,
        ", поперечная ", mm10(cross_tube_len), " мм × ", 2 * n,
        ", шпилька M4 ", mm10(n * unit_h + stud_extra), " мм × 4"
    ));
}

cut_line(1);
cut_line(2);
cut_line(3);
echo(str("Показаны ярусы: ", tiers));

module tube_x(length) {
    rotate([0, 90, 0])
        cylinder(h = length, d = rod_d);
}

module tube_z(length) {
    cylinder(h = length, d = rod_d);
}

module tier_corners() {
    stack_corner();
    translate([frame_w, 0, 0])
        mirror([1, 0, 0])
            stack_corner();
    translate([0, 0, stack_depth])
        mirror([0, 0, 1])
            stack_corner();
    translate([frame_w, 0, stack_depth])
        mirror([1, 0, 0])
            mirror([0, 0, 1])
                stack_corner();
}

module tier_tubes() {
    for (y = [rod_y0, rod_y1]) {
        translate([post_x - socket_depth, y, width_axis_z])
            tube_x(width_tube_len);
        translate([post_x - socket_depth, y, rear_width_z])
            tube_x(width_tube_len);
        translate([depth_axis_x, y, depth_bore_z])
            tube_z(depth_tube_len);
        translate([frame_w - depth_axis_x, y, depth_bore_z])
            tube_z(depth_tube_len);
    }
    for (z = [mid_rail_z, bay_rail_z])
        translate([rail_x0, rod_y0, z])
            tube_x(cross_tube_len);
}

module tier_clamps() {
    translate([depth_axis_x - clamp_dx, 0, 0]) {
        translate([0, 0, mid_rail_z - clamp_cz])
            rail_clamp();
        translate([0, 0, bay_rail_z - clamp_cz])
            rail_clamp();
    }
    translate([frame_w, 0, 0])
        mirror([1, 0, 0])
            translate([depth_axis_x - clamp_dx, 0, 0]) {
                translate([0, 0, mid_rail_z - clamp_cz])
                    rail_clamp();
                translate([0, 0, bay_rail_z - clamp_cz])
                    rail_clamp();
            }
}

module tier_cradles() {
    for (i = [0 : bay_count - 1])
        translate([post_x + i * (basket_w + bay_gap), cradle_y, cradle_z0])
            drive_cradle();
}

module tier_drives() {
    gap_x = (basket_w - drive_width) / 2;
    for (i = [0 : bay_count - 1])
        translate([
            post_x + i * (basket_w + bay_gap) + gap_x,
            cradle_y + rail_t,
            drive_z0
        ])
            cube([drive_width, drive_height, drive_length]);
}

module board_plate(length, width) {
    translate([0, standoff_h, 0])
        cube([length, board_t, width]);
}

module tier_boards(level) {
    sata_x = (frame_w - sata_tray_w) / 2;
    ctrl_x = frame_w - post_x - ctrl_tray_w - 6;
    pi_x = post_x + 6;

    translate([sata_x, cradle_y, tray_z0])
        sata_tray();
    translate([
        sata_x + (sata_tray_w - sata_l) / 2,
        cradle_y + tray_t,
        tray_z0 + ear_past + rod_d / 2 + ((tray_span - rod_d) - sata_w) / 2
    ])
        color([0.20, 0.50, 0.32])
            board_plate(sata_l, sata_w);

    if (level == 0) {
        translate([ctrl_x, cradle_y, tray_z0])
            ctrl_tray();
        translate([
            ctrl_x + (ctrl_tray_w - ctrl_l) / 2,
            cradle_y + tray_t,
            tray_z0 + ear_past + rod_d / 2 + ((tray_span - rod_d) - ctrl_w) / 2
        ])
            color([0.20, 0.38, 0.62])
                board_plate(ctrl_l, ctrl_w);

        translate([pi_x, cradle_y, tray_z0])
            pi_plate();
        translate([
            pi_x + (pi_tray_w - pi_l) / 2,
            cradle_y + tray_t,
            tray_z0 + ear_past + rod_d / 2 + ((tray_span - rod_d) - pi_w) / 2
        ])
            color([0.62, 0.24, 0.28])
                board_plate(pi_l, pi_w);
    }
}

module tier_ears() {
    translate([-ear_out, 0, -ear_t])
        rack_ear(1);
    translate([frame_w, 0, -ear_t])
        mirror([1, 0, 0])
            translate([-ear_out, 0, 0])
                rack_ear(1);
}

module one_tier(level) {
    color([0.76, 0.73, 0.66])
        tier_corners();
    color([0.58, 0.62, 0.66])
        tier_tubes();
    color([0.62, 0.52, 0.40])
        tier_clamps();
    color([0.42, 0.54, 0.60])
        tier_cradles();
    color([0.28, 0.30, 0.34])
        tier_drives();
    color([0.55, 0.58, 0.46])
        tier_boards(level);
    color([0.72, 0.70, 0.64])
        tier_ears();
}

module stack_rods() {
    h = tiers * unit_h + stud_extra;
    for (x = [rod_hole_x, frame_w - rod_hole_x])
        for (z = [rod_hole_z, stack_depth - rod_hole_z])
            translate([x, -stud_extra / 2, z])
                rotate([-90, 0, 0])
                    cylinder(h = h, d = 4);
}

for (level = [0 : tiers - 1])
    translate([0, level * unit_h, 0])
        one_tier(level);

color([0.42, 0.42, 0.46])
    stack_rods();
