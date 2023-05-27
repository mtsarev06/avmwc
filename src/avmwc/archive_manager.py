import os
from typing import Union
from pathlib import Path
from abc import ABCMeta, abstractmethod

from . import VirtualMachine, vim
from .exceptions import ArchivingError, ExtractionError


class ArchiveManager(metaclass=ABCMeta):
    """
    Abstract class for implementing archive managers
    for different operation systems.

    Attributes
    ----------
    _vm: VirtualMachine
        Instance of virtual machine to work with.

    Methods
    ----------
    archive(path_to_files: Union[str, list],
            archive_path: str, archive_type: str = None)
        Archives files or a directories with passed path. You can also send
        a single path to a file to archive. Wildcards are supported.
        If archive_type is not passed, the script will try to automatically
        recognize archive type by resulting archive extension.
    extract(path_to_archive: str, archive_type: str = None)
        Extracts an archive with passed path.
        If archive_type is not passed, the script will automatically recognize
        archive type using it's extension.
    """
    _vm = None
    _os_name = None

    def __init__(self, virtual_machine: VirtualMachine):
        if not self._os_name:
            raise ValueError(f"OS name isn't provided in the "
                             f"class {self.__class__.__name__}")
        if not isinstance(virtual_machine, VirtualMachine):
            raise TypeError('To initiate an instance of ArchiveManager '
                            'you should pass a virtual machine instance.')
        self._vm = virtual_machine
        self._check_os()
        self._check_if_environment_is_ready()

    @property
    def vm(self):
        return self._vm

    def archive(self, path_to_files: Union[str, list], archive_path: str,
                password: str = None, archive_type: str = None):
        """
        Create an archive on the connected virtual machine with passed files.

        Parameters
        ----------
        path_to_files: Union[str, list]
            Path or list of paths to files which are to be put in the archive.
        archive_path: str
            Where to save the resulting archive.
        password: str
            If passed, sets this password to the archive if possible.
        archive_type: str
            Explicitly sets the resulting archive type. If not passed,
            the function tries to recognize archive type by resulting
            archive name extension.

        """
        if not isinstance(path_to_files, list):
            path_to_files = [path_to_files]

        archive_type = ''.join(Path(archive_path).suffixes) \
            if not archive_type else archive_type

        archive_method = None
        if "tar.gz" in archive_type:
            pass
        elif "tar" in archive_type:
            archive_method = self._archive_into_tar
        elif "zip" in archive_type:
            archive_method = self._archive_into_zip
        if not archive_method:
            raise NotImplementedError(f"{self.__class__.__name__} is not able "
                                      f"to archive files into {archive_type} "
                                      f"archive.")

        return archive_method(path_to_files=path_to_files,
                              archive_path=archive_path,
                              password=password)

    def extract(self, path_to_archive: str, path_to_extract: str,
                password: str = None, archive_type: str = None):
        """
        Extracts an archive on the connected virtual machine with passed files.

        Parameters
        ----------
        path_to_archive: str
            Path to the archive to extract on the virtual machine.
        path_to_extract: str
            Where to extract selected archive.
        password: str
            If passed, tries to decrypt the archive with
            the password if possible.
        archive_type: str
            Explicitly sets the resulting archive type. If not passed,
            the function tries to recognize archive type by passed
            archive name extension.
        """

        if not isinstance(path_to_archive, str):
            path_to_archive = str(path_to_archive)

        archive_type = ''.join(Path(path_to_archive).suffixes) \
            if not archive_type else archive_type

        extract_method = None
        if "tar" in archive_type:
            extract_method = self._extract_from_tar
        if "zip" in archive_type:
            extract_method = self._extract_from_zip
        if not extract_method:
            raise NotImplementedError(f"{self.__class__.__name__} is not able "
                                      f"to extract an archive of "
                                      f"{archive_type} type")

        return extract_method(path_to_archive=path_to_archive,
                              path_to_extract=path_to_extract,
                              password=password)

    def _check_os(self):
        """
        Checks whether OS of connected virtual machine
        is compatible with the current archive manager.

        Raises
        -------
        EnvironmentError
            Operating system of the connected virtual machine
            isn't compatible with the current archive manager.
        """
        if not self._os_name:
            raise ValueError(f"OS name isn't provided in "
                             f"the class {self.__class__.__name__}")
        if self._os_name not in self.vm.summary.guest.guestId:
            raise EnvironmentError(f'Operating system '
                                   f'{self.vm.summary.guest.guestId} of the '
                                   f'passed virtual machine is not compatible '
                                   f'with {self.__class__.__name__}')

    @abstractmethod
    def _archive_into_zip(self, path_to_files: list, archive_path: str,
                          password: str, **kwargs):
        """
        Implements a way to archive files into zip archive.

        Parameters
        ----------
        path_to_files: list
            List of files to put into the archive.
        archive_path: str
            Resulting path of the created archive.
        password: str
            Password to set on the archive

        """
        raise NotImplementedError()

    @abstractmethod
    def _archive_into_tar(self, path_to_files: list, archive_path: str,
                          **kwargs):
        """
        Implements a way to archive files into tar archive.

        Parameters
        ----------
        path_to_files: list
            List of files to put into the archive.
        archive_path: str
            Resulting path of the created archive.

        """
        raise NotImplementedError()

    @abstractmethod
    def _extract_from_zip(self, path_to_archive: str, path_to_extract: str,
                          password: str, **kwargs):
        """
        Implements a way to extract files from zip archive.

        Parameters
        ----------
        path_to_archive: list
            Path to the archive to extract from.
        path_to_extract: str
            Path to extract files from the archive.
        password: str
            Password used to decrypt the archive.

        """
        raise NotImplementedError()

    @abstractmethod
    def _extract_from_tar(self, path_to_archive: str, path_to_extract: str,
                          **kwargs):
        """
        Implements a way to extract files from zip archive.

        Parameters
        ----------
        path_to_archive: list
            Path to the archive to extract from.
        path_to_extract: str
            Path to extract files from the archive.

        """
        raise NotImplementedError()

    @abstractmethod
    def _check_if_environment_is_ready(self):
        """
        Checks whether the environment of the connected VM is ready
        to work with the current ArchiveManager.

        Raises
        ---------
        EnvironmentError
            If environment isn't ready for the ArchiveManager.
        """
        raise EnvironmentError("Environment of the virtual machine isn't "
                               "ready for working with ArchiveManager.")


