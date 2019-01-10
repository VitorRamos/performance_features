from collections import defaultdict
from scipy import interpolate
import pandas as pd
import numpy as np
import pickle
from matplotlib import pyplot as plt
from scipy.signal import savgol_filter

flat_list= lambda x: [ g for f in x for g in f ]
double_list= lambda x: [[g] for g in x]
split_n= lambda x, n: [x[i:i + n] for i in range(0, len(x), n)]


class Analyser:

    def __init__(self, name):
        self.data= self.load_data(name)
    
    def load_data(self, name):
        """
            load data from file
        """
        with open(name, 'rb+') as f:
            data= pickle.load(f)
        return data

    def smooth_df(self, verbose=False):
        """
            Resume multiple runs in one dataframe
            
            Remove outsamples using median split
            Average results and calculate standard deviation
        """
        # find the moda shape
        count_shapes= defaultdict(lambda:0)
        for r in self.data['data']:
            count_shapes[np.shape(r)]+=1
        moda_shape= max(count_shapes,key=count_shapes.get)
        data_moda= [d for d in self.data['data'] if np.shape(d) == moda_shape]
        
        if verbose:
            print("Moda shape counts {:.2f}%".format(count_shapes[moda_shape]/sum(count_shapes.values())*100))
            print(count_shapes[moda_shape], sum(count_shapes.values()))

        # create a big table where each row is a run
        big_l= []
        for r in data_moda:
            big_l.append(np.array(r).reshape(-1))
        big_l= np.asarray(big_l)
        
        # sort executions and remove outlines and calculate the mean an std
        med_avg= []
        std_avg= []
        for s in range(big_l.shape[1]):
            el= int(len(big_l[:,s])*0.1)//2
            median= np.sort(big_l[:,s])
            if el: median= median[el:-el]
            med_avg.append(median.mean())
            std_avg.append(median.std())
        
        med_avg= np.asarray(med_avg)
        std_avg= np.asarray(std_avg)
        
        # create the dataframe
        med_avg= pd.DataFrame(med_avg.reshape(moda_shape), columns=flat_list(self.data['to_monitor']))
        std_avg= pd.DataFrame(std_avg.reshape(moda_shape), columns=flat_list(self.data['to_monitor']))
        
        # quality of the samples (experimental)
        if verbose:
            q= std_avg.values/med_avg.values
            print("AVG 68% samples error", np.nanmean(q))
            print("AVG 99% stds error", np.nanmean(3*q))
            print("MAX 68% stds error", np.nanmax(q))
            print("MAX 99% stds error", np.nanmax(3*q))
        
        return med_avg, std_avg

    @staticmethod
    def homography_tranform(x0, y0, x1, y1):
        """
            find homography matrix and tranform y0 to y1
        """
        A = []
        for i in range(0, len(x0)):
            x, y = x0[i], y0[i]
            u, v = x1[i], y1[i]
            A.append([x, y, 1, 0, 0, 0, -u*x, -u*y, -u])
            A.append([0, 0, 0, x, y, 1, -v*x, -v*y, -v])
        A = np.asarray(A)
        U, S, Vh = np.linalg.svd(A)
        L = Vh[-1,:] / Vh[-1,-1]
        R = L.reshape(3, 3)
        
        h= np.ones(y0.shape)
        P1= np.hstack( [x0,y0,h] ).reshape((-1,3),order='F')
        P2= np.hstack( [x1,y1,h] ).reshape((-1,3),order='F')

        t_p= R.dot(P1.T).T
        return t_p, np.mean( np.abs(t_p-P2) )

    @staticmethod
    def scale_translation_matrix(x0,y0,x1,y1):
        """
        R= [[s 0 tx]
            [0 s ty]]
        R*[x
           y]=tx
        
        """
        def scf(c,x,y):
            return c[0]*x+c[1]-y
        
        from scipy.optimize import least_squares
        res= least_squares(scf,np.ones(2), args=(x0,x1), loss='cauchy')
        Rx= res.x
        res= least_squares(scf,np.ones(2), args=(y0,y1), loss='cauchy')
        Ry= res.x

        # from scipy.linalg import inv
        # A= np.vstack((x0,np.ones(x0.shape))).T
        # Rx= np.dot(inv(np.dot(A.T, A)), np.dot(A.T,x1))
        # A= np.vstack((y0,np.ones(y0.shape))).T
        # Ry= np.dot(inv(np.dot(A.T, A)), np.dot(A.T,y1))
        xt= x0*Rx[0]+Rx[1]
        yt= y0*Ry[0]+Ry[1]
        t_p= np.hstack( [xt,yt] ).reshape((-1,2),order='F')
        P2= np.hstack( [x1,y1] ).reshape((-1,2),order='F')

        return t_p, np.mean( np.abs(t_p-P2) )

    def interpolate(self, feature, npoints=100):
        def diff(df):
            x= df.values
            x= np.row_stack( (x[0,:] , x[1:,:]-x[:-1,:]) )
            return pd.DataFrame(x, columns=df.columns)

        def smooth(y, box_pts):
            box = np.ones(box_pts)/box_pts
            y_smooth = np.convolve(y, box, mode='same')
            return y_smooth

        df_m, _= self.smooth_df()
        df_m= diff(df_m)
        #df_m= df_m.apply(lambda x: smooth(x,19))
        #df_m= df_m.apply(lambda x: savgol_filter(x,npoints//2+1,3))

        f_series= df_m[feature].values

        x0, y0= np.linspace(0,1,len(f_series)), f_series
        tck = interpolate.splrep(x0, y0, s=0)
        x1 = np.linspace(0,1,npoints)
        y1 = interpolate.splev(x1, tck, der=0)
        y1= savgol_filter(y1,15,3)

        return x1, y1
    
    @staticmethod
    def compare(a1, a2, feature='PERF_COUNT_HW_INSTRUCTIONS'):
        plt.figure()
        x0, y0= a1.interpolate(feature=feature, npoints= 100)
        x1, y1= a2.interpolate(feature=feature, npoints= 100)
        #y1= 2*y0+10+2*np.random.randn(*y0.shape)
        # y0= np.log(y0)
        # y1= np.log(y1)
        yt, err= Analyser.scale_translation_matrix(x0, y0, x1, y1)
        
        plt.plot(x0,y0,)
        plt.plot(x0,y1,)
        plt.plot(yt[:,0],yt[:,1])
        plt.legend(['y0','y1','yt'])
        plt.title(err)
        return err


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

