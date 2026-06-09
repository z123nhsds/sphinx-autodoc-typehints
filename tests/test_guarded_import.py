from __future__ import annotations

import sys
import types
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from io import StringIO

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx("text", testroot="integration")
def test_guarded_import_missing_name_no_warning(
    app: SphinxTestApp,
    status: StringIO,
    warning: StringIO,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_mod = types.ModuleType("target_mod")
    target_mod.__file__ = "/fake/target_mod.py"

    source = dedent("""\
    from __future__ import annotations
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from target_mod import nonexistent_name

    def func(x: int) -> int:
        '''Do something.

        Args:
            x: a number
        '''
        return x
    """)
    user_mod = types.ModuleType("user_mod")
    user_mod.__file__ = "/fake/user_mod.py"
    exec(compile(source, "/fake/user_mod.py", "exec"), user_mod.__dict__)  # noqa: S102

    monkeypatch.setitem(sys.modules, "target_mod", target_mod)
    monkeypatch.setitem(sys.modules, "user_mod", user_mod)

    (Path(app.srcdir) / "index.rst").write_text(
        dedent("""\
        Test
        ====

        .. autofunction:: user_mod.func
    """)
    )
    app.build()
    assert "build succeeded" in status.getvalue()
    assert "Failed guarded type import" not in warning.getvalue()


@pytest.mark.sphinx("text", testroot="integration")
def test_type_checking_block_parses_types(
    app: SphinxTestApp,
    status: StringIO,
    warning: StringIO,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """【类型解析测试】验证TYPE_CHECKING块中的类型能被正确解析。

    模拟场景：
    - help_module 模块中通过 `if TYPE_CHECKING:` 保护块导入 `SomeType`
    - `process` 函数的参数类型 `x: SomeType` 和返回值 `-> SomeType`
      引用了仅在 TYPE_CHECKING 块中导入的类型
    - 验证sphinx-autodoc-typehints能够在文档构建时正确解析这些类型

    预期导入行为：
    - 运行时 TYPE_CHECKING 为 False，help_module的 `if TYPE_CHECKING:` 块不执行
    - 但由于有 `from __future__ import annotations`，注解以字符串形式存储
    - sphinx-autodoc-typehints 应当能通过AST分析或get_type_hints机制解析出实际类型
    - 构建应成功，不应产生 "Cannot resolve forward reference" 等警告
    """

    helper_mod = types.ModuleType("helper_mod")
    helper_mod.__file__ = "/fake/helper_mod.py"

    helper_source = dedent("""\
    from __future__ import annotations

    class SomeType:
        '''Helper type used in TYPE_CHECKING guard.'''
    """)
    exec(compile(helper_source, "/fake/helper_mod.py", "exec"), helper_mod.__dict__)  # noqa: S102

    main_source = dedent("""\
    from __future__ import annotations
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from helper_mod import SomeType

    def process(x: SomeType) -> SomeType:
        '''Process a value.

        Args:
            x: the value to process
        '''
        return x
    """)
    main_mod = types.ModuleType("main_mod")
    main_mod.__file__ = "/fake/main_mod.py"
    exec(compile(main_source, "/fake/main_mod.py", "exec"), main_mod.__dict__)  # noqa: S102

    monkeypatch.setitem(sys.modules, "helper_mod", helper_mod)
    monkeypatch.setitem(sys.modules, "main_mod", main_mod)

    (Path(app.srcdir) / "index.rst").write_text(
        dedent("""\
        Test
        ====

        .. autofunction:: main_mod.process
    """)
    )
    app.build()
    assert "build succeeded" in status.getvalue()
    assert "Cannot resolve forward reference" not in warning.getvalue()

    result = (Path(app.srcdir) / "_build/text/index.txt").read_text()
    assert "SomeType" in result
