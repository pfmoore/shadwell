# ==== Versions
# --pre
# constraints

# ==== Specific files
# hashes

# ==== Tag stuff
# --platform
# --python-version
# --implementation
# --abi

# ==== Wheels or sdists
# --no-binary (all, none, package...)
# --only-binary (all, none, package...)

# ==== Python version
# data-requires-python

# Normalized project names
# See https://www.python.org/dev/peps/pep-0503/#normalized-names

import re
import enum
from packaging.version import Version, parse
from packaging.tags import Tag, parse_tag

def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def split_prefix_norm(name, filename):
    # name must be normalised
    prefix_pat = name.replace("-", r"[-_.]+")
    m = re.match(prefix_pat, filename, re.I)
    if m is None:
        # filename is not a file for name
        return None
    assert filename[m.end()] == "-"
    return filename[m.end()+1:]


def parse_wheel(filename):
    assert filename.endswith(".whl")
    filename = filename[:-4]
    dashes = filename.count("-")
    assert dashes in (4, 5), f"{filename} is incorrect format"
    name, ver, *build, tag = filename.split("-", dashes-2)
    # Normalized names use "-", wheels use "_"
    assert name.lower() == normalize(name).replace("-","_"), f"{name} is not normalized"
    ver = parse(ver)
    assert type(ver) is Version, f"{ver} is not a valid version"
    if build:
        build = build[0]
        assert build[0].isdigit(), f"Build number {build} must start with a digit"
    else:
        build = None
    tag = parse_tag(tag)

    return name, ver, build, tag


def parse_sdist(filename, name=None):
    assert filename.endswith(".tar.gz")
    filename = filename[:-7]
    if name:
        rest = split_prefix_norm(name, filename)
        assert rest is not None, f"{filename} is not a sdist for {name}"
    else:
        # Don't allow dashes in the version. This is unreliable,
        # but the best we can do...
        name, sep, rest = filename.rpartition("-")
        name = normalize(name)
    ver = parse(rest)
    assert type(ver) is Version, f"{ver} is not a valid version"

    return name, ver


class Candidate:
    def __init__(self, name, filename):
        self.name = name
        self.filename = filename
        self.parse_filename(filename, name)


    def parse_filename(self, filename, name=None):
        if filename.endswith(".whl"):
            self.type = "wheel"
            self.is_binary = True
            self.name, self.version, self.build, self.tag = parse_wheel(filename)
        elif filename.endswith(".tar.gz"):
            self.type = "sdist"
            self.is_binary = False
            self.name, self.version = parse_sdist(filename, name)
        else:
            raise ValueError(f"Invalid file type: {filename}")


class Format(enum.Flag):
    BINARY = enum.auto()
    SOURCE = enum.auto()

class Finder:
    def __init__(
            self,
            allow_prereleases=False,
            allow_format=Format.BINARY|Format.SOURCE,
            constraints={},
            platform=None,
            python_version=None,
            implementation=None,
            abi=None,

        ):
        self.sources = []
        self.prefer_binary = False
        self.allow_prereleases = allow_prereleases
        # allow_format needs to be per-project
        self.allow_format = lambda name: allow_format
        self.constraints = constraints
        if python_version is None:
            self.python_version = "{0.major}.{0.minor}.{0.micro}".format(sys.version_info)
        else:
            self.python_version = python_version
        # TODO: Allow user-specified platform
        self.supported_tags = packaging.tags.sys_tags()

    def get_candidates(self, name):
        for source in self.sources:
            for cand in source.get(name):
                yield cand

    def matches(self, cand):
        if cand.version.is_prerelease and not self.allow_prerelease:
            return False
        if not (cand.format & self.allow_format(cand.name)):
            return False
        if not cand.version in self.constraints.get(cand.name, SpecifierSet()):
            return False

    def find(self, name):
        candidates = self.get_candidates(name)
