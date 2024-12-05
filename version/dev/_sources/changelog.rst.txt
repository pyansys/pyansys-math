.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the PyAnsys Math project.

.. vale off

.. towncrier release notes start

`0.2.0 <https://github.com/ansys/pyansys-math/releases/tag/v0.2.0>`_ - 2024-10-08
=================================================================================

Changed
^^^^^^^

- chore: update CHANGELOG for v0.1.5 `#328 <https://github.com/ansys/pyansys-math/pull/328>`_
- maint: adding `update-changelog` as a CICD dependency `#329 <https://github.com/ansys/pyansys-math/pull/329>`_
- [pre-commit.ci] pre-commit autoupdate `#351 <https://github.com/ansys/pyansys-math/pull/351>`_
- maint: implement `ansys/actions/check-vulnerabilities` in CICD `#355 <https://github.com/ansys/pyansys-math/pull/355>`_
- maint: bump docker/login-action from 3.1.0 to 3.2.0 in the actions group `#356 <https://github.com/ansys/pyansys-math/pull/356>`_
- maint: bump docker/login-action from 3.2.0 to 3.3.0 in the actions group `#388 <https://github.com/ansys/pyansys-math/pull/388>`_


Fixed
^^^^^

- fix: adding a waiting time for MAPDL service to start `#354 <https://github.com/ansys/pyansys-math/pull/354>`_


Dependencies
^^^^^^^^^^^^

