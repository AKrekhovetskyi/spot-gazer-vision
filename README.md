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

## 🔩 Installation and launch

To run the vision service, execute the following commands in the Linux terminal:

```bash
git clone https://github.com/AKrekhovetskyi/spot-gazer-vision.git
cd spot-gazer-vision
```

Create an `.env` file from [`.env.sample`](./.env.sample) and set the necessary variables

```bash
mv .env.sample .env
```

Install dependencies:

```bash
poetry install
pre-commit install --install-hooks
```

Make sure the Django server of the [SpotGazer Backend](https://github.com/AKrekhovetskyi/spot-gazer-backend) service is up and running. Then run SpotGazer Vision:

```bash
poetry run python -m run_prediction
```

## 👨‍💻 Contribution

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
