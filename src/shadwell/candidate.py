import re
from packaging.version import Version
from packaging.tags import Tag, parse_tag
from packaging.specifiers import SpecifierSet
from typing import Set


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


class Candidate:
    name: str
    version: Version
    requires_python: SpecifierSet
    is_wheel: bool
    tags: Set[Tag]
    is_yanked: bool


    def attributes_from_filename(self, filename: str) -> None:
        filename = filename.lower()

        if filename.endswith(".whl"):
            self.is_wheel = True
            filename = filename[:-4]
            dashes = filename.count("-")
            assert dashes in (4, 5), f"{filename} is incorrect format"
            name, ver, *build, tag = filename.split("-", dashes-2)
            self.name = normalize(name)
            self.version = Version(ver)
            self.tags = parse_tag(tag)

        elif filename.endswith(".tar.gz"):
            self.is_wheel = False
            # We are requiring a PEP 440 version, which cannot contain dashes,
            # so we split on the last dash.
            name, sep, version = filename[:-7].rpartition("-")
            self.name = normalize(name)
            self.version = Version(version)
            self.tags = set()
