#!/usr/bin/env python

# Copyright 2010 by Philipp Kraft
# This file is part of cmf.
#
#   cmf is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   cmf is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with cmf.  If not, see <http://www.gnu.org/licenses/>.
#   

# This file can build and install cmf
import sys
import os

# Change these variables to match your compiler. (gcc or 
# For Visual Studio 2008 no action is needed
msvc = sys.platform == 'win32'
gcc = not msvc

# Change these pathes to your sundials 2.4+ installation

# Change this path to your boost installation (not needed for gcc)

boost_path = os.environ.get('BOOSTDIR',r"..\boost_1_41_0")


# No user action required beyond this point
import datetime
import shutil
from distutils.core import setup,Extension
from distutils.version import LooseVersion as Version
try:
    # Import a function to get a path to the include directories of numpy
    from numpy import get_include as get_numpy_include
except ImportError:
    raise RuntimeError("For building and running of cmf an installation of numpy is needed")

if "swig" in sys.argv:
    swig=True
    sys.argv.remove("swig")
else:
    swig=False
if "noopenmp" in sys.argv:
    openmp=False
    sys.argv.remove("noopenmp")
else:
    openmp=True

def count_lines(files):
    lcount=0
    for fn in files:
        if not fn.endswith('.c'):
            lines = file(fn).readlines()
            lcount+=len(lines)
    return lcount
def is_source_file(fn,include_headerfiles=False):
    fn=fn.lower()
    res = False
    res = res or fn.endswith('.cpp')
    res = res or fn.endswith('.c')
    res = res or fn.endswith('.cc')
    res = res or (include_headerfiles and fn.endswith('.h'))
    res = res or (include_headerfiles and fn.endswith('.hpp'))
    return res
def make_cmf_core():
    include_dirs=[os.path.join(*'cmf/cmf_core_src/math/integrators/sundials_cvode/include'.split('/'))]
    include_dirs += [get_numpy_include()]
    libraries=None
    if msvc:
        include_dirs += [boost_path,boost_path+r"\boost\tr1"]
        compile_args = ["/EHsc",r'/Fd"build\vc90.pdb"',"/D_SCL_SECURE_NO_WARNINGS", "/D_CRT_SECURE_NO_WARNINGS","/MP"]
        if openmp: compile_args.append("/openmp")
        link_args=["/DEBUG"]
    if gcc: 
        compile_args=['-Wno-comment','-Wno-reorder','-Wno-unused','-Wno-sign-compare']
        if openmp: compile_args.append('-fopenmp')
        link_args=["-fopenmp"] if openmp else None
        libraries = ['gomp'] if openmp else None
    cmf_files=[]
    cmf_headers=[]
    for root,dirs,files in os.walk('cmf/cmf_core_src'):
        if os.path.basename(root)!='debug_scripts':
            cmf_files.extend(os.path.join(root,f) for f in files if is_source_file(f) and f!='cmf_wrap.cpp')
            cmf_headers.extend(os.path.join(root,f) for f in files if f.endswith('.h'))
    print "Compiling %i source files" % (len(cmf_files)+1)
    if swig:
        cmf_files.append("cmf/cmf_core_src/cmf.i")
    else:
        cmf_files.append("cmf/cmf_core_src/cmf_wrap.cpp")
    print "Total number of C++ loc:", count_lines(cmf_files + cmf_headers)
    cmf_core = Extension('cmf._cmf_core',
                            sources=cmf_files,
                            libraries = libraries,
                            include_dirs=include_dirs,
                            extra_compile_args=compile_args,
                            extra_link_args=link_args,
                            swig_opts=['-c++','-Wextra','-w512','-w511','-O','-keyword','-castmode'] #,'-threads'
                        )
    return cmf_core
def make_raster():
    if swig:
        files=['cmf/raster/raster_src/raster.i']
    else:
        files=['cmf/raster/raster_src/raster_wrap.cpp']
 
    if msvc: 
        compile_args = ["/EHsc",r'/Fd"build\vc90.pdb"',"/MP"]
        if openmp: compile_args.append("/openmp")
        link_args=["/DEBUG"]
        libraries=None
    if gcc: 
        compile_args=['-Wno-comment','-Wno-reorder','-Wno-unused','-Wno-sign-compare']
        if openmp: compile_args.append('-fopenmp')
        link_args=["-fopenmp"] if openmp else None
        libraries = ['gomp'] if openmp else None
    raster = Extension('cmf.raster._raster',
                        sources=files,
                        libraries = libraries,
                        extra_compile_args=compile_args,
                        extra_link_args=link_args,
                        swig_opts=['-c++','-Wextra','-w512','-w511','-keyword','-castmode','-O','-threads']
                    )
    return raster
def get_revision():
    pipe = os.popen('svnversion')
    res=pipe.read().strip()
    if ':' in res:
        res=res.split(':')[-1]
    return res.strip('M')
def updateversion(revision):
    if revision:
        module_code = file('cmf/__init__.py').readlines()
        fout = file('cmf/__init__.py','w')
        for line in module_code:
            if line.startswith('__version__'):
                fout.write("__version__ = '%s'\n" % revision)
            else:
                fout.write(line)
        doxycode = file('Doxyfile').readlines()
        fout = file('Doxyfile','w')
        for line in doxycode:
            if line.strip().startswith('PROJECT_NUMBER'):
                fout.write("PROJECT_NUMBER         = %s\n" % revision)
            else:
                fout.write(line)
if __name__=='__main__':
    
    ext = [make_raster(),make_cmf_core()]
    author = "Philipp Kraft"
    author_email = "philipp.kraft@umwelt.uni-giessen.de"
    url = "www.uni-giessen.de/ilr/frede/cmf"
    description="""
    cmf extends Python by hydrological objects. The objects of the framework, allows the user to create a wide range
    of hydrological models using Python.
    This version was compiled on %s
    """ % datetime.datetime.now().strftime('%d. %b %Y (%H:%M)')
    py=[]
    for root,dirs,files in os.walk('cmf'):
        for d in dirs:
            if d.endswith('_src'):
                dirs.remove(d)
        py_found=[os.path.join(root,f[:-3]).replace('\\','.') for f in files if f.endswith('.py')]
        if py_found:
            print 'In %s %i modules found' % (root,len(py_found))
        py.extend(py_found)
    revision = get_revision()
    if 'build' in sys.argv or 'build_py' in sys.argv:
        updateversion(revision)
    now = datetime.datetime.now()
    setup(name='cmf',
          version='0.' + revision,
          license='GPL',
          ext_modules=ext,
          py_modules=py, 
          requires=['shapely (>=1.0)'],
          author=author,
          url=url,
          description=description,
          author_email=author_email)
    #if msvc: shutil.copy('build/lib.win32-2.7/cmf/raster/_raster.pyd','cmf/raster/')
    #setup(name='cmf_setups',version='0.1',license='GPL',
    #      py_modules=['cmf_setups.'+f[:-3] for f in os.listdir('cmf_setups') if f.endswith('.py')])
    print "build ok"
