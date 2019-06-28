from os import path
from re import search, DOTALL

class kindTemplate:

    def __init__(self, config, latex_model, formatter):
        self._template = dict()
        self._config = config
        self._config.load_config("kindTemplate")
        self._get_latex_model = latex_model
        self._fmt = formatter


    def load_new_content(self, _path):
        self._path = _path
        if not self._path:
            raise Exception("Enter a valid latex directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_glossary(template)


    def _add_all_content_to_glossary(self, template):

        sub_templates = template.split('h1. ')[1:]
        for sub_template in sub_templates:
            sub_template = 'h1. '+sub_template

            self._template['parent_name'] = str()
            self._template['parent'] = str()
            self._update_parent = False

            parent = sub_template.split('\n')[0]

            if self._fmt.format_key(parent)[0]:
                self._template['parent_name'] = self._fmt.to_latex_name(self._fmt.format_key(parent)[0])
                self._template['parent'] = self._template['parent_name'].lower()
                self._update_parent = True

            parts = sub_template.split('h2. ')[1:]
            for part in parts:
                part = 'h2. '+part
                self._template['model'] = self._get_part_no(part)

                kinds = part.split('h3. ')[1:]
                for kind in kinds:
                    kind = 'h3. '+kind

                    kinds_str, kinds_type = self._get_content_from_template(kind)
                    self._add_types_to_glossary(kinds_str, kinds_type)
                    self._update_parent_in_glossary(kinds_type)


    def _get_part_no(self, part_str):
        part_no_pattern = 'h2. Part(.+?)\n'
        part_no = None

        if search(part_no_pattern, part_str, DOTALL):
            part_no_str = search(part_no_pattern, part_str, DOTALL).group(1)
            part_no_str = part_no_str.lower().split('part')[-1]

            if float(part_no_str) == int(float(part_no_str)):
                part_no = int(part_no_str)
            else:
                part_no = float(part_no_str)

            self._latex_model = self._get_latex_model(part_no)

        return part_no


    def _get_content_from_template(self, kinds_str):

        kinds_type_pattern = 'h3. ([a-z-A-Z]+)\n'
        #h4. examples? TBD
        kinds_type_search = search(kinds_type_pattern, kinds_str, DOTALL)
        kinds_type = kinds_type_search.group(1).lower()

        part_no = self._template['model']
        parent = self._template['parent']

        self._latex_model = self._get_latex_model(part_no)

        table_name = self._config.table_name(part_no, kinds_type)
        if table_name and '_' in table_name:
            table_name = table_name.replace('_',parent)

        elif kinds_type in self._latex_model.get_table_names():
            self._update_parent = False
            table_name = kinds_type

        self._table_names = {kinds_type :table_name}

        self._template[kinds_type] = dict()

        columns_str = search('\|(.+?)\|\n', kinds_str, DOTALL).groups()[0]
        columns = self._fmt.extract_row_columns_from_string(columns_str)

        self._template[kinds_type]['columns'] = columns
        self._template[kinds_type]['columns_str'] = columns_str

        return kinds_str, kinds_type


    def _get_types_from_template(self, string, columns, columns_str):

        #Extract rows from string
        rows_str = string.split(columns_str+'|')[-1]
        rows_str_list = self._fmt.extract_row_columns_from_string(rows_str)
        rows = list()
        
        for col in rows_str_list:
            if len(col)>1 or (len(col)==1 and '\n' not in col):
                rows.append(col)
    
        #Format rows wrt columns
        rows_dict = dict()
        for i,col in enumerate(rows):
            if i%len(columns) == 0:
                col, _type = self._fmt.format_key(col)
                if _type == 'type':
                    key = self._fmt.to_key(col)
                    name = self._fmt.to_latex_name(col)
                    if name in self._latex_model._glossary['names']:
                        key = self._latex_model._glossary['names'][name][0]
                    else:
                        self._latex_model._glossary['names'][name] = [key, '\\gls{']
                        self._fmt._latex_model._glossary['names'][name] = [key, '\\gls{']
                    rows_dict[key] = dict()
                    rows_dict[key]['_type'] = _type
                    rows_dict[key][key] = [col]

            elif i%len(columns) >= 1:
                col = self._fmt.format_desc(col)
                if _type == 'type':
                    rows_dict[key][key].append(col)

        return rows_dict


    def _add_types_to_glossary(self, string, kind):

        columns = self._template[kind]['columns']
        columns_str = self._template[kind]['columns_str']

        rows = self._get_types_from_template(string, columns, columns_str)
        self._template[kind]['rows'] = rows

        for key, val in rows.items():

            row = val[key]

            self._add_to_glossary(row, key, kind)


    def _add_to_glossary(self, row, gls_key, _type = str()):

        #Expecting row content to be in the following order
        name = row[0]
        occurrence = str()
        description = str()
        nativeunits = str()
        units = str()
        representation = str()
        elementname = str()
        kind = str()
        if self._update_parent:
            kind = _type.lower()

        columns = self._template[_type]['columns']

        for i,val in enumerate(columns):
            if 'description' in val.lower():
                description = row[i]
            elif 'occurrence' in val.lower():
                occurrence = row[i]
            elif 'nativeunits' in val.lower():
                nativeunits = row[i]
            elif 'units' in val.lower() and _type.lower() != 'units':
                units = row[i]
            elif 'representation' in val.lower():
                representation = row[i]
                elementname = self._fmt.to_elem_name(name)

        latex_name = self._fmt.to_latex_name(name)

        if not self._latex_model.get_gls_name(gls_key):
            self._latex_model.add_glossary_entry(
                gls_key,
                self._fmt.to_latex_name(name),
                description,
                'type', 'mtc',
                'category', 'model',
                'kind', kind,
                'representation', representation,
                'units', units,
                'elementname', elementname,
                'nativeunits', nativeunits
                )

        table_name = self._table_names[_type.lower()]

        if table_name not in self._latex_model.get_table_names():
            return

        latex_name = self._fmt.to_latex_name(name)
        if latex_name in self._latex_model._glossary['names']:
            gls_key = self._latex_model._glossary['names'][latex_name][0]

        row[0] = gls_key
        values = row

        self._latex_model.update_table(
            action = 'add',
            table_name = table_name,
            row = gls_key,
            columns = columns,
            values = values,
            _type = _type
            )


    def _update_parent_in_glossary(self, kinds_type):
        if not self._update_parent:
            return
        parent_name = self._template['parent_name']
        parent_key = self._latex_model._glossary['names'][parent_name][0]

        gls_keys = str()

        if kinds_type in self._template:
            new_keys = list(self._template[kinds_type]['rows'].keys())

            if kinds_type not in self._latex_model._glossary['terms'][parent_key]:
                self._latex_model._glossary['terms'][parent_key][kinds_type] = str('{}')

            gls_keys = self._latex_model._glossary['terms'][parent_key][kinds_type][:-1]

            for key in new_keys:
                if '\\gls{' + key + '}' not in gls_keys:
                    if gls_keys == '{': gls_keys = ''.join([gls_keys, '\\gls{' + key + '}'])
                    else: gls_keys = ','.join([gls_keys, '\\gls{' + key + '}'])
            gls_keys = gls_keys + '}'

            self._latex_model._glossary['terms'][parent_key][kinds_type] = gls_keys

        self._latex_model.update_gls_entry(parent_key)

