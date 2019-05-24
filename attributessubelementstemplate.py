from os import path
from re import search, DOTALL

class attributesSubElementsTemplate:

    def __init__(self, config, latex_model, fmt):
        self._template = dict()
        self._config = config
        self._config.load_config("attributesSubElementsTemplate")
        self._latex_model = latex_model(2)
        self._latex_model3 = latex_model(3)
        self._fmt = fmt


    def load_new_content(self, _path):
        self._path = _path
        if not self._path:
            raise Exception("Enter a valid latex directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_glossary(template)


    def _add_all_content_to_glossary(self, template):

        model, parent, attributes, elements = self._get_content_from_template(template)

        self._add_types_to_glossary(attributes, 'attribute')
        self._add_types_to_glossary(elements, 'element')

        self._update_parent_in_glossary()


    def _get_content_from_template(self, template):

        content_pattern = 'h1. (.+?)\nh2. (.+?)\nh3. (.+?)\nh3. (.+?)\n|h1. (.+?)\nh2. (.+?)\nh3. (.+?)\n'
        search_result = search(content_pattern, template, DOTALL)
        model, parent, attributes, elements = str(), str(), str(), str()

        if search_result.group(5):
            parent = search_result.group(5)
            model = search_result.group(6)

            if 'attribute' in search_result.group(7).lower():
                attributes = 'h3. ' + template.split('h3. ')[-1]

            elif 'element' in search_result.group(7).lower():
                elements = 'h3. ' + template.split('h3. ')[-1]

        elif search_result.group(1):
            parent = search_result.group(1)
            model = search_result.group(2)

            kind_str = search_result.group(3)
            if 'attribute' in kind_str.split('\n')[0]:
                attributes = kind_str

            elif 'element' in kind_str.split('\n')[0]:
                elements = kind_str

            kind_str = search_result.group(4)
            if 'attribute' in kind_str.lower():
                attributes = 'h3. ' + template.split('h3. ')[-1]

            elif 'element' in kind_str.lower():
                elements = 'h3. ' + template.split('h3. ')[-1]

        return self._get_content_from_pattern(model, parent, attributes, elements)


    def _get_content_from_pattern(self, model, parent, attributes, elements):

        if 'part 2' in model.lower():
            model = 'meta'
        elif 'part 3' in model.lower():
            model = 'observation'
        self._template['model'] = model

        if parent:
            parent = self._fmt.to_key(self._fmt.format_key(parent)[0])
            self._create_table_name(parent, model)

        if attributes:
            self._template['attribute'] = dict()

            columns_str = search('\|(.+?)\|\n', attributes, DOTALL).groups()[0]
            columns = self._fmt.extract_row_columns_from_string(columns_str)

            self._template['attribute']['columns'] = columns
            self._template['attribute']['columns_str'] = columns_str

        if elements:
            self._template['element'] = dict()

            columns_str = search('\|(.+?)\|\n', elements, DOTALL).groups()[0]
            columns = self._fmt.extract_row_columns_from_string(columns_str)

            self._template['element']['columns'] = columns
            self._template['element']['columns_str'] = columns_str

        return model, parent, attributes, elements


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
                    self._latex_model._glossary['names'][self._fmt.to_latex_name(col)] = [key, '\\gls{']
                    rows_dict[key] = dict()
                    rows_dict[key]['_type'] = _type
                    rows_dict[key][key] = [col]
                    rows_dict[key]['initial'] = dict()

                    if self._latex_model.get_gls_name(key):
                        rows_dict[key]['initial']['parent'] = self._latex_model._glossary['terms'][key]
                    else:
                        rows_dict[key]['initial']['parent'] = None

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


    def _create_table_name(self, parent, model):
        self._template['parent'] = parent
        part_no = int()

        if model == 'meta':
            part_no = 2
        elif model == 'observation':
            part_no = 3

        attrib_table_name = self._config.table_name(part_no, "attribute") + parent
        elem_table_name = self._config.table_name(part_no, "element") + parent

        self._table_names = {'attribute':attrib_table_name,
                           'element':elem_table_name}


    def _add_to_glossary(self, row, gls_key, _type = str()):

        if self._template['model'] == 'meta':
            latex_model = self._latex_model

        elif self._template['model'] == 'observation':
            latex_model = self._latex_model3
        else:
            return

        #Expecting row content to be in the following order
        name = row[0]
        description = row[1]
        occurrence = row[2]

        if not self._latex_model.get_gls_name(gls_key):
            self._latex_model.add_glossary_entry(
                gls_key,
                self._fmt.to_latex_name(name),
                description,
                'type', 'model',
                'category', 'code',
                'kind', _type.lower()
                )

        table_name = self._table_names[_type.lower()]
        values = [gls_key, description, occurrence]

        latex_model.update_table(
            action = 'add',
            table_name = table_name,
            row = gls_key,
            columns = self._template[_type.lower()]['columns'],
            values = values,
            _type = _type
            )


    def _update_parent_in_glossary(self):
        parent = self._template['parent']
        gls_element_keys, gls_attrib_keys = str(), str()

        if 'attribute' in self._template:
            new_attrib_keys = list(self._template['attribute']['rows'].keys())

            gls_attrib_keys = self._latex_model._glossary['terms'][parent]['attributes'][:-1]

            for key in new_attrib_keys:
                if '\\gls{' + key + '}' not in gls_attrib_keys:
                    gls_attrib_keys = ','.join([gls_attrib_keys, '\\gls{' + key + '}'])

            gls_attrib_keys = gls_attrib_keys + '}'

            self._latex_model._glossary['terms'][parent]['attributes'] = gls_attrib_keys

        if 'element' in self._template:
            new_element_keys = list(self._template['element']['rows'].keys())

            gls_element_keys = self._latex_model._glossary['terms'][parent]['elements'][:-1]

            for key in new_element_keys:
                if '\\gls{' + key + '}' not in gls_element_keys:
                    gls_element_keys = ','.join([gls_element_keys, '\\gls{' + key + '}'])

            gls_element_keys = gls_element_keys + '}'

            self._latex_model._glossary['terms'][parent]['elements'] = gls_element_keys

        self._latex_model.update_gls_entry(parent)

