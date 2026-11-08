"""
Build the archive of the measurements of multilayer coatings for the second flight.

The archive holds the final product of each measurement, the file exactly as
the software of the instrument wrote it, beside a manifest which records what
is known of each sample and the SHA-256 checksum of its file. None of the
intermediate products the final ones were made from are kept.

So far that is one measurement, of the reflectivity of a test sample of Si/Sc,
the coating chosen for the second flight. Eric Gullikson of Lawrence Berkeley
National Laboratory measured it on beamline 6.3.2 of the Advanced Light Source
and sent it on November 5, 2026.

Run it as ``python tools/build_multilayer.py <source> <directory>``. It finds
each file listed in :data:`files` under ``<source>`` by its name, checks it
against its checksum, copies it into ``<directory>``, and writes
``<directory>/esis-f2-multilayer.tar``, whose contents and bytes depend only on
the files. It needs only the Python standard library.
"""

import csv
import dataclasses
import pathlib
import shutil
import sys
import tarfile

from build_metrology import normalize, sha256


@dataclasses.dataclass(frozen=True)
class Measurement:
    """A file in the archive, and the sample it measures."""

    directory: str
    """The directory of the archive which holds the file."""

    name: str
    """The name of the file, as the software of the instrument saved it."""

    sample: str
    """The name of the sample, which heads the file."""

    coating: str
    """The materials of the multilayer, top first."""

    num_periods: int
    """The number of periods of the multilayer."""

    ratio: float
    """The thickness of the Sc layer of a period divided by the period."""

    top: str
    """The material of the top layer."""

    substrate: str
    """The material of the substrate."""

    coated: str
    """When the sample was coated, from its name."""

    beamline: str
    """The beamline the sample was measured on."""

    angle: float
    """The angle of incidence, in degrees from the normal."""

    polarization: float
    """The degree of linear polarization of the beam, which is s-polarized."""

    sha256: str
    """The SHA-256 checksum of the file."""


files = (
    Measurement(
        directory="multilayer",
        name="mul080572.abs",
        sample="CX250916B",
        coating="Si/Sc",
        num_periods=10,
        ratio=0.4,
        top="Si",
        substrate="Si",
        coated="2025-09-16",
        beamline="ALS 6.3.2",
        angle=5,
        polarization=0.98,
        sha256="a0f18bd667ebae51d75084b4f205c2b02c2869dc95d7380201f5ce37fd21ffaa",
    ),
)
"""The files in the archive."""

name_archive = "esis-f2-multilayer.tar"
"""The name of the archive."""

name_manifest = "manifest.csv"
"""The name of the manifest in each directory of the archive."""

columns = (
    "file",
    "sample",
    "coating",
    "num_periods",
    "ratio",
    "top",
    "substrate",
    "coated",
    "beamline",
    "angle",
    "polarization",
    "sha256",
)
"""
The columns of each manifest, the fields of :class:`Measurement`.

Each file is text. Its first line is ``#`` and the name of the sample, and each
line after it is a wavelength in nanometers and the reflectivity of the sample
at that wavelength.
"""


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
            if path.read_bytes().split(b"\n", 1)[0].strip() != f"# {measurement.sample}".encode():
                raise ValueError(f"{path} is not headed by the name of {measurement.sample}")

        with open(path_directory / name_manifest, "w", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(columns)
            for measurement in measurements:
                row = dataclasses.asdict(measurement)
                row["file"] = row.pop("name")
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
