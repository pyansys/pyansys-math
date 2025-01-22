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

"""Test AnsMath functionality."""
import os
import re

from ansys.mapdl.core.errors import ANSYSDataTypeError, MapdlRuntimeError
from ansys.mapdl.core.launcher import get_start_instance
from ansys.mapdl.core.misc import random_string
from ansys.tools.versioning.exceptions import VersionError
from ansys.tools.versioning.utils import server_meets_version
import numpy as np
import pytest
from scipy import sparse

import ansys.math.core.math as pymath

# skip entire module unless HAS_GRPC
pytestmark = pytest.mark.skip_grpc

skip_in_cloud = pytest.mark.skipif(
    not get_start_instance(),
    reason="""
Must be able to launch MAPDL locally. Remote execution does not allow for
directory creation.
""",
)


PATH = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(PATH, "test_files")


@pytest.fixture(scope="module")
def mm(mapdl):
    mm = pymath.AnsMath(mapdl)
    return mm


@pytest.fixture()
def cube_with_damping(mm):
    mm._mapdl.prep7()
    db = os.path.join(lib_path, "model_damping.db")
    mm._mapdl.upload(db)
    mm._mapdl.resume("model_damping.db")
    mm._mapdl.mp("dens", 1, 7800 / 0.5)

    mm._mapdl.slashsolu()
    mm._mapdl.antype("modal")
    mm._mapdl.modopt("damp", 5)
    mm._mapdl.mxpand(5)
    mm._mapdl.mascale(0.15)

    mm._mapdl.alphad(10)
    mm._mapdl.solve()
    mm._mapdl.save()
    if mm._mapdl._distributed:
        mm._mapdl.aux2()
        mm._mapdl.combine("full")
        mm._mapdl.slashsolu()


def test_ones(mm):
    v = mm.ones(10)
    assert v.size == 10
    assert v[0] == 1


def test_rand(mm):
    w = mm.rand(10)
    assert w.size == 10


def test_asarray(mm):
    v = mm.ones(10)
    assert np.allclose(v.asarray(), np.ones(10))


def test_add(mm):
    v = mm.ones(10)
    w = mm.ones(10)
    z = v + w
    assert np.allclose(z.asarray(), 2)


def test_norm(mm):
    v = mm.ones(10)
    assert np.isclose(v.norm(), np.linalg.norm(v))
    assert np.isclose(mm.norm(v), v.norm())


def test_inplace_add(mm):
    v = mm.ones(10)
    w = mm.ones(10)
    w += v
    assert w[0] == 2


def test_inplace_mult(mm):
    v = mm.ones(10)
    v *= 2
    assert v[0] == 2


def test_inplace_mult_with_vec(mm):
    mapdl_version = mm._mapdl.version
    if mapdl_version < 23.2:
        pytest.skip("Requires MAPDL 2023 R2 or later.")

    m1 = mm.rand(3, 3)
    m2 = m1.copy()
    v1 = mm.ones(3)
    v1.const(2)
    m2 *= v1
    assert np.allclose(m2, np.multiply(m1, v1) * v1)


def test_set_vec_large(mm):
    # send a vector larger than the gRPC size limit of 4 MB
    sz = 1000000
    a = np.random.random(1000000)  # 7.62 MB (as FLOAT64)
    assert a.nbytes > 4 * 1024**2
    ans_vec = mm.set_vec(a)
    assert a[sz - 1] == ans_vec[sz - 1]
    assert np.allclose(a, ans_vec.asarray())


def test_dot(mm):
    a = np.arange(10000, dtype=np.double)
    b = np.arange(10000, dtype=np.double)
    np_rst = a.dot(b)

    vec_a = mm.set_vec(a)
    vec_b = mm.set_vec(b)
    assert np.allclose(vec_a.dot(vec_b), np_rst)
    assert np.allclose(mm.dot(vec_a, vec_b), np_rst)


def test_invalid_dtype(mm):
    with pytest.raises(ANSYSDataTypeError):
        mm.vec(10, dtype=np.uint8)


def test_vec(mm):
    vec = mm.vec(10, asarray=False)
    assert isinstance(vec, pymath.AnsVec)

    arr = mm.vec(10, asarray=True)
    assert isinstance(arr, np.ndarray)


