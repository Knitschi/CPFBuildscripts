
include(ccbAddPackage)
include(ccbAddRunTestsTarget)

# add a custom target that does nothing, so the files appear in the Visual Studio solution explorer.

set( PACKAGE_NAMESPACE CcbBS )
ccbInitPackageProject(
	PACKAGE_NAME
	${PACKAGE_NAMESPACE}
)

set( sources 
    run_tests.py
    0_CopyScripts.py
    1_Configure.py
    2_Generate.py
    3_Make.py
    cppcodebasebuildscripts/buildautomat.py
    cppcodebasebuildscripts/buildautomat_unit_tests.py
    cppcodebasebuildscripts/docopt.py
    cppcodebasebuildscripts/filelocations.py
    cppcodebasebuildscripts/filesystemaccess.py
    cppcodebasebuildscripts/filesystemaccess_unit_tests.py
    cppcodebasebuildscripts/miscosaccess.py
)

# add a target that only holds the files and does nothing
add_custom_target( 
    ${PACKAGE_NAME}
    SOURCES ${sources}
)
set_property( TARGET ${PACKAGE_NAME} PROPERTY FOLDER ${PACKAGE_NAME} )


# Add a runAllTests target to run the unit tests.
ccbAddRunPython3TestTarget( ${PACKAGE_NAME} run_tests.py ${sources} )



