# API reference

Import public helpers directly from `utils`:

```python
from utils import Saver, Sweep, fitT1
```

Use NumPy arrays for numerical analysis and fitting inputs. Unless stated
otherwise, functions retain the signatures and calculations from `quick.helper`.

## YAML and CSV data

### print_yaml

```python
print_yaml(data)
```

Print `data` as YAML using `yaml.dump`. Returns `None`.
NumPy arrays are serialized as sequences and NumPy scalars as Python scalars.

### load_yaml

```python
load_yaml(path)
```

Read a YAML file at `path` with `yaml.safe_load`. Returns the decoded Python
object, such as a dictionary, list, or scalar; an empty file returns `None`.

### save_yaml

```python
save_yaml(path, data)
```

Serialize `data` with `yaml.dump` and write it to `path`, overwriting an existing
file. Returns the YAML text. The containing directory must already exist.
NumPy arrays and scalars use the same serialization as `print_yaml`.

### load_data

```python
load_data(*paths)
```

Read one or more CSV files with `numpy.genfromtxt` and concatenate their arrays
along the first axis. Returns a NumPy array. For ordinary tables with multiple
rows and columns, this joins the rows; column counts must match.

NumPy's input shape is preserved: single-row or single-column files can produce
one-dimensional arrays. This function does not force a two-dimensional result.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from utils import load_data, load_yaml, save_yaml

with TemporaryDirectory() as directory:
    path = Path(directory)
    save_yaml(path / "config.yml", {"frequency": [100, 200]})
    config = load_yaml(path / "config.yml")
    np.savetxt(path / "data.csv", [[1, 2], [3, 4]], delimiter=",")
    data = load_data(path / "data.csv")
```

### Saver

```python
Saver(title, path, indep_params=[], dep_params=[], params={})
```

Create a numbered CSV file and a companion YAML metadata file.

- `title`: label used in the filenames and metadata.
- `path`: string naming an existing output directory. The directory is not created.
- `indep_params`, `dep_params`: sequences of `(name, unit)` pairs, in column order.
- `params`: dictionary of additional metadata.

Construction immediately writes both files. Names have the form
`00000 - Title.csv` and `00000 - Title.yml`; numbering advances past existing
files matching that pattern. The instance's `file_name` attribute contains the
full filename without an extension.

#### Saver.write_data

```python
saver.write_data(data)
```

Append numeric rows to the CSV file using `numpy.savetxt`, with a comma delimiter
and `%.9e` formatting. Supply a two-dimensional array or sequence of rows whose
columns follow the independent parameters, then dependent parameters.
Returns `None`. This method does not update the YAML metadata.

#### Saver.write_yml

```python
saver.write_yml()
```

Overwrite the YAML metadata with creation time, completion time, title, parameter
labels, and `params`. Completion is recorded as the current time after any call
to `write_data`, or `"N/A"` before data is written. Returns `None`.

```python
from tempfile import TemporaryDirectory
from utils import Saver

with TemporaryDirectory() as directory:
    saver = Saver(
        "Measurement", directory,
        indep_params=[("Time", "us")],
        dep_params=[("Amplitude", "")],
        params={"sample": "A"},
    )
    saver.write_data([[0, 1.0], [1, 0.8]])
    saver.write_yml()
```

## Parameter sweeps

### Sweep

```python
Sweep(config, sweepConfig, random=False, progressBar=True)
```

Iterate over combinations of parameter values in a nested configuration.

- `config`: template dictionary, deep-copied at construction.
- `sweepConfig`: dictionary with matching nested structure. Non-string iterables
  with a length provide sweep values; scalar values and strings are constants.
- `random`: use a pseudo-random order when `True`. Each instance keeps one seed,
  so repeated iteration over that instance uses the same order.
- `progressBar`: display a tqdm progress bar when `True`.

Nested parent dictionaries must already exist in `config`, and sweep sequences
must be nonempty. With no swept parameters, the configured dictionary is yielded
once. Otherwise, every combination is yielded, with the last listed swept
parameter changing fastest when `random=False`.

The original template is preserved, but each iteration mutates and returns the
**same copied dictionary**. Deep-copy each result if retaining snapshots.

```python
from copy import deepcopy
from utils import Sweep

