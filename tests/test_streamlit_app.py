from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "04_app"
HOME_APP = APP_ROOT / "home.py"
PAGES_DIR = APP_ROOT / "pages"


if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


def run_app(script_path: Path) -> AppTest:
    app = AppTest.from_file(script_path, default_timeout=30)
    app.run()
    return app


def run_page(page_path: Path) -> AppTest:
    app = AppTest.from_file(HOME_APP, default_timeout=30)
    app.switch_page(f"pages/{page_path.name}")
    app.run()
    return app


def assert_no_streamlit_exceptions(app: AppTest, script_path: Path) -> None:
    assert len(app.exception) == 0, f"{script_path.name} raised Streamlit exceptions"


def test_home_page_renders_without_uncaught_exceptions() -> None:
    app = run_app(HOME_APP)
    assert_no_streamlit_exceptions(app, HOME_APP)
    assert len(app.title) + len(app.header) + len(app.subheader) + len(app.markdown) > 0


def test_all_page_scripts_render_without_uncaught_exceptions() -> None:
    page_scripts = sorted(PAGES_DIR.glob("*.py"))
    assert page_scripts, "Expected Streamlit page scripts under 04_app/pages"

    failures: list[str] = []
    for script_path in page_scripts:
        app = run_page(script_path)
        if len(app.exception) != 0:
            failures.append(script_path.name)

    assert not failures, f"Streamlit page smoke test failures: {', '.join(failures)}"