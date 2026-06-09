"""Demo module for the new Python-type-syntax features in sphinx-autodoc-typehints.

This file is intentionally hand-written to exercise:

* The ``X | Y`` union rendering path (native ``types.UnionType`` on Py3.10+).
* Nested ``Annotated[T, Doc(...)]`` markers at any depth in the type tree.
* The ``:no-overloads:`` and new ``:no-rtype:`` per-function directives.
"""

from __future__ import annotations

from typing import Annotated, Union

from typing_extensions import Doc, overload


def count_items(items: list[Annotated[int, Doc("The item count")]] | None) -> int:
    """Return the number of items passed in, or 0 on ``None``.

    Demonstrates: ``X | Y`` rendering + nested ``Annotated`` extraction.
    """
    return len(items) if items is not None else 0


def fetch_url(url: Annotated[str, Doc("The absolute URL to fetch")]) -> Annotated[bytes, Doc("Raw response body")]:
    """Demonstrates Annotated[T, Doc(...)] on both parameter and return value.

    The ``:param url:`` and ``:return:`` lines will be auto-injected from the
    ``Doc(...)`` markers.
    """
    import urllib.request

    return urllib.request.urlopen(url).read()


def internal_helper(value: int) -> dict[str, int]:
    """A helper that should not emit a :rtype: line.

    :no-rtype:
    """
    return {"value": value}


@overload
def parse(raw: str) -> int: ...


@overload
def parse(raw: bytes) -> int: ...


def parse(raw: str | bytes) -> int:
    """Parse a numeric payload.

    :no-overloads:

    A docstring directive hides the ``:Overloads:`` section for this specific
    function, even though :confval:`typehints_document_overloads` is globally
    enabled.
    """
    if isinstance(raw, bytes):
        raw = raw.decode()
    return int(raw)


def classic_union(x: Union[int, str]) -> str:
    """On Python 3.14+ ``typing.Union`` itself renders as ``int | str``."""
    return str(x)
