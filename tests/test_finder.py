from sys import version_info

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import Tag, sys_tags
from packaging.version import Version

from shadwell.finder import Candidate, Finder, WheelPolicy

FILES = [
    "proj-0.1.tar.gz",
    "proj-0.2.tar.gz",
    "proj-0.3.tar.gz",
    "proj-0.2-py3-none-any.whl",
    "proj-0.1-py2.py3-none-any.whl",
]


class MyCandidate(Candidate):
    def __init__(self, filename):
        self.filename = filename
        self.attributes_from_filename(filename)
        self.requires_python = SpecifierSet()
        self.is_yanked = False


def test_finder_ordering():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
        "proj-0.1-py2.py3-none-any.whl",
        "proj-0.1.tar.gz",
    ]


def test_finder_matches_tags():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py2", "none", "any")],
        python_version=Version("2.7"),
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2.tar.gz",
        "proj-0.1-py2.py3-none-any.whl",
        "proj-0.1.tar.gz",
    ]


def test_finder_respects_requires_python():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if "0.1" in filename:
                c.requires_python = SpecifierSet("<=3.7")
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
    ]


def test_finder_respects_yanked():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if "0.1" in filename:
                c.is_yanked = True
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
        allow_yanked=False,
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
    ]


def test_finder_defaults():
    f = Finder([])
    assert set(f.compatibility_tags) == set(sys_tags())
    assert f.python_version.major == version_info.major
    assert f.python_version.minor == version_info.minor
    assert f.python_version.micro == version_info.micro


def test_finder_prohibit_wheels():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
        wheel_policy=lambda name: WheelPolicy.PROHIBIT,
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2.tar.gz",
        "proj-0.1.tar.gz",
    ]


def test_finder_prefer_wheels():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
        wheel_policy=lambda name: WheelPolicy.PREFER,
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.2-py3-none-any.whl",
        "proj-0.1-py2.py3-none-any.whl",
        "proj-0.3.tar.gz",
        "proj-0.2.tar.gz",
        "proj-0.1.tar.gz",
    ]


def test_finder_require_wheels():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
        wheel_policy=lambda name: WheelPolicy.REQUIRE,
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.2-py3-none-any.whl",
        "proj-0.1-py2.py3-none-any.whl",
    ]


def test_finder_version_limit():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj>=0.2"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
    ]


def test_finder_all_yanked():
    def src(name):
        for filename in FILES:
            c = MyCandidate(filename)
            c.is_yanked = True
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
        allow_yanked=True,
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
        "proj-0.1-py2.py3-none-any.whl",
        "proj-0.1.tar.gz",
    ]


def test_finder_prereleases():
    def src(name):
        PRE_FILES = [
            "proj-0.1a1.tar.gz",
            "proj-0.1a1-py2.py3-none-any.whl",
        ]
        for filename in FILES + PRE_FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
        allow_prerelease=True,
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
        "proj-0.1-py2.py3-none-any.whl",
        "proj-0.1.tar.gz",
        "proj-0.1a1-py2.py3-none-any.whl",
        "proj-0.1a1.tar.gz",
    ]

    f2 = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
        allow_prerelease=False,
    )

    assert [c.filename for c in f2.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
        "proj-0.1-py2.py3-none-any.whl",
        "proj-0.1.tar.gz",
    ]


def test_finder_only_prereleases():
    def src(name):
        FILES = [
            "proj-0.1a1.tar.gz",
            "proj-0.1a1-py2.py3-none-any.whl",
        ]
        for filename in FILES:
            c = MyCandidate(filename)
            if c.name == name:
                yield c

    f = Finder(
        sources=[src],
        compatibility_tags=[Tag("py3", "none", "any")],
        python_version=Version("3.8"),
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.1a1-py2.py3-none-any.whl",
        "proj-0.1a1.tar.gz",
    ]
