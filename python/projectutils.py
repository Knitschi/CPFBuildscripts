
from . import miscosaccess



def get_version_from_repository(cpfRootDir, cpfCMakeDir, package = None):
    """
    Runs the getVersionFromRepository.cmake in order to get the version of a package or build-project repository.
    """

    osa = miscosaccess.MiscOsAccess()
    repo_dir = cpfRootDir
    if package:
        repo_dir = repo_dir.joinpath('Sources/{0}'.format(package))
    script = cpfRootDir / cpfCMakeDir / 'Scripts/getVersionFromRepository.cmake'

    return osa.execute_command_output(
        'cmake -DREPO_DIR="{0}" -P "{1}"'.format(repo_dir, script),
        cwd=cpfRootDir,
        print_output=miscosaccess.OutputMode.ON_ERROR,
        print_command=False
    )[0]