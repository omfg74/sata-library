// Общие размеры первой итерации: один отсек 3.5" и детали вокруг него.
// Корпус диска — SFF-8301, таблица 3-1, класс высоты 26.10 мм (максимум).
// Положение разъёма SATA сюда не зашито: его снимают калибром gauge.scad
// с конкретного диска и только потом переносят в окно салазок.

drive_width = 101.60;
drive_height = 26.10;
drive_length = 147.00;

wall = 4.0;
floor_t = 4.0;
lip_t = 3.0;
nib = 4.0;
side_clearance = 0.8;
top_clearance = 1.5;

front_gap = 3.0;
plate_t = 8.0;
front_extra = front_gap + plate_t;

pusher_d = 4.4;
m3_clear = 3.4;
m3_pilot = 2.6;
m3_nut_af = 5.5;
m3_nut_t = 2.8;

cavity_w = drive_width + side_clearance;
outer_w = cavity_w + 2 * wall;
wall_h = drive_height + top_clearance;
body_z = drive_length + front_extra;

strap_z = 18;
strap_t = 4.0;
strap_foot = 14.0;

plate_screw_x = [14, drive_width - 14];
plate_z0 = drive_length + front_gap;
plate_screw_z = plate_z0 + plate_t / 2;
plate_bar_h = 10;
tower_w = 28;
tower_x = drive_width / 2 - tower_w / 2;

sled_w = 78;
sled_h = 48;
sled_t = 8;
sled_window_w = 50;
sled_window_h = 18;
sled_hole_inset = 6;

$fn = 32;
