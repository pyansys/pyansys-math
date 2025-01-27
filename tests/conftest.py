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

import os
from pathlib import Path

import pytest

# import time

pytest_plugins = ["pytester"]

from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core._version import SUPPORTED_ANSYS_VERSIONS
from ansys.mapdl.core.errors import MapdlExitedError
from ansys.mapdl.core.launcher import MAPDL_DEFAULT_PORT, get_start_instance
from ansys.tools.path import find_ansys

# Check if MAPDL is installed
# NOTE: checks in this order to get the newest installed version


valid_rver = SUPPORTED_ANSYS_VERSIONS.keys()

EXEC_FILE, rver = find_ansys()
if rver:
    rver = int(rver * 10)
    HAS_GRPC = int(rver) >= 211 or ON_CI
else:
    # assuming remote with gRPC
    HAS_GRPC = True

# Cache if gRPC MAPDL is installed.
#
# minimum version on linux.  Windows is v202, but using v211 for consistency
# Override this if running on CI/CD and PYMAPDL_PORT has been specified
ON_CI = "PYMAPDL_START_INSTANCE" in os.environ and "PYMAPDL_PORT" in os.environ


# determine if we can launch an instance of MAPDL locally
# start with ``False`` and always assume the remote case
LOCAL = [False]

# check if the user wants to permit pytest to start MAPDL
START_INSTANCE = get_start_instance()

if os.name == "nt":
    os_msg = """SET PYMAPDL_START_INSTANCE=False
SET PYMAPDL_PORT=<MAPDL Port> (default 50052)
SET PYMAPDL_IP=<MAPDL IP> (default 127.0.0.1)"""
else:
    os_msg = """export PYMAPDL_START_INSTANCE=False
export PYMAPDL_PORT=<MAPDL Port> (default 50052)
export PYMAPDL_IP=<MAPDL IP> (default 127.0.0.1)"""

ERRMSG = f"""Unable to run unit tests without MAPDL installed or
accessible.  Either install Ansys 2021R1 or newer or specify the
remote server with:

{os_msg}

If you do have Ansys installed, you may have to patch pymapdl to
automatically find your Ansys installation.  Email the developer at:
alexander.kaszynski@ansys.com

"""

if START_INSTANCE and EXEC_FILE is None:
    raise RuntimeError(ERRMSG)


@pytest.fixture(scope="session", params=LOCAL)
def mapdl(request, tmpdir_factory):
    # don't use the default run location as tests run multiple unit testings
    run_path = str(tmpdir_factory.mktemp("ansys"))

    # don't allow mapdl to exit upon collection unless mapdl is local
    cleanup = START_INSTANCE

    if request.param:
        # usage of a just closed channel on same port causes connectivity issues
        port = MAPDL_DEFAULT_PORT + 10
    else:
        port = MAPDL_DEFAULT_PORT

    mapdl = launch_mapdl(
        EXEC_FILE,
        override=True,
        run_location=run_path,
        cleanup_on_exit=cleanup,
    )
    mapdl._show_matplotlib_figures = False  # CI: don't show matplotlib figures

    if HAS_GRPC:
        mapdl._local = request.param  # CI: override for testing

    if mapdl._local:
        assert Path(mapdl.directory) == Path(run_path)
        assert mapdl._distributed

    # using yield rather than return here to be able to test exit
    yield mapdl

    ###########################################################################
    # test exit: only when allowed to start PYMAPDL
    ###########################################################################
    if START_INSTANCE:
        mapdl._local = True
        mapdl.exit()
        assert mapdl._exited
        assert "MAPDL exited" in str(mapdl)

        if mapdl._local:
            assert not os.path.isfile(mapdl._lockfile)

        # should test if _exited protects from execution
        with pytest.raises(MapdlExitedError):
            mapdl.prep7()

        # actually test if server is shutdown
        if HAS_GRPC:
            with pytest.raises(MapdlExitedError):
                mapdl._send_command("/PREP7")
            with pytest.raises(MapdlExitedError):
                mapdl._send_command_stream("/PREP7")

            # verify PIDs are closed
            # time.sleep(1)  # takes a second for the processes to shutdown
            # for pid in mapdl._pids:
            #     assert not check_pid(pid)


@pytest.fixture(scope="function")
def cleared(mapdl):
    mapdl.finish(mute=True)
    # *MUST* be NOSTART.  With START fails after 20 calls...
    # this has been fixed in later pymapdl and MAPDL releases
    mapdl.clear("NOSTART", mute=True)
    mapdl.prep7(mute=True)
    yield


@pytest.fixture(scope="function")
def cube_solve(cleared, mapdl):
    # setup the full file
    mapdl.block(0, 1, 0, 1, 0, 1)
    mapdl.et(1, 186)
    mapdl.esize(0.5)
    mapdl.vmesh("all")

    # Define a material (nominal steel in SI)
    mapdl.mp("EX", 1, 210e9)  # Elastic moduli in Pa (kg/(m*s**2))
    mapdl.mp("DENS", 1, 7800)  # Density in kg/m3
    mapdl.mp("NUXY", 1, 0.3)  # Poisson's Ratio

    # solve first 10 non-trivial modes
    out = mapdl.modal_analysis(nmode=10, freqb=1)
