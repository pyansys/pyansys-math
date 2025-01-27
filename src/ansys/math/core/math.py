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

"""Contains the Math classes, allowing for math operations within
PyAnsys Math from Python."""
from enum import Enum
import os
import string
from warnings import warn

from ansys.api.mapdl.v0 import ansys_kernel_pb2 as anskernel
from ansys.api.mapdl.v0 import mapdl_pb2 as pb_types
from ansys.mapdl.core import VERSION_MAP, launch_mapdl
from ansys.mapdl.core.common_grpc import (
    ANSYS_VALUE_TYPE,
    DEFAULT_CHUNKSIZE,
    DEFAULT_FILE_CHUNK_SIZE,
)
from ansys.mapdl.core.errors import (
    ANSYSDataTypeError,
    MapdlRuntimeError,
    VersionError,
    protect_grpc,
)
from ansys.mapdl.core.misc import load_file
from ansys.mapdl.core.parameters import interp_star_status
from ansys.tools.versioning import requires_version
from ansys.tools.versioning.utils import server_meets_version
import numpy as np

MYCTYPE = {
    np.int32: "I",
    np.int64: "L",
    np.single: "F",
    np.double: "D",
    np.complex64: "C",
    np.complex128: "Z",
}


NP_VALUE_TYPE = {value: key for key, value in ANSYS_VALUE_TYPE.items()}

# for windows LONG vs INT32
if os.name == "nt":
    NP_VALUE_TYPE[np.intc] = 1


def id_generator(size=6, chars=string.ascii_uppercase):
    """Generate a random string"""
    import secrets

    return "".join(secrets.choice(chars) for _ in range(size))


class ObjType(Enum):
    """Provides the generic AnsMath object (a shared features between AnsMath
    objects and AnsSolver components)."""

    GEN = 1
    VEC = 2
    DMAT = 3
    SMAT = 4


def get_nparray_chunks(name, array, chunk_size=DEFAULT_FILE_CHUNK_SIZE):
    """Serializes a NumPy array into chunks."""
    stype = NP_VALUE_TYPE[array.dtype.type]
    arr_sz = array.size
    i = 0  # position counter
    byte_array = array.tobytes()
    while i < len(byte_array):
        piece = byte_array[i : i + chunk_size]
        chunk = anskernel.Chunk(payload=piece, size=len(piece))
        yield pb_types.SetVecDataRequest(vname=name, stype=stype, size=arr_sz, chunk=chunk)
        i += chunk_size


def get_nparray_chunks_mat(name, array, chunk_size=DEFAULT_FILE_CHUNK_SIZE):
    """Serializes a 2D NumPy array into chunks.

    It uses the ``SetMatDataRequest`` method.

    """
    stype = NP_VALUE_TYPE[array.dtype.type]
    sh1 = array.shape[0]
    sh2 = array.shape[1]
    i = 0  # position counter
    byte_array = array.tobytes(order="F")
    while i < len(byte_array):
        piece = byte_array[i : i + chunk_size]
        chunk = anskernel.Chunk(payload=piece, size=len(piece))
        yield pb_types.SetMatDataRequest(mname=name, stype=stype, nrow=sh1, ncol=sh2, chunk=chunk)
        i += chunk_size


def list_allowed_dtypes():
    """Return a list of human-readable AnsMath supported data types."""
    dtypes = list(NP_VALUE_TYPE.keys())
    if None in dtypes:
        dtypes.remove(None)
    return "\n".join([f"{dtype}" for dtype in dtypes])


