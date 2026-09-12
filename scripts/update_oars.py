"""Publish a cask update only after all three release archives are verified."""

import hashlib
import io
import json
from pathlib import Path
import plistlib
import re
import struct
import subprocess
import tarfile
import tempfile
import zipfile

REPO = "onyedikachi-david/oars"
ROOT = Path(__file__).resolve().parents[1]
CASK = ROOT / "Casks/oars.rb"
ASSETS = {"macos_arm64": "macos.zip", "macos_x86_64": "macos-x86_64.zip", "linux_x86_64": "linux-x86_64.tar.gz"}
CHECKSUM_PATTERNS = {
    "macos_arm64": r'\barm:\s*"([a-f0-9]{64})"',
    "macos_x86_64": r'\bintel:\s*"([a-f0-9]{64})"',
    "linux_x86_64": r'on_linux do\s+sha256 "([a-f0-9]{64})"',
}


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
    required = {f"oars-v{version}-{suffix}" for suffix in ASSETS.values()} | {"SHA256SUMS"}
    uploaded = {a["name"] for a in release["assets"] if a["state"] == "uploaded"}
    return version if required <= uploaded else None


def verify_archive(version, platform, archive, checksums):
    version_tuple(version)
    filename = f"oars-v{version}-{ASSETS[platform]}"
    matches = re.findall(r"^([a-f0-9]{64})\s+\*?" + re.escape(filename) + r"$", checksums, re.MULTILINE)
    digest = hashlib.sha256(archive).hexdigest()
    if matches != [digest]:
        raise ValueError(f"{platform} archive does not match SHA256SUMS")
    if platform.startswith("macos_"):
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
            cpu = 0x0100000C if platform == "macos_arm64" else 0x01000007
            if len(executable) < 8 or executable[:4] != b"\xcf\xfa\xed\xfe" or struct.unpack_from("<I", executable, 4)[0] != cpu:
                raise ValueError(f"Unexpected executable architecture for {platform}")
            if not package.read(bundle + "Resources/frontend/dist/index.html"):
                raise ValueError("Missing packaged frontend")
    else:
        bundle = f"oars-{version}-linux-ReleaseFast/"
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
            members = {m.name.removeprefix("./"): m for m in package.getmembers()}

            def read(path):
                member = members[bundle + path]
                if not member.isfile():
                    raise ValueError(f"Expected a regular package file: {path}")
                return package.extractfile(member).read()

            executable = read("bin/oars")
            if len(executable) < 20 or executable[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", executable, 18)[0] != 62:
                raise ValueError("Expected a Linux x86_64 executable")
            manifest = read("package-manifest.zon").decode()
            for field, value in {"version": version, "app_id": "app.getoars", "target": "linux", "executable": "oars"}.items():
                if not re.search(r"\." + field + r'\s*=\s*"' + re.escape(value) + '"', manifest):
                    raise ValueError(f"Unexpected Linux package {field}")
            desktop = read("share/applications/oars.desktop").decode()
            if 'Exec="oars"' not in desktop or 'Icon=app-icon' not in desktop:
                raise ValueError("Linux desktop entry changed; review the cask")
            if not read("resources/frontend/dist/index.html"):
                raise ValueError("Missing packaged frontend")
            read("share/icons/hicolor/256x256/apps/app-icon.png")
    return digest


def render_cask(version, digests):
    version_tuple(version)
    if set(digests) != set(ASSETS) or not all(re.fullmatch(r"[a-f0-9]{64}", d) for d in digests.values()):
        raise ValueError("All three package checksums are required")
    result = (ROOT / "templates/oars.rb").read_text().replace("@VERSION@", version)
    for platform, digest in digests.items():
        result = result.replace("@" + platform.upper() + "@", digest)
    return result


def updated_cask(current_text, version, digests):
    current = re.search(r'^  version "([^"]+)"$', current_text, re.MULTILINE)[1]
    if version_tuple(version) < version_tuple(current):
        raise ValueError("Refusing to downgrade the cask")
    if version == current:
        for platform, pattern in CHECKSUM_PATTERNS.items():
            previous = re.search(pattern, current_text)
            if previous is None or previous[1] != digests.get(platform):
                raise ValueError("Existing release archive changed; manual review required")
    return render_cask(version, digests)


def main():
    current_text = CASK.read_text()
    current = re.search(r'^  version "([^"]+)"$', current_text, re.MULTILINE)[1]
    release = json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/releases/latest"]))
    version = release_version(release, current)
    if version is None:
        print("Latest release is not ready on all platforms; leaving the cask unchanged.")
        return
    with tempfile.TemporaryDirectory(prefix="oars-cask-") as directory:
        command = ["gh", "release", "download", f"v{version}", "--repo", REPO, "--dir", directory, "--pattern", "SHA256SUMS"]
        for suffix in ASSETS.values():
            command += ["--pattern", f"oars-v{version}-{suffix}"]
        subprocess.run(command, check=True)
        assets = Path(directory)
        checksums = (assets / "SHA256SUMS").read_text()
        digests = {platform: verify_archive(version, platform, (assets / f"oars-v{version}-{suffix}").read_bytes(), checksums)
                   for platform, suffix in ASSETS.items()}
    result = updated_cask(current_text, version, digests)
    if result == current_text:
        print(f"Oars {version} is current; all three package checksums are unchanged.")
        return
    CASK.write_text(result)
    print(f"Updated Oars to {version} after verifying all three release archives.")


if __name__ == "__main__":
    main()