@pytest.mark.parametrize("vecval", [np.zeros(10), np.array([1.0, 2.0, 8.0, 5.0, 6.2]), np.ones(3)])
def test_vec_from_name(mm, vecval):
    vec0 = mm.set_vec(vecval)
    vec1 = mm.vec(name=vec0.id)
    assert np.allclose(vec0, vec1)

    vec1 = mm.vec(name=vec0.id, asarray=True)
    assert isinstance(vec1, np.ndarray)


def test_vec__mul__(mm):
    # version check must be performed at runtime
    if mm._server_version[1] >= 4:
        a = mm.vec(10)
        b = mm.vec(10)
        assert np.allclose(a * b, np.asarray(a) * np.asarray(b))

        with pytest.raises(ValueError):
            mm.vec(10) * mm.vec(11)

        with pytest.raises(TypeError):
            mm.vec(10) * np.ones(10)


def test_numpy_max(mm):
    apdl_vec = mm.vec(10, init="rand")
    assert np.isclose(apdl_vec.asarray().max(), np.max(apdl_vec))


def test_shape(mm):
    shape = (10, 8)
    m1 = mm.rand(*shape)
    assert m1.shape == shape


def test_matrix(mm):
    sz = 5000
    mat = sparse.random(sz, sz, density=0.05, format="csr")
    assert mat.data.nbytes // 1024**2 > 4, "Must test over gRPC message limit"

    name = "TMP_MATRIX"
    ans_mat = mm.matrix(mat, name)
    assert ans_mat.id == name

    mat_back = ans_mat.asarray()
    assert np.allclose(mat.data, mat_back.data)
    assert np.allclose(mat.indices, mat_back.indices)
    assert np.allclose(mat.indptr, mat_back.indptr)


def test_matrix_fail(mm):
    mat = sparse.random(10, 10, density=0.05, format="csr")

    with pytest.raises(ValueError, match="':' is not permitted"):
        mm.matrix(mat, "my:mat")

    with pytest.raises(TypeError):
        mm.matrix(mat.astype(np.int8))


def test_matrix_addition(mm):
    m1 = mm.rand(10, 10)
    m2 = mm.rand(10, 10)
    m3 = m1 + m2
    assert np.allclose(m1.asarray() + m2.asarray(), m3.asarray())


def test_mul(mm):
    m1 = mm.rand(10, 10)
    w = mm.rand(10)
    with pytest.raises(AttributeError):
        m1 * w


# test kept for the eventual inclusion of mult
# def test_matrix_mult(mm):
#     m1 = mm.rand(10, 10)
#     w = mm.rand(10)
#     v = m1.w
#     assert np.allclose(w.asarray() @ m1.asarray(), v.asarray())

#     m1 = mm.rand(10, 10)
#     m2 = mm.rand(10, 10)
#     m3 = m1*m2
#     assert np.allclose(m1.asarray() @ m2.asarray(), m3.asarray())


def test_matrix_matmult(mm):
    u = mm.rand(10)
    v = mm.rand(10)
    w = u @ v
    assert np.allclose(u.asarray() @ v.asarray(), w)

    m1 = mm.rand(10, 10)
    w = mm.rand(10)
    v = m1 @ w
    assert np.allclose(m1.asarray() @ w.asarray(), v.asarray())

    m1 = mm.rand(10, 10)
    m2 = mm.rand(10, 10)
    m3 = m1 @ m2
    assert np.allclose(m1.asarray() @ m2.asarray(), m3.asarray())


def test_getitem_AnsMat(mm):
    size_i, size_j = (3, 3)
    mat = mm.rand(size_i, size_j)
    np_mat = mat.asarray()

    for i in range(size_i):
        vec = mat[i]
        for j in range(size_j):
            # recall that MAPDL uses fortran order
            assert vec[j] == np_mat[j, i]


@pytest.mark.parametrize("dtype_", [np.int64, np.double, np.complex128])
def test_getitem_AnsVec(mm, dtype_):
    size_i = 3
    vec = mm.rand(size_i, dtype=dtype_)
    np_vec = vec.asarray()
    for i in range(size_i):
        assert vec[i] == np_vec[i]