class AnsMath:
    """Provides the common class for abstract math objects.

    Examples
    --------
    Create an instance.

    >>> import ansys.math.core.math as pymath
    >>> mm = pymath.AnsMath()

    Add vectors.

    >>> v1 = mm.ones(10)
    >>> v2 = mm.ones(10)
    >>> v3 = v1 + v2

    Multiply matrices (not yet available).

    >>> v1 = mm.ones(10)
    >>> m1 = mm.rand(10, 10)
    >>> v2 = m1*v1

    """

    def __init__(self, mapdl=None, **kwargs):
        """Initiate a common class for abstract math object."""
        if mapdl is None:
            mapdl = launch_mapdl(**kwargs)

        self._mapdl = mapdl

    @property
    def _server_version(self):
        """Version of MAPDL which is running in the background."""
        return self._mapdl._server_version

    @property
    def _status(self):
        """Status of all AnsMath objects."""
        return self._mapdl.run("*STATUS,MATH", mute=False)

    @property
    def _parm(self):
        return interp_star_status(self._status)

    def free(self, mat=None):
        """Delete AnsMath objects.

        mat: AnsMath object, optional
            AnsMath object to be deleted. Default value is None;
            all the AnsMath objects are deleted.

        Examples
        --------
        >>> u = mm.vec(10)
        >>> mm.free()
        >>> mm.status()

        """
        if mat is not None:
            if isinstance(mat, AnsMathObj):
                self._mapdl.run(f"*FREE,{mat.id}", mute=True)
            else:
                raise TypeError("The object to delete needs to be an AnsMath object.")
        else:
            self._mapdl.run("*FREE,ALL", mute=True)

    def __repr__(self):
        return self._status

    def status(self):
        """Print the status of all AnsMath objects.

        Examples
        --------
        >>> mm.status()
        APDLMATH PARAMETER STATUS-  (      4 PARAMETERS DEFINED)
        Name         Type   Mem. (MB)       Dims            Workspace
        NJHLVM       SMAT   0.011           [126:126]               1
        RMAXLQ       SMAT   0.011           [126:126]               1
        WWYLBR       SMAT   0.011           [126:126]               1
        FIOMZR       VEC    0.001           126                     1

        """
        print(self._status)

    def vec(self, size=0, dtype=np.double, init=None, name=None, asarray=False):
        """Create a vector.

        Parameters
        ----------
        size : int
            Size of the vector.
        dtype : np.dtype, optional
            NumPy data type of the vector. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
        init : str, optional
            Initialization options. Options are ``"ones"``, ``"zeros"``,
            or ``"rand"``. The default is ``"zeros"``.
        name : str, optional
            AnsMath vector name. The default is ``None``, in which case a
            name is automatically generated.
        asarray : bool, optional
            Whether the output is to be a NumPy array vector rather than an
            AnsMath vector. The default is ``False``.

        Returns
        -------
        AnsVec or numpy.ndarray
            AnsMath vector or NumPy array vector, depending on the value for
            the ``asarray`` parameter.
        """
        if dtype not in MYCTYPE:
            raise ANSYSDataTypeError

        if not name:
            name = id_generator()

        if name.upper() not in self._parm:
            self._mapdl.run(f"*VEC,{name},{MYCTYPE[dtype]},ALLOC,{size}", mute=True)

        ans_vec = AnsVec(name, self._mapdl, dtype, init)

        if asarray:
            vec = self._mapdl._vec_data(ans_vec.id)
        else:
            vec = ans_vec

        return vec

    def mat(self, nrow=1, ncol=1, dtype=np.double, init=None, name=None, asarray=False):
        """Create a matrix.

        Parameters
        ----------
        nrow : int, optional
            Number of rows. The default is ``1``.
        ncol : int, optional
            Number of columns. The default is ``1``.
        dtype : np.dtype, optional
            NumPy data type of the matrix. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
        init : str, optional
            Initialization options. Options are ``"zeros"``, ``"ones"``,
            or ``"rand"``. The default is ``"zeros"``.
        name : str, optional
            AnsMath matrix name. The default is ``None``, in which case a
            name is automatically generated.
        asarray : bool, optional
            Whether to return a NumPy array rather than an AnsMath matrix.
            The default is ``False``.

        Returns
        -------
        AnsMat or numpy.ndarray
            AnsMath matrix or NumPy array matrix, depending on the value for
            the ``asarray`` parameter.
        """
        if dtype not in MYCTYPE:
            raise ValueError(
                "Invalid data type. The data type must be one of the following:\n"
                "np.int32, np.int64, or np.double."
            )

        if not name:
            name = id_generator()
            self._mapdl.run(f"*DMAT,{name},{MYCTYPE[dtype]},ALLOC,{nrow},{ncol}", mute=True)
            mat = AnsDenseMat(name, self._mapdl)

            if init == "rand":
                mat.rand()
            elif init == "ones":
                mat.ones()
            elif init == "zeros" or init is None:
                mat.zeros()
            elif init is not None:
                raise ValueError(f"Invalid initialization method '{init}'.")
        else:
            info = self._mapdl._data_info(name)
            if info.objtype == pb_types.DataType.DMAT:
                mat = AnsDenseMat(name, self._mapdl)
            elif info.objtype == pb_types.DataType.SMAT:
                mat = AnsSparseMat(name, self._mapdl)
            else:  # pragma: no cover
                raise ValueError(f"Unhandled AnsMath matrix object type {info.objtype}.")

        if asarray:
            mat = mat.asarray()
        return mat

    def zeros(self, nrow, ncol=None, dtype=np.double, name=None, asarray=False):
        """Create a vector or a matrix where all values are zeros.

        Parameters
        ----------
        nrow : int
            Number of rows.
        ncol : int, optional
            Number of columns. If a value is specified, a matrix is returned.
        dtype : np.dtype, optional
            NumPy data type of the object. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
        name : str, optional
            AnsMath object name. The default is ``None``, in which case a
            name is automatically generated.
        asarray : bool, optional
            Whether to return a NumPy array rather than an AnsMath object.
            The default is ``False``.

        Returns
        -------
        AnsVec, AnsMat, or numpy.ndarray
            AnsMath vector, NumPy array vector, AnsMath matrix, or NumPy array matrix,
            depending on the value for the ``asarray`` parameter and if a value for
            the ``ncol`` parameter is specified.

        Examples
        --------
        Create a vector where all values are zeros.

        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> vec = mm.zeros(10)

        Create a matrix where all values are zeros.

        >>> mat = mm.zeros(10, 10)
        """
        if not ncol:
            return self.vec(nrow, dtype, init="zeros", name=name, asarray=asarray)
        return self.mat(nrow, ncol, dtype, init="zeros", name=name, asarray=asarray)

    def ones(self, nrow, ncol=None, dtype=np.double, name=None, asarray=False):
        """Create a vector or a matrix where all values are ones.

        Parameters
        ----------
        nrow : int
            Number of rows.
        ncol : int, optional
            Number of columns. If a value is specified, a matrix is returned.
        dtype : np.dtype, optional
            NumPy data type of the object. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
        name : str, optional
            AnsMath object name. The default is ``None``, in which case a
            name is automatically generated.
        asarray : bool, optional
            Whether to return a NumPy array rather than an AnsMath object.
            The default is ``False``.

        Returns
        -------
        AnsVec, AnsMat, or numpy.ndarray
            AnsMath vector, NumPy array vector, AnsMath matrix, or NumPy array matrix,
            depending on the value for the ``asarray`` parameter and if a value for
            the ``ncol`` parameter is specified.

        Examples
        --------
        Create a vector where all values are ones.

        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> vec = mm.ones(10)

        Create a matrix where all values are ones.

        >>> mat = mm.ones(10, 10)
        """
        if not ncol:
            return self.vec(nrow, dtype, init="ones", name=name, asarray=asarray)
        else:
            return self.mat(nrow, ncol, dtype, init="ones", name=name, asarray=asarray)

    def rand(self, nrow, ncol=None, dtype=np.double, name=None, asarray=False):
        """Create a vector or a matrix where all values are random.

        Parameters
        ----------
        nrow : int
            Number of rows.
        ncol : int, optional
            Number of columns. If a value is specified, a matrix is returned.
        dtype : np.dtype, optional
            NumPy data type of the object. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
        name : str, optional
            AnsMath object name. The default is ``None``, in which case a
            name is automatically generated.
        asarray : bool, optional
            Whether to return a NumPy array rather than an AnsMath object.
            The default is ``False``.

        Returns
        -------
        AnsVec, AnsMat, or numpy.ndarray
            AnsMath vector, NumPy array vector, AnsMath matrix, or NumPy array matrix,
            depending on the value for the ``asarray`` parameter and if a value for
            the ``ncol`` parameter is specified.

        Examples
        --------
        Create a vector where all values are random.

        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> vec = mm.rand(10)

        Create a matrix where all values are random.

        >>> mat = mm.rand(10, 10)
        """
        if not ncol:
            return self.vec(nrow, dtype, init="rand", name=name, asarray=asarray)
        return self.mat(nrow, ncol, dtype, init="rand", name=name, asarray=asarray)

    def matrix(self, matrix, name=None, triu=False):
        """Send a SciPy matrix or NumPy array to MAPDL.

        Parameters
        ----------
        matrix : np.ndarray
            SciPy matrix or NumPy array to send as a matrix to MAPDL.
        name : str, optional
            AnsMath matrix name. The default is ``None``, in which case a
            name is automatically generated.
        triu : bool, optional
            Whether the matrix is the upper triangular. The default is ``False``,
            which means that the matrix is unsymmetric.

        Returns
        -------
        AnsMat
            Math matrix.

        Examples
        --------
        Generate a random sparse matrix.

        >>> from scipy import sparse
        >>> sz = 5000
        >>> mat = sparse.random(sz, sz, density=0.05, format='csr')
        >>> ans_mat = mm.matrix(mat, name)
        >>> ans_mat
        AnsMath matrix 5000 x 5000

        Transfer the matrix back to Python.

        >>> ans_mat.asarray()
        <500x5000 sparse matrix of type '<class 'numpy.float64'>'
                with 1250000 stored elements in Compressed Sparse Row (CSR) format>

        """
        if name is None:
            name = id_generator()
        elif not isinstance(name, str):
            raise TypeError("``name`` parameter must be a string")

        from scipy import sparse

        self._set_mat(name, matrix, triu)
        if sparse.issparse(matrix):
            ans_mat = AnsSparseMat(name, self._mapdl)
        else:
            ans_mat = AnsDenseMat(name, self._mapdl)
        return ans_mat

    def load_matrix_from_file(
        self,
        dtype=np.double,
        name=None,
        fname="file.full",
        mat_id="STIFF",
        asarray=False,
    ):
        """Import a matrix from an existing FULL file.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            Data type to store the matrix as. The options are double
            (``"DOUBLE"`` or ``"D"``), complex numbers (``"COMPLEX"`` or ``"Z"``),
            or NumPy data type (``np.double``, ``np.int32``, and ``np.int64``).
            The default is ``np.double``.
        fname : str, optional
            Name of the file to read the matrix from. The default is ``"file.full"``.
        name : str, optional
            AnsMath matrix name. The default is ``None``, in which case a
            name is automatically generated.
        mat_id : str, optional
            Matrix type. The default is ``"STIFF"``. Options are:

            * ``"STIFF"``: Stiffness matrix.
            * ``"MASS"``: Mass matrix.
            * ``"DAMP"``: Damping matrix.
            * ``"GMAT"``: Constraint equation matrix.
            * ``"K_RE"``: Real part of the stiffness matrix.
            * ``"K_IM"``: Imaginary part of the stiffness matrix.
        asarray : bool, optional
            Whether to return a SciPy array rather than an AnsMath matrix.
            The default is ``False``.

        Returns
        -------
        AnsMat or scipy.sparse.csr.csr_matrix
            AnsMath matrix or SciPy sparse matrix, depending on the value for
            the ``asarray`` parameter.

        """
        if name is None:
            name = id_generator()
        elif not isinstance(name, str):
            raise TypeError("``name`` parameter must be a string")

        self._mapdl._log.info("Calling MAPDL to extract the %s matrix from %s", mat_id, fname)
        quotes = "'"
        allowed_mat_id = (
            "STIFF",
            "MASS",
            "DAMP",
            # "NOD2BCS",  # Not allowed since #990
            # "USR2BCS",
            "GMAT",
            "K_RE",
            "K_IM",
        )
        if mat_id.upper() not in allowed_mat_id:
            raise ValueError(
                f"The 'mat_id' parameter supplied ('{mat_id}') is not allowed. "
                f"Only the following are allowed: \n"
                f"{', '.join([quotes + each + quotes for each in allowed_mat_id])}."
            )

        if isinstance(dtype, str):
            if dtype.lower() not in ("complex", "double", "d", "z"):
                raise ValueError(
                    f"Data type ({dtype}) not allowed as a string."
                    "Use either: 'double' or 'complex', or a valid NumPy data type."
                )
            if dtype.lower() in ("complex", "z"):
                dtype_ = "'Z'"
                dtype = np.complex64
            else:
                dtype_ = "'D'"
                dtype = np.double
        else:
            if dtype not in ANSYS_VALUE_TYPE.values():
                allowables_np_dtypes = ", ".join(
                    [str(each).split("'")[1] for each in ANSYS_VALUE_TYPE.values() if each]
                )
                raise ValueError(f"NumPy data type not allowed. Only: {allowables_np_dtypes}.")
            if "complex" in str(dtype):
                dtype_ = "'Z'"
            else:
                dtype_ = "'D'"

        if dtype_ == "'Z'" and mat_id.upper() in ("STIFF", "MASS", "DAMP"):
            raise ValueError(
                "Reading the stiffness, mass, or damping matrices to a complex "
                "array is not supported."
            )

        self._mapdl.run(f"*SMAT,{name},{dtype_},IMPORT,FULL,{fname},{mat_id}", mute=True)
        ans_sparse_mat = AnsSparseMat(name, self._mapdl)
        if asarray:
            return self._mapdl._mat_data(ans_sparse_mat.id).astype(dtype)
        return ans_sparse_mat

    def _load_file(self, fname):
        """
        Provide file to MAPDL instance.

        If in local:
            Checks if the file exists. If not, raise a FileNotFound exception.

        If in not-local:
            Check if the file exists locally or in the working directory, if not,
            it will raise a FileNotFound exception.
            If the file is local, it will be uploaded.

        """
        return load_file(self._mapdl, fname)

    def stiff(
        self, dtype=np.double, name=None, fname="file.full", asarray=False
    ):  # to be moved to .io
        """Load the stiffness matrix from a FULL file.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            NumPy data type to store the matrix as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
            This parameter is only applicable if ``asarray=True``.
        name : str, optional
            AnsMath matrix name. The default is ``None``, in which case a
            name is automatically generated.
        fname : str, optional
            Name of the file to read the matrix from. The default is ``"file.full"``.
        asarray : bool, optional
            Whether to return a SciPy array rather than an AnsMath matrix.
            The default is ``False``.

        Returns
        -------
        AnsMat or `scipy.sparse.csr.csr_matrix`
            AnsMath matrix or SciPy sparse matrix, depending on the value for
            the ``asarray`` parameter.

        Examples
        --------
        >>> k = mm.stiff()
        AnsMath matrix 60 x 60

        Convert to a SciPy array.

        >>> mat = k.asarray()
        >>> mat
        <60x60 sparse matrix of type '<class 'numpy.float64'>'
            with 1734 stored elements in Compressed Sparse Row (CSR) format>
        """
        fname = self._load_file(fname)
        return self.load_matrix_from_file(dtype, name, fname, "STIFF", asarray)

    def mass(
        self, dtype=np.double, name=None, fname="file.full", asarray=False
    ):  # to be moved to .io
        """Load the mass matrix from a FULL file.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            NumPy data type to store the matrix as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
            This parameter is only applicable if ``asarray=True``.
        name : str, optional
            AnsMath matrix name. The default is ``None``, in which case a
            name is automatically generated.
        fname : str, optional
            Name of the file to read the matrix from. The default is ``"file.full"``.
        asarray : bool, optional
            Whether to return a SciPy array rather than an AnsMath matrix.
            The default is ``False``.

        Returns
        -------
        AnsMat or scipy.sparse.csr.csr_matrix
            AnsMath matrix or SciPy sparse matrix, depending on the value for
            the ``asarray`` parameter.

        Examples
        --------
        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> mass = mm.mass()
        >>> mass
        AnsMath matrix 60 x 60

        Convert to a SciPy array.

        >>> mat = mass.asarray()
        >>> mat
        <60x60 sparse matrix of type '<class 'numpy.float64'>'
            with 1734 stored elements in Compressed Sparse Row (CSR) format>.
        """
        fname = self._load_file(fname)
        return self.load_matrix_from_file(dtype, name, fname, "MASS", asarray)

    def damp(
        self, dtype=np.double, name=None, fname="file.full", asarray=False
    ):  # to be moved to .io
        """Load the damping matrix from a FULL file.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            NumPy data type to store the matrix as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
            This parameter is only applicable if ``asarray=True``.
        name : str, optional
            AnsMath matrix name. The default is ``None``, in which case a
            name is automatically generated.
        fname : str, optional
            Name of the file to read the matrix from. The default is ``"file.full"``.
        asarray : bool, optional
            Whether to return a SciPy array rather than an AnsMath matrix.
            The default is ``False``.

        Returns
        -------
        AnsMat or `scipy.sparse.csr.csr_matrix`
            AnsMath matrix or SciPy sparse matrix, depending on the value for
            the ``asarray`` parameter.

        Examples
        --------
        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> ans_mat = mm.damp()
        >>> ans_mat
        AnsMath Matrix 60 x 60

        Convert to a SciPy array.

        >>> mat = ans_mat.asarray()
        >>> mat
        <60x60 sparse matrix of type '<class 'numpy.float64'>'
            with 1734 stored elements in Compressed Sparse Row (CSR) format>.

        """
        fname = self._load_file(fname)
        return self.load_matrix_from_file(dtype, name, fname, "DAMP", asarray)

    def get_vec(
        self, dtype=None, name=None, fname="file.full", mat_id="RHS", asarray=False
    ):  # to be moved to .io
        """Load a vector from a FULL file.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            NumPy data type to store the vector as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
        name : str, optional
            AnsMath vector name. The default is ``None``, in which case a
            name is automatically generated.
        fname : str, optional
            Name of the file to read the vector from. The default is ``"file.full"``.
        mat_id : str, optional
            Vector ID to load. If loading from a ``"*.full"`` file,
            the vector ID can be one of the following:

            * ``"RHS"``: Load vector
            * ``"GVEC"``: Constraint equation constant terms
            * ``"BACK"``: Nodal mapping vector (internal to user)
              If this vector ID is used, the default ``dtype`` is ``np.int32``.
            * ``"FORWARD"`` - Nodal mapping vector (user to internal).
              If this vector ID is used, the default ``dtype`` is ``np.int32``.
        asarray : bool, optional
            Whether to return a NumPy array rather than an AnsMath vector.
            The default is ``False``.

        Returns
        -------
        AnsVec or numpy.ndarray
            AnsMath vector or NumPy array vector, depending on the value for
            the ``asarray`` parameter.

        Examples
        --------
        >>> vec = mm.get_vec(fname='PRSMEMB.full', mat_id="RHS")
        >>> vec
        AnsMath vector size 126

        """
        if name is None:
            name = id_generator()
        elif not isinstance(name, str):
            raise TypeError("The ``name`` parameter must be a string.")

        self._mapdl._log.info(
            "Call MAPDL to extract the %s vector from the file %s.", mat_id, fname
        )

        if mat_id.upper() not in ["RHS", "GVEC", "BACK", "FORWARD"]:
            raise ValueError(
                f"The 'mat_id' value ({mat_id}) is not allowed."
                'Only "RHS", "GVEC", "BACK", or "FORWARD" are allowed.'
            )

        if mat_id.upper() in ["BACK", "FORWARD"] and not dtype:
            dtype = np.int32
        else:
            dtype = np.double

        fname = self._load_file(fname)
        self._mapdl.run(f"*VEC,{name},{MYCTYPE[dtype]},IMPORT,FULL,{fname},{mat_id}", mute=True)
        ans_vec = AnsVec(name, self._mapdl)
        if asarray:
            return self._mapdl._vec_data(ans_vec.id).astype(dtype, copy=False)
        return ans_vec

    def set_vec(self, data, name=None):
        """Push a NumPy array or a Python list to the MAPDL memory workspace.

        Parameters
        ----------
        data : np.ndarray, list
            NumPy array or Python list to push to MAPDL. It must be
            one dimensional.
        name : str, optional
            AnsMath vector name. The default is ``None``, in which case
            a name is automatically generated.

        Returns
        -------
        AnsVec
            AnsMath vector instance generated from the pushed vector.

        Examples
        --------
        Push a random vector from NumPy to MAPDL.

        >>> data = np.random.random(10)
        >>> vec = mm.set_vec(data)
        >>> np.isclose(vec.asarray(), data)
        True
        """
        if name is None:
            name = id_generator()
        self._set_vec(name, data)
        return AnsVec(name, self._mapdl)

    def rhs(
        self, dtype=np.double, name=None, fname="file.full", asarray=False
    ):  # to be moved to .io
        """Return the load vector from a FULL file.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            NumPy data type to store the vector as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is ``np.double``.
        name : str, optional
            AnsMath vector name. The default is ``None``, in which case a
            name is automatically generated.
        fname : str, optional
            Name of the file to read the vector from. The default is ``"file.full"``.
        asarray : bool, optional
            Whether to return a NumPy array rather than an AnsMath vector.
            The default is ``False``.

        Returns
        -------
        AnsVec or numpy.ndarray
            AnsMath vector or NumPy array vector, depending on the value for
            the ``asarray`` parameter.

        Examples
        --------
        >>> rhs = mm.rhs(fname='PRSMEMB.full')
        AnsMath vector size 126

        """
        fname = self._load_file(fname)
        return self.get_vec(dtype, name, fname, "RHS", asarray)

    def svd(self, mat, thresh="", sig="", v="", **kwargs):
        """Apply an SVD algorithm on a matrix.

        The SVD algorithm is only applicable to dense matrices.
        Columns that are linearly dependent on others are removed,
        leaving the independent or basis vectors. The matrix is
        resized according to the new size determined by the SVD algorithm.

        For the SVD algorithm, the singular value decomposition of an
        input matrix is a factorization of the form:

        ``M = U*SIGMA*V.T``

        For more information, see `Singular Value Decomposition
        <https://en.wikipedia.org/wiki/Singular_value_decomposition>`_.

        Parameters
        ----------
        mat : AnsMat
            Array to compress.
        thresh : float, optional
            Numerical threshold value for managing the compression.
            The default is is 1E-7.
        sig : str, optional
            Name of the vector for storing the ``SIGMA`` values.
        v : str, optional
            Name of the vector for storing the values from ``v``.
            See the preceding equation.

        Examples
        --------
        Apply the SVD algorithm on an existing dense rectangular matrix, using
        the default threshold. The matrix is modified in-place.

        >>> mm.svd(mat)
        """
        kwargs.setdefault("mute", True)
        self._mapdl.run(f"*COMP,{mat.id},SVD,{thresh},{sig},{v}", **kwargs)

    def mgs(self, mat, thresh="", **kwargs):
        """Apply the Modified Gram-Schmidt (MGS) algorithm to a matrix.

        The MGS algorithm is only applicable to dense matrices.
        Columns that are linearly dependent on others are removed,
        leaving the independent or basis vectors. The matrix is
        resized according to the new size determined by the algorithm.

        Parameters
        ----------
        mat : AnsMat
            Array to apply the Modified Gram-Schmidt algorithm to.
        thresh : float, optional
            Numerical threshold value for managing the compression.
            For the MGS algorithm, the default value is ``1E-14``.

        Examples
        --------
        Apply the MGS algorithm on an existing dense rectangular matrix,
        using the default threshold. The AnsMath matrix is modified in-situ.

        >>> mm.mgs(mat)
        """
        kwargs.setdefault("mute", True)
        self._mapdl.run(f"*COMP,{mat.id},MGS,{thresh}", **kwargs)

    def sparse(self, mat, thresh="", **kwargs):
        """Sparsify an existing matrix based on a threshold value.

        Parameters
        ----------
        mat : AnsMat
            Dense matrix to convert to a sparse matrix.
        thresh : float, optional
            Numerical threshold value for sparsifying. The default
            value is ``1E-16``.
        """
        kwargs.setdefault("mute", True)
        self._mapdl.run(f"*COMP,{mat.id},SPARSE,{thresh}", **kwargs)

    def eigs(
        self,
        nev,
        k,
        m=None,
        c=None,
        phi=None,
        algo=None,
        fmin=None,
        fmax=None,
        cpxmod=None,
    ):
        """Solve an eigenproblem.

        Parameters
        ----------
        nev : int
            Number of eigenvalues to compute.
        k : AnsMat
            AnsMath matrix representing the operation ``A * x`` where ``A`` is a
            square matrix.
        m : AnsMat, optional
            AnsMath matrix representing the operation ``M * x`` for the
            generalized eigenvalue problem:

            ``K * x = M * x``

        Examples
        --------
        Solve an eigenproblem using the mass and stiffness matrices
        stored from a prior Ansys run.

        >>> k = mm.stiff()
        >>> m = mm.mass()
        >>> nev = 10
        >>> a = mm.mat(k.nrow, nev)
        >>> ev = mm.eigs(nev, k, m, phi=a)
        """
        if not fmin:
            fmin = ""
        if not fmax:
            fmax = ""
        if not cpxmod:
            cpxmod = ""

        cid = ""
        if not c:
            if k.sym() and m.sym():
                if not algo:
                    algo = "LANB"
            else:
                algo = "UNSYM"
        else:
            cid = c.id
            algo = "DAMP"

        self._mapdl.run("/SOLU", mute=True)
        self._mapdl.run("antype,modal", mute=True)
        self._mapdl.run(f"modopt,{algo},{nev},{fmin},{fmax},{cpxmod}", mute=True)
        ev = self.vec()

        phistr = "" if not phi else phi.id
        self._mapdl.run(f"*EIG,{k.id},{m.id},{cid},{ev.id},{phistr}", mute=True)
        return ev

    def dot(self, vec_a, vec_b):
        """Multiply two AnsMath vectors.

        Parameters
        ----------
        vec_a : AnsVec
            AnsMath vector.

        vec_b : AnsVec
            AnsMath vector.

        Returns
        -------
        float
            Product of multiplying the two vectors.

        Examples
        --------
        >>> v = mm.ones(10)
        >>> w = mm.ones(10)
        >>> v.dot(w)
        """
        return dot(vec_a, vec_b)

    def add(self, obj1, obj2):
        """Add two AnsMath vectors or matrices.

        Parameters
        ----------
        obj1 : AnsVec or AnsMat
            AnsMath object.
        obj2 : AnsVec or AnsMat
            AnsMath object.

        Returns
        -------
        AnsVec or AnsMat
            Sum of the two input objects. The type of the output matches
            the type of the input.

        Examples
        --------
        Add two AnsMath vectors.

        >>> v = mm.ones(10)
        >>> w = mm.ones(10)
        >>> x = mm.add(v, w)
        """
        return obj1 + obj2

    def subtract(self, obj1, obj2):
        """Subtract two AnsMath vectors or matrices.

        Parameters
        ----------
        obj1 : AnsVec or AnsMat
            AnsMath object.
        obj2 : AnsVec or AnsMat
            AnsMath object.

        Returns
        -------
        AnsVec or AnsMat
            Difference of the two input vectors or matrices. The type of
            the output matches the type of the input.

        Examples
        --------
        Subtract two AnsMath vectors.

        >>> v = mm.ones(10)
        >>> w = mm.ones(10)
        >>> x = mm.subtract(v, w)
        """
        return obj1 - obj2

    def factorize(self, mat, algo=None, inplace=True):
        """Factorize a matrix.

        Parameters
        ----------
        mat : AnsMat
            AnsMath matrix.
        algo : str, optional
            Factorization algorithm. Options are ``"LAPACK"`` and ``"DSP"``.
            The default is ``"LAPACK"`` for dense matrices and ``"DSP"`` for
            sparse matrices.
        inplace : bool, optional
            Whether the factorization is performed on the input matrix
            rather than on a copy of this matrix. Performing factorization on
            a copy of this matrix would result in no changes to the input
            matrix. The default is ``True``.

        Returns
        -------
        AnsSolver
            Ansys Solver object.


        Examples
        --------
        Factorize a random matrix.

        >>> dim = 1000
        >>> m2 = mm.rand(dim, dim)
        >>> m3 = m2.copy()
        >>> mat = mm.factorize(m2)

        """
        solver = AnsSolver(id_generator(), self._mapdl)
        solver.factorize(mat, algo=algo, inplace=inplace)
        return solver

    def norm(self, obj, order="nrm2"):
        """Return the norm of an AnsMath object.

        Parameters
        ----------
        obj : AnsMat or AnsVec
            AnsMath object to compute the norm from.
        order : str
            Mathematical norm to use. The default is ``'NRM2'``.
            Options are:

            * ``'NRM2'``: L2 (Euclidean or SRSS) norm.
            * ``'NRM1'``: L1 (absolute sum) norm (vectors only).
            * ``'NRMINF'``: Maximum norm.
        nrm : float
            Norm of the matrix or the one or more vectors.

        Examples
        --------
        Compute the norm of an AnsMath vector.

        >>> v = mm.ones(10)
        >>> print (mm.norm(v))
        >>> 3.1622776601683795

        """
        return obj.norm(nrmtype=order)

    @protect_grpc
    def _set_vec(self, vname, arr, dtype=None, chunk_size=DEFAULT_CHUNKSIZE):
        """Transfer a NumPy array to MAPDL as an AnsMath vector.

        Parameters
        ----------
        vname : str
            Vector parameter name. The character ":" is not allowed.
        arr : np.ndarray
            NumPy array to upload.
        dtype : np.dtype, optional
            NumPy data type to upload the array as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is the current array
            type.
        chunk_size : int, optional
            Chunk size in bytes. The value must be less than 4MB.

        """
        if ":" in vname:
            raise ValueError(
                "The character ':' is not permitted in an AnsMath vector parameter name."
            )
        if not isinstance(arr, np.ndarray):
            arr = np.asarray(arr)

        if dtype is not None:
            if arr.dtype != dtype:
                arr = arr.astype(dtype)

        if arr.dtype not in list(MYCTYPE.keys()):
            raise TypeError(
                f"Invalid array data type {arr.dtype}\n."
                f"The data type must be one of the following:\n"
                f"{list_allowed_dtypes()}"
            )

        chunks_generator = get_nparray_chunks(vname, arr, chunk_size)
        self._mapdl._stub.SetVecData(chunks_generator)

    @protect_grpc
    def _set_mat(self, mname, arr, sym=False, dtype=None, chunk_size=DEFAULT_CHUNKSIZE):
        """Transfer a 2D dense or sparse SciPy array to MAPDL as an AnsMath matrix.

        Parameters
        ----------
        mname : str
            Matrix parameter name. The character ":" is not allowed.
        arr : np.ndarray or scipy.sparse matrix
            Matrix to upload.
        sym : bool
            Whether the matrix is symmetric rather than dense.
            The default is ``False`` which means that the matrix is dense.
        dtype : np.dtype, optional
            NumPy data type to upload the array as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is the current array
            type.
        chunk_size : int, optional
            Chunk size in bytes. The value must be less than 4MB.

        """
        from scipy import sparse

        if ":" in mname:
            raise ValueError("The character ':' is not permitted in the name of an AnsMath matrix.")
        if not len(mname):
            raise ValueError("A name must be supplied for the AnsMath matrix.")

        if isinstance(arr, np.ndarray):
            if arr.ndim == 1:
                raise ValueError("Input appears to be an array. " "Use ``set_vec`` instead.)")
            if arr.ndim > 2:
                raise ValueError("Arrays must be 2-dimensional.")

        if sparse.issparse(arr):
            self._send_sparse(mname, arr, sym, dtype, chunk_size)
        else:  # must be dense matrix
            self._send_dense(mname, arr, dtype, chunk_size)

    @requires_version((0, 4, 0), VERSION_MAP)
    def _send_dense(self, mname, arr, dtype, chunk_size):
        """Send a dense NumPy array/matrix to MAPDL."""
        if dtype is not None:
            if arr.dtype != dtype:
                arr = arr.astype(dtype)

        if arr.dtype not in list(NP_VALUE_TYPE.keys()):
            raise TypeError(
                f"Invalid array data type {arr.dtype}\n."
                f"The data type must be one of the following:\n"
                f"{list_allowed_dtypes()}"
            )

        chunks_generator = get_nparray_chunks_mat(mname, arr, chunk_size)
        self._mapdl._stub.SetMatData(chunks_generator)

    def _send_sparse(self, mname, arr, sym, dtype, chunk_size):
        """Send a SciPy sparse sparse matrix to MAPDL."""
        if sym is None:
            raise ValueError("The symmetric flag ``sym`` must be set for a sparse matrix.")
        from scipy import sparse

        arr = sparse.csr_matrix(arr)

        if arr.shape[0] != arr.shape[1]:
            raise ValueError("AnsMath only supports square matrices.")

        if dtype is not None:
            if arr.data.dtype != dtype:
                arr.data = arr.data.astype(dtype)

        if arr.dtype not in list(NP_VALUE_TYPE.keys()):
            raise TypeError(
                f"Invalid array datatype {arr.dtype}\n."
                f"The data type must be one of the following:\n"
                f"{list_allowed_dtypes()}"
            )

        # data vector
        dataname = f"{mname}_DATA"
        ans_vec = self.set_vec(arr.data, dataname)
        if dtype is None:
            info = self._mapdl._data_info(ans_vec.id)
            dtype = ANSYS_VALUE_TYPE[info.stype]

        # indptr vector
        indptrname = f"{mname}_IND"
        indv = arr.indptr.astype("int64") + 1  # FORTRAN indexing
        self.set_vec(indv, indptrname)

        # indices vector
        indxname = f"{mname}_PTR"
        idx = arr.indices + 1  # FORTRAN indexing
        self.set_vec(idx, indxname)

        flagsym = "TRUE" if sym else "FALSE"
        self._mapdl.run(
            f"*SMAT,{mname},{MYCTYPE[dtype]},ALLOC,CSR,{indptrname},{indxname},"
            f"{dataname},{flagsym}"
        )