- maint: bump pyvista from 0.43.5 to 0.43.6 `#331 <https://github.com/ansys/pyansys-math/pull/331>`_
- maint: bump pytest from 8.1.1 to 8.2.0 `#332 <https://github.com/ansys/pyansys-math/pull/332>`_
- maint: bump jupyterlab from 4.1.6 to 4.1.8 `#333 <https://github.com/ansys/pyansys-math/pull/333>`_
- maint: bump sphinx-gallery from 0.15.0 to 0.16.0 `#334 <https://github.com/ansys/pyansys-math/pull/334>`_
- maint: bump pyvista[jupyter,trame] from 0.43.5 to 0.43.6 `#335 <https://github.com/ansys/pyansys-math/pull/335>`_
- maint: bump pyvista from 0.43.6 to 0.43.7 `#337 <https://github.com/ansys/pyansys-math/pull/337>`_
- maint: bump pyvista[jupyter,trame] from 0.43.5 to 0.43.7 `#338 <https://github.com/ansys/pyansys-math/pull/338>`_
- maint: bump jupyterlab from 4.1.8 to 4.2.0 `#339 <https://github.com/ansys/pyansys-math/pull/339>`_
- maint: bump pytest from 8.2.0 to 8.2.1 `#341 <https://github.com/ansys/pyansys-math/pull/341>`_
- maint: bump pyvista from 0.43.7 to 0.43.8 `#342 <https://github.com/ansys/pyansys-math/pull/342>`_
- maint: bump ansys-sphinx-theme from 0.15.2 to 0.16.0 `#343 <https://github.com/ansys/pyansys-math/pull/343>`_
- maint: bump pyvista[jupyter,trame] from 0.43.7 to 0.43.8 `#344 <https://github.com/ansys/pyansys-math/pull/344>`_, `#357 <https://github.com/ansys/pyansys-math/pull/357>`_
- maint: bump jupyterlab from 4.2.0 to 4.2.1 `#346 <https://github.com/ansys/pyansys-math/pull/346>`_
- maint: bump sphinx-design from 0.5.0 to 0.6.0 `#347 <https://github.com/ansys/pyansys-math/pull/347>`_
- maint: bump pyansys-tools-report from 0.7.0 to 0.7.3 `#348 <https://github.com/ansys/pyansys-math/pull/348>`_
- maint: bump sphinx-notfound-page from 1.0.0 to 1.0.2 `#349 <https://github.com/ansys/pyansys-math/pull/349>`_
- maint: bump scipy from 1.13.0 to 1.13.1 `#350 <https://github.com/ansys/pyansys-math/pull/350>`_
- maint: bump trame from 3.6.0 to 3.6.2 `#358 <https://github.com/ansys/pyansys-math/pull/358>`_
- maint: bump ansys-sphinx-theme from 0.16.0 to 0.16.5 `#359 <https://github.com/ansys/pyansys-math/pull/359>`_
- maint: bump pytest from 8.2.1 to 8.2.2 `#360 <https://github.com/ansys/pyansys-math/pull/360>`_
- maint: bump pyvista[jupyter,trame] from 0.43.8 to 0.43.9 `#361 <https://github.com/ansys/pyansys-math/pull/361>`_, `#366 <https://github.com/ansys/pyansys-math/pull/366>`_
- maint: bump pyvista from 0.43.8 to 0.43.9 `#362 <https://github.com/ansys/pyansys-math/pull/362>`_
- maint: bump jupyterlab from 4.2.1 to 4.2.2 `#363 <https://github.com/ansys/pyansys-math/pull/363>`_
- maint: bump sphinx-autodoc-typehints from 2.1.0 to 2.1.1 `#364 <https://github.com/ansys/pyansys-math/pull/364>`_
- maint: bump numpy from 1.26.4 to 2.1.2 `#367 <https://github.com/ansys/pyansys-math/pull/367>`_
- maint: bump sphinx-autodoc-typehints from 2.1.1 to 2.2.2 `#369 <https://github.com/ansys/pyansys-math/pull/369>`_
- maint: bump pyvista[jupyter,trame] from 0.43.9 to 0.43.10 `#370 <https://github.com/ansys/pyansys-math/pull/370>`_
- maint: bump pyvista from 0.43.9 to 0.43.10 `#371 <https://github.com/ansys/pyansys-math/pull/371>`_
- maint: bump ansys-sphinx-theme from 0.16.5 to 0.16.6 `#372 <https://github.com/ansys/pyansys-math/pull/372>`_
- maint: bump jupyterlab from 4.2.2 to 4.2.3 `#374 <https://github.com/ansys/pyansys-math/pull/374>`_
- maint: bump vtk from 9.3.0 to 9.3.1 `#375 <https://github.com/ansys/pyansys-math/pull/375>`_
- maint: bump trame from 3.6.2 to 3.6.3 `#376 <https://github.com/ansys/pyansys-math/pull/376>`_
- maint: bump scipy from 1.13.1 to 1.14.0 `#379 <https://github.com/ansys/pyansys-math/pull/379>`_
- maint: bump pyvista from 0.43.10 to 0.44.0 `#380 <https://github.com/ansys/pyansys-math/pull/380>`_
- maint: bump ansys-mapdl-core from 0.68.1 to 0.68.4 `#383 <https://github.com/ansys/pyansys-math/pull/383>`_
- maint: bump pytest from 8.2.2 to 8.3.1 `#384 <https://github.com/ansys/pyansys-math/pull/384>`_
- maint: bump sphinx-gallery from 0.16.0 to 0.17.0 `#385 <https://github.com/ansys/pyansys-math/pull/385>`_
- maint: bump sphinx-autodoc-typehints from 2.2.2 to 2.2.3 `#386 <https://github.com/ansys/pyansys-math/pull/386>`_
- maint: bump pyvista from 0.44.0 to 0.44.1 `#387 <https://github.com/ansys/pyansys-math/pull/387>`_
- maint: bump pytest from 8.3.1 to 8.3.2 `#390 <https://github.com/ansys/pyansys-math/pull/390>`_
- maint: bump sphinx-notfound-page from 1.0.2 to 1.0.4 `#391 <https://github.com/ansys/pyansys-math/pull/391>`_
- maint: bump pyvista[jupyter,trame] from 0.44.0 to 0.44.1 `#393 <https://github.com/ansys/pyansys-math/pull/393>`_
- maint: bump jupyterlab from 4.2.3 to 4.2.4 `#396 <https://github.com/ansys/pyansys-math/pull/396>`_
- maint: bump numpydoc from 1.7.0 to 1.8.0 `#397 <https://github.com/ansys/pyansys-math/pull/397>`_
- maint: bump sphinx-gallery from 0.17.0 to 0.17.1 `#398 <https://github.com/ansys/pyansys-math/pull/398>`_
- maint: bump pyansys-tools-report from 0.7.3 to 0.8.0 `#400 <https://github.com/ansys/pyansys-math/pull/400>`_
- maint: bump ansys-sphinx-theme from 1.0.3 to 1.0.5 `#401 <https://github.com/ansys/pyansys-math/pull/401>`_
- maint: bump ansys-sphinx-theme from 1.0.5 to 1.0.7 `#402 <https://github.com/ansys/pyansys-math/pull/402>`_
- maint: bump scipy from 1.14.0 to 1.14.1 `#404 <https://github.com/ansys/pyansys-math/pull/404>`_
- maint: bump sphinx-autodoc-typehints from 2.2.3 to 2.3.0 `#406 <https://github.com/ansys/pyansys-math/pull/406>`_
- maint: bump jupyterlab from 4.2.4 to 4.2.5 `#407 <https://github.com/ansys/pyansys-math/pull/407>`_
- maint: bump sphinx-autobuild from 2024.4.16 to 2024.9.3 `#408 <https://github.com/ansys/pyansys-math/pull/408>`_
- maint: bump pytest from 8.3.2 to 8.3.3 `#409 <https://github.com/ansys/pyansys-math/pull/409>`_
- maint: bump trame from 3.6.3 to 3.6.5 `#410 <https://github.com/ansys/pyansys-math/pull/410>`_
- maint: bump ansys-sphinx-theme from 1.0.7 to 1.0.9 `#411 <https://github.com/ansys/pyansys-math/pull/411>`_
- maint: bump ansys-mapdl-reader from 0.53.0 to 0.54.1 `#412 <https://github.com/ansys/pyansys-math/pull/412>`_
- maint: bump ansys-sphinx-theme from 1.0.9 to 1.0.11 `#413 <https://github.com/ansys/pyansys-math/pull/413>`_
- maint: bump sphinx-autodoc-typehints from 2.3.0 to 2.4.4 `#414 <https://github.com/ansys/pyansys-math/pull/414>`_
- maint: bump sphinx-autobuild from 2024.9.3 to 2024.9.19 `#415 <https://github.com/ansys/pyansys-math/pull/415>`_
- maint: bump sphinx-autobuild from 2024.9.19 to 2024.10.3 `#421 <https://github.com/ansys/pyansys-math/pull/421>`_
- maint: bump ansys-sphinx-theme from 1.0.11 to 1.1.2 `#422 <https://github.com/ansys/pyansys-math/pull/422>`_


