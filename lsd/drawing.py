import plotly.graph_objects as go
import warnings
from dataclasses import dataclass
from .spacer import SpaceManager
from .read import Level, Transition, read
from .styles import levelstyles
import numpy as np
import copy


class Canvas(go.Figure):
    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.update_layout(xaxis=go.layout.XAxis(visible=False, autorange=False, range=(0,1)),
                           yaxis=go.layout.YAxis(visible=False),
                           template='simple_white',
                           margin=dict(t=20,l=20,b=20,r=20))
    
    def add_level(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0, style: str='',
                  name='', spin='', parity='',
                  trace_kw={}, annotations_kw={}):
        
        if width>1 or width<0:
            raise ValueError("width is relative width and must be between 0 and 1")
        
        
        
        style= style.lower()
        Style = levelstyles[style]
        levelstyle = Style(x, y, width, height)
        trace_kw["mode"] = 'lines'
        trace_kw["showlegend"] = False
        trace = levelstyle.get_line(**trace_kw)
        self.add_trace(trace)
        
        for st, anno in zip(levelstyle.labels(name=name, spin=spin, parity=parity), levelstyle.get_annotations()):
            self.add_annotation(x=anno[0],
                               y=anno[1],
                               text=st,
                               xref='x',
                               yref='y',
                               showarrow=False,
                               xanchor='right',
                               yanchor='bottom',
                               **annotations_kw)
            
    def add_transition(self, px=None, py=None, dx=None, dy=None, **kwargs):
        if None in [px,py,dx,dy]:
            raise ValueError(f"(px,py,dx,dy) must all be specified: {px,py,dx,dy} not valid")
        if px<0 or px>1 or dx<0 or dx>1:
            raise ValueError("x positions must be in relative units")
        
        kwargs["xref"] = 'x'
        kwargs["axref"] = 'x'
        kwargs['yref'] = 'y'
        kwargs['ayref'] = 'y'
        
        self.add_annotation(x=dx, y=dy, ax=px, ay=py, **kwargs)
            
    def read_from_nlv(self, filename:str, spacing=100, x_points=np.linspace(0.2,0.8,10),
                      transition_sort: callable = None, proportional=False, level_kw={}, transition_kw={}):
        levels, transitions = read(filename)
        
        float_levels = []
        for level in levels:
            float_levels.append(level.energy)
        
        if 'style' in level_kw.keys():
            Style = levelstyles[level_kw['style']]
            reverse = Style(0,0,0,0).reverse
        else:
            reverse=False
        
        
        spc_mng = SpaceManager(x_points, float_levels, spacing=spacing, reverse=reverse)
        
        
        defaults = dict(x=0.5, width=1, style='flat', height=10, trace_kw=dict(line=dict(color='black')))
        # make the levels
        for level in levels:
            for default in defaults.keys():
                if default not in list(level_kw.keys()):
                    
                    level_kw[default] = defaults[default]
            
            available_y = spc_mng.get_spaced_y(level.energy)
            # print(level.energy, available_y)
            if level.spin == None:
                spin = ''
            else:
                spin = str(level.spin)
                
            if level.parity == None:
                parity = ''
            else:
                parity = str(level.parity)

            if proportional:
                level_kw_cp = copy.deepcopy(level_kw) 
                level_kw_cp['height'] += abs(available_y - level.energy)
                self.add_level(y=level.energy, name=str(level.energy), spin=spin, parity=parity, **level_kw_cp)
                
            else:
                self.add_level(y=available_y, name=str(level.energy), spin=spin, parity=parity, **level_kw)
            
        
        if transition_sort is None:
            transitions.sort(key=lambda transition: transition.parent.energy)
        else:
            transitions.sort(key=transition_sort)
            
        # make the transitions
        defaults = dict(showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5, arrowcolor='black', text='')
        for transition in transitions:
            for default in defaults.keys():
                if default not in list(transition_kw.keys()):
                    transition_kw[default] = defaults[default]
            available_x = spc_mng.get_path(transition.parent.energy, transition.daughter.energy)
            available_y_head = spc_mng.get_spaced_y(transition.daughter.energy)
            available_y_tail = spc_mng.get_spaced_y(transition.parent.energy)
            
            if proportional:
                self.add_transition(px=available_x,
                                    dx=available_x,
                                    py=transition.parent.energy,
                                    dy=transition.daughter.energy,
                                    **transition_kw)
            else:
                self.add_transition(px=available_x,
                                    dx=available_x,
                                    py=available_y_tail,
                                    dy=available_y_head,
                                    **transition_kw)
        
        
        
        
            
        


    