@pytest.mark.parametrize("dtype_", [np.double, np.complex128])
def test_kron_product(mm, dtype_):
    mapdl_version = mm._mapdl.version
    if mapdl_version < 23.2:
        pytest.skip("Requires MAPDL 2023 R2 or later.")

    m1 = mm.rand(3, 3, dtype=dtype_)
    m2 = mm.rand(2, 2, dtype=dtype_)
    v1 = mm.rand(2, dtype=dtype_)
    v2 = mm.rand(4, dtype=dtype_)
    # *kron product between matrix and another matrix
    res1 = m1.kron(m2)

    # *kron product between Vector and a matrix
    res2 = v1.kron(m2)

    # *kron product between Vector and another Vector
    res3 = v1.kron(v2)

    assert np.allclose(res1.asarray(), np.kron(m1, m2))
    assert np.allclose(res2.asarray(), np.kron(v1.asarray().reshape(2, 1), m2))
    assert np.allclose(res3.asarray(), np.kron(v1, v2))


def test_kron_product_unsupported_dtype(mm):
    mapdl_version = mm._mapdl.version
    if mapdl_version < 23.2:
        pytest.skip("Requires MAPDL 2023 R2 or later.")

    with pytest.raises(TypeError, match=r"Must be an AnsMath object."):
        m1 = mm.rand(3, 3)
        m1.kron(2)


def test_load_stiff_mass(mm, cube_solve, tmpdir):
    k = mm.stiff()
    m = mm.mass()
    assert k.shape == m.shape


def test_load_stiff_mass_different_location(mm, cube_solve, tmpdir):
    full_files = mm._mapdl.download("*.full", target_dir=tmpdir)
    fname_ = os.path.join(tmpdir, full_files[0])
    assert os.path.exists(fname_)

    k = mm.stiff(fname=fname_)
    m = mm.mass(fname=fname_)
    assert k.shape == m.shape
    assert all([each > 0 for each in k.shape])
    assert all([each > 0 for each in m.shape])


def test_load_stiff_mass_as_array(mm, cube_solve):
    k = mm.stiff(asarray=True)
    m = mm.mass(asarray=True)

    assert sparse.issparse(k)
    assert sparse.issparse(m)
    assert all([each > 0 for each in k.shape])
    assert all([each > 0 for each in m.shape])


def test_stiff_mass_name(mm, cube_solve):
    kname = pymath.id_generator()
    mname = pymath.id_generator()

    k = mm.stiff(name=kname)
    m = mm.mass(name=mname)

    assert k.id == kname
    assert m.id == mname


def test_stiff_mass_as_array(mm, cube_solve):
    k = mm.stiff()
    m = mm.mass()

    k = k.asarray()
    m = m.asarray()

    assert sparse.issparse(k)
    assert sparse.issparse(m)
    assert all([each > 0 for each in k.shape])
    assert all([each > 0 for each in m.shape])


@pytest.mark.parametrize(
    "dtype_",
    [
        np.int64,
        np.double,
        pytest.param(np.complex64, marks=pytest.mark.xfail),
        pytest.param("Z", marks=pytest.mark.xfail),
        "D",
        pytest.param("dummy", marks=pytest.mark.xfail),
        pytest.param(np.int8, marks=pytest.mark.xfail),
    ],
)
def test_load_stiff_mass_different_dtype(mm, cube_solve, dtype_):
    # AnsMat object do not support dtype assignment, you need to convert them to array first.
    k = mm.stiff(asarray=True, dtype=dtype_)
    m = mm.mass(asarray=True, dtype=dtype_)

    if isinstance(dtype_, str):
        if dtype_ == "Z":
            dtype_ = np.complex_
        else:
            dtype_ = np.double

    assert sparse.issparse(k)
    assert sparse.issparse(m)
    assert all([each > 0 for each in k.shape])
    assert all([each > 0 for each in m.shape])
    assert k.dtype == dtype_
    assert m.dtype == dtype_

    k = mm.stiff(dtype=dtype_)
    m = mm.mass(dtype=dtype_)

    k = k.asarray(dtype=dtype_)
    m = m.asarray(dtype=dtype_)

    assert sparse.issparse(k)
    assert sparse.issparse(m)
    assert all([each > 0 for each in k.shape])
    assert all([each > 0 for each in m.shape])
    assert k.dtype == dtype_
    assert m.dtype == dtype_


def test_load_matrix_from_file_incorrect_mat_id(mm, cube_solve):
    with pytest.raises(ValueError, match=r"The 'mat_id' parameter supplied.*is not allowed."):
        mm.load_matrix_from_file(fname="file.full", mat_id="DUMMY")


def test_load_matrix_from_file_incorrect_name(mm, cube_solve):
    with pytest.raises(TypeError, match=r"``name`` parameter must be a string"):
        mm.load_matrix_from_file(name=1245)


