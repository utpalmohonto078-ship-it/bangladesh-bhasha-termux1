import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path


MANIFEST = "bhasha-package.json"
PACKAGE_DIR = ".bhasha/packages"
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

MAX_MANIFEST_SIZE = 64 * 1024
MAX_PACKAGE_FILES = 100
MAX_PACKAGE_FILE_SIZE = 1024 * 1024
MAX_PACKAGE_TOTAL_SIZE = 10 * 1024 * 1024


class PackageError(Exception):
    pass


def _reject_duplicate_keys(pairs):
    result = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value

    return result


def _read_manifest(path):
    manifest = path / MANIFEST

    if manifest.is_symlink() or not manifest.is_file():
        raise PackageError(f"Manifest পাওয়া যায়নি: {manifest}")

    try:
        raw = manifest.read_bytes()

        if len(raw) > MAX_MANIFEST_SIZE:
            raise PackageError("Manifest 64 KiB সীমা অতিক্রম করেছে।")

        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except PackageError:
        raise
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise PackageError(f"Manifest ভুল: {exc}") from exc

    if not isinstance(data, dict):
        raise PackageError("Manifest অবশ্যই JSON object হতে হবে।")

    name = data.get("name")
    version = data.get("version", "1.0.0")
    dependencies = data.get("dependencies", {})

    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise PackageError("Package name সঠিক নয়।")

    if not isinstance(version, str) or not version.strip():
        raise PackageError("Package version সঠিক নয়।")

    if not isinstance(dependencies, dict):
        raise PackageError("dependencies অবশ্যই JSON object হতে হবে।")

    for dep, dep_version in dependencies.items():
        if not isinstance(dep, str) or not NAME_PATTERN.fullmatch(dep):
            raise PackageError(f"Dependency name ভুল: {dep}")
        if not isinstance(dep_version, str) or not dep_version.strip():
            raise PackageError(f"Dependency version ভুল: {dep}")

    return data


