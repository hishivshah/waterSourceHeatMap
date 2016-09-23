# High Level Water Source Heat Map

Water source heat pumps have the potential to provide low carbon and renewable energy to buildings located near rivers. An assessment of the suitability of major Welsh rivers for water source heat pump deployment has been carried out, and the results summarised on a national scale map.

## Folder structure

Python scripts were used to process and analyse the data. These can be found within the code directory.

The data directory represents the latest version of the source data. Datasets from external sources are not included here but can be obtained following the instructions in the readme file.

## Setup
Setup for Windows 7 64-bit:

- Install Python 2.7 64-bit (tested on 2.7.12), from https://www.python.org/downloads/
- Install GDAL (tested on version 2.1.0) via the [OSgeo4W installer (64-bit)](https://trac.osgeo.org/osgeo4w/)
- Download [mod_spatialite 4.2.0](http://www.gaia-gis.it/gaia-sins/windows-bin-amd64-prev/mod_spatialite-4.2.0-win-amd64.7z), extract, and add extracted folder to Windows PATH environment variable
- Download GDAL-2.0.3-cp27-cp27m-win_amd64.whl from http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
- Download Shapely-1.5.17-cp27-cp27m-win_amd64.whl from http://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
- Install Python modules via pip:
```
pip install GDAL-2.0.3-cp27-cp27m-win_amd64.whl
pip install Shapely-1.5.17-cp27-cp27m-win_amd64.whl
pip install networkx
```

## License

All content licensed under the MIT License, see LICENSE file for full details.
