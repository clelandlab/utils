# API reference

Import public helpers directly from `utils`:

```python
from utils import Saver, Sweep, fitT1
```

Use NumPy arrays for numerical analysis and fitting inputs.

## print_yaml

```python
print_yaml(data)
```

Print a Python object as YAML using `yaml.dump`.

**Parameters**

- `data` (`object`): object to serialize. NumPy arrays become sequences and
  NumPy scalars become Python scalars.

**Returns**

- `None`.

## load_yaml

```python
load_yaml(path)
```

Read a YAML file with `yaml.safe_load`.

**Parameters**

- `path` (`str` or path-like): path to an existing YAML file.

**Returns**

- `data` (`object`): decoded dictionary, list, scalar, or other YAML value;
  `None` for an empty file.

## save_yaml

```python
save_yaml(path, data)
```

Serialize a Python object with `yaml.dump`, overwriting an existing file.

**Parameters**

- `path` (`str` or path-like): destination YAML file. Its directory must exist.
- `data` (`object`): object to serialize, with the same NumPy array and scalar
  support as `print_yaml`.

**Returns**

- `content` (`str`): YAML text written to the file.

## load_data

```python
load_data(*paths)
```

Read CSV files with `numpy.genfromtxt` and concatenate their arrays along the
first axis.

**Parameters**

- `*paths` (`str` or path-like): one or more CSV file paths. For tables with
  multiple rows and columns, column counts must match.

**Returns**

- `data` (`numpy.ndarray`): concatenated data; ordinary two-dimensional tables
  are joined by rows.

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

## Saver

```python
Saver(title, path, indep_params=[], dep_params=[], params={})
```

Create a numbered CSV file and a companion YAML metadata file.

**Parameters**

- `title` (`str`): label used in filenames and metadata.
- `path` (`str`): existing output directory. The directory is not created.
- `indep_params` (sequence of `(str, str)` pairs, default `[]`): independent
  variable names and units, in column order.
- `dep_params` (sequence of `(str, str)` pairs, default `[]`): dependent variable
  names and units, in column order after the independent variables.
- `params` (`dict`, default `{}`): additional metadata.

**Returns**

- `saver` (`Saver`): data saver. Its `file_name` attribute is the full filename
  without an extension.

Construction immediately writes both files. Names have the form
`00000 - Title.csv` and `00000 - Title.yml`; numbering advances past existing
files matching that pattern.

## Saver.write_data

```python
saver.write_data(data)
```

Append numeric rows to the CSV file using `numpy.savetxt`, with a comma delimiter
and `%.9e` formatting. This method does not update the YAML metadata.

**Parameters**

- `data` (two-dimensional numeric array-like): rows to append. Columns follow
  the independent parameters, then dependent parameters, in their declared units.

**Returns**

- `None`.

## Saver.write_yml

```python
saver.write_yml()
```

Overwrite the YAML metadata with creation time, completion time, title, parameter
labels, and `params`. Completion is recorded as the current time after any call
to `write_data`, or `"N/A"` before data is written.

**Parameters**

- None.

**Returns**

- `None`.

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

## Sweep

```python
Sweep(config, sweepConfig, random=False, progressBar=True)
```

Iterate over combinations of parameter values in a nested configuration.

**Parameters**

- `config` (`dict`): template dictionary, deep-copied at construction.
- `sweepConfig` (`dict`): matching nested structure containing sweep values.
  Non-string iterables with a length provide values; scalars and strings are constants.
- `random` (`bool`, default `False`): use pseudo-random order. Each instance keeps
  one seed, so repeated iteration over that instance uses the same order.
- `progressBar` (`bool`, default `True`): display a tqdm progress bar.

**Returns**

- `sweep` (`Sweep`): iterable that yields a configuration dictionary for each
  parameter combination.

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

## feistel_network

```python
feistel_network(i, N, seed)
```

Generate a repeatable pseudo-random permutation of a range.

**Parameters**

- `i` (`int`): input position, reduced modulo `N`.
- `N` (`int`): positive range size.
- `seed` (`int`): seed defining the permutation for that range size.

**Returns**

- `index` (`int`): permuted index in `range(N)`.

## nested_get

```python
nested_get(d, key)
```

Follow a sequence of keys through a nested dictionary. Missing keys raise the
underlying dictionary error.

**Parameters**

- `d` (`dict`): dictionary to traverse.
- `key` (sequence): keys to follow in order; an empty sequence returns `d` itself.

**Returns**

- `value` (`object`): value reached after following all keys.

For example, `nested_get({"a": {"b": 3}}, ["a", "b"])` returns `3`.

## dB2gain

```python
dB2gain(dB, ref_gain=1, ref_dB=None)
```

