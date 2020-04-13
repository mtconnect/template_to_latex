from os import path
from re import search, DOTALL

from library.formatcontent import formatContent

class eventTemplate:

    def __init__(self,  config, latex_model, formatter):
        self._template = dict()
        self._config = config
        self._config.load_config("eventTemplate")
        self._get_latex_model = latex_model
        self._latex_model = self._get_latex_model()
        self._fmt = formatter

    def load_new_content(self, _path):
        self._path = _path
        self._latex_model = self._get_latex_model(2) #default
        self._fmt = formatContent(self._get_latex_model())

        if not self._path:
            raise Exception("Enter a valid LaTeX directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_glossary(template)


    def _add_all_content_to_glossary(self, template):

        part2, part3, examples2, examples3 = self._get_content_from_template(template)

        self._add_types_to_glossary(part2, 'meta')
        self._fmt = formatContent(self._get_latex_model())
        self._add_types_to_glossary(part3, 'observation')


    def _get_content_from_template(self, template):
        event, part2, part3 = template.split('h2. ')

        #part2 content
        category, columns_str = search('Category: (.+?)\|(.+?)\|\n', part2, DOTALL).groups()
        category = search('@(.+?)@', category).group(1)
        self._template['category'] = category

        self._template['columns'] = dict()
        self._template['columns_str'] = dict()

        columns = self._fmt.extract_row_columns_from_string(columns_str)
        self._template['columns']['meta'] = columns
        self._template['columns_str']['meta'] = columns_str

        part2, examples2 = self._get_content_from_pattern('h2. '+part2)

        #part3 content
        columns_str = search('\|(.+?)\|\n', part3, DOTALL).groups()[0]
        columns = self._fmt.extract_row_columns_from_string(columns_str)
        self._template['columns']['observation'] = columns
        self._template['columns_str']['observation'] = columns_str

        part3, examples3 = self._get_content_from_pattern('h2. '+part3)

        return part2, part3, examples2, examples3


    def _get_content_from_pattern(self, string):
        pattern = 'h2. (?:(.+?)h3. (.+?)\n|(.+?)\n)'
        search_result = search(pattern, string, DOTALL)
        return_dict={'content':string,'example':str()}

        if search_result:
            if search_result.group(1):
                return_dict['example'] = string.split('h3. '+search_result.group(2)+'\n')[-1]
                return_dict['content'] = search_result.group(1)

            elif search_result.group(3):
                return_dict['content'] = string.split('h2. '+search_result.group(3)+'\n')[-1]

        return list(return_dict.values())


    def _get_types_from_template(self, part, model):

        category = self._template['category']
        columns = self._template['columns'][model]
        columns_str = self._template['columns_str'][model]

        #Extract rows from string
        rows_str = part.split(columns_str+'|')[-1]
        rows_str_list = self._fmt.extract_row_columns_from_string(rows_str)
        rows = list()
        
        for col in rows_str_list:
            if len(col)>1:
                rows.append(col)

        #Format rows wrt columns
        rows_dict = dict()
        for i,col in enumerate(rows):
            if i%len(columns) == 0:
                col, _type = self._fmt.format_key(col)
                if _type == 'subType':
                    subType_key = self._fmt.to_key(col, _type)
                    if _type not in rows_dict[key]:
                        rows_dict[key][_type] = dict()
                    rows_dict[key][_type][subType_key] = dict()
                    rows_dict[key][_type][subType_key][subType_key] = [col]
                elif _type == 'type':
                    key = self._fmt.to_key(col, category)
                    self._latex_model._glossary['names'][self._fmt.to_latex_name(col)] = [key, '\\gls{']
                    self._fmt._latex_model._glossary['names'][self._fmt.to_latex_name(col)] = [key, '\\gls{']
                    if category.lower() == 'event':
                        elem_name = self._fmt.to_elem_name(col)
                        self._latex_model._glossary['names'][elem_name] = [key, '\\glselementname{']
                        self._fmt._latex_model._glossary['names'][elem_name] = [key, '\\glselementname{']
                    rows_dict[key] = dict()
                    rows_dict[key]['_type'] = _type
                    rows_dict[key][key] = [col]
                    rows_dict[key]['initial'] = dict() #initial state of a glossary entry
                    if self._latex_model.get_gls_name(key):
                        rows_dict[key]['initial']['parent'] = self._latex_model._glossary['terms'][key]
                    else:
                        rows_dict[key]['initial']['parent'] = None

            elif i%len(columns) >= 1:
                col = self._fmt.format_desc(col)
                if _type == 'type':
                    rows_dict[key][key].append(col)
                elif _type == 'subType':
                    rows_dict[key][_type][subType_key][subType_key].append(col)

        return rows_dict


    def _add_types_to_glossary(self, part, model):

        rows = self._get_types_from_template(part, model)
        if model == 'meta': self._template['rows'] = rows

        for key, val in rows.items():

            row = val[key]

            #Check for subtypes of type
            
            subtype = []
            if model == 'meta' and 'subType' in val:
                for subtype_key, subtype_val in val['subType'].items():
                    subtype_name = subtype_val[subtype_key][0]
                    subtype_name = self._fmt.to_latex_name(subtype_name)

                    if self._latex_model.get_gls_key(subtype_name):
                        gls_key = self._latex_model.get_gls_key(subtype_name)
                    else:
                        gls_key = subtype_key

                    subtype_key = '\\gls{'+gls_key+'}'
                    subtype.append(subtype_key)
            #--------------------


            # adding types then its subtypes : is order significant?
            self._add_to_glossary(row, key, subtype = subtype, model = model)

            if 'subType' in val:
                for k,v in val['subType'].items():
                    row = v[k]
                    self._add_to_glossary(row, k, _type = 'subType', model = model, subtype_type = key)


    def _add_to_glossary(self, row, gls_key, _type = 'event,type', subtype = list(), model = str(), subtype_type = str()):

        if model == 'meta':
            self._latex_model = self._get_latex_model(2)
            self._fmt = formatContent(self._get_latex_model())

            #Expecting row content to be in the following order
            name = row[0]
            elementname = self._fmt.to_elem_name(name)
            description = row[1]
            subtype = ', '.join(subtype)

            formatted_name = self._fmt.to_latex_name(name)

            if self._latex_model.get_gls_key(formatted_name):
                gls_key = self._latex_model.get_gls_key(formatted_name)

            if _type == 'subType':
                elementname = str()
                
                if self._latex_model.get_gls_key(formatted_name):
                    print ("subType "+ name + " is already in the Glossary!")
                

            if not self._latex_model.get_gls_name(gls_key):
                self._latex_model.add_glossary_entry(
                    gls_key,
                    self._fmt.to_latex_name(name),
                    description,
                    'type', 'mtc',
                    'category', 'model',
                    'kind', _type.lower(),
                    'elementname',elementname,
                    'subtype',subtype
                    )
            table_name = self._config.table_name(2, "category")
            values = [gls_key, description]

        elif model == 'observation':
            self._latex_model = self._get_latex_model(3)
            self._fmt = formatContent(self._get_latex_model())

            elementname = row[1]
            description = row[2]

            formatted_name = self._fmt.to_latex_name(row[0])

            if self._latex_model.get_gls_key(formatted_name):
                gls_key = self._latex_model.get_gls_key(formatted_name)

            table_name = self._config.table_name(3, "elementName")
            values = [gls_key, elementname, description]

        else:
            return

        if _type == 'subType':
            #table row keys
            gls_key = str(',').join([subtype_type,gls_key])

        self._latex_model.update_table(
            action = 'add',
            table_name = table_name,
            row = gls_key,
            columns = self._template['columns'][model],
            values = values,
            _type = _type
            )


