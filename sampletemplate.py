from os import path
from re import search, DOTALL

from library.formatcontent import formatContent
from library.config import config
from library.latexmodel import latexModel

class sampleTemplate:

    def __init__(self, _path = None):
        self._path = _path
        self._template = dict()
        self._config = config("sampleTemplate")
        self._latex_model = latexModel(self._config.latex_model(2))
        self._latex_model3 = latexModel(self._config.latex_model(3))

        self.fmt = formatContent(self._latex_model)
        self._load_template()

    def _load_template(self):
        if not self._path:
            raise Exception("Enter a valid LaTeX directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_glossary(template)


    def _add_all_content_to_glossary(self, template):

        part2, part3, examples2, examples3, nativeUnits, units = self._get_content_from_template(template)

        self._add_units_to_glossary(units, kind = 'units')
        self._add_units_to_glossary(nativeUnits, kind = 'nativeUnits')

        self._add_types_to_glossary(part2, 'meta')
        self._add_types_to_glossary(part3, 'observation')


    def _get_content_from_template(self, template):
        sample, part2, part3 = template.split('h2. ')

        #part2 content
        category, columns_str = search('Category: (.+?)\|(.+?)\|\n', part2, DOTALL).groups()
        category = search('@(.+?)@', category).group(1)
        self._template['category'] = category

        self._template['columns'] = dict()
        self._template['columns_str'] = dict()

        columns = self.fmt.extract_row_columns_from_string(columns_str)
        self._template['columns']['meta'] = columns
        self._template['columns_str']['meta'] = columns_str

        part2, examples2, nativeUnits, units = self._get_content_from_pattern('h2. '+part2)

        #part3 content
        columns_str = search('\|(.+?)\|\n', part3, DOTALL).groups()[0]
        columns = self.fmt.extract_row_columns_from_string(columns_str)
        self._template['columns']['observation'] = columns
        self._template['columns_str']['observation'] = columns_str

        part3, examples3 = self._get_content_from_pattern('h2. '+part3)[:2]

        return part2, part3, examples2, examples3, nativeUnits, units



    def _get_content_from_pattern(self, string):
        pattern = 'h2. (?:(.+?)h3. (.+?)h3. (.+?)h3. (.+?)\n|(.+?)h3. (.+?)h3. (.+?)\n|(.+?)h3. (.+?)\n|(.+?)\n)'
        search_result = search(pattern, string, DOTALL)
        return_dict={'content':string,'example':str(),'nativeUnits':str(),'units':str()}

        if search_result:
            if search_result.group(10):
                index = 10
                iteration = 0

            elif search_result.group(8):
                index = 8
                iteration = 1

            elif search_result.group(5):
                index = 5
                iteration = 2

            elif search_result.group(1):
                index = 1
                iteration = 3

            if index:
                if iteration:
                    for i in range(index+1,index+iteration+1):
                        if i == index+iteration:
                            content = string.split('h3. '+search_result.group(i)+'\n')[-1]
                        else:
                            content = search_result.group(i)

                        if 'example' in content.lower():
                            return_dict['example'] = content

                        elif 'nativeunit' in content.lower():
                            return_dict['nativeUnits'] = content

                        elif 'unit' in content.lower():
                            return_dict['units'] = content

                    return_dict['content'] = search_result.group(index)

                else:
                    return_dict['content'] = string.split('h2. '+search_result.group(index)+'\n')[-1]

        return list(return_dict.values())


    def _get_types_from_template(self, part, model):

        category = self._template['category']
        columns = self._template['columns'][model]
        columns_str = self._template['columns_str'][model]

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
                if _type == 'subType':
                    subType_key = self.fmt.to_key(col, _type)
                    if _type not in rows_dict[key]:
                        rows_dict[key][_type] = dict()
                    rows_dict[key][_type][subType_key] = dict()
                    rows_dict[key][_type][subType_key][subType_key] = [col]
                elif _type == 'type':
                    key = self.fmt.to_key(col, category)
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
                    subtype_name = self.fmt.to_latex_name(subtype_name)

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
                    row[2] = key
                    self._add_to_glossary(row, k, _type = 'subType', model = model, subtype_type = key)


    def _add_to_glossary(self, row, gls_key, _type = 'sample,type', subtype = list(), model = str(), subtype_type = str()):

        if model == 'meta':
            latex_model = self._latex_model

            #Expecting row content to be in the following order
            name = row[0]
            elementname = self.fmt.to_elem_name(name)
            description = row[1]
            units = row[2]
            subtype = ', '.join(subtype)

            if _type == 'subType':
                elementname = str()
                formatted_name = self.fmt.to_latex_name(name)

                if self._latex_model.get_gls_key(formatted_name):
                    print ("subType "+ name + " is already in the Glossary!")
                    gls_key = self._latex_model.get_gls_key(formatted_name)

            if not self._latex_model.get_gls_name(gls_key):
                self._latex_model.add_glossary_entry(
                    gls_key,
                    self.fmt.to_latex_name(name),
                    description,
                    'type', 'model',
                    'category', 'code',
                    'units', units,
                    'kind', _type.lower(),
                    'elementname',elementname,
                    'subtype',subtype
                    )
            table_name = self._config.table_name(2, "category")
            values = [gls_key, description, units]

        elif model == 'observation':
            latex_model = self._latex_model3

            elementname = row[1]
            description = row[2]

            table_name = self._config.table_name(3, "elementName")
            values = [gls_key, elementname, description]

        else:
            return

        if _type == 'subType':
            gls_key = str(',').join([subtype_type,gls_key])

        latex_model.update_table(
            action = 'add',
            table_name = table_name,
            row = gls_key,
            columns = self._template['columns'][model],
            values = values,
            _type = _type
            )


    def _add_units_to_glossary(self, units, kind = 'units'):

        columns, rows = self._get_units_from_template(units, kind)

        for row in rows:
            entry_name, entry_key = self._latex_model._format_units(row[0])
            self._latex_model.add_glossary_entry(
                entry_key,
                entry_name,
                row[1],
                'type', 'model',
                'category', 'code',
                'kind', kind.lower()
                )

            self._latex_model.update_table(
                action='add',
                table_name = self._config.table_name(2, kind),
                row=entry_key,
                columns=columns,
                values=[entry_key,str()]) #assumes glossary desc


    def _get_units_from_template(self, units, kind):
        if not units:
            return [], []

        columns = []
        rows = []
        row_entry = []

        units_list = units.split('|')

        for i,col in enumerate(units_list):
            if '\n' in col and len(col) < 5 and i!=0:  #length check is arbitrary
                break
            elif not('\n' in col and len(col) < 5):
                columns.append(self.fmt.format_col_name(col))


        for i,row in enumerate(units_list[len(columns)+2:]):
            if i%(len(columns)+1) <= 1:
                row_entry.append(row)

            elif i%(len(columns)+1) == 2 and row_entry:
                rows.append(row_entry)
                row_entry = []

        return columns, rows


if __name__ == '__main__':
    template = sampleTemplate('path-to/newcontent/path_data_items_samples.txt')
