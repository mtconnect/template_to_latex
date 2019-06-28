from os import path
from re import search, DOTALL
from library.generatecontent import generateContent
from library.formatcontent import formatContent

class newSectionTemplate:

    def __init__(self, config, latex_model, formatter):
        self._template = dict()
        self._contents = dict()
        self._contents['tables'] = dict()
        self._contents['figures'] = dict()
        self._contents['examples'] = dict()
        self._contents['labels'] = dict()
        self._config = config
        self._generate = generateContent(config)
        self._config.load_config("newSectionTemplate")
        self._get_latex_model = latex_model
        self._fmt = formatter


    def load_new_content(self, _path):
        self._path = _path
        if not self._path:
            raise Exception("Enter a valid latex directory path!")

        else:
            template = open(self._path,'r').read()
            self._add_all_content_to_doc(template)


    def _add_all_content_to_doc(self, template):

        sub_templates = template.split('h1. ')
        self.doc_str = str()

        for sub_template in sub_templates[1:]:
            sub_template = 'h1. '+sub_template
            section, tables, figures, examples = self._get_content_from_template(sub_template)

            self._get_tables_content(tables)
            self._get_figures_content(figures)
            self._get_examples_content(examples)
            self._get_section_content(section)

        self._write_doc(self.doc_str)


    def _get_content_from_template(self, template):
        tables, figures, examples = list(),list(),list()
        content_list = template.split('h3. ')

        section = content_list[0]
        part_no = self._get_part_no(section)

        content_pattern = '(.+?)\n'
        for content in content_list[1:]:
            if search(content_pattern, content, DOTALL):
                content_type = search(content_pattern, content, DOTALL).group(1)

                if 'table' in content_type.lower():
                    tables.append(content)
                elif 'figure' in content_type.lower():
                    figures.append(content)
                elif 'example' in content_type.lower():
                    examples.append(content)

        return section, tables, figures, examples


    def _get_part_no(self, section):
        part_no_pattern = '\* Part(.+?)\n'
        part_no = None

        if search(part_no_pattern, section, DOTALL):
            part_no_str = search(part_no_pattern, section, DOTALL).group(1)
            part_no_str = part_no_str.lower().split('part')[-1]

            if float(part_no_str) == int(float(part_no_str)):
                part_no = int(part_no_str)
            else:
                part_no = float(part_no_str)

            self._latex_model = self._get_latex_model(part_no)
            self._config.load_config("newSectionTemplate")

        self._template['model'] = part_no
        return part_no


    def _get_tables_content(self, tables):
        for table_str in tables:
            label = self._get_label_from_content(table_str)
            caption = self._get_caption_from_content(table_str)
            self._add_table(label, table_str, caption)
            

    def _add_table(self, label, table_str, caption = str()):

        columns_str = search('\|(.+?)\|\n', table_str, DOTALL).groups()[0]
        columns = self._fmt.extract_row_columns_from_string(columns_str)

        if label not in self._latex_model._tables:
            path = self._latex_model._path +'/tables/' + label + '.tex'
            self._generate.create_table(path, label, columns, caption)
            self._latex_model._load_tables()

        self._contents['tables'][label] = dict()
        self._contents['tables'][label]['string'] = '\\input{tables/'+label+'.tex}'
        self._contents['labels'][label] = 'table'

        rows = self._get_types_from_template(table_str, columns, columns_str)

        self._add_to_glossary(columns, rows)

        for key, val in rows.items():
            row = val[key]

            self._latex_model.update_table(
                action = 'add',
                table_name = label,
                row = key,
                columns = columns,
                values = row
                )


    def _add_to_glossary(self, columns, rows = dict(), _type = str()):
        for key, val in rows.items():
            row = val[key]
            if not _type:
                if 'element' in columns[0].lower():
                    _type = 'element'
                elif 'attribute' in columns[0].lower():
                    _type = 'attribute'
                elif 'enum' in columns[0].lower():
                    _type = 'enum'
                else:
                    _type = columns[0].lower().replace(' ','')

            name = row[0]
            description = str()
            if 'Description' in columns:
                description = row[columns.index('Description')]


            if not self._latex_model.get_gls_name(key):
                self._latex_model.add_glossary_entry(
                    key,
                    self._fmt.to_latex_name(name),
                    description,
                    'type', 'mtc',
                    'category', 'model',
                    'kind', _type
                    )

            elif 'kind' not in self._latex_model._glossary['terms'][key].keys():
                keys = self._latex_model._glossary['terms'][key].keys()

                if 'description' not in keys:
                    self._latex_model._glossary['terms'][key]['description'] = '{'+description+'}'

                self._latex_model._glossary['terms'][key]['kind'] = '{'+_type+'}'

                self._latex_model.update_gls_entry(key)


    def _get_types_from_template(self, part, columns, columns_str):

        #Extract rows from string
        rows_str = part.split(columns_str+'|')[-1]
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
                        category = 'model'
                        name = str(',').join([category,name])
                    self._latex_model._glossary['names'][name] = [key, '\\gls{']
                    rows_dict[key] = dict()
                    rows_dict[key]['_type'] = _type
                    rows_dict[key][key] = [col]

            elif i%len(columns) >= 1:
                self._search_types_within_desc(col)
                col = self._fmt.format_desc(col)
                if _type == 'type':
                    rows_dict[key][key].append(col)

        return rows_dict


    def _search_types_within_desc(self, desc):
        if search('\n- @(.+?)@:(.+?)@\n|\n- @(.+?)@:(.+?)',desc, DOTALL):
            category = 'model'
            term = search('\n- @(.+?)@:(.+?)@\n|\n- @(.+?)@:(.+?)',desc, DOTALL)

            if term.group(1):
                gls_name = self._fmt.to_latex_name(term.group(1))
                description = self._fmt.format_desc(term.group(2))
            else:
                gls_name = self._fmt.to_latex_name(term.group(3))
                description = desc.split('\n- @'+term.group(3)+'@:',1)[-1].split('|')[0]
                description = self._fmt.format_desc(description)
            term_formatted = self._latex_model.get_gls_key_entry_command(gls_name, category)

            if not term_formatted:
                self._latex_model.add_glossary_entry(
                    self._fmt.to_key(self._fmt.from_latex_name(gls_name)),
                    gls_name,
                    description,
                    'type', 'mtc',
                    'category', 'model'
                    )
            return self._search_types_within_desc(desc.split(term.group(0),1)[-1])
        else:
            return

    def _get_figures_content(self, figures):
        for figure_str in figures:
            label = self._get_label_from_content(figure_str)

            filename_pattern = '\|filename\|(.+?)\|\n'
            filename = search(filename_pattern, figure_str, DOTALL).group(1)

            caption_pattern = '\|caption\|(.+?)\|\n'
            caption = search(caption_pattern, figure_str, DOTALL).group(1)

            figure_latex_str = self._generate._generate_figure_str(filename,label,caption)
            self._contents['figures'][label] = dict()
            self._contents['figures'][label]['string'] = figure_latex_str
            self._contents['labels'][label] = 'figure'


    def _get_examples_content(self, examples):
        for example_str in examples:
            label = self._get_label_from_content(example_str)

            content_pattern = '<pre>\n(.+?)\n</pre>'
            content = search(content_pattern, example_str, DOTALL).group(1)

            example_latex_str = self._generate._generate_example_str(content,label)
            self._contents['examples'][label] = dict()
            self._contents['examples'][label]['string'] = example_latex_str
            self._contents['labels'][label] = 'example'


    def _get_section_content(self, section):

        pattern = 'h1. (.+?)\nh2. (.+?)\n|h1. (.+?)\n\*(.+?)\n'
        pattern_search = search(pattern, section, DOTALL)

        if pattern_search:
            if pattern_search.group(3):
                section_name_str = pattern_search.group(3)

            elif pattern_search.group(1):
                section_name_str = pattern_search.group(1).split('\n')[0]

        section_desc = section.split(pattern_search.group(0))[-1]

        
        if not self.doc_str:
            self.doc_str = self._read_doc()
        doc_str = self.doc_str

        section_name = self._fmt.format_key(section_name_str)[0]
        section_name = self._fmt.to_latex_name(section_name)
        parent, parent_sect_type = self._get_parent_section(section, doc_str)
        section_desc = self._format_section_content(section_desc)

        self._add_to_doc(doc_str, section_name, section_desc, parent, parent_sect_type)


    def _read_doc(self):
        part = self._template['model']
        _file_path = path.join(self._config.latex_model(part), self._config.doc_name(part, "section"))
        _file=open(_file_path+'.tex','r',errors='ignore')
        doc_str = _file.read()
        _file.close()
        return doc_str


    def _write_doc(self, doc_str):
        part = self._template['model']
        _file_path = path.join(self._config.latex_model(part), self._config.doc_name(part, "section"))
        _file=open(_file_path+'.tex','w')
        _file.write(doc_str)
        _file.close()


    def _subsection_type(self, sect_type):
        subsection_type = str()

        if not sect_type:
            return self._sect_types[0]

        for i, _type in enumerate(self._sect_types):
            if sect_type == _type and i < len(self._sect_types)-1:
                subsection_type = self._sect_types[i+1]
                break
            elif sect_type == _type:
                subsection_type = _type
                break

        if not subsection_type:
            subsection_type = self._sect_types[0]

        return subsection_type


    def _add_to_doc(self, doc_str, section_name, section_desc, parent, parent_sect_type):

        section_type = self._subsection_type(parent_sect_type)

        if parent:
            split_str = '\\'+parent_sect_type+'{'+parent+'}'
            parent_sect = doc_str.split(split_str)[-1]

            for sect_type in self._sect_types:
                parent_sect_type = parent_sect.split('\n\\'+sect_type)
                if len(parent_sect_type) >1:
                    break
            parent_sect = split_str + parent_sect_type[0]
        else:
            parent_sect = doc_str

        new_section = list()
        new_section.append(parent_sect)
        new_section.append('\n\\'+section_type+'{'+section_name+'}\n')
        new_section.append(section_desc)

        if str().join(new_section[1:]) not in parent_sect:
            new_section_str = str().join(new_section)
            doc_str = doc_str.replace(parent_sect, new_section_str)

            self.doc_str = doc_str
        else:
            print("Duplicate: New Content for Section "
                  + self._fmt.from_latex_name(section_name)
                  + " already in the document!")


    def _get_parent_section(self, section, doc_str = str()):
        parent_pattern = 'h2. (.+?)\n'
        parent = str()
        parent_sect_type = str()

        sect_types = ['section','subsection','subsubsection','paragraph','subparagraph', 'ulheading']
        self._sect_types = sect_types

        if search(parent_pattern, section, DOTALL):
            parent = search(parent_pattern, section, DOTALL).group(1)
            parent = self._fmt.format_key(parent)[0]

            for _type in sect_types:
                sect_type_str = '\\'+_type+'{'+parent+'}'
                if sect_type_str in doc_str:
                    parent_sect_type = _type
                    break

        return parent, parent_sect_type


    def _get_label_from_content(self, content):
        label_pattern = '\* label(.+?)\n'
        label = str()

        if search(label_pattern, content, DOTALL):
            label_str = search(label_pattern, content, DOTALL).group(1)
            label = self._fmt.format_key(label_str)[0]

        return label

    def _get_caption_from_content(self, content):
        caption_pattern = '\* caption(.+?)\n'
        caption = str()

        if search(caption_pattern, content, DOTALL):
            caption_str = search(caption_pattern, content, DOTALL).group(1)
            caption = self._fmt.format_key(caption_str)[0]

        return caption


    def _format_section_content(self, section):
        pattern = '{(ref):([a-z A-Z 0-9 -]+)}|{(table):([a-z A-Z 0-9 -]+)}|{(example):([a-z A-Z 0-9 -]+)}|{(figure):([a-z A-Z 0-9 -]+)}'

        if search(pattern,section, DOTALL):
            search_result = search(pattern,section, DOTALL)
            content = search_result.group(0)
            [key,val] = content.split(':')
            key = key[1:]
            val = val[:-1]

            content_type = self._contents['labels'][val]

            if content_type == 'table':
                formatted_content = self._get_table_from_ref(key,val)
            elif content_type == 'figure':
                formatted_content = self._get_figure_from_ref(key,val)
            elif content_type == 'example':
                formatted_content = self._get_example_from_ref(key,val)
            else:
                formatted_content = str()

            section = section.replace(content, formatted_content)

            return self._format_section_content(section)

        else:
            return self._fmt.format_desc(section)


    def _get_table_from_ref(self, key, val):
        if key == 'ref':
            return '\\tbl{'+val+'}'
        elif key == 'table':
            return self._contents['tables'][val]['string']


    def _get_figure_from_ref(self, key, val):
        if key == 'ref':
            return '\\fig{'+val+'}'
        elif key == 'figure':
            return self._contents['figures'][val]['string']

    def _get_example_from_ref(self, key, val):
        if key == 'ref':
            return '\\lst{'+val+'}'
        elif key == 'example':
            return self._contents['examples'][val]['string']