class AnsMathObj:
    """Provides the common class for AnsMath objects."""

    def __init__(self, id_, mapdl=None, dtype=ObjType.GEN):
        """Initiate a common class for AnsMath objects."""
        if mapdl is None:
            mapdl = launch_mapdl()
        self.id = id_
        self._mapdl = mapdl
        self.type = dtype

    def __repr__(self):
        return f"AnsMath object {self.id}"

    def __str__(self):
        return self._mapdl.run(f"*PRINT,{self.id}", mute=False)

    def copy(self):
        """Get the name of the copy of this object."""
        name = id_generator()  # internal name of the new object
        info = self._mapdl._data_info(self.id)
        dtype = ANSYS_VALUE_TYPE[info.stype]

        if self.type == ObjType.VEC:
            acmd = "*VEC"
        elif self.type == ObjType.DMAT:
            acmd = "*DMAT"
        elif self.type == ObjType.SMAT:
            acmd = "*SMAT"
        else:
            raise TypeError(f"Copy stopped: Unknown obj type {self.type}.")

        # AnsMath cmd to copy vin to vout.
        self._mapdl.run(f"{acmd},{name},{MYCTYPE[dtype]},COPY,{self.id}", mute=True)
        return name

    def _init(self, method):
        self._mapdl.run(f"*INIT,{self.id},{method}", mute=True)

    def zeros(self):
        """Set all values of the object to zero."""
        return self._init("ZERO")

    def ones(self):
        """Set all values of the object to one."""
        return self._init("CONST,1")

    def rand(self):
        """Set all values of the object to a random number."""
        return self._init("RAND")

    def const(self, value):
        """Set all values of the object to a constant."""
        return self._init(f"CONST,{value}")

    def norm(self, nrmtype="nrm2"):
        """Return the norm of the AnsMath object.

        Parameters
        ----------
        nrmtype : str, optional
            Mathematical norm to use. The default is ``'NRM2'``. Options are:

            - ``'NRM2'``: L2 (Euclidean or SRSS) norm.
            - ``'NRM1'``: L1 (absolute sum) norm (vectors only).
            - ``'NRMINF'``: Maximum norm.

        Returns
        -------
        float
            Norm of the matrix or the one or more vectors.

        Examples
        --------
        >>> dim = 1000
        >>> m2 = mm.rand(dim, dim)
        >>> nrm = m2.norm()
        """
        val_name = "py_val"
        self._mapdl.run(f"*NRM,{self.id},{nrmtype},{val_name}", mute=True)
        return self._mapdl.scalar_param(val_name)

    def axpy(self, obj, val1, val2):
        """Perform the matrix operation: ``self= val1*obj + val2*self``.

        Parameters
        ----------
        obj : AnsVec or AnsMat
            AnsMath object.

        val1 : float
            Ratio applied to the AnsMath object.

        val2 : float
            Ratio applied to the self object.

        Returns
        -------
        AnsVec or AnsMat
            Matrix operation result of ``self= val1*obj + val2*self``.

        Examples
        --------
        >>> dim = 2
        >>> m1 = mm.ones(dim, dim)
        >>> m2 = mm.rand(dim, dim)
        >>> m1.axpy(m2, 3, 4)
        >>> m1.asarray()
        array([[5.251066  , 6.16097347], [6.99155442, 6.79767208]])
        """
        if not hasattr(obj, "id"):
            raise TypeError("The object to be added must be an AnsMath object.")
        self._mapdl._log.info("Call MAPDL to perform an AXPY operation.")
        self._mapdl.run(f"*AXPY,{val1},0,{obj.id},{val2},0,{self.id}", mute=True)
        return self

    def kron(self, obj):
        """Calculates the Kronecker product of two matrices/vectors

        Parameters
        ----------
        obj : ``AnsVec`` or ``AnsMat``
            AnsMath object.

        Returns
        -------
        ``AnsMat`` or ``AnsVec``
            Kronecker product between the two matrices/vectors.

        .. note::
            Requires at least MAPDL version 2023R2.

        Examples
        --------
        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> m1 = mm.rand(3, 3)
        >>> m2 = mm.rand(4,2)
        >>> res = m1.kron(m2)
        """

        mapdl_version = self._mapdl.version
        if mapdl_version < 23.2:  # pragma: no cover
            raise VersionError("``kron`` requires MAPDL version 2023R2")

        if not isinstance(obj, AnsMathObj):
            raise TypeError("Must be an AnsMath object.")

        if not isinstance(self, (AnsMat, AnsVec)):
            raise TypeError(f"Kron product aborted: Unknown obj type ({self.type})")
        if not isinstance(obj, (AnsMat, AnsVec)):
            raise TypeError(f"Kron product aborted: Unknown obj type ({obj.type})")

        name = id_generator()  # internal name of the new vector/matrix
        # perform the Kronecker product
        self._mapdl.run(f"*KRON,{self.id},{obj.id},{name}")

        if isinstance(self, AnsVec) and isinstance(obj, AnsVec):
            objout = AnsVec(name, self._mapdl)
        else:
            objout = AnsMat(name, self._mapdl)
        return objout

    def __add__(self, op2):
        if not hasattr(op2, "id"):
            raise TypeError("The object to be added must be an AnsMath object.")

        opout = self.copy()
        self._mapdl._log.info("Call MAPDL to perform an AXPY operation.")
        self._mapdl.run(f"*AXPY,1,0,{op2.id},1,0,{opout.id}", mute=True)
        return opout

    def __sub__(self, op2):
        if not hasattr(op2, "id"):
            raise TypeError("The object to be subtracted must be an AnsMath object.")

        opout = self.copy()
        self._mapdl._log.info("Call MAPDL to perform an AXPY operation.")
        self._mapdl.run(f"*AXPY,-1,0,{op2.id},1,0,{opout.id}", mute=True)
        return opout

    def __matmul__(self, op):
        return self.dot(op)

    def __iadd__(self, op):
        return self.axpy(op, 1, 1)

    def __isub__(self, op):
        return self.axpy(op, -1, 1)

    def __imul__(self, val):
        mapdl_version = self._mapdl.version
        self._mapdl._log.info("Call MAPDL to scale the object")

        if isinstance(val, AnsVec):
            if mapdl_version < 23.2:  # pragma: no cover
                raise VersionError("Scaling by a vector requires MAPDL version 2023R2 or superior.")
            else:
                self._mapdl._log.info(f"Scaling ({self.type}) by a vector")
                self._mapdl.run(f"*SCAL,{self.id},{val.id}", mute=False)
        elif isinstance(val, (int, float)):
            self._mapdl.run(f"*SCAL,{self.id},{val}", mute=True)
        else:
            raise TypeError(f"The provided type {type(val)} is not supported.")

        return self

    def __itruediv__(self, val):
        if val == 0:
            raise ZeroDivisionError("division by zero")
        self._mapdl._log.info("Call MAPDL to 1/scale the object.")
        self._mapdl.run(f"*SCAL,{self.id},{1/val}", mute=True)
        return self

    @property
    @protect_grpc
    def _data_info(self):
        """Data type of a parameter."""
        request = pb_types.ParameterRequest(name=self.id)
        return self._stub.GetDataInfo(request)


