"""The page, stylesheet and script, checked as served files (BR3.1 to BR3.3, BR4.1 to BR4.13).

Written before the page files exist (Red). These are text and structure checks: the script is
never executed by a test (no browser here). The keyboard and phone pass is by hand, from
`docs/manual-checks.md`.
"""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fixtures.sample_data import artist_mbid

from listenbrainz_recs.app.main import create_app

STATIC = Path(__file__).parents[2] / "src" / "listenbrainz_recs" / "app" / "static"
LINK_PREFIXES = (
    "https://musicbrainz.org/artist/",
    "https://www.youtube.com/results?search_query=",
    "https://open.spotify.com/search/",
)
FORBIDDEN_CALLS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(")


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> TestClient:
    from fixtures.web_models import build_web_models, search_artists

    models = tmp_path_factory.mktemp("page_models")
    build_web_models(models, search_artists())
    return TestClient(create_app(models))


@pytest.fixture(scope="module")
def html(client: TestClient) -> str:
    return client.get("/").text


@pytest.fixture(scope="module")
def css(client: TestClient) -> str:
    return client.get("/static/style.css").text


@pytest.fixture(scope="module")
def js(client: TestClient) -> str:
    return client.get("/static/app.js").text


def test_root_and_artist_addresses_serve_one_html_page(client: TestClient, html: str) -> None:
    for path in ("/", f"/artist/{artist_mbid(1)}", "/artist/not-an-id"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert response.text == html
    assert "<title>" in html and html.lstrip().lower().startswith("<!doctype html>")


def test_page_declares_language_one_h1_one_h2_and_the_visible_label(html: str) -> None:
    assert re.search(r'<html lang="en"', html)
    assert len(re.findall(r"<h1[\s>]", html)) == 1
    assert len(re.findall(r"<h2[\s>]", html)) == 1
    assert re.search(r'<label for="artist-search"[^>]*>\s*Artist\s*</label>', html)


def test_search_box_has_combobox_and_listbox_roles_a_live_region_and_clear_button(
    html: str,
) -> None:
    assert 'role="combobox"' in html and 'aria-controls="suggestions"' in html
    assert 'role="listbox"' in html
    assert re.search(r'aria-live="polite"', html)
    assert re.search(r'<button[^>]*id="clear-search"[^>]*aria-label="Clear', html)
    assert 'id="artist-search"' in html and 'autocomplete="off"' in html


def test_page_has_no_inline_script_style_or_event_handlers(html: str) -> None:
    assert "<style" not in html
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html)
    assert not re.search(r"\son[a-z]+\s*=", html)
    assert not re.search(r'style\s*=\s*"', html)
    assert '<link rel="stylesheet" href="/static/style.css">' in html
    assert re.search(r'<script src="/static/app.js" defer>', html)


def test_icons_are_inline_svg_templates_with_no_outside_files(html: str) -> None:
    assert 'id="link-icons"' in html
    for name in ("musicbrainz", "youtube", "spotify"):
        assert f'data-icon="{name}"' in html
    assert "<img" not in html


def test_stylesheet_has_the_design_tokens_focus_ring_and_radii(css: str) -> None:
    squashed = re.sub(r"\s+", "", css)
    for token in (
        "--ink:#1d2939",
        "--muted:#617184",
        "--line:#e2e8ef",
        "--accent:#176b80",
        "--surface:#fff",
        "--bg:#f5f7f9",
    ):
        assert token in squashed
    assert "3pxsolid#93d3e1" in squashed and "outline-offset:2px" in squashed
    assert "border-radius:14px" in squashed and "border-radius:9px" in squashed
    assert "max-width:800px" in squashed
    assert "system-ui" in css


def test_stylesheet_fits_a_375px_phone_and_wraps_long_names(css: str) -> None:
    squashed = re.sub(r"\s+", "", css)
    assert "@media(max-width:767px)" in squashed
    assert "overflow-wrap:break-word" in squashed or "overflow-wrap:anywhere" in squashed
    fixed = [
        int(n) for n in re.findall(r"(?<![-\w])(?:min-)?width:(\d+)px", squashed) if int(n) > 375
    ]
    assert fixed == []
    assert re.search(r"min-height:44px", squashed) and re.search(r"min-width:44px", squashed)
    assert "text-overflow:ellipsis" in squashed


def test_script_never_builds_markup_from_text(js: str) -> None:
    for call in FORBIDDEN_CALLS:
        assert call not in js, call
    for needed in ("createElement", "textContent", "setAttribute", "encodeURIComponent"):
        assert needed in js, needed


def test_script_has_the_pause_the_request_counters_and_the_busy_flag(js: str) -> None:
    assert re.search(r"SUGGEST_DELAY_MS\s*=\s*150\b", js)
    assert "suggestRequest" in js and "resultsRequest" in js
    assert re.search(r"\bbusy\b", js)
    assert "setTimeout" in js and "clearTimeout" in js
    assert "PAGE_SIZE = 20" in js
    assert ".focus()" in js


def test_script_uses_history_and_the_four_keys(js: str) -> None:
    assert "history.pushState" in js and "popstate" in js
    for key in ("ArrowDown", "ArrowUp", "Enter", "Escape"):
        assert f'"{key}"' in js, key
    assert "/artist/" in js and "/api/suggest" in js and "/api/artists/" in js


def test_script_holds_the_exact_messages(js: str) -> None:
    for message in (
        "No artists match '",
        "Not enough listening data to find artists like ",
        "We don't know this artist.",
        "Something went wrong finding similar artists. Try again.",
        "no genres listed",
        "Artists like ",
        "similarity ",
    ):
        assert message in js, message


def test_page_has_the_retry_and_show_more_buttons_hidden_at_start(html: str) -> None:
    assert re.search(r'<button id="retry-button"[^>]*hidden>Retry</button>', html)
    assert re.search(r'<button id="show-more"[^>]*hidden>Show more</button>', html)


def test_script_checks_the_three_link_prefixes_and_opens_links_safely(js: str) -> None:
    for prefix in LINK_PREFIXES:
        assert f'"{prefix}"' in js, prefix
    assert "noopener noreferrer" in js and "_blank" in js
    assert " on MusicBrainz" in js and " on YouTube" in js and " on Spotify" in js


def test_page_files_mention_no_other_website(html: str, css: str, js: str) -> None:
    for name, text in (("html", html), ("css", css), ("js", js)):
        cleaned = text
        for prefix in LINK_PREFIXES:
            cleaned = cleaned.replace(prefix, "")
        assert "http://" not in cleaned and "https://" not in cleaned, name
        assert "//cdn" not in cleaned and "@import" not in cleaned


def test_the_three_files_total_under_100_kb() -> None:
    sizes = {name: (STATIC / name).stat().st_size for name in ("index.html", "style.css", "app.js")}
    assert sum(sizes.values()) < 100 * 1024, sizes


def test_static_files_are_served_with_their_type_and_nothing_outside_the_folder(
    client: TestClient,
) -> None:
    assert client.get("/static/style.css").headers["content-type"].startswith("text/css")
    assert "javascript" in client.get("/static/app.js").headers["content-type"]
    assert client.get("/static/missing.js").status_code == 404
    escape = client.get("/static/../main.py")
    assert escape.status_code == 404 and "create_app" not in escape.text


def test_script_marks_the_search_box_focus_the_clear_button_and_live_region(js: str) -> None:
    assert re.search(r"search(Box|Input)\.focus\(\)", js)
    assert "clear-search" in js
    assert "aria-activedescendant" in js and "aria-expanded" in js
    assert "live-status" in js