Convert decibels to amplitude gain.

**Parameters**

- `dB` (`float` or `numpy.ndarray`): input level in decibels.
- `ref_gain` (`float`, default `1`): amplitude gain corresponding to zero input dB.
- `ref_dB` (`float` or `None`, default `None`): additive reference offset in dB;
  when supplied, overrides `ref_gain`.

**Returns**

- `gain` (scalar or `numpy.ndarray`): `ref_gain * 10 ** (dB / 20)`, or
  `10 ** ((dB + ref_dB) / 20)` when `ref_dB` is supplied.

## gain2dB

```python
gain2dB(gain, ref_gain=1, ref_dB=None)
```

Convert positive amplitude gain to decibels.

**Parameters**

- `gain` (`float` or `numpy.ndarray`): positive amplitude gain values.
- `ref_gain` (`float`, default `1`): positive reference amplitude gain.
- `ref_dB` (`float` or `None`, default `None`): reference offset in dB to subtract;
  when supplied, overrides `ref_gain`.

**Returns**

- `dB` (scalar or `numpy.ndarray`): `20 * numpy.log10(gain / ref_gain)`, or
  `20 * numpy.log10(gain) - ref_dB` when `ref_dB` is supplied.

## π

```python
from utils import π
```

The constant `numpy.pi`, also used by the fitting helpers.

## estimateOmega

```python
estimateOmega(x, y)
```

Estimate angular frequency from the largest FFT component, useful as an initial
guess for `fitT2`.

**Parameters**

- `x` (`numpy.ndarray`, shape `(n,)`): evenly spaced independent-variable values.
- `y` (`numpy.ndarray`, shape `(n,)`): nonconstant signal sampled at `x`.

**Returns**

- `omega` (`float`): estimated angular frequency in radians per unit of `x`.

## symmetryCenter

```python
symmetryCenter(x, y, it=3)
```

Estimate a signal's symmetry center using iterative Fourier correlation.

**Parameters**

- `x` (`numpy.ndarray`, shape `(n,)`): independent-variable values; equal spacing
  is preferred.
- `y` (`numpy.ndarray`, shape `(n,)`): nonconstant signal sampled at `x`.
- `it` (`int`, default `3`): number of refinement iterations.

**Returns**

- `center` (`float`): interpolated symmetry-center position in the units of `x`;
  it need not be an existing sample position.

## iq_scatter

```python
iq_scatter(S0s, S1s, c0=None, c1=None, plot=True)
```

Analyze separation between two sets of complex IQ samples.

**Parameters**

- `S0s` (`numpy.ndarray`, shape `(n0,)`, complex): IQ samples for state 0.
- `S1s` (`numpy.ndarray`, shape `(n1,)`, complex): IQ samples for state 1, in the
  same amplitude units as `S0s`.
- `c0` (`complex` or `None`, default `None`): fixed state-0 center; defaults to
  the component-wise medians of `S0s`.
- `c1` (`complex` or `None`, default `None`): initial state-1 center; defaults to
  the component-wise medians of `S1s`. It is optimized for visibility even when supplied.
- `plot` (`bool`, default `True`): create IQ scatter and projected histogram plots.

**Returns**

Tuple `(phase, threshold, visibility, Fg, Fe, c0, c1, fig)`:

- `phase` (`float`): rotation angle in degrees aligning separation with the real axis.
- `threshold` (`float`): real-axis decision threshold after rotation, in input amplitude units.
- `visibility` (`float`): optimized difference in projected state probabilities.
- `Fg` (`float`): fraction of state-0 samples correctly classified.
- `Fe` (`float`): fraction of state-1 samples correctly classified.
- `c0` (`complex`): state-0 center used for classification.
- `c1` (`complex`): optimized state-1 center used for classification.
- `fig` (`matplotlib.figure.Figure` or `None`): plots, or `None` when `plot=False`.

## fitT1

```python
fitT1(T, S, plot=True)
```

Fit `S0 * exp(-T / T1) + C` to a decay signal.

**Parameters**

- `T` (`numpy.ndarray`, shape `(n,)`): delay values. Plot annotations assume microseconds.
- `S` (`numpy.ndarray`, shape `(n,)`): signal or population sampled at `T`.
- `plot` (`bool`, default `True`): create a plot of data and fitted decay.

**Returns**

Tuple `(p, perr, r2, fig)`:

- `p` (`numpy.ndarray`, shape `(3,)`): fitted `[S0, T1, C]`; `T1` uses the units of `T`.
- `perr` (`numpy.ndarray`, shape `(3,)`): estimated parameter standard errors, in the same order and units.
- `r2` (`float`): coefficient of determination, not multiplied by 100.
- `fig` (`matplotlib.figure.Figure` or `None`): fit plot, or `None` when `plot=False`.