class AnsVec(AnsMathObj):
    """Provides the AnsMath vector objects."""

    def __init__(self, id_, mapdl, dtype=np.double, init=None):
        """Initiate an AnsMath vector object."""
        AnsMathObj.__init__(self, id_, mapdl, ObjType.VEC)

        if init not in ["ones", "zeros", "rand", None]:
            raise ValueError(
                f"Invalid initialization option {init}.\n"
                'The option should be "ones", "zeros", "rand", or None.'
            )

        if init == "rand":
            self.rand()
        elif init == "ones":
            self.ones()
        elif init == "zeros":
            self.zeros()

    @property
    def size(self):
        """Number of items in this vector."""
        sz = self._mapdl.scalar_param(f"{self.id}_DIM")
        if sz is None:
            raise MapdlRuntimeError("This vector has been deleted within MAPDL.")
        return int(sz)

    def __repr__(self):
        return f"AnsMath vector size {self.size}"

    def __getitem__(self, num):
        info = self._mapdl._data_info(self.id)
        dtype = ANSYS_VALUE_TYPE[info.stype]
        if num < 0:
            raise ValueError("Negative indices not permitted")

        self._mapdl.run(f"pyval_={self.id}({num+1})", mute=True)
        item_val = self._mapdl.scalar_param("pyval_")

        if MYCTYPE[dtype].upper() in ["C", "Z"]:
            self._mapdl.run(f"pyval_img_={self.id}({num+1},2)", mute=True)
            img_val = self._mapdl.scalar_param("pyval_img_")
            item_val = item_val + img_val * 1j

            # Clean parameters
            self._mapdl.run("item_val =")
            self._mapdl.run("pyval_img_=")

        return item_val

    def __mul__(self, vec):
        """Return the element-wise product with another AnsMath vector.

        This value is known as a Hadamard product.

        .. note::
            This method requires MAPDL 2021 R2 or later.

        Parameters
        ----------
        vec : AnsVec
            AnsMath vector.

        Returns
        -------
        AnsVec
            Hadamard product between this vector and the other vector.
        """
        if not server_meets_version(self._mapdl._server_version, (0, 4, 0)):  # pragma: no cover
            raise VersionError("``AnsVec`` requires MAPDL version 2021 R2 or later.")

        if not isinstance(vec, AnsVec):
            raise TypeError("The object to be multiplied must be an AnsMath vector.")

        name = id_generator()  # internal name of the new vector/matrix
        info = self._mapdl._data_info(self.id)
        dtype = ANSYS_VALUE_TYPE[info.stype]

        # check size consistency
        if self.size != vec.size:
            raise ValueError("Vectors have inconsistent sizes.")

        self._mapdl.run(f"*VEC,{name},{MYCTYPE[dtype]},ALLOC,{info.size1}")
        objout = AnsVec(name, self._mapdl)

        # perform the Hadamard product
        self._mapdl.run(f"*HPROD,{self.id},{vec.id},{name}")
        return objout

    def copy(self):
        """Get a copy of the vector."""
        return AnsVec(AnsMathObj.copy(self), self._mapdl)

    def dot(self, vec) -> float:
        """Multiply the AnsMath vector by another AnsMath vector.

        Parameters
        ----------
        vec : AnsVec
            AnsMath vector.

        Returns
        -------
        float
            Product of multiplying this vector with another vector.
        """
        if not isinstance(vec, AnsVec):
            raise TypeError("The object to be multiplied must be an AnsMath vector.")

        self._mapdl.run(f"*DOT,{self.id},{vec.id},py_val")
        return self._mapdl.scalar_param("py_val")

    def asarray(self, dtype=None) -> np.ndarray:
        """Return the vector as a NumPy array.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            NumPy data type to upload the array as. The options are :class:`numpy.double`,
            :class:`numpy.int32`, and :class:`numpy.int64`. The default is the current
            array type.

        Returns
        -------
        np.ndarray
            NumPy array with the defined data type.

        Examples
        --------
        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> v = mm.ones(10)
        >>> v.asarray()
        [1. 1. 1. 1. 1. 1. 1. 1. 1. 1.]
        >>> v.asarray(dtype=np.int32)
        [1 1 1 1 1 1 1 1 1 1]

        """
        vec_data = self._mapdl._vec_data(self.id)
        return vec_data.astype(dtype) if dtype else vec_data

    def __array__(self):
        """Allow NumPy to access this object as if it was an array."""
        return self.asarray()


