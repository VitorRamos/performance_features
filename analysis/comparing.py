from profiler import Analyser, flat_list
from collections import defaultdict, OrderedDict
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import os, pickle
from tqdm import tqdm
import gc

sd= {'EXTRALARGE':5, 'LARGE':4, 'MEDIUM':3, 'SMALL':2, 'MINI':1}
bpath= '/home/vitor/Documents/performance_features/analysis/hpc_belgica_v3/'
programs= [p for p in os.listdir(bpath) if not 'MINI' in p and 'SMALL' not in p]
pdic= defaultdict(lambda:[])
for p in programs:
    pname= p.split('_')[0]
    pdic[pname].append(p)
print("Loading data to memory")
for p in tqdm(pdic):
    pdic[p]= sorted(pdic[p],key=lambda x: sd[x.split('_')[1]],reverse=True)
    for i, a in enumerate(pdic[p]):
        px= Analyser(bpath+a)
        pdic[p][i]= px

def diff(df, dt):
    x= df.values
    x= np.row_stack( (x[0,:] , x[1:,:]-x[:-1,:]) )/dt
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

def input_sz_figures(mode=0):
    print("Creating input size figures")
    for p_list in tqdm(pdic):
        #plt.figure()
        colors= colorgen()
        for i, a in p_list:
            try:
                if mode == 0:
                    a.df['input_size']= a.df['PERF_COUNT_HW_INSTRUCTIONS']/a.df['MEM_UOPS_RETIRED:ALL_STORES']
                    a.df= a.df.dropna()
                    x0, y0= a.interpolate(feature='input_size', npoints= 100)

                # diff diff interpoalated (interpoalated both)
                if mode == 1:
                    _, x0= a.interpolate(feature='PERF_COUNT_HW_INSTRUCTIONS', npoints= 100)
                    _, y0= a.interpolate(feature='MEM_UOPS_RETIRED:ALL_STORES', npoints= len(x0))

                # int diff (interpoalated mem)
                if mode == 2:
                    x0= np.cumsum(a.df['PERF_COUNT_HW_INSTRUCTIONS'])
                    _, y0= a.interpolate(feature='MEM_UOPS_RETIRED:ALL_STORES', npoints= len(x0))

                # int diff
                if mode == 3:
                    x0= np.cumsum(a.df['PERF_COUNT_HW_INSTRUCTIONS'])
                    y0= a.df['MEM_UOPS_RETIRED:ALL_STORES']

                # int int
                if mode == 4:
                    x0= np.cumsum(a.df['PERF_COUNT_HW_INSTRUCTIONS'])
                    y0= np.cumsum(a.df['MEM_UOPS_RETIRED:ALL_STORES'])

                plt.plot(x0,y0,label=pdic[p][i].split('_')[1], c=next(colors))
            except Exception as e:
                print(e)
        plt.legend()
        plt.title('{}'.format(p))
        plt.savefig('figures/%s.png'%p)
        plt.close()
        #plt.show()

def features_figures():
    print("Create workflow figures")
    for p_list,p in zip(pdic.values(),pdic.keys()):
        print("Program ", p)
        print("Garbage Collector cleans ", gc.collect())
        try:
            os.mkdir('figures/{}'.format(p))
        except: pass
        for f in ['PERF_COUNT_HW_INSTRUCTIONS','MEM_UOPS_RETIRED:ALL_LOADS', 'MEM_UOPS_RETIRED:ALL_STORES','FP_ARITH_INST_RETIRED:SCALAR']:
            Colorgen= colorgen()
            for i, a in enumerate(p_list):
                cor= next(Colorgen)
                for df_ in a.data['data']:
                    df= pd.DataFrame(df_,  columns= flat_list(a.data['to_monitor']))
                    df= diff(df, a.data['sample_period'])
                    x0= np.linspace(0,1,len(df[f]))
                    y0= df[f]
                    plt.plot(x0,y0,c=cor,label=a.name.split('/')[-1].split('_')[1])
                # y0= a.df[f]
                # x0= np.linspace(0,1,len(y0))
                # plt.plot(x0,y0,label=a.name.split('_')[1],c=lighten_color(cor,1.1),linewidth=5,linestyle="--")
            plt.title(f)
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = OrderedDict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys())
            plt.savefig('figures/{}/{}.png'.format(p, f))
            plt.close()

            for i, a in enumerate(p_list):
                x0= np.linspace(0,1,len(a.df[f]))
                y0= a.df[f]
                plt.plot(x0,y0,label=a.name.split('/')[-1].split('_')[1])
            plt.title(f)
            plt.legend()
            plt.savefig('figures/{}/{}_1.png'.format(p, f))
            plt.close()

            for i, a in enumerate(p_list):
                try:
                    x0, y0 = a.interpolate(f,filter_signal=False)
                    plt.plot(x0,y0,label=a.name.split('/')[-1].split('_')[1])
                except:
                    pass
            plt.title(f)
            plt.legend()
            plt.savefig('figures/{}/{}_2.png'.format(p, f))
            plt.close()
            
            for i, a in enumerate(p_list):
                try:
                    x0, y0 = a.interpolate(f)
                    plt.plot(x0,y0,label=a.name.split('/')[-1].split('_')[1])
                except:
                    pass
            plt.title(f)
            plt.legend()
            plt.savefig('figures/{}/{}_3.png'.format(p, f))
            plt.close()

        for i, a in enumerate(p_list):
            try:
                a.df['input_size']= a.df['PERF_COUNT_HW_INSTRUCTIONS']/a.df['MEM_UOPS_RETIRED:ALL_STORES']
                a.df= a.df.dropna()
                x0, y0= a.interpolate(feature='input_size', npoints= 100)
                plt.plot(x0,y0,label=a.name.split('/')[-1].split('_')[1])
            except:
                pass
        plt.title('input_size')
        plt.legend()
        plt.savefig('figures/{}/{}_4.png'.format(p, 'input_size'))
        plt.close()

def compare_input_sz(p1, p2):
    a1= Analyser(bpath+p1)
    a1.df['input_size']= a1.df['PERF_COUNT_HW_INSTRUCTIONS']/a1.df['MEM_UOPS_RETIRED:ALL_STORES']
    a1.df= a1.df.dropna()
    x0, y0= a1.interpolate('PERF_COUNT_HW_INSTRUCTIONS', 100)

    a2= Analyser(bpath+p2)
    a2.df['input_size']= a2.df['PERF_COUNT_HW_INSTRUCTIONS']/a2.df['MEM_UOPS_RETIRED:ALL_STORES']
    a2.df= a2.df.dropna()
    x1, y1= a2.interpolate('PERF_COUNT_HW_INSTRUCTIONS', 100)

    yt, err= Analyser.scale_translation_matrix(x1,y1,x0,y0)
    #yt, err= Analyser.homography_tranform(x1,y1,x0,y0)

    plt.plot(x0,y0,label='y0')
    plt.plot(x1,y1,label='y1')
    plt.plot(yt[:,0],yt[:,1],label='yt')
    plt.legend()
    plt.show()

features_figures()
#input_sz_figures()
#compare_input_sz(pdic['3mm'][2], pdic['2mm'][2])