Advanced VMWC
==========

Package which extends and improves functionality of VMWC library.
You can work with AVMWC the same way you do it with VMWC.

## Modifications

1. **VirtualMachine.vmware_tools_execute_process** - the function returns 
   PID of the started process.
   
## New functionality

All default and new methods starting with **vmware_tools_** are now available 
via **vmware_tools** attribute.

1. **VirtualMachine.vmware_tools.create_directory(path, create_parents = False)** - 
   creates a directory in the provided *path*. If *create_parents = True* provided, 
   absent directories in the path are created as well automatically.
2. **VirtualMachine.vmware_tools.delete_directory(path, recursive = False)** - 
   deletes a directory specified by *path*. If *recursive = True* provided, 
   subdirectories are deleted as well.
3. **VirtualMachine.vmware_tools.file_exists(path)** - checks if a file with
   such *path* exists. If it does, returns True, and False otherwise.
4. **VirtualMachine.vmware_tools.delete_file(path)** - deletes a file with
   specified *path*.
5. **VirtualMachine.vmware_tools.get_file_attributes(path)** - retrieve 
   attribute of a file with specified *path*.
6. **VirtualMachine.vmware_tools.list_path(path)** - Returns file list of 
   specified directory.
7. **VirtualMachine.vmware_tools.archive(path, archive_path = None, password = None)** - 
   Tries to archive a file or a directory with specified *path* with *password*, if
   necessary, and stores the archive to the *archive_path*.
8. **VirtualMachine.vmware_tools.extract_archive(archive_path, extract_path = None, password = None)** - 
   Extract contents of an archive with specified *archive_path* (using *password* to decrypt 
   it, if necessary) to the specified *extract_path*.
9. **VirtualMachine.vmware_tools.extract_archive_into_one_file(archive_path, extract_path, password = None)** - 
   Extract contents of an archive with specified *path* (using *password*, if 
   necessary) into one file with **extract_path**.
10. **VirtualMachine.vmware_tools.execute_command(command, working_directory="", 
   arguments="", environment_variables=None, save_output=False)** -  Execute a 
   command in shell or cmd.exe.
11. **VirtualMachine.vmware_tools.get_process_info(pid)** - Retrieve information
   of a process with provided *pid*.
12. **VirtualMachine.vmware_tools.get_process_exit_code(pid, timeout=60)** - 
   Waits for the process with *pid* to finish work and returns the exit code.
13. **VirtualMachine.vmware_tools.get_process_output(pid)** - 
   Returns stdout and stderr output of the process, if it was saved by using
   *save_output=True* in execute_command method.
