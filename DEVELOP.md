## Basic workflow
The version is taken from the git tags, so if you are in the commit with a "1.0.1" tag, then the 1.0.1 version will be used.
If you are in between tags, then the last digit will be increased and a "devXXX" string will be appended.
For specifics, check [setuptools_scm](https://kandi.openweaver.com/python/pypa/setuptools_scm).

To publish a new release/packages to pypi, use tox:
```
TWINE_PASSWORD="$(awk '/^\[pypi\]/,/^$/ { if ($1 == "password") {print $3}}' ~/.pypirc)" tox -e release
```
(note: it's currently not publishing packages to pypi, but it creates them inside `dist/`, so it is subsequently possible to manually run `twine upload dist/*`)

## References
Check the [skeleton blog post](https://blog.jaraco.com/skeleton/)
You can check MarkDown online via [stackedit](https://stackedit.io/app)
