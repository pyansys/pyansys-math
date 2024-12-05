
PyAnsys Math documentation
==========================

Introduction
------------

PyAnsys Math aims to gather all mathematical calculation tools present
in Ansys software.

This Python library allows you to access and manipulate large sparse matrices
and solve a variety of eigenproblems. It is presented in a similar manner to
the popular `NumPy <numpy_docs_>`_ and `SciPy <scipy_docs_>`_ libraries.

The command set for PyAnsys Math is based on tools for manipulating large mathematical
matrices and vectors that provide access to standard linear algebra operations and the
powerful sparse linear solvers of Ansys Mechanical APDL (MAPDL), providing the ability
to solve eigenproblems.

Python and MATLAB eigensolvers are based on the publicly available
LAPACK libraries and provide reasonable solve times for eigenproblems
with relatively small degrees of freedom (DOF), perhaps 100,000.
However, Ansys solvers are designed for the scale of hundreds of
millions of DOF, providing a variety of situations where you can
directly leverage Ansys high-performance solvers on a variety of
eigenproblems. Fortunately, you can leverage this without relearning
an entirely new language because PyAnsys Math is written in a similar manner
as the NumPy and SciPy libraries. For example, here is a comparison between
the NumPy and SciPy linear algebra solvers and the PyAnsys Math solver:

.. table:: NumPy and SciPy versus PyAnsys Math implementations

   +--------------------------------------------+-----------------------------------+
   | NumPy and SciPy                            | PyAnsys Math                      |
   +============================================+===================================+
   | .. code:: python3                          | .. code:: python3                 |
   |                                            |                                   |
   |   k_py = k + sparse.triu(k, 1).T           |   k = mm.matrix(k_py, triu=True)  |
   |   m_py = m + sparse.triu(m, 1).T           |   m = mm.matrix(m_py, triu=True)  |
   |   n = 10                                   |   n = 10                          |
   |   ev = linalg.eigsh(k_py, k=neqv, M=m_py)  |   ev = mm.eigs(n, k, m)           |
   |                                            |                                   |
   +--------------------------------------------+-----------------------------------+


Background
----------

PyAnsys Math uses the MAPDL solver in the background. It is based on the
``launch_mapdl()`` method from PyMAPDL's `ansys-mapdl-core <pymapdl_github_>`_
package.

Because PyMAPDL is `gRPC <grpc_>`_-based, the MAPDL solver can function as
a server, ready to respond to connecting clients. With gRPC establishing
secure connections, a client app can directly call methods on a potentially
remote MAPDL instance as if it were a local object. The use of HTTP/2 makes
gRPC friendly to modern internet infrastructures. This, along with the use
of binary transmission formats, favors higher performance.


Quick code
----------

Here is a brief example of how you use PyAnsys Math:

.. code:: python3

    import ansys.math.core.math as pymath

    mm = pymath.AnsMath()

    u = mm.ones(5)
    v = mm.rand(5)
    w = u + v

    print(w)

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

      UDWZKD :
      Size : 5
      1.417e+00   1.997e+00   1.720e+00   1.933e+00   1.000e+00      <       5


For comprehensive PyAnsys Math examples, see :ref:`ref_pymath_examples`.


.. toctree::
   :hidden:
   :maxdepth: 1

   getting_started/index
   user_guide/index
   api/index
   examples/index
   contributing/index
   changelog