def _write_json_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.is_symlink():
        raise PackageError(f"Manifest Symlink হতে পারবে না: {path}")

    fd, temp_name = tempfile.mkstemp(
        prefix=".bhasha-manifest-",
        dir=str(path.parent),
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")

        os.replace(temp_name, path)

    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _safe_packages_root(create=False):
    root = Path.cwd()
    hidden = root / ".bhasha"
    packages = root / PACKAGE_DIR

    if hidden.is_symlink():
        raise PackageError(".bhasha directory Symlink হতে পারবে না।")

    if hidden.exists() and not hidden.is_dir():
        raise PackageError(".bhasha একটি directory হতে হবে।")

    if packages.is_symlink():
        raise PackageError("Package directory Symlink হতে পারবে না।")

    if packages.exists() and not packages.is_dir():
        raise PackageError("Package installation path directory নয়।")

    if create:
        packages.mkdir(parents=True, exist_ok=True)

        if hidden.is_symlink() or packages.is_symlink():
            raise PackageError("Symlink directory অনুমোদিত নয়।")

    return packages


def _reject_symlink_components(path):
    absolute = Path(os.path.abspath(str(path)))

    for item in (absolute, *absolute.parents):
        if item.is_symlink():
            raise PackageError(f"Source path-এ Symlink অনুমোদিত নয়: {item}")


def init_project(name=None):
    root = Path.cwd()

    if name is None:
        name = root.name.lower().replace(" ", "-")

    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise PackageError("Package name সঠিক নয়।")

    manifest = root / MANIFEST

    if manifest.exists() or manifest.is_symlink():
        raise PackageError("Manifest আগে থেকেই আছে।")

    data = {
        "name": name,
        "version": "1.0.0",
        "description": "",
        "dependencies": {},
    }

    _write_json_atomic(manifest, data)
    print(f"Package project তৈরি: {manifest}")
    return True


def _package_files(source):
    files = []
    total_size = 0

    def walk_error(error):
        raise PackageError(f"Package directory পড়া যায়নি: {error}")

    for current, dirs, names in os.walk(
        source,
        followlinks=False,
        onerror=walk_error,
    ):
        current_path = Path(current)

        for directory in list(dirs):
            item = current_path / directory
            if item.is_symlink():
                raise PackageError(f"Symlink directory অনুমোদিত নয়: {item}")

        dirs[:] = sorted(dirs)

        for filename in sorted(names):
            item = current_path / filename

            if item.is_symlink():
                raise PackageError(f"Symlink file অনুমোদিত নয়: {item}")

            if item.name == MANIFEST:
                continue

            if item.suffix == ".bb":
                if not item.is_file():
                    raise PackageError(f"সঠিক ফাইল নয়: {item}")

                if len(files) >= MAX_PACKAGE_FILES:
                    raise PackageError("Package-এ সর্বোচ্চ 100টি .bb ফাইল অনুমোদিত।")

                try:
                    size = item.stat().st_size
                except OSError as exc:
                    raise PackageError(f"ফাইলের আকার পড়া যায়নি: {item}") from exc

                if size > MAX_PACKAGE_FILE_SIZE:
                    raise PackageError(f".bb ফাইল 1 MiB সীমা অতিক্রম করেছে: {item}")

                total_size += size

                if total_size > MAX_PACKAGE_TOTAL_SIZE:
                    raise PackageError("Package-এর মোট source size 10 MiB সীমা অতিক্রম করেছে।")

                files.append(item)

    if not files:
        raise PackageError("Package-এ কোনো .bb source file পাওয়া যায়নি।")

    return files



def _copy_limited(source, target, max_bytes, label):
    """Copy a regular file while enforcing a hard read-size limit."""
    source = Path(source)
    target = Path(target)

    if type(max_bytes) is not int or max_bytes < 0:
        raise PackageError("Copy size limit সঠিক নয়।")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)

    try:
        fd = os.open(str(source), flags)
    except OSError as exc:
        raise PackageError(f"{label} খোলা যায়নি: {source}") from exc

    copied = 0
    try:
        with os.fdopen(fd, "rb") as src:
            if not stat.S_ISREG(os.fstat(src.fileno()).st_mode):
                raise PackageError(f"{label} নিয়মিত ফাইল নয়: {source}")

            target.parent.mkdir(parents=True, exist_ok=True)

            with target.open("xb") as dst:
                while True:
                    chunk = src.read(min(65536, max_bytes - copied + 1))
                    if not chunk:
                        break

                    if copied + len(chunk) > max_bytes:
                        raise PackageError(f"{label} নির্ধারিত Size Limit অতিক্রম করেছে।")

                    dst.write(chunk)
                    copied += len(chunk)

        return copied

    except Exception:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise

def install_package(source_path, record_dependency=False):
    source_input = Path(source_path).expanduser()
    _reject_symlink_components(source_input)

    source = source_input.resolve(strict=True)

    if not source.is_dir():
        raise PackageError("Package source একটি directory হতে হবে।")

    package = _read_manifest(source)
    files = _package_files(source)

    root = Path.cwd()
    project_manifest = root / MANIFEST

    project = None
    if project_manifest.exists() or project_manifest.is_symlink():
        project = _read_manifest(root)

    if record_dependency and project is None:
        raise PackageError("আগে 'bhasha pkg init' চালান।")

    name = package["name"]
    packages_root = _safe_packages_root(create=True)
    destination = packages_root / name

    if destination.exists() or destination.is_symlink():
        raise PackageError(f"Package আগে থেকেই ইনস্টল আছে: {name}")

    staging = Path(tempfile.mkdtemp(
        prefix=".install-",
        dir=str(packages_root),
    ))

    try:
        copied_total = 0

        for file_path in files:
            relative = file_path.relative_to(source)
            target = staging / relative

            remaining = MAX_PACKAGE_TOTAL_SIZE - copied_total
            allowed = min(MAX_PACKAGE_FILE_SIZE, remaining)

            copied = _copy_limited(
                file_path, target, allowed, ".bb source file"
            )
            copied_total += copied

        _copy_limited(
            source / MANIFEST,
            staging / MANIFEST,
            MAX_MANIFEST_SIZE,
            "Manifest",
        )

        # Copy চলাকালে Manifest বদলে গেলে Installation বাতিল।
        if _read_manifest(staging) != package:
            raise PackageError("Installation চলাকালে Manifest পরিবর্তিত হয়েছে।")

        os.replace(staging, destination)

        if record_dependency:
            project["dependencies"][name] = package.get("version", "1.0.0")

            try:
                _write_json_atomic(project_manifest, project)
            except Exception:
                shutil.rmtree(destination, ignore_errors=True)
                raise

    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    print(f"Package ইনস্টল সফল: {name} ({package.get('version', '1.0.0')})")
    print(f"Location: {destination}")
    return True


