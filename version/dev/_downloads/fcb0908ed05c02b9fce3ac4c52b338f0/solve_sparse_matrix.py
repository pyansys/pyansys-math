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
Perform sparse factorization and solve operations
-------------------------------------------------

Using PyAnsys Math, you can solve linear systems of equations
based on sparse or dense matrices.

"""
# Perform required imports and start PyAnsys
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Perform required imports.

from ansys.mapdl.core.examples import vmfiles
import matplotlib.pyplot as plt

import ansys.math.core.math as pymath

# Start PyAnsys Math as a server.
mm = pymath.AnsMath()

###############################################################################
# Factorize and solve sparse linear systems
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Run a MAPDL solve to create a Full file. This code
# uses a model from the official verification manual.
#
# After a solve command, the ``FULL`` file contains the assembled stiffness
# matrix, mass matrix, and load vector.
#
out = mm._mapdl.input(vmfiles["vm152"])

###############################################################################
# List files in current directory
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# List the files in current directory.
#
mm._mapdl.list_files()

###############################################################################
# Extract stiffness matrix
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Extract the stiffness matrix from the FULL file in a sparse
# matrix format. For help on the ``stiff`` function, use the
# ``help(mm.stiff)`` command.
#
# Print dimensions of sparse matrix
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Print the dimensions of the sparse matrix.

fullfile = mm._mapdl.jobname + ".full"
k = mm.stiff(fname=fullfile, name="K")
k

################################################################################
# Copy AnsMath sparse matrix to SciPy CSR matrix and plot
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copy the AnsMath sparse matrix to a SciPy CSR matrix. Then, plot the
# graph of the sparse matrix.

pk = k.asarray()
plt.spy(pk, color="orange", markersize=3)
plt.title("AnsMath sparse matrix")
plt.show()

###############################################################################
# Get a copy of sparse matrix as a NumPy array
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Get a copy of the ``k`` sparse matrix as a NumPy array

ky = k.asarray()
ky

###############################################################################
# Extract load vector from FULL file and print norm
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Extract the load vector from the FULL file and print the norm of this
# vector.
b = mm.rhs(fname=fullfile, name="B")
b.norm()

###############################################################################
# Get a copy of load vector as a NumPy array
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Get a copy of the load vector as a NumPy array.

by = b.asarray()

###############################################################################
# Factorize stiffness matrix
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Factorize the stiffness matrix using PyAnsys Math.
#
s = mm.factorize(k)

###############################################################################
# Solve linear system
# ~~~~~~~~~~~~~~~~~~~
# Solve the linear system.

x = s.solve(b)

###############################################################################
# Print norm** of solution vector
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Print the norm of the solution vector.

x.norm()

###############################################################################
# Check accuracy of solution
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Check the accuracy of the solution by verifying that
# :math:`KX - B = 0`.

kx = k.dot(x)
kx -= b
print("Residual error:", kx.norm() / b.norm())

###############################################################################
# Get a summary of allocated objects
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Get a summary of all allocated AnsMath objects.

mm.status()

######################################################################
# Delete all AnsMath objects
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
# Delete all AnsMath objects.

mm.free()

###############################################################################
# Stop PyAnsys Math
# ~~~~~~~~~~~~~~~~~
# Stop PyAnsys Math.

mm._mapdl.exit()
