# ss13_wiki_tools

This repository contains various scripts for working with documentation for SS13 servers.

## `wiki_department_areamap.py`

The areamap script generates an images that uses simple colors and labels to highlight the departments of a station map. It takes two argument:

- `--dmm_file`, pointing to the map file in question, is required.
- `--labels [rooms|polygons]`, to generate text either containing the specified room names or the polgyon IDs for debugging.

This script uses the "[Minimal5x7](https://opengameart.org/content/minimalist-pixel-fonts)" font, created by kheftel and placed in the public domain.