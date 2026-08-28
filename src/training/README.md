# Training Module

This directory is reserved for project-owned AI-training code.

Future additions belong in the following areas:

- `environment/` — headless reset/step API, observations, rewards, and terminal states.
- `agents/` — trainable policies and adapters for benchmark opponents.
- `evaluation/` — match runners, metrics, and reproducible benchmarks.
- `config/` — versioned experiment templates.

The module must remain independent from `src/app/ui/` so that simulations can run headlessly.
