"""
Build the archive of the measurements of the optics built for the second flight.

The archive holds the final product of each measurement, the file exactly as
the software of the instrument wrote it, beside a manifest which records the
metadata of each file and its SHA-256 checksum. None of the intermediate
products the final ones were made from are kept.

So far those are the measurements Optimax Systems made of the two primary
mirrors it polished, SN2 and SN3:

- a map of the figure of each mirror, measured with a Nanomefos profilometer;
- two fields of the finish of each mirror, measured with a Zygo NexView
  white-light interferometer through its 1.4X and 20X objectives.

Each is a file in Zygo's MetroPro ``.dat`` format.

Run it as ``python tools/build_metrology.py <source> <directory>``. It finds
each file listed in :data:`files` under ``<source>`` by its name, checks it
against its checksum, copies it into ``<directory>``, and writes
``<directory>/esis-f2-metrology.tar``, whose contents and bytes depend only on
the files. It needs only the Python standard library.
"""

import csv
import dataclasses
import datetime
import hashlib
import pathlib
import shutil
import struct
import sys
import tarfile


@dataclasses.dataclass(frozen=True)
class Measurement:
    """A file in the archive, and the optic it measures."""

    directory: str
    """The directory of the archive which holds the file."""

    name: str
    """The name of the file, as the software of the instrument saved it."""

    optic: str
    """The optic which was measured."""

    serial: str
    """The serial number of the optic."""

    instrument: str
    """The instrument which measured the optic."""

    sha256: str
    """The SHA-256 checksum of the file."""


files = (
    Measurement(
        directory="primary",
        name="SN2_3219CC ASP_IRR_UC.dat",
        optic="primary mirror",
        serial="SN2",
        instrument="Nanomefos",
        sha256="d5078cff32f07e64add326983af7696ea863203c044be4e8835555ca056a51b6",
    ),
    Measurement(
        directory="primary",
        name="SN2_00a_MET01_NXV1_1.4X_1XZOOM.dat",
        optic="primary mirror",
        serial="SN2",
        instrument="NexView 1.4X",
        sha256="c7256653257142530a997ce284e213f0cfe065da1d3752912ee3cfb19782dd0b",
    ),
    Measurement(
        directory="primary",
        name="SN2_00a_MET01_NXV1_20X_1XZOOM.dat",
        optic="primary mirror",
        serial="SN2",
        instrument="NexView 20X",
        sha256="0b4c6c5b581879d5e0704097544bc86b0f430abcf19e11bc145c335b270b4cd6",
    ),
    Measurement(
        directory="primary",
        name="SN3_3219CC ASP_IRR_UC.dat",
        optic="primary mirror",
        serial="SN3",
        instrument="Nanomefos",
        sha256="ea9c99c8fdd75e9043963abcfe95d914bfa319daacbe93e0efedc046996a499a",
    ),
    Measurement(
        directory="primary",
        name="SN3_00a_MET01_NXV1_1.4X_1XZOOM.dat",
        optic="primary mirror",
        serial="SN3",
        instrument="NexView 1.4X",
        sha256="8c5b1a5ee4838684411f1babdaf95312d9c916f66c00dc625ea2c35212e89b6c",
    ),
    Measurement(
        directory="primary",
        name="SN3_00a_MET01_NXV1_20X_1XZOOM.dat",
        optic="primary mirror",
        serial="SN3",
        instrument="NexView 20X",
        sha256="a901018d4f3660c0b20874b77bcfe25f69c52cb3d8bba8ecc14a81880e4c7cdf",
    ),
)
"""The files in the archive."""

name_archive = "esis-f2-metrology.tar"
"""The name of the archive."""

name_manifest = "manifest.csv"
"""The name of the manifest in each directory of the archive."""

columns = (
    "file",
    "optic",
    "serial",
    "instrument",
    "date",
    "software_version",
    "wavelength",
    "scale_factor",
    "obliquity_factor",
    "phase_res",
    "lateral_res",
    "sha256",
)
"""
The columns of each manifest.

The date is the time stamp in the header of the file, in UTC. The map in the
file is an array of big-endian 32-bit integers, whose shape the header gives,
after the intensity if the header gives it any bytes. Each integer times ``scale_factor``,
``obliquity_factor``, and ``wavelength``, divided by 4096, 32768, or 131072
for a ``phase_res`` of 0, 1, or 2, is the height of the surface in meters.
Integers of 2147483640 or more mark pixels without data. The pixels are
``lateral_res`` meters apart on the surface.
"""