class AnsMat(AnsMathObj):
    """Provides the AnsMath matrix objects."""

    def __init__(self, id_, mapdl, type_=ObjType.DMAT):
        """Initiate an AnsMath matrix object."""
        AnsMathObj.__init__(self, id_, mapdl, type_)

    @property
    def nrow(self) -> int:
        """Number of columns in the matrix."""
        return int(self._mapdl.scalar_param(self.id + "_ROWDIM"))

    @property
    def ncol(self) -> int:
        """Number of rows in the matrix."""
        return int(self._mapdl.scalar_param(self.id + "_COLDIM"))

    @property
    def size(self) -> int:
        """Number of items in the matrix."""
        return self.nrow * self.ncol

    @property
    def shape(self) -> tuple:
        """NumPy-like shape.

        Tuple of (rows and columns).
        """
        return (self.nrow, self.ncol)

    def sym(self) -> bool:
        """Return if the matrix is symmetric.

        Returns
        -------
        bool
            ``True`` when this matrix is symmetric.

        """

        info = self._mapdl._data_info(self.id)

        if server_meets_version(self._mapdl._server_version, (0, 5, 0)):  # pragma: no cover
            return info.mattype in [
                0,
                1,
                2,
            ]  # [UPPER, LOWER, DIAG] respectively

        warn(
            "Call to ``sym`` method cannot evaluate if this matrix is symmetric "
            "with this version of MAPDL."
        )
        return True

    def asarray(self, dtype=None) -> np.ndarray:
        """Return the matrix as a NumPy array.

        Parameters
        ----------
        dtype : numpy.dtype, optional
            NumPy data type to upload the array as. The options are ``np.double``,
            ``np.int32``, and ``np.int64``. The default is the current array
            type.

        Returns
        -------
        np.ndarray
            NumPy array with the defined data type.

        Examples
        --------
        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> v = mm.ones(2,2)
        >>> v.asarray()
        array([[1., 1.], [1., 1.]])
        >>> v.asarray(dtype=np.int32)
        array([[1, 1], [1, 1]])

        """
        if dtype:
            return self._mapdl._mat_data(self.id).astype(dtype)
        else:
            return self._mapdl._mat_data(self.id)

    def __mul__(self, vec):
        raise AttributeError(
            "Array multiplication is not available. For scalar product, use `dot()`."
        )

    def dot(self, obj):
        """Multiply the AnsMath object by another AnsMath object.

        Parameters
        ----------
        obj : AnsVec or AnsMat
            AnsMath object.

        Returns
        -------
        AnsVec or AnsMat
            Matrix multiplication result.

        Examples
        --------
        Multiplication of a matrix and vector.

        >>> m1 = mm.rand(10, 10)
        >>> v1 = mm.rand(10)
        >>> v2 = m1.dot(v1)
        >>> assert np.allclose(m1.asarray() @ v1.asarray(), v2)

        """
        name = id_generator()  # internal name of the new vector/matrix
        info = self._mapdl._data_info(self.id)
        dtype = ANSYS_VALUE_TYPE[info.stype]
        if obj.type == ObjType.VEC:
            self._mapdl.run(f"*VEC,{name},{MYCTYPE[dtype]},ALLOC,{info.size1}", mute=True)
            objout = AnsVec(name, self._mapdl)
        else:
            self._mapdl.run(
                f"*DMAT,{name},{MYCTYPE[dtype]},ALLOC,{info.size1},{info.size2}",
                mute=True,
            )
            objout = AnsDenseMat(name, self._mapdl)

        self._mapdl._log.info("Call MAPDL to perform the multiplication.")
        self._mapdl.run(f"*MULT,{self.id},,{obj.id},,{name}", mute=True)
        return objout

    def __getitem__(self, num):
        """Return a vector from a given index."""
        name = id_generator()
        info = self._mapdl._data_info(self.id)
        dtype = ANSYS_VALUE_TYPE[info.stype]
        self._mapdl.run(f"*VEC,{name},{MYCTYPE[dtype]},LINK,{self.id},{num+1}", mute=True)
        return AnsVec(name, self._mapdl)

    @property
    def T(self):
        """Transposition of an AnsMath matrix.

        Examples
        --------
        >>> import ansys.math.core.math as pymath
        >>> mm = pymath.AnsMath()
        >>> mat = mm.rand(2, 3)
        >>> mat_t = mat.T

        """
        info = self._mapdl._data_info(self.id)

        if info.objtype == 2:
            objtype = "*DMAT"
        else:
            objtype = "*SMAT"

        dtype = ANSYS_VALUE_TYPE[info.stype]
        name = id_generator()
        self._mapdl._log.info("Call MAPDL to transpose.")
        self._mapdl.run(f"{objtype},{name},{MYCTYPE[dtype]},COPY,{self.id},TRANS", mute=True)
        if info.objtype == 2:
            mat = AnsDenseMat(name, self._mapdl)
        else:
            mat = AnsSparseMat(name, self._mapdl)
        return mat


