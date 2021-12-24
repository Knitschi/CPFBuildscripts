
include(cpfPackageProject)
include(cpfAddPythonPackageComponent)
include(cpfAddRunTestsTarget)

cpfPackageProject(
    TARGET_NAMESPACE CIConfig
	COMPONENTS SINGLE_COMPONENT
    LANGUAGES NONE
)

set( sources 
    run_tests.py
    0_CopyScripts.py
    1_Configure.py.in
    2_GetDependencies.py.in
    3_Generate.py.in
    4_Make.py.in
    python/buildautomat.py
    python/buildautomat_unit_tests.py
    python/docopt.py
    python/filelocations.py
    python/filesystemaccess.py
    python/filesystemaccess_unit_tests.py
    python/miscosaccess.py
	python/projectutils.py
    documentation/CPFBuildscripts.rst
    documentation/0_CopyScriptsDocs.rst
    documentation/1_ConfigureDocs.rst
    documentation/2_GetDependenciesDocs.rst
    documentation/3_GenerateDocs.rst
    documentation/4_MakeDocs.rst
	README.md
)

# add a target that only holds the files and does nothing
cpfAddPythonPackageComponent(
    SOURCES ${sources}
    TEST_SCRIPT run_tests.py
    # The CPFTESTS_TEST_NAME variable can be specified to run only a subset of all tests. Its value should be set in the developers config file.
    # Running only one test is useful when adding new tests.
    # Examples:
    # set( CPFTESTS_TEST_NAME "" )                                                          -> run all tests
    # set( CPFTESTS_TEST_NAME "misc_tests" )                                              -> run all tests in the misc tests module
    # set( CPFTESTS_TEST_NAME "misc_tests.ExcecuteCommandCase.test_execute_command" )     -> runs only one test function
    #
    TEST_SCRIPT_ARGUMENTS ${CPFTESTS_TEST_NAME}
)

cpfFinalizePackageProject()

