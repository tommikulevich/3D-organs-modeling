import os
import threading


class MainAlgorithm:
    def __init__(self):
        self.input_path = None
        self.output_path = None
        self.filter_kernel = None

    def startAlgorithm(self, input_path, output_path, filter_kernel):
        self.input_path = input_path
        self.output_path = output_path
        self.filter_kernel = filter_kernel

        thread_serv = threading.Thread(target=self.startServer)
        thread_slicer = threading.Thread(target=self.startSlicer)
        thread_slicer.start()
        thread_serv.start()

    @staticmethod
    def startServer():
        os.system(f'python.exe ./Lib/monailabel/main.py start_server --app apps/radiology --studies myData1 --conf models deepedit')

    def startSlicer(self):
        path = os.getcwd()
        file_to_search = 'commands.py'

        with open(file_to_search, 'r') as file:
            file_data = file.read().split('\n')

        file_data[0] = f'dicomDataDir= "{self.input_path}"'
        file_data[1] = f'outputFolder= "{self.output_path}"'
        file_data = '\n'.join(file_data)

        with open(file_to_search, 'w') as file:
            file.write(file_data)

        absolute_path = os.path.join(path, "commands.py")
        os.system(f'cd Slicer 5.2.1 & '
                  f'Slicer.exe --python-script "{absolute_path}"')
