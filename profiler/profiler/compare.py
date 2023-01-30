import pickle
from collections import defaultdict

import pandas as pd
import numpy as np

from scipy.signal import savgol_filter
from scipy import interpolate
from scipy.optimize import least_squares
from scipy import integrate

flat_list = lambda x: [g for f in x for g in f]
double_list = lambda x: [[g] for g in x]
split_n = lambda x, n: [x[i : i + n] for i in range(0, len(x), n)]


class Analyser:
    def __init__(self, name, method="moda", npoints=100):
        self.name = name
        if type(name) == str:
            self.data = self.load_data(name)
        else:
            self.data = name
        if method == "moda":
            self.df, _ = self.moda_df()
        elif method == "interpolation":
            self.df = self.interpolated_df(npoints)

    def load_data(self, name):
        """
        load data from file
        """
        with open(name, "rb+") as f:
            data = pickle.load(f)
        return data

    def moda_df(self, verbose=False):
        """
        Resume multiple runs in one dataframe

        Remove outsamples using median split
        Average results and calculate standard deviation
        """
        # find the moda shape
        count_shapes = defaultdict(lambda: 0)
        for r in self.data["data"]:
            count_shapes[np.shape(r)] += 1
        moda_shape = max(count_shapes, key=count_shapes.get)
        data_moda = [d for d in self.data["data"] if np.shape(d) == moda_shape]

        if verbose:
            print(
                "Moda shape counts {:.2f}%".format(
                    count_shapes[moda_shape] / len(count_shapes.values()) * 100
                )
            )
            print(count_shapes[moda_shape], sum(count_shapes.values()))

        el = int(count_shapes[moda_shape] * 0.3) // 2
        data_moda = np.asarray(data_moda)
        med_avg = np.sort(data_moda, axis=0)

        if el != 0:
            med_avg = med_avg[el:-el]

        def diff(x):
            x = (
                np.concatenate((x[:, 0:1, :], x[:, 1:, :] - x[:, :-1, :]), axis=1)
                / self.data["sample_period"]
            )
            return x

        med_avg = diff(med_avg)
        std_avg = med_avg.std(axis=0)
        med_avg = med_avg.mean(axis=0)

        # create the dataframe
        med_avg = pd.DataFrame(med_avg, columns=flat_list(self.data["to_monitor"]))
        std_avg = pd.DataFrame(std_avg, columns=flat_list(self.data["to_monitor"]))

        # quality of the samples (experimental)
        if verbose:
            q = std_avg.values / med_avg.values
            print("AVG 68% samples error", np.nanmean(q) * 100)
            print("AVG 99% samples error", np.nanmean(3 * q) * 100)

            print("MAX 68% samples error", np.nanmax(q) * 100)
            print("MAX 99% samples error", np.nanmax(3 * q) * 100)

        return med_avg, std_avg

    def interpolated_df(self, npoints=100):
        new_data = []
        for r in self.data["data"]:
            x = np.asarray(r)
            new_c = []
            for c in range(x.shape[1]):
                fserie = np.trim_zeros(x[:, c])
                if len(fserie) < 4:
                    if len(fserie) >= 1:
                        fserie = np.hstack((fserie, [fserie[-1]] * (4 - len(fserie))))
                    else:
                        fserie = np.hstack((fserie, [0] * (4 - len(fserie))))
                x0, y0 = np.linspace(0, 1, len(fserie)), fserie
                tck = interpolate.splrep(x0, y0, s=0)
                x1 = np.linspace(0, 1, npoints)
                y1 = interpolate.splev(x1, tck, der=0)
                new_c.append(list(y1))
            new_data.append(new_c)

        new_data = np.asarray(new_data)
        # med_avg= []
        # el= int(len(self.data['data'])*0.2)
        # for c in range(new_data.shape[1]):
        #     vals= new_data[:,c,:]
        #     vals= np.sort(vals, axis=0)[el:-el,:]
        #     med_avg.append(vals.mean(axis=0))

        # med_avg= new_data.mean(axis=0)
        # med_avg= pd.DataFrame(np.asarray(med_avg).T, columns=flat_list(self.data['to_monitor']))

        # NEED TO TEST THIS
        el = int(len(self.data["data"]) * 0.3) // 2
        med_avg = np.sort(new_data, axis=0)
        std_avg = np.sort(new_data, axis=0)
        if el != 0:
            med_avg = med_avg[el:-el].mean(axis=0)
            std_avg = std_avg[el:-el].std(axis=0)
        else:
            med_avg = med_avg.mean(axis=0)
            std_avg = std_avg.mean(axis=0)
        # NEED TO TEST THIS

        med_avg = pd.DataFrame(med_avg, columns=flat_list(self.data["to_monitor"]))

        count_shapes = defaultdict(lambda: 0)
        for r in self.data["data"]:
            count_shapes[np.shape(r)] += 1
        moda_shape = max(count_shapes, key=count_shapes.get)

        def diff(df):
            x = df.values
            x = np.row_stack((x[0, :], x[1:, :] - x[:-1, :])) / (
                self.data["sample_period"] * moda_shape[0] / npoints
            )
            return pd.DataFrame(x, columns=df.columns)

        med_avg = diff(med_avg)
        for c in med_avg.columns:
            med_avg[c] = savgol_filter(med_avg[c].values, 11, 3)

        return med_avg

    def interpolate(self, feature, npoints=100, filter_signal=True, proportional=False):
        f_series = np.trim_zeros(self.df[feature].values)
        if f_series.shape[0] < 4:
            raise Exception("Cant interpolate")

        x0, y0 = np.linspace(0, 1, len(f_series)), f_series
        tck = interpolate.splrep(x0, y0, s=0)
        x1 = np.linspace(0, 1, npoints)
        y1 = interpolate.splev(x1, tck, der=0)

        if filter_signal:
            y1 = savgol_filter(y1, 11, 3)

        if proportional:
            I = integrate.simps(y0)  # ,dx=self.data['sample_period'])
            Ia = integrate.simps(y1)  # ,dx=1.0/npoints)
            y1 *= I / Ia
            # Ic= integrate.simps(y1,dx=1.0/npoints)
            # print(I, Ia, Ic)

        return x1, y1

    @staticmethod
    def homography_tranform(x0, y0, x1, y1):
        """
        find homography matrix and tranform y0 to y1
        """
        A = []
        for i in range(0, len(x0)):
            x, y = x0[i], y0[i]
            u, v = x1[i], y1[i]
            A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
            A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
        A = np.asarray(A)
        U, S, Vh = np.linalg.svd(A)
        L = Vh[-1, :] / Vh[-1, -1]
        R = L.reshape(3, 3)

        h = np.ones(y0.shape)
        P1 = np.hstack([x0, y0, h]).reshape((-1, 3), order="F")
        P2 = np.hstack([x1, y1, h]).reshape((-1, 3), order="F")

        t_p = R.dot(P1.T).T
        return t_p, np.mean(np.abs(t_p - P2))

    @staticmethod
    def scale_translation_matrix(x0, y0, x1, y1):
        """
        find the scale and translation matrix from (x0,y0) to (x1,y1)
        """

        def scf(c, x, y):
            return c[0] * x + c[1] - y

        Rx = least_squares(scf, np.ones(2), args=(x0, x1), loss="soft_l1").x
        Ry = least_squares(scf, np.ones(2), args=(y0, y1), loss="soft_l1").x

        # from scipy.linalg import inv
        # A= np.vstack((x0,np.ones(x0.shape))).T
        # Rx= np.dot(inv(np.dot(A.T, A)), np.dot(A.T,x1))
        # A= np.vstack((y0,np.ones(y0.shape))).T
        # Ry= np.dot(inv(np.dot(A.T, A)), np.dot(A.T,y1))
        xt = x0 * Rx[0] + Rx[1]
        yt = y0 * Ry[0] + Ry[1]
        t_p = np.hstack([xt, yt]).reshape((-1, 2), order="F")
        P2 = np.hstack([x1, y1]).reshape((-1, 2), order="F")

        return t_p, np.sum(np.abs(t_p - P2))

    @staticmethod
    def compare(a1, a2, feature="PERF_COUNT_HW_INSTRUCTIONS", npoints_=100):
        x0, y0 = a1.interpolate(feature=feature, npoints=npoints_)
        x1, y1 = a2.interpolate(feature=feature, npoints=npoints_)
        yt, err = Analyser.scale_translation_matrix(x0, y0, x1, y1)
        return yt, err
