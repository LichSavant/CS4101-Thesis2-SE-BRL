"""Record the actual interpreter and parser modules; no emulated version claim."""
from pathlib import Path
import hashlib
import html.parser
import _markupbase
import platform
import sys
from importlib.metadata import version, PackageNotFoundError

def _version(name):
    try: return version(name)
    except PackageNotFoundError: return None

def execution_environment():
    return {"python_version": platform.python_version(), "sys_version": sys.version,
            "implementation": platform.python_implementation(), "executable": sys.executable,
            "native_execution": True, "parser_modules_replaced": False,
            "parser_modules": {m.__name__: {"path": m.__file__, "sha256": hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}
                               for m in (html.parser, _markupbase)},
            "dependency_versions": {name: _version(name) for name in ("pytest", "pydantic", "fastapi", "httpx", "sqlalchemy")}}


def runtime_source_hashes(root):
    root = Path(root)
    names = sorted({p.relative_to(root).as_posix() for folder in (root/"ml", root/"backend", root/"scripts")
                    for p in folder.rglob("*.py")})
    names += ["ml/research-inputs.v1.json", "ml/se_brl/codebook.v0.1.0.json", "ml/se_brl/semantic-model.v1.json",
              "experiments/vera_validation/V13_nli_hypotheses_v0.1.0.json"]
    return {n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
