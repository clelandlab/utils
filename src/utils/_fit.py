"""Internal T1, T2, and resonator fitting and plotting.

Copyright (c) 2024 Cleland Lab. Licensed under the MIT License; see LICENSE.
"""

import matplotlib.pyplot as plt
import numpy as np
from numpy import pi as π
from scipy.optimize import curve_fit, leastsq

__all__ = ["fitT1", "fitT2", "fitResonator"]


# T1 fit and plot
def fitT1(T, S, plot=True):
    def m(x, *p):
        return p[0] * np.exp(-x / p[1]) + p[2]
    def jac(x, *p):
        d0 = np.exp(-x / p[1])
        d1 = p[0] * x / p[1] ** 2 * np.exp(-x / p[1])
        d2 = np.ones(len(x))
        return np.transpose([d0, d1, d2])
    p0 = [1.0, 1.0, 1.0]
    p, pcov = curve_fit(m, T, S, p0=p0, jac=jac)
    perr = np.sqrt(np.diag(pcov))  # Standard deviation of parameters
    residuals = S - m(T, *p)
    r2 = 1 - np.sum(residuals**2) / np.sum((S - np.mean(S))**2)
    if not plot:
        return p, perr, r2, None
    dof = len(T) - len(p)
    fig, ax = plt.subplots()
    ax.scatter(T, S, color='black', s=10, label='Original Data')
    ax.plot(T, m(T, *p), color='red', label='Fit')
    annotation_text = (
        r"$S = S_0e^{-\tau/T_1} + C$" + "\n" +
        "Fitting Result:\n" +
        r"$S_0 = ({:.2f} \pm {:.2f})$".format(p[0], perr[0]) + "\n" +
        r"$T_1 = ({:.2f} \pm {:.2f})$ us".format(p[1], perr[1]) + "\n" +
        r"$C = ({:.2f} \pm {:.2f})$".format(p[2], perr[2]) + "\n" +
        r"$n = {}$ (DOF)".format(dof) + "\n" +
        r"$R^2 = {:.3f}$%".format(r2*100)
    )
    ax.set_xlabel(r"Pulse Delay $\tau$ (us)")
    ax.set_ylabel("Population")
    ax.set_title("T1 Measurement")
    ax.grid()
    ax.legend()
    mid_index = len(T) // 2
    ax.annotate(annotation_text, (T[mid_index], S[mid_index]), fontsize=8, xycoords='data', textcoords='offset points', xytext=(20, 20))
    return p, perr, r2, fig

# T2 fit and plot
def fitT2(T, S, omega=2*π, T2=20.0, plot=True):
    def m(x, *p):
        return p[0] * np.exp(-x / p[1]) * np.cos(p[2] * x) + p[3]
    def jac(x, *p):
        d0 = np.exp(-x / p[1]) * np.cos(p[2] * x)
        d1 = p[0] * x / p[1] ** 2 * np.exp(-x / p[1]) * np.cos(p[2] * x)
        d2 = - x * p[0] * np.exp(-x / p[1]) * np.sin(p[2] * x)
        d3 = np.ones(len(x))
        return np.transpose([d0, d1, d2, d3])
    def me(x, *p):
        return p[0] * np.exp(-x / p[1]) + p[3]
    p0 = [0.4, T2, omega, 0.5]
    p, pcov = curve_fit(m, T, S, p0=p0, jac=jac)
    perr = np.sqrt(np.diag(pcov))  # Standard deviation of parameters
    residuals = S - m(T, *p)
    r2 = 1 - np.sum(residuals**2) / np.sum((S - np.mean(S))**2)
    if not plot:
        return p, perr, r2, None
    dof = len(T) - len(p)
    fig, ax = plt.subplots()
    ax.scatter(T, S, color='black', s=10, label='Original Data')
    ax.plot(T, m(T, *p), color='red', label='Fit')
    ax.plot(T, me(T, *p), color='blue', label='Fit Exponential')
    annotation_text = (
        r"$S = S_0e^{-\tau/T_2}\cos(\omega\tau) + C$" + "\n" +
        "Fitting Result:\n" +
        r"$S_0 = ({:.2f} \pm {:.2f})$, $C = ({:.2f} \pm {:.2f})$".format(p[0], perr[0], p[3], perr[3]) + "\n" +
        r"$T_2 = ({:.2f} \pm {:.2f})$ us".format(p[1], perr[1]) + "\n" +
        r"$\omega = ({:.2f} \pm {:.2f})$ rad/us".format(p[2], perr[2]) + "\n" +
        r"$n = {}$ (DOF), $R^2 = {:.3f}$%".format(dof, r2 * 100)
    )
    ax.set_xlabel(r"Pulse Delay $\tau$ (us)")
    ax.set_ylabel("Population")
    ax.set_title("T2 Measurement")
    ax.grid()
    ax.legend(loc="lower right")
    mid_index = len(T) // 2
    ax.annotate(annotation_text, (T[mid_index], me(T[mid_index], *p)), fontsize=8, xycoords='data', textcoords='offset points', xytext=(10, 10))
    return p, perr, r2, fig

