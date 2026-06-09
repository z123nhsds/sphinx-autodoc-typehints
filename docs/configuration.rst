sphinx-autodoc-typehints Configuration
========================================

This extension adds configuration options that you can set in your Sphinx
``conf.py`` to fine-tune how types are rendered in the generated documentation.

Return type display
--------------------

``typehints_document_rtype`` (default: ``True``)
    When set to ``False``, no ``:rtype:`` block is generated for any function,
    regardless of the return type.

``typehints_document_rtype_none`` (default: ``True``)
    Controls whether ``:rtype:`` content is shown when a function returns
    ``None``. Setting it to ``False`` hides the rendered type inside the
    block, but the block itself is still created (so a pre-existing
    ``:return:`` description is not affected).

``typehints_strip_none_return`` (default: ``False``)
    When set to ``True``, functions annotated with ``-> None`` (or whose
    return type is ``NoneType``) get **no** ``:rtype:`` block at all. The
    entire rtype section is skipped, so no type information appears and no
    empty block is produced. This is a stricter variant of
    ``typehints_document_rtype_none``: that option hides the type content
    while this one removes the block entirely.

``typehints_use_rtype`` (default: ``True``)
    When set to ``False``, the return type is appended inline to the
    ``:return:`` text instead of appearing as a separate ``:rtype:`` block.

Union formatting
----------------

``always_use_bars_union`` (default: ``False``)
    Render unions using the ``X | Y`` pipe syntax. Always used on Python
    3.14+.

``simplify_optional_unions`` (default: ``True``)
    Simplify ``Optional[Union[A, B]]`` to ``Union[A, B, None]``. When set
    to ``False``, any union containing ``None`` is shown as ``Optional``.

Default values and signatures
-----------------------------

``typehints_defaults`` (default: ``None``)
    Controls how parameter defaults are shown next to types. One of
    ``"comma"``, ``"braces"``, ``"braces-after"``, or ``None`` to disable.

``typehints_use_signature`` (default: ``False``)
    Keep parameter types visible inside the function signature.

``typehints_use_signature_return`` (default: ``False``)
    Keep the return type visible inside the function signature.

``typehints_fully_qualified`` (default: ``False``)
    Render type names with their full module path (e.g.
    ``collections.OrderedDict`` instead of ``OrderedDict``).

``always_document_param_types`` (default: ``False``)
    Insert types for parameters that don't have a ``:param:`` entry in the
    docstring.

Custom rendering
----------------

``typehints_formatter`` (default: ``None``)
    A callable ``(annotation, Config) -> str | None`` that takes over
    rendering of specific types. Returning ``None`` falls back to the
    default renderer.

``typehints_fixup_module_name`` (default: ``None``)
    A callable ``(str) -> str`` that rewrites module paths before any
    cross-reference links are generated.

Overloads
---------

``typehints_document_overloads`` (default: ``True``)
    Show ``@overload`` signatures in docs. Use the ``:no-overloads:``
    directive inside an individual docstring to disable rendering for one
    specific function.
