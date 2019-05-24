from os import path
from json import loads

class config:

    def __init__(self, _path = str()):
        self.path = _path
        self.config_path = path.join(_path,'config','template.cfg')

    def load_config(self, _type = str()):
        self._type = _type
        try:
            config_file = open(self.config_path,"r")
            self.config_json = loads(config_file.read())

        except Exception as e:
            print (e)

    def latex_model(self, part_number):
        part = 'part' + str(part_number)
        if part not in self.config_json.keys():
            return str()

        latex_path = self.config_json['latex']['path']
        part_path = self.config_json[part]['model']

        _path = path.join(latex_path, part_path)
        return _path

    def table_name(self, part_number, table_type):
        part = 'part' + str(part_number)
        if table_type in self.config_json[self._type][part]:
            return self.config_json[self._type][part][table_type]['tableName']
        else:
            return None

    def doc_name(self, part_number, doc_type):
        part = 'part' + str(part_number)
        if doc_type in self.config_json[self._type][part]:
            return self.config_json[self._type][part][doc_type]['docName']
        else:
            return None

    def path_to_content_type_template(self, content_type):
        filename = self.config_json[self._type][content_type]['template']
        _path = path.join(self.path,'templates','othertemplates',filename+'.tex')
        return _path