def test_mat_asarray(mm):
    mat0 = mm.mat(10, 10, asarray=True)
    mat1 = mm.mat(10, 10)
    assert np.allclose(mat0, mat1.asarray())


def test_mat_from_name_mapdl(mm):
    mat0 = mm.mat(10, 10, init="ones")  # The test has to be done with a
    # value other than the default one.
    mat1 = mm.mat(name=mat0.id)
    assert np.allclose(mat0, mat1)


@pytest.mark.parametrize(
    "matval",
    [
        np.zeros((5, 5)),
        np.array([[1.0, 2.0, 8.0, 5.0, 6.2], [5.1, 3.8, 8.2, 4.5, 2.0]]),
        np.ones((3, 4)),
    ],
)
def test_mat_from_name_dense(mm, matval):
    if not server_meets_version(mm._server_version, (0, 4, 0)):
        with pytest.raises(VersionError):
            mat0 = mm.matrix(matval)
    else:
        mat0 = mm.matrix(matval)
        mat1 = mm.mat(name=mat0.id)
        assert np.allclose(matval, mat1.asarray())


def test_mat_from_name_sparse(mm):
    scipy_mat = sparse.random(5, 5, density=1, format="csr")
    mat0 = mm.matrix(scipy_mat)
    mat1 = mm.mat(name=mat0.id)
    assert np.allclose(mat0, mat1)


def test_mat_invalid_dtype(mm):
    with pytest.raises(ValueError):
        mm.mat(10, 10, dtype=np.uint8)


def test_mat_invalid_init(mm):
    with pytest.raises(ValueError, match="Invalid initialization method"):
        mm.mat(10, 10, init="foo")


def test_solve(mm, cube_solve):
    k = mm.stiff()
    m = mm.mass()

    nev = 10
    a = mm.mat(k.nrow, nev)
    ev = mm.eigs(nev, k, m, phi=a)
    assert ev.size == nev


# alternative solve using math.solve
def test_solve_alt(mm, cube_solve):
    k = mm.stiff()
    b = mm.rand(k.nrow)
    eig_val = pymath.solve(k, b)
    assert eig_val.size == k.nrow


def test_solve_eigs_km(mapdl, mm, cube_solve):
    mapdl.post1()
    resp = mapdl.set("LIST")
    w_n = np.array(re.findall(r"\s\d*\.\d*\s", resp), np.float32)

    k = mm.stiff()
    m = mm.mass()
    vec = mm.eigs(w_n.size, k, m, fmin=1)
    eigval = vec.asarray()
    assert np.allclose(w_n, eigval, atol=0.1)


def test_solve_py(mapdl, mm, cube_solve):
    mapdl.post1()
    resp = mapdl.set("LIST")
    w_n = np.array(re.findall(r"\s\d*\.\d*\s", resp), np.float32)

    # load by default from file.full
    k = mm.stiff()
    m = mm.mass()

    # convert to numpy
    k_py = k.asarray()
    m_py = m.asarray()

    mapdl.clear()
    my_stiff = mm.matrix(k_py, triu=True)
    my_mass = mm.matrix(m_py, triu=True)

    nmode = w_n.size
    a = mm.mat(my_stiff.nrow, nmode)  # for eigenvectors
    vec = mm.eigs(nmode, my_stiff, my_mass, phi=a, fmin=1)
    eigval = vec.asarray()
    assert np.allclose(w_n, eigval, atol=0.1)


def test_copy2(mm):
    dim = 1000
    m2 = mm.rand(dim, dim)
    m3 = m2.copy()

    assert np.allclose(m2.asarray(), m3.asarray())


def test_dense_solver(mm):
    dim = 1000
    m2 = mm.rand(dim, dim)
    # factorize do changes inplace in m2, so we
    # need a copy to later compare.
    # factorize do changes inplace in m2, so we
    # need a copy to later compare.
    m3 = m2.copy()

    solver = mm.factorize(m2)

    v = mm.ones(dim)
    C = solver.solve(v)

    # TODO: we need to verify this works
    m3_ = m3.asarray()
    v_ = v.asarray()
    x = np.linalg.solve(m3_, v_)

    assert np.allclose(C, x)
    m3_ = m3.asarray()
    v_ = v.asarray()
    x = np.linalg.solve(m3_, v_)

    assert np.allclose(C, x)


