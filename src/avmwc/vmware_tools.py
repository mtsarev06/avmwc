import re
from io import IOBase, BytesIO
from time import sleep
from typing import Union, BinaryIO
from datetime import datetime
from pathlib import Path

import requests
from vmwc import vim

from . import VirtualMachine
from .archive_manager import get_archive_manager
from .exceptions import NotPerformedException


class VMWareTools:

    @property
    def tmp_path(self):
        if not self._tmp_path:
            self._tmp_path = "/tmp"
            if "win" in self.vm.summary.guest.guestId:
                self._tmp_path = self.vm._client. \
                    get_guest_operations_manager().processManager. \
                    ReadEnvironmentVariable(
                        vm=self.vm._raw_virtual_machine,
                        auth=self.vm._tools_credentials,
                        names=["TMP"]
                    )[0]
                self._tmp_path = Path(self._tmp_path[4:]).as_posix()
        return self._tmp_path
    
    @property
    def vm(self):
        return self._vm

    def __init__(self, vm):
        if not isinstance(vm, VirtualMachine):
            raise ValueError('VM must be an instance of the '
                             'avmwc.VirtualMachine class.')
        self._vm = vm
        self._tmp_path = None

    def execute_command(self, command, working_directory="", arguments="",
                        environment_variables=None, save_output=False):
        """
        Executes a command in shell or cmd.exe.

        Parameters
        ----------
        command: str
            Command to execute.
        working_directory: str
            Place where the command will be executed.
        arguments: str
            Arguments to put after the command call.
        environment_variables: list
            List of strings with environment variables to use during
            command execution.
        save_output: bool
            Whether the script should save stdout and stderr output
            to retrieve afterwards.

        Returns
        -------
        int
            ID of the created process.
        """
        platform = "win" if "win" in self.vm.summary.guest.guestId else "linux"
        arguments = " "+arguments if arguments else ""
        program_path, dummy_arg = ("cmd.exe", "cmd /c ") if platform == "win" \
            else ('.', "<( ) && ")
        if save_output:
            platform = "win" if "win" in self.vm.summary.guest.guestId \
                else "linux"
            output_tmp_path = f"{self.tmp_path}/process_output" \
                if platform == "win" else f"{self.tmp_path}/process_output"
            if not self.file_exists(output_tmp_path):
                self.create_directory(output_tmp_path)
            output_file = f"{output_tmp_path}/{Path(program_path).name}_" \
                          f"{datetime.now().timestamp()}.output"
            arguments += f" > {output_file} 2>&1" if platform == "win" \
                else f" &> {output_file}"
            if platform == "win":
                cleanup_arguments = f'ForFiles /p ' \
                                    f'"{str(Path(output_tmp_path))}" ' \
                                    f'/s /d -1 /c "cmd /c del @file"'
            else:
                cleanup_arguments = f'find {output_tmp_path}/* -name ' \
                                    f'"*.output" -mtime +1 -delete'
            self.execute_process(program_path, "", dummy_arg+cleanup_arguments)
        return self.execute_process(program_path, working_directory,
                                    dummy_arg+command+arguments,
                                    environment_variables)

    def execute_process(self, program_path, working_directory,
                        arguments="", environment_variables=None):
        """
        Absolutely the same method but returns process PID for the future work.
        """
        self.vm._ensure_vmware_tools_logged_in()

        spec = vim.vm.guest.ProcessManager.ProgramSpec(
            programPath=program_path,
            arguments=arguments,
            workingDirectory=working_directory,
            envVariables=environment_variables)

        pid = self.vm._client.get_guest_operations_manager().processManager. \
            StartProgramInGuest(vm=self.vm._raw_virtual_machine,
                                auth=self.vm._tools_credentials,
                                spec=spec)

        return pid

    def create_directory(self, path, create_parents: bool = False):
        """
        Creates a directory on the given path.

        Parameters
        ----------
        path
            Absolute path of the new directory on the virtual machine.
        create_parents: bool
            Whether the script should automatically create missing
            directories in the path.

        """
        self.vm._ensure_vmware_tools_logged_in()

        self.vm._client.get_guest_operations_manager().fileManager. \
            MakeDirectoryInGuest(
                vm=self.vm._raw_virtual_machine,
                auth=self.vm._tools_credentials,
                directoryPath=str(path),
                createParentDirectories=create_parents)

    def file_exists(self, file_path):
        """
        Checks if a file with such absolute path exists on the virtual machine.

        Parameters
        ----------
        file_path
            Absolute path to the file on the virtual machine.

        Returns
        ----------
        bool
            True if it does and False otherwise.
        """
        self.vm._ensure_vmware_tools_logged_in()

        try:
            self.vm._client.get_guest_operations_manager().fileManager.\
                ListFilesInGuest(vm=self.vm._raw_virtual_machine,
                                 auth=self.vm._tools_credentials,
                                 filePath=str(file_path))
            return True
        except vim.fault.FileNotFound:
            return False

    def delete_directory(self, path, recursive: bool = False):
        """
        Removes a directory on the virtual machine.

        Parameters
        ----------
        path
            PureWindowsPath to the directory to delete.
        recursive: bool
            Whether the script should delete everything inside
            the folder as well.

        """
        self.vm._ensure_vmware_tools_logged_in()
        self.vm._client.get_guest_operations_manager().fileManager.\
            DeleteDirectoryInGuest(
                vm=self.vm._raw_virtual_machine,
                auth=self.vm._tools_credentials,
                directoryPath=str(path),
                recursive=recursive)

    def list_path(self, path):
        """
        Lists contents of a directory with given path.

        Parameters
        ----------
        path
            PureWindowsPath to the desirable directory.

        Returns
        -------
        list[vim.vm.guest.FileManager.WindowsFileAttributes]
            List of the files in the directory.
        """
        self.vm._ensure_vmware_tools_logged_in()
        file_manager = self.vm._client.get_guest_operations_manager(). \
            fileManager
        file_objects = file_manager.ListFilesInGuest(
            vm=self.vm._raw_virtual_machine,
            auth=self.vm._tools_credentials,
            filePath=str(path)).files
        return list(file_objects)

    def get_file_attributes(self, path):
        """
        Retrieve attributes of a file or a directory on the virtual machine.

        Parameters
        ----------
        path

        Returns
        -------
        vim.vm.guest.FileManager.WindowsFileAttributes
            Attributes of the file
        """
        self.vm._ensure_vmware_tools_logged_in()
        file_manager = self.vm._client.get_guest_operations_manager(). \
            fileManager
        file_attributes = file_manager.ListFilesInGuest(
            vm=self.vm._raw_virtual_machine,
            auth=self.vm._tools_credentials,
            filePath=str(path))
        return file_attributes.files[0]

    def delete_file(self, path):
        """
        Removes a file from the virtual machine.

        Parameters
        ----------
        path
            PureWindowsPath to the file to delete.

        """
        self.vm._ensure_vmware_tools_logged_in()
        file_manager = self.vm._client.get_guest_operations_manager(). \
            fileManager
        file_manager.DeleteFileInGuest(
            vm=self.vm._raw_virtual_machine,
            auth=self.vm._tools_credentials,
            filePath=str(path))

    def archive_files(self, path_to_files: Union[str, list], archive_path: str,
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
            Explicitly set the resulting archive type. If not passed,
            the function tries to recognize archive type
            by resulting archive name extension.
        """
        archive_manager = get_archive_manager(self.vm)
        archive_manager.archive(path_to_files, archive_path,
                                password, archive_type)

    def extract_archive(self, path_to_archive: str, path_to_extract: str,
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
            the function tries to recognize archive type
            by passed archive name extension.
        """
        archive_manager = get_archive_manager(self.vm)
        archive_manager.extract(path_to_archive, path_to_extract,
                                password, archive_type)

    def login(self, username, password):
        return self.vm.vmware_tools_login(username, password)

    def upload_file(self, local_file_path: Union[str, BinaryIO],
                    remote_file_path: str):
        if not isinstance(local_file_path, IOBase):
            return self.vm.vmware_tools_upload_file(local_file_path,
                                                    remote_file_path)

        self.vm._ensure_vmware_tools_logged_in()

        data = local_file_path.read()

        file_attributes = vim.vm.guest.FileManager.FileAttributes()
        url = self.vm._client.get_guest_operations_manager().fileManager. \
            InitiateFileTransferToGuest(
                vm=self.vm._raw_virtual_machine,
                auth=self.vm._tools_credentials,
                guestFilePath=remote_file_path,
                fileAttributes=file_attributes,
                fileSize=len(data),
                overwrite=True)

        url = self.vm._normalize_url(url)
        r = requests.put(url, data=data, verify=False)
        r.raise_for_status()

    def download_file(self, local_file_path: Union[str, BinaryIO],
                      remote_file_path: str, chunk_size=1024):
        """
        Downloads a file from the remote machine.

        Parameters
        ----------
        local_file_path: Union[str, BinaryIO]
            Path to save the downloaded file. IO object can also be
            used as a receiver.
        remote_file_path: str
            Path to a remote file to download
        chunk_size: int
            Size of a chunk used in download.

        Returns
        -------
        int
            Size of the downloaded file
        """
        if not isinstance(local_file_path, IOBase):
            return self.vm.vmware_tools_download_file(local_file_path,
                                                      remote_file_path,
                                                      chunk_size)

        self.vm._ensure_vmware_tools_logged_in()

        platform = "win" if "win" in self.vm.summary.guest.guestId else "linux"
        remote_file_path = str(Path(remote_file_path)) if platform == "win" \
            else Path(remote_file_path).as_posix()

        fti = self.vm._client.get_guest_operations_manager().fileManager. \
            InitiateFileTransferFromGuest(
                vm=self.vm._raw_virtual_machine,
                auth=self.vm._tools_credentials,
                guestFilePath=str(remote_file_path))

        url = self.vm._normalize_url(fti.url)
        r = requests.get(url, verify=self.vm._client.verify)
        r.raise_for_status()

        size = 0

        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                local_file_path.write(chunk)
                size += len(chunk)

        return size

    def create_temporary_directory(self, prefix, suffix=""):
        return self.vm.vmware_tools_create_temporary_directory(prefix, suffix)

    def list_processes(self, pids=None, max_retries=5, retry_delay_seconds=5):
        return self.vm.vmware_tools_list_processes(pids, max_retries,
                                                   retry_delay_seconds)

    def get_process_info(self, pid: int):
        """
        Returns process info of a process with passed pid.

        Parameters
        ----------
        pid: int
            PID of a process to get info of.
        Returns
        -------
        vim.vm.guest.ProcessManager.ProcessInfo
            Information about the process.
        """
        matched_process = self.list_processes(pids=[pid])
        if not matched_process:
            raise Exception(f'There is no process with such pid ({pid}).')
        return matched_process[0]

    def get_process_exit_code(self, pid: int, timeout: int = 60):
        """
        Waits when the process with passed pid finishes work and
        returns it's exit code.

        Parameters
        ----------
        pid: int
            Process ID
        timeout: int
            How long to wait for the process to finish it's work in seconds.
        Returns
        -------
        int
            Exit code.
        """
        while self.get_process_info(pid).exitCode is None and timeout:
            sleep(1)
            timeout -= 1
            if timeout == 0:
                raise Exception("Couldn't retrieve the process "
                                "exit code (timeout).")
        return self.list_processes([pid])[0].exitCode

    def get_process_output(self, pid: int):
        """
        Returns stdout and stderr output of the process, if it was saved.
        You have to pass "save_output=True" to the
        execute_command method to get this working.

        Parameters
        ----------
        pid: int
            ID of the process to get output of.

        Returns
        -------
        bytes
            stdout or stderr output of the process.
        """
        process_info = self.get_process_info(pid)
        remote_output_file = re.search(">\s?([^\s]*\\.output).*",
                                       process_info.cmdLine)
        if not remote_output_file or \
                not self.file_exists(remote_output_file[1]):
            raise NotPerformedException(f"Either the process with pid {pid} "
                                        f"wasn't run with save_output=True, "
                                        f"or it's not finished yet.")
        output_object = BytesIO()
        self.download_file(output_object, remote_output_file[1])
        return output_object.getvalue()
