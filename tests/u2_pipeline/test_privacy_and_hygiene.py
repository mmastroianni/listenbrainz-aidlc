"""Privacy and repository rules: no listener data out, dumps untouched, nothing written elsewhere.

Covers AC4.1.1, AC4.1.5, AC4.1.6 and NFR3.4 to NFR3.8, NFR4.2, NFR5.2, NFR8.4.
"""

import ast
import hashlib
import os
import shutil
from pathlib import Path

import pytest
from conftest import FIXTURE_TRAIN_SETTINGS
from fixtures.sample_data import DISTINCT_LISTENER_NUMBERS, PRIVATE_LISTENER_NAME
from pyspark.sql import SparkSession

from listenbrainz_recs.catalogue import build_catalogue
from listenbrainz_recs.index import build
from listenbrainz_recs.paths import C2_FILES, output_paths
from listenbrainz_recs.prep import prepare
from listenbrainz_recs.train import train

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HTTP_CLIENT_MODULES = {"requests", "httpx", "aiohttp", "urllib3", "http.client", "urllib.request"}


def _snapshot(root: Path) -> dict[str, tuple[str, float]]:
    return {
        str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


@pytest.fixture(scope="module")
def full_run(
    sample_dump_root: Path,
    spark: SparkSession,
    tmp_path_factory: pytest.TempPathFactory,
    summaries: list[str],
) -> dict[str, object]:
    """Run the four steps on the fixture, noting the dump files and the surroundings."""
    base = tmp_path_factory.mktemp("hygiene")
    work, models = base / "work", base / "models"
    dump_before = _snapshot(sample_dump_root)
    cwd_before = set(os.listdir())

    printed = [
        prepare(sample_dump_root, work, spark).line(),
        train(work, spark, settings=FIXTURE_TRAIN_SETTINGS).line(),
        build_catalogue(sample_dump_root, work, models, spark).line(),
        build(work, models).line(),
    ]
    summaries.extend(printed)
    return {
        "base": base,
        "work": work,
        "models": models,
        "dump_before": dump_before,
        "dump_after": _snapshot(sample_dump_root),
        "cwd_new": set(os.listdir()) - cwd_before,
    }


@pytest.fixture(scope="module")
def summaries() -> list[str]:
    """Collects the one-line summaries each step prints."""
    return []


def test_no_built_file_or_summary_holds_a_listener_number_or_name(
    full_run: dict[str, object], summaries: list[str]
) -> None:
    models = full_run["models"]
    work = full_run["work"]
    assert isinstance(models, Path) and isinstance(work, Path)
    for number in map(str, DISTINCT_LISTENER_NUMBERS):
        for line in summaries:
            assert number not in line
        for name in C2_FILES:
            data = (models / name).read_bytes()
            assert number.encode() not in data, f"{number} found in {name}"
    for path in [*models.rglob("*"), *work.rglob("*")]:
        if path.is_file():
            assert PRIVATE_LISTENER_NAME.encode() not in path.read_bytes()
    paths = output_paths(work, models)
    for folder in (paths.artist_names, paths.artist_listeners, paths.vectors):
        for file in folder.glob("*.parquet"):
            assert b"user_id" not in file.read_bytes()  # no listener column outside interactions


def test_dump_files_are_unchanged_after_every_step(
    full_run: dict[str, object], sample_dump_root: Path
) -> None:
    assert full_run["dump_after"] == full_run["dump_before"]
    assert _snapshot(sample_dump_root) == full_run["dump_before"]


def test_each_step_creates_files_only_under_the_work_and_models_folders(
    full_run: dict[str, object],
) -> None:
    base = full_run["base"]
    assert isinstance(base, Path)
    assert {p.name for p in base.iterdir()} == {"work", "models"}
    assert full_run["cwd_new"] == set()  # nothing dropped into the working folder either
    work, models = full_run["work"], full_run["models"]
    assert isinstance(work, Path) and isinstance(models, Path)
    allowed = {p.name for p in output_paths(work, models).all_paths()}
    assert {p.name for p in work.iterdir()} <= allowed
    assert {p.name for p in models.iterdir()} == set(C2_FILES)


def test_the_spark_session_is_local_with_no_web_page_and_bound_to_loopback(
    spark: SparkSession,
) -> None:
    conf = spark.sparkContext.getConf()
    assert (conf.get("spark.master") or "").startswith("local")
    assert conf.get("spark.ui.enabled") == "false"
    assert conf.get("spark.driver.bindAddress") == "127.0.0.1"
    assert conf.get("spark.driver.host") == "127.0.0.1"
    assert spark.sparkContext.uiWebUrl is None


def test_gitignore_lists_the_data_and_models_folders_and_built_file_types() -> None:
    lines = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in ("/data/", "/models/", "*.parquet", "*.faiss", "*.sqlite"):
        assert entry in lines


def test_no_http_client_library_is_imported_anywhere_in_src() -> None:
    offenders: list[str] = []
    for source in (PROJECT_ROOT / "src").rglob("*.py"):
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module, *(f"{node.module}.{alias.name}" for alias in node.names)]
            offenders += [
                f"{source.name}: {n}"
                for n in names
                if n in HTTP_CLIENT_MODULES or n.split(".")[0] in {"requests", "httpx", "aiohttp"}
            ]
    assert offenders == []


def test_a_copy_of_the_dump_folder_read_by_the_steps_stays_byte_identical(
    sample_dump_root: Path, spark: SparkSession, tmp_path: Path
) -> None:
    """The same check on a private read-only copy, so a stray write would also show as an error."""
    root = tmp_path / "root"
    shutil.copytree(sample_dump_root, root)
    for path in root.rglob("*"):
        path.chmod(0o555 if path.is_dir() else 0o444)
    try:
        before = _snapshot(root)
        prepare(root, tmp_path / "work", spark)
        assert _snapshot(root) == before
    finally:
        for path in root.rglob("*"):
            path.chmod(0o755 if path.is_dir() else 0o644)
