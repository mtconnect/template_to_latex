from os import listdir, fsencode, fsdecode, path, getcwd, mkdir
from shutil import copyfile
from subprocess import check_call
from time import perf_counter

from library.formatcontent import formatContent
from library.config import config
from library.latexmodel import latexModel
from library.generatecontent import generateContent

from glossaryentrytemplate import glossaryEntryTemplate
from componenttemplate import componentTemplate
from compositiontemplate import compositionTemplate
from kindtemplate import kindTemplate
from sampletemplate import sampleTemplate
from eventtemplate import eventTemplate
from newsectiontemplate import newSectionTemplate

class writeToDoc:

    def __init__(self):
        self._latex_model = dict()
        self._new_content_dict = dict()
        self._project_groups = dict()
        self._configure()
        self._load_latex_model()
        self._fmt = formatContent(self.latex_model())
        self._load_new_content()


    def _configure(self):
        self.path = getcwd()
        self.new_content_path = path.join(self.path,'templates','newcontent')
        self.config = config(_path = self.path)
        self.config.load_config()
        self.perl_path = self.config.get_perl_path()

        for content_type in list(self.config.config_json.keys()):
            if content_type.endswith('Template'):
                self._new_content_dict[content_type] = list()


    def _load_latex_model(self):
        #assuming common glossary: part 2
        glossary_path = self.config.latex_model(2)

        for key in list(self.config.config_json.keys()):
            if key.startswith('part'):
                part_no_str = key.split('part')[-1]
                if float(part_no_str) == int(float(part_no_str)):
                    part_no = int(part_no_str)
                else:
                    part_no = float(part_no_str)

                self._latex_model[part_no] = latexModel(
                                                self.config.latex_model(part_no),
                                                glossary_path
                                                )

    def latex_model(self, part = int()):
        self._load_latex_model()
        if not part:
            part = 2
            #assumes default part as part2 for any edits

        elif part and part not in self._latex_model:
            self._create_new_part(part)

        return self._latex_model[part]


    def _create_new_part(self, part):
        self.config.create_new_model(part)
        glossary_path = self.config.latex_model(2)
        self._latex_model[part] = latexModel(self.config.latex_model(part), glossary_path)


    def _load_new_content(self):
        for folder in listdir(self.new_content_path):

            if folder.endswith('Template'):

                for file in listdir(path.join(self.new_content_path,folder)):
                    filename = fsdecode(file)
                    if not filename.startswith('mod_doc_'):
                        continue

                    #by template?
                    file_path = path.join(self.new_content_path,folder, filename)
                    file_creation_time = path.getctime(file_path)
                    self._new_content_dict[folder].append([file_creation_time,filename,file_path])

                    #OR
                    #by WG? Current Approach
                    project_group = self._get_project_group(filename, folder)
                    self._project_groups[project_group][folder].append([file_creation_time,filename,file_path])

                self._project_groups[project_group][folder].sort()
                self._new_content_dict[folder].sort()


    def _get_project_group(self, filename, folder):
        filename_list = filename.split('_')

        if filename_list[:2] == ['mod','doc']:
            project_group = filename_list[2]

            if project_group not in self._project_groups:
                self._project_groups[project_group] = dict()

            if folder not in self._project_groups[project_group]:
                self._project_groups[project_group][folder] = list()

            return project_group
        else:
            return None


    def _write_new_content_for(self, content_type, template_class, project_group):

        content_list = list()
        if content_type in self._project_groups[project_group].keys():
            content_list = self._project_groups[project_group][content_type]

        for new_content in content_list:
            file_path = new_content[2]
            template_class.load_new_content(file_path)
            issue_no = file_path.split('mod_doc_')[-1].split('_')[1]
            print ("Completed Issue: "+str(issue_no)+" !")


    def write_all_new_content(self):

        for project_group in self._project_groups.keys():
            self.write_all_new_content_for_project_group(project_group)
            print ("Completed Issues for Project Group: "+project_group+" !")

        self.update_glossary_for_all_parts()

    def update_glossary_for_all_parts(self):
        new_path = path.join(self.path,'overleaf','v1.5')
        glossary_path = self.config.latex_model(2)
        glossary_file_path = path.join(glossary_path, 'mtc-terms.tex')

        for folder in listdir(new_path):
            if 'Part 2' not in folder:
                part_glossary_file_path = path.join(new_path,folder,'mtc-terms.tex')
                copyfile(glossary_file_path, part_glossary_file_path)


    def create_latexdiff_files(self, old_version, new_version):
        new_path = path.join(self.path,'overleaf','v'+str(new_version))
        old_path = path.join(self.path,'overleaf','v'+str(old_version))
        latexdiff_path = path.join(self.path,'overleaf','latexdiff','latexdiff')
        perl_path = self.perl_path

        for folder in listdir(new_path):
            safe_commands = ['must',
                             'mustnot',
                             'should',
                             'shouldnot',
                             'may',
                             'maynot',
                             'shall',
                             'shallnot',
                             'MUST',
                             'MUSTNOT',
                             'SHOULD',
                             'SHOULDNOT',
                             'MAY',
                             'MAYNOT',
                             'SHALL',
                             'SHALLNOT',
                             'fig',
                             'tbl',
                             'sect',
                             'lst',
                             'apx',
                             'cfont',
                             'textit',
                             'deprecated',
                             'DEPRECATED',
                             'DEPRECATIONWARNING',
                             'glselementname',
                             'glsrepresentation',
                             'citetitle',
                             'glsunits',
                             'gls',
                             'glsentrydesc',
                             'glspl',
                             'glsentryunits']
            command = [perl_path,
                       latexdiff_path,
                       '--flatten',
                       path.join(old_path,folder,'main.tex'),
                       path.join(new_path,folder,'main.tex'),
                       '>',
                       path.join(new_path,folder,'main_diff.tex'),
                       '--append-safecmd='+str(',').join(safe_commands)]

            check_call(command, shell = True)

            self.correction_for_latexdiff(path.join(new_path,folder,'main_diff.tex'))


    def correction_for_latexdiff(self, file_path):

        _file  = open(file_path,'r',encoding='utf8')
        _file_str = _file.read()
        _file.close()

        old_str = '\\begin{longtabu} \\DIFadd{to \\textwidth{|l|X[3l]|l|}\n}'
        new_str = '\\begin{longtabu} to \\textwidth{|l|X[3l]|l|}\n'

        _file_str = _file_str.replace(old_str, new_str).replace('–','-').replace('“','"').replace('”','"').replace("’","'")

        #update latexdiff DIFadd and DIFdel commands
        difadd_old = '\n\\providecommand{\\DIFadd}[1]{{\\protect\\color{blue}\\uwave{#1}}}'
        difadd_new = '\n\\providecommand{\\DIFadd}[1]{{\\hspace{0pt}\\protect\\color{blue}#1}}'

        _file_str = _file_str.replace(difadd_old, difadd_new)

        difdel_old = '\n\\providecommand{\\DIFdel}[1]{{\\protect\\color{red}\\sout{#1}}}'
        difdel_new = '\n\\providecommand{\\DIFdel}[1]{{\\hspace{0pt}\\protect\\color{red}#1}}'

        _file_str = _file_str.replace(difdel_old, difdel_new)

        _file = open(file_path,'w')
        _file.write(_file_str)
        _file.close()


    def write_all_new_content_for_project_group(self, project_group):

        #order is significant

        self._glossary_entry_template = glossaryEntryTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('glossaryEntryTemplate', self._glossary_entry_template, project_group)

        self._kind_template = kindTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('kindTemplate', self._kind_template, project_group)
        self._fmt = formatContent(self.latex_model())

        self._component_template = componentTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('componentTemplate', self._component_template, project_group)
        self._fmt = formatContent(self.latex_model())

        self._composition_template = compositionTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('compositionTemplate', self._composition_template, project_group)
        self._fmt = formatContent(self.latex_model())

        self._sample_template = sampleTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('sampleTemplate', self._sample_template, project_group)
        self._fmt = formatContent(self.latex_model())

        self._event_template = eventTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('eventTemplate', self._event_template, project_group)
        self._fmt = formatContent(self.latex_model())

        self._new_section_template = newSectionTemplate(self.config, self.latex_model, self._fmt)
        self._write_new_content_for('newSectionTemplate', self._new_section_template, project_group)
        self._fmt = formatContent(self.latex_model())


if __name__ == '__main__':
    time_start = perf_counter()

    writetodoc = writeToDoc()
    writetodoc.write_all_new_content()

    time_latexdiff = perf_counter()

    writetodoc.create_latexdiff_files(1.4,1.5)

    print ('Completed in: ' + str(time_latexdiff-time_start) + ' seconds!\nLatexdiff completed in ' + str(perf_counter()-time_latexdiff)+ ' seconds!')

