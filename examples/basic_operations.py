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
.. _ref_pyansys-math_basic:

PyAnsys Math basic operations
-----------------------------

This tutorial shows how you can use PyAnsys Math for basic
operations on AnsMath vectors and matrices in the APDL memory
workspace.

"""
###############################################################################
# Perform required imports and start PyAnsys
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Perform required imports.

import matplotlib.pyplot as plt
import numpy as np

import ansys.math.core.math as pymath

# Start PyAnsys Math as a service.
mm = pymath.AnsMath()

###############################################################################
# Create and manipulate vectors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Create two AnsMath vectors of size 5. The :math:`\vec{v}` method is initialized with
# ones, and the :math:`\vec{w}` is filled with random values.
#

v = mm.ones(2)
w = mm.rand(2)
print(v)
print(w)

###############################################################################
# Plot vectors
# ~~~~~~~~~~~~
# Plot the created vectors.

origin = np.array([[0, 0], [0, 0]])
plt.title("Vectors V and W")
plt.quiver(*origin, v, w, angles="xy", scale_units="xy", scale=1, color=["orange", "gray"])
plt.xlim(-1.5, 1.5)
plt.ylim(-1.5, 1.5)
plt.show()


###############################################################################
# Use operators on vectors
# ~~~~~~~~~~~~~~~~~~~~~~~~
# Like NumPy vectors, AnsMath vectors can use most of the
# standard operators, such as ``+``, ``-``, ``+=``, ``-=``,
# and ``*=``.
#
# Here this form is used: :math:`\vec{z}=\vec{v}+\vec{w}`
#
# Compute :math:`\|z\|_2`. (The default norm is nrm2. Note that you
# can use ``.norm('nrm1')`` or ``.norm('nrminf')`` for different normals.
# For more information, see `help(z.norm)`.
#

z = v + w
z.norm()


###############################################################################
# Methods
# ~~~~~~~
# Alternatively you can use methods, following the NumPy
# standards. Available methods are:
#
# - ``mm.add()``
# - ``mm.subtract()``
# - ``mm.dot()``
#
# Equivalent operator for addition:
# ``z = v + w``

z = mm.add(v, w)
z.norm()

###############################################################################
# Equivalent operator for subtraction:
# ``z = v - w``

z = mm.subtract(v, w)
print(z)

###############################################################################
# Equivalent dot operation for the product of two vectors:
#

vw = mm.dot(v, w)
print("Dot product :", str(vw))


###############################################################################
# Perform in-place operations (without copying vectors)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Perform in-place addition.

v += v
print(v)


###############################################################################
# Perform in-place multiplication.

v *= 2
print(v)

###############################################################################
# Perform another in-place multiplication.

v /= 2.0
print(v)


###############################################################################
# Working with dense matrices
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Allocate two dense matrices with random values.

m1 = mm.rand(4, 5)
m2 = mm.ones(4, 5)
m1, m2

###############################################################################
# Add these 2 dense matrices and then scale the result matrix.

m3 = m1 + m2
print(m3)

m3 *= 2
print(m3)

###############################################################################
# Transpose a matrix.

m4 = m3.T
print(m4)


###############################################################################
# As for vectors, methods are available as an alternative to operators.

m3 = mm.add(m1, m2)
print(m3)


###############################################################################
# Compute a matrix vector multiplication.

mw = m3.dot(m4)
print(mw)

###############################################################################
# AnsMath matrices can be identified by printing, viewing their types, or
# using the ``__repr__`` method by simply typing out the variable.
#
# Here is an example with an AnsMath matrix.
#

type(m1)
print(m1)
m1

###############################################################################
# Here is an example with an AnsMath vector.
#

type(w)
print(w)
w

###############################################################################
# Use NumPy methods on AnsMath objects
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Regardless of the underlying AnsMath object type, you are generally
# able to perform most NumPy or SciPy operations on these arrays. You
# can do this in one of two ways.
#
# You can convert a matrix to a NumPy array.

apdl_mat = mm.rand(5, 5)
np_mat = apdl_mat.asarray()
print(np_mat)


###############################################################################
# Alternatively, you can use NumPy to compute the maximum of the array.
#
# This works because PyAnsys Math copies over the matrix to the local
# Python memory and then computes the maximum using NumPy.

print(np.max(apdl_mat))


###############################################################################
# While this works for most NumPy operations, keep in mind that
# operations supported within PyAnsys Math (such as adding or
# multiplying arrays) compute much faster because the data is not copied.

apdl_arr = mm.rand(5, 5)
np_array = apdl_mat.asarray()
print(np.allclose(apdl_mat, np_array))

###############################################################################
# Stop PyAnsys Math
# ~~~~~~~~~~~~~~~~~
# Stop PyAnsys Math.

mm._mapdl.exit()
