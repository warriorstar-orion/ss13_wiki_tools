from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click
import largestinteriorrectangle
from avulto import DMM, Path as p
import rasterio
import rasterio.features
from shapely.geometry import Polygon
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class MapRegion:
    area: p
    color: str
    text: Optional[str] = ""
    alt_colors: Optional[dict[int, str]] = None


SUPPLY_COLOR = "#ff6a00ff"
SUPPLY_AREAS = [
    MapRegion(p("/area/station/maintenance/disposal"), SUPPLY_COLOR, "Mining"),
    MapRegion(p("/area/station/supply/miningdock"), SUPPLY_COLOR, "Mining"),
    MapRegion(p("/area/station/supply/office"), SUPPLY_COLOR, "Cargo"),
    MapRegion(p("/area/station/supply/qm"), SUPPLY_COLOR, "QM"),
    MapRegion(p("/area/station/supply/storage"), SUPPLY_COLOR, "Cargo\nBay"),
]

COMMAND_COLOR = "#0094ffff"
COMMAND_AREAS = [
    MapRegion(p("/area/station/ai_monitored/storage/eva"), COMMAND_COLOR, "EVA"),
    MapRegion(p("/area/station/command/bridge"), COMMAND_COLOR, "Bridge"),
    MapRegion(p("/area/station/command/office/blueshield"), COMMAND_COLOR, "NT\nRep"),
    MapRegion(p("/area/station/command/office/captain"), COMMAND_COLOR, "Cptn."),
    MapRegion(p("/area/station/command/office/captain/bedroom"), COMMAND_COLOR),
    MapRegion(p("/area/station/command/office/ntrep"), COMMAND_COLOR, "NT\nRep"),
    MapRegion(p("/area/station/command/server"), COMMAND_COLOR),
    MapRegion(p("/area/station/command/teleporter"), COMMAND_COLOR),
    MapRegion(p("/area/station/command/vault"), COMMAND_COLOR, "Vlt."),
]

