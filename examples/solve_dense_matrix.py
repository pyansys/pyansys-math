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
Use PyAnsys Math to solve a dense matrix linear system
------------------------------------------------------
This example shows how to use PyAnsys Math to solve a dense matrix linear system.

"""
# Perform required imports and start PyAnsys
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Perform required imports.

import time

import matplotlib.pyplot as plt
import numpy.linalg as npl

import ansys.math.core.math as pymath

# Start PyAnsys Math as a server.
mm = pymath.AnsMath()

###############################################################################
# Allocate dense matrix
# ~~~~~~~~~~~~~~~~~~~~~
# Allocate a dense matrix in the MAPDL workspace.

mm._mapdl.clear()
dim = 1000
a = mm.rand(dim, dim)
b = mm.rand(dim)
x = mm.zeros(dim)

###############################################################################
# Copy matrices as NumPy arrays
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copy the matrices as NumPy arrays before they are modified by
# a factorization call.
#
a_py = a.asarray()
b_py = b.asarray()

###############################################################################
# Solve using PyAnsys Math
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Solve the dense matrix linear system using PyAnsys Math.
#
print(f"Solving a ({dim} x {dim}) dense linear system using PyAnsys Math...")

t1 = time.time()
s = mm.factorize(a)
x = s.solve(b, x)
t2 = time.time()
pymath_time = t2 - t1
print(f"Elapsed time to solve the linear system using PyAnsys Math: {pymath_time} seconds")

###############################################################################
# Get norm of solution
# ~~~~~~~~~~~~~~~~~~~~
# Get the norm of the PyAnsys Math solution.
mm.norm(x)


###############################################################################
# Solve using NumPy
# ~~~~~~~~~~~~~~~~~
# Solve the dense matrix linear system using NumPy.
#
print(f"Solving a ({dim} x {dim}) dense linear system using NumPy...")

t1 = time.time()
x_py = npl.solve(a_py, b_py)
t2 = time.time()
numpy_time = t2 - t1
print(f"Elapsed time to solve the linear system using NumPy: {numpy_time} seconds")

###############################################################################
# Plot elapsed times
# ~~~~~~~~~~~~~~~~~~~
# Plot the elapsed times for PyAnsys Math and Numpy to solve the dense
# matrix linear system.
#
max_time = max(pymath_time, numpy_time)
fig = plt.figure(figsize=(12, 10))
ax = plt.axes()
x = ["PyAnsys Math", "NumPy"]
y = [pymath_time, numpy_time]
plt.title("Elapsed time to solve the linear system")
plt.ylim([0, max_time + 0.2 * max_time])
plt.ylabel("Elapsed time (s)")
ax.bar(x, y, color="orange")
plt.show()

###############################################################################
# Get norm of solution
# ~~~~~~~~~~~~~~~~~~~~
# Get the norm of the NumPy solution.

npl.norm(x_py)

###############################################################################
# Stop PyAnsys Math
# ~~~~~~~~~~~~~~~~~
# Stop PyAnsys Math.

mm._mapdl.exit()
