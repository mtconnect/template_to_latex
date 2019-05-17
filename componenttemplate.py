from os import path
from re import search, DOTALL

from library.formatcontent import formatContent
from library.config import config
from library.latexmodel import latexModel

class componentTemplate:

    def __init__(self, _path = None):
        self._path = _path
        self._template = dict()
        self._config = config("componentTemplate")
        self._latex_model = latexModel(self._config.latex_model(2))

        self.fmt = formatContent(self._latex_model)
        self._load_template()


    def _load_template(self):
        if not self._path:
            raise Exception("Enter a valid latex directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_glossary(template)


    def _add_all_content_to_glossary(self, template):

        part2 = self._get_content_from_template(template)
        self._add_types_to_glossary(part2)


    def _get_content_from_template(self, template):

        content_pattern = 'h1. (.+?)\nh1. (.+?)\n|h1. (.+?)\n'
        search_result = search(content_pattern, template, DOTALL)
        part2_str = str()
        self._template['component'] = str()

        if search_result.group(3):
            part2_str = 'h1. ' + template.split('h1. ')[-1]
            self._template['component'] = search_result.group(3)

        elif search_result.group(1):
            heading = search_result.group(1).split('\n')[0]
            if 'component' in heading.lower():
                part2_str = 'h1. ' + search_result.group(1)
                self._template['component'] = heading

            elif 'component' in search_result.group(2).lower():
                part2_str = 'h1. ' + template.split('h1. ')[-1]
                self._template['component'] = search_result.group(2)

        part2 = self._get_content_from_pattern(part2_str)

        return part2


    def _get_content_from_pattern(self, string):

        self._template['columns'] = dict()
        self._template['columns_str'] = dict()
        self._template['description'] = str()
        self._template['parent'] = str()
        self._template['is_parent'] = True

        row = list()
        row_str= str()

        columns = ['elements', 'description']
        self._template['columns']['meta'] = columns

        columns_str = '|'.join(columns)
        self._template['columns_str']['meta'] = columns_str


        parent_search_pattern = 'h2. Parent: (.+?)\n'
        parent_search_result = search(parent_search_pattern, string, DOTALL)

        if parent_search_result and parent_search_result.group(1):
            parent_key = parent_search_result.group(1)
            self._template['parent'] = parent_key
            self._template['is_parent'] = False

            description = string.split(parent_search_result.group(0))[-1]
            self._template['description'] = description

        else:
            description = string.split('h1. ')[-1].split('\n',1)[-1]
            self._template['description'] = description

        row.append(self._template['component'])
        short_description_list = description.split('\n')
        for desc in short_description_list:
            if len(desc)>5: #arbitrary flag to check if content present
                row.append(desc)
                break

        row_str = '|'+'|'.join(row)+'|'

        string = string + '\n|' + columns_str + '|\n' + row_str

        return string


    def _get_types_from_template(self, part):

        columns = self._template['columns']['meta']
        columns_str = self._template['columns_str']['meta']

        #Extract rows from string
        rows_str = part.split(columns_str+'|')[-1]
        rows_str_list = self.fmt.extract_row_columns_from_string(rows_str)
        rows = list()
        
        for col in rows_str_list:
            if len(col)>1:
                rows.append(col)
    
        #Format rows wrt columns
        rows_dict = dict()
        for i,col in enumerate(rows):
            if i%len(columns) == 0:
                col, _type = self.fmt.format_key(col)
                if _type == 'type':
                    key = self.fmt.to_key(col)
                    self._latex_model._glossary['names'][self.fmt.to_latex_name(col)] = [key, '\\gls{']
                    rows_dict[key] = dict()
                    rows_dict[key]['_type'] = _type
                    rows_dict[key][key] = [col]
                    rows_dict[key]['initial'] = dict()

                    if self._latex_model.get_gls_name(key):
                        rows_dict[key]['initial']['parent'] = self._latex_model._glossary['terms'][key]
                    else:
                        rows_dict[key]['initial']['parent'] = None

            elif i%len(columns) >= 1:
                col = self.fmt.format_desc(col)
                if _type == 'type':
                    rows_dict[key][key].append(col)

        return rows_dict


    def _add_types_to_glossary(self, part):

        rows = self._get_types_from_template(part)
        self._template['rows'] = rows

        for key, val in rows.items():

            row = val[key]

            self._add_to_glossary(row, key)


    def _add_to_glossary(self, row, gls_key, _type = 'component'):

        latex_model = self._latex_model

        #Expecting row content to be in the following order
        name = row[0]
        description = row[1]

        if not self._template["is_parent"]:
            _types = list()
            _types.append(_type)
            _types.append(self.fmt.to_key(self.fmt.format_key(self._template["parent"])[0]))

            _type = ','.join(_types)

        if not self._latex_model.get_gls_name(gls_key):
            self._latex_model.add_glossary_entry(
                gls_key,
                self.fmt.to_latex_name(name),
                description,
                'type', 'model',
                'category', 'code',
                'kind', _type.lower()
                )

        if self._template["is_parent"]:
            table_name = self._config.table_name(2, "component")
            values = [gls_key, description]

            latex_model.update_table(
                action = 'add',
                table_name = table_name,
                row = gls_key,
                columns = self._template['columns']['meta'],
                values = values,
                _type = _type
                )

        self._add_to_doc()


    def _add_to_doc(self): #move to the library?
        _file_path = self._config.latex_model(2) +'/'+ self._config.doc_name(2, "component")
        _file=open(_file_path+'.tex','r',errors='ignore')
        _file=_file.read()

        comp_struct_sec = _file.split('\section{Component Structural Elements}')[1]
        comp_struct_sec = comp_struct_sec.split('\section')[0]

        sub_sections = comp_struct_sec.split('\subsection')

        sub_sections_str = str()
        if self._template['is_parent']:
            new_sub_section = '{'+self.fmt.format_key(self._template['component'])[0]+'}\n'
            new_sub_section += self.fmt.format_desc(self._template['description'])+'\n'

            if new_sub_section in sub_sections: #already added
                return

            sub_sections = sub_sections[:-1]+[new_sub_section]+[sub_sections[-1]]
            sub_sections = [sub_sections[0]]+['\\subsection'+sect for sect in sub_sections[1:]]

            sub_sections_str = sub_sections_str.join(sub_sections)

        else:
            for i,sub_sect in enumerate(sub_sections):
                if sub_sect.startswith('{'+self.fmt.format_key(self._template['parent'])[0]+'}'):
                    subsubsect = '\\subsubsection{'+self.fmt.format_key(self._template['component'])[0]+'}\n'
                    subsubsect += self.fmt.format_desc(self._template['description'])+'\n'

                    if subsubsect in sub_sections[i]: #already added
                        return

                    sub_sections[i] += subsubsect
                    break

            sub_sections = [sub_sections[0]]+['\\subsection'+sect for sect in sub_sections[1:]]
            sub_sections_str = sub_sections_str.join(sub_sections)

        if sub_sections_str:
            _new_file = str()

            _file_prepend = _file.split('\section{Component Structural Elements}')[0]

            _file_append = _file.split('\section{Component Structural Elements}')[1].partition('\\section')[1:]

            _new_file = _file_prepend + '\\section{Component Structural Elements}' +sub_sections_str+ _new_file.join(_file_append)

            _file_write = open(_file_path+'.tex', 'w')
            _file_write.write(_new_file)
            _file_write.close()


if __name__ == '__main__':
    template = componentTemplate('path-to/newcontent/deposition_component_composition.txt')
