import numpy
from Cython.Compiler.Options import get_directive_defaults
from Cython.Distutils import Extension
from setuptools import setup

directive_defaults = get_directive_defaults()

directive_defaults['profile'] = True
directive_defaults["linetrace"] = True
directive_defaults["language_level"] = 3
directive_defaults['binding'] = True

extensions = [
    Extension(
        path[:-4].replace("/", "."), [path], include_dirs=[numpy.get_include()], define_macros=[("CYTHON_TRACE", "1")]
    )
    for path in ["lwe/public.pyx", "lwe/secret.pyx"]
]

setup(
    ext_modules=extensions
)