x= Analyser('/home/vitor/Documents/performance_features/analysis/hpc_belgica_v2/2mm_LARGE_DATASET_mem.dat')
y= Analyser('/home/vitor/Documents/performance_features/analysis/hpc_belgica_v2/2mm_EXTRALARGE_DATASET_mem.dat')
for f in x.smooth_df()[0].columns[:]:
    Analyser.compare(x,y,feature=f)
plt.show()

# def getHm(p1, p2):
#     A = []
#     for i in range(0, len(p1)):
#         x, y = p1[i][0], p1[i][1]
#         u, v = p2[i][0], p2[i][1]
#         A.append([x, y, 1, 0, 0, 0, -u*x, -u*y, -u])
#         A.append([0, 0, 0, x, y, 1, -v*x, -v*y, -v])
#     A = np.asarray(A)
#     U, S, Vh = np.linalg.svd(A)
#     L = Vh[-1,:] / Vh[-1,-1]
#     H = L.reshape(3, 3)
#     return H

# def fp(x, y):
#     from scipy.optimize import least_squares

#     poly= lambda c, x: sum( [c[n]*x**n for n in range(len(c))] )
#     err= lambda c,x,y: poly(c,x)-y

#     res= least_squares(err, np.ones(5), args=(x,y))
#     spoly= lambda s: poly(res.x, s)
#     return spoly


# x= np.arange(0,10,0.5)
# y= x**2
# pol= fp(x, y)
# print(pol(10))

#pol= fp(np.linspace(0,inst_s.max(), len(inst_s)), inst_s)
#plt.plot(np.linspace(0,inst_s.max(), len(inst_s)), pol(np.linspace(0,inst_s.max(), len(inst_s))))

# from scipy import interpolate
# def interp(name):
#     x= Compare()
#     data= x.load_data(name)
#     df_m, df_std= x.smooth_df(data)

#     inst_s= df_m['PERF_COUNT_HW_INSTRUCTIONS'].values
#     x0= np.linspace(0,1,len(inst_s))
#     y0= inst_s
#     print(y0)

#     tck = interpolate.splrep(x0, y0, s=0)
#     x1= np.linspace(0,1,2*len(inst_s))
#     y1 = interpolate.splev(x1, tck, der=0)
#     plt.semilogy(x1,y1)

#interp('analysis/hpc_belgica_v2/2mm_LARGE_DATASET_mem.dat')

#plt.plot(x=x0,y=df_m['PERF_COUNT_HW_INSTRUCTIONS'])
# plt.show()