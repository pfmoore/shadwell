import enum
import sys
from packaging.version import Version
from packaging.tags import Tag, sys_tags
from packaging.requirements import Requirement
from typing import Optional, Callable, Set, Tuple, List

from .candidate import Candidate

SortKey = Tuple[int, Version, int]

class WheelPolicy(enum.Enum):
    ALLOW = enum.auto()  # Source or wheel is OK (default)
    REQUIRE = enum.auto()  # Must be wheel
    PROHIBIT = enum.auto()  # Must be source
    PREFER = enum.auto()  # May be either, but prefer wheel


def compatibility(tags: Set[Tag], sys_tags: List[Tag]) -> int:
    """Given a set of tags, say "how compatible" it is.

    A tag set is more compatible if it matches a tag earlier
    in the list of system tags.

    A return value of -1 means "not compatible".
    """
    # Returns a compatibility value
    max_compat = len(sys_tags)
    for i, tag in enumerate(sys_tags):
        if tag in tags:
            return max_compat - i
    return -1


class Finder:
    sources: List[Callable[[str], List[Candidate]]]
    compatibility_tags: List[Tag]
    allow_prerelease: bool
    python_version: Version
    wheel_policy: Callable[[str], WheelPolicy]
    allow_yanked: bool

    def __init__(self,
        sources: List[Callable[[str], List[Candidate]]],
        compatibility_tags: Optional[List[Tag]] = None,
        allow_prerelease: bool = False,
        python_version: Optional[Version] = None,
        wheel_policy: Optional[Callable[[str], WheelPolicy]] = None,
        allow_yanked: bool = False,
    ):
        # Default values
        if compatibility_tags is None:
            compatibility_tags = list(sys_tags())
        if python_version is None:
            python_version = Version("{0.major}.{0.minor}.{0.micro}".format(sys.version_info))
        if wheel_policy is None:
            wheel_policy = lambda name: WheelPolicy.ALLOW

        self.sources = sources
        self.compatibility_tags = compatibility_tags
        self.allow_prerelease = allow_prerelease
        self.python_version = python_version
        self.wheel_policy = wheel_policy
        self.allow_yanked = allow_yanked

    def _sort_key(self, candidate: Candidate) -> Optional[SortKey]:

        # Handle the simple cases first (prerelease and Python version)
        # TODO: Allow prereleases if they are the only option? See
        #       the rules in PEP 440.
        if candidate.version.is_prerelease:
            if not self.allow_prerelease:
                return None

        if self.python_version not in candidate.requires_python:
            return None

        # Wheel handling. We need to know the policy.
        wheel = self.wheel_policy(candidate.name)
        wheel_first = 0

        if candidate.is_wheel:
            if wheel == WheelPolicy.PROHIBIT:
                return None
            elif wheel == WheelPolicy.PREFER:
                wheel_first = 1

            compatibility_level = compatibility(candidate.tags, self.compatibility_tags)
            if compatibility_level == -1:
                return None
        else:
            if wheel == WheelPolicy.REQUIRE:
                return None

            # Source distributions are considered
            # "less compatible" than binaries.
            compatibility_level = 0

        # We're a valid match. Sort key is:
        #
        #   - Wheel first, if prefer_wheel
        #   - Version
        #   - More compatible before less compatible

        return (wheel_first, candidate.version, compatibility_level)

    def get_candidates(self, req: Requirement) -> List[Candidate]:
        """Return candidates matching the requirement.
        """
        candidates = []
        for source in self.sources:
            for candidate in source(req.name):
                if candidate.version not in req.specifier:
                    continue
                key = self._sort_key(candidate)
                if key is None:
                    continue
                candidates.append((key, candidate))
        candidates.sort(reverse=True)
        candidates = [c for (k, c) in candidates]

        # If we allow yanked candidates when they are the only option,
        # do so now.
        if self.allow_yanked and all(c.is_yanked for c in candidates):
            return candidates

        return [c for c in candidates if not c.is_yanked]
