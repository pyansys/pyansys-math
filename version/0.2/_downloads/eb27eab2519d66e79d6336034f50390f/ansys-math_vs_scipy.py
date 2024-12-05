# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
.. _ref_ansys_math_vs_scipy:

Compute Eigenvalues using PyAnsys Math and SciPy
------------------------------------------------

This example shows how to perform these tasks:

- Extract the stiffness and mass matrices from an MAPDL model.
- Use PyAnsys Math to compute the first eigenvalues.
- Get these matrices using SciPy to obtain the same
  solutions using Python resources.
- See if PyAnsys Math is more accurate and faster than SciPy.
"""

###############################################################################
# Perform required imports and start PyAnsys Math
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Perform required imports.

import math
import time

from ansys.mapdl.core.examples import examples
import matplotlib.pylab as plt
import numpy as np
import scipy
from scipy.sparse.linalg import eigsh

import ansys.math.core.math as pymath

# Start PyAnsys Math as a service.
mm = pymath.AnsMath()

###############################################################################
# Load the input file
# ~~~~~~~~~~~~~~~~~~~
# Load the input file using MAPDL.

print(mm._mapdl.input(examples.wing_model))


###############################################################################
# Plot and mesh
# ~~~~~~~~~~~~~
# Plot and mesh using the ``eplot`` method.

mm._mapdl.eplot()


###############################################################################
# Set up modal analysis
# ~~~~~~~~~~~~~~~~~~~~~
# Set up a modal analysis and form the :math:`K` and :math:`M` matrices.
# MAPDL stores these matrices in a ``.FULL`` file.

print(mm._mapdl.slashsolu())
print(mm._mapdl.antype(antype="MODAL"))
print(mm._mapdl.modopt(method="LANB", nmode="10", freqb="1."))
print(mm._mapdl.wrfull(ldstep="1"))

# store the output of the solve command
output = mm._mapdl.solve()


###############################################################################
# Read sparse matrices
# ~~~~~~~~~~~~~~~~~~~~
# Read the sparse matrices using PyAnsys Math.

mm._mapdl.finish()
mm.free()
k = mm.stiff(fname="file.full")
M = mm.mass(fname="file.full")


###############################################################################
# Solve eigenproblem
# ~~~~~~~~~~~~~~~~~~
# Solve the eigenproblme using PyAnsys Math.
#
nev = 10
A = mm.mat(k.nrow, nev)

t1 = time.time()
ev = mm.eigs(nev, k, M, phi=A, fmin=1.0)
t2 = time.time()
pymath_elapsed_time = t2 - t1
print("\nElapsed time to solve this problem : ", pymath_elapsed_time)

###############################################################################
# Print eigenfrequencies and accuracy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Print the eigenfrequencies and the accuracy.
#
# Accuracy : :math:`\frac{||(K-\lambda.M).\phi||_2}{||K.\phi||_2}`
#
pymath_acc = np.empty(nev)

for i in range(nev):
    f = ev[i]  # Eigenfrequency (Hz)
    omega = 2 * np.pi * f  # omega = 2.pi.Frequency
    lam = omega**2  # lambda = omega^2

    phi = A[i]  # i-th eigenshape
    kphi = k.dot(phi)  # K.Phi
    mphi = M.dot(phi)  # M.Phi

    kphi_nrm = kphi.norm()  # Normalization scalar value

    mphi *= lam  # (K-\lambda.M).Phi
    kphi -= mphi

    pymath_acc[i] = kphi.norm() / kphi_nrm  # compute the residual
    print(f"[{i}] : Freq = {f:8.2f} Hz\t Residual = {pymath_acc[i]:.5}")


###############################################################################
# Use SciPy to solve the same eigenproblem
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Get the MAPDL sparse matrices into Python memory as SciPy
# matrices.

pk = k.asarray()
pm = M.asarray()

# get_ipython().run_line_magic('matplotlib', 'inline')

fig, (ax1, ax2) = plt.subplots(1, 2)
fig.suptitle("K and M Matrix profiles")
ax1.spy(pk, markersize=0.01)
ax1.set_title("K Matrix")
ax2.spy(pm, markersize=0.01)
ax2.set_title("M Matrix")
plt.show(block=True)


###############################################################################
# Make the sparse matrices for SciPy unsymmetric because symmetric matrices
# in SciPy are memory inefficient.
#
# :math:`K = K + K^T - diag(K)`
#
pkd = scipy.sparse.diags(pk.diagonal())
pK = pk + pk.transpose() - pkd
pmd = scipy.sparse.diags(pm.diagonal())
pm = pm + pm.transpose() - pmd


###############################################################################
# Plot the matrices.
#
fig, (ax1, ax2) = plt.subplots(1, 2)
fig.suptitle("K and M Matrix profiles")
ax1.spy(pk, markersize=0.01)
ax1.set_title("K Matrix")
ax2.spy(pm, markersize=0.01)
ax2.set_title("M Matrix")
plt.show(block=True)


###############################################################################
# Solve the eigenproblem.
#
t3 = time.time()
vals, vecs = eigsh(A=pK, M=pm, k=10, sigma=1, which="LA")
t4 = time.time()
scipy_elapsed_time = t4 - t3
print("\nElapsed time to solve this problem : ", scipy_elapsed_time)


###############################################################################
# Convert lambda values to frequency values:
# :math:`freq = \frac{\sqrt(\lambda)}{2.\pi}`
#
freqs = np.sqrt(vals) / (2 * math.pi)


###############################################################################
# Compute the residual error for SciPy.
#
# :math:`Err=\frac{||(K-\lambda.M).\phi||_2}{||K.\phi||_2}`
#
scipy_acc = np.zeros(nev)

for i in range(nev):
    lam = vals[i]  # i-th eigenvalue
    phi = vecs.T[i]  # i-th eigenshape

    kphi = pk * phi.T  # K.Phi
    mphi = pm * phi.T  # M.Phi

    kphi_nrm = np.linalg.norm(kphi, 2)  # Normalization scalar value

    mphi *= lam  # (K-\lambda.M).Phi
    kphi -= mphi

    scipy_acc[i] = 1 - np.linalg.norm(kphi, 2) / kphi_nrm  # compute the residual
    print(f"[{i}] : Freq = {freqs[i]:8.2f} Hz\t Residual = {scipy_acc[i]:.5}")


###############################################################################
# See if PyAnsys Math is more accurate than SciPy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot residual error to see if PyAnsys Math is more accurate than SciPy.

fig = plt.figure(figsize=(12, 10))
ax = plt.axes()
x = np.linspace(1, 10, 10)
plt.title("Residual Error")
plt.yscale("log")
plt.xlabel("Mode")
plt.ylabel("% Error")
ax.bar(x, scipy_acc, label="SciPy Results")
ax.bar(x, pymath_acc, label="PyAnsys Math Results")
plt.legend(loc="lower right")
plt.show()

###############################################################################
# See if PyAnsys Math is faster than SciPy
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot elapsed time to see if PyAnsys Math is more accurate than SciPy.

ratio = scipy_elapsed_time / pymath_elapsed_time
print(f"PyAnsys Math is {ratio:.3} times faster.")

###############################################################################
# Stop PyAnsys Math
# ~~~~~~~~~~~~~~~~~
# Stop PyAnsys Math.

mm._mapdl.exit()
