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
    # alt_colors: Optional[dict[int, str]] = None
    map_color_overrides: Optional[dict[str, str]] = None


AI_SAT_COLOR = "#00ffffff"
ARRIVALS_COLOR = "#b6ff00ff"
ATMOS_COLOR = "#00ff90ff"
BOTANY_COLOR = "#43db00ff"
COMMAND_COLOR = "#0094ffff"
ENGINEERING_COLOR = "#ffd800ff"
ESCAPE_POD_COLOR = "#47687fff"
HALLWAY_COLOR = "#fff1adff"
MAINTS_COLOR = "#808080ff"
MEDBAY_COLOR = "#6cadd2ff"
PUBLIC_COLOR = "#bfffffff"
SCIENCE_COLOR = "#b200ffff"
SECURITY_COLOR = "#e20000ff"
SERVICE_COLOR = "#ffb787ff"
SOLARS_COLOR = "#005491ff"
SUPPLY_COLOR = "#ff6a00ff"
DISPOSALS_COLOR = "#dbaf6dff"
QUANTUMPAD_COLOR = "#dbaf6dff"  # same as above at the moment
ASTEROID_COLOR = "#a09078ff"
EMERALD_PLASMA_COLOR = "#bd5d9cff"

# python wiki_department_areamap.py --dmm_file D:/ExternalRepos/third_party/Paradise/_maps/map_files/stations/emeraldstation.dmm
# python wiki_department_areamap.py --dmm_file D:/ExternalRepos/third_party/Paradise/_maps/map_files/stations/cerestation.dmm
# python wiki_department_areamap.py --dmm_file D:/ExternalRepos/third_party/Paradise/_maps/map_files/stations/metastation.dmm
# python wiki_department_areamap.py --dmm_file D:/ExternalRepos/third_party/Paradise/_maps/map_files/stations/deltastation.dmm
# python wiki_department_areamap.py --dmm_file D:/ExternalRepos/third_party/Paradise/_maps/map_files/stations/boxstation.dmm

