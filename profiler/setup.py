import setuptools
from distutils.core import  Extension
from distutils.command.build_ext import build_ext

with open("README.md", "r") as fh:
    long_description = fh.read()

class cbuild_ext(build_ext):
    def run(self):
        super().run()
        self.copy_file("perfmon/perfmon_int.py", f"{self.build_lib}/perfmon"),

setuptools.setup(
    cmdclass={"build_ext": cbuild_ext},
    name='performance_features',
    version='0.2.5',
    packages=['perfmon', 'profiler'],
    package_dir={ 'perfmon' : 'perfmon', 'profiler': 'profiler' },
    py_modules=['perfmon.perfmon_int', 'profiler.profiler'],
    ext_modules=[Extension('perfmon._perfmon_int',
                sources = ['perfmon/perfmon_int.i'],
                libraries = ['pfm'],
                include_dirs = ['/usr/include/perfmon'],
                swig_opts=['-I/usr/include/']),
                Extension('profiler._workload',
                  sources = ['profiler/workload.i', 'profiler/workload.cpp'],
                  libraries = ['pfm'],
                  extra_compile_args= ['-fopenmp','-std=c++11'],
                  swig_opts=['-c++'])],
    install_requires=["pandas","scipy"],
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
