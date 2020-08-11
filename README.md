# Apache Pony Mail Unit Tests Repository

The aim of this repository is to create a comprehensive suite of tests for ensuring 
that changes to the Pony Mail codebase does not impact stability and reproducibility.

The repository is split into three main directories:

- `tests/`: The python test scripts
- `yaml/`: The test specifications
- `corpus/`: The test corpus (data input to be used during tests)

The root directory has a `runall.py`, which will run all tests it can find in the 
yaml directory, and summarize the results at the end. You may also run individual 
tests from the tests directory (more on that as we build out the test dir).

