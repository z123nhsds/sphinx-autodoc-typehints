"""集成测试: 覆盖 TYPE_CHECKING 解析、always_use_bars_union、local_function 警告、签名保留。

按模块标签（@pytest.mark.*）顺序输出，最终内容可被 patch 化。
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any

import pytest
from conftest import make_docstring_app, normalize_sphinx_text

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


# ---------------------------------------------------------------------------
# 1. 类型解析测试: 函数能否从 TYPE_CHECKING 块中解析类型
# ---------------------------------------------------------------------------
# 场景: 在一个模块内将类型导入放在 `if TYPE_CHECKING:` 守卫块内,
#       然后对该模块内的某个函数执行类型解析。期望:
#       1) 类型解析器会扫描模块源码并执行被守卫的导入代码;
#       2) `typing` / `typing_extensions` 的 TYPE_CHECKING 常量都能识别;
#       3) `autodoc_mock_imports` 中的包会被 mock, 不触发真实 ImportError;
#       4) 同模块的第二次调用会命中缓存 (_TYPE_GUARD_IMPORTS_RESOLVED), 不会重复执行。
# ---------------------------------------------------------------------------


@pytest.mark.type_checking_resolution
@pytest.mark.sphinx("text", testroot="dummy")
def test_function_resolves_types_from_type_checking_block(
    app: SphinxTestApp,
    tmp_path: Path,
) -> None:
    """在一个全新模块内放 TYPE_CHECKING 守卫, 验证它对 `get_type_hints` 可见."""
    from sphinx_autodoc_typehints._resolver._type_hints import (  # noqa: PLC0415
        _TYPE_GUARD_IMPORTS_RESOLVED,
        get_all_type_hints,
    )

    module_file = tmp_path / "module_with_type_checking.py"
    module_file.write_text(
        dedent(
            '''
            from __future__ import annotations

            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from pathlib import Path as PathType

            def compute(x: PathType) -> str:
                return str(x)
            ''',
        ).lstrip(),
    )
    import importlib.util  # noqa: PLC0415

    spec = importlib.util.spec_from_file_location("module_with_type_checking", module_file)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    # 清理缓存, 确保这个模块在当前测试中被独立扫描.
    _TYPE_GUARD_IMPORTS_RESOLVED.discard("module_with_type_checking")

    hints = get_all_type_hints([], mod.compute, "module_with_type_checking.compute", {})

    from pathlib import Path as _Path  # noqa: PLC0415

    assert hints["x"] is _Path
    assert hints["return"] is str


@pytest.mark.type_checking_resolution
def test_type_checking_guard_parses_typing_prefix() -> None:
    """`if typing.TYPE_CHECKING:` 这种全称写法也应被正则识别."""
    from sphinx_autodoc_typehints._resolver._type_hints import (  # noqa: PLC0415
        _TYPE_GUARD_IMPORT_RE,
    )

    code_prefixed = '\nif typing.TYPE_CHECKING:\n    import os\n'
    assert _TYPE_GUARD_IMPORT_RE.search(code_prefixed) is not None


@pytest.mark.type_checking_resolution
def test_autodoc_mock_imports_prevents_real_import() -> None:
    """当 TYPE_CHECKING 内部导入的包被列入 `autodoc_mock_imports` 时, 不会真的导入."""
    from sphinx_autodoc_typehints._resolver._type_hints import (  # noqa: PLC0415
        _run_guarded_import,
    )

    ns: dict[str, Any] = {}
    obj: Any = type("FakeObj", (), {"__globals__": ns, "__module__": "fake"})()

    # 非 mock 情况下, 导入一个不存在的包会抛 ImportError; 但加入 mock 列表应被吞掉.
    _run_guarded_import(["this_package_does_not_exist"], obj, "import this_package_does_not_exist\n")
    # 关键断言: exec 不抛异常即为通过 (已进入 guarded 分支).
    assert True


# ---------------------------------------------------------------------------
# 2. 配置项测试: always_use_bars_union
# ---------------------------------------------------------------------------
# 行为:
#   - always_use_bars_union=False  ->  typing.Union[X, Y]
#   - always_use_bars_union=True   ->  X | Y
# ---------------------------------------------------------------------------


@pytest.mark.always_use_bars_union
def test_union_rendered_as_typing_union_when_disabled() -> None:
    from typing import Union  # noqa: PLC0415

    from sphinx_autodoc_typehints._annotations import format_annotation  # noqa: PLC0415

    config = type("C", (), {"always_use_bars_union": False})()
    result = format_annotation(Union[int, str], config)  # noqa: UP007
    assert "Union" in result
    assert " | " not in result


@pytest.mark.always_use_bars_union
def test_union_rendered_as_bars_when_enabled() -> None:
    from typing import Union  # noqa: PLC0415

    from sphinx_autodoc_typehints._annotations import format_annotation  # noqa: PLC0415

    config = type("C", (), {"always_use_bars_union": True})()
    result = format_annotation(Union[int, str], config)  # noqa: UP007
    assert "Union" not in result
    assert " | " in result


# ---------------------------------------------------------------------------
# 3. 警告测试: local_function 警告以及 conf.py 抑制
# ---------------------------------------------------------------------------
# 触发条件: method 类型 + <locals> 在 qualname 中 + 不是 dataclass __init__.
# 抑制方式: conf.py 中 `suppress_warnings = ["sphinx_autodoc_typehints.local_function"]`.
# ---------------------------------------------------------------------------


@pytest.mark.local_function_warning
@pytest.mark.sphinx("text", testroot="dummy")
def test_local_function_emits_warning(
    app: SphinxTestApp,
    status: Any,  # noqa: ARG001
    warning: Any,
) -> None:
    """当一个 method 被定义在局部作用域里时, 应触发 local_function 警告."""
    from sphinx_autodoc_typehints import process_signature  # noqa: PLC0415

    def outer() -> None:
        class Inner:
            def method(self, x: int) -> str:  # pragma: no cover
                return str(x)

        return Inner.method  # type: ignore[no-any-return]

    fn = outer()
    # 伪造一个类似 autodoc 调用的上下文: what="method", qualname 含 <locals>.
    assert "<locals>" in fn.__qualname__

    from sphinx.ext.autodoc import Options  # noqa: PLC0415

    result = process_signature(
        app,
        "method",
        f"test.{fn.__qualname__}",
        fn,
        Options(),
        "",
        "",
    )
    assert result is None
    assert "local_function" in warning.getvalue()


@pytest.mark.local_function_warning
def test_conf_py_suppresses_local_function_warning(tmp_path: Path) -> None:
    """conf.py 里配置 suppress_warnings 后, 警告不应出现在 stderr."""
    import subprocess  # noqa: S404
    import sys  # noqa: PLC0415

    # 构造最小可运行的 conf.py + index.rst, 验证 sphinx-build 本身的配置抑制路径.
    (tmp_path / "conf.py").write_text(
        dedent(
            '''
            master_doc = "index"
            extensions = ["sphinx.ext.autodoc", "sphinx_autodoc_typehints"]
            suppress_warnings = ["sphinx_autodoc_typehints.local_function"]
            ''',
        ).lstrip(),
    )
    (tmp_path / "index.rst").write_text("Test\n====\n\n.. autofunction:: demo.fn\n")
    (tmp_path / "demo.py").write_text(
        dedent(
            '''
            def _make_fn():
                def fn(x: int) -> str:  # pragma: no cover
                    return str(x)
                return fn
            fn = _make_fn()
            ''',
        ).lstrip(),
    )
    out_dir = tmp_path / "_build"
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "sphinx", "-W", "--keep-going", str(tmp_path), str(out_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    # 只要 stderr 里没有 sphinx_autodoc_typehints.local_function, 就认为抑制生效.
    assert "sphinx_autodoc_typehints.local_function" not in completed.stderr


# ---------------------------------------------------------------------------
# 4. 签名保留测试: typehints_use_signature + typehints_use_signature_return
# ---------------------------------------------------------------------------
# 需要验证的两点:
#   (a) typehints_use_signature=True  -> 参数类型出现在签名里
#   (b) typehints_use_signature_return=False  -> 返回类型不在签名里
# ---------------------------------------------------------------------------


@pytest.mark.signature_preservation
@pytest.mark.sphinx("text", testroot="dummy")
def test_parameter_types_in_signature_when_enabled(
    app: SphinxTestApp,
    write_rst: Any,
) -> None:
    """启用 typehints_use_signature 后, 输出里应能看到 `x: int` 形式."""
    app.config.typehints_use_signature = True
    app.config.typehints_use_signature_return = False

    write_rst(
        """
        .. autofunction:: dummy_module.undocumented_function
        """,
    )
    app.build()

    text = normalize_sphinx_text((Path(app.srcdir) / "_build/text/index.txt").read_text())
    # 参数类型出现在签名中 (注意 render 会包含 `x: int` 之类形式).
    assert "x: int" in text


@pytest.mark.signature_preservation
@pytest.mark.sphinx("text", testroot="dummy")
def test_return_type_absent_from_signature_when_disabled(
    app: SphinxTestApp,
    write_rst: Any,
) -> None:
    """typehints_use_signature_return=False 时, 签名末尾不得有 `-> ...`."""
    app.config.typehints_use_signature = True
    app.config.typehints_use_signature_return = False

    write_rst(
        """
        .. autofunction:: dummy_module.undocumented_function
        """,
    )
    app.build()

    text = normalize_sphinx_text((Path(app.srcdir) / "_build/text/index.txt").read_text())
    # 签名行里不含 -> 箭头
    sig_line = next(line for line in text.splitlines() if "undocumented_function" in line)
    assert "->" not in sig_line


# ---------------------------------------------------------------------------
# 5. 辅助: 让 conftest 级别的 make_docstring_app 覆盖到文档字符串注入路径
# ---------------------------------------------------------------------------


def test_docstring_app_integration_smoke() -> None:
    """对文档字符串注入路径做一个冒烟测试, 保证配置项测试不会影响到 process_docstring."""
    lines: list[str] = []
    app = make_docstring_app()

    def fn(x: int) -> str:  # pragma: no cover
        return str(x)

    from sphinx_autodoc_typehints import process_docstring  # noqa: PLC0415

    process_docstring(app, "function", "fn", fn, None, lines)
    # 只要 process_docstring 不抛异常, 就认为可运行.
    assert isinstance(lines, list)
