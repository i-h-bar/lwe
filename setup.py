from distutils.core import setup
from glob import glob

from pybind11.setup_helpers import Pybind11Extension, build_ext

cpp_modules = sorted(glob("**/*.cpp"))

setup(
    cmdclass={"build_ext": build_ext},
    ext_modules=[Pybind11Extension("encoding", cpp_modules)],
)
