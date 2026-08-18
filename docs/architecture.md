# Architecture Notes: RPG / Game Simulation Projects (Umbrella)

## Pipeline

```text
Independent Sub-Projects, each with its own game loop and mechanics module
```

## Components

- 2D RPG prototype
- Hunger/thirst/stamina survival systems
- Roulette physics simulation
- Procedural game mechanics experiments

## Design Notes

- Keep provider/model choices swappable behind interfaces (see `multi-llm-router`
  and similar projects in this portfolio for the general pattern).
- Prefer configuration-driven pipelines (YAML/JSON in `configs/`) over hardcoded
  parameters so experiments are reproducible.
