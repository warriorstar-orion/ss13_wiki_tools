from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

import toml

import click
from avulto import DMM
import rasterio.features
from shapely.geometry import Polygon
from PIL import Image, ImageDraw, ImageFont

from ss13_blackbox_tools.model import Round


ZOOM_LEVEL = 4

dmm_cache: dict[str, DMM] = dict()

ruin_root = Path(
    "D:/ExternalRepos/third_party/Paradise/_maps/map_files/RandomRuins/SpaceRuins"
)

TRANSITZONE_COLOR = "#440000ff"
RUIN_PADDING_COLOR = "#0000aaff"
SAFE_ZONE_COLOR = "#000000ff"

RUIN_RECT_COLOR = "#444444ff"
RUIN_TILE_COLOR = "#8080ffff"
RUIN_NEARSPACE_COLOR = "#6060a0ff"
TEXT_COLOR = "#ffffffff"


@dataclass(frozen=True)
class RuinPlacement:
    map: str
    coords: tuple[int, int, int]

    def ruin_rect(self):
        ruin_map = dmm_cache[self.map]
        ruin_width = ruin_map.extents[0]
        ruin_height = ruin_map.extents[1]
        ruin_x0 = self.coords[0] - int(ruin_width / 2)
        ruin_y0 = self.coords[1] - int(ruin_height / 2)
        ruin_x1 = ruin_x0 + ruin_width - 1
        ruin_y1 = ruin_y0 + ruin_height - 1

        return [(ruin_x0, ruin_y0), (ruin_x1, ruin_y1)]

    def shapely_rect(self):
        ruin_map = dmm_cache[self.map]
        ruin_rect = self.ruin_rect()
        ruin_x0, ruin_y0 = DMCOORD(*ruin_rect[0])
        # ruin_x0 = ruin_rect[0][0]
        # ruin_y0 = ruin_rect[0][1]
        return [
            [ruin_x0, ruin_y0],
            [ruin_x0 + ruin_map.extents[0], ruin_y0],
            [ruin_x0 + ruin_map.extents[0], ruin_y0 - ruin_map.extents[1]],
            [ruin_x0, ruin_y0 - ruin_map.extents[1]],
        ]


def DMCOORD(x, y):
    return (x - 1, (255 - y - 1))


