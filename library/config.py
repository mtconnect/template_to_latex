from os import path
from json import loads

class config:

    def __init__(self, _type):
        self._type = _type 
        self.config_address = "path-to-config-file/template.cfg"

        self.load_config()

    def load_config(self):
        try:
            config_file = open(self.config_address,"r")
            self.config_json = loads(config_file.read())

        except Exception as e:
            print (e)

    def latex_model(self, part_number):
        part = 'part' + str(part_number)
        return self.config_json[part]['model']

    def table_name(self, part_number, table_type):
        part = 'part' + str(part_number)
        if table_type in self.config_json[self._type][part]:
            return self.config_json[self._type][part][table_type]['tableName']
        else:
            return None
