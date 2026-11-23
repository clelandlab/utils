"""Internal gain conversion, signal estimation, and IQ analysis.

Copyright (c) 2024 Cleland Lab. Licensed under the MIT License; see LICENSE.
"""

import matplotlib.pyplot as plt
import numpy as np
from numpy import pi as π
from scipy import stats
from scipy.optimize import minimize

__all__ = ["dB2gain", "gain2dB", "symmetryCenter", "estimateOmega", "iq_scatter", "π"]


def dB2gain(dB, ref_gain=1, ref_dB=None):
    return ref_gain * 10 ** (dB / 20) if ref_dB is None else 10 ** ((dB + ref_dB) / 20)

def gain2dB(gain, ref_gain=1, ref_dB=None):
    return 20 * np.log10(gain / ref_gain) if ref_dB is None else 20 * np.log10(gain) - ref_dB


def symmetryCenter(x, y, it=3):
    L = len(y)
    R = int(L / 2)
    Δ = int(R / 2)
    freq = np.fft.rfftfreq(L*2)
    y = (y - np.mean(y)) / np.std(y)
    fft = np.fft.rfft(np.append(y, np.zeros(L)))
    res, d = 0, 0
    for _ in range(it): # dark magic: phase shift in Fourier space to align cross-correlation peak to the center iteratively
        fft *= np.exp(2j*π*d*freq)
        co = np.fft.irfft(fft**2)[R-1:L+R-1]
        i = np.argmax(co[R-Δ:R+Δ]) + R-Δ
        p = np.polynomial.polynomial.polyfit(np.arange(i-2, i+3), co[i-2:i+3], 2)
        d = -p[1]/4/p[2] - R/2
        res += d
    i = res + R - 0.5
    _i = int(i)
    return x[_i] + (x[_i+1] - x[_i]) * (i - _i)

def estimateOmega(x, y):
    y = (y - np.mean(y)) / np.std(y)
    rfft = np.fft.rfft(y)
    freq = np.fft.rfftfreq(len(y))
    return len(y) * freq[np.argmax(np.abs(rfft))] * 2 * π / (x[len(x) - 1] - x[0])

