from os import path
from re import search, DOTALL

class glossaryEntryTemplate:

    def __init__(self, config, latex_model, formatter):
        self._template = dict()
        self._config = config
        self._config.load_config("glossaryEntryTemplate")
        self._latex_model = latex_model()
        self._fmt = formatter


    def load_new_content(self, _path):
        self._path = _path
        if not self._path:
            raise Exception("Enter a valid latex directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_glossary(template)


    def _add_all_content_to_glossary(self, template):

        entries_str_list = template.split('h1. ')[1:]
        content_pattern = 'h1. (.+?)\n'

        for entry in entries_str_list:
            entries_dict = dict()
            entry = 'h1. '+entry
            entry_dict = dict()
            entry_dict['str'] = entry

            search_result = search(content_pattern, entry, DOTALL)
            entry_dict['name_str'] = search_result.group(1)
            name_str = self._fmt.format_key(entry_dict['name_str'])[0]

            name = self._fmt.to_latex_name(name_str) 

            _type_search = search('\|kind\|(.+?)\|', entry, DOTALL)

            if _type_search:
                _type = _type_search.group(1)
            else:
                _type = str('new')

            if not name:
                name_search = search('_(.+?)_', entry_dict['name_str'], DOTALL)
                if name_search:
                    name_str = name_search.group(1)
                    name = self._fmt.to_latex_name(name_str)

            if name not in self._latex_model._glossary['names']:
                name_key = self._fmt.to_key(name_str)
                if name_key in self._latex_model._glossary['terms']:
                    name_key = self._fmt.to_key(name_str, _type)

            else:
                name_key = self._latex_model._glossary['names'][name][0]

            columns_str = search('\|(.+?)\|\n', entry, DOTALL).groups()[0]
            columns = self._fmt.extract_row_columns_from_string(columns_str)

            entry_dict['keys'] = self._get_keys_from_template(entry, columns, columns_str)

            entries_dict[name_key] = entry_dict
            if 'name' not in entries_dict[name_key]['keys']:
                entries_dict[name_key]['keys']['name'] = name
            if _type != 'new':
                entries_dict[name_key]['keys']['kind'] = _type

            self._template['entries'] = entries_dict

            if self._get_value_from_key(name_key, 'name'):
                name = self._get_value_from_key(name_key, 'name')
                self._latex_model._glossary['names'][name] = [name_key, '\\gls{']
                self._fmt._latex_model._glossary['names'][name] = [name_key, '\\gls{']

            elif self._get_value_from_key(name_key, 'plural'):
                plural = self._get_value_from_key(name_key, 'plural')
                self._latex_model._glossary['names'][plural] = [name_key, '\\glspl{']
                self._fmt._latex_model._glossary['names'][plural] = [name_key, '\\glspl{']

            self._update_entry_in_glossary(entries_dict)


    def _get_keys_from_template(self, string, columns, columns_str):

        #Extract rows from string
        rows_str = string.split(columns_str+'|')[-1]
        rows_str_list = self._fmt.extract_row_columns_from_string(rows_str)
        rows = list()

        for col in rows_str_list:
            if len(col)>1 or (len(col)==1 and '\n' not in col):
                rows.append(col)

        rows_dict = dict()
        for i,col in enumerate(rows):
            if i%len(columns) == 0:
                key = col

            elif i%len(columns) == 1:
                rows_dict[key] = self._fmt.format_desc(col)

        return rows_dict


    def _get_value_from_key(self, entry_key, key):
        if key in self._template['entries'][entry_key]['keys']:
            return self._template['entries'][entry_key]['keys'][key]
        else:
            return str()


    def _update_entry_in_glossary(self, entries):

        for entry, entry_dict  in entries.items():
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

