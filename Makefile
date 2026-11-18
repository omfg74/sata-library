.PHONY: test stl stl-fit stl-stack preview preview-rack

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

stl: stl-fit stl-stack

stl-fit:
	mkdir -p cad/out
	openscad -o cad/out/bay.stl cad/bay.scad
	openscad -o cad/out/front_plate.stl cad/front_plate.scad
	openscad -o cad/out/strap.stl cad/strap.scad
	openscad -o cad/out/gauge.stl cad/gauge.scad
	openscad -o cad/out/sled.stl cad/sled.scad
	openscad -o cad/out/corner.stl cad/corner.scad
	openscad -o cad/out/basket.stl cad/basket.scad
	openscad -o cad/out/endstop_clip.stl cad/endstop_clip.scad

stl-stack:
	mkdir -p cad/out
	openscad -o cad/out/stack-corner.stl cad/stack/corner.scad
	openscad -o cad/out/stack-cradle.stl cad/stack/cradle.scad
	openscad -o cad/out/stack-rail-clamp.stl cad/stack/rail_clamp.scad
	openscad -o cad/out/stack-board-tray.stl cad/stack/board_tray.scad
	openscad -o cad/out/stack-control-tray.stl cad/stack/control_tray.scad
	openscad -o cad/out/stack-host-plate.stl cad/stack/host_plate.scad
	openscad -o cad/out/stack-rack-ear.stl cad/stack/rack_ear.scad

preview-rack:
	mkdir -p cad/out
	openscad -o cad/out/rack.png --imgsize=1600,900 \
		--colorscheme=Tomorrow --projection=ortho \
		--autocenter --viewall \
		--camera=0,0,0,32,0,54,520 \
		cad/rack.scad

preview:
	mkdir -p cad/out
	openscad -o cad/out/assembly.png --imgsize=1400,900 \
		--colorscheme=Tomorrow --projection=ortho \
		--autocenter --viewall \
		--camera=0,0,0,65,0,40,300 \
		cad/assembly.scad
