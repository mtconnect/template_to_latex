
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
            raise Exception("Enter a valid latex directory path!")

        elif not path.isfile(self._path+'/main.tex'):
            raise Exception("Invalid latex directory path!")

        else:
            self._load_content()
            return "Latex directory loaded!"


    def _load_content(self):
        self._load_tables()
        self._load_glossary()
        #self._load_other_content() #other models:figures?sections?

    def _load_tables(self):
        _path = self._path+'/tables/'

        for filename in listdir(_path):

            if filename.endswith(".tex"):
                _file = open(_path+filename, 'r')
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


    def _exists(self, string): #obsolete
        if search('[a-zA-Z0-9*]+',string):
            return string
        else:
            return


    def _table_rows(self, table_name): #should also have row strings
        self._tables[table_name]['rows'] = {}
        rows = self._tables[table_name]['string'].split('\endhead')[-1].split('\hline')[:-1]

        for row in rows:
            columns = row.split('&')
            columns[-1] = columns[-1].split("\\\\")[0]
            columns.append(row)
            key = self._extract_key(columns[0])

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


    def _validate_cell_update_args(self, action, table_name, row, column, value):
        if action not in ['update','replace']:
            return
        elif table_name not in self._tables:
            return
        elif row not in self.get_table_row_names(table_name):
            return
        elif column not in self.get_table_column_names(table_name):
            return
        elif not value:
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
            self.update_table_cell(action, table_name, row, columns, values)


    def add_table_row(self, action, table_name, row, columns, values, _type = str()):
        if row in self._tables[table_name]['rows'] and _type.lower() != 'subtype':
            print (row+' already in table '+table_name+'!')
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

        if row:
            values[0] = row

        if _type == 'subType':
            quad = '\\quad '

        for index, val in enumerate(values):
            if index == 0: #assumed to be an entry
                gls_entry = val
                string_entry = '\n'+quad+'\\gls'+pl+'{'+val+'}\n&\n'

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
                    string_description+= ' \\\\\n\\hline\n\n'
                else:
                    string_description += '\n&\n'

            elif columns[index].lower() in ['element name', 'elementname']: #accounting for flexibility for use of elementname
                string_elementname = '\\glselementname{'+gls_entry+'}'+'\n&\n'

            elif columns[index].lower() == 'occurrence':
                string_occurrence = val+' \\\\\n\\hline\n\n'

            elif columns[index].lower() == 'units':
                if _type != 'subType':
                    val = gls_entry
                string_units = '\\glsentryunits{'+val+'}'+' \\\\\n\\hline\n\n'

        return string_entry+string_elementname+string_description+string_occurrence+string_units


    def update_table_cell(self, action, table_name, row, column, value):

        if not self._validate_cell_update_args(action, table_name, row, column, value):
            raise Exception ("Invalid args for update_table_cell !")

        column_index = self._get_column_index(table_name, column)

        #partioning file string to identify the substring for update
        parent_file_string = self._tables[table_name]['string']
        row_file_string = self._tables[table_name]['rows'][row][-1]
        table_cell = self.get_table_cell(table_name, row, column)

        #partitioning to identify the substring and its location
        #avoiding duplicate values
        file_string = parent_file_string.partition(row_file_string)

        #spliting at table cell substring that needs to be updated
        #table cell substring will be updated and added later
        file_sub_strings = file_string[1].split(table_cell)

        #updating the value
        if action == "update":
            self._tables[table_name]['rows'][row][column_index] += str(' \\newline '+value)

        elif action == "replace":
            #asterisks = self._tables[table_name]['rows'][row][column_index].count('*')
            asterisk_note = str()
            #for notes in latex document? perhaps change it since in uml * is entirely different
            #if asterisks: 
            #    for astrsk in range(asterisks):
            #        asterisk_note+= '*'

            self._tables[table_name]['rows'][row][column_index] = str('\n'+value+ ' '+ asterisk_note+'\n')

        #updating the table cell substring
        file_sub_strings = str(file_sub_strings[0]
                               + self._tables[table_name]['rows'][row][column_index]
                               + file_sub_strings[1])

        #updating the file string
        self._tables[table_name]['string'] = str(file_string[0] #string before updated substring
                                                 + file_sub_strings #updated table cell substring
                                                 + file_string[2]) #string after updated substring
        
        self.write_table(table_name)


    def write_table(self, table_name = None):
        if table_name not in self._tables:
            raise Exception("Invalid table name!")

        _path = self._path+'/tables/'+table_name+'.tex'

        if not path.isfile(_path):
            raise Exception("Write Error. Invalid path!")

        _file = open(_path, 'w')
        _file.write(self._tables[table_name]['string'])
        _file.close()

        return "LaTeX file successfully updated!"


    def _load_glossary(self):
        _path = self._path+'/mtc-terms.tex'

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

        string = string[:-2]+'\n}\n'

        _path = self._path+'/mtc-terms.tex'
        _file = open(_path, 'w')
        _file.write(self._glossary['string']+string)
        _file.close()

        print ("Term " + name + " of kind " + kind + " added to the glossary!")
        self._load_glossary()


    def write_glossary(self, file_name='mtc-terms-new'):
        self.format_glossary() #obsolete
        glossary_string = str()
        for key, val in self._glossary['terms'].items():
            string = """\n\n\\newglossaryentry{""" + key + """}\n{\n"""

            for k,v in val.items():
                string += '  '+k+'='+v+',\n'

            string = string[:-2]+'\n}\n'

            glossary_string+=string

        _path = self._path+'/'+file_name+'.tex'
        _file = open(_path, 'w')
        _file.write(glossary_string)
        _file.close()


    def format_glossary(self): #obsolete
        #facet for event types; need to add for sample/condition
        for key,val in self._glossary['terms'].items():
            if 'event' in val['kind'].lower():
                self._glossary['terms'][key]['facet'] = '{\\gls{string}}'


    def _create_glossary_terms(self):
        gls_substr = self._glossary['string'].split('newglossaryentry')[1:]

        for string in gls_substr:
            key = self._extract_glossary_key(string)
            values = self._extract_glossary_values(key, string)

            self._glossary['terms'][key] = values

            name = values['name'].split('{')[-1].split('}')[0]
            self._glossary['names'][name] = [key, '\\gls{'] #key, gls call

            if 'elementname' in values:
                elementname = values['elementname'].split('{')[-1].split('}')[0]
                self._glossary['names'][elementname] = [key, '\\glselementname{']

            if 'plural' in values:
                plural = values['plural'].split('{')[-1].split('}')[0]
                self._glossary['names'][plural] = [key, '\\glspl{']

            else: #few pluralization rules
                if name.endswith('s'):
                    plural = name+'ES'
                elif name.endswith('y'):
                    plural = name[:-1]+'IES'
                else:
                    plural = name+'S'
                self._glossary['names'][plural] = [key, '\\glspl{']


    def _extract_glossary_key(self, string):
        return sub('[(){}<>]', '', search('{.+?}', string).group(0))


    def _extract_glossary_values(self, parent_key, string):
        value_string = sub(parent_key, '', string, 1)
        value_string = sub('\n', '', value_string)

        value_string_list = value_string.split('{',1)[1].rsplit('}',1)[0].split(',')

        values = dict()

        for value in value_string_list:
            if '=' not in value:
                if key and value: values[key] += ','+value
                continue

            key, val = value.split('=',1)

            key = self._extract_key(key)

            values[key] = val

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

    def get_gls_key_entry_call(self, name):
        if self.get_gls_key(name):
            gls_key = self.get_gls_key(name)
            gls_string_format = self._glossary['names'][name][1]

            return gls_string_format + gls_key + '}'
        else:
            return None

if __name__=='__main__':
    latex_model = latexModel('path-to/MTConnect Part 2')
    latex_model.write_glossary()


        