class AnsDenseMat(AnsMat):
    """Provides the AnsMath dense matrix objects."""

    def __init__(self, uid, mapdl):
        """Initiate an AnsMath dense matrix object."""
        AnsMat.__init__(self, uid, mapdl, ObjType.DMAT)

    def __array__(self):
        """Allow NumPy to access this object as if it was an array."""
        return self.asarray()

    def __repr__(self):
        return f"AnsMath dense matrix ({self.nrow}, {self.ncol}"

    def copy(self):
        """Return a copy of the matrix."""
        return AnsDenseMat(AnsMathObj.copy(self), self._mapdl)


class AnsSparseMat(AnsMat):
    """Provides the AnsMath sparse matrix objects."""

    def __init__(self, uid, mapdl):
        """Initiate an AnsMath sparse matrix object."""
        AnsMat.__init__(self, uid, mapdl, ObjType.SMAT)

    def __repr__(self):
        return f"AnsMath sparse matrix ({self.nrow}, {self.ncol})"

    def copy(self):
        """Return a copy of the matrix.

        Matrix remains in MAPDL.

        Examples
        --------
        >>> k
        AnsMath sparse matrix (126, 126)

        >>> kcopy = k.copy()
        >>> kcopy
        AnsMath sparse matrix (126, 126)

        """
        return AnsSparseMat(AnsMathObj.copy(self), self._mapdl)

    def todense(self) -> np.ndarray:
        """Return the array as a NumPy dense array.

        Examples
        --------
        >>> k
        AnsMath sparse matrix (126, 126)

        >>> mat = k.todense()
        >>> mat
        matrix([[ 2.02925393e-01,  3.78142616e-03,  0.00000000e+00, ...,
                  0.00000000e+00,  0.00000000e+00,  0.00000000e+00],
                [ 0.00000000e+00,  2.00906608e-01,  0.00000000e+00, ...,
                  0.00000000e+00,  0.00000000e+00,  0.00000000e+00],
                [ 0.00000000e+00,  0.00000000e+00,  2.29396542e+03, ...,
                  0.00000000e+00,  0.00000000e+00,  0.00000000e+00],
                ...,
                [ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00, ...,
                  2.26431549e+03, -9.11391851e-08,  0.00000000e+00],
                [ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00, ...,
                  0.00000000e+00,  3.32179197e+03,  0.00000000e+00],
                [ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00, ...,
                  0.00000000e+00,  0.00000000e+00,  2.48282229e-01]])

        """
        return self.asarray().todense()

    def __array__(self):
        """Allow NumPy to access this object as if it was an array."""
        return self.todense()


