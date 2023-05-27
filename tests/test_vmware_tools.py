import os
from unittest import TestCase

from src.avmwc import VMWareClient
from src.avmwc.exceptions import NotPerformedException


class TestVMWareTools(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vcenter_host = os.environ.get('VCENTER_HOST')
        vcenter_login, vcenter_password = os.environ.get('VCENTER_LOGIN'), \
                                          os.environ.get('VCENTER_PASSWORD')
        cls.client = VMWareClient(vcenter_host,
                                  vcenter_login, vcenter_password).__enter__()
        cls.vm = cls.client.get_virtual_machine("test-win-1")
        cls.vm.vmware_tools.login("Admin", "0")
        cls.work_dir = "C:\\tests"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def test_file_operations(self):
        test_file_path = "C:\\tests\\test_file.txt"
        file = open(test_file_path, "w")
        file.write('123')
        file.close()

        self.vm.vmware_tools.upload_file(test_file_path,
                                         self.work_dir+"\\test_file.txt")
        self.assertTrue(self.vm.vmware_tools.
                        file_exists(self.work_dir+"\\test_file.txt"))

        try:
            attributes = self.vm.vmware_tools.\
                get_file_attributes(self.work_dir+"\\test_file.txt")
        except Exception:
            self.fail(f"Haven't managed to get file "
                      f"attributes of a uploaded file: {attributes}")

        self.assertEqual(attributes.size, os.stat(test_file_path).st_size)

        self.vm.vmware_tools.archive_files(self.work_dir+"\\test_file.txt",
                                           self.work_dir+"\\test_file.txt.zip")
        self.assertTrue(self.vm.vmware_tools.
                        file_exists(self.work_dir+"\\test_file.txt.zip"))

        self.vm.vmware_tools.\
            extract_archive(self.work_dir+"\\test_file.txt.zip",
                            self.work_dir+"\\extracted")
        self.assertTrue(self.vm.vmware_tools.
                        file_exists(self.work_dir +
                                    "\\extracted\\test_file.txt"))
        self.vm.vmware_tools.\
            delete_file(self.work_dir + "\\extracted\\test_file.txt")
        self.assertFalse(self.vm.vmware_tools.
                         file_exists(self.work_dir +
                                     "\\extracted\\test_file.txt"))
        self.vm.vmware_tools.delete_directory(self.work_dir + "\\extracted")
        self.assertFalse(self.vm.vmware_tools.
                         file_exists(self.work_dir + "\\extracted"))

        self.vm.vmware_tools.delete_file(self.work_dir+"\\test_file.txt.zip")
        self.assertFalse(self.vm.vmware_tools.
                         file_exists(self.work_dir + "\\test_file.txt.zip"))

        self.vm.vmware_tools.delete_file(self.work_dir+"\\test_file.txt")
        self.assertFalse(self.vm.vmware_tools.
                         file_exists(self.work_dir + "\\test_file.txt"))
        os.remove(test_file_path)

    def test_save_output(self):
        pid = self.vm.vmware_tools.\
            execute_command('echo testing', save_output=True)
        self.assertEqual(self.vm.vmware_tools.get_process_exit_code(pid), 0)
        self.assertEqual(b'testing \r\n',
                         self.vm.vmware_tools.get_process_output(pid))

        pid = self.vm.vmware_tools.execute_command('echo testing',
                                                   save_output=False)
        self.assertEqual(self.vm.vmware_tools.get_process_exit_code(pid), 0)
        self.assertRaises(NotPerformedException,
                          self.vm.vmware_tools.get_process_output, pid)

        pid = self.vm.vmware_tools.execute_command('tarzip testing',
                                                   save_output=True)
        self.assertEqual(self.vm.vmware_tools.get_process_exit_code(pid), 1)
        self.assertTrue('tarzip' in self.vm.vmware_tools.
                        get_process_output(pid).decode("OEM"))


