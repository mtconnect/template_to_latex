from os import listdir, fsencode, fsdecode, path, getcwd

from library.formatcontent import formatContent
from library.config import config
from library.latexmodel import latexModel
from library.generatecontent import generateContent

from glossaryentrytemplate import glossaryEntryTemplate
from componenttemplate import componentTemplate
from compositiontemplate import compositionTemplate
from attributessubelementstemplate import attributesSubElementsTemplate
from sampletemplate import sampleTemplate
from eventtemplate import eventTemplate
from newsectiontemplate import newSectionTemplate

class writeToDoc:

    def __init__(self):
        self._latex_model = dict()
        self._new_content_dict = dict()
        self._configure()
        self._load_latex_model()
        self._fmt = formatContent(self.latex_model())
        self._load_new_content()


    def _configure(self):
        self.path = getcwd()
        self.new_content_path = path.join(self.path,'templates','newcontent')
        self.config = config(_path = self.path)
        self.config.load_config()

        for content_type in list(self.config.config_json.keys()):
            if content_type.endswith('Template'):
                self._new_content_dict[content_type] = list()


    def _load_latex_model(self):
        self._latex_model[1] = latexModel(self.config.latex_model(1))
        self._latex_model[2] = latexModel(self.config.latex_model(2))
        self._latex_model[3] = latexModel(self.config.latex_model(3))
        self._latex_model[4] = latexModel(self.config.latex_model(4))
        self._latex_model[4.1] = latexModel(self.config.latex_model(4.1))
        self._latex_model[5] = latexModel(self.config.latex_model(5))


    def latex_model(self, part = int()):
        if part:
            return self._latex_model[part]
        else:
            #assumes default part as part2 : assumed source for glossary
            return self._latex_model[2]


    def _load_new_content(self):
        for folder in listdir(self.new_content_path):

            if folder.endswith('Template'):

                for file in listdir(path.join(self.new_content_path,folder)):
                    filename = fsdecode(file)
                    file_path = path.join(self.new_content_path,folder, filename)
                    file_creation_time = path.getctime(file_path)
                    self._new_content_dict[folder].append([file_creation_time,filename,file_path])

                self._new_content_dict[folder].sort()


    def _write_new_content_for(self, content_type, template_class):

        content_list = self._new_content_dict[content_type]

        for new_content in content_list:
            file_path = new_content[2]
            template_class.load_new_content(file_path)
        

    def write_all_new_content(self):

        #order is significant

        self._glossary_entry_template = glossaryEntryTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('glossaryEntryTemplate', self._glossary_entry_template)

        self._component_template = componentTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('componentTemplate', self._component_template)

        self._composition_template = compositionTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('compositionTemplate', self._composition_template)

        self._attribs_subelems_template = attributesSubElementsTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('attributesSubElementsTemplate', self._attribs_subelems_template)

        self._sample_template = sampleTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('sampleTemplate', self._sample_template)

        self._event_template = eventTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('eventTemplate', self._event_template)

        self._new_section_template = newSectionTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('newSectionTemplate', self._new_section_template)



if __name__ == '__main__':
    writetodoc = writeToDoc()
    writetodoc.write_all_new_content()
