"""Internal YAML serialization, CSV loading, and experiment data saving.

Copyright (c) 2024 Cleland Lab. Licensed under the MIT License; see LICENSE.
"""

import os
import re
from datetime import datetime

import numpy as np
import yaml

__all__ = ["Saver", "load_data", "load_yaml", "print_yaml", "save_yaml"]


yaml.add_representer(np.ndarray, lambda dumper, array: dumper.represent_sequence('tag:yaml.org,2002:seq', array.tolist(), flow_style=True))
yaml.add_multi_representer(np.generic, lambda dumper, data: dumper.represent_data(data.item()))

def print_yaml(data): # Print in yaml format
    print(yaml.dump(data))

def load_yaml(path):
    file = open(path, "r")
    content = yaml.safe_load(file)
    file.close()
    return content

def save_yaml(path, data):
    file = open(path, "w")
    content = yaml.dump(data)
    file.write(content)
    return content

def load_data(*paths):
    data_list = []
    for p in paths:
        d = np.genfromtxt(p, delimiter=",")
        data_list.append(d)
    return np.concatenate(data_list)


class Saver:
    def __init__(self, title, path, indep_params=[], dep_params=[], params={}):
        self.indep_params = []
        self.dep_params = []
        self.params = params
        self.title = title
        self.path = path
        self.file_name = ''
        self.has_data = False
        os.path.exists(path)
        try: # check variables
            for value in indep_params:
                self.indep_params.append([value[0], value[1]])
            for value in dep_params:
                self.dep_params.append([value[0], value[1]])
        except KeyError:
            print("Variables incorrectly formatted. Variable: ('label', 'unit')")
        # Detect max existing file number
        existing_files = [f for f in os.listdir(self.path) if re.search(r"^\d\d\d\d\d \- .*\.csv$", f)]
        if existing_files:
            existing_numbers = [int(f.split(' - ')[0]) for f in existing_files]
            next_number = max(existing_numbers) + 1
        else:
            next_number = 0
        # Creating file name + path
        self.file_name = self.path + f"/{next_number:05d} - {self.title}"
        self.created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.write_yml()
        np.savetxt(self.file_name + '.csv', [], delimiter=',')
    def write_yml(self):
        meta = {
            "created": self.created_time,
            "completed": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if self.has_data else "N/A",
            "title": self.title,
            "independent": self.indep_params,
            "dependent": self.dep_params,
            "parameters": self.params
        }
        save_yaml(self.file_name + ".yml", meta)
    def write_data(self, data):
        self.has_data = True
        with open(self.file_name + '.csv', 'a+') as f:
            np.savetxt(f, data, fmt="%.9e", delimiter=',')
        # self.write_yml() # do not call it every time for efficiency
