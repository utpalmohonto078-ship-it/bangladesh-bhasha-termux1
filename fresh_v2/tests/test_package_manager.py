import json
from pathlib import Path

import pytest

import package_manager as pm


def make_package(root, name="demo-lib", version="1.2.0"):
    root.mkdir(parents=True)
    (root / pm.MANIFEST).write_text(
        json.dumps({
            "name": name,
            "version": version,
            "dependencies": {},
        }),
        encoding="utf-8",
    )
    (root / "hello.bb").write_text('লিখো "Hello"\n', encoding="utf-8")
    return root


def test_init_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert pm.init_project("my-project") is True

    data = json.loads((tmp_path / pm.MANIFEST).read_text())
    assert data["name"] == "my-project"
    assert data["dependencies"] == {}


def test_init_rejects_duplicate_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pm.init_project("my-project")

    with pytest.raises(pm.PackageError):
        pm.init_project("another-project")


def test_init_rejects_invalid_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(pm.PackageError):
        pm.init_project("../bad")


def test_install_package(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = make_package(tmp_path / "source")

    assert pm.install_package(source) is True
    installed = tmp_path / pm.PACKAGE_DIR / "demo-lib"

    assert (installed / "hello.bb").is_file()
    assert (installed / pm.MANIFEST).is_file()


def test_add_records_dependency(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pm.init_project("my-project")
    source = make_package(tmp_path / "source")

    pm.install_package(source, record_dependency=True)

    data = json.loads((tmp_path / pm.MANIFEST).read_text())
    assert data["dependencies"]["demo-lib"] == "1.2.0"


def test_install_rejects_duplicate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = make_package(tmp_path / "source")

    pm.install_package(source)

    with pytest.raises(pm.PackageError):
        pm.install_package(source)


def test_install_rejects_missing_bb_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "empty"
    source.mkdir()
    (source / pm.MANIFEST).write_text('{"name":"empty-lib"}')

    with pytest.raises(pm.PackageError):
        pm.install_package(source)


def test_remove_package(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pm.init_project("my-project")
    source = make_package(tmp_path / "source")
    pm.install_package(source, record_dependency=True)

    assert pm.remove_package("demo-lib") is True
    assert not (tmp_path / pm.PACKAGE_DIR / "demo-lib").exists()

    data = json.loads((tmp_path / pm.MANIFEST).read_text())
    assert "demo-lib" not in data["dependencies"]


def test_remove_rejects_invalid_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(pm.PackageError):
        pm.remove_package("../outside")


def test_list_packages(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    source = make_package(tmp_path / "source")
    pm.install_package(source)

    assert pm.list_packages() is True
    assert "demo-lib" in capsys.readouterr().out


def test_cli_package_help():
    assert pm.handle_package_command(["help"]) is True


def test_install_rejects_bhasha_parent_symlink(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = make_package(tmp_path / "source")
    outside = tmp_path / "outside"
    outside.mkdir()

    try:
        (tmp_path / ".bhasha").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable")

    with pytest.raises(pm.PackageError):
        pm.install_package(source)

    assert not (outside / "packages").exists()


def test_install_rejects_source_symlink(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    source = make_package(tmp_path / "source")
    link = tmp_path / "source-link"

    try:
        link.symlink_to(source, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable")

    with pytest.raises(pm.PackageError):
        pm.install_package(link)


def test_remove_rolls_back_if_manifest_write_fails(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    pm.init_project("my-project")

    source = make_package(tmp_path / "source")
    pm.install_package(source, record_dependency=True)

    original_writer = pm._write_json_atomic

    def failing_writer(path, data):
        raise OSError("simulated manifest write failure")

    monkeypatch.setattr(pm, "_write_json_atomic", failing_writer)

    with pytest.raises(OSError):
        pm.remove_package("demo-lib")

    installed = tmp_path / pm.PACKAGE_DIR / "demo-lib"
    assert installed.is_dir()
    assert (installed / "hello.bb").is_file()

    data = json.loads((tmp_path / pm.MANIFEST).read_text())
    assert data["dependencies"]["demo-lib"] == "1.2.0"

    monkeypatch.setattr(pm, "_write_json_atomic", original_writer)


def test_list_rejects_bhasha_parent_symlink(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    outside = tmp_path / "outside"
    outside.mkdir()

    try:
        (tmp_path / ".bhasha").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable")

    with pytest.raises(pm.PackageError):
        pm.list_packages()


def test_manifest_size_limit(tmp_path):
    import package_manager as pm
    import pytest

    (tmp_path / pm.MANIFEST).write_bytes(b" " * (pm.MAX_MANIFEST_SIZE + 1))

    with pytest.raises(pm.PackageError):
        pm._read_manifest(tmp_path)


def test_manifest_rejects_duplicate_json_keys(tmp_path):
    import package_manager as pm
    import pytest

    (tmp_path / pm.MANIFEST).write_text(
        '{"name":"first","name":"second","version":"1.0.0"}',
        encoding="utf-8",
    )

    with pytest.raises(pm.PackageError, match="Duplicate JSON key"):
        pm._read_manifest(tmp_path)


def test_package_file_count_limit(tmp_path):
    import package_manager as pm
    import pytest

    for index in range(pm.MAX_PACKAGE_FILES + 1):
        (tmp_path / f"file-{index:03}.bb").write_text(
            "লিখো 1\\n", encoding="utf-8"
        )

    with pytest.raises(pm.PackageError, match="100"):
        pm._package_files(tmp_path)


def test_package_single_file_size_limit(tmp_path):
    import package_manager as pm
    import pytest

    (tmp_path / "large.bb").write_bytes(
        b"x" * (pm.MAX_PACKAGE_FILE_SIZE + 1)
    )

    with pytest.raises(pm.PackageError, match="1 MiB"):
        pm._package_files(tmp_path)


def test_package_total_size_limit(tmp_path):
    import package_manager as pm
    import pytest

    for index in range(11):
        (tmp_path / f"part-{index:02}.bb").write_bytes(
            b"x" * pm.MAX_PACKAGE_FILE_SIZE
        )

    with pytest.raises(pm.PackageError, match="10 MiB"):
        pm._package_files(tmp_path)


def test_copy_limited_rejects_file_that_grows_after_scan(tmp_path, monkeypatch):
    source = make_package(tmp_path / "source")
    monkeypatch.chdir(tmp_path)

    original = pm._copy_limited

    def grow_before_copy(path, target, max_bytes, label):
        if Path(path).name == "hello.bb":
            Path(path).write_bytes(b"x" * (pm.MAX_PACKAGE_FILE_SIZE + 1))
        return original(path, target, max_bytes, label)

    monkeypatch.setattr(pm, "_copy_limited", grow_before_copy)

    with pytest.raises(pm.PackageError, match="Size Limit"):
        pm.install_package(source)

    installed = tmp_path / pm.PACKAGE_DIR / "demo-lib"
    assert not installed.exists()


def test_copy_limited_enforces_exact_limit(tmp_path):
    source = tmp_path / "source.bb"
    target = tmp_path / "target.bb"
    source.write_bytes(b"12345")

    copied = pm._copy_limited(source, target, 5, "test")
    assert copied == 5
    assert target.read_bytes() == b"12345"


def test_copy_limited_rejects_oversize_and_cleans_target(tmp_path):
    source = tmp_path / "source.bb"
    target = tmp_path / "target.bb"
    source.write_bytes(b"123456")

    with pytest.raises(pm.PackageError, match="Size Limit"):
        pm._copy_limited(source, target, 5, "test")

    assert not target.exists()
