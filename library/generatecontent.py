from os import path
from re import search, DOTALL

class generateContent:

    def __init__(self, config):
        self._content = dict()
        self._path = dict()
        self._config = config
        self._config.load_config("generateContent")
        self._get_path_to_content_templates()
        self._load_templates()


    def _get_path_to_content_templates(self):
        self._path['table'] = self._config.path_to_content_type_template('table')
        self._path['figure'] = self._config.path_to_content_type_template('figure')
        self._path['example'] = self._config.path_to_content_type_template('example')


    def _load_templates(self):
        self._content['table'] = dict()
        self._content['figure'] = dict()
        self._content['example'] = dict()
        self._content['table']['template'] = self._load_template(self._path['table'])
        self._content['figure']['template'] = self._load_template(self._path['figure'])
        self._content['example']['template'] = self._load_template(self._path['example'])


    def _load_template(self, path):
        _file = open(path,'r')
        return _file.read()


    def _generate_table_str(self, label, columns, caption):
        template  = self._content['table']['template']

        textwidth = self._get_textwidth(columns)
        caption = '\\caption{'+self._create_caption_from_label(label, caption)+'}'
        columns_str = str(' & ').join(columns)
        label_str = '\\label{' + str(':').join(['table',label]) + '}'
        ref_str = '\\ref{' + str(':').join(['table',label]) + '}'
        multicolumn = '\\multicolumn{' + str(len(columns)) + '}'

        table_str = template.replace('\\textwidth{}',textwidth)
        table_str = table_str.replace('\\caption{}',caption)
        table_str = table_str.replace('\\columns',columns_str)
        table_str = table_str.replace('\\label{}',label_str)
        table_str = table_str.replace('\\ref{}',ref_str)
        table_str = table_str.replace('\\multicolumn{}',multicolumn)

        return table_str


    def _get_textwidth(self, columns):
        textwidth = '|'
        for col in columns:
            if 'description' in col.lower():
                textwidth = textwidth+'X[3l]|'
            else:
                textwidth = textwidth+'l|'
        return '\\textwidth{'+textwidth+'}'


    def _create_caption_from_label(self, label, caption = str()):
        if not caption:
            caption = label.replace('-',' ')
            return caption.title()
        else:
            return caption


    def create_table(self, path, label, columns, caption = str()):
        table_str =  self._generate_table_str(label, columns, caption)
        _file = open(path, 'w')
        _file.write(table_str)


    def _generate_figure_str(self, filename, label, caption):
        template  = self._content['figure']['template']

        caption = '\\caption{'+caption+'}'
        label = '\\label{'+str(':').join(['fig',label])+'}'
        filename = 'figures/'+filename
        
        fig_str = template.replace('figures/',filename)
        fig_str = fig_str.replace('\\caption{}',caption)
        fig_str = fig_str.replace('\\label{}',label)

        return fig_str


    def _generate_example_str(self, content, label):
        template  = self._content['example']['template']

        caption = 'caption={'+self._create_caption_from_label(label)+'}'
        label = 'label={'+str(':').join(['lst',label])+'}'
        
        lst_str = template.replace('caption={}',caption)
        lst_str = lst_str.replace('label={}',label)
        lst_str = lst_str.replace('<>',content)

        return lst_str
