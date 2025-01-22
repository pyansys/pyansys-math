# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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
.. _ref_pymath_eigen_solve:

Use PyAnsys Math to solve eigenproblems
---------------------------------------

This example uses a verification manual input file, but you can use
your own sparse or dense matrices.

"""
###############################################################################
# Perform required imports and start PyAnsys
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Perform required imports.

import time

from ansys.mapdl.core.examples import vmfiles
import matplotlib.pylab as plt
import numpy as np

import ansys.math.core.math as pymath

# Start PyAnsys Math as a service.
mm = pymath.AnsMath()

###############################################################################
# Get matrices
# ~~~~~~~~~~~~
# Run the input file from Verification Manual 153 and then
# get the stiff (``k``) and mass (``m``) matrices from the FULL file.

out = mm._mapdl.input(vmfiles["vm153"])
fullfile = mm._mapdl.jobname + ".full"
k = mm.stiff(fname=fullfile)
m = mm.mass(fname=fullfile)


###############################################################################
# Display size of the matrices
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display size of the ``k`` and ``m`` matrices.

print(m.shape)
print(k.shape)

###############################################################################
# Allocate an array to store eigenshapes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Allocate an array to store the eigenshapes, where ``nev``` is the number
# of eigenvalues requested,
#
nev = 10
a = mm.mat(k.nrow, nev)
a

###############################################################################
# Perform modal analysis
# ~~~~~~~~~~~~~~~~~~~~~~
# Perform the modal analysis.
#
# The algorithm is automatically chosen with respect to the properties
# of the matrices (such as scalar, storage, or symmetry).
#
print("Calling PyAnsys Math to solve the eigenproblem...")

t1 = time.time()
ev = mm.eigs(nev, k, m, phi=a)
print(f"Elapsed time to solve this problem: {time.time() - t1}")


###############################################################################
# Print eigenfrequencies
# ~~~~~~~~~~~~~~~~~~~~~~
# Print the vector of eigenfrequencies.

print(ev)

###############################################################################
# Verify the accuracy of eigenresults
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Check the residual error for the first eigenresult:
# :math:`R_1=||(K-\lambda_1.M).\phi_1||_2`
#
# First, compute :math:`\lambda_1 = \omega_1^2 = (2.\pi.f_1)^2`

# Eigenfrequency (Hz)
i = 0
f = ev[0]
omega = 2 * np.pi * f
lam = omega * omega


###############################################################################
# Then get the first eigenshape :math:`\phi_1` and compute both
# :math:`K.\phi_1` and :math:`M.\phi_1`.

# shape
phi = a[0]

# APDL command: *MULT,K,,Phi,,KPhi
kphi = k.dot(phi)

# APDL command: *MULT,M,,Phi,,MPhi
mphi = m.dot(phi)


######################################################################
# Next, compute the :math:`||K.\phi_1||_2` quantity and normalize the
# residual value.

# APDL command: *MULT,K,,Phi,,KPhi
kphi = k.dot(phi)


# APDL command: *NRM,KPhi,NRM2,KPhiNrm
kphinrm = kphi.norm()


###############################################################################
# Add these two vectors, using the :math:`\lambda_1` scalar
# factor, and compute the normalized residual value:
# :math:`\frac{R_1}{||K.\phi_1||_2}`

# APDL command: *AXPY,-lambda,,MPhi,1,,KPhi
mphi *= lam
kphi -= mphi

# Compute residual
res = kphi.norm() / kphinrm
print(res)

###############################################################################
# Compute this residual for all eigenmodes


def get_res(i):
    """Compute the residual for a given eigenmode."""
    # Eigenfrequency (Hz)
    f = ev[i]

    # omega = 2.pi.Frequency
    omega = 2 * np.pi * f

    # lambda = omega^2
    lam = omega * omega

    # i-th eigenshape
    phi = a[i]

    # K.Phi
    kphi = k.dot(phi)

    # M.Phi
    mphi = m.dot(phi)

    # Normalize scalar value
    kphinrm = kphi.norm()

    # (K-\lambda.M).Phi
    mphi *= lam
    kphi -= mphi

    # Return the residual
    return kphi.norm() / kphinrm


pymath_acc = np.zeros(nev)

for i in range(nev):
    f = ev[i]
    pymath_acc[i] = get_res(i)
    print(f"[{i}] : Freq = {f}\t - Residual = {pymath_acc[i]}")

###############################################################################
# Plot accuracy of eigenresults
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Plot tahe accuracy of the eigenresults.

fig = plt.figure(figsize=(12, 10))
ax = plt.axes()
x = np.linspace(1, nev, nev)
plt.title("PyAnsys Math Residual Error (%)")
plt.yscale("log")
plt.ylim([10e-13, 10e-7])
plt.xlabel("Frequency #")
plt.ylabel("Errors (%)")
ax.bar(x, pymath_acc, label="PyAnsys Math Results", color="orange")
plt.show()

###############################################################################
# Stop PyAnsys Math
# ~~~~~~~~~~~~~~~~~
# Stop PyAnsys Math.

mm._mapdl.exit()
