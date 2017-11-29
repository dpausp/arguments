import jinja2


class Cell:
    """
    View model base class which is basically a wrapper around a template.
    Templates can access attributes of the cell and some selected model properties directly.
    """
    model_properties = []

    def __init__(self, model, request, template_path=None):
        self._model = model
        self._request = request
        self._template_path = template_path

    @property
    def template_path(self):
        if self._template_path is None:
            name = self._model.__class__.__name__.lower()
            self._template_path = name + ".j2.jade"
        
        return self._template_path

    def render_template(self, template_path):
        return self._request.render_template(template_path, _cell=self)
        
    def link(self, model):
        return self._request.link(model)

    def __getattr__(self, name):
        if name in self.model_properties:
            return getattr(self._model, name)

        raise AttributeError()
    
    def __getitem__(self, name):
        if hasattr(self, name):
            return getattr(self, name)
        
        if name in self.model_properties:
            return getattr(self._model, name)

        raise KeyError()
    
    def __contains__(self, name):
        return name in self.model_properties or hasattr(self, name)
    
    def show(self):
        return self.render_template(self.template_path)
    
    
class JinjaCellContext(jinja2.runtime.Context):
    """
    Custom jinja context with the ability to look up template variables in a cell (view model)
    """
    
    def __init__(self, environment, parent, name, blocks):
        super().__init__(environment, parent, name, blocks)
        self._cell = parent.get('_cell')
    
    def resolve_or_missing(self, key):
        if self._cell and key in self._cell:
            return self._cell[key]
            
        return super().resolve_or_missing(key)
    
    def __contains__(self, name):
        if self._cell and name in self._cell:
            return True
        
        return super().__contains__(name)


class JinjaCellEnvironment(jinja2.Environment):
    """
    Example jinja environment class which uses the JinjaCellContext
    """
    context_class = JinjaCellContext
    