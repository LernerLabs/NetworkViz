import numpy as np
import ipycytoscape

def normalized_count_dict2(d):
    # Want 2nd most common thing, because most common is always Twist1 and it completely dominates.
    if d is None:
        return d
    biggest2 = sorted(d.values(),reverse=True)[1]
    result = {}
    for i in d:
        result[i] = d[i]/biggest2
    return result

def make_random_scores(nodes,seed=None):
    if seed is not None:
        np.random.seed(seed)
    scores = {}
    for n in nodes:
        scores[n] = np.random.randint(0,400)
    return scores


def get_graph_subset(ed,interesting_nodes=None):
    if interesting_nodes is None:
        interesting_nodes = list(set([a for (a,b) in ed] + [b for (a,b) in ed]))
    def is_interesting(k,v):
        if k in interesting_nodes:
            return True
        if v in interesting_nodes:
            return True
        return False
    
    _edges = list(set([(k,v) for (k,v) in ed if is_interesting(k,v)]))
    _nodes = list(set([i[0] for i in _edges] + [i[1] for i in _edges]))

    return _edges,_nodes


def show_graph_cytoscape(edge_dict, driver_dict, response_dict,
                             interesting_nodes=None,
                             remove_nodes=None,
                             layout='cola',
                             force_highlight=None, # force these to have artifically high scores to make them more visible.
                             score_dict=None, # a dictionary of things where we know the 'scores' ... leaving out values is fine
                             normalize_scores=True,
                             score_cutoff = 0,
                             color_by_score=True,
                             size_by_score=True,
                             ):
    """
    interesting_nodes: we will only plot these nodes or things directly connected to them
    score_dict and score_cutoff: we will color things by the scores you give here. If you give a score_cutoff, we will remove nodes that are below that cutoff.

    Notes: both interesting_nodes and score_dict/score_cutoff control which nodes are seen, which can lead to some confusion. If you specify both, we will raise an error.
    """

    if score_dict is not None and interesting_nodes is not None:
        raise ValueError("You have specified both score_dict and interesting_nodes. If you just want to plot things from score_dict, please stop specifying interesting_nodes")
    if score_dict is not None and interesting_nodes is None:
        interesting_nodes = list(score_dict.keys())
    if normalize_scores:
        score_dict = normalized_count_dict2(score_dict)

    ed = edge_dict
    dd = driver_dict
    rd = response_dict
    sd = score_dict
    data = {'nodes':[],
       'edges':[]}

    if remove_nodes:
        ed = [(a,b) for (a,b) in ed if (a not in remove_nodes) and (b not in remove_nodes)]
        dd = [n for n in dd if n not in remove_nodes]
        rd = [n for n in rd if n not in remove_nodes]
        if sd is not None:
            sd = {k:sd[k] for k in sd if k not in remove_nodes}

    _edges, _nodes = get_graph_subset(ed,interesting_nodes)
    
    e1 = len(_edges)
    n1 = len(_nodes)
    if sd is not None:
        high_scores = [n for n in sd if sd[n] >= score_cutoff]
        #_nodes = [n for n in _nodes if n in high_scores]
        _edges = [(a,b) for (a,b) in _edges if a in high_scores or b in high_scores]
    _nodes = list(set([a for (a,b) in _edges] + [b for (a,b) in _edges]))
    e2 = len(_edges)
    n2 = len(_nodes)
    print(f'I started with {e1} edges and ended up with {e2}')
    print(f'I started with {n1} nodes and ended up with {n2}')
    #print(_nodes)
    #print(_edges)
    for n in _nodes:
        nodeclass = 'intermediate'
        if n in dd:
            nodeclass = 'driver'
        elif n in rd:
            nodeclass = 'response'
        if sd is not None and n in sd:
            score = sd[n]
        else:
            score = 0.0

        if force_highlight is not None and n in force_highlight:
            score = 1.0
        data['nodes'].append( # A dictionary for each node.
            {
                'data': {
                    'id': n, 'name': n, 
                    'score': score,
                    'nodetype': {
                        'intermediate':0,
                        'response':1,
                        'driver':0.5,}[nodeclass],
                },
            }
                            
                             )

    # Drivers: light blue
    # Responses: light green
    # Everything else: light grey
    for (a,b) in _edges:
        data['edges'].append({'data':{'source':a, 'target':b,}})
    cytoscapeobj = ipycytoscape.CytoscapeWidget()
    cytoscapeobj.graph.add_graph_from_json(data)

    color_map_line = "mapData(score, 0, 1, lightgrey, lightgreen)"
    size_map_line = 'mapData(score,0,1,10,50)'
    if color_by_score:
        color_line = color_map_line
    else:
        color_line = 'lightgrey'
    if size_by_score:
        width_line,height_line = size_map_line,size_map_line
    else:
        width_line,height_line = '25','25'
    cytoscapeobj.set_style([
        {
            'selector': 'node',
            'css': {
                'content': 'data(name)',
                'text-valign': 'center',
                'color': 'black',
                'text-outline-color': 'black',
                #'border-color':'black',
                #'text-outline-width': 0.1,
                # This is a cheap and ugly hack. MGL could not get css classes to
                # correctly pick out the drivers and responses, so we make a linear
                # scale from "driver" to "response" and use cytoscape's cool `mapData`
                # function to color that. In this scale, you'll get a slightly different
                # green for the driver, because it only takes the endpoints of a linear map.
                # Feel free to improve!
                "background-color": color_line,
                'width': width_line,
                'height':height_line,
                }
        },
        { # Makes one arrow for each direction.
            'selector': 'edge',
            'style': {
                'width': 1,
                #'line-color': '#9dbaea',
                'target-arrow-shape': 'triangle',
                #'target-arrow-color': '#9dbaea',
                'curve-style': 'bezier'
                }
        },
        {
            'selector': ':selected',
            'css': {
            'background-color': 'black',
            'line-color': 'black',
            'target-arrow-color': 'black',
            'source-arrow-color': 'black',
            'text-outline-color': 'black'
                }
        },
                            ])
    cytoscapeobj.set_layout(name=layout)
    return cytoscapeobj




