import argparse
import os
import platform
import requests
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GO2RTC_VERSION = "1.9.14"
VERSION_MARKER = b'version_string = "rokenbok-webserver (dev)"'


def detect_target():
    machine = platform.machine().lower()
    if sys.platform == "win32" and machine in ("amd64", "x86_64"):
        return "win64", "win"
    if sys.platform == "darwin":
        if machine == "x86_64":
            return "mac_amd64", "mac_intel"
        if machine in ("arm64", "aarch64"):
            return "mac_arm64", "mac"
    raise RuntimeError(f"Unsupported build platform: {sys.platform} {machine}")


def download(url, destination):
    print(f"Downloading {url}")
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(destination, "wb") as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    out_file.write(chunk)


def extract_binary(archive_path, destination, member_name):
    with zipfile.ZipFile(archive_path) as archive:
        candidates = [name for name in archive.namelist() if Path(name).name.lower() == member_name.lower()]
        if not candidates:
            raise RuntimeError(f"{member_name} was not found in {archive_path}")
        with archive.open(candidates[0]) as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target)


def download_binaries(go2rtc_arch):
    binary_dir = ROOT / "bin"
    binary_dir.mkdir(exist_ok=True)
    go2rtc_path = binary_dir / "go2rtc"
    ffmpeg_path = binary_dir / "ffmpeg.bin"
    for path in (go2rtc_path, binary_dir / "go2rtc.exe", ffmpeg_path):
        path.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        go2rtc_archive = temporary_path / "go2rtc.zip"
        download(
            f"https://github.com/AlexxIT/go2rtc/releases/download/v{GO2RTC_VERSION}/go2rtc_{go2rtc_arch}.zip",
            go2rtc_archive,
        )
        go2rtc_member = "go2rtc.exe" if go2rtc_arch == "win64" else "go2rtc"
        extract_binary(go2rtc_archive, go2rtc_path, go2rtc_member)

        ffmpeg_archive = temporary_path / "ffmpeg.zip"
        if go2rtc_arch == "win64":
            ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            ffmpeg_member = "ffmpeg.exe"
        else:
            architecture = go2rtc_arch.removeprefix("mac_")
            ffmpeg_url = f"https://ffmpeg.martin-riedl.de/redirect/latest/macos/{architecture}/release/ffmpeg.zip"
            ffmpeg_member = "ffmpeg"
        download(ffmpeg_url, ffmpeg_archive)
        extract_binary(ffmpeg_archive, ffmpeg_path, ffmpeg_member)

    if os.name != "nt":
        go2rtc_path.chmod(go2rtc_path.stat().st_mode | 0o111)
        ffmpeg_path.chmod(ffmpeg_path.stat().st_mode | 0o111)


def build(download_name):
    with (ROOT / "pyproject.toml").open("rb") as project_file:
        version = tomllib.load(project_file)["project"]["version"]
    commit_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()[:6]

    source_path = ROOT / "rokenbok_webserver.py"
    original_source = source_path.read_bytes()
    if original_source.count(VERSION_MARKER) != 1:
        raise RuntimeError(f"Expected one version marker in {source_path.name}")
    version_string = f"rokenbok-webserver {version}+{commit_hash}"
    source_path.write_bytes(
        original_source.replace(
            VERSION_MARKER,
            f"version_string = {version_string!r}".encode(),
            1,
        )
    )

    try:
        dist_dir = ROOT / "dist"
        dist_dir.mkdir(exist_ok=True)
        executable = dist_dir / ("rokenbok_webserver.exe" if sys.platform == "win32" else "rokenbok_webserver")
        executable.unlink(missing_ok=True)
        subprocess.run(["uv", "sync"], cwd=ROOT, check=True)
        subprocess.run(["uv", "run", "pyinstaller", "pyinstaller.spec"], cwd=ROOT, check=True)
    finally:
        source_path.write_bytes(original_source)

    if not executable.is_file():
        raise RuntimeError(f"PyInstaller did not produce {executable.name}")
    shutil.copy2(ROOT / "settings.ini", dist_dir / "settings.ini")

    artifact_name = f"rokenbok_webserver_{version}_{commit_hash}_{download_name}"
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as environment_file:
            environment_file.write(f"ARTIFACT_NAME={artifact_name}\n")
    print(f"rokenbok-webserver version: {version_string}")
    print(f"Commit hash: {commit_hash}")
    print(f"Artifact name: {artifact_name}")


def main():
    parser = argparse.ArgumentParser(description="Download build dependencies and package rokenbok-webserver.")
    parser.parse_args()
    go2rtc_arch, download_name = detect_target()
    print(f"Building {download_name} target ({go2rtc_arch})")
    download_binaries(go2rtc_arch)
    build(download_name)


if __name__ == "__main__":
    main()
