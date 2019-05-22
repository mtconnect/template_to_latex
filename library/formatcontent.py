from re import search, DOTALL

class formatContent:

    def __init__(self, latex_model):
        self._latex_model = latex_model

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
        string = string.replace('_','').lower()
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

        if search('@(.+?)@',desc, DOTALL):
            category = 'model'
            term = search('@(.+?)@',desc, DOTALL)

            if term.group(1) == '\n':
                term_formatted = '\n'

            else:
                gls_name = self.to_latex_name(term.group(1))
                term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)
            if not term_formatted:
                print (term)

            desc = desc.replace(term.group(0), term_formatted)

            return self.format_desc(desc)

        elif search('\*(.+?)\*',desc, DOTALL):
            term = search('\*(.+?)\*',desc, DOTALL).group(0)
            term_formatted = '\\'+search('\*(.+?)\*',desc, DOTALL).group(1)

            desc = desc.replace(term, term_formatted)

            return self.format_desc(desc)

        elif search('_([a-z A-Z]+)_',desc):
            category = 'term'
            term = search('_([a-z A-Z]+)_',desc)
            gls_name = term.group(1)
            term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)

            desc = desc.replace(term.group(0), term_formatted)

            return desc

        return desc