class WindowsArchiveManager(ArchiveManager):
    _os_name = "win"
    _exe_name = None

    def _archive_into_zip(self, path_to_files: list, archive_path: str,
                          password: str, **kwargs):
        password = "-p" + password if password else ""
        cmd_path_argument = " ".join(path_to_files)
        cmd = f"cmd /c {self._exe_name} a -y -tzip {archive_path} " \
              f"{cmd_path_argument} {password}"
        pid = self.vm.vmware_tools.\
            execute_process(program_path="C:\\Windows\\System32\\cmd.exe",
                            working_directory=None,
                            arguments=cmd)
        exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
        if exit_code != 0:
            raise ArchivingError(f'There was an error archiving '
                                 f'{cmd_path_argument}: exit code '
                                 f'{exit_code}.')

    def _archive_into_tar(self, path_to_files: list, archive_path: str,
                          **kwargs):
        cmd_path_argument = " ".join(path_to_files)
        cmd = f"cmd /c {self._exe_name} a -y -ttar {archive_path} " \
              f"{cmd_path_argument}"
        pid = self.vm.vmware_tools.\
            execute_process(program_path="C:\\Windows\\System32\\cmd.exe",
                            working_directory=None,
                            arguments=cmd)
        exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
        if exit_code != 0:
            raise ArchivingError(f'There was an error archiving '
                                 f'{cmd_path_argument}: exit code '
                                 f'{exit_code}.')

    def _extract_from_zip(self, path_to_archive: str, path_to_extract: str,
                          password: str, **kwargs):
        path_to_extract = path_to_extract if path_to_extract else \
            os.path.dirname(path_to_archive)
        password = "-p" + password if password else ""

        cmd = f"cmd /c {self._exe_name} x {path_to_archive} -y " \
              f"-o{path_to_extract} {password}"
        pid = self.vm.vmware_tools.\
            execute_process(program_path="C:\\Windows\\System32\\cmd.exe",
                            working_directory=None, arguments=cmd)
        exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
        if exit_code != 0:
            raise ExtractionError(f'There was an error extracting zip'
                                  f' archive {path_to_archive} to '
                                  f'{path_to_extract} (exit code '
                                  f'{exit_code}).')

    def _extract_from_tar(self, path_to_archive: str, path_to_extract: str,
                          **kwargs):
        path_to_extract = path_to_extract if path_to_extract else \
            os.path.dirname(path_to_archive)

        cmd = f"cmd /c {self._exe_name} x {path_to_archive} -y " \
              f"-ttar -o{path_to_extract}"
        pid = self.vm.vmware_tools.\
            execute_process(program_path="C:\\Windows\\System32\\cmd.exe",
                            working_directory=None,
                            arguments=cmd)
        exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
        if exit_code != 0:
            raise ExtractionError(f'There was an error extracting zip archive '
                                  f'({path_to_archive} to {path_to_extract} '
                                  f'(exit code {exit_code}).')

    def _check_if_environment_is_ready(self):
        possible_exe_names = ['7za', '7z', '7zg']
        for exe_name in possible_exe_names:
            pid = self.vm.vmware_tools.\
                execute_process('C:\\Windows\\System32\\cmd.exe', '',
                                f'cmd /c {exe_name}')
            exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
            if exit_code == 0:
                self._exe_name = exe_name
                return True
        raise EnvironmentError(f'There is no 7zip installed on the virtual '
                               f'machine {self.vm}. Please, install it before '
                               f'using WindowsArchiveManager.')


