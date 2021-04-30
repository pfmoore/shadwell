import re
from typing import Set

from packaging.specifiers import SpecifierSet
from packaging.tags import Tag
from packaging.utils import parse_sdist_filename, parse_wheel_filename
from packaging.version import Version


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
            self.name, self.version, _, self.tags = parse_wheel_filename(filename)

        elif filename.endswith(".tar.gz"):
            self.is_wheel = False
            # We are requiring a PEP 440 version, which cannot contain dashes,
            # so we split on the last dash.
            self.name, self.version = parse_sdist_filename(filename)
            self.tags = set()
