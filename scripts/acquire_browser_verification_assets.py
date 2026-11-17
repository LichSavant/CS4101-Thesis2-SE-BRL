"""Verify pinned local archives; download only with explicit --acquire approval.

No model or browser downloads. Extracted software stays in the ignored harness.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".venv-transformer/browser-harness"
PINS = ROOT / "tools/verification/browser-fp32/packages.v1.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquire", action="store_true", help="Requires explicit user approval for these exact archives")
    args = parser.parse_args()
    pins = json.loads(PINS.read_text(encoding="utf-8"))
    result = []
    directories = {"onnxruntime-web": "ort", "@huggingface/tokenizers": "tokenizers", "pyodide": "pyodide"}
    for package in pins["approved_packages"]:
        name, version = package["name"], package["version"]
        directory = directories[name]
        archive = LOCAL / "archives" / (directory + "-" + version + ".tgz")
        if not archive.exists():
            if not args.acquire:
                raise RuntimeError("Missing archive; explicit acquisition approval required: " + name)
            assert package["url"].startswith("https://registry.npmjs.org/")
            archive.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(package["url"], timeout=60) as response, archive.open("wb") as stream:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    stream.write(chunk)
        algorithm, expected = package["integrity"].split("-", 1)
        data = archive.read_bytes()
        assert base64.b64encode(hashlib.new(algorithm, data).digest()).decode() == expected
        target = LOCAL / "packages" / directory
        files = {}
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar.getmembers():
                parts = Path(member.name).parts
                assert parts[0] == "package" and not member.issym() and not member.islnk()
                output = (target / Path(*parts[1:])).resolve()
                assert output.is_relative_to(target.resolve())
                if member.isdir():
                    if args.acquire:
                        output.mkdir(parents=True, exist_ok=True)
                    continue
                assert member.isfile()
                payload = tar.extractfile(member).read()
                if not output.exists() and args.acquire:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(payload)
                assert output.read_bytes() == payload, "Installed asset changed: " + str(output)
                files[Path(*parts[1:]).as_posix()] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        installed = json.loads((target / "package.json").read_text(encoding="utf-8"))
        assert installed["name"] == name and installed["version"] == version
        result.append({**package, "archive_sha256": hashlib.sha256(data).hexdigest(),
                       "archive_bytes": len(data), "files": files})
    LOCAL.mkdir(parents=True, exist_ok=True)
    (LOCAL / "package-integrity.json").write_text(json.dumps({"status": "PASS", "packages": result}, indent=2) + "\n", encoding="utf-8")
    print("PACKAGE_INTEGRITY PASS; no model/browser downloads")


if __name__ == "__main__":
    main()