def iq_scatter(S0s, S1s, c0=None, c1=None, plot=True):
    if c0 is None:
        c0 = np.median(S0s.real) + 1j * np.median(S0s.imag)
    if c1 is None:
        c1 = np.median(S1s.real) + 1j * np.median(S1s.imag)
    def negative_visibility(_p):
        p = _p[0] + 1j * _p[1]
        angle = np.angle(c0 - p)
        S0 = (S0s - (p + c0) / 2.0) * np.exp(-1j * angle)
        S1 = (S1s - (p + c0) / 2.0) * np.exp(-1j * angle)
        prob0 = float(S0.real[S0.real < 0].size) / S0.size
        prob1 = float(S1.real[S1.real < 0].size) / S1.size
        return prob0 - prob1
    res = minimize(negative_visibility, [c1.real, c1.imag], method='Nelder-Mead') # optimize c1
    visibility = -1 * negative_visibility(res.x)
    c1 = res.x[0] + 1j * res.x[1]
    o = (c0 + c1) / 2.0 # origin
    g = o - c0 # project on opposite of g
    S0p = np.real((S0s - o) * np.conj(g)) / np.abs(g)
    S1p = np.real((S1s - o) * np.conj(g)) / np.abs(g)
    S0p_right, S1p_right = S0p[S0p < 0], S1p[S1p > 0]
    S0s_right, S0s_wrong = S0s[S0p < 0], S0s[S0p >= 0]
    S1s_right, S1s_wrong = S1s[S1p > 0], S1s[S1p <= 0]
    Fg, Fe = len(S0p_right) / len(S0p), len(S1p_right) / len(S1p)
    phase, threshold = float(-np.angle(c1 - c0, deg=True)), float(np.real((c1 + c0) / 2 * np.exp(-1j *  np.angle(c1 - c0))))
    if not plot:
        return phase, threshold, visibility, Fg, Fe, c0, c1, None
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.44)) # plot the histogram
    xp = np.linspace(np.min(S0p), np.max(S1p), 2001) # axis of projection
    g_hist, _ = np.histogram(S0p, bins=100, density=True, range=[xp[0], xp[-1]])
    e_hist, _ = np.histogram(S1p, bins=100, density=True, range=[xp[0], xp[-1]])
    g_cdf = np.cumsum(g_hist) * (xp[-1] - xp[0]) / 100
    e_cdf = np.cumsum(e_hist) * (xp[-1] - xp[0]) / 100
    axes[1].hist(S0p, color='blue', alpha=0.5, bins=100, density=True, range=[xp[0], xp[-1]], label=r'$|g\rangle$')
    axes[1].hist(S1p, color='red', alpha=0.5, bins=100, density=True, range=[xp[0], xp[-1]], label=r'$|e\rangle$')
    g_mu, g_std = stats.norm.fit(S0p_right)
    axes[1].plot(xp, stats.norm.pdf(xp, g_mu, g_std), color='blue', linestyle='dotted')
    e_mu, e_std = stats.norm.fit(S1p_right)
    axes[1].plot(xp, stats.norm.pdf(xp, e_mu, e_std), color='red', linestyle='dotted')
    axr = axes[1].twinx()
    axr.set_ylim([0, 1])
    axr.set_ylabel("Cumulative Probability")
    axr.plot(np.linspace(xp[0], xp[-1], 100), g_cdf, color='blue', linewidth=2)
    axr.plot(np.linspace(xp[0], xp[-1], 100), e_cdf, color='red', linewidth=2)
    axr.plot(np.linspace(xp[0], xp[-1], 100), g_cdf - e_cdf, color='green', linewidth=2)
    axes[1].set_xlabel('Projected IQ Amplitude (a.u.)')
    axes[1].set_ylabel('Probability Density')
    axes[1].legend(shadow=False, loc=1, frameon=True)
    axes[1].grid()
    axes[1].text(0.05, 0.95, 'Visibility=%.3f' % visibility, ha='left', transform=axes[1].transAxes)
    axes[1].text(0.05, 0.9, '$F_g$=%.3f' % Fg, ha='left', transform=axes[1].transAxes)
    axes[1].text(0.05, 0.85, '$F_e$=%.3f' % Fe, ha='left', transform=axes[1].transAxes)
    # scatter plot
    axes[0].scatter(S0s_right.real, S0s_right.imag, s=10, marker='o', zorder=0, alpha=0.5, c='blue', linewidths=0.0)
    axes[0].scatter(S1s_right.real, S1s_right.imag, s=10, marker='o', zorder=0, alpha=0.5, c='red', linewidths=0.0)
    axes[0].scatter(S0s_wrong.real, S0s_wrong.imag, s=10, marker='o', zorder=0, alpha=0.5, c='blue', linewidths=0.0)
    axes[0].scatter(S1s_wrong.real, S1s_wrong.imag, s=10, marker='o', zorder=0, alpha=0.5, c='red', linewidths=0.0)
    axes[0].grid()
    axes[0].set_xlabel('I (a.u.)')
    axes[0].set_ylabel('Q (a.u.)')
    _r = max(max(np.max(np.real(S0s - o)), np.max(np.real(S1s - o))), max(np.max(np.imag(S0s - o)), np.max(np.imag(S1s - o))))
    axes[0].set_xlim(-1.1 * _r + o.real, 1.1 * _r + o.real)
    axes[0].set_ylim(-1.1 * _r + o.imag, 1.1 * _r + o.imag)
    # plot the cut
    _x = np.linspace(-1.1 * _r + o.real, 1.1 * _r + o.real, 101)
    axes[0].plot(_x, -(c0.real - c1.real) / (c0.imag - c1.imag) * (_x - (c0.real + c1.real) / 2) + (c0.imag + c1.imag) / 2, 'k--')
    # add the circle to the IQ scatter plot
    theta = np.linspace(-π, π, 1001)
    I_g_fit_list = np.median(S0s_right.real) + np.cos(theta) * 3 * g_std
    Q_g_fit_list = np.median(S0s_right.imag) + np.sin(theta) * 3 * g_std
    I_e_fit_list = np.median(S1s_right.real) + np.cos(theta) * 3 * e_std
    Q_e_fit_list = np.median(S1s_right.imag) + np.sin(theta) * 3 * e_std
    axes[0].plot(I_g_fit_list, Q_g_fit_list, color='darkblue', linestyle='--', label=r'$|g\rangle$, $3\sigma$')
    axes[0].plot(I_e_fit_list, Q_e_fit_list, color='darkred', linestyle='--', label=r'$|e\rangle$, $3\sigma$')
    axes[0].legend(shadow=False, loc=1, frameon=True)
    return phase, threshold, visibility, Fg, Fe, c0, c1, fig
