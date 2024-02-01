import sys
from distutils.core import setup
from distutils.extension import Extension
import pybind11

sys.argv.append("build_ext")
sys.argv.append("--inplace")
cpp_modules = ["lwe/utils/encoding.cpp"]

ext_modules = [
    Extension(
        'lwe.encoding',
        cpp_modules,
        include_dirs=[pybind11.get_include()],
        language='c++'
    )
]

setup(
    ext_modules=ext_modules
)
