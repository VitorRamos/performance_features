from profiler import Analyser, flat_list
from collections import defaultdict
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import pickle
import os

bpath= '/home/vitor/Documents/performance_features/analysis/hpc_belgica_v2/'
programs= [p for p in os.listdir(bpath)]# if 'MEDIUM' in p or 'LARGE' in p]

pdic= defaultdict(lambda:[])
for p in programs:
    pname= p.split('_')[0]
    pdic[pname].append(p)

sd= {'EXTRALARGE':5, 'LARGE':4, 'MEDIUM':3, 'SMALL':2, 'MINI':1}
for p in pdic:
    pdic[p]= sorted(pdic[p],key=lambda x: sd[x.split('_')[1]],reverse=True)

def diff(df):
    x= df.values
    x= np.row_stack( (x[0,:] , x[1:,:]-x[:-1,:]) )
    return pd.DataFrame(x, columns=df.columns)

def lighten_color(color, amount=0.5):
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])

def colorgen():
    for c in plt.rcParams['axes.prop_cycle'].by_key()['color']:
        yield c

for p in list(pdic.keys()):
    try:
        os.mkdir('figures/{}'.format(p))
    except: pass
    for f in ['PERF_COUNT_HW_INSTRUCTIONS','MEM_UOPS_RETIRED:ALL_LOADS', 'MEM_UOPS_RETIRED:ALL_STORES','FP_ARITH_INST_RETIRED:SCALAR']:
        plt.figure()
        Colorgen= colorgen()
        for i, a in enumerate(pdic[p]):
            cor= next(Colorgen)
            a= Analyser(bpath+a)
            for df_ in a.data['data']:
                df= pd.DataFrame(df_,  columns= flat_list(a.data['to_monitor']))
                df= diff(df)
                x0= np.linspace(0,1,len(df[f]))
                y0= df[f]
                plt.plot(x0,y0,c=cor,label=pdic[p][i].split('_')[1])
            # y0= a.df[f]
            # x0= np.linspace(0,1,len(y0))
            # plt.plot(x0,y0,label=pdic[p][i].split('_')[1],c=lighten_color(cor,1.1),linewidth=5,linestyle="--")
        plt.title(f+' '+pdic[p][i].split('_')[1])
        from collections import OrderedDict
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())
        plt.savefig('figures/{}/{}.png'.format(p, f))

        plt.figure()
        for i, a in enumerate(pdic[p]):
            a= Analyser(bpath+a)
            x0= np.linspace(0,1,len(a.df[f]))
            y0= a.df[f]
            plt.plot(x0,y0,label=pdic[p][i].split('_')[1])
        plt.title(f)
        plt.legend()
        plt.savefig('figures/{}/{}_1.png'.format(p, f))

        plt.figure()
        for i, a in enumerate(pdic[p]):
            a= Analyser(bpath+a)
            try:
                x0, y0 = a.interpolate(f,filter_signal=False)
                plt.plot(x0,y0,label=pdic[p][i].split('_')[1])
            except:
                pass
        plt.title(f)
        plt.legend()
        plt.savefig('figures/{}/{}_2.png'.format(p, f))
        
        plt.figure()
        for i, a in enumerate(pdic[p]):
            a= Analyser(bpath+a)
            try:
                x0, y0 = a.interpolate(f)
                plt.plot(x0,y0,label=pdic[p][i].split('_')[1])
            except:
                pass
        plt.title(f)
        plt.legend()
        plt.savefig('figures/{}/{}_3.png'.format(p, f))

    plt.figure()
    for i, a in enumerate(pdic[p]):
        a= Analyser(bpath+a)
        try:
            a.df['input_size']= a.df['PERF_COUNT_HW_INSTRUCTIONS']/a.df['MEM_UOPS_RETIRED:ALL_STORES']
            a.df= a.df.dropna()
            x0, y0= a.interpolate(feature='input_size', npoints= 100)
            plt.plot(x0,y0,label=pdic[p][i].split('_')[1])
        except:
            pass
    plt.title('input_size')
    plt.legend()
    plt.savefig('figures/{}/{}_4.png'.format(p, 'input_size'))

def compare_input_sz():
    a1= Analyser(bpath+pdic['seidel-2d'][2])
    a1.df['input_size']= a1.df['PERF_COUNT_HW_INSTRUCTIONS']/a1.df['MEM_UOPS_RETIRED:ALL_STORES']
    a1.df= a1.df.dropna()
    x0, y0= a1.interpolate('input_size', 100)

    a2= Analyser(bpath+pdic['seidel-2d'][1])
    a2.df['input_size']= a2.df['PERF_COUNT_HW_INSTRUCTIONS']/a2.df['MEM_UOPS_RETIRED:ALL_STORES']
    a2.df= a2.df.dropna()
    x1, y1= a2.interpolate('input_size', 100)

    yt, err= Analyser.scale_translation_matrix(x1,y1,x0,y0)

    plt.plot(x0,y0,label='y0')
    plt.plot(x1,y1,label='y1')
    plt.plot(yt[:,0],yt[:,1],label='yt')
    plt.legend()
    plt.show()

#p='seidel-2d'
#print(pdic.keys())
"""
for p in ['seidel-2d']:
    try:
        plt.figure()
        for i, a in enumerate(pdic[p]):
            a= Analyser(bpath+a)
            a.df['input_size']= a.df['PERF_COUNT_HW_INSTRUCTIONS']/a.df['MEM_UOPS_RETIRED:ALL_STORES']
            a.df= a.df.dropna()
            x0, y0= a.interpolate(feature='input_size', npoints= 100)

            plt.plot(x0,y0,label=i)
        plt.legend()
        plt.title('{}'.format(p))
        #plt.savefig('figures/%s.png'%p)
        plt.show()
    except Exception as e:
        print(e)
"""


# x0= np.arange(0,10,1)
# y0= x0**2
# y1= 2*x0**2+10

# pt, err= Analyser.scale_translation_matrix(x0,y0,x0,y1)
# plt.plot(x0,y0)
# plt.plot(x0,y1)
# plt.plot(pt[:,0],pt[:,1])
# plt.title(err)
# plt.legend(['y0','y1','yt'])
# plt.show()
# exit(0)