HALLWAY_COLOR = "#fff1adff"
HALLWAY_AREAS = [
    MapRegion(p("/area/station/hallway/primary/aft"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/ne"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/north"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/nw"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/se"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/south"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/sw"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/west"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/fore"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/port"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/starboard/east"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/starboard/west"), HALLWAY_COLOR),
    MapRegion(p("/area/station/security/lobby"), HALLWAY_COLOR),
]

ENGINEERING_COLOR = "#ffd800ff"
ENGINEERING_AREAS = [
    MapRegion(p("/area/station/engineering/break_room"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/control"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/controlroom"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/gravitygenerator"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/hardsuitstorage"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/secure_storage"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/tech_storage"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/maintenance/assembly_line"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/maintenance/electrical"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/public/construction"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/command/office/ce"), ENGINEERING_COLOR, "CE"),
 
]

ATMOS_COLOR = "#00ff90ff"
ATMOS_AREAS = [
    MapRegion(p("/area/station/engineering/atmos"), ATMOS_COLOR),
    MapRegion(p("/area/station/engineering/atmos/control"), ATMOS_COLOR),    
    MapRegion(p("/area/station/engineering/atmos/distribution"), ATMOS_COLOR),
    MapRegion(p("/area/station/engineering/atmos/distribution"), ATMOS_COLOR),
    MapRegion(p("/area/station/maintenance/turbine"), ATMOS_COLOR),
]

MAINTS_COLOR = "#808080ff"
MAINTS_AREAS = [
    MapRegion(p("/area/station/maintenance/abandonedbar"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/aft"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/apmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/apmaint2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/asmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/asmaint2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fore"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fpmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fpmaint2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fsmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/incinerator"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/port"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/storage"), MAINTS_COLOR),
]

PUBLIC_COLOR = "#bfffffff"
PUBLIC_AREAS = [
    MapRegion(p("/area/station/hallway/secondary/garden"), PUBLIC_COLOR, "Grdn."),
    MapRegion(p("/area/station/public/locker"), PUBLIC_COLOR, "Lockers"),
    MapRegion(p("/area/station/public/storage/emergency/port"), PUBLIC_COLOR, "Tools"),
    MapRegion(p("/area/station/public/storage/tools"), PUBLIC_COLOR, "Tools"),
    MapRegion(p("/area/station/public/storage/tools/auxiliary"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/toilet/lockerroom"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/toilet/unisex"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/vacant_office"), PUBLIC_COLOR),
]

SECURITY_COLOR = "#e20000ff"
SECURITY_AREAS = [
    MapRegion(p("/area/station/command/office/hos"), SECURITY_COLOR, "HoS"),
    MapRegion(p("/area/station/legal/courtroom"), SECURITY_COLOR, "Court"),
    MapRegion(p("/area/station/legal/lawoffice"), SECURITY_COLOR, "IAA"),
    MapRegion(p("/area/station/legal/magistrate"), SECURITY_COLOR, "Magi."),
    MapRegion(p("/area/station/security/armory/secure"), SECURITY_COLOR, "Armory"),
    MapRegion(p("/area/station/security/brig"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/checkpoint/secondary"), SECURITY_COLOR, "Chk."),
    MapRegion(p("/area/station/security/evidence"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/execution"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/main"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/permabrig"), SECURITY_COLOR, "Permabrig"),
    MapRegion(p("/area/station/security/prisonlockers"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/processing"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/storage"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/warden"), SECURITY_COLOR, "Wrdn."),
]

ARRIVALS_COLOR = "#b6ff00ff"
ARRIVALS_AREAS = [
    MapRegion(p("/area/shuttle/arrival/station"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/secondary/entry"), ARRIVALS_COLOR, "Arrivals"),
    MapRegion(p("/area/station/hallway/secondary/exit"), ARRIVALS_COLOR, "Escape"),
]

MEDBAY_COLOR = "#6cadd2ff"
MEDBAY_AREAS = [
    MapRegion(p("/area/station/maintenance/aft2"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/chemistry"), MEDBAY_COLOR, "Chem"),
    MapRegion(p("/area/station/medical/coldroom"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/cryo"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/medbay"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/medbay2"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/morgue"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/paramedic"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/reception"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/sleeper"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/storage"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/surgery"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/surgery/observation"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/surgery/primary"), MEDBAY_COLOR, "OR1"),
    MapRegion(p("/area/station/medical/surgery/secondary"), MEDBAY_COLOR, "OR2"),    
]

SOLARS_COLOR = "#005491ff"
SOLARS_AREAS = [
    MapRegion(p("/area/station/maintenance/portsolar"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/starboardsolar"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/auxsolarport"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/auxsolarstarboard"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/port"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/auxport"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/auxstarboard"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/starboard"), SOLARS_COLOR),
]

AREAS = (
    SUPPLY_AREAS
    + COMMAND_AREAS
    + HALLWAY_AREAS
    + ENGINEERING_AREAS
    + ATMOS_AREAS
    + MAINTS_AREAS
    + PUBLIC_AREAS
    + SECURITY_AREAS
    + ARRIVALS_AREAS
    + MEDBAY_AREAS
    + SOLARS_AREAS
)


def render_map(dmm: DMM, output_path: Path, labels: str):
    fnt = ImageFont.truetype("Minimal5x7.ttf", 16)
    image = Image.new(size=(1024, 1024), mode="RGBA")
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"
    for region in AREAS:
        area_points = set()
        for coord in dmm.coords():
            tile = dmm.tiledef(*coord)
            if tile.area_path() == region.area:
                area_points.add((coord[0], coord[1]))

        myarray = np.zeros((256, 256))
        for point in area_points:
            myarray[point] = 1
        myarray = myarray.astype(np.int32)
        polygons = [p[0]["coordinates"] for p in rasterio.features.shapes(myarray)]
        # for idx, polygon in enumerate(polygons):
        #     print(f"{region.area} polygon {idx} = {polygon}\n")
        
        polygon_process_order = list()
        dupe_polygons = set()

        # The last polygon is usually fucked up
        polygons.pop()

        for polygon in polygons:
            tupled_polygon = tuple(x for xs in polygon for x in xs)
            if tupled_polygon in dupe_polygons:
                continue

            # If our first coordinate is space, this is an inner hole in a
            # polygon that's just space, which we want to render last
            first_coordinate = [int(x) for x in reversed(polygon[0][0])]
            print(f"area={region.area} polygon={polygon} first_coordinate={first_coordinate}")
            tiledef = dmm.tiledef(*[int(x) for x in reversed(polygon[0][0])], 1)
            if tiledef.area_path().child_of('/area/space'):
                polygon_process_order.append(tupled_polygon)
            else:
                polygon_process_order.insert(0, tupled_polygon)


        for idx, polygon in enumerate(polygon_process_order):
            print(f"{region.area} polygon {idx} = {polygon}")
            tupled_polygon = tuple(x for xs in polygon for x in xs)
            if tupled_polygon in dupe_polygons:
                continue
            dupe_polygons.add(tupled_polygon)
            color = region.color
            if region.alt_colors and idx in region.alt_colors:
                color = region.alt_colors[idx]

            # If our first coordinate is space, this is an inner hole in a polygon that's just space
            int_coords = list(reversed([int(x) for x in polygon[0]]))
            tiledef = dmm.tiledef(*int_coords, 1)
            if tiledef.area_path().child_of('/area/space'):
                color = "#00000000"
            
            flipped = [(y * 4, (255 - x) * 4) for (x, y) in polygon]
            draw.polygon(flipped, fill=color, outline="#00000000")

            msg = None
            
            # Put the text label on the first polygon, this may be wrong
            # at some point but then we can configure it
            if labels == 'rooms' and region.text and idx == 0:
                msg = region.text
            elif labels == 'polygons':
                msg = str(idx)

            if not labels:
                continue
            lir = largestinteriorrectangle.lir(np.array([flipped], np.int32))
            x, y, width, height = lir
            best_fit_rect = [
                [x, y],
                [x + width, y],
                [x + width, y + height],
                [x, y + height],
            ]
            shapely_poly = Polygon(best_fit_rect)
            centroid = shapely_poly.centroid
            rect = draw.textbbox(xy=(centroid.x, centroid.y), text=msg)
            (left, top, right, bottom) = rect
            text_xy = (
                left - ((right - left) / 2),
                top - ((bottom - top) / 2),
            )
            draw.text(text_xy, msg, fill="black", font=fnt)

    image.save(output_path)


@click.command()
@click.option("--dmm_file", required=True)
@click.option("--labels", type=click.Choice(['rooms', 'polygons', 'none']), default=None)
def main(dmm_file, labels):
    dmm_path = Path(dmm_file)
    dmm = DMM.from_file(dmm_path)
    render_map(dmm, Path(f"./{dmm_path.stem}.png"), labels)


if __name__ == "__main__":
    main()
