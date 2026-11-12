.PHONY: test stl preview

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

stl:
	mkdir -p cad/out
	openscad -o cad/out/bay.stl cad/bay.scad
	openscad -o cad/out/front_plate.stl cad/front_plate.scad
	openscad -o cad/out/strap.stl cad/strap.scad
	openscad -o cad/out/gauge.stl cad/gauge.scad
	openscad -o cad/out/sled.stl cad/sled.scad

preview:
	mkdir -p cad/out
	openscad -o cad/out/assembly.png --imgsize=1400,900 \
		--colorscheme=Tomorrow --projection=ortho \
		--autocenter --viewall \
		--camera=0,0,0,65,0,40,300 \
		cad/assembly.scad
