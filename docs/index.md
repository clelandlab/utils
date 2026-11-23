# Get Started

[![Documentation](https://img.shields.io/readthedocs/clelandlab-utils?style=for-the-badge&logo=readthedocs&logoColor=white)](https://clelandlab-utils.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/clelandlab-utils?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/clelandlab-utils/)
[![GitHub stars](https://img.shields.io/github/stars/clelandlab/utils?style=for-the-badge&logo=github)](https://github.com/clelandlab/utils)

Cleland Lab utils is a collection of functions for saving data, sweeping
parameters, analyzing signals, and fitting experimental data.

## Installation

Requires Python 3.13 or newer (Python 3 only).

```shell
pip install clelandlab-utils
```

## Usage

Import functions and classes directly from `utils`:

```python
from utils import dB2gain, load_data, fitT1

gain = dB2gain(-20)
data = load_data("measurement.csv").T
parameters, errors, r_squared, figure = fitT1(data[0], data[1])
```

See the [API reference](api.md) for function signatures, parameters, return
values, and examples.
