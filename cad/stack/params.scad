// Наборный ярус. Стоит рядом с cad/rack.scad и ту стойку не заменяет.
// Диск, юнит, гнездо 8.4 мм и ширина четырёх отсеков — из ../params.scad.
// Здесь их не копируют: если правка там, ярус подхватит её сам.
include <../params.scad>

$fn = 32;

// Сборка на трубке 6 мм. Гнездо принимает и 8 мм, но тогда диск 26.1 мм
// в юнит 44 мм уже не входит: между трубками остаётся около 29 мм.
m4_clear = 4.4;
board_t = 1.6;
standoff_h = 6;
comp_max = 10;
tray_t = 2.4;
tie_hole = 3.6;

// Плата Pi 4: 85 × 56 мм. Отверстия Ø2.7 под M2.5, шаг 58 × 49,
// отступ 3.5 от левого края и от обеих кромок стороны 56 мм.
// Чертёж Raspberry Pi Ltd RP-008343-DS-1. В пластике проход 2.9 мм.
// https://pip-assets.raspberrypi.com/categories/545-raspberry-pi-4-model-b/documents/RP-008343-DS-1-raspberry-pi-4-mechanical-drawing.pdf
pi_l = 85;
pi_w = 56;
pi_hole_d = 2.9;
pi_pitch_x = 58;
pi_pitch_y = 49;
pi_inset = 3.5;

sata_l = 100;
sata_w = 80;
ctrl_l = 100;
ctrl_w = 100;

// Шпилька M4 не встаёт рядом с гнездом в столбике 12 мм,
// а столбик шире раздвигает каркас за просвет 450 мм.
// Поэтому колодец шпильки — в переднем блоке, гнёзда за ним по глубине.
rod_hole_x = post_x / 2;
rod_hole_z = 5;
socket_gap = 1.6;

width_axis_z = rod_hole_z + m4_clear / 2 + socket_gap + socket_r;
depth_bore_z = width_axis_z + socket_r + socket_gap;
stack_post_z = depth_bore_z + socket_depth;
depth_axis_x = post_x / 2;

// Ложемент. Его z = 0 — передний край ушка.
ear_past = rod_d / 2 + 4;
cradle_lip_t = 2.4;
cradle_cheek_t = 2.4;
cradle_cheek = 4;
cradle_gap_tube = 1.0;
cradle_rear_inset = 22;
cradle_lip_h = 8;

cradle_z_front = ear_past;
cradle_z_drive0 = cradle_z_front + rod_d / 2 + cradle_gap_tube + cradle_lip_t;
cradle_z_drive1 = cradle_z_drive0 + drive_length;
cradle_z_rear = cradle_z_drive1 - cradle_rear_inset;
cradle_z_end = cradle_z_drive1 + cradle_cheek_t;

// Передняя трубка яруса совпадает с гнездом уголка.
cradle_z0 = width_axis_z - cradle_z_front;
drive_z0 = cradle_z0 + cradle_z_drive0;
drive_z1 = cradle_z0 + cradle_z_drive1;
mid_rail_z = cradle_z0 + cradle_z_rear;
cradle_y = rod_y0 + rod_d / 2;

// Задний отсек: кабели и платы лёжа. Договор просит не меньше 90 мм.
// Контрольная плата 100 мм, поэтому между осями трубок лотка 120 мм.
cable_gap = 36;
tray_span = 120;
bay_rail_z = drive_z1 + cable_gap;
rear_width_z = bay_rail_z + tray_span;
stack_depth = rear_width_z + width_axis_z;
tray_len = tray_span + 2 * ear_past;
tray_z0 = bay_rail_z - ear_past;

width_tube_len = frame_w - 2 * (post_x - socket_depth);
depth_tube_len = stack_depth - 2 * depth_bore_z;
rail_end_gap = 0.4;
rail_x0 = depth_axis_x + rod_d / 2 + rail_end_gap;
cross_tube_len = frame_w - 2 * rail_x0;

// Хомут рельса. Оси локальные, сборка совмещает их с трубками.
clamp_dx = 10;
clamp_cz = 12;

stud_extra = 16;
ear_out = 16;
ear_t = 3.2;

sata_tray_w = sata_l + 16;
ctrl_tray_w = ctrl_l + 16;
pi_tray_w = pi_l + 16;

bay_clear = (rear_width_z - rod_d / 2) - drive_z1;
board_stack = tray_t + standoff_h + board_t + comp_max;
