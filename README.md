# SpotGazer Vision

Computer vision service of the parking lot occupancy recognition system.
The repository is a part of a multi-service [SpotGather](https://github.com/AKrekhovetskyi/spot-gazer) system.

## 🛠️ Prerequisites

To successfully setup and run the vision kernel, your system must meet the following requirements:

- Linux OS (tested on Debian-based distributions)
- Python 3.12 or higher
- [`poetry`](https://python-poetry.org/) and the [`poetry-dotenv-plugin`](https://github.com/pivoshenko/poetry-plugin-dotenv)

```bash
poetry self add poetry-dotenv-plugin
```

## Contribution

Make sure to install `pre-commit` and its hooks before making any commits:

```bash
pre-commit install --install-hooks
```

Run the tests with the following command:

```bash
poetry run pytest tests -vv -s -rA
```

Sometimes it might be necessary to add the `./src` folder to the Python path so that to run the tests:

```bash
export PYTHONPATH=${PYTHONPATH}:$(pwd)/src
```
