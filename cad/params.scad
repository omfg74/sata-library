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

// Каркас 1U. Шаг EIA — 44.45 мм, уголок 44.0 мм, чтобы соседний юнит не тёрся.
// Гнездо 8.4 мм принимает трубку до 8 мм. Хомут тянет её к внешней стенке гнезда.
// При rod_d = 6 между трубками 29 мм: пол корзины 1.6 мм, диск 26.1 мм, воздух ~1 мм.
// При 8 мм диск 26.1 мм в этот юнит уже не входит.
unit_h = 44.0;
rod_d = 6;
socket_d = 8.4;
// 10 мм хватает, чтобы трубка села и хомут её зажал. Столбик тогда 12 мм,
// и четыре корзины остаются внутри просвета 450 мм.
socket_depth = 10;
socket_wall = 1.6;
skin = 0.8;
foot = 1.6;
roof = 1.4;
tie_w = 3.2;
// Просвет между направляющими стойки 19 дюймов — 450 мм.
opening_w = 450;
bay_count = 4;
bay_gap = 1.0;
basket_wall = 1.6;
basket_clear = 0.6;
rail_t = 1.6;
// Торец разъёма выступает за ближнюю трубку к каретке, чтобы трубка не перекрыла SATA.
plug_overhang = 16;
stop_margin = 14;

socket_r = socket_d / 2;
post_x = socket_depth + 2;
axis_inset = skin + socket_r;
bottom_axis_y = foot + socket_r;
top_axis_y = unit_h - roof - socket_r;
depth_z0 = axis_inset + socket_r + socket_wall;
post_z = depth_z0 + socket_depth;
basket_w = drive_width + basket_clear + 2 * basket_wall;
inner_w = bay_count * basket_w + (bay_count - 1) * bay_gap;
frame_w = inner_w + 2 * post_x;
rod_span = drive_length - plug_overhang + stop_margin;
frame_depth = rod_span + 2 * axis_inset;
rod_y0 = foot + rod_d / 2;
rod_y1 = unit_h - roof - rod_d / 2;
rod_gap = (rod_y1 - rod_d / 2) - (rod_y0 + rod_d / 2);

// KW11-3Z: корпус около 19.8 x 10.2 x 6.4 мм, два отверстия 2.35–2.5 мм
// с шагом 9.5 мм под винты M2.
switch_hole_d = 2.5;
switch_pitch = 9.5;

$fn = 32;
