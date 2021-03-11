import tornado
from tornado.template import Template

class VarDump(tornado.web.UIModule):
    def render(self, var):
        return repr(var)


class ServerCard(tornado.web.UIModule):
    def render(self, stat):
       return self.render_string('helpers/server-card.html', stat=stat) 

class Table(tornado.web.UIModule):
    def render(self, columns: dict, data: list):
        template = Template("""
    {% autoescape None %}
    <table class="table">
    <thead>
        <tr>
            {{header}}
        <tr>
    </thead>
    <tbody>
        {{lines}}
    </tbody>
</table>"""
        ) 
        header = ''
        for column in columns:
            header += f'<th>{column:s}</th>'

        lines = ''
        for entity in data:
            line = '<tr>'
            for column in columns:
                line += f'<td>{entity[column]}</td>'
            line += '</tr>'
            lines += line

        
        return template.generate(header=header, lines=lines)