```python
import numpy as np
from utils import fitT1

T = np.linspace(0, 10, 101)
S = 0.8 * np.exp(-T / 2.0) + 0.1
p, perr, r2, fig = fitT1(T, S, plot=False)
```

## fitT2

```python
fitT2(T, S, omega=2*π, T2=20.0, plot=True)
```

Fit `S0 * exp(-T / T2) * cos(omega * T) + C` to a damped oscillation.

**Parameters**

- `T` (`numpy.ndarray`, shape `(n,)`): delay values. Plot annotations assume microseconds.
- `S` (`numpy.ndarray`, shape `(n,)`): signal or population sampled at `T`.
- `omega` (`float`, default `2*π`): initial angular-frequency guess, in radians per unit of `T`.
- `T2` (`float`, default `20.0`): initial decay-time guess, in the units of `T`.
- `plot` (`bool`, default `True`): create plots of the data, fitted signal, and exponential envelope.

**Returns**

Tuple `(p, perr, r2, fig)`:

- `p` (`numpy.ndarray`, shape `(4,)`): fitted `[S0, T2, omega, C]`, using the units above.
- `perr` (`numpy.ndarray`, shape `(4,)`): estimated parameter standard errors, in the same order and units.
- `r2` (`float`): coefficient of determination, not multiplied by 100.
- `fig` (`matplotlib.figure.Figure` or `None`): fit plot, or `None` when `plot=False`.

## fitResonator

```python
fitResonator(F, S, fit="circle", p0=[None, None, None, None], plot=True,
             normalize_background=True, normalize_phase=True)
```

Fit a resonator transmission response. Data is sorted by frequency before fitting.

**Parameters**

- `F` (`numpy.ndarray`, shape `(n,)`): frequencies. Plots label them in MHz.
- `S` (`numpy.ndarray`, shape `(n,)`, complex): transmission samples at `F`.
- `fit` (`str`, default `"circle"`): `"circle"` fits complex inverse transmission;
  `"amp"` fits magnitude in decibels; `"arg"` fits phase.
- `p0` (sequence of length 4, default `[None, None, None, None]`): initial guesses
  `[Qi, Qc, fr, phi]`. Each `None` is replaced by `100000`, `10000`, the frequency
  of minimum normalized magnitude, or `0.0`, respectively. `fr` uses the units
  of `F`; `phi` is in radians.
- `plot` (`bool`, default `True`): create plots of inverse transmission, magnitude, and phase.
- `normalize_background` (`bool`, default `True`): remove a linear magnitude
  background in decibels using the first and last four points.
- `normalize_phase` (`bool`, default `True`): remove a linear unwrapped phase
  background using the first and last four points.

**Returns**

Tuple `(p, perr, r2, fig)`:

- `p` (`list`, length 4): `[Qi, Qc, fr, phi]`, comprising internal quality factor,
  coupling quality factor, resonance frequency, and phase. Quality factors are
  made positive; frequency uses the units of `F` and phase is in radians.
- `perr` (`list`, length 4): estimated parameter errors, in the same order and units.
- `r2` (`float`): coefficient of determination from complex inverse-transmission
  residuals for every fit mode, not multiplied by 100.
- `fig` (`matplotlib.figure.Figure` or `None`): fit plots, or `None` when `plot=False`.

## evalStr

```python
evalStr(s, var, _var=None)
```

Evaluate a string as a Python f-string. Expressions inside braces execute as
Python code, so use trusted templates.

**Parameters**

- `s` (`str`): f-string template containing expressions in braces.
- `var` (`dict`): local variables available to those expressions.
- `_var` (`dict` or `None`, default `None`): global variables passed to `eval`;
  `None` uses the helper module's globals.

**Returns**

- `text` (`str`): evaluated string.

```python
from utils import evalStr

text = evalStr("{value} + 1 = {value + 1}", {"value": 3})
```

## safe_wrap

```python
safe_wrap(retry=2, timeout=300)
```

Decorate a function with retries and a per-call timeout using `func_timeout`.

**Parameters**

- `retry` (`int`, default `2`): nonnegative number of additional attempts after
  an exception; the default allows three attempts in total.
- `timeout` (`float`, default `300`): time limit in seconds for each call.

**Returns**

- `decorator` (callable): wraps a function with the retry and timeout behavior,
  forwarding its arguments and returning its successful result.

The wrapper re-raises the final exception derived from `Exception`.
`func_timeout` timeout exceptions derive from `BaseException` and propagate
immediately without being retried.

```python
from utils import safe_wrap

@safe_wrap(retry=2, timeout=10)
def add(a, b):
    return a + b

result = add(2, 3)
```
