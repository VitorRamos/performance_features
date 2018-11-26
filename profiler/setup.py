from distutils.core import setup, Extension
from distutils.command.install_data import install_data

setup(name='profiler',
      version='0.1',
      author='Vitor Ramos',
      author_email='ramos.vitor89@gmail.com',
      description='perf event wrapper for python',
      packages=['profiler'],
      package_dir={ 'profiler' : 'src' },
      py_modules=['profiler.profiler'],
      ext_modules=[Extension('profiler._workload',
                  sources = ['src/workload.i', 'src/workload.cpp'],
                  libraries = ['pfm'],
                  swig_opts=['-c++'])])
