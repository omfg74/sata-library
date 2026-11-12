include <params.scad>

// Цилиндр гайки M3. Ось цилиндра — Z вызывающего модуля.
module m3_nut() {
    cylinder(h = m3_nut_t, d = m3_nut_af / cos(30), $fn = 6);
}
