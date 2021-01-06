import enum
import re
import sys
from packaging.version import Version
from packaging.tags import Tag, sys_tags, parse_tag
from packaging.specifiers import SpecifierSet
from typing import Optional, Callable, Set, Tuple, List


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


class Candidate:
    name: str
    version: Version
    requires_python: SpecifierSet
    is_binary: bool
    tags: Set[Tag]


    def attributes_from_filename(self, filename: str) -> None:
        filename = filename.lower()

        if filename.endswith(".whl"):
            self.is_binary = True
            filename = filename[:-4]
            dashes = filename.count("-")
            assert dashes in (4, 5), f"{filename} is incorrect format"
            name, ver, *build, tag = filename.split("-", dashes-2)
            self.name = normalize(name)
            self.version = Version(ver)
            self.tags = parse_tag(tag)

        elif filename.endswith(".tar.gz"):
            self.is_binary = False
            # We are requiring a PEP 440 version, which cannot contain dashes,
            # so we split on the last dash.
            name, sep, version = filename[:-7].rpartition("-")
            self.name = normalize(name)
            self.version = Version(version)
            self.tags = set()


SortKey = Tuple[int, Version, int]


# Require binary (bool or set of names, default False)
# Disallow binary (bool or set of names, default False)
# Prefer binary (bool or set of names, default False)
# Compatibility tags (list, default is sys_tags())
# Python version (Version, default interpreter version)
# Allow prerelease


class BinaryPolicy(enum.Enum):
    ALLOW = enum.auto()  # Source or binary is OK (default)
    REQUIRE = enum.auto()  # Must be binary
    PROHIBIT = enum.auto()  # Must be source
    PREFER = enum.auto()  # May be either, but prefer binary


def match(tags: Set[Tag], sys_tags: List[Tag]) -> int:
    # Returns a compatibility value
    max_compat = len(sys_tags)
    for i, tag in enumerate(sys_tags):
        if tag in tags:
            return max_compat - i
    return 0


class Finder:
    compatibility_tags: List[Tag]
    allow_prerelease: bool
    python_version: Version
    binary_policy: Callable[[str], BinaryPolicy]


    def __init__(self,
        compatibility_tags: Optional[List[Tag]] = None,
        allow_prerelease: bool = False,
        python_version: Optional[Version] = None,
        binary_policy: Optional[Callable[[str], BinaryPolicy]] = None,
    ):
        # Default values
        if compatibility_tags is None:
            compatibility_tags = list(sys_tags())
        if python_version is None:
            python_version = Version("{0.major}.{0.minor}.{0.micro}".format(sys.version_info))
        if binary_policy is None:
            binary_policy = lambda name: BinaryPolicy.ALLOW

        self.compatibility_tags = compatibility_tags
        self.allow_prerelease = allow_prerelease
        self.python_version = python_version
        self.binary_policy = binary_policy


    def sort_key(self, candidate: Candidate) -> Optional[SortKey]:

        # Handle the simple cases first (prerelease and Python version)
        if candidate.version.is_prerelease:
            if not self.allow_prerelease:
                return None

        if self.python_version not in candidate.requires_python:
            return None

        # Binary handling. We need to know the policy.
        binary = self.binary_policy(candidate.name)
        binary_first = 0

        if candidate.is_binary:
            if binary == BinaryPolicy.PROHIBIT:
                return None
            elif binary == BinaryPolicy.PREFER:
                binary_first = 1

            compatibility_level = match(candidate.tags, self.compatibility_tags)
            if compatibility_level == 0:
                return None
        else:
            if binary == BinaryPolicy.REQUIRE:
                return None

            # Source distributions are considered
            # "less compatible" than binaries.
            compatibility_level = 0

        # We're a valid match. Sort key is:
        #
        #   - Binary first, if prefer_binary
        #   - Version
        #   - More compatible before less compatible

        return (binary_first, candidate.version, compatibility_level)


    def get_candidates(self, source):
        candidates = ((self.sort_key(c), c) for c in source)
        candidates = ((k, c) for (k, c) in candidates if k is not None)
        candidates = sorted(candidates, reverse=True)
        return (c for (k, c) in candidates)
