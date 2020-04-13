from os import path
from re import search, DOTALL, split
from library.generatecontent import generateContent
from library.formatcontent import formatContent

class newSectionTemplate:

    def __init__(self, config, latex_model, formatter):

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
            new_content = open(self._path,'r').read()
            self._add_new_content_to_doc(new_content)


    def _add_new_content_to_doc(self, templated_content):

        sub_templates = templated_content.split('h1. ')

        for sub_template in sub_templates[1:]:
            self._commands_dict = dict()
            self._get_content_from_template(str(), sub_template)


    def _get_content_from_template(self, doc_str, templated_content):

        self._commands_dict['part_no'] = self._get_part_no(templated_content)

        sections = self._rearrange_for_table_figures(templated_content)
        
        for i, section_commands_list in enumerate(sections):

            self._extract_commands(section_commands_list)

            if i>0: #subsection addition
                desc = section_commands_list[-1].split('\n',1)[-1]
                desc = self._format_section_content(desc)
                content_type = 'subsection'
                action = 'Add'
                position, relative_sect = str(), str()
                action_command = [action, desc, position, relative_sect]

                sub_section_name_string = section_commands_list[0].split('\n')[0]
                sub_section_name = self._fmt.format_key(sub_section_name_string)[0]

                if self._parents_dict[sub_section_name]['parent'] == 'parent':
                    parent = self._get_command('section_name')
                else:
                    parent = self._parents_dict[sub_section_name]['parent']
                parent_section_type = self._get_parent_section_type(parent, doc_str)

                doc_str = self._add_to_doc(doc_str,
                                           sub_section_name,
                                           desc,
                                           parent,
                                           parent_section_type,
                                           action_command,
                                           content_type)
            else:
                if not doc_str:
                    doc_str = self._read_doc()
                action_commands = self._get_command('action_commands')
                if not action_commands: continue

                section_name_string = section_commands_list[0].split('\n')[0]
                section_name = self._fmt.format_key(section_name_string)[0]
                self._commands_dict['section_name'] = section_name
                parent = self._get_command('parent')
                parent_section_type = self._get_parent_section_type(parent, doc_str)

                for action_command in action_commands:

                    desc = action_command[1]
                    content_type = action_command[-1]
                    doc_str = self._add_to_doc(doc_str,
                                               section_name,
                                               desc,
                                               parent,
                                               parent_section_type,
                                               action_command[:-1],
                                               content_type)



        if self._get_command('rename'):
            position = str()
            parent_sect = self._get_command('parent')
            parent_sect_type = self._get_parent_section_type(parent_sect, doc_str)
            section_type = self._subsection_type(parent_sect_type)
            section_name = self._commands_dict['section_name']
            old_content = '\n\\'+section_type+'{'+section_name+'}'
            new_content = '\n\\'+section_type+'{'+self._get_command('rename')+'}'
            doc_str = self._modify_doc_section(doc_str, 'rename', new_content, position, old_content)

        #return doc_str
        self._write_doc(doc_str)

    def _rearrange_for_table_figures(self, templated_content):

        command_list = split('(\n\* )|(\nh2. )|(\nh3. )|(\nh4. )|(\nh5. )', templated_content)

        self._parents_dict = dict()
        parent = str()
        self._parents_dict[1] = str()

        commands_list = list()
        for command in command_list:
            if command:
                commands_list.append(command)
        
        updated_section_list = list()
        updated_content_list = list()
        _type = str()

        for i, command_str in enumerate(commands_list):

            if command_str == '\n* ':
                _type = 'command'

            elif command_str.startswith('\nh'):
                _type = 'subsection'
                updated_section_list.append(updated_content_list)
                updated_content_list = list()

                heading_key = self._fmt.format_key(commands_list[i+1])[0]
                heading_level = int(command_str[2])

                self._parents_dict[heading_key] = dict()

                if not parent:
                    parent = 'parent'
                    self._parents_dict[heading_key]['parent'] = parent

                elif heading_level > self._parents_dict[parent]['heading_level']:
                    self._parents_dict[heading_key]['parent'] = parent

                elif heading_level == self._parents_dict[parent]['heading_level']:
                    self._parents_dict[heading_key]['parent'] = self._parents_dict[parent]['parent']

                elif heading_level < self._parents_dict[parent]['heading_level']:
                    self._parents_dict[heading_key]['parent'] = self._parents_dict[self._parents_dict[heading_level]]['parent']

                self._parents_dict[heading_key]['heading_level'] = heading_level
                self._parents_dict[heading_level] = heading_key
                parent = heading_key

            elif command_str.startswith('Table'):
                caption = self._fmt.format_key(search('Table:(.+?)\n',command_str).group(1))[0]
                content_update = self._add_table(caption, command_str)

                updated_content_list[-1] = updated_content_list[-1] + content_update

            elif command_str.startswith('Update Table'):
                caption = self._fmt.format_key(search('Update Table:(.+?)\n',command_str).group(1))[0]
                content_update = self._add_table(caption, command_str)

            elif command_str.startswith('Figure'):
                caption = self._fmt.format_key(search('Figure:(.+?)\n',command_str).group(1))[0]
                content_update = self._add_figure(caption, command_str)

                updated_content_list[-1] = updated_content_list[-1] + '\n' + content_update

            elif command_str.startswith('Example'):
                caption = self._fmt.format_key(search('Example:(.+?)\n',command_str).group(1))[0]
                content_update = self._add_example(caption, command_str)

                updated_content_list[-1] = updated_content_list[-1] + content_update

            elif command_str.startswith('Notes:') or command_str.startswith('Note:'):
                content_update = self._add_notes(command_str)

                updated_content_list[-1] = updated_content_list[-1] + content_update

            elif command_str.startswith('Itemized List:'):
                content_update = self._add_itemized_list(command_str)

                updated_content_list[-1] = updated_content_list[-1] + content_update

            elif command_str.startswith('End List'):
                updated_content_list[-1] = updated_content_list[-1] + '\n' + command_str.split('End List',1)[-1]

            else:
                updated_content_list.append(command_str)

        updated_section_list.append(updated_content_list)

        return updated_section_list




    def _add_to_doc(self, doc_str, section_name, section_desc, parent, parent_sect_type, action_command = list(), content_type = str()):

        new_section = list()
        action, new_content, position, old_content = action_command
        if parent_sect_type: section_type = self._subsection_type(parent_sect_type)
        else:section_type = 'section'
        

        if parent:
            split_str = '\\'+parent_sect_type+'{'+parent+'}'
            parent_sect = doc_str.split(split_str)[-1]

            for i,sect_type in enumerate(self._sect_types):
                parent_of_parent_sect = parent_sect.split('\n\\'+sect_type)
                parent_sect = parent_of_parent_sect[0]
                if i >= self._sect_types.index(parent_sect_type):
                    parent_sect = split_str + parent_sect
                    break
        else:
            parent_sect = doc_str

        if action.lower() == 'remove':
            subsection_list = parent_sect.split('\n\\'+section_type)
            for subsection in subsection_list:
                if subsection.startswith('{'+section_name+'}'):
                    sect = '\n\\'+section_type+subsection
                    break        
            
            subsection_type = self._subsection_type(section_type)
            subsubsection_list = sect.split('\n\\'+subsection_type)
            for subsubsection in subsubsection_list:
                if subsubsection.startswith('{'+action_command[-1]+'}'):
                    subsect = '\n\\'+subsection_type+subsubsection
                    break
            
            new_section_str = parent_sect.replace(sect,sect.replace(subsect,'\n\n'))
            doc_str = doc_str.replace(parent_sect, new_section_str)
            return doc_str
        
        elif 'section' in content_type:
            if action_command[-1]:
                subsection_list = parent_sect.split('\n\\'+section_type)
                for subsection in subsection_list:
                    if subsection.startswith('{'+action_command[-1]+'}'):
                        old_content = '\n\\'+section_type+subsection
                        break

            section_type_str = '\n\\'+section_type+'{'+section_name+'}'
            
            if 'paragraph' in section_type_str: section_type_str += '\\mbox{}'
            section_type_str += '\n\\label{sec:'+section_name+'}\n'

            new_content = section_type_str + section_desc
        new_section_str = self._modify_doc_section(parent_sect, action, new_content, position, old_content)

        if new_section_str not in parent_sect:
            doc_str = doc_str.replace(parent_sect, new_section_str)

        else:
            print("Duplicate: New Content for Section: "
                  + self._fmt.from_latex_name(section_name)
                  + " already in the document!")

        return doc_str


    def _modify_doc_section(self, section, action, new_content, position = str(), old_content = str()):

        action = action.lower().replace(' ','')
        position = position.lower().replace(' ','')

        if action == 'add':
            if position == 'before':
                updated_content = '\n' + new_content + '\n' + old_content
                section = section.replace(old_content, updated_content)

            elif position == 'after':
                updated_content = old_content + '\n' + new_content
                section = section.replace(old_content, updated_content)

            elif not position:
                section = section + new_content

        elif action == 'update':
            section = section.replace(old_content, new_content)

        return section


    def _get_parent_section_type(self, parent, doc_str = str()):

        parent_sect_type = str()
        sect_types = ['section','subsection','subsubsection','paragraph','subparagraph', 'ulheading']
        self._sect_types = sect_types

        if parent:
                
            for _type in sect_types:
                sect_type_str = '\\'+_type+'{'+parent+'}'
                if sect_type_str in doc_str:
                    parent_sect_type = _type
                    break

            return parent_sect_type
        else:
            return str()



    def _add_figure(self, caption, figure_str):
        content_update = str()
        label = caption.lower().replace(' ','-').replace('_','')

        filename_pattern = '!(.+?)!'
        filename_search = search(filename_pattern, figure_str)
        filename = filename_search.group(1)

        figure_latex_str = self._generate._generate_figure_str(filename,label,caption)

        content_update = content_update + figure_latex_str

        content_update = content_update + figure_str.split(filename_search.group(0))[-1]

        return content_update

    def _add_example(self, caption, example_str):
        content_update = str()
        label = caption.lower().replace(' ','-').replace('_','')

        content_pattern = '<pre>\n(.+?)\n</pre>'
        content_search = search(content_pattern, example_str, DOTALL)
        content = content_search.group(1)

        example_latex_str = self._generate._generate_example_str(content,label,caption)

        content_update = content_update + example_latex_str

        content_update = content_update + example_str.split(content_search.group(0))[-1]

        return content_update

    def _add_notes(self, note_str):

        note_latex_str = self._generate._generate_note_str(note_str)
        return note_latex_str

    def _add_itemized_list(self, itemized_list_str):

        itemized_list_str = self._generate._generate_itemized_list_str(itemized_list_str)
        return itemized_list_str

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


    def _add_table(self, caption, table_str):
        content_update = str()

        columns_str = search('\|(.+?)\|\n', table_str, DOTALL).groups()[0]
        columns = self._fmt.extract_row_columns_from_string(columns_str)

        table_str_split = split('\|', table_str)
        table_str = str('|').join(table_str_split[:-1]+[''])

        label = caption.lower().replace(' ','-').replace('_','')

        if label not in self._latex_model._tables:
            path = self._latex_model._path +'/tables/' + label + '.tex'
            self._generate.create_table(path, label, columns, caption)
            self._latex_model._load_tables()
            content_update += '\n\\input{tables/'+label+'.tex}'
            content_update += table_str_split[-1]
        else:
            content_update += '\n\\input{tables/'+label+'.tex}'
            content_update += table_str_split[-1]

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

        return content_update


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


    def _extract_commands(self, commands_list):
        self._commands_dict['action_commands'] = list()

        for command_str in commands_list:

            if command_str.startswith('Parent'):
                parent = self._get_parent_section(command_str)
                self._commands_dict['parent'] = parent

            elif command_str.startswith('Part') and not self._commands_dict['part_no']:
                part_no = self._get_part_no(command_str)
                self._commands_dict['part_no'] = part_no

            elif command_str.startswith('Rename'):
                rename = self._get_rename(command_str)
                self._commands_dict['rename'] = rename

            elif command_str.split(':')[0].endswith('Line'):
                content_type = 'line'
                action, new, position, old = self._get_line_content(command_str)
                self._commands_dict['action_commands'].append([action, new, position, old, content_type])

            elif command_str.split(':')[0].endswith('Section'):
                content_type = 'section'
                action, new, position, relative_sect = self._get_section_content(command_str)
                self._commands_dict['action_commands'].append([action, new, position, relative_sect, content_type])

                


    def _get_parent_section(self, command_str):
        pattern = 'Parent:(.+?)$'
        pattern_search = search(pattern, command_str)
        if pattern_search:
            return self._fmt.format_key(pattern_search.group(1))[0]
        else:
            return str()


    def _get_part_no(self, command_str):
        part_no_pattern = 'Part: Part(.+?)\n'
        part_no = None

        if search(part_no_pattern, command_str):
            part_no_str = search(part_no_pattern, command_str).group(1)

            if float(part_no_str) == int(float(part_no_str)):
                part_no = int(part_no_str)
            else:
                part_no = float(part_no_str)

            self._latex_model = self._get_latex_model(part_no)
            self._config.load_config("newSectionTemplate")

        return part_no


    def _get_rename(self, command_str):
        pattern = 'Rename:(.+?)$'
        pattern_search = search(pattern, command_str)
        if pattern_search:
            return self._fmt.format_key(pattern_search.group(1))[0]
        else:
            return str()

    def _get_remove(self, command_str):
        pattern = 'Remove Section:(.+?)$'
        pattern_search = search(pattern, command_str)
        if pattern_search:
            return self._fmt.format_key(pattern_search.group(1))[0]
        else:
            return str()


    def _get_line_content(self, command_str):
        pattern = ' Line: \[\[(.+?)\]\]'
        pattern_search = search(pattern, command_str, DOTALL)
        action, new, position, old = str(), str(), str(), str()
        if pattern_search:
            pre_string = command_str.split(pattern_search.group(0))[0]
            if len(pre_string.split(' '))==2:
                action, position = pre_string.split(' ')
            else:
                action = pre_string

            new = command_str.split(pattern_search.group(0))[-1]
            new = self._format_section_content(new)[2:-2]
            old = pattern_search.group(1)
            old = self._format_section_content(old)

        return action, new, position, old


    def _get_section_content(self, command_str):
        pattern = ' Section: @(.+?)@\n'
        pattern_search = search(pattern, command_str, DOTALL)
        action, new, position, relative_sect = str(), str(), str(), str()
        if pattern_search:
            pre_string = command_str.split(pattern_search.group(0))[0]
            if len(pre_string.split(' '))==2:
                action, position = pre_string.split(' ')
            else:
                action = pre_string

            new = command_str.split(pattern_search.group(0))[-1]
            new = self._format_section_content(new)
            relative_sect = pattern_search.group(1)

        return action, new, position, relative_sect



    def _get_command(self, key):
        if key in self._commands_dict.keys():
            command = self._commands_dict[key]
            if command:
                return command
            else:
                return None
        else:
            return None

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


    def _format_section_content(self, section):
        pattern = '{(section):([a-z A-Z 0-9 - _]+)}|{(table):([a-z A-Z 0-9 - _]+)}|{(example):([a-z A-Z 0-9 - _]+)}|{(figure):([a-z A-Z 0-9 - _]+)}|{(cite):(.+?)}|{(ref):(.+?)}'

        if search(pattern,section, DOTALL):
            search_result = search(pattern,section, DOTALL)
            content = search_result.group(0)
            [key,val] = content.split(':',1)
            key = key[1:]
            val = val[:-1]

            formatted_content = self._get_ref_string(key,val)

            section = section.replace(content, formatted_content)

            return self._format_section_content(section)

        else:
            return self._fmt.format_desc(section)


    def _get_ref_string(self, ref_type, caption):
        label = caption.lower().replace(' ','-').replace('_','')

        if ref_type == 'table':
            return '\\tbl{'+label+'}'

        elif ref_type == 'figure':
            return '\\fig{'+label+'}'

        elif ref_type == 'example':
            return '\\lst{'+label+'}'

        elif ref_type == 'section':
            return '\\sect{'+caption+'}'

        elif ref_type == 'cite':
            section = str()
            if ':' in caption:
                part, section = caption.split(':',1)
                part = part.replace(' ','')
                return '\\citetitle{MTC'+part+'} \\textit{Section '+caption+'}'
            else:
                part = caption.replace(' ','')
                return '\\citetitle{MTC'+part+'}'
        elif ref_type == 'ref':
            return '\\textit{Ref: '+caption+'}'

        else:
            return str()


    def _read_doc(self):
        part = self._get_command('part_no')
        _file_path = path.join(self._config.latex_model(part), self._config.doc_name(part, "section"))
        _file=open(_file_path+'.tex','r',errors='ignore')
        doc_str = _file.read()
        _file.close()
        return doc_str


    def _write_doc(self, doc_str):
        part = self._get_command('part_no')
        _file_path = path.join(self._config.latex_model(part), self._config.doc_name(part, "section"))
        _file=open(_file_path+'.tex','w')
        _file.write(doc_str)
        _file.close()
