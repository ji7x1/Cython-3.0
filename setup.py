from Cython.Build import cythonize
from setuptools import Extension, setup

setup(
    ext_modules=cythonize(
        [Extension("fastmath._core", ["src/fastmath/_core.pyx"])],
        compiler_directives={"language_level": "3"},
    ),
)