def remove_package(name):
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise PackageError("Package name সঠিক নয়।")

    root = Path.cwd()
    packages_root = _safe_packages_root(create=False)
    destination = packages_root / name

    if destination.is_symlink():
        raise PackageError("Installed package Symlink হলে সরানো যাবে না।")

    if not destination.is_dir():
        raise PackageError(f"Package ইনস্টল নেই: {name}")

    project_manifest = root / MANIFEST
    project = None

    if project_manifest.exists() or project_manifest.is_symlink():
        project = _read_manifest(root)

    # Package আগে quarantine নামে সরানো হবে।
    quarantine = Path(tempfile.mkdtemp(
        prefix=".remove-",
        dir=str(packages_root),
    ))
    quarantine.rmdir()

    os.replace(destination, quarantine)

    if project is not None:
        old_project = json.loads(json.dumps(project))
        project["dependencies"].pop(name, None)

        try:
            _write_json_atomic(project_manifest, project)
        except Exception:
            # Manifest update ব্যর্থ হলে Package ফিরিয়ে আনা হবে।
            try:
                os.replace(quarantine, destination)
            except OSError as rollback_error:
                raise PackageError(
                    f"Manifest ব্যর্থ এবং Package Rollback-ও ব্যর্থ: "
                    f"{rollback_error}"
                )
            raise

    try:
        shutil.rmtree(quarantine)
    except OSError as exc:
        # Manifest ও Installed Package state সামঞ্জস্যপূর্ণ থাকবে।
        print(f"সতর্কতা: অস্থায়ী Package মুছতে পারেনি: {exc}")

    print(f"Package সরানো হয়েছে: {name}")
    return True


def list_packages():
    packages_root = _safe_packages_root(create=False)

    print("Installed Bangladesh Bhasha packages:")

    if not packages_root.exists():
        print("(কোনো Package ইনস্টল নেই)")
        return True

    found = False

    for directory in sorted(packages_root.iterdir()):
        if directory.is_symlink():
            print(f"INVALID SYMLINK: {directory.name}")
            continue

        if not directory.is_dir():
            continue

        try:
            data = _read_manifest(directory)
        except PackageError:
            print(f"INVALID: {directory.name}")
            continue

        found = True
        print(f"{data['name']}  v{data.get('version', '1.0.0')}")

    if not found:
        print("(কোনো Package ইনস্টল নেই)")

    return True


def handle_package_command(args):
    try:
        if not args or args[0] in ("help", "--help", "-h"):
            print(
                "Package Manager:\n"
                "  bhasha pkg init [name]\n"
                "  bhasha pkg install <package-directory>\n"
                "  bhasha pkg add <package-directory>\n"
                "  bhasha pkg remove <name>\n"
                "  bhasha pkg list"
            )
            return True

        command = args[0]

        if command == "init" and len(args) <= 2:
            return init_project(args[1] if len(args) == 2 else None)

        if command == "install" and len(args) == 2:
            return install_package(args[1], record_dependency=False)

        if command == "add" and len(args) == 2:
            return install_package(args[1], record_dependency=True)

        if command == "remove" and len(args) == 2:
            return remove_package(args[1])

        if command == "list" and len(args) == 1:
            return list_packages()

        raise PackageError("ভুল command বা argument। 'bhasha pkg help' দেখুন।")

    except (PackageError, OSError, ValueError) as exc:
        print(f"Package Error: {exc}")
        return False
