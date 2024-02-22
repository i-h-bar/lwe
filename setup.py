import shutil
import sys
import pybind11
from setuptools import setup, Extension

shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("lwe.egg-info", ignore_errors=True)

sys.argv.append("build_ext")
sys.argv.append("--inplace")
cpp_modules = ["lwe/lwe.cpp"]

ext_modules = [
    Extension(
        'lwe.lwe',
        cpp_modules,
        include_dirs=[pybind11.get_include()],
        language='c++'
    )
]

setup(
    ext_modules=ext_modules
)
