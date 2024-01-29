from dataclasses import dataclass
from pathlib import Path

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
    text: str


SUPPLY_COLOR = "#ff6a00ff"
SUPPLY_AREAS = [
    MapRegion(p("/area/station/supply/qm"), SUPPLY_COLOR, "QM"),
    MapRegion(p("/area/station/supply/storage"), SUPPLY_COLOR, "Cargo\nBay"),
    MapRegion(p("/area/station/supply/office"), SUPPLY_COLOR, "Cargo"),
    MapRegion(p("/area/station/supply/miningdock"), SUPPLY_COLOR, "Mining"),
]

COMMAND_COLOR = "#0094ffff"
COMMAND_AREAS = [
    MapRegion(p("/area/station/command/office/ntrep"), COMMAND_COLOR, "NT\nRep"),
]

HALLWAY_COLOR = "#fff1adff"
HALLWAY_AREAS = [
    # TODO(wso): Make separate areas for different area types based on one parent type
    MapRegion(p("/area/station/hallway/primary/aft"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/central/ne"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/central/north"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/central/nw"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/central/se"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/central/south"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/central/sw"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/central/west"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/fore"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/port"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/starboard/east"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/hallway/primary/starboard/west"), HALLWAY_COLOR, ""),
    MapRegion(p("/area/station/security/lobby"), HALLWAY_COLOR, ""),
]

MAINTS_COLOR = "#808080ff"
MAINTS_AREAS = [
    MapRegion(p("/area/station/maintenance/abandonedbar"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/aft"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/aft2"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/apmaint"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/apmaint2"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/asmaint"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/asmaint2"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/assembly_line"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/auxsolarport"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/auxsolarstarboard"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/disposal"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/electrical"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/fore"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/fpmaint"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/fpmaint2"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/fsmaint"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/incinerator"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/port"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/portsolar"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/starboardsolar"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/storage"), MAINTS_COLOR, ""),
    MapRegion(p("/area/station/maintenance/turbine"), MAINTS_COLOR, ""),
]

PUBLIC_COLOR = "#bfffffff"
PUBLIC_AREAS = [
    MapRegion(p("/area/station/public/storage/tools/auxiliary"), PUBLIC_COLOR, ""),
    MapRegion(p("/area/station/public/vacant_office"), PUBLIC_COLOR, ""),
    MapRegion(p("/area/station/public/toilet/lockerroom"), PUBLIC_COLOR, ""),
    MapRegion(p("/area/station/public/locker"), PUBLIC_COLOR, "Lockers"),
]

SECURITY_COLOR = "#e20000ff"
SECURITY_AREAS = [
    MapRegion(p("/area/station/security/checkpoint/secondary"), SECURITY_COLOR, "Chk."),
    MapRegion(p("/area/station/security/permabrig"), SECURITY_COLOR, "Permabrig"),
    MapRegion(p("/area/station/security/execution"), SECURITY_COLOR, ""),
    MapRegion(p("/area/station/security/brig"), SECURITY_COLOR, ""),
    MapRegion(p("/area/station/legal/courtroom"), SECURITY_COLOR, "Court"),
    MapRegion(p("/area/station/legal/lawoffice"), SECURITY_COLOR, "IAA"),
    MapRegion(p("/area/station/legal/magistrate"), SECURITY_COLOR, "Magi."),
    MapRegion(p("/area/station/security/prisonlockers"), SECURITY_COLOR, ""),
    MapRegion(p("/area/station/security/warden"), SECURITY_COLOR, "Wrdn."),
    MapRegion(p("/area/station/security/armory/secure"), SECURITY_COLOR, "Armory"),
    MapRegion(p("/area/station/security/storage"), SECURITY_COLOR, ""),
    MapRegion(p("/area/station/security/main"), SECURITY_COLOR, ""),
    MapRegion(p("/area/station/security/processing"), SECURITY_COLOR, ""),
    MapRegion(p("/area/station/command/office/hos"), SECURITY_COLOR, "HoS"),
    MapRegion(p("/area/station/security/evidence"), SECURITY_COLOR, ""),

]

AREAS = (
    SUPPLY_AREAS
    + COMMAND_AREAS
    + HALLWAY_AREAS
    + MAINTS_AREAS
    + PUBLIC_AREAS
    + SECURITY_AREAS
)


def render_map(dmm: DMM, output_path: Path, include_text: bool):
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
        flipped = [(y * 4, (255 - x) * 4) for (x, y) in polygons[0][0]]
        draw.polygon(flipped, fill=region.color, outline="#00000000")
        if include_text and region.text:
            msg = region.text
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
@click.option("--text/--no-text", default=True)
def main(dmm_file, text):
    dmm_path = Path(dmm_file)
    dmm = DMM.from_file(dmm_path)
    render_map(dmm, Path(f"./{dmm_path.stem}.png"), text)


if __name__ == "__main__":
    main()
