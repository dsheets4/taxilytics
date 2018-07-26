from rest_framework import renderers


class MapRenderer(renderers.TemplateHTMLRenderer):
    template_name = 'map.html'
    context = {
        'dataObj': {
            'className': 'Rest',
            'args': {}
        },
    }
    format = 'map'
    title = 'Map'

    def get_template_context(self, data, renderer_context):
        context = {
            'data': data,
            'context': self.get_context(),
            'title': self.get_title(),
        }
        response = renderer_context['response']
        if response.exception:
            data['status_code'] = response.status_code
        return context

    def get_context(self):
        return self.context

    def get_title(self):
        return self.title
