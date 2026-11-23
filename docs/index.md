# Get Started

Cleland Lab utils is a collection of functions for saving data, sweeping
parameters, analyzing signals, and fitting experimental data. No QuICK or QICK
dependency is required.

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

Functions are provided as-is. Their names and arguments follow the original
helpers from `quick.helper`. The grouped implementation modules are private;
`utils` is the public API.

See the [API reference](api.md) for function signatures, parameters, return
values, and examples.
