---
okf_version: "0.2"
---
# OKF bundle — `glom`

OKF v0.2 progressive-disclosure knowledge for `glom`.

## Start here

* [Repository overview](./repo.md) - test command, layout and modules

## Modules

* [glom](./modules/glom.md) - internal helpers with no public API
* [glom.__main__](./modules/glom.__main__.md) - internal helpers with no public API
* [glom._version](./modules/glom._version.md) - internal helpers with no public API
* [glom.cli](./modules/glom.cli.md) - Provides a command-line interface to the glom library, enabling nested data access and restructuring using Python-powered specs directly from the shell. It supp
* [glom.core](./modules/glom.core.md) - glom.core is the heart of the glom package, built around the central glom() function for accessing and transforming nested data. It defines the core specifier t
* [glom.grouping](./modules/glom.grouping.md) - The `glom.grouping` module implements "Group mode," a glom dispatch mode that aggregates collections of values through nested, combinable operations like Avg, F
* [glom.matching](./modules/glom.matching.md) - The `glom.matching` module provides inline data validation and pattern matching capabilities within glom specs, allowing engineers to confirm target data matche
* [glom.mutation](./modules/glom.mutation.md) - The glom.mutation module provides in-place mutation capabilities for glom, complementing the library's default behavior of safely returning transformed copies o
* [glom.reduction](./modules/glom.reduction.md) - The glom.reduction module provides specifier types and helper functions for reducing and aggregating iterables in data, including counting elements, flattening 
* [glom.streaming](./modules/glom.streaming.md) - The `glom.streaming` module provides specifier types for incrementally processing streaming targets (e.g., database rows, file lines) without excessive memory u
* [glom.tutorial](./modules/glom.tutorial.md) - The glom.tutorial module is a runnable, interactive tutorial that teaches engineers how to use glom for nested data access and transformation through executable

## Function pages

150 function contracts under `functions/`.