from os import path, listdir
from re import search, sub, DOTALL


class latexModel:

    def __init__(self, _path = None):
        self._path = _path
        self._tables = dict()
        self._glossary = dict()
        self._glossary['terms'] = dict()
        self._glossary['names'] = dict()
        self._create_latex_tree()


    def _create_latex_tree(self):
        if not self._path:
            return

        elif not path.isfile(path.join(self._path,'main.tex')):
            raise Exception("Invalid latex directory path!")

        else:
            self._load_content()
            return "Latex directory loaded!"


    def _load_content(self):
        self._glossary_path = path.join(self._path,'mtc-terms.tex')
        self._tables_path = path.join(self._path,'tables')
        self._load_tables()
        self._load_glossary()


    def _load_tables(self):
        _path = self._tables_path

        for filename in listdir(_path):

            if filename.endswith(".tex"):
                file_path = path.join(_path, filename)
                _file = open(file_path, 'r')
                table_name = filename.split('.')[0]

                _file_str = _file.read()
                if type(_file_str) == bytes:
                    _file_str=_file_str.decode('utf-8')

                self._tables[table_name] = {'string':_file_str}
                self._create_table_features(table_name)
                _file.close()


    def _create_table_features(self, table_name):
        self._table_heading(table_name)
        self._table_rows(table_name)


    def _table_heading(self, table_name):
        column_heading = self._tables[table_name]['string'].split('\endfirsthead')[0].split('\hline')[1]
        columns = [self._extract_key(column) for column in column_heading.split('&')]

        self._tables[table_name]['column_heading'] = columns


    def _extract_key(self, key):
        if search('{(.+?)}',key):

            if search('\\\glspl{(.+?)}',key):
                key = search('\\\glspl{(.+?)}',key).group(1)

                if key in self._glossary['terms']:
                    return self._extract_key(self._glossary['terms'][key]['plural'])
                else:
                    return self._extract_key(key)

            elif search('\\\gls{(.+?)}',key):
                key = search('\\\gls{(.+?)}',key).group(1)

                if key in self._glossary['terms']:
                    return self._extract_key(self._glossary['terms'][key]['name'])
                else:
                    return self._extract_key(key)

            else:
                return self._extract_key(search('{(.+?)}',key).group(1))

        elif key.startswith(' '):
            return self._extract_key(key[1:])

        elif key.endswith(' '):
            return self._extract_key(key[:-1])

        elif search('([a-zA-Z0-9*:]+)([a-zA-Z0-9*: ]+)([a-zA-Z0-9*:]+)',key):
            key = search('([a-zA-Z0-9*:]+)([a-zA-Z0-9*: ]+)([a-zA-Z0-9*:]+)',key).group(0)
            return key
        else:
            return key

    def _table_rows(self, table_name): #should also have row strings
        self._tables[table_name]['rows'] = {}
        rows = self._tables[table_name]['string'].split('\endhead')[-1].split('\hline')[:-1]
        type_key = str()

        for row in rows:
            columns = row.split('&')
            columns[-1] = columns[-1].split("\\\\")[0]
            columns.append(row+'\hline')
            key = self._extract_key(columns[0])

            if '\\quad' in columns[0]: #when subtype
                key = str(',').join([type_key, key])
            else:
                type_key = key
            self._tables[table_name]['rows'][key] = columns


    def _format_units(self, string):
        if not string:
            return None, None
        units_name = string
        units_name = units_name.replace(' ','').replace('@','').replace('_','\_')
        units_name = units_name.replace('^2','$^2$')

        units_entry = string.replace(' ','').replace('@','').lower()
        units_entry = units_entry.replace('^2','squared')
        units_entry = units_entry.replace('/','per')
        units_entry = units_entry.replace('_','')

        return units_name, units_entry


    def _validate_cell_update_args(self, action, table_name, row):
        if action not in ['update','replace']:
            return
        elif table_name not in self._tables:
            return
        elif row not in self.get_table_row_names(table_name):
            return
        else:
            return True


    def _get_column_index(self, table_name, column):
        return self._tables[table_name]['column_heading'].index(column)


    def get_table_names(self):
        return self._tables.keys()


    def get_table_column_names(self, table_name):
        return self._tables[table_name]['column_heading']


    def get_table_row_names(self, table_name):
        return self._tables[table_name]['rows'].keys()


    def get_table_cell(self, table_name, row, column):
        column_index = self._tables[table_name]['column_heading'].index(column)
        return self._tables[table_name]['rows'][row][column_index]


    def update_table(self, action, table_name, row, columns, values, _type = str()):
        if action == 'add':
            self.add_table_row(action, table_name, row, columns, values, _type)
        else:
            self.update_table_cell(action, table_name, row, columns, values, _type)


    def add_table_row(self, action, table_name, row, columns, values, _type = str()):

        if row in self._tables[table_name]['rows']:
            print (row+' already in table '+table_name+'!')
            print ('Updating...')
            self.update_table_cell('replace', table_name, row, columns, values, _type)
            return

        new_string = self.add_table_row_string(columns, values, False, row, _type)

        string = self._tables[table_name]['string'].split('\end{longtabu}')[0]

        self._tables[table_name]['string'] = string + new_string + '\end{longtabu}'

        self.write_table(table_name)

        print ("Row entry with key " + row + " added to the table " + table_name + " !")


    def add_table_row_string(self, columns, values, plural = False, row = None, _type = None):
        new_string = str()
        string_entry = str()
        string_elementname = str()
        string_description = str()
        string_occurrence = str()
        string_units = str()
        quad = str() #tab for subtypes in tables
        if plural:
            pl = 'pl'
            plural = 'plural'
        else:
            pl, plural = str(), str()

        if _type == 'subType':
            quad = '\\quad '
            row = row.split(',')[-1]

        if row:
            values[0] = row

        for index, val in enumerate(values):
            if index == 0: #assumed to be an entry
                gls_entry = val
                string_entry = '\n\n'+quad+'\\gls'+pl+'{'+val+'}\n&\n'

            elif columns[index].lower() == 'description':
                desc = val.split('\n')
                if len(desc)>1:
                    val = str()
                    for i, line in enumerate(desc):
                        val += line
                        if i<len(desc)-2 and len(line)>1:
                             val+='\n\\newline '
                if not val:
                    string_description = '\\glsentrydesc'+plural+'{'+values[0]+'}\n'
                else:
                    string_description = val

                if index == len(values)-1:
                    string_description+= ' \\\\\n\\hline'
                else:
                    string_description += '\n&\n'

            elif columns[index].lower() in ['element name', 'elementname']: #accounting for flexibility for use of elementname
                string_elementname = '\\glselementname{'+gls_entry+'}'+'\n&\n'

            elif columns[index].lower() == 'occurrence':
                string_occurrence = val+' \\\\\n\\hline'

            elif columns[index].lower() == 'units':
                if _type != 'subType':
                    val = gls_entry
                string_units = '\\glsentryunits{'+val+'}'+' \\\\\n\\hline'

        return string_entry+string_elementname+string_description+string_occurrence+string_units


    def update_table_cell(self, action, table_name, row, columns, values, _type = str()):

        if not self._validate_cell_update_args(action, table_name, row):
            raise Exception ("Invalid args for update_table_cell !")

        #partioning file string to identify the substring for update
        parent_file_string = self._tables[table_name]['string']
        row_file_string = self._tables[table_name]['rows'][row][-1]

        #identify the substring and its location
        #avoiding duplicate values
        file_string_list = parent_file_string.split(row_file_string)

        new_string = self.add_table_row_string(columns, values, False, row, _type)

        file_string_list = file_string_list[0] + new_string + file_string_list[-1]

        self._tables[table_name]['string'] = str().join(file_string_list)

        self.write_table(table_name)
        print ("Updated!")


    def write_table(self, table_name = None):
        if table_name not in self._tables:
            raise Exception("Invalid table name!")

        _path = path.join(self._tables_path,table_name+'.tex')

        if not path.isfile(_path):
            raise Exception("Write Error. Invalid path!")

        _file = open(_path, 'w')
        _file.write(self._tables[table_name]['string'])
        _file.close()

        return "LaTeX file successfully updated!"


    def _load_glossary(self):
        _path = self._glossary_path

        _file = open(_path,encoding="utf8" ,errors='ignore')

        _file_str = _file.read()
        if type(_file_str) == bytes:
            _file_str=_file_str.decode('utf-8')

        self._glossary['string'] = _file_str
        _file.close()

        self._create_glossary_terms()


    def add_glossary_entry(self, entry, name, description, *args):
        if entry in self._glossary['terms']:
            print (entry+' already in glossary!')
            return

        _type = str()
        plural = str()
        descpl = str()
        units = str()
        category = str()
        kind = str()
        elementname = str()
        subtype = str()
        elements = str()
        attributes = str()

        for i,arg in enumerate(args):
            if i%2 == 0:
                if arg == 'type':
                    _type = args[i+1]
                elif arg == 'plural':
                    plural = args[i+1]
                elif arg == 'descriptionplural':
                    descpl = args[i+1]
                elif arg == 'units':
                    units = self._format_units(args[i+1])[1]
                elif arg == 'category':
                    category = args[i+1]
                elif arg == 'kind':
                    kind = args[i+1]
                elif arg == 'elementname':
                    elementname = args[i+1]
                elif arg == 'subtype':
                    subtype = args[i+1]
                elif arg == 'elements':
                    elements = args[i+1]
                elif arg == 'attributes':
                    attributes = args[i+1]

        string = """\n\n\\newglossaryentry{""" + entry + """}\n{\n"""

        if _type: string += '  type='+_type+',\n'
        if category: string += '  category='+category+',\n'
        if name: string += '  name={'+name+'},\n'
        if elementname: string += '  elementname=\cfont{'+elementname+'},\n'
        if description: string += '  description={'+description+'},\n'
        if plural: string += '  plural={'+plural+'},\n'
        if descpl: string += '  descriptionplural={'+descpl+'},\n'
        if units: string += '  units=\cfont{\gls{'+units+'}},\n'
        if kind: string += '  kind={'+kind+'},\n'
        if subtype: string += '  subtype={'+subtype+'},\n'
        if attributes: string += '  attributes={'+attributes+'},\n'
        if elements: string += '  elements={'+elements+'},\n'

        string = string[:-2]+'\n}\n'

        _path = self._glossary_path
        _file = open(_path, 'w')
        _file.write(self._glossary['string']+string)
        _file.close()

        print ("Term " + name + " of kind " + kind + " added to the glossary!")
        self._load_glossary()


    def rewrite_glossary(self, file_name='mtc-terms', sort = True):
        glossary_string = str()
        terms = self._glossary['terms'].items()

        if sort: terms = sorted(terms)

        for key, val in terms:
            glossary_string_end = '\n}\n'
            gls_entry_command = self._glossary['gls_entry_command'][key]
            string = """\n\n\\"""+gls_entry_command+"""{""" + key + """}\n{\n"""

            for k,v in val.items():
                if gls_entry_command.startswith('long') and k=='description':
                    glossary_string_end = '}\n{'+v+'}\n'
                else:
                    string += '  '+k+'='+v+',\n'

            string = string[:-2]+glossary_string_end

            glossary_string+=string

        _path = self._path+'/'+file_name+'.tex'
        _file = open(_path, 'w')
        _file.write(glossary_string)
        _file.close()


    def _create_glossary_terms(self):
        string_list = self._glossary['string'].split('newglossaryentry')
        gls_substr = string_list[1:]
        string_prev = string_list[0]

        self._glossary['gls_entry_command'] = dict()

        for string in gls_substr:
            key = self._extract_glossary_key(string)

            if string_prev.endswith('long'):
                self._glossary['gls_entry_command'][key] = 'longnewglossaryentry'
            else:
                self._glossary['gls_entry_command'][key] = 'newglossaryentry'

            values = self._extract_glossary_values(key, string)
            self._glossary['terms'][key] = values

            name = values['name'].split('{')[-1].split('}')[0]

            if name in self._glossary['names']:
                if 'category' in values and 'model' in values['category']:
                    category = 'model'
                else:
                    category = 'term'
                name = str(',').join([category,name])
            else:
                category = str()

            self._glossary['names'][name] = [key, '\\gls{'] #key, gls command

            if 'elementname' in values:
                elementname = values['elementname'].split('{')[-1].split('}')[0]
                if category:
                    elementname = str(',').join([category,elementname])

                self._glossary['names'][elementname] = [key, '\\glselementname{']

            if 'plural' in values:
                plural = values['plural'].split('{')[-1].split('}')[0]
                if category:
                    plural = str(',').join([category,plural])

                self._glossary['names'][plural] = [key, '\\glspl{']

            else: #few pluralization rules
                if name[-1].islower():
                    if name.endswith('s'):
                        plural = name+'es'
                    elif name.endswith('y'):
                        plural = name[:-1]+'ies'
                    else:
                        plural = name+'s'
                elif name[-1].isupper():
                    if name.endswith('S'):
                        plural = name+'ES'
                    elif name.endswith('Y'):
                        plural = name[:-1]+'IES'
                    else:
                        plural = name+'S'

                if plural not in self._glossary['names']:
                    self._glossary['names'][plural] = [key, '\\glspl{']

            string_prev = string


    def _extract_glossary_key(self, string):
        return sub('[(){}<>]', '', search('{.+?}', string).group(0))


    def _extract_glossary_values(self, parent_key, string):
        value_string = sub(parent_key, '', string, 1)
        if not self._glossary['gls_entry_command'][parent_key].startswith('long'):
            value_string = sub('\n', '', value_string)

        value_string_list = value_string.split('{',1)[1].rsplit('}',1)[0].split(',')

        values = dict()

        for i, value in enumerate(value_string_list):

            if (self._glossary['gls_entry_command'][parent_key].startswith('long')
                    and i<len(value_string_list)-1):
                value = sub('\n', '', value)

            if '=' not in value:
                if key and value: values[key] += ','+value
                continue

            key, val = value.split('=',1)

            key = self._extract_key(key)

            values[key] = val

        if self._glossary['gls_entry_command'][parent_key].startswith('long'):

            last_value = list(values.values())[-1]
            last_key = list(values.keys())[-1]

            if len(last_value.split('}{',1)) == 2:
                val, description = last_value.split('}{',1)

            elif len(last_value.split('}\n{',1)) == 2:
                val, description = last_value.split('}\n{',1)

            values['description'] = description
            values[last_key] = val

        return values

    def get_gls_name(self, term, plural = False):
        if term in self._glossary['terms']:
            if not plural:
                return self._extract_key(self._glossary['terms'][term]['name'])
            elif 'plural' in self._glossary['terms'][term]:
                return self._extract_key(self._glossary['terms'][term]['plural'])
            else:
                return None

    def get_gls_key(self, name):
        if name in self._glossary['names']:
            return self._glossary['names'][name][0]
        else:
            return None

    def get_gls_key_entry_command(self, name, category):
        if self.get_gls_key(str(',').join([category,name])):
            name = str(',').join([category,name])
            gls_key = self.get_gls_key(name)
            gls_string_format = self._glossary['names'][name][1]

            return gls_string_format + gls_key + '}'

        elif self.get_gls_key(name):
            gls_key = self.get_gls_key(name)
            gls_string_format = self._glossary['names'][name][1]

            return gls_string_format + gls_key + '}'
            
        else:
            return None

    def update_gls_entry(self, key):
        entry_command = 'newglossaryentry'
        entry_command_end = '\n}\n\n'
        next_entry_command = '\\newglossaryentry'

        gls_string = self._glossary['string'].split(entry_command+'{'+key+'}')

        if len(gls_string) == 2:
            post_gls_string = gls_string[-1].split(entry_command,1)
            if 'newglossaryentry' not in gls_string[-1]:
                next_entry_command = str()
                post_gls_string[-1] = str()

            elif post_gls_string[0].endswith('long'):
                next_entry_command = '\\longnewglossaryentry'

            gls_string[-1] = post_gls_string[-1]

            updated_key_string = entry_command + """{""" + key + """}\n{\n"""

            for k,v in self._glossary['terms'][key].items():
                if next_entry_command == '\\longnewglossaryentry' and k == 'description':
                    entry_command_end = '\n}'+v+'\n\n'
                else:
                    updated_key_string += '  '+k+'='+v+',\n'

            updated_key_string = updated_key_string[:-2] + entry_command_end

            if next_entry_command:
                gls_string = gls_string[0] + updated_key_string + next_entry_command + gls_string[-1]
            else:
                gls_string = gls_string[0] + updated_key_string

            self._glossary['string'] = gls_string

            _path = self._glossary_path
            _file = open(_path, 'w')
            _file.write(gls_string)
            _file.close()

            print("Term "+key+" updated in the glossary!")


        elif len(gls_string)<2:
            print ('Error: '+key+' not found in glossary!')

        else:
            print ('Error: '+key+' found multiple times in glossary!')

