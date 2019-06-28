from os import path, mkdir
from shutil import copyfile
from json import loads, dumps

class config:

    def __init__(self, _path = str()):
        self.path = _path
        self._type = str()
        self.config_path = path.join(_path,'config','template.cfg')

    def load_config(self, _type = str()):
        if not self._type or _type: self._type = _type
        try:
            config_file = open(self.config_path,"r")
            self.config_json = loads(config_file.read())

        except Exception as e:
            print (e)

    def get_perl_path(self):
        perl_path = self.config_json['perl']['path']
        return perl_path

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
        if part not in self.config_json[self._type].keys():
            return None
        elif table_type in self.config_json[self._type][part]:
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

    def create_new_model(self, part):
        latex_path = self.config_json['latex']['path']
        new_path = path.join(latex_path,"MTConnect Part "+str(part))
        mkdir(new_path)

        #copying common files from part2
        part2_path = self.latex_model(2)
        #mtconnect.cls
        copyfile(
            path.join(part2_path,"mtconnect.cls"),
            path.join(new_path,"mtconnect.cls")
            )

        #legal.tex
        copyfile(
            path.join(part2_path,"legal.tex"),
            path.join(new_path,"legal.tex")
            )

        #latexmkrc
        copyfile(
            path.join(part2_path,"latexmkrc"),
            path.join(new_path,"latexmkrc")
            )

        #guide.tex
        copyfile(
            path.join(part2_path,"guide.tex"),
            path.join(new_path,"guide.tex")
            )

        #mtc.bib
        copyfile(
            path.join(part2_path,"mtc.bib"),
            path.join(new_path,"mtc.bib")
            )

        #references.bib
        copyfile(
            path.join(part2_path,"references.bib"),
            path.join(new_path,"references.bib")
            )

        #acronyms.tex
        copyfile(
            path.join(part2_path,"acronyms.tex"),
            path.join(new_path,"acronyms.tex")
            )

        #mtc-terms.tex
        copyfile(
            path.join(part2_path,"mtc-terms.tex"),
            path.join(new_path,"mtc-terms.tex")
            )

        #main.tex
        maintex_str = self.get_maintex_template(part2_path)
        maintex = open(path.join(new_path,"main.tex"),"w")
        maintex.write(maintex_str)
        maintex.close()

        #body.tex
        #all the new content goes here
        bodytex = open(path.join(new_path,"body.tex"),"w")
        bodytex.close()

        #dir for tables and figures
        mkdir(path.join(new_path,"tables"))
        mkdir(path.join(new_path,"figures"))

        #updating config file
        part_key = 'part'+str(part)
        self.config_json[part_key] = dict()
        self.config_json[part_key]['model'] = "MTConnect Part "+str(part)

        self.config_json[self._type][part_key] = dict()
        self.config_json["newSectionTemplate"][part_key]['section'] = {"docName":"body"}

        config_file = open(self.config_path,"w")
        config_file.write(dumps(self.config_json, indent =4, sort_keys = True))
        config_file.close()

        #reloading config file
        self.load_config()

    def get_maintex_template(self,_path):
        maintex = open(path.join(_path,"main.tex"),'r')
        main = maintex.read()
        template = main.split("\\input{introduction.tex}",1)[0]
        template = template + "\\input{body.tex}\n\n\\end{document}"
        return template
