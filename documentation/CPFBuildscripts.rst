
.. _cpfbuildscripts:

CPFBuildscripts
===============

The CPFBuildscripts package provides python scripts for simplifying the CMake calls of CPF projects.
The scripts can be used for configuring and building a CPFCMake project.
CMake projects usually require calls to CMake to generate makefiles and build the project. Depending on
the project, the calls can require quite a list of arguments. The python scripts provided by the
CPFBuildscripts package use the knowledge about the structure of the CPF project to reduce the length
of those commands. It is therefore highly recommended to use the CPFBuildscripts package in combination
with the CPFCMake package.


Index
-----

.. toctree::
  :maxdepth: 1

  ../README
  0_CopyScriptsDocs
  1_ConfigureDocs
  2_GetDependenciesDocs
  3_GenerateDocs
  4_MakeDocs

