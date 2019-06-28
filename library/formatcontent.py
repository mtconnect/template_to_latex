from re import search, DOTALL

class formatContent:

    def __init__(self, latex_inst):
        self._latex_model = latex_inst

    def format_key(self, string):

        key = str()
        key_kind = str()

        if search('>.@(.+?)@',string):
            key = search('>.@(.+?)@',string).group(1)
            key_kind = 'subType'

        elif search('@(.+?)@',string):
            key = search('@(.+?)@',string).group(1)
            key_kind = 'type'

        return key, key_kind


    def to_latex_name(self, string):
        latex_name = string.replace('_','\\_').replace('^2','$^2$')
        return latex_name

    def from_latex_name(self, string):
        name = string.replace('\\','').replace('$','')
        return name

    def to_key(self, string, _type = str(), separator = ' '):
        string = string.replace('_','').lower().replace('^2','squared').replace('^3','cubed').replace('^','').replace('/','per')
        if _type:
            string = string + separator + _type.lower()

        return string

    def extract_row_columns_from_string(self, string, separator = '|'):
        string_list = string.split(separator)

        for i,sub_string in enumerate(string_list):
            if sub_string.startswith('_.'):
                string_list[i] = string_list[i].replace('_.','')

        return string_list

    def format_col_name(self, string):
        return string.replace('_.','')

    def to_elem_name(self, string, separator = '_'):
        return string.title().replace(separator,'')

    def format_desc(self, desc):

        if search('\n- @(.+?)@:(.+?)@\n|\n- @(.+?)@:(.+?)',desc, DOTALL):
            category = 'model'
            term = search('\n- @(.+?)@:(.+?)@\n|\n- @(.+?)@:(.+?)',desc, DOTALL)

            if term.group(1):
                gls_name = self.to_latex_name(term.group(1))
                description = self.format_desc(term.group(2))
            else:
                gls_name = self.to_latex_name(term.group(3))
                description = desc.split('\n- @'+term.group(3)+'@:',1)[-1].split('|')[0]
                description = self.format_desc(description)
            term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)

            if not term_formatted:
                self._latex_model.add_glossary_entry(
                    self.to_key(self.from_latex_name(gls_name)),
                    gls_name,
                    description,
                    'type', 'mtc',
                    'category', 'model'
                    )
                term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)

            else:
                key = search('{(.+?)}',term_formatted).group(1)
                if 'kind' not in self._latex_model._glossary['terms'][key].keys():
                    keys = self._latex_model._glossary['terms'][key].keys()

                    if 'description' not in keys:
                        self._latex_model._glossary['terms'][key]['description'] = '{'+description+'}'

                    self._latex_model.update_gls_entry(key)

            desc = desc.replace('@'+self.from_latex_name(gls_name)+'@', term_formatted)

            return self.format_desc(desc)

        elif search('@(.+?)@',desc, DOTALL):
            category = 'model'
            term = search('@(.+?)@',desc, DOTALL)

            if '\n' in term.group(1) and term.group(1).replace(' ','').replace('-','') == '\n':
                term_formatted = '\n'
                if '-' in term.group(0):
                    term_formatted = '\n- @'

            else:
                gls_name = self.to_latex_name(term.group(1))
                term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)

            """
            if not term_formatted:
                self._latex_model.add_glossary_entry(
                    self.to_key(self.from_latex_name(gls_name)),
                    gls_name,
                    str(),
                    'type', 'mtc',
                    'category', 'model'
                    )
                term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)
            """
            if not term_formatted:
                term_formatted = self.to_key(self.from_latex_name(gls_name))
                print ("WARNING: Term '" + term_formatted + "' not defined in the glossary yet!")
                term_formatted = '\\gls{'+term_formatted+'}'
                print ("WARNING: Confirm default style '" + term_formatted + "' used in the documentation!")

            desc = desc.replace(term.group(0), term_formatted)

            return self.format_desc(desc)

        elif search('\*([a-z A-Z]+)\*',desc):
            term = search('\*([a-z A-Z]+)\*',desc)
            term_formatted = '\\'+term.group(1).replace(' ','')

            desc = desc.replace(term.group(0), term_formatted)

            return self.format_desc(desc)

        elif search('_([a-z A-Z]+)_',desc):
            category = 'term'
            term = search('_([a-z A-Z]+)_',desc)
            gls_name = term.group(1)
            term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)

            desc = desc.replace(term.group(0), term_formatted)

            return self.format_desc(desc)

        elif search('_(.+?)_',desc):
            category = 'term'
            term = search('_(.+?)_',desc)
            gls_name = term.group(1)
            term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)

            if not term_formatted:
                #Do we add new term? for italics(non-model terms)
                term_formatted = '\\textit{'+gls_name+'}'
                print ("WARNING: Please update format for '" + term_formatted + "' in the documentation!")

            desc = desc.replace(term.group(0), term_formatted)

            return self.format_desc(desc)

        elif search('---(.+?)---',desc, DOTALL):
            term = search('---(.+?)---',desc,DOTALL)
            term_formatted = '\\deprecated{'+term.group(1)+'}'

            desc = desc.replace(term.group(0), term_formatted)

            return self.format_desc(desc)

        return desc




