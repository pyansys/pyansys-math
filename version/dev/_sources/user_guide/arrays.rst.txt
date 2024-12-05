
Handling arrays between PyAnsys Math and Python
===============================================


Sending arrays to PyAnsys Math
------------------------------

.. code:: python3

    import numpy as np
    import ansys.math.core.math as pymath

    # Start PyAnsys Math as a service.
    mm = pymath.AnsMath()

    a = np.random.random((2, 3))
    a_pymath = mm.matrix(a, name="A")

    print(a_pymath)

.. rst-class:: sphx-glr-script-out

 .. code-block:: none

    A: 
    [1,1]: 4.018e-01 [1,2]: 4.635e-01 [1,3]: 3.682e-01
    [2,1]: 9.711e-01 [2,2]: 7.601e-02 [2,3]: 8.833e-01



Transfer a PyAnsys Math matrix to NumPy
---------------------------------------

.. code:: python3

    a_python = a_pymath.asarray()
    print((a == a_python).all())


.. rst-class:: sphx-glr-script-out

 .. code-block:: none

    True

    


    
