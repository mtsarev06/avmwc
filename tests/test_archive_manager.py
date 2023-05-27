import os
from pathlib import Path
from unittest import TestCase

from src.avmwc import VMWareClient
from src.avmwc.archive_manager import (WindowsArchiveManager,
                                       DebianArchiveManager)


class TestWindowsArchiveManager(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vcenter_host = os.environ.get('VCENTER_HOST')
        vcenter_login, vcenter_password = os.environ.get('VCENTER_LOGIN'), \
                                          os.environ.get('VCENTER_PASSWORD')
        vm_login, vm_password = os.environ.get('VM_LOGIN'), \
                                os.environ.get('VM_PASSWORD')
        if not vcenter_host or not vcenter_login or not vcenter_password or \
                not vm_login or not vm_password:
            raise EnvironmentError('Please set VCENTER_HOST, VCENTER_LOGIN '
                                   'and VCENTER_PASSWORD environment '
                                   'variables to preform testing')
        cls._vcenter_client = VMWareClient(vcenter_host, 
                                           vcenter_login, 
                                           vcenter_password).__enter__()
        cls._test_vm_debian = cls._vcenter_client.\
            get_virtual_machine("test_debian")
        cls._test_vm_debian.vmware_tools.login("debian", "0")
        cls._test_vm_win = cls._vcenter_client.\
            get_virtual_machine("test-win")
        cls._test_vm_win.vmware_tools.login("Admin", "0")

        if cls._test_vm_win.vmware_tools.\
                file_exists("C:\\tests\\test_archive_manager"):
            cls._test_vm_win.vmware_tools.\
                delete_directory("C:\\tests\\test_archive_manager", True)
        cls._test_vm_win.vmware_tools.\
            create_directory("C:\\tests\\test_archive_manager", 
                             create_parents=True)
        cls._test_vm_win.vmware_tools.\
            create_directory("C:\\tests\\test_archive_manager\\inner_dir")
        cls._test_vm_win.vmware_tools.\
            execute_process("cmd.exe", "C:\\tests\\test_archive_manager", 
                            "cmd /c echo|set /p=\"123 \" > 1.txt")
        cls._test_vm_win.vmware_tools.\
            execute_process("cmd.exe", 
                            "C:\\tests\\test_archive_manager\\inner_dir", 
                            "cmd /c echo|set /p=\"123 \" > 2.txt")
        cls._test_vm_win.vmware_tools.\
            execute_process("cmd.exe", 
                            "C:\\tests\\test_archive_manager\\inner_dir", 
                            "cmd /c echo|set /p=\"123 \" > 3.txt")

        if cls._test_vm_debian.vmware_tools.\
                file_exists("/home/debian/test_archive_manager"):
            cls._test_vm_debian.vmware_tools.\
                delete_directory("/home/debian/test_archive_manager", True)
        cls._test_vm_debian.vmware_tools.\
            create_directory("/home/debian/test_archive_manager", 
                             create_parents=True)
        cls._test_vm_debian.vmware_tools.\
            create_directory("/home/debian/test_archive_manager/inner_dir")
        cls._test_vm_debian.vmware_tools.\
            execute_process("/usr/bin/echo",
                            "/home/debian/test_archive_manager",
                            "123 > 1.txt")
        cls._test_vm_debian.vmware_tools.\
            execute_process("/usr/bin/echo", 
                            "/home/debian/test_archive_manager/inner_dir",
                            "123 > 2.txt")
        cls._test_vm_debian.vmware_tools.\
            execute_process("/usr/bin/echo", 
                            "/home/debian/test_archive_manager/inner_dir", 
                            "123 > 3.txt")


    @classmethod
    def tearDownClass(cls) -> None:
        cls._test_vm_win.vmware_tools.\
            delete_directory("C:\\tests\\test_archive_manager", True)
        cls._test_vm_debian.vmware_tools.\
            delete_directory("/home/debian/test_archive_manager", True)
        cls._vcenter_client.__exit__(None, None, None)

    def test_init(self):
        self.assertRaises(TypeError, WindowsArchiveManager, None)
        self.assertRaises(EnvironmentError, WindowsArchiveManager, 
                          self._test_vm_debian)
        self.assertRaises(EnvironmentError, DebianArchiveManager, 
                          self._test_vm_win)
        try:
            WindowsArchiveManager(self._test_vm_win)
            DebianArchiveManager(self._test_vm_debian)
        except Exception as error:
            self.fail(f'There was an error initializing a '
                      f'WindowsArchiveManager object: {error}')

    def test_windows_archive_manager(self):
        archive_manager = WindowsArchiveManager(self._test_vm_win)
        work_dir = "C:\\tests\\test_archive_manager\\"
        self.functionality_testing(self._test_vm_win, archive_manager,
                                   work_dir)
        self.password_testing(self._test_vm_win, archive_manager, work_dir)

    def test_debian_archive_manager(self):
        archive_manager = DebianArchiveManager(self._test_vm_debian)
        work_dir = "/home/debian/test_archive_manager"
        self.functionality_testing(self._test_vm_debian, archive_manager,
                                   work_dir)

    def functionality_testing(self, test_vm, archive_manager, work_dir):
        test_data = [
            (Path(work_dir, "1.txt").as_posix(),
             Path(work_dir, "1.zip").as_posix(), ["1.txt"]),
            (Path(work_dir, "inner_dir").as_posix(),
             Path(work_dir, "2.zip").as_posix(), ["inner_dir"]),
            (Path(work_dir, "inner_dir", "*").as_posix(),
             Path(work_dir, "3.zip").as_posix(), ["2.txt", "3.txt"]),
            ([Path(work_dir, "1.txt").as_posix(),
              Path(work_dir, "inner_dir", "*").as_posix()],
             Path(work_dir, "4.zip").as_posix(), ["1.txt", "2.txt", "3.txt"]),

            (Path(work_dir, "1.txt").as_posix(),
             Path(work_dir, "1.tar").as_posix(), ["1.txt"]),
            (Path(work_dir, "inner_dir").as_posix(),
             Path(work_dir, "2.tar").as_posix(), ["inner_dir"]),
            (Path(work_dir, "inner_dir", "*").as_posix(),
             Path(work_dir, "3.tar").as_posix(), ["2.txt", "3.txt"]),
            ([Path(work_dir, "1.txt").as_posix(),
              Path(work_dir, "inner_dir", "*").as_posix()],
             Path(work_dir, "4.tar").as_posix(), ["1.txt", "2.txt", "3.txt"])
        ]
        for data in test_data:
            file_to_archive = data[0]
            archive_path = data[1]
            archive_manager.archive(file_to_archive, archive_path)
            self.assertTrue(test_vm.vmware_tools.file_exists(archive_path))
            self.assertTrue(test_vm.vmware_tools.
                            get_file_attributes(archive_path).size)

        for data in test_data:
            test_vm.vmware_tools.\
                create_directory(Path(work_dir, "extraction").as_posix())
            archive_path = data[1]
            expected_files = data[2]
            archive_manager.extract(archive_path,
                                    Path(work_dir, "extraction").as_posix())
            extraction_file_list = test_vm.vmware_tools.\
                list_path(Path(work_dir, "extraction").as_posix())
            extraction_file_names_list = [os.path.basename(file.path)
                                          for file in extraction_file_list]

            for file in expected_files:
                if file not in extraction_file_names_list:
                    self.fail(f"Expected file {file} of the archive "
                              f"{archive_path} either wasn't in archive or "
                              f"extraction process failed.")
                extracted_file_attributes = test_vm.vmware_tools.\
                    get_file_attributes(Path(work_dir, "extraction", file).
                                        as_posix())
                if extracted_file_attributes.type != "directory":
                    self.assertEqual(extracted_file_attributes.size, 4)
            test_vm.vmware_tools.\
                delete_directory(Path(work_dir, "extraction").as_posix(),
                                 recursive=True)

    def password_testing(self, test_vm, archive_manager, work_dir):
        file_to_archive = Path(work_dir, '*').as_posix(),
        archive_path = Path(work_dir, "passworded_archive.zip").as_posix()
        archive_manager.archive(file_to_archive, archive_path, password="123")
        pid = test_vm.vmware_tools.\
            execute_process(program_path="C:\\Windows\\System32\\cmd.exe",
                            working_directory=work_dir,
                            arguments=f"cmd /c {archive_manager._exe_name} "
                                      f"l -slt passworded_archive.zip | "
                                      f"findstr \"Encrypted\" | findstr \"+\"")
        exit_code = test_vm.vmware_tools.get_process_exit_code(pid)
        self.assertEqual(exit_code, 0)
