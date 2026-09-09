# Shardy

Shardy is an MLIR-based tensor partitioning system for all dialects. Built from
the collaboration of both the [GSPMD](https://arxiv.org/abs/2105.04663) and
[PartIR](https://arxiv.org/abs/2401.11202) teams, it incorporates the best of
both systems, and the shared experience of both teams and users.

Shardy is meant to be dialect agnostic and provide extensive user control and
debuggability features. It includes an axis-based sharding representation, a set
of compiler APIs, functionality for sharding propagation, and plans for an SPMD
partitioner.

## Documentation

Official Documentation: <https://openxla.org/shardy>

For more information see the docs directory.

## Status

Shardy is a work in progress. Currently the core dialect and C bindings are
fully functional. The Python bindings are under development.

## Contacts

Currently we are not accepting contributions directly to the GitHub repository.

If you still wish to contribute, please contact the maintainers - maintainers at
openxla.org

## Build instructions

Here's how to build the Shardy repo on Linux or macOS:

1.  Bazel is our primary build tool, so before you begin make sure that you have
    it installed.

    ```sh
    # On Linux
    sudo apt install bazel

    # On macOS
    brew install bazel
    ```

2.  Clone the Shardy repo:

    ```sh
    git clone https://github.com/openxla/shardy
    cd shardy
    ```

3.  Update the
    [bazel lockfile](https://bazel.build/versions/7.7.0/external/lockfile), if
    necessary:

    ```sh
    bazel mod deps --lockfile_mode=update
    ```

4.  Build Shardy:

    ```sh
    bazel build -c opt --lockfile_mode=error shardy/...
    ```

5.  Now you can make sure it works by running some tests:

    ```sh
    bazel test -c opt --test_output=errors shardy/...
    ```

## Using Shardy with JAX

If you'd like to build JAX with a modified version of Shardy, you can find
instructions at
https://jax.readthedocs.io/en/latest/developer.html#building-jaxlib-from-source-with-a-modified-xla-repository.
