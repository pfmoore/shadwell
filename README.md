# Shadwell - A finder for Python packages

> "It wasn't a dark and stormy night.
>  It should have been, but that's the weather for you."

Shadwell lets you find Python packages, from a set of "sources" (typically
a package index or local directory).

## Finders
In order to use the library, you need to create a `Finder` object, and then
use that to fetch candidates for a requirement, as follows:

```python
sources = [
    # A list of package sources, we'll come back to this
]
finder = Finder(sources)
results = finder.find(requirement)
```

The results are returned in "best first" order, so callers which just want
the best match can take the first result returned and ignore the rest.

When creating a finder, you can supply any of the following arguments, to
configure its behaviour:

* `compatibility_tags`: This is a set of binary compatibility tags, used
  to determine if a wheel is compatible with the target platform. It should
  be a list of `packaging.tags.Tag` objects. Normally this will be omitted,
  in which case the default is to use `packaging.tags.sys_tags()`, which
  is the set supported by the current Python interpreter.
* `allow_prerelease`: If this is `True`, the finder will return pre-release
  versions. Otherwise it will ignore prereleases (this is the default
  behaviour).
* `python_version`: A `packaging.version.Version` object representing the
  target Python release. It is used to filter candidates based on their
  `Requires-Python` metadata. As usual, the current interpreter is used
  by default.
* `binary_policy`: This is a function that determines for a package, how
  we should choose between binary and source distributions. Called with a
  package name, it should return one of the `BinaryPolicy` values `ALLOW`
  (binaries can be used), `REQUIRE` (only binaries are allowed), `PROHIBIT`
  (binaries cannot be used, only sources are allowed) or `PREFER` (older
  binaries will be selected in preference to newer source-only versions).
* `allow_yanked`: This option only affects the case where all of the
  selected candidates are yanked. If there are any unyanked candidates,
  yanked candidates will be omitted regardless of the value of this option.
  If only yanked candidates are available, this option determines whether
  to return them rather than returning an empty list (the default).
  The intention here is to allow callers flexibility in how they implement
  the rules in [PEP 592](https://www.python.org/dev/peps/pep-0592/#installers).

## Candidates
The objects returned from the finder are `Candidate` objects. The exact class
is up to the source, but they must have the following attributes:

* `name`: The project name (a string).
* `version`: The project version (`packaging.version.Version`)
* `requires_python`: The Python versions this candidate works with
  (`packaging.specifiers.SpecifierSet`)
* `is_binary`: Is this a binary (wheel) or source (sdist).
* `tags`: The compatibility tags for this (binary) distribution.
  (`Set[packaging.tags.Tag]`)

## Sources
A `source` is any Python object - the only requirement is that it has a
`get(name)` method, which yields candidate objects for the named project.
Note in particular that it is *not* the responsibility of the source to
do any sort of filtering.

**TODO: Maybe just make each source a callable?**