# The lists of areas are not necessarily in alphabetical order. They may be
# arranged in certain ways because of inner polygon holes having to be drawn in
# a specific order because of specific map layouts.
ASTEROID_AREAS = [
    MapRegion(p("/area/mine/unexplored/cere/civilian"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/research"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/command"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/ai"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/cargo"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/engineering"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/orbiting"), ASTEROID_COLOR),
    MapRegion(p("/area/station/service/clown/secret"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/engineering"), ASTEROID_COLOR),
    MapRegion(p("/area/mine/unexplored/cere/medical"), ASTEROID_COLOR),
    MapRegion(p("/area/station/engineering/atmos/asteroid"), ASTEROID_COLOR),
]

SUPPLY_AREAS = [
    MapRegion(p("/area/station/maintenance/disposal"), SUPPLY_COLOR, "Disposals"),
    MapRegion(p("/area/station/supply/miningdock"), SUPPLY_COLOR, "Mining"),
    MapRegion(p("/area/station/supply/office"), SUPPLY_COLOR, "Cargo"),
    MapRegion(p("/area/station/supply/qm"), SUPPLY_COLOR, "QM"),
    MapRegion(p("/area/station/supply/storage"), SUPPLY_COLOR, "Cargo\nBay"),
    MapRegion(p("/area/station/supply/sorting"), SUPPLY_COLOR),
    MapRegion(p("/area/station/supply/expedition"), SUPPLY_COLOR),
    MapRegion(p("/area/station/supply/warehouse"), SUPPLY_COLOR),
    MapRegion(p("/area/station/supply/break_room"), SUPPLY_COLOR),
]


COMMAND_AREAS = [
    MapRegion(p("/area/station/ai_monitored/storage/eva"), COMMAND_COLOR, "EVA"),
    MapRegion(p("/area/station/command/bridge"), COMMAND_COLOR, "Bridge"),
    MapRegion(p("/area/station/command/meeting_room"), COMMAND_COLOR),
    MapRegion(p("/area/station/command/office/blueshield"), COMMAND_COLOR, "Blue."),
    MapRegion(p("/area/station/command/office/captain"), COMMAND_COLOR, "Cptn."),
    MapRegion(p("/area/station/command/office/captain/bedroom"), COMMAND_COLOR),
    MapRegion(p("/area/station/command/office/hop"), COMMAND_COLOR, "HoP"),
    MapRegion(p("/area/station/command/office/ntrep"), COMMAND_COLOR, "NT\nRep"),
    MapRegion(p("/area/station/command/server"), COMMAND_COLOR),
    MapRegion(p("/area/station/command/teleporter"), COMMAND_COLOR),
    MapRegion(p("/area/station/command/vault"), COMMAND_COLOR, "Vlt."),
    MapRegion(p("/area/station/turret_protected/ai_upload"), COMMAND_COLOR, "AI\nUpl."),
    MapRegion(p("/area/station/turret_protected/ai_upload/foyer"), COMMAND_COLOR),
]


HALLWAY_AREAS = [
    MapRegion(p("/area/station/hallway/primary/aft"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/ne"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/north"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/nw"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/se"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/sw"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/west"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/east"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/fore"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/port"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/starboard/east"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/starboard/west"), HALLWAY_COLOR),
    MapRegion(p("/area/station/security/lobby"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/secondary/bridge"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/central/south"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/starboard"), HALLWAY_COLOR),
    # Cargo lobby extends into hallway on Metastation
    MapRegion(p("/area/station/supply/lobby"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/port/north"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/port/east"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/port/west"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/port/south"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/aft/north"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/aft/south"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/aft/west"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/fore"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/fore/north"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/fore/east"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/fore/west"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/aft/east"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/primary/starboard/south"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/servsci"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/serveng"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/sercom"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/medcargo"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/dockmed"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/comeng"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/scidock"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/engmed"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/cargocom"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/security/south"), HALLWAY_COLOR),
    MapRegion(p("/area/station/hallway/spacebridge/security/west"), HALLWAY_COLOR),
    
    MapRegion(p("/area/station/hallway/primary/starboard/north"), HALLWAY_COLOR),
]

ENGINEERING_AREAS = [
    MapRegion(p("/area/station/command/office/ce"), ENGINEERING_COLOR, "CE"),
    MapRegion(p("/area/station/engineering/break_room"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/control"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/controlroom"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/equipmentstorage"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/gravitygenerator"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/hardsuitstorage"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/secure_storage"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/smes"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/tech_storage"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/maintenance/assembly_line"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/maintenance/electrical"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/public/construction"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/ai_transit_tube"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/engine/supermatter"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/maintenance/electrical_shop"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/break_room/secondary"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/atmos/asteroid_filtering"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/atmos/asteroid_maint"), ENGINEERING_COLOR),
    MapRegion(p("/area/station/engineering/atmos/storage"), ENGINEERING_COLOR),
]

ATMOS_AREAS = [
    MapRegion(p("/area/station/engineering/atmos"), ATMOS_COLOR),
    MapRegion(p("/area/station/engineering/atmos/control"), ATMOS_COLOR),
    MapRegion(p("/area/station/engineering/atmos/distribution"), ATMOS_COLOR),
    MapRegion(p("/area/station/engineering/atmos/distribution"), ATMOS_COLOR),
    MapRegion(p("/area/station/maintenance/turbine"), ATMOS_COLOR),
    MapRegion(p("/area/station/maintenance/incinerator"), ATMOS_COLOR, "Incin."),
]

MAINTS_AREAS = [
    MapRegion(p("/area/station/maintenance/abandonedbar"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/aft"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/apmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/apmaint2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/asmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/asmaint2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fore"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fpmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fpmaint2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fsmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fsmaint2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/port"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/port2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/storage"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/maintcentral"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/starboard"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/starboard2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/medmaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/xenobio_north"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/xenobio_south"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/fore2"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/spacehut"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/engimaint"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/abandoned_garden"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/gambling_den"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/library"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/theatre"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/north"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/dorms/port"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/dorms/aft"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/dorms/fore"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/dorms/starboard"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/security"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/security/aft_port"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/security/aft_starboard"), MAINTS_COLOR),
    MapRegion(p("/area/station/maintenance/security/fore"), MAINTS_COLOR),
]

PUBLIC_AREAS = [
    MapRegion(p("/area/station/public/fitness"), PUBLIC_COLOR),
    MapRegion(p("/area/station/hallway/secondary/garden"), PUBLIC_COLOR, "Grdn."),
    MapRegion(p("/area/station/public/arcade"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/dorms"), PUBLIC_COLOR, "Dorms"),
    MapRegion(p("/area/station/public/locker"), PUBLIC_COLOR, "Lockers"),
    MapRegion(p("/area/station/public/mrchangs"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/sleep"), PUBLIC_COLOR, "Cryo"),
    MapRegion(p("/area/station/public/sleep/secondary"), PUBLIC_COLOR, "Cryo"),
    MapRegion(p("/area/station/public/storage/emergency/port"), PUBLIC_COLOR, "Tools"),
    MapRegion(p("/area/station/public/storage/tools"), PUBLIC_COLOR, "Tools"),
    MapRegion(p("/area/station/public/storage/tools/auxiliary"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/toilet/lockerroom"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/toilet/unisex"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/toilet"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/vacant_office"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/storefront"), PUBLIC_COLOR),
    MapRegion(p("/area/station/service/barber"), PUBLIC_COLOR),
    MapRegion(p("/area/station/science/robotics/showroom"), PUBLIC_COLOR),
    MapRegion(p("/area/station/service/cafeteria"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/storage/office"), PUBLIC_COLOR),
    MapRegion(p("/area/holodeck/alphadeck"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/shops"), PUBLIC_COLOR),
    MapRegion(p("/area/station/public/park"), PUBLIC_COLOR),
    MapRegion(p("/area/station/maintenance/abandoned_office"), PUBLIC_COLOR),
]

SECURITY_AREAS = [
    MapRegion(p("/area/station/command/office/hos"), SECURITY_COLOR, "HoS"),
    MapRegion(p("/area/station/legal/courtroom"), SECURITY_COLOR, "Court"),
    MapRegion(p("/area/station/legal/lawoffice"), SECURITY_COLOR, "IAA"),
    MapRegion(p("/area/station/legal/magistrate"), SECURITY_COLOR, "Magi."),
    MapRegion(p("/area/station/security/armory/secure"), SECURITY_COLOR, "Armory"),
    MapRegion(p("/area/station/security/brig"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/checkpoint"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/checkpoint/secondary"), SECURITY_COLOR, "Chk."),
    MapRegion(p("/area/station/security/armory"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/detective"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/evidence"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/execution"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/interrogation"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/main"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/permabrig"), SECURITY_COLOR, "Permabrig"),
    MapRegion(p("/area/station/security/prison/cell_block"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/prison/cell_block/A"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/prisonlockers"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/processing"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/range"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/storage"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/warden"), SECURITY_COLOR, "Wrdn."),
    MapRegion(p("/area/station/security/permasolitary"), SECURITY_COLOR),
    MapRegion(p("/area/station/command/customs"), SECURITY_COLOR),
    MapRegion(p("/area/station/security/prisonershuttle"), SECURITY_COLOR),
    MapRegion(p("/area/station/legal/courtroom/gallery"), SECURITY_COLOR),
]

ARRIVALS_AREAS = [
    MapRegion(p("/area/shuttle/arrival/station"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/secondary/entry"), ARRIVALS_COLOR, "Arrivals"),
    MapRegion(p("/area/station/hallway/secondary/exit"), ARRIVALS_COLOR, "Escape"),
    MapRegion(p("/area/station/hallway/entry/south"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/entry/north"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/secondary/entry/north"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/secondary/entry/south"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/secondary/entry/lounge"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/secondary/entry/east"), ARRIVALS_COLOR),
    MapRegion(p("/area/station/hallway/secondary/entry/west"), ARRIVALS_COLOR),
]

MEDBAY_AREAS = [
    MapRegion(
        p("/area/station/maintenance/aft2"),
        MEDBAY_COLOR,
        map_color_overrides={
            "metastation": MAINTS_COLOR,
        },
    ),
    MapRegion(p("/area/station/medical/chemistry"), MEDBAY_COLOR, "Chem"),
    MapRegion(p("/area/station/medical/coldroom"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/cryo"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/medbay"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/medbay2"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/medbay3"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/morgue"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/paramedic"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/psych"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/reception"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/sleeper"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/storage"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/storage/secondary"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/surgery"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/surgery/observation"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/surgery/primary"), MEDBAY_COLOR, "OR1"),
    MapRegion(p("/area/station/medical/surgery/secondary"), MEDBAY_COLOR, "OR2"),
    MapRegion(p("/area/station/medical/cloning"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/virology"), MEDBAY_COLOR, "Virology"),
    MapRegion(p("/area/station/medical/virology/lab"), MEDBAY_COLOR, "Virology"),
    MapRegion(p("/area/station/command/office/cmo"), MEDBAY_COLOR, "CMO"),
    MapRegion(p("/area/station/medical/exam_room"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/break_room"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/patients_rooms"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/patients_rooms_secondary"), MEDBAY_COLOR),
    MapRegion(p("/area/station/medical/patients_rooms1"), MEDBAY_COLOR),
    MapRegion(p("/area/station/public/storage/emergency"), MEDBAY_COLOR),
]

SCIENCE_AREAS = [
    MapRegion(p("/area/station/science/lobby"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/hallway"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/rnd"), SCIENCE_COLOR, "R&D"),
    MapRegion(p("/area/station/science/robotics/chargebay"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/robotics"), SCIENCE_COLOR, "Robotics"),
    MapRegion(p("/area/station/command/office/rd"), SCIENCE_COLOR, "RD"),
    MapRegion(p("/area/station/science/genetics"), SCIENCE_COLOR, "Genetics"),
    MapRegion(p("/area/station/science/server"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/server/coldroom"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/misc_lab"), SCIENCE_COLOR, "Chem"),
    MapRegion(p("/area/station/science/explab/chamber"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/explab"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/storage"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/test_chamber"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/xenobiology"), SCIENCE_COLOR, "Xenobio"),
    MapRegion(p("/area/station/science/toxins/launch"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/toxins/test"), SCIENCE_COLOR, "Toxins\nTesting"),
    MapRegion(p("/area/station/science/toxins/mixing"), SCIENCE_COLOR, "Toxins"),
    MapRegion(p("/area/station/science/research"), SCIENCE_COLOR),
    MapRegion(p("/area/station/science/break_room"), SCIENCE_COLOR),
]

AI_SAT_AREAS = [
    MapRegion(p("/area/station/aisat"), AI_SAT_COLOR),
    MapRegion(p("/area/station/aisat/atmos"), AI_SAT_COLOR),
    MapRegion(p("/area/station/aisat/hall"), AI_SAT_COLOR, "AI Sat."),
    MapRegion(p("/area/station/aisat/service"), AI_SAT_COLOR),
    MapRegion(p("/area/station/telecomms/chamber"), AI_SAT_COLOR),
    MapRegion(p("/area/station/turret_protected/ai"), AI_SAT_COLOR),
    MapRegion(p("/area/station/turret_protected/aisat"), AI_SAT_COLOR),
    MapRegion(p("/area/station/turret_protected/aisat/interior"), AI_SAT_COLOR),
    MapRegion(p("/area/station/telecomms/computer"), AI_SAT_COLOR),
    MapRegion(p("/area/station/engineering/ai_transit_tube"), AI_SAT_COLOR),
    MapRegion(p("/area/station/aisat/breakroom"), AI_SAT_COLOR),
    MapRegion(
        p("/area/station/turret_protected/aisat/interior/secondary"), AI_SAT_COLOR
    ),
    
]

SERVICE_AREAS = [
    MapRegion(p("/area/station/service/expedition"), SERVICE_COLOR, "Expl."),
    MapRegion(p("/area/station/service/janitor"), SERVICE_COLOR, "Jani."),
    MapRegion(p("/area/station/service/bar"), SERVICE_COLOR, "Bar"),
    MapRegion(p("/area/station/service/kitchen"), SERVICE_COLOR, "Kitchen"),
    MapRegion(p("/area/station/service/clown"), SERVICE_COLOR),
    MapRegion(p("/area/station/service/mime"), SERVICE_COLOR),
    MapRegion(p("/area/station/service/library"), SERVICE_COLOR, "Library"),
    MapRegion(p("/area/station/service/chapel"), SERVICE_COLOR, "Chapel"),
    MapRegion(p("/area/station/service/chapel/funeral"), SERVICE_COLOR, "Chapel"),
    MapRegion(p("/area/station/service/chapel/office"), SERVICE_COLOR),
    MapRegion(p("/area/station/service/hydroponics"), BOTANY_COLOR, "Botany"),
    MapRegion(p("/area/station/public/pet_store"), SERVICE_COLOR),
    MapRegion(p("/area/station/public/storage/art"), SERVICE_COLOR),
    MapRegion(p("/area/station/service/theatre"), SERVICE_COLOR),
]

SOLARS_AREAS = [
    MapRegion(p("/area/station/maintenance/solar_maintenance"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/aft"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/aft_port"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/aft_starboard"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/fore"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/fore_port"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/fore_starboard"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/port"), SOLARS_COLOR),
    MapRegion(p("/area/station/maintenance/solar_maintenance/starboard"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/aft"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/aft_port"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/aft_starboard"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/fore"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/fore_port"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/fore_starboard"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/port"), SOLARS_COLOR),
    MapRegion(p("/area/station/engineering/solar/starboard"), SOLARS_COLOR),
    ]

ESCAPE_POD_AREAS = [
    MapRegion(p("/area/shuttle/pod_1"), ESCAPE_POD_COLOR),
    MapRegion(p("/area/shuttle/pod_2"), ESCAPE_POD_COLOR),
    MapRegion(p("/area/shuttle/pod_3"), ESCAPE_POD_COLOR),
    MapRegion(p("/area/shuttle/pod_4"), ESCAPE_POD_COLOR),
]


MISC_AREAS = [
    MapRegion(p("/area/space/nearstation/disposals"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/northwest"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/west"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/northeast"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/east"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/southeast"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/south"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/southwest"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/external/east"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/maintenance/disposal/external/north"), DISPOSALS_COLOR),
    MapRegion(
        p("/area/station/maintenance/disposal/external/southeast"), DISPOSALS_COLOR
    ),
    MapRegion(
        p("/area/station/maintenance/disposal/external/southwest"), DISPOSALS_COLOR
    ),
    MapRegion(p("/area/station/maintenance/disposal/westalt"), DISPOSALS_COLOR),
    MapRegion(p("/area/station/engineering/atmos/asteroid_core"), EMERALD_PLASMA_COLOR),
]

QUANTUMPAD_AREAS = [
    MapRegion(p("/area/station/public/quantum/cargo"), QUANTUMPAD_COLOR),
    MapRegion(p("/area/station/public/quantum/docking"), QUANTUMPAD_COLOR),
    MapRegion(p("/area/station/public/quantum/medbay"), QUANTUMPAD_COLOR),
    MapRegion(p("/area/station/public/quantum/science"), QUANTUMPAD_COLOR),
    MapRegion(p("/area/station/public/quantum/security"), QUANTUMPAD_COLOR),
    MapRegion(p("/area/station/public/quantum/service"), QUANTUMPAD_COLOR),
]

AREAS = (
    HALLWAY_AREAS
    + SUPPLY_AREAS
    + COMMAND_AREAS
    + ATMOS_AREAS
    + MAINTS_AREAS
    + ENGINEERING_AREAS
    + PUBLIC_AREAS
    + SECURITY_AREAS
    + ARRIVALS_AREAS
    + MEDBAY_AREAS
    + SCIENCE_AREAS
    + AI_SAT_AREAS
    + SERVICE_AREAS
    + SOLARS_AREAS
    + ESCAPE_POD_AREAS
    + MISC_AREAS
    + QUANTUMPAD_AREAS
    + ASTEROID_AREAS
)

ZOOM_LEVEL = 8


def render_map(dmm: DMM, output_path: Path, labels: str, dmm_filename: str):
    fnt = ImageFont.truetype("Minimal5x7.ttf", 16)
    image = Image.new(
        size=(int(dmm.extents[0] * ZOOM_LEVEL), int(dmm.extents[1] * ZOOM_LEVEL)),
        mode="RGBA",
    )
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
        # if len(polygons) > 1:
        polygons.pop()

        for polygon in polygons:
            first_coordinate = [int(x) for x in reversed(polygon[0][0])]
            # print(f"area={region.area} polygon={polygon} first_coordinate={first_coordinate}")
            tiledef = dmm.tiledef(*[int(x) for x in reversed(polygon[0][0])], 1)

            if 0 in first_coordinate:
                continue

            # If our first coordinate is space, this is an inner hole in a
            # polygon that's just space. We want to render them last because
            # transparent polygons will still replace filled polygons
            if tiledef.area_path().child_of("/area/space"):
                polygon_process_order.append(polygon)
            else:
                polygon_process_order.insert(0, polygon)

        for idx, polygon in enumerate(polygon_process_order):
            tupled_polygon = tuple(x for xs in polygon for x in xs)
            if tupled_polygon in dupe_polygons:
                continue
            dupe_polygons.add(tupled_polygon)
            color = region.color
            # if region.alt_colors and idx in region.alt_colors:
            #     color = region.alt_colors[idx]

            tiledef = dmm.tiledef(*[int(x) for x in reversed(polygon[0][0])], 1)
            if tiledef.area_path().child_of(
                "/area/space"
            ) and not tiledef.area_path().child_of("/area/space/nearstation/disposals"):
                color = "#00000000"
            elif tiledef.area_path() != region.area:
                # We can't just skip polygons whose first coordinates don't
                # contain the same area because we might be looking at the
                # outside of a polygon which has an inner hole that isn't the
                # same area, and this won't get matched here.
                #
                # In general these areas are hallways that form loops, which is
                # why hallways are drawn first.
                color = "#00000000"
            elif (
                region.map_color_overrides
                and dmm_filename.lower() in region.map_color_overrides
            ):
                color = region.map_color_overrides[dmm_filename.lower()]

            flipped = [
                (int(y * ZOOM_LEVEL), int((255 - x) * ZOOM_LEVEL))
                for (x, y) in polygon[0]
            ]
            draw.polygon(flipped, fill=color, outline="#00000000")

            print(f"polygon area={region.area} idx={idx} => {polygon} => {color}")

            msg = None

            # Put the text label on the first polygon, this may be wrong
            # at some point but then we can configure it
            if labels == "rooms" and region.text and idx == 0:
                msg = region.text
            elif labels == "polygons":
                path_leaf = str(region.area).split("/")[-1]
                msg = f"{path_leaf}{idx}"

            if not labels or not msg:
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
@click.option(
    "--labels", type=click.Choice(["rooms", "polygons", "none"]), default=None
)
def main(dmm_file, labels):
    dmm_path = Path(dmm_file)
    dmm = DMM.from_file(dmm_path)
    render_map(dmm, Path(f"./{dmm_path.stem}.png"), labels, dmm_path.stem)


if __name__ == "__main__":
    main()
