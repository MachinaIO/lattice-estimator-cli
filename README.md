# lattice-estimator-cli: CLI for Lattice Estimator

This CLI is for calling [lattice estimator](https://github.com/malb/lattice-estimator). It estimates the security parameter from ROP for the given parameters.

## Usage

```bash
python -m lattice_cli <ring_dim> <q> \
  --s-dist '{"name": "DiscreteGaussianAlpha", "alpha": 0.001, "q": 12289}' \
  --e-dist '{"name": "CenteredBinomial", "eta": 3}' \
  [--m <int>] [--exact]
```

- `<ring_dim>`: ring dimension (n)
- `<q>`: modulus q
- `--s-dist`: JSON spec for the secret noise distribution
- `--e-dist`: JSON spec for the error noise distribution
- `--m`: optional number of samples; if omitted, infinity is used
- `--exact`: use exact estimation; by default, a rough estimate is used
  (The CLI automatically uses the bundled `estimator/` submodule in this repo.)

### Distribution specs

Provide a JSON object with at least a `name` field. Supported types and fields:

- `DiscreteGaussian`: `{ "stddev": float, "mean"?: float, "n"?: int }`
- `DiscreteGaussianAlpha`: `{ "alpha": float, "q"?: int, "mean"?: float, "n"?: int }`
- `CenteredBinomial`: `{ "eta": int, "n"?: int }`
- `Uniform`: `{ "a": int, "b": int, "n"?: int }`
- `UniformMod`: `{ "q": int, "n"?: int }`
- `SparseTernary`: `{ "p": int, "m": int, "n"?: int }`
- `SparseBinary`: `{ "hw": int, "n"?: int }`
- `Binary`: `{}` (alias of `Uniform(0,1)`)`
- `Ternary`: `{}` (alias of `Uniform(-1,1)`)`

Notes:
- For `DiscreteGaussianAlpha` and `UniformMod`, if `q` is omitted in the spec,
  the top-level `<q>` argument is used.

### Examples

```bash
# Rough estimate (default)
python -m lattice_cli 1024 12289 \
  --s-dist '{"name": "DiscreteGaussianAlpha", "alpha": 0.001}' \
  --e-dist '{"name": "CenteredBinomial", "eta": 3}'

# Exact estimate with explicit m
python -m lattice_cli 1024 12289 \
  --s-dist '{"name": "Binary"}' \
  --e-dist '{"name": "DiscreteGaussian", "stddev": 3.2}' \
  --m 100000 --exact
```

## Run From Anywhere

Use the provided wrapper so the local `estimator/` submodule is found and Sage's
Python is used:

```bash
# From the repository root
./scripts/lattice-estimator-cli 1024 12289 --s-dist '{"name":"CenteredBinomial","eta":3}' --e-dist '{"name":"Ternary"}'

# Or put it on PATH
export PATH="$PWD/scripts:$PATH"
lattice-estimator-cli 1024 12289 --s-dist '{"name":"CenteredBinomial","eta":3}' --e-dist '{"name":"Ternary"}'
```

The wrapper sets `PYTHONPATH` to the repository root and executes
`sage -python -m lattice_cli ...`.

## Call From Rust (example)

```rust
use std::process::Command;

fn main() {
    let output = Command::new("/absolute/path/to/repo/scripts/lattice-estimator-cli")
        .args([
            "1024",
            "12289",
            "--s-dist",
            "{\"name\":\"CenteredBinomial\",\"eta\":3}",
            "--e-dist",
            "{\"name\":\"Ternary\"}",
        ])
        .output()
        .expect("failed to execute process");

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        println!("secpar = {}", stdout.trim());
    } else {
        eprintln!("stderr: {}", String::from_utf8_lossy(&output.stderr));
    }
}
```

## Repository layout

The CLI lives under the `lattice_cli/` package and can be invoked with
`python -m lattice_cli`.

- `lattice_cli/cli.py`: Main CLI implementation (argparse‑based)
- `lattice_cli/__main__.py`: Bootstraps `python -m lattice_cli`
- `lattice_cli/__init__.py`: Package metadata (version, etc.)
- `lattice_cli/core.py`: The `estimate_rop_secpar` implementation

## Notes on dependencies

The CLI automatically adds the local `estimator/` submodule (at repo root) to
`sys.path`. Some `estimator` modules depend on Sage (`sage`); ensure Sage and
other dependencies are installed in your environment.
