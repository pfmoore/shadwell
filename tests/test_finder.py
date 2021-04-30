from shadwell.finder import Finder, Candidate
from packaging.specifiers import SpecifierSet
from packaging.tags import Tag
from packaging.version import Version
from packaging.requirements import Requirement

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
        sources = [src],
        compatibility_tags = [Tag("py3", "none", "any")],
        python_version = Version("3.8"),
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
        sources = [src],
        compatibility_tags = [Tag("py2", "none", "any")],
        python_version = Version("2.7"),
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
            if '0.1' in filename:
                c.requires_python = SpecifierSet("<=3.7")
            if c.name == name:
                yield c

    f = Finder(
        sources = [src],
        compatibility_tags = [Tag("py3", "none", "any")],
        python_version = Version("3.8"),
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
            if '0.1' in filename:
                c.is_yanked = True
            if c.name == name:
                yield c

    f = Finder(
        sources = [src],
        compatibility_tags = [Tag("py3", "none", "any")],
        python_version = Version("3.8"),
        allow_yanked=False,
    )

    assert [c.filename for c in f.get_candidates(Requirement("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
    ]