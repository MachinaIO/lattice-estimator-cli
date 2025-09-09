import argparse
import json
import os
import sys
from typing import Any, List, Mapping, Optional
from .core import estimate_rop_secpar
from . import __version__


def parse_json(value: str, default: Any) -> Any:
    """Parse a JSON string safely, falling back to a default on empty input."""
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {exc}") from exc


def _build_noise_dist(spec: Mapping[str, Any], default_q: Optional[int] = None):
    """Build a NoiseDistribution object from a simple JSON spec.

    The spec must include a "name" field identifying the distribution type and
    any required parameters for that type. Supported types:
      - DiscreteGaussian: {"stddev": float, "mean"?: float, "n"?: int}
      - DiscreteGaussianAlpha: {"alpha": float, "q"?: int, "mean"?: float, "n"?: int}
      - CenteredBinomial: {"eta": int, "n"?: int}
      - Uniform: {"a": int, "b": int, "n"?: int}
      - UniformMod: {"q": int, "n"?: int}
      - SparseTernary: {"p": int, "m": int, "n"?: int}
      - SparseBinary: {"hw": int, "n"?: int}
      - Binary: {}
      - Ternary: {}
    """
    try:
        from estimator.estimator import nd as ND
    except Exception as exc:  # pragma: no cover - environment-specific
        raise SystemExit(
            "Failed to import estimator's noise distributions. "
            "Ensure dependencies (e.g., Sage) are installed and importable. "
            f"Underlying error: {exc}"
        ) from exc

    if not isinstance(spec, dict):
        raise SystemExit("Distribution spec must be a JSON object.")
    if "name" not in spec:
        raise SystemExit("Distribution spec requires a 'name' field.")

    name = str(spec["name"]).strip()
    lname = name.lower()

    if lname in {"discretegaussian", "dg", "gaussian"}:
        stddev = spec.get("stddev")
        if stddev is None:
            raise SystemExit("DiscreteGaussian requires 'stddev'.")
        mean = spec.get("mean", 0)
        n = spec.get("n", None)
        return ND.DiscreteGaussian(stddev, mean=mean, n=n)

    if lname in {"discretegaussianalpha", "dg_alpha", "dga"}:
        alpha = spec.get("alpha")
        if alpha is None:
            raise SystemExit("DiscreteGaussianAlpha requires 'alpha'.")
        q = spec.get("q", default_q)
        if q is None:
            raise SystemExit(
                "DiscreteGaussianAlpha requires 'q' (or provide top-level q)."
            )
        mean = spec.get("mean", 0)
        n = spec.get("n", None)
        return ND.DiscreteGaussianAlpha(alpha, q, mean=mean, n=n)

    if lname in {"centeredbinomial", "cb", "binomial"}:
        eta = spec.get("eta")
        if eta is None:
            raise SystemExit("CenteredBinomial requires 'eta'.")
        n = spec.get("n", None)
        return ND.CenteredBinomial(eta, n=n)

    if lname in {"uniform"}:
        a = spec.get("a")
        b = spec.get("b")
        if a is None or b is None:
            raise SystemExit("Uniform requires 'a' and 'b'.")
        n = spec.get("n", None)
        return ND.Uniform(a, b, n=n)

    if lname in {"uniformmod", "uniform_mod", "umod"}:
        q = spec.get("q", default_q)
        if q is None:
            raise SystemExit("UniformMod requires 'q' (or provide top-level q).")
        n = spec.get("n", None)
        return ND.UniformMod(q, n=n)

    if lname in {"sparseternary", "ternary_sparse", "st"}:
        p = spec.get("p")
        m = spec.get("m")
        if p is None or m is None:
            raise SystemExit("SparseTernary requires 'p' and 'm'.")
        n = spec.get("n", None)
        return ND.SparseTernary(p, m, n)

    if lname in {"sparsebinary", "binary_sparse", "sb"}:
        hw = spec.get("hw")
        if hw is None:
            raise SystemExit("SparseBinary requires 'hw'.")
        n = spec.get("n", None)
        return ND.SparseBinary(hw, n)

    if lname in {"binary"}:
        return ND.Binary
    if lname in {"ternary"}:
        return ND.Ternary

    raise SystemExit(f"Unknown distribution type: {name}")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for estimate_rop_secpar."""
    parser = argparse.ArgumentParser(
        prog="lattice-estimator-cli",
        description=(
            "Estimate security parameter from ROP for given LWE-like parameters.\n"
            "Calls lattice_cli.core.estimate_rop_secpar. Uses the bundled 'estimator' submodule."
        ),
    )

    # Positional core parameters
    parser.add_argument("ring_dim", type=int, help="Ring dimension (n).")
    parser.add_argument("q", type=int, help="Modulus q.")

    # Noise distributions as JSON specs
    parser.add_argument(
        "--s-dist",
        required=True,
        help=(
            'JSON spec for secret distribution. Example: \'{"name": "DiscreteGaussianAlpha", '
            '"alpha": 0.001, "q": 12289}\''
        ),
    )
    parser.add_argument(
        "--e-dist",
        required=True,
        help=(
            'JSON spec for error distribution. Example: \'{"name": "CenteredBinomial", "eta": 3}\''
        ),
    )

    # Optional overrides
    parser.add_argument(
        "--m",
        type=int,
        default=None,
        help="Number of samples m (omit to use function default).",
    )
    parser.add_argument(
        "--exact",
        action="store_true",
        help="Use exact estimation (by default, rough estimation is used).",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"lattice-estimator-cli {__version__}",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    """CLI entrypoint specialized for estimate_rop_secpar."""
    parser = build_parser()
    ns = parser.parse_args(argv)

    # Always use the local 'estimator' submodule next to this package.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    estimator_dir = os.path.join(repo_root, "estimator")
    if not os.path.isdir(estimator_dir):
        print(
            f"Bundled 'estimator' directory not found at {estimator_dir}",
            file=sys.stderr,
        )
        return 1
    # Put repository root on sys.path so imports like 'estimator.estimator.nd' resolve.
    sys.path.insert(0, repo_root)

    # Build noise distributions from JSON specs.
    s_spec = parse_json(ns.s_dist, default=None)
    e_spec = parse_json(ns.e_dist, default=None)
    if not isinstance(s_spec, dict):
        raise SystemExit("--s-dist must be a JSON object.")
    if not isinstance(e_spec, dict):
        raise SystemExit("--e-dist must be a JSON object.")

    s_dist = _build_noise_dist(s_spec, default_q=ns.q)
    e_dist = _build_noise_dist(e_spec, default_q=ns.q)

    try:
        if ns.m is None:
            # Use function defaults for m and is_rough.
            result = estimate_rop_secpar(
                ns.ring_dim, ns.q, s_dist, e_dist, is_rough=not ns.exact
            )
        else:
            result = estimate_rop_secpar(
                ns.ring_dim, ns.q, s_dist, e_dist, ns.m, is_rough=not ns.exact
            )
    except Exception as exc:  # noqa: BLE001
        print(f"Error while estimating: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