def render_z_levels(ruin_data, output_path: Path):
    fnt = ImageFont.truetype("ss13_wiki_tools/Minimal5x7.ttf", 16)

    space_ruins: list[RuinPlacement] = list()
    z_levels = set()

    transition_border = 7
    safe_border = 15  # TRANSITIONEDGE + SPACERUIN_MAP_EDGE_PAD
    transition_rect = (
        DMCOORD(transition_border, transition_border),
        DMCOORD(255 - transition_border, 255 - transition_border),
    )

    safe_rect = (
        DMCOORD(transition_border + safe_border, transition_border + safe_border),
        DMCOORD(
            255 - transition_border - safe_border, 255 - transition_border - safe_border
        ),
    )

    for ruin in ruin_data.values():
        coords = [int(c) for c in ruin["coords"].split(",")]
        if coords[2] == 3:
            continue

        space_ruins.append(RuinPlacement(ruin["map"], coords))
        z_levels.add(coords[2])

    for z_level in z_levels:
        image = Image.new(
            size=(255, 255),
            mode="RGBA",
        )
        draw = ImageDraw.Draw(image)
        draw.fontmode = "1"

        draw.rectangle([0, 0, 255, 255], fill=TRANSITZONE_COLOR)

        draw.rectangle(transition_rect, fill=RUIN_PADDING_COLOR)
        draw.rectangle(safe_rect, fill=SAFE_ZONE_COLOR)

        for ruin in space_ruins:
            if ruin.coords[2] != z_level:
                continue

            if ruin.map not in dmm_cache:
                dmm_cache[ruin.map] = DMM.from_file(ruin_root / ruin.map)

            ruin_rect = ruin.ruin_rect()
            print(f"ruin={ruin.map}, coords={ruin.coords}")

            draw.rectangle(
                (DMCOORD(*ruin_rect[0]), DMCOORD(*ruin_rect[1])),
                fill=RUIN_RECT_COLOR,
                outline=None,
            )

            ruin_map = dmm_cache[ruin.map]
            ruin_rect = ruin.ruin_rect()
            ruin_x0, ruin_y0 = ruin_rect[0]
            for coord in ruin_map.coords():
                tile = ruin_map.tiledef(*coord)
                is_space = tile.area_path().child_of("/area/space")
                is_noop = tile.area_path().child_of("/area/template_noop")
                is_nearstation = tile.area_path().child_of("/area/space/nearstation")
                if not is_nearstation and (is_space or is_noop):
                    continue
                if not is_nearstation and tile.turf_path().child_of(
                    "/turf/template_noop"
                ):
                    continue

                color = RUIN_TILE_COLOR
                if is_nearstation:
                    color = RUIN_NEARSPACE_COLOR

                draw.point(
                    [DMCOORD(ruin_x0 + coord[0] - 1, ruin_y0 + coord[1] - 1)],
                    fill=color,
                )

        # Scale up after we draw the rectangles because fuck dealing with trying
        # to calculate offsets of rectangles while drawing them zoomed in
        image = image.resize(
            (255 * ZOOM_LEVEL, 255 * ZOOM_LEVEL), resample=Image.Resampling.NEAREST
        )

        draw = ImageDraw.Draw(image)
        draw.fontmode = "1"

        draw.rectangle(
            (0, 0, 255 * ZOOM_LEVEL - 1, 255 * ZOOM_LEVEL - 1),
            outline=(255, 255, 255),
            fill=None,
        )

        for ruin in space_ruins:
            if ruin.coords[2] != z_level:
                continue

            shapely_coords = ruin.shapely_rect()
            msg = ruin.map.replace(".dmm", "")

            shapely_poly = Polygon(
                [x * ZOOM_LEVEL, y * ZOOM_LEVEL] for x, y in shapely_coords
            )
            centroid = shapely_poly.centroid
            rect = draw.textbbox(xy=(centroid.x, centroid.y), text=msg)
            (left, top, right, bottom) = rect
            text_xy = (
                left - ((right - left) / 2),
                top - ((bottom - top) / 2),
            )
            draw.text(text_xy, msg, fill=TEXT_COLOR, font=fnt)

        for msg, y_pos in (("TRANSITION EDGE", 16), ("RUIN PLACEMENT PADDING", 40)):
            rect = draw.textbbox(xy=(255 * ZOOM_LEVEL / 2, y_pos), text=msg, font=fnt)
            (left, top, right, bottom) = rect
            text_xy = (
                left - ((right - left) / 2),
                top - ((bottom - top) / 2),
            )
            draw.text(text_xy, msg, fill=TEXT_COLOR, font=fnt)

        # draw.text((255*ZOOM_LEVEL / 2, 8), text="transition edge", fill=TEXT_COLOR)
        # draw.text((255*ZOOM_LEVEL / 2, 24), text="ruin placement padding", fill=TEXT_COLOR)

        image.save(output_path / f"space_ruin_{z_level}.png")


@click.command()
@click.option("--output_path", required=True)
@click.option("--round_id", required=True)
def main(output_path, round_id):
    config = toml.load(open("ss13_blackbox_tools/config.toml"))
    connection_string = config["database"]["prod_connection_string"]
    engine = create_engine(connection_string)
    with Session(engine) as session:
        round = session.get(Round, int(round_id))
        if not round.has_feedback("ruin_placement"):
            raise RuntimeError(f"no ruin placement found for round ID {round.id}")

        ruin_placements = round.feedback("ruin_placement")
        output_path = Path(output_path) / str(round.id)
        output_path.mkdir(parents=True, exist_ok=True)
        render_z_levels(ruin_placements, output_path)


if __name__ == "__main__":
    main()
