import hypothesis.strategies as s
from hypothesis import given
from packaging.version import Version


def optional(strat):
    return s.one_of(s.none(), strat)
def nat():
    return s.integers(min_value=0)

def build_version(epoch, rel, pre, post, dev):
    ver = ".".join(str(r) for r in rel)
    if pre:
        ver += pre[0] + str(pre[1])
    if post:
        ver += ".post" + str(post)
    if dev:
        ver += ".dev" + str(dev)
    if epoch:
        ver = str(epoch) + "!" + ver
    return Version(ver)

ver_strat = s.builds(build_version,
    optional(nat()),
    s.lists(nat(), min_size=1, max_size=5),
    optional(s.tuples(s.sampled_from(("a", "b", "rc")), nat())),
    optional(nat()),
    optional(nat()),
)

@given(ver_strat)
def test_example(v):
    assert type(v) == Version
    assert v.is_prerelease
