import setuptools
from distutils.core import  Extension

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='performance_features',
    version='0.1.2',
    packages=['perfmon', 'profiler'],
    package_dir={ 'perfmon' : 'perfmon', 'profiler': 'profiler' },
    py_modules=['perfmon.perfmon_int', 'profiler.profiler'],
    ext_modules=[Extension('perfmon._perfmon_int',
                sources = ['perfmon/perfmon_int.i'],
                libraries = ['pfm'],
                include_dirs = ['perfmon/include/'],
                swig_opts=['-Iperfmon/include/']),
                Extension('profiler._workload',
                  sources = ['profiler/workload.i', 'profiler/workload.cpp'],
                  libraries = ['pfm'],
                  extra_compile_args= ['-fopenmp'],
                  swig_opts=['-c++'])],
    author="Vitor Ramos",
    author_email="ramos.vitor89@gmail.com",
    description="perf event wrapper for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VitorRamos/performance_features",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
)