class AnsSolver(AnsMathObj):
    """Provides the AnsMath solver class."""

    def __repr__(self):
        return "AnsMath Linear Solver."

    def factorize(self, mat, algo=None, inplace=True):
        """Factorize a matrix.

        Perform the numerical factorization of a linear solver system: (:math:`A*x=b`).

        .. warning:: By default, factorization modifies the input matrix ``mat``
           in place. This behavior can be changed using the ``inplace`` parameter.

        Parameters
        ----------
        mat : AnsMat
            AnsMath matrix.
        algo : str, optional
            Factorization algorithm. Options are ``"LAPACK"`` and ``"DSP"``.
            The default is ``"LAPACK"`` for dense matrices and ``"DSP"`` for
            sparse matrices.
        inplace : bool, optional
            Whether the factorization is performed on the input matrix
            rather than on a copy of this matrix. Performing factorization on
            a copy of this matrix would result in no changes to the input
            matrix. The default is ``True``.

        Examples
        --------
        Factorize a random matrix and solve a linear system.

        >>> dim = 1000
        >>> m2 = mm.rand(dim, dim)
        >>> solver = mm.factorize(m2)
        >>> b = mm.ones(dim)
        >>> x = solver.solve(b)

        """
        mat_id = mat.id
        if not inplace:
            self._mapdl._log.info("Performing factorization in a copy of the array.")
            copy_mat = mat.copy()
            mat_id = copy_mat.id
        else:
            self._mapdl._log.info(
                "Performing factorization in place. This changes the input array."
            )

        if not algo:
            if mat.type == ObjType.DMAT:
                algo = "LAPACK"
            elif mat.type == ObjType.SMAT:
                algo = "DSP"

        self._mapdl.run(f"*LSENGINE,{algo},{self.id},{mat_id}", mute=True)
        self._mapdl._log.info(f"Factorizing using the {algo} package.")
        self._mapdl.run(f"*LSFACTOR,{self.id}", mute=True)

    def solve(self, b, x=None):
        """Solve a linear system.

        Parameters
        ----------
        b : AnsVec
            AnsMath vector.
        x : AnsVec, optional
            AnsMath vector to place the solution into.

        Returns
        -------
        AnsVec
            Solution vector, which is identical to the ``x`` parameter if supplied.

        Examples
        --------
        >>> k = mm.stiff(fname='PRSMEMB.full')
        >>> s = mm.factorize(k)
        >>> b = mm.get_vec(fname='PRSMEMB.full', mat_id="RHS")
        >>> x = s.solve(b)
        >>> x
        AnsMath vector size 20000

        """
        if not x:
            x = b.copy()
        self._mapdl._log.info("Solving")
        self._mapdl.run(f"*LSBAC,{self.id},{b.id},{x.id}", mute=True)
        return x


def rand(obj):
    """Set all values of an AnsMath object to random values.

    Parameters
    ----------
    obj : AnsMath object
        Math object.

    Examples
    --------
    >>> vec = mm.ones(10)
    >>> mm.rand(vec)
    """
    obj._mapdl.run(f"*INIT,{obj.id},RAND", mute=True)


def solve(mat, b, x=None, algo=None):
    solver = AnsSolver(id_generator(), mat._mapdl)
    solver.factorize(mat, algo)
    if not x:
        x = b.copy()
    x = solver.solve(b, x)

    del solver
    return x


def dot(vec1, vec2) -> float:
    """Multiply two AnsMath vectors.

    Parameters
    ----------
    vec1 : AnsVec
        First AnsMath vector.

    vec1 : AnsVec
        Second AnsMath vector.

    Returns
    -------
    float
        Product of multiplying the two vectors.

    """
    if vec1.type != ObjType.VEC or vec2.type != ObjType.VEC:
        raise TypeError("Both objects must be AnsMath vectors.")

    mapdl = vec1._mapdl
    mapdl.run(f"*DOT,{vec1.id},{vec2.id},py_val", mute=True)
    return mapdl.scalar_param("py_val")