config = {"frequency": 0, "pulse": {"amplitude": 0}}
values = {"frequency": [100, 200], "pulse": {"amplitude": [0.1, 0.2]}}
steps = [deepcopy(step) for step in Sweep(config, values, progressBar=False)]
```

### feistel_network

```python
feistel_network(i, N, seed)
```

Return the pseudo-randomly permuted index for position `i` in a range of size
`N`. Use integer inputs with `N > 0`. The result is in `range(N)`; the same
`N` and `seed` define a repeatable permutation. Input `i` is reduced modulo `N`.

### nested_get

```python
nested_get(d, key)
```

Follow the sequence of keys in `key` through `d` and return the final value.
For example, `nested_get({"a": {"b": 3}}, ["a", "b"])` returns `3`.
An empty key sequence returns `d` itself. Missing keys raise the underlying
dictionary error.

## Gain and signal analysis

### dB2gain

```python
dB2gain(dB, ref_gain=1, ref_dB=None)
```

Convert decibels to amplitude gain. Returns
`ref_gain * 10 ** (dB / 20)` by default. If `ref_dB` is supplied, `ref_gain` is
ignored and the result is `10 ** ((dB + ref_dB) / 20)`.
Accepts a scalar or NumPy array.

### gain2dB

```python
gain2dB(gain, ref_gain=1, ref_dB=None)
```

Convert positive amplitude gain to decibels. Returns
`20 * numpy.log10(gain / ref_gain)` by default. If `ref_dB` is supplied,
`ref_gain` is ignored and the result is `20 * numpy.log10(gain) - ref_dB`.
Accepts a scalar or NumPy array.

### symmetryCenter

```python
symmetryCenter(x, y, it=3)
```

Estimate a signal's symmetry center using iterative Fourier correlation.
`x` and `y` are equal-length one-dimensional NumPy arrays; equally spaced `x`
values are preferred. `it` controls the iteration count. Returns an interpolated
position in the units of `x`, which need not be an existing sample position.

### estimateOmega

```python
estimateOmega(x, y)
```

Estimate angular frequency from the largest FFT component. Supply equal-length
one-dimensional NumPy arrays with evenly spaced `x` and nonconstant `y`.
Returns angular frequency in radians per unit of `x`.

### iq_scatter

```python
iq_scatter(S0s, S1s, c0=None, c1=None, plot=True)
```

Analyze separation between two sets of complex IQ samples. `S0s` and `S1s` are
one-dimensional complex NumPy arrays. `c0` and `c1` are optional complex centers;
omitted centers start at the component-wise medians. `c1` is then optimized for
visibility, including when an initial `c1` is supplied.

Returns `(phase, threshold, visibility, Fg, Fe, c0, c1, fig)`:

- `phase`: rotation angle in degrees aligning the separation with the real axis.
- `threshold`: real-axis decision threshold after that rotation.
- `visibility`: optimized difference in the projected state probabilities.
- `Fg`, `Fe`: fractions correctly classified for the two sample sets.
- `c0`, `c1`: centers used for the classification.
- `fig`: Matplotlib figure with IQ scatter and projected histograms, or `None`
  when `plot=False`.

### π

```python
from utils import π
```

The constant `numpy.pi`, also used by the signal and fitting helpers.

## Curve fitting

All fitting functions return `(p, perr, r2, fig)`: fitted parameters, estimated
parameter errors, the coefficient of determination, and a Matplotlib figure.
`r2` is a fraction, not a percentage. `plot=False` returns `None` for `fig`.

### fitT1

```python
fitT1(T, S, plot=True)
```

Fit `S0 * exp(-T / T1) + C` to equal-length one-dimensional NumPy arrays `T`
(delay) and `S` (signal). Parameters and errors are ordered `[S0, T1, C]`.
`T1` has the same units as `T`; plot annotations assume microseconds.

```python
import numpy as np
from utils import fitT1

T = np.linspace(0, 10, 101)
S = 0.8 * np.exp(-T / 2.0) + 0.1
p, perr, r2, fig = fitT1(T, S, plot=False)
```

### fitT2

```python
fitT2(T, S, omega=2*π, T2=20.0, plot=True)
```

Fit `S0 * exp(-T / T2) * cos(omega * T) + C` to one-dimensional NumPy arrays.
`omega` and `T2` are initial guesses. Parameters and errors are ordered
`[S0, T2, omega, C]`. Use consistent delay and angular-frequency units;
plot annotations assume microseconds and radians per microsecond.

### fitResonator

```python
fitResonator(F, S, fit="circle", p0=[None, None, None, None], plot=True,
             normalize_background=True, normalize_phase=True)
```

Fit a resonator response from one-dimensional NumPy arrays `F` (frequency) and
`S` (complex transmission). Data is sorted by frequency before fitting.

- `fit`: `"circle"` fits complex inverse transmission; `"amp"` fits magnitude in
  decibels; `"arg"` fits phase.
- `p0`: four initial guesses in order `[Qi, Qc, fr, phi]`. Each `None` entry is
  replaced with its default: `100000`, `10000`, the frequency of minimum
  normalized magnitude, or `0.0`, respectively.
- `normalize_background`: remove a linear magnitude background in decibels using
  the first and last four points.
- `normalize_phase`: remove a linear unwrapped phase background using those points.

Parameters and errors are ordered `[Qi, Qc, fr, phi]`: internal quality factor,
coupling quality factor, resonance frequency, and phase in radians. Returned
quality factors are made positive. `fr` uses the units of `F`; plots label
frequency in MHz. `r2` is computed from complex inverse-transmission residuals
for every fit mode.

## Expression evaluation and retries

### evalStr

```python
evalStr(s, var, _var=None)
```

Evaluate `s` as a Python f-string, using `var` for locals and `_var` for globals.
Returns the resulting string. Expressions inside braces execute as Python code,
so use trusted templates. For example:

```python
from utils import evalStr

text = evalStr("{value} + 1 = {value + 1}", {"value": 3})
```

### safe_wrap

```python
safe_wrap(retry=2, timeout=300)
```

Return a decorator that calls a function through `func_timeout`. `retry` is the
number of additional attempts after an exception, so the default allows three
attempts. `timeout` is the time limit in seconds for each call.

The wrapper returns the function's successful result or re-raises the final
exception derived from `Exception`. `func_timeout` timeout exceptions derive
from `BaseException` and propagate immediately without being retried.

```python
from utils import safe_wrap

@safe_wrap(retry=2, timeout=10)
def add(a, b):
    return a + b

result = add(2, 3)
```
