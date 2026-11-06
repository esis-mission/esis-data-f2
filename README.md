# esis-data-f2
Data from the second flight of the EUV Snapshot Imaging Spectrograph (ESIS-II), starting with measurements of its optics.

## Measurements of the optics

The `metrology-v1.0` release will hold `esis-f2-metrology.tar`, measurements of the optics built for the second flight.
Each is the final product of a measurement, the file exactly as the software of the instrument saved it; none of the intermediate products it was made from are kept.
Later releases add measurements, and keep these byte for byte the same.

So far the archive holds the measurements Optimax Systems made in September 2026 of the two primary mirrors it polished, serial numbers SN2 and SN3.
Which of them will fly is not decided yet.
For each mirror, `primary/` holds:

- `<serial>_3219CC ASP_IRR_UC.dat`, the map of the figure of the mirror over its clear aperture, measured with a Nanomefos profilometer on a grid of 0.25 mm. It is the height of the surface relative to a paraboloid, with piston, tilt, and power removed.
- `<serial>_00a_MET01_NXV1_1.4X_1XZOOM.dat`, a field 6.07 mm across of the finish of the mirror, measured with a Zygo NexView white-light interferometer through its 1.4X objective on pixels 5.92 µm apart.
- `<serial>_00a_MET01_NXV1_20X_1XZOOM.dat`, a field 0.417 mm across, measured through its 20X Mirau objective on pixels 0.407 µm apart.

Each file is in the MetroPro `.dat` format of Zygo's software, with a header of 834 bytes.
The `manifest.csv` of each directory lists each file's optic, serial number, instrument, date, software version, wavelength, scale and obliquity factors, phase resolution, pixel size, and SHA-256 checksum.
The docstring of `columns` in `tools/build_metrology.py` says how they convert the integers of a map to the height of the surface in meters.

`tools/build_metrology.py` builds the archive from Optimax's data package. It finds each file by name, checks it against its checksum, and needs only the Python standard library:

    python tools/build_metrology.py <source> <directory>
