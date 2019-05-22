from os import path
from re import search, DOTALL

from library.formatcontent import formatContent
from library.config import config
from library.latexmodel import latexModel
from library.generatecontent import generateContent

class newSectionTemplate:

    def __init__(self, _path = None):
        self._path = _path
        self._template = dict()
        self._contents = dict()
        self._contents['tables'] = dict()
        self._contents['figures'] = dict()
        self._contents['examples'] = dict()
        self._contents['labels'] = dict()
        self._config = config("newSectionTemplate")
        self._latex_model2 = latexModel(self._config.latex_model(2))
        self._latex_model3 = latexModel(self._config.latex_model(3))

        self.fmt = formatContent(self._latex_model2)
        self.generate = generateContent()
        self._load_template()


    def _load_template(self):
        if not self._path:
            raise Exception("Enter a valid latex directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_doc(template)


    def _add_all_content_to_doc(self, template):

        section, tables, figures, examples = self._get_content_from_template(template)

        self._get_tables_content(tables)
        self._get_figures_content(figures)
        self._get_examples_content(examples)
        self._get_section_content(section)


    def _get_content_from_template(self, template):
        tables, figures, examples = list(),list(),list()
        content_list = template.split('h3. ')

        section = content_list[0]
        part_no = self._get_part_no(section)

        content_pattern = '(.+?)\n'
        for content in content_list[1:]:
            if search(content_pattern, content, DOTALL):
                content_type = search(content_pattern, content, DOTALL).group(1)

                if 'table' in content_type.lower():
                    tables.append(content)
                elif 'figure' in content_type.lower():
                    figures.append(content)
                elif 'example' in content_type.lower():
                    examples.append(content)

        return section, tables, figures, examples


    def _get_part_no(self, section):
        part_no_pattern = '\* Part(.+?)\n'
        part_no = None

        if search(part_no_pattern, section, DOTALL):
            part_no_str = search(part_no_pattern, section, DOTALL).group(1)

            if 'part 3' in part_no_str.lower():
                self._template['model'] = 3
                self._latex_model = self._latex_model3
            else:
                self._template['model'] = 2
                self._latex_model = self._latex_model2
                
        return part_no


    def _get_tables_content(self, tables):
        for table_str in tables:
            label = self._get_label_from_content(table_str)
            self._add_table(label, table_str)
            

    def _add_table(self, label, table_str):

        columns_str = search('\|(.+?)\|\n', table_str, DOTALL).groups()[0]
        columns = self.fmt.extract_row_columns_from_string(columns_str)

        if table_str not in self._latex_model._tables:
            path = self._latex_model._path +'/tables/' + label + '.tex'
            self.generate.create_table(path, label, columns)
            self._latex_model._load_tables()
            self._contents['tables'][label] = dict()
            self._contents['tables'][label]['string'] = '\\input{tables/'+label+'.tex}'
            self._contents['labels'][label] = 'table'

        rows = self._get_types_from_template(table_str, columns, columns_str)

        for key, val in rows.items():
            row = val[key]

            self._latex_model.update_table(
                action = 'add',
                table_name = label,
                row = row[0],
                columns = columns,
                values = row
                )


    def _get_types_from_template(self, part, columns, columns_str):

        #Extract rows from string
        rows_str = part.split(columns_str+'|')[-1]
        rows_str_list = self.fmt.extract_row_columns_from_string(rows_str)
        rows = list()

        for col in rows_str_list:
            if len(col)>1 or (len(col)==1 and '\n' not in col):
                rows.append(col)

        #Format rows wrt columns
        rows_dict = dict()
        for i,col in enumerate(rows):
            if i%len(columns) == 0:
                col, _type = self.fmt.format_key(col)
                if _type == 'type':
                    key = self.fmt.to_key(col)
                    name = self.fmt.to_latex_name(col)
                    if name in self._latex_model._glossary['names']:
                        category = 'model'
                        name = str(',').join([category,name])
                    self._latex_model._glossary['names'][name] = [key, '\\gls{']
                    rows_dict[key] = dict()
                    rows_dict[key]['_type'] = _type
                    rows_dict[key][key] = [col]

            elif i%len(columns) >= 1:
                col = self.fmt.format_desc(col)
                if _type == 'type':
                    rows_dict[key][key].append(col)

        return rows_dict


    def _get_figures_content(self, figures):
        for figure_str in figures:
            label = self._get_label_from_content(figure_str)

            filename_pattern = '\|filename\|(.+?)\|\n'
            filename = search(filename_pattern, figure_str, DOTALL).group(1)

            caption_pattern = '\|caption\|(.+?)\|\n'
            caption = search(caption_pattern, figure_str, DOTALL).group(1)

            figure_latex_str = self.generate._generate_figure_str(filename,label,caption)
            self._contents['figures'][label] = dict()
            self._contents['figures'][label]['string'] = figure_latex_str
            self._contents['labels'][label] = 'figure'


    def _get_examples_content(self, examples):
        for example_str in examples:
            label = self._get_label_from_content(example_str)

            content_pattern = '<pre>\n(.+?)\n</pre>'
            content = search(content_pattern, example_str, DOTALL).group(1)

            example_latex_str = self.generate._generate_example_str(content,label)
            self._contents['examples'][label] = dict()
            self._contents['examples'][label]['string'] = example_latex_str
            self._contents['labels'][label] = 'example'


    def _get_section_content(self, section):

        pattern = 'h1. (.+?)\nh2. (.+?)\n|h1. (.+?)\n\*(.+?)\n'
        pattern_search = search(pattern, section, DOTALL)

        if pattern_search:
            if pattern_search.group(3):
                section_name_str = pattern_search.group(3)

            elif pattern_search.group(1):
                section_name_str = pattern_search.group(1).split('\n')[0]

        section_desc = section.split(pattern_search.group(0))[-1]

        doc_str = self._read_doc()
        section_name = self.fmt.format_key(section_name_str)[0]
        parent, parent_sect_type = self._get_parent_section(section, doc_str)
        section_desc = self._format_section_content(section_desc)

        self._add_to_doc(doc_str, section_name, section_desc, parent, parent_sect_type)


    def _read_doc(self):
        part = self._template['model']
        _file_path = self._config.latex_model(part) +'/'+ self._config.doc_name(part, "section")
        _file=open(_file_path+'.tex','r',errors='ignore')
        doc_str = _file.read()
        _file.close()
        return doc_str


    def _write_doc(self, doc_str):
        part = self._template['model']
        _file_path = self._config.latex_model(part) +'/'+ self._config.doc_name(part, "section")
        _file=open(_file_path+'.tex','w')
        _file.write(doc_str)
        _file.close()


    def _subsection_type(self, sect_type):
        subsection_type = str()

        for i, _type in enumerate(self._sect_types):
            if sect_type == _type and i < len(self._sect_types)-1:
                subsection_type = self._sect_types[i+1]
                break
            elif sect_type == _type:
                subsection_type = _type
                break

        if not subsection_type:
            subsection_type = self._sect_types[0]

        return subsection_type


    def _add_to_doc(self, doc_str, section_name, section_desc, parent, parent_sect_type):

        section_type = self._subsection_type(parent_sect_type)

        if parent:
            split_str = '\n\\'+parent_sect_type+'{'+parent+'}'
            parent_sect = doc_str.split(split_str)[-1]
            parent_sect = split_str + parent_sect.split('\n\\'+parent_sect_type)[0]
        else:
            parent_sect = doc_str

        new_section = list()
        new_section.append(parent_sect)
        new_section.append('\n\\'+section_type+'{'+section_name+'}\n')
        new_section.append(section_desc)

        new_section_str = str().join(new_section)

        doc_str = doc_str.replace(parent_sect, new_section_str)

        self._write_doc(doc_str)


    def _get_parent_section(self, section, doc_str = str()):
        parent_pattern = 'h2. (.+?)\n'
        parent = str()
        parent_sect_type = str()

        sect_types = ['section','subsection','subsubsection','paragraph','subparagraph', 'ulheading']
        self._sect_types = sect_types

        if search(parent_pattern, section, DOTALL):
            parent = search(parent_pattern, section, DOTALL).group(1)
            parent = self.fmt.format_key(parent)[0]

        for _type in sect_types:
            sect_type_str = '\n\\'+_type+'{'+parent+'}'
            if sect_type_str in doc_str:
                parent_sect_type = sect_type_str
                break

        return parent, _type


    def _get_label_from_content(self, content):
        label_pattern = '\*(.+?)\n'
        label = str()

        if search(label_pattern, content, DOTALL):
            label_str = search(label_pattern, content, DOTALL).group(1)
            label = self.fmt.format_key(label_str)[0]

        return label


    def _format_section_content(self, section):
        pattern = '{(ref):([a-z A-Z 0-9 -]+)}|{(table):([a-z A-Z 0-9 -]+)}|{(example):([a-z A-Z 0-9 -]+)}|{(figure):([a-z A-Z 0-9 -]+)}'

        if search(pattern,section, DOTALL):
            search_result = search(pattern,section, DOTALL)
            content = search_result.group(0)
            [key,val] = content.split(':')
            key = key[1:]
            val = val[:-1]

            content_type = self._contents['labels'][val]

            if content_type == 'table':
                formatted_content = self._get_table_from_ref(key,val)
            elif content_type == 'figure':
                formatted_content = self._get_figure_from_ref(key,val)
            elif content_type == 'example':
                formatted_content = self._get_example_from_ref(key,val)
            else:
                formatted_content = str()

            section = section.replace(content, formatted_content)

            return self._format_section_content(section)

        else:
            return self.fmt.format_desc(section)


    def _get_table_from_ref(self, key, val):
        if key == 'ref':
            return '\\tbl{'+val+'}'
        elif key == 'table':
            return self._contents['tables'][val]['string']


    def _get_figure_from_ref(self, key, val):
        if key == 'ref':
            return '\\fig{'+val+'}'
        elif key == 'figure':
            return self._contents['figures'][val]['string']

    def _get_example_from_ref(self, key, val):
        if key == 'ref':
            return '\\lst{'+val+'}'
        elif key == 'example':
            return self._contents['examples'][val]['string']



if __name__ == '__main__':
    template = newSectionTemplate('path-to/templates/newcontent/data_set_representation.txt')
