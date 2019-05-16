from os import path
from re import search, DOTALL

from library.formatcontent import formatContent
from library.config import config
from library.latexmodel import latexModel

class compositionTemplate:

    def __init__(self, _path = None):
        self._path = _path
        self._template = dict()
        self._config = config("compositionTemplate")
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

        if search_result.group(3):
            part2_str = 'h1. ' + template.split('h1. ')[-1]

        elif search_result.group(1):
            heading = search_result.group(1).split('\n')[0]
            if 'composition' in heading.lower():
                part2_str = 'h1. ' + search_result.group(1)

            elif 'composition' in search_result.group(2).lower():
                part2_str = 'h1. ' + template.split('h1. ')[-1]

        part2 = self._get_content_from_pattern(part2_str)

        return part2


    def _get_content_from_pattern(self, string):

        columns_str = search('\|(.+?)\|\n', string, DOTALL).groups()[0]
        columns = self.fmt.extract_row_columns_from_string(columns_str)

        self._template['columns'] = dict()
        self._template['columns_str'] = dict()

        self._template['columns']['meta'] = columns
        self._template['columns_str']['meta'] = columns_str

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


    def _add_to_glossary(self, row, gls_key, _type = 'composition'):


        latex_model = self._latex_model

        #Expecting row content to be in the following order
        name = row[0]
        description = row[1]

        if not self._latex_model.get_gls_name(gls_key):
            self._latex_model.add_glossary_entry(
                gls_key,
                self.fmt.to_latex_name(name),
                description,
                'type', 'model',
                'category', 'code',
                'kind', _type.lower()
                )
        table_name = self._config.table_name(2, "composition")
        values = [gls_key, description]

        latex_model.update_table(
            action = 'add',
            table_name = table_name,
            row = gls_key,
            columns = self._template['columns']['meta'],
            values = values,
            _type = _type
            )

if __name__ == '__main__':
    template = compositionTemplate('path-to/newcontent/deposition_component_composition.txt')
