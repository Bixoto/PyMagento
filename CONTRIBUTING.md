# Contributing to PyMagento

First, thank you for wanting to contribute to PyMagento!

Feel free to open a pull-request if you found a typo or a small bug in the code.

If you want to make more substantial changes, please open an issue first to explain your ideas.

## Making a release

1. Update the CHANGELOG
2. Update the version in `pyproject.toml` and in `magento/version.py`
3. Commit and tag with `v` followed by the version (e.g. `git tag v1.1.1`)
4. Push (without the tag) and wait for the [CI job][ci1] to succeed
5. Push the tag
6. Wait for the [CI job][ci2] to finish

[ci1]: https://github.com/Bixoto/PyMagento/actions/workflows/build.yml
[ci2]: https://github.com/Bixoto/pymagento/actions/workflows/publish.yml
