from openalea.mtg.io import *
import openalea.mtg.plantframe as plantframe
import openalea.mtg.algo as algo 
from openalea.mtg import aml, dresser
from openalea.plantgl.all import norm,Vector3
from numpy import mean

def flatten(g):
    microroot = g.component_roots_at_scale(g.root,g.max_scale()).next()
    
    g = g.sub_tree(microroot,True)
    g, props = colored_tree(g,colors={1:list(g.vertices(scale=g.max_scale()))})
    
    #f = file('debug.txt','w')
    #f.write(str(g))
    #f.close()
    return g

def read_mtg(fn = 'walnut.mtg' ,drf = 'walnut.drf'):
    g = read_mtg_file(fn)

    topdia = lambda x: g.property('TopDia').get(x)

    dressing_data = dresser.dressing_data_from_file(drf)
    pf = plantframe.PlantFrame(g,  TopDiameter=topdia, 
                               DressingData = dressing_data)
    pf.propagate_constraints()

    diameters = pf.algo_diameter()
    toppositions = pf.points
    
    def botdiameter(g,topdiameter):
        botdiam = {}
        for vid,topdiam in topdiameter.iteritems():
            if g.edge_type(vid) == '<':
                botdiam[vid] = topdiameter[g.parent(vid)]
            else: botdiam[vid] = topdiam
        return botdiam
    
    g.properties()['topdiameter']=diameters
    g.properties()['bottomdiameter']=botdiameter(g,diameters)
    g.properties()['tipposition']= dict([ (k,Vector3(v)) for k,v in toppositions.iteritems()])
    
    g = flatten(g)
    return g

def color_last_year_node(g):
    def year_ancestors(i):
        ancestors = [i]
        assert g.label(i)[0] == 'U'
        while g.label(g.parent(i))[0] == 'U' :
            i = g.parent(i)
            ancestors.append(i)
        return ancestors
    leaves = [vtx for vtx in g.vertices(scale=1) if g.nb_children(vtx) == 0 and g.label(vtx)[0] == 'U']
    gu = [year_ancestors(leaf) for leaf in leaves]
    toppos = g.property('tipposition')
    def nodepos(i):
        try:
            return toppos[i]
        except:
            return toppos[g.parent(i)]
    
    def nodelength(i):
        try:
           return norm(toppos[i]-nodepos(g.parent(i)))
        except:
           return 0
    
    gul = [sum([nodelength(i) for i in ui]) for ui in gu]
    avg_length_gu = mean(gul)
    print '**', avg_length_gu, min(gul), max(gul)
    leavesly = [g.parent(i[-1]) for i in gu]
    
    def last_year_ancestors(i):
        ancestors = [i]
        l = 0
        p = nodepos(i)
        while l < avg_length_gu:
            i = g.parent(i)
            if i:
                ancestors.append(i)
                try:
                  np = toppos[i]
                  l += norm(p-np)
                  p = np
                except:
                  pass
            else:
               break
        return ancestors
    lygus = [last_year_ancestors(i) for i in leavesly]
    labels = g.property('label')
    for lygu in reversed(lygus):
        for i in lygu:
          if len([j for j in g.children(i) if labels[j][0] in 'S']) == 0:
            assert labels[i][0] in 'SV'
            labels[i] = 'V'+labels[i][1:]



def construct_walnut_lstring():
    g = read_mtg()
    color_last_year_node(g)
    return construct_lstring(g)

def write_clean_mtg(fn = 'walnut.mtg', out = 'walnut_complete.mtg', drf = 'walnut.drf'):
    g = read_mtg(fn,drf)
    color_last_year_node(g)
    positions = g.property('tipposition')
    xx = dict([(i,v.x) for i,v in positions.iteritems()])
    yy = dict([(i,v.y) for i,v in positions.iteritems()])
    zz = dict([(i,v.z) for i,v in positions.iteritems()])
    g.properties()['XX'] = xx
    g.properties()['YY'] = yy
    g.properties()['ZZ'] = zz
    
    properties = [(p, 'REAL') for p in  ['XX', 'YY', 'ZZ', 'bottomdiameter', 'topdiameter']]
    mtg_lines = write_mtg(g, properties)

    # Write the result into a file example.mtg

    f = open(out, 'w')
    f.write(mtg_lines)
    f.close()
    
if __name__ == '__main__':
    write_clean_mtg()