Miscellaneous
^^^^^^^^^^^^^

- [pre-commit.ci] pre-commit autoupdate `#336 <https://github.com/ansys/pyansys-math/pull/336>`_, `#340 <https://github.com/ansys/pyansys-math/pull/340>`_, `#345 <https://github.com/ansys/pyansys-math/pull/345>`_, `#365 <https://github.com/ansys/pyansys-math/pull/365>`_, `#368 <https://github.com/ansys/pyansys-math/pull/368>`_, `#373 <https://github.com/ansys/pyansys-math/pull/373>`_, `#377 <https://github.com/ansys/pyansys-math/pull/377>`_, `#382 <https://github.com/ansys/pyansys-math/pull/382>`_, `#389 <https://github.com/ansys/pyansys-math/pull/389>`_, `#394 <https://github.com/ansys/pyansys-math/pull/394>`_, `#399 <https://github.com/ansys/pyansys-math/pull/399>`_, `#405 <https://github.com/ansys/pyansys-math/pull/405>`_, `#416 <https://github.com/ansys/pyansys-math/pull/416>`_, `#424 <https://github.com/ansys/pyansys-math/pull/424>`_


Documentation
^^^^^^^^^^^^^

- maint: bump sphinx from 7.3.7 to 8.0.2 `#392 <https://github.com/ansys/pyansys-math/pull/392>`_


Maintenance
^^^^^^^^^^^

- maint: bump ansys/actions from 6 to 7 in the actions group `#395 <https://github.com/ansys/pyansys-math/pull/395>`_
- ci: updating supported Python versions `#420 <https://github.com/ansys/pyansys-math/pull/420>`_
- maint: bump ansys/actions from 7 to 8 in the actions group `#423 <https://github.com/ansys/pyansys-math/pull/423>`_
- maint: updating ``CONTRIBUTORS.md`` and ``AUTHORS`` files `#425 <https://github.com/ansys/pyansys-math/pull/425>`_

`0.1.5 <https://github.com/ansys/pyansys-math/releases/tag/v0.1.5>`_ - 2024-04-22
=================================================================================

Changed
^^^^^^^

- chore: update CHANGELOG for v0.1.4 `#325 <https://github.com/ansys/pyansys-math/pull/325>`_
- ci: establish stage dependencies for release `#327 <https://github.com/ansys/pyansys-math/pull/327>`_


Miscellaneous
^^^^^^^^^^^^^

- docs: title level for release notes `#326 <https://github.com/ansys/pyansys-math/pull/326>`_

`0.1.4 <https://github.com/ansys/pyansys-math/releases/tag/v0.1.4>`_ - 2024-04-22
=================================================================================

Added
^^^^^

- feat: implementing `ansys/actions/doc-changelog` `#316 <https://github.com/ansys/pyansys-math/pull/316>`_


Changed
^^^^^^^

- doc: adding release notes in documentation `#324 <https://github.com/ansys/pyansys-math/pull/324>`_


Fixed
^^^^^

- fix: updating CICD (Vale, MAPDL image) `#322 <https://github.com/ansys/pyansys-math/pull/322>`_
- fix: removing `md` Vale checks `#323 <https://github.com/ansys/pyansys-math/pull/323>`_


Dependencies
^^^^^^^^^^^^

- maint: bump sphinx-autodoc-typehints from 2.0.0 to 2.1.0 `#317 <https://github.com/ansys/pyansys-math/pull/317>`_
- maint: bump ansys-sphinx-theme from 0.15.0 to 0.15.2 `#318 <https://github.com/ansys/pyansys-math/pull/318>`_
- maint: bump sphinx-autobuild from 2024.4.13 to 2024.4.16 `#319 <https://github.com/ansys/pyansys-math/pull/319>`_
- maint: bump sphinx from 7.2.6 to 7.3.7 `#320 <https://github.com/ansys/pyansys-math/pull/320>`_
- maint: bump jupyterlab from 4.1.5 to 4.1.6 `#321 <https://github.com/ansys/pyansys-math/pull/321>`_

.. vale on
