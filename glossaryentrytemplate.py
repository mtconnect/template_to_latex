from os import path
from re import search, DOTALL

from library.formatcontent import formatContent
from library.config import config
from library.latexmodel import latexModel

class glossaryEntryTemplate:

    def __init__(self, _path = None):
        self._path = _path
        self._template = dict()
        self._config = config("glossaryEntryTemplate")
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

        entries = self._get_content_from_template(template)
        self._template['entries'] = entries
        self._update_entry_in_glossary(entries)


    def _get_content_from_template(self, template):

        entries_str_list = template.split('h1. ')[1:]
        content_pattern = 'h1. (.+?)\n'

        entries_dict = dict()

        for entry in entries_str_list:
            entry = 'h1. '+entry
            entry_dict = dict()
            entry_dict['str'] = entry

            search_result = search(content_pattern, entry, DOTALL)
            entry_dict['name_str'] = search_result.group(1)
            name_str = self.fmt.format_key(entry_dict['name_str'])[0]

            name = self.fmt.to_latex_name(name_str) #check format in gls

            _type_search = search('\|kind\|(.+?)\|', entry, DOTALL)

            if _type_search:
                _type = _type_search.group(1)
            else:
                _type = str('new')

            if name not in self._latex_model._glossary['names']:
                name_key = self.fmt.to_key(name_str)
                if name_key in self._latex_model._glossary['terms']:
                    name_key = self.fmt.to_key(name_str, _type)

            else:
                name_key = self._latex_model._glossary['names'][name][0]

            columns_str = search('\|(.+?)\|\n', entry, DOTALL).groups()[0]
            columns = self.fmt.extract_row_columns_from_string(columns_str)

            entry_dict['keys'] = self._get_keys_from_template(entry, columns, columns_str)

            entries_dict[name_key] = entry_dict
            entries_dict[name_key]['keys']['name'] = name
            if _type != 'new':
                entries_dict[name_key]['keys']['kind'] = _type

        return entries_dict


    def _get_keys_from_template(self, string, columns, columns_str):

        #Extract rows from string
        rows_str = string.split(columns_str+'|')[-1]
        rows_str_list = self.fmt.extract_row_columns_from_string(rows_str)
        rows = list()

        for col in rows_str_list:
            if len(col)>1 or (len(col)==1 and '\n' not in col):
                rows.append(col)

        rows_dict = dict()
        for i,col in enumerate(rows):
            if i%len(columns) == 0:
                key = col

            elif i%len(columns) == 1:
                rows_dict[key] = self.fmt.format_desc(col)

        return rows_dict


    def _get_value_from_key(self, entry_key, key):
        if key in self._template['entries'][entry_key]['keys']:
            return self._template['entries'][entry_key]['keys'][key]
        else:
            return str()


    def _update_entry_in_glossary(self, entries):

        for entry, entry_dict  in entries.items(): #actual, dict
            self._add_to_glossary(entry)



    def _add_to_glossary(self, gls_key):

        if not self._latex_model.get_gls_name(gls_key):
            self._latex_model.add_glossary_entry(
                gls_key,
                self._get_value_from_key(gls_key, 'name'),
                self._get_value_from_key(gls_key, 'description'),
                'type', self._get_value_from_key(gls_key, 'type'),
                'category', self._get_value_from_key(gls_key, 'category'),
                'kind', self._get_value_from_key(gls_key, 'kind'),
                'elementname', self._get_value_from_key(gls_key, 'elementname'),
                'plural', self._get_value_from_key(gls_key, 'plural'),
                'pluraldescription', self._get_value_from_key(gls_key, 'pluraldescription'),
                'elements', self._get_value_from_key(gls_key, 'elements'),
                'attributes', self._get_value_from_key(gls_key, 'attributes'),
                'subtype', self._get_value_from_key(gls_key, 'subtype')
                )

        else:

            for key, val in self._template['entries'][gls_key]['keys'].items():
                new_val = self._get_value_from_key(gls_key, key)
                self._latex_model._glossary['terms'][gls_key][key] = '{'+new_val+'}'

            self._latex_model.update_gls_entry(gls_key)



if __name__ == '__main__':
    template = glossaryEntryTemplate('path-to/templates/Glossary Entry Template.txt')



