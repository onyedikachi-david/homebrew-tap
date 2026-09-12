"""Update the cask only after a complete, verified stable release is available."""

import hashlib
import io
import json
from pathlib import Path
import plistlib
import re
import struct
import subprocess
import tempfile
import zipfile


REPO = "onyedikachi-david/oars"
CASK = Path(__file__).resolve().parents[1] / "Casks/oars.rb"


def version_tuple(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError(f"Unsupported release version: {value!r}")
    return tuple(map(int, value.split(".")))


def release_version(release, current):
    if release["draft"] or release["prerelease"]:
        return None
    tag = release["tag_name"]
    if not tag.startswith("v"):
        raise ValueError("Expected a v-prefixed release tag")
    version = tag[1:]
    if version_tuple(version) < version_tuple(current):
        raise ValueError("Refusing to downgrade the cask")
    required = {f"oars-v{version}-macos.zip", "SHA256SUMS"}
    uploaded = {a["name"] for a in release["assets"] if a["state"] == "uploaded"}
    return version if required <= uploaded else None


def verify_archive(version, archive, checksums):
    filename = f"oars-v{version}-macos.zip"
    matches = re.findall(r"^([a-f0-9]{64})\s+\*?" + re.escape(filename) + r"$",
                         checksums, re.MULTILINE)
    digest = hashlib.sha256(archive).hexdigest()
    if matches != [digest]:
        raise ValueError("Release archive does not match SHA256SUMS")
    bundle = f"oars-{version}-macos-ReleaseFast.app/Contents/"
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        info = plistlib.loads(package.read(bundle + "Info.plist"))
        if (info["CFBundleIdentifier"] != "app.getoars"
                or info["CFBundleShortVersionString"] != version
                or info["CFBundleExecutable"] != "oars"):
            raise ValueError("Unexpected app identity or version")
        if info["LSMinimumSystemVersion"] != "11.0":
            raise ValueError("macOS requirement changed; review the cask")
        executable = package.read(bundle + "MacOS/oars")
        if executable[:4] != b"\xcf\xfa\xed\xfe" or struct.unpack_from("<I", executable, 4)[0] != 0x0100000C:
            raise ValueError("Expected an Apple Silicon executable; review the cask")
    return digest


def updated_cask(current_text, version, digest):
    current = re.search(r'^  version "([^"]+)"$', current_text, re.MULTILINE)[1]
    version_tuple(version)
    if version_tuple(version) < version_tuple(current):
        raise ValueError("Refusing to downgrade the cask")
    old_digest = re.search(r'^  sha256 "([a-f0-9]{64})"$', current_text, re.MULTILINE)[1]
    if version == current and digest != old_digest:
        raise ValueError("Existing release archive changed; manual review required")
    result = re.sub(r'^  version "[^"]+"$', f'  version "{version}"', current_text, flags=re.MULTILINE)
    return re.sub(r'^  sha256 "[a-f0-9]{64}"$', f'  sha256 "{digest}"', result, flags=re.MULTILINE)


def main():
    current_text = CASK.read_text()
    current = re.search(r'^  version "([^"]+)"$', current_text, re.MULTILINE)[1]
    release = json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/releases/latest"]))
    version = release_version(release, current)
    if version is None:
        print("Latest release is not ready; leaving the cask unchanged.")
        return
    filename = f"oars-v{version}-macos.zip"
    with tempfile.TemporaryDirectory(prefix="oars-cask-") as directory:
        subprocess.run(["gh", "release", "download", f"v{version}", "--repo", REPO,
                        "--pattern", filename, "--pattern", "SHA256SUMS", "--dir", directory], check=True)
        assets = Path(directory)
        digest = verify_archive(version, (assets / filename).read_bytes(), (assets / "SHA256SUMS").read_text())
    result = updated_cask(current_text, version, digest)
    if result == current_text:
        print(f"Oars {version} is already current and its checksum is unchanged.")
        return
    CASK.write_text(result)
    print(f"Updated Oars to {version} after verifying its release archive.")


if __name__ == "__main__":
    main()
