// Сборка первой примерки: отсек, упор, планка, диск и салазки с зазором.
// Салазки не доведены до диска специально.

include <params.scad>
use <bay.scad>
use <front_plate.scad>
use <strap.scad>
use <sled.scad>

color([0.76, 0.73, 0.66])
    bay();

color([0.38, 0.56, 0.74])
    translate([0, 0, plate_z0])
        front_plate_body();

color([0.42, 0.62, 0.38])
    translate([-wall, wall_h, strap_z - strap_foot / 2])
        strap_body();

color([0.84, 0.46, 0.24])
    translate([drive_width / 2 - sled_w / 2, -11, -24 - sled_t])
        sled();

color([0.16, 0.17, 0.19, 0.55])
    cube([drive_width, drive_height, drive_length]);
