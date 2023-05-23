from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize(["utils/vector.pyx", "lwe/public.pyx", "lwe/secret.pyx"])
)
