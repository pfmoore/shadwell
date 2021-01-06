from shadwell.finder import Finder, Candidate
from packaging.specifiers import SpecifierSet
from packaging.tags import Tag
from packaging.version import Version

FILES = [
    "proj-0.1.tar.gz",
    "proj-0.2.tar.gz",
    "proj-0.3.tar.gz",
    "proj-0.2-py3-none-any.whl",
    "proj-0.1-py2.py3-none-any.whl",
]

class C(Candidate):
    def __init__(self, filename):
        self.filename = filename
        self.attributes_from_filename(filename)
        self.requires_python = SpecifierSet()


def source(name):
    for filename in FILES:
        c = C(filename)
        if c.name == name:
            yield c


def test_finder():
    f = Finder(
        compatibility_tags = [Tag("py3", "none", "any")],
        python_version = Version("3.8")
    )

    assert [c.filename for c in f.get_candidates(source("proj"))] == [
        "proj-0.3.tar.gz",
        "proj-0.2-py3-none-any.whl",
        "proj-0.2.tar.gz",
        "proj-0.1-py2.py3-none-any.whl",
        "proj-0.1.tar.gz",
    ]