def fitResonator(F, S, fit="circle", p0=[None, None, None, None], plot=True, normalize_background=True, normalize_phase=True):
    def dB(a):
        return 20. * np.log10(np.abs(a))
    def S21_th(f, *p):
        Qi, Qc, fr, phi = p
        return 1 / (1 + Qi / Qc * np.exp(1j * phi) / (1 + 2j * Qi * (f - fr) / fr))
    def normalize(F, S):
        n = 4
        s = F.argsort()
        F, S = F[s], S[s]
        logmag = dB(S)
        if normalize_background:
            magoffset = np.mean(np.concatenate((logmag[:n], logmag[-n:])))
            logmag = logmag - magoffset
            fit_logmag_background = np.polyfit(np.concatenate((F[:n], F[-n:])), np.concatenate((logmag[:n], logmag[-n:])), 1)
            logmag_background_line = np.poly1d(fit_logmag_background)
            logmag = logmag - logmag_background_line(F)
        phase = np.unwrap(np.angle(S))
        if normalize_phase:
            fitphase = np.polyfit(np.concatenate((F[:n], F[-n:])), np.concatenate((phase[:n], phase[-n:])), 1)
            phaseline = np.poly1d(fitphase)
            phase = phase - phaseline(F)
        S = 10**(logmag/20.)*np.exp(1j*phase)
        return F, S
    F, S = normalize(F, S)
    S_inv, S_dB = 1 / S, dB(S)
    _p0 = [100000, 10000, F[np.argmin(S_dB)], 0.0]
    p0 = list(p0)
    for i in range(len(p0)):
        if p0[i] is None:
            p0[i] = _p0[i]
    bounds = ([-np.inf, -np.inf, 0, -2*π], [np.inf, np.inf, np.inf, 2*π])
    def p_b2i(p):
        _p = []
        for i in range(len(p)):
            if bounds[0][i] == -np.inf:
                _p.append(p[i])
                continue
            if bounds[1][i] == np.inf:
                _p.append(np.sqrt((p[i] - bounds[0][i] + 1) ** 2 - 1))
                continue
            _p.append(np.arcsin(2 * (p[i] - bounds[0][i]) / (bounds[1][i] - bounds[0][i]) - 1))
        return _p
    def p_i2b(_p):
        p = []
        for i in range(len(_p)):
            if bounds[0][i] == -np.inf:
                p.append(_p[i])
                continue
            if bounds[1][i] == np.inf:
                p.append(bounds[0][i] - 1 + np.sqrt(_p[i] ** 2 + 1))
                continue
            p.append(bounds[0][i] + (np.sin(_p[i]) + 1) * (bounds[1][i] - bounds[0][i]) / 2)
        return p
    def err_i2b(_p, _perr):
        perr = []
        for i in range(len(_p)):
            if bounds[1][i] == np.inf:
                perr.append(np.abs(_p[i] / np.sqrt(_p[i]**2 + 1)) * _perr[i])
            else:
                perr.append(np.abs(np.cos(_p[i]) * (bounds[1][i] - bounds[0][i]) / 2) * _perr[i])
        return perr
    def S21_circle_fit_err(_p):
        y = 1 / S21_th(F, *p_i2b(_p))
        return np.concatenate((np.real(S_inv - y), np.imag(S_inv - y)))
    def S21_amp_fit_err(_p):
        return dB(S21_th(F, *p_i2b(_p))) - S_dB
    def S21_arg_fit_err(_p):
        return np.angle(S / S21_th(F, *p_i2b(_p)))
    fun = { "circle": S21_circle_fit_err, "amp": S21_amp_fit_err, "arg": S21_arg_fit_err }
    result, cov, _, _, _ = leastsq(fun[fit], p_b2i(p0), maxfev=50000, xtol=1.e-7, ftol=1.e-7, col_deriv=False, gtol=1.e-7, full_output=True)
    p = p_i2b(result)
    perr = err_i2b(result, np.sqrt(np.diag(cov*np.var(fun[fit](p)))))
    S21_fit = S21_th(F, *p)
    residuals = 1/S - 1/S21_fit
    residuals = np.concatenate((np.real(residuals), np.imag(residuals)))
    flat_S_inv = np.concatenate((np.real(S_inv), np.imag(S_inv)))
    r2 = 1 - np.sum(residuals**2) / np.sum((flat_S_inv - np.mean(flat_S_inv))**2)
    p[0], p[1] = abs(p[0]), abs(p[1])
    if not plot:
        return p, perr, r2, None
    dof = len(residuals) - len(p)
    fig = plt.figure(figsize=(12, 6), tight_layout=True)
    axes = [fig.add_subplot(121), fig.add_subplot(222), fig.add_subplot(224)]
    axes[0].scatter((1 / S).real, (1 / S).imag, label="raw", alpha=0.5, linewidths=0.0)
    axes[0].plot((1 / S21_fit).real, (1 / S21_fit).imag, "r-", label="fit")
    axes[0].set_xlabel(r"Re $\widetilde{S}_{21}^{-1}$")
    axes[0].set_ylabel(r"Im $\widetilde{S}_{21}^{-1}$")
    axes[0].grid()
    axes[1].scatter(F, S_dB, alpha=0.5, linewidths=0.0)
    axes[1].plot(F, dB(S21_fit), "r-")
    axes[1].set_ylabel(r"$|S_{21}|$(dB)")
    axes[1].text(0.025, 0.21, r"$Q_i = %.3e$" % p[0] + "\n" + r"        $\pm %.1e$" % perr[0], ha="left", va="bottom", transform=axes[1].transAxes)
    axes[1].text(0.025, 0.05, r"$Q_c = %.3e$" % p[1] + "\n" + r"        $\pm %.1e$" % perr[1], ha="left", va="bottom", transform=axes[1].transAxes)
    axes[1].text(0.7, 0.05, r"$f = %.7e$" % p[2], ha="left", va="bottom", transform=axes[1].transAxes)
    axes[1].grid()
    mean_phase_data, mean_phase_fit = np.mean(np.unwrap(np.angle(S))), np.mean(np.unwrap(np.angle(S21_fit)))
    match = int((mean_phase_fit - mean_phase_data) / (2 * π) + 0.5)
    axes[2].sharex(axes[1])
    axes[2].scatter(F, np.unwrap(np.angle(S)), alpha=0.5, linewidths=0.0)
    axes[2].plot(F, np.unwrap(np.angle(S21_fit)) - match * 2 * π, 'r-')
    axes[2].text(0.025, 0.95, r"n = {} (DOF)".format(dof), ha="left", va="top", transform=axes[2].transAxes)
    axes[2].text(0.025, 0.87, r"$R^2 = {:.3f}$%".format(r2 * 100), ha="left", va="top", transform=axes[2].transAxes)
    axes[2].set_xlim(F[0], F[-1])
    axes[2].set_xlabel(r"Frequency (MHz)")
    axes[2].set_ylabel(r"$arg~S_{21}$")
    axes[2].grid()
    return p, perr, r2, fig
