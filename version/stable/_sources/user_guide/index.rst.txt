.. _ref_user_guide:

User guide
==========

Overview
--------

You can use the ``AnsMath()`` method to launch an instance of PyAnsys Math.

.. code:: python3

    import ansys.math.core.math as pymath

    # Start PyAnsys Math.
    mm = pymath.AnsMath()
    print(mm)

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

    APDLMATH PARAMETER STATUS-  (      0 PARAMETERS DEFINED)

   Name                   Type            Mem. (MB)       Dims            Workspace

.. toctree::
   :hidden:
   :maxdepth: 1

   arrays.rst