def test_solve_py(mapdl, mm, cube_solve):
    rhs0 = mm.get_vec()
    rhs1 = mm.rhs()
    assert np.allclose(rhs0, rhs1)


@pytest.mark.parametrize(
    "vec_type", ["RHS", "BACK", pytest.param("dummy", marks=pytest.mark.xfail)]
)
def test_get_vec(mapdl, mm, cube_solve, vec_type):
    if vec_type.upper() == "BACK":
        vec = mm.get_vec(mat_id=vec_type, asarray=True)  # To test asarray arg.
        assert vec.dtype == np.int32
    else:
        vec = mm.get_vec(mat_id=vec_type).asarray()
        assert vec.dtype == np.double
    assert vec.shape


def test_get_vec_incorrect_name(mm, cube_solve):
    with pytest.raises(TypeError, match=r"``name`` parameter must be a string"):
        mm.get_vec(name=18536)


def test_get_vector(mm):
    vec = mm.ones(10)
    arr = vec.asarray()
    assert np.allclose(arr, 1)


def test_vector_add(mm):
    vec0 = mm.ones(10)
    vec1 = mm.ones(10)
    assert np.allclose(vec0 + vec1, mm.add(vec0, vec1))


def test_vector_subtract(mm):
    vec0 = mm.ones(10)
    vec1 = mm.ones(10)
    assert np.allclose(vec0 - vec1, mm.subtract(vec0, vec1))


def test_vector_neg_index(mm):
    vec = mm.ones(10)
    with pytest.raises(ValueError):
        vec[-1]


def test_vec_itruediv(mm):
    vec = mm.ones(10)
    vec /= 2
    assert np.allclose(vec, 0.5)


def test_vec_const(mm):
    vec = mm.ones(10)
    vec.const(2)
    assert np.allclose(vec, 2)


@pytest.mark.parametrize("pname", ["vector", "my_vec"])
@pytest.mark.parametrize("vec", [np.random.random(10), [1, 2, 3, 4]])
def test_set_vector(mm, vec, pname):
    ans_vec = mm.set_vec(vec, pname)
    assert np.allclose(ans_vec.asarray(), vec)
    assert "AnsMath vector size" in repr(ans_vec)
    assert "" in str(vec[0])[:4]  # output from *PRINT


def test_set_vector_catch(mm):
    with pytest.raises(ValueError, match="':' is not permitted"):
        mm.set_vec(np.ones(10), "my:vec")

    with pytest.raises(TypeError):
        mm.set_vec(np.ones(10, dtype=np.int16))

    with pytest.raises(TypeError):
        mm.set_vec(np.array([1, 2, 3], np.uint8))


def test_get_dense(mm):
    ans_mat = mm.ones(10, 10)
    assert np.allclose(ans_mat.asarray(), 1)

    ans_mat = mm.zeros(10, 10)
    assert np.allclose(ans_mat.asarray(), 0)


def test_zeros_vec(mm):
    assert isinstance(mm.zeros(10), pymath.AnsVec)


def test_get_sparse(mm):
    k = mm.stiff()
    matrix = k.asarray()
    assert isinstance(matrix, sparse.csr.csr_matrix)
    assert np.any(matrix.data)


def test_copy(mm):
    k = mm.stiff()
    kcopy = k.copy()
    assert np.allclose(k, kcopy)


def test_copy_complex(mm):
    data_a = np.random.random(10) + np.random.random(10) * 1j
    vec_a = mm.set_vec(data_a)
    data_b = vec_a.copy().asarray()
    assert data_b.dtype == data_a.dtype
    assert np.allclose(data_a, data_b)


def test_sparse_repr(mm):
    k = mm.stiff()
    assert "AnsMath sparse matrix" in repr(k)


def test_invalid_matrix_size(mm):
    mat = sparse.random(10, 9, density=0.05, format="csr")
    with pytest.raises(ValueError):
        mm.matrix(mat, "NUMPY_MAT")


def test_matrix_incorrect_name(mm, cube_solve):
    with pytest.raises(TypeError, match=r"``name`` parameter must be a string"):
        mm.matrix(np.ones((3, 3)), name=18536)


def test_transpose(mm):
    mat = sparse.random(5, 5, density=1, format="csr")
    apdl_mat = mm.matrix(mat)
    apdl_mat_t = apdl_mat.T
    assert np.allclose(apdl_mat.asarray().todense().T, apdl_mat_t.asarray().todense())


def test_dense(mm):
    # version check must be performed at runtime
    if mm._server_version[1] >= 4:
        # Test if an AnsMath object can treated as an array.
        array = np.random.random((5, 5))
        apdl_mat = mm.matrix(array)
        assert isinstance(apdl_mat, pymath.AnsMat)
        assert np.allclose(array, apdl_mat)

        with pytest.raises(TypeError):
            apdl_mat = mm.matrix(array.astype(np.uint8))

        assert "AnsMath dense matrix" in repr(apdl_mat)

        # check transpose
        assert np.allclose(apdl_mat.T, array.T)

        # check dot (vector and matrix)
        ones = mm.ones(apdl_mat.nrow)
        assert np.allclose(apdl_mat.dot(ones), np.dot(array, np.ones(5)))
        assert np.allclose(apdl_mat.dot(apdl_mat), np.dot(array, array))


def test_invalid_sparse_type(mm):
    mat = sparse.random(10, 10, density=0.05, format="csr", dtype=np.uint8)
    with pytest.raises(TypeError):
        mm._send_sparse("pytest01", mat, False, None, 100)


def test_invalid_sparse_name(mm):
    mat = sparse.random(10, 10, density=0.05, format="csr", dtype=np.uint8)
    with pytest.raises(TypeError, match="must be a string"):
        mm.matrix(mat, name=1)


def test_free_all(mm):
    my_mat1 = mm.ones(10)
    my_mat2 = mm.ones(10)
    mm.free()
    with pytest.raises(MapdlRuntimeError, match="This vector has been deleted"):
        my_mat1.size
    with pytest.raises(MapdlRuntimeError, match="This vector has been deleted"):
        my_mat2.size


def test_free_mat(mm):
    my_mat1 = mm.ones(10)
    my_mat2 = mm.ones(10)
    mm.free(my_mat1)
    assert my_mat2.size == 10
    with pytest.raises(MapdlRuntimeError, match="This vector has been deleted"):
        my_mat1.size


def test_free_mat_failing(mm):
    my_mat1 = mm.ones(10)
    arrmy_mat1 = my_mat1.asarray()
    with pytest.raises(TypeError, match="The object to delete needs to be an AnsMath object."):
        mm.free(arrmy_mat1)


def test_repr(mm):
    assert mm._status == repr(mm)


def test__load_file(mm, tmpdir):  # pragma: no cover
    # generating dummy file
    # mm._mapdl._local = True  # Uncomment to test locally.
    if not mm._mapdl._local:
        return True

    fname_ = random_string() + ".file"
    fname = str(tmpdir.mkdir("tmpdir").join(fname_))

    ## Checking non-exists
    with pytest.raises(FileNotFoundError):
        assert fname_ == mm._load_file(fname)

    with open(fname, "w") as fid:
        fid.write("# Dummy")

    ## Checking case where the file is only in python folder
    assert fname_ not in mm._mapdl.list_files()
    assert fname_ == mm._load_file(fname)
    assert fname_ in mm._mapdl.list_files()

    ## Checking case where the file is in both.
    with pytest.warns():
        assert fname_ == mm._load_file(fname)

    ## Checking the case where the file is only in the MAPDL folder
    os.remove(fname)
    assert fname_ == mm._load_file(fname)
    assert not os.path.exists(fname)
    assert fname_ in mm._mapdl.list_files()
    mm._mapdl._local = False


def test_status(mm, capsys):
    assert mm.status() is None
    captured = capsys.readouterr()
    printed_output = captured.out

    assert "APDLMATH PARAMETER STATUS-" in printed_output
    assert all([each in printed_output for each in ["Name", "Type", "Dims", "Workspace"]])

    # Checking also _status property
    assert "APDLMATH PARAMETER STATUS-" in mm._status
    assert all([each in mm._status for each in ["Name", "Type", "Dims", "Workspace"]])


def test_factorize_inplace_arg(mm):
    dim = 1000
    m2 = mm.rand(dim, dim)
    m3 = m2.copy()
    mm.factorize(m2, inplace=False)

    assert np.allclose(m2.asarray(), m3.asarray())


