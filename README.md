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

## Measurements of multilayer coatings

The `multilayer-v1.0` release holds `esis-f2-multilayer.tar`, measurements of the reflectivity of multilayer coatings for the second flight.
Like the measurements of the optics, each is the file exactly as the software of the instrument saved it, and later releases add measurements and keep these byte for byte the same.

So far the archive holds one measurement, which Eric Gullikson of Lawrence Berkeley National Laboratory sent on November 5, 2026.
`multilayer/mul080572.abs` is the reflectivity of sample CX250916B, a test of the Si/Sc coating planned for the second flight.

- The sample has 10 periods of Si and Sc, with Sc 0.4 of each period, on a Si substrate. Its top layer is about 16 nm of Si, under about 1.5 nm of native SiO2.
- It was coated on September 16, 2025, the date in its name, and measured about two months later. It was measured only once, so how it ages is not known.
- It was measured on beamline 6.3.2 of the Advanced Light Source, 5° from the normal, with a beam 0.98 linearly polarized (s), from 25.1 to 50.0 nm.

The file is text.
Its first line is `#` and the name of the sample, and each line after it is a wavelength in nanometers and the reflectivity at it.
The first line ends with LF and the others with CRLF, as Eric's software wrote them.
`multilayer/manifest.csv` lists each file's sample, coating, number of periods, Sc fraction, top layer, substrate, date of coating, beamline, angle of incidence, degree of polarization, and SHA-256 checksum.

`tools/build_multilayer.py` builds the archive from the files as they were sent. It finds each file by name, checks it against its checksum, and needs only the Python standard library:

    python tools/build_multilayer.py <source> <directory>
