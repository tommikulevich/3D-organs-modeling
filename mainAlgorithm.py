import os
import threading
import sys
import fileinput
class MainAlgorithm:
    def __init__(self):
        pass

    def startAlgorithm(self, input_path, output_path):
        print(f"Test starting algorithm. Example input: '{input_path}'. Example output: '{output_path}'")
        thread_serv = threading.Thread(target=self.startServer)
        thread_slicer = threading.Thread(target=self.startSlicer, args=(input_path, output_path,))
        thread_slicer.start()
        thread_serv.start()

    def startServer(self):

        #os.system('cd Slicer 5.2.1 & cd bin & PythonSlicer.exe -m monailabel start_server --app apps/radiology --studies myData1 --conf models deepedit"')
        os.system('cd Slicer 5.2.1 & cd bin & monailabel start_server --app apps/radiology --studies myData1 --conf models deepedit"')
        # os.system('dir')
        # os.system('cd bin')
        #
        # os.system('PythonSlicer.exe -m monailabel start_server --app apps/radiology --studies myData1 --conf models deepedit"')

    def startSlicer(self, input_path, output_path):
        path = os.getcwd()
        fileToSearch = 'commands.py'
        with open(fileToSearch, 'r') as file:
            filedata = file.read().split('\n')

        filedata[0] = f'dicomDataDir= "{input_path}"'
        filedata[1] = f'outputFolder= "{output_path}"'
        filedata = '\n'.join(filedata)

        with open(fileToSearch, 'w') as file:
            file.write(filedata)
        absolute_path = os.path.join(path, "commands.py")
        os.system(f'cd Slicer 5.2.1 & Slicer.exe --python-script {absolute_path}')
        #os.system('Slicer.exe --python-script "commands.py"')