def test_mult(mapdl, mm):
    rand_ = np.random.rand(100, 100)

    if not server_meets_version(mm._server_version, (0, 4, 0)):
        with pytest.raises(VersionError):
            AA = mm.matrix(rand_, name="AA")

    else:
        AA = mm.matrix(rand_, name="AA")

        BB = mm.vec(size=rand_.shape[1])
        CC = mm.vec(size=rand_.shape[1], init="zeros")
        BB_trans = mm.matrix(np.random.rand(1, 100), "BBtrans")

        assert mapdl.mult(m1=AA.id, m2=BB.id, m3=CC.id)
        assert mapdl.mult(m1=BB.id, t1="Trans", m2=AA.id, m3=CC.id)
        assert mapdl.mult(m1=AA.id, m2=BB_trans.id, t2="Trans", m3=CC.id)


def test__parm(mm):
    sz = 5000
    mat = sparse.random(sz, sz, density=0.05, format="csr")

    rand_ = np.random.rand(100, 100)
    if not server_meets_version(mm._server_version, (0, 4, 0)):
        with pytest.raises(VersionError):
            AA = mm.matrix(rand_, name="AA")

    else:
        AA = mm.matrix(rand_, name="AA")
        assert AA.id == "AA"
        BB = mm.vec(size=rand_.shape[1], name="BB")
        assert BB.id == "BB"
        CC = mm.matrix(mat, "CC")
        assert CC.id == "CC"

        assert isinstance(mm._parm, dict)
        AA_parm = mm._parm["AA"]
        assert AA_parm["type"] == "DMAT"
        assert AA_parm["dimensions"] == AA.shape
        assert AA_parm["workspace"] == 1

        BB_parm = mm._parm["BB"]
        assert BB_parm["type"] == "VEC"
        assert BB_parm["dimensions"] == BB.size
        assert BB_parm["workspace"] == 1

        # Sparse matrices are made of three matrices
        assert "CC_DATA" in mm._parm
        assert "CC_IND" in mm._parm
        assert "CC_PTR" in mm._parm

        assert mm._parm["CC_DATA"]["dimensions"] == mat.indices.shape[0]
        assert mm._parm["CC_DATA"]["type"] == "VEC"
        assert mm._parm["CC_IND"]["dimensions"] == sz + 1
        assert mm._parm["CC_IND"]["type"] == "VEC"
        assert mm._parm["CC_PTR"]["dimensions"] == mat.indices.shape[0]
        assert mm._parm["CC_PTR"]["type"] == "VEC"


def test_vec2(mm):
    mm._mapdl.clear()

    assert mm._parm == {}

    # Create a new vector if no name is provided
    mm.vec(100)
    assert mm._parm != {}
    assert len(mm._parm.keys()) == 1
    name_ = list(mm._parm.keys())[0]
    parameter_ = mm._parm[name_]
    assert parameter_["type"] == "VEC"
    assert parameter_["dimensions"] == 100

    # retrieve a vector if the name is given and exists
    vec = mm.vec(10, name=name_)
    assert vec.size != 10
    assert vec.size == 100
    assert vec.id == name_

    parameter_ = mm._parm[name_]
    assert parameter_["type"] == "VEC"
    assert parameter_["dimensions"] == 100

    # Create a new vector if a name is given and doesn't exist
    vec_ = mm.vec(20, name="ASDF")
    parameter_ = mm._parm["ASDF"]
    assert parameter_["type"] == "VEC"
    assert parameter_["dimensions"] == vec_.size


def test_damp_matrix(mm, cube_with_damping):
    d = mm.damp()
    m = mm.mass()

    assert d.shape == m.shape
    assert isinstance(d, pymath.AnsMat)


def test_damp_matrix_as_array(mm, cube_with_damping):
    d = mm.damp()
    d = d.asarray()

    assert sparse.issparse(d)
    assert all([each > 0 for each in d.shape])

    d = mm.damp(asarray=True)
    assert sparse.issparse(d)
    assert all([each > 0 for each in d.shape])


@pytest.mark.parametrize("dtype_", [np.int64, np.double])
def test_damp_matrix_dtype(mm, cube_with_damping, dtype_):
    d = mm.stiff(asarray=True, dtype=dtype_)

    assert sparse.issparse(d)
    assert all([each > 0 for each in d.shape])
    assert d.dtype == dtype_

    d = mm.stiff(dtype=dtype_)
    d = d.asarray(dtype=dtype_)

    assert sparse.issparse(d)
    assert all([each > 0 for each in d.shape])
    assert d.dtype == dtype_


@pytest.fixture(scope="module")
def exit(mm):
    return mm._mapdl.exit()
