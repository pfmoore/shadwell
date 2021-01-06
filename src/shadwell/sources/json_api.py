from urllib.request import urlopen
import json
from packaging.specifiers import SpecifierSet
from ..finder import Candidate

PYPI_TEMPLATE = "https://pypi.org/pypi/{pkg}/json"

class JsonSource:
    def __init__(self, template=PYPI_TEMPLATE):
        self.template = template
    def __call__(self, name):
        with urlopen(self.template.format(pkg=name)) as f:
            data = json.load(f)
        for release in data["releases"]:
            for url in data["releases"][release]:
                if url["yanked"]:
                    # TODO: Implement complex client logic
                    # to allow using yanked releases for exact matches
                    continue
                candidate = Candidate()
                candidate.attributes_from_filename(url["filename"])
                if candidate.name != name:
                    # Handles both "not a wheel or sdist" (name is not set)
                    # or mismatches from bad data
                    continue
                candidate.url = url["url"]
                spec = url["requires_python"]
                if spec:
                    candidate.requires_python = SpecifierSet(spec)
                else:
                    candidate.requires_python = SpecifierSet()
                yield candidate