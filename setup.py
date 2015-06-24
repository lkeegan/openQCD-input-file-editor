from setuptools import setup

setup(name='openQCD-input-file-editor',
      version='0.1',
      description='An input file editor with a graphical user interface for the openQCD lattice QCD simulation program',
      url='http://lkeegan.github.io/openQCD-input-file-editor/',
      author='Liam Keegan',
      author_email='liam.r.g.keegan@gmail.com',
      license='MIT',
      packages=['openqcd_input_file_editor'],
      scripts=['bin/openQCD-input-file-editor'],
      zip_safe=False)