size_header = 834
"""The size in bytes of a MetroPro header of format 1."""

magic = 0x881B036F
"""The number which begins a MetroPro header of format 1."""


def sha256(path: pathlib.Path) -> str:
    """The SHA-256 checksum of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def float32(value: float) -> str:
    """The shortest text which reads back as the same 32-bit floating-point number."""
    packed = struct.pack(">f", value)
    for digits in range(1, 9):
        text = f"{value:.{digits}g}"
        if struct.pack(">f", float(text)) == packed:
            return text
    return f"{value:.9g}"


def metadata(path: pathlib.Path) -> dict[str, str]:
    """The metadata in the header of a MetroPro file, for its manifest."""
    with open(path, "rb") as f:
        header = f.read(size_header)
    if struct.unpack(">IhI", header[:10]) != (magic, 1, size_header):
        raise ValueError(f"{path} does not begin with a MetroPro header of format 1")
    version = struct.unpack(">hhh", header[42:48])
    (time_stamp,) = struct.unpack(">i", header[76:80])
    (
        scale_factor,
        wavelength,
        _,
        obliquity_factor,
        _,
        lateral_res,
    ) = struct.unpack(">ffffff", header[164:188])
    (phase_res,) = struct.unpack(">h", header[218:220])
    date = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    return {
        "date": date.isoformat(),
        "software_version": ".".join(str(v) for v in version),
        "wavelength": float32(wavelength),
        "scale_factor": float32(scale_factor),
        "obliquity_factor": float32(obliquity_factor),
        "phase_res": str(phase_res),
        "lateral_res": float32(lateral_res),
    }


def find(source: pathlib.Path, measurement: Measurement) -> pathlib.Path:
    """The one file under `source` with the name of `measurement`, checked against its checksum."""
    paths = sorted(source.rglob(measurement.name))
    if len(paths) != 1:
        raise FileNotFoundError(
            f"expected one {measurement.name} under {source}, found {len(paths)}"
        )
    path = paths[0]
    if sha256(path) != measurement.sha256:
        raise ValueError(f"{path} does not match its checksum")
    return path


def normalize(info: tarfile.TarInfo) -> tarfile.TarInfo:
    """Drop the owner and the time of each file so the archive is reproducible."""
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    info.mode = 0o644
    return info


def build(source: pathlib.Path, directory: pathlib.Path) -> pathlib.Path:
    """Copy the files from `source` into `directory` and pack them into an archive there."""
    directories = sorted({m.directory for m in files})

    for name in directories:
        path_directory = directory / name
        path_directory.mkdir(parents=True, exist_ok=True)
        measurements = [m for m in files if m.directory == name]
        for measurement in measurements:
            path = path_directory / measurement.name
            shutil.copyfile(find(source, measurement), path)
            if sha256(path) != measurement.sha256:
                raise ValueError(f"{path} does not match its checksum")

        with open(path_directory / name_manifest, "w", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(columns)
            for measurement in measurements:
                path = path_directory / measurement.name
                row = dict(
                    file=measurement.name,
                    optic=measurement.optic,
                    serial=measurement.serial,
                    instrument=measurement.instrument,
                    sha256=measurement.sha256,
                    **metadata(path),
                )
                writer.writerow(tuple(row[c] for c in columns))

    path_archive = directory / name_archive
    with tarfile.open(path_archive, "w", format=tarfile.USTAR_FORMAT) as tar:
        for name in directories:
            path_directory = directory / name
            tar.add(
                path_directory / name_manifest,
                arcname=f"{name}/{name_manifest}",
                filter=normalize,
            )
            for measurement in files:
                if measurement.directory == name:
                    tar.add(
                        path_directory / measurement.name,
                        arcname=f"{name}/{measurement.name}",
                        filter=normalize,
                    )

    return path_archive


if __name__ == "__main__":
    path = build(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
    print(f"{path}\n    sha256  {sha256(path)}")