class DebianArchiveManager(ArchiveManager):
    _os_name = "debian"

    def _archive_into_zip(self, path_to_files: list, archive_path: str,
                          password: str, **kwargs):
        password = "--password " + password if password else " "
        for file_to_archive in path_to_files:
            file_path = Path(file_to_archive)
            pid = self.vm.vmware_tools.\
                execute_process(program_path="/usr/bin/zip",
                                working_directory=file_path.parent.as_posix(),
                                arguments=f"-ur {archive_path} "
                                          f"{file_path.name} {password}")
            exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
            if exit_code != 0:
                raise ArchivingError(f'There was an error adding '
                                     f'{file_path.as_posix()} to the archive '
                                     f'{archive_path} (exit code {exit_code})')

    def _archive_into_tar(self, path_to_files: list, archive_path: str,
                          **kwargs):
        for file_to_archive in path_to_files:
            file_path = Path(file_to_archive)
            pid = self.vm.vmware_tools.\
                execute_process(program_path="/usr/bin/tar",
                                working_directory=file_path.parent.as_posix(),
                                arguments=f"-rvf {archive_path} "
                                          f"{file_path.name}")
            exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
            if exit_code != 0:
                raise ArchivingError(f'There was an error adding '
                                     f'{file_path.as_posix()} to the archive '
                                     f'{archive_path} (exit code {exit_code})')

    def _extract_from_zip(self, path_to_archive: str, path_to_extract: str,
                          password: str, **kwargs):
        password = "--password " + password if password else " "
        pid = self.vm.vmware_tools.\
            execute_process(program_path="/usr/bin/unzip",
                            working_directory=None,
                            arguments=f"{path_to_archive} -d "
                                      f"{path_to_extract} {password}")
        exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
        if exit_code != 0:
            raise ExtractionError(f'There was an error extracting from '
                                  f'{path_to_archive} to {path_to_extract} '
                                  f'(exit code {exit_code})')

    def _extract_from_tar(self, path_to_archive: str, path_to_extract: str,
                          **kwargs):
        pid = self.vm.vmware_tools.\
            execute_process(program_path="/usr/bin/tar",
                            working_directory=None,
                            arguments=f"-xf {path_to_archive} -C "
                                      f"{path_to_extract} ")
        exit_code = self.vm.vmware_tools.get_process_exit_code(pid)
        if exit_code != 0:
            raise ExtractionError(f'There was an error extracting from '
                                  f'{path_to_archive} to {path_to_extract} '
                                  f'(exit code {exit_code})')

    def _check_if_environment_is_ready(self):
        programs_to_check = ['zip', 'unzip']
        for program in programs_to_check:
            try:
                self.vm.vmware_tools.\
                    execute_process(program_path=f"/usr/bin/{program}",
                                    working_directory=None)
            except vim.fault.FileNotFound:
                raise EnvironmentError(f'There is no {program} installed on '
                                       f'the virtual machine. Please install '
                                       f'it before using '
                                       f'DebianArchiveManager.')


def get_archive_manager(vm: VirtualMachine) -> ArchiveManager:
    """
    Returns an archive manager for the corresponding
    OS of the passed virtual machine.

    Parameters
    ----------
    vm: VirtualMachine
        Instance of virtual machine for matching
        an appropriate ArchiveManager to.

    Returns
    ----------
    ArchiveManager
        ArchiveManager for the OS of passed virtual machine.

    Raises
    ----------
    EnvironmentError
        OS of the passed virtual machine isn't
        compatible with implemented archive managers.
    """

    available_managers = {
        "win": WindowsArchiveManager,
        "debian": DebianArchiveManager
    }

    vm_os = vm.summary.guest.guestId

    for manager in available_managers:
        if manager in vm_os:
            return available_managers[manager](vm)

    raise EnvironmentError(f"There is no ArchiveManager implemented for OS "
                           f"of the passed virtual machine ({vm_os})")
