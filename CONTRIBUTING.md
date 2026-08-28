# Contributing to TankTrouble AI Train

Thanks for contributing. This repository combines an attributed upstream game client with project-owned AI-training work, so changes should preserve that distinction.

## Before you start

1. Search existing issues before opening a new one.
2. Open an issue or discussion for substantial design changes before implementing them.
3. Read [NOTICE.md](NOTICE.md) to understand the upstream attribution requirements.

## Development guidelines

- Use C++17 and keep user-facing text and documentation in English.
- Keep pull requests focused and explain the problem, approach, and verification performed.
- Do not commit build outputs, generated training artefacts, credentials, datasets, or checkpoints.
- Put project-owned AI features behind clear interfaces; do not couple model training to the GTKmm view layer.
- Preserve copyright notices and do not remove upstream attribution.

## Validation

On Linux, initialize submodules and build before opening a pull request:

```bash
git submodule update --init --recursive
cmake -S . -B build
cmake --build build
```

The GitHub Actions workflow runs the same build on Ubuntu for pull requests and pushes to `main`.

## Pull requests

Use the pull-request template, link related issues, and describe any user-visible, protocol, or training-environment changes. Maintainers may ask for smaller commits, documentation updates, or tests before merging.
