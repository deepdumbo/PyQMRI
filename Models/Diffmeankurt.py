#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 30 11:42:42 2017

@author: omaier
"""

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use("Qt5agg")
plt.ion()
DTYPE = np.complex64

unknowns_TGV = 8
unknowns_H1 = 0


class constraint:
    def __init__(
            self,
            min_val=-np.inf,
            max_val=np.inf,
            real_const=False,
            pos_real=False):
        self.min = min_val
        self.max = max_val
        self.real = real_const
        self.pos_real = pos_real

    def update(self, scale):
        self.min = self.min / scale
        self.max = self.max / scale


class Model:
    def __init__(self, par, images):
        self.constraints = []

        self.images = images
        self.NSlice = par['NSlice']
        self.figure = None

        (NScan, Nislice, dimX, dimY) = images.shape

        self.NScan = par["b_value"].size
        self.b = np.ones((self.NScan, 1, 1, 1))
        self.dir = par["DWI_dir"].T

        for i in range(self.NScan):
            self.b[i, ...] = par["b_value"][i] * np.ones((1, 1, 1))


#    print(par["b_value"])
#    self.b_x = self.b*(self.dir[:,0][:,None,None,None])
#    self.b_y = self.b*(self.dir[:,1][:,None,None,None])
#    self.b_z = self.b*(self.dir[:,2][:,None,None,None])

        self.dir = self.dir[:, None, None, None, :]
#    print(self.dir.shape)

        self.uk_scale = []
        self.uk_scale.append(1 / np.max(np.abs(images)))
        self.uk_scale.append(1)
        self.uk_scale.append(1)
        self.uk_scale.append(1)
        self.uk_scale.append(1)
        self.uk_scale.append(1)
        self.uk_scale.append(1)
        self.uk_scale.append(1)

        ADC = np.reshape(
            np.linspace(
                1e-6,
                1e-2,
                dimX *
                dimY *
                Nislice),
            (Nislice,
             dimX,
             dimY))
        kurt = np.reshape(
            np.linspace(
                0,
                2,
                dimX *
                dimY *
                Nislice),
            (Nislice,
             dimX,
             dimY))
        # 1*np.sqrt((dimX*np.pi/2)/par['Nproj'])
        test_M0 = 10 * np.ones((Nislice, dimY, dimX), dtype=DTYPE)
#    print(test_M0)
        ADC_x = 1 / self.uk_scale[1] * ADC * \
            np.ones((Nislice, dimY, dimX), dtype=DTYPE)
        ADC_xy = 1 / self.uk_scale[1] * ADC * \
            np.ones((Nislice, dimY, dimX), dtype=DTYPE)
        ADC_y = 1 / self.uk_scale[1] * ADC * \
            np.ones((Nislice, dimY, dimX), dtype=DTYPE)
        ADC_xz = 1 / self.uk_scale[1] * ADC * \
            np.ones((Nislice, dimY, dimX), dtype=DTYPE)
        ADC_z = 1 / self.uk_scale[1] * ADC * \
            np.ones((Nislice, dimY, dimX), dtype=DTYPE)
        ADC_yz = 1 / self.uk_scale[1] * ADC * \
            np.ones((Nislice, dimY, dimX), dtype=DTYPE)
        kurt = 1 / self.uk_scale[1] * kurt * \
            np.ones((Nislice, dimY, dimX), dtype=DTYPE)
#    kurt_y = 1/self.uk_scale[1]*kurt*np.ones((Nislice,dimY,dimX),dtype=DTYPE)
#    kurt_z = 1/self.uk_scale[1]*kurt*np.ones((Nislice,dimY,dimX),dtype=DTYPE)

        G_x = self.execute_forward_3D(
            np.array(
                [
                    test_M0 /
                    self.uk_scale[0],
                    ADC_x,
                    ADC_xy,
                    ADC_y,
                    ADC_xz,
                    ADC_z,
                    ADC_yz,
                    kurt],
                dtype=DTYPE))
#    print(np.max(np.abs(G_x))/np.max(np.abs(images)))
        self.uk_scale[0] *= 1 / np.max(np.abs(G_x))
#
#    test_M0*=self.uk_scale[0]
#    self.uk_scale[0] = 2

        DG_x = self.execute_gradient_3D(
            np.array(
                [
                    test_M0 /
                    self.uk_scale[0],
                    ADC_x,
                    ADC_xy,
                    ADC_y,
                    ADC_xz,
                    ADC_z,
                    ADC_yz,
                    kurt],
                dtype=DTYPE))
        self.uk_scale[1] = self.uk_scale[1] * np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[1, ...]))
        self.uk_scale[2] = self.uk_scale[2] * np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[2, ...]))
        self.uk_scale[3] = self.uk_scale[3] * np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[3, ...]))
        self.uk_scale[4] = self.uk_scale[4] * np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[4, ...]))
        self.uk_scale[5] = self.uk_scale[5] * np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[5, ...]))
        self.uk_scale[6] = self.uk_scale[6] * np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[6, ...]))

        self.uk_scale[7] = self.uk_scale[7] * np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[7, ...]))

        DG_x = self.execute_gradient_3D(
            np.array(
                [
                    images[0] / self.uk_scale[0],
                    ADC_x / self.uk_scale[1],
                    ADC_xy / self.uk_scale[2],
                    ADC_y / self.uk_scale[3],
                    ADC_xz / self.uk_scale[4],
                    ADC_z / self.uk_scale[5],
                    ADC_yz / self.uk_scale[6],
                    kurt / self.uk_scale[7]],
                dtype=DTYPE))

        print('Grad Scaling init', np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[1, ...])))
        print('Grad Scaling init', np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[2, ...])))
        print('Grad Scaling init', np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[3, ...])))
        print('Grad Scaling init', np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[4, ...])))
        print('Grad Scaling init', np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[5, ...])))
        print('Grad Scaling init', np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[6, ...])))
        print('Grad Scaling init', np.linalg.norm(
            np.abs(DG_x[0, ...])) / np.linalg.norm(np.abs(DG_x[7, ...])))
        print('ADC scale: ', self.uk_scale[1])
        print('kurt scale: ', self.uk_scale[2])
        print('M0 scale: ', self.uk_scale[0])
        print('ADC_y scale: ', self.uk_scale[3])
        print('ADC_xz scale: ', self.uk_scale[4])
        print('ADC_z scale: ', self.uk_scale[5])
        print('ADC_yz scale: ', self.uk_scale[6])
        print('kurt scale: ', self.uk_scale[7])

        result = np.array([np.ones_like(test_M0) /
                           self.uk_scale[0], np.mean(ADC_x) *
                           np.ones_like(ADC_x) /
                           self.uk_scale[1], np.mean(ADC_xy) *
                           np.ones_like(ADC_xy) /
                           self.uk_scale[2], np.mean(ADC_y) *
                           np.ones_like(ADC_y) /
                           self.uk_scale[3], np.mean(ADC_xz) *
                           np.ones_like(ADC_xz) /
                           self.uk_scale[4], np.mean(ADC_z) *
                           np.ones_like(ADC_z) /
                           self.uk_scale[5], np.mean(ADC_yz) *
                           np.ones_like(ADC_yz) /
                           self.uk_scale[6], 0 *
                           np.ones_like(kurt) /
                           self.uk_scale[7]], dtype=DTYPE)
        self.guess = result

        self.constraints.append(
            constraint(
                0 / self.uk_scale[0],
                100 / self.uk_scale[0],
                False))
        self.constraints.append(
            constraint(
                (0 / self.uk_scale[1]),
                (5e0 / self.uk_scale[1]),
                True))
        self.constraints.append(
            constraint(
                (-1e0 / self.uk_scale[2]),
                (1e0 / self.uk_scale[2]),
                True))
        self.constraints.append(
            constraint(
                (0 / self.uk_scale[3]),
                (5e0 / self.uk_scale[3]),
                True))
        self.constraints.append(
            constraint(
                (-1e0 / self.uk_scale[4]),
                (1e0 / self.uk_scale[4]),
                True))
        self.constraints.append(
            constraint(
                (0 / self.uk_scale[5]),
                (5e0 / self.uk_scale[5]),
                True))
        self.constraints.append(
            constraint(
                (-1e0 / self.uk_scale[6]),
                (1e0 / self.uk_scale[6]),
                True))
        self.constraints.append(
            constraint(
                (-5 / self.uk_scale[7]),
                (5 / self.uk_scale[7]),
                True))

    def rescale(self, x):
        M0 = x[0, ...] * self.uk_scale[0]
        ADC_x = (x[1, ...] * self.uk_scale[1])
        ADC_xy = (x[2, ...] * self.uk_scale[2])
        ADC_y = (x[3, ...] * self.uk_scale[3])
        ADC_xz = (x[4, ...] * self.uk_scale[4])
        ADC_z = (x[5, ...] * self.uk_scale[5])
        ADC_yz = (x[6, ...] * self.uk_scale[6])
        kurt = x[7, ...] * self.uk_scale[7]
        return np.array(
            (M0,
             ADC_x,
             ADC_xy,
             ADC_y,
             ADC_xz,
             ADC_z,
             ADC_yz,
             kurt))

    def execute_forward_3D(self, x):
        ADC_x = x[1, ...] * self.uk_scale[1]
        ADC_xy = x[2, ...] * self.uk_scale[2]
        ADC_y = x[3, ...] * self.uk_scale[3]
        ADC_xz = x[4, ...] * self.uk_scale[4]
        ADC_z = x[5, ...] * self.uk_scale[5]
        ADC_yz = x[6, ...] * self.uk_scale[6]
        kurt = x[7, ...] * self.uk_scale[7]

        ADC = ADC_x * self.dir[...,
                               0]**2 + ADC_y * self.dir[...,
                                                        1]**2 + ADC_z * self.dir[...,
                                                                                 2]**2 + 2 * ADC_xy * self.dir[...,
                                                                                                               0] * self.dir[...,
                                                                                                                             1] + 2 * ADC_xz * self.dir[...,
                                                                                                                                                        0] * self.dir[...,
                                                                                                                                                                      2] + 2 * ADC_yz * self.dir[...,
                                                                                                                                                                                                 1] * self.dir[...,
                                                                                                                                                                                                               2]
        meanADC = 1 / 3 * (ADC_x + ADC_y + ADC_z)

        S = (x[0, ...] * self.uk_scale[0] * np.exp(1 / 6 * meanADC **
                                                   2 * self.b**2 * kurt - ADC * self.b)).astype(DTYPE)
        S[~np.isfinite(S)] = 1e-20
        return S

    def execute_gradient_3D(self, x):
        M0 = x[0, ...]
        ADC_x = x[1, ...]
        ADC_xy = x[2, ...]
        M0_sc = self.uk_scale[0]
        ADC_x_sc = self.uk_scale[1]
        ADC_xy_sc = self.uk_scale[2]
        ADC_y = x[3, ...]
        ADC_xz = x[4, ...]
        ADC_y_sc = self.uk_scale[3]
        ADC_xz_sc = self.uk_scale[4]
        ADC_z = x[5, ...]
        ADC_yz = x[6, ...]
        ADC_z_sc = self.uk_scale[5]
        ADC_yz_sc = self.uk_scale[6]
        kurt = x[7, ...]
        kurt_sc = self.uk_scale[7]

        ADC = ADC_x * ADC_x_sc * self.dir[...,
                                          0]**2 + ADC_y * ADC_y_sc * self.dir[...,
                                                                              1]**2 + ADC_z * ADC_z_sc * self.dir[...,
                                                                                                                  2]**2 + 2 * ADC_xy * ADC_xy_sc * self.dir[...,
                                                                                                                                                            0] * self.dir[...,
                                                                                                                                                                          1] + 2 * ADC_xz * ADC_xz_sc * self.dir[...,
                                                                                                                                                                                                                 0] * self.dir[...,
                                                                                                                                                                                                                               2] + 2 * ADC_yz * ADC_yz_sc * self.dir[...,
                                                                                                                                                                                                                                                                      1] * self.dir[...,
                                                                                                                                                                                                                                                                                    2]

        meanADC = 1 / 3 * (ADC_x * ADC_x_sc + ADC_y *
                           ADC_y_sc + ADC_z * ADC_z_sc)
        kurt = kurt * kurt_sc

        diffexp = np.exp(1 / 6 * meanADC**2 * self.b**2 * kurt - ADC * self.b)

        grad_M0 = self.uk_scale[0] * diffexp

        grad_ADC_x = M0 * M0_sc * (2 / 6 * 1 / 3 * meanADC * ADC_x_sc * self.b **
                                   2 * kurt - ADC_x_sc * self.dir[..., 0]**2 * self.b) * diffexp
        grad_ADC_xy = M0 * M0_sc * \
            (-2 * ADC_xy_sc * self.dir[..., 0] * self.dir[..., 1] * self.b) * diffexp

        grad_ADC_y = M0 * M0_sc * (2 / 6 * 1 / 3 * meanADC * ADC_y_sc * self.b **
                                   2 * kurt - ADC_y_sc * self.dir[..., 1]**2 * self.b) * diffexp
        grad_ADC_xz = M0 * M0_sc * \
            (-2 * ADC_xz_sc * self.dir[..., 0] * self.dir[..., 2] * self.b) * diffexp

        grad_ADC_z = M0 * M0_sc * (2 / 6 * 1 / 3 * meanADC * ADC_z_sc * self.b **
                                   2 * kurt - ADC_z_sc * self.dir[..., 2]**2 * self.b) * diffexp
        grad_ADC_yz = M0 * M0_sc * \
            (-2 * ADC_yz_sc * self.dir[..., 1] * self.dir[..., 2] * self.b) * diffexp

        grad_kurt = M0 * M0_sc * \
            (1 / 6 * meanADC**2 * self.b**2 * kurt_sc) * diffexp
#
#    print('Grad Scaling', np.linalg.norm(np.abs(grad_M0))/np.linalg.norm(np.abs(grad_ADC_x)))
#    print('Grad Scaling', np.linalg.norm(np.abs(grad_M0))/np.linalg.norm(np.abs(grad_ADC_y)))
#    print('Grad Scaling', np.linalg.norm(np.abs(grad_M0))/np.linalg.norm(np.abs(grad_ADC_z)))
#
#    print('Grad Scaling', np.linalg.norm(np.abs(grad_M0))/np.linalg.norm(np.abs(grad_ADC_xy)))
#    print('Grad Scaling', np.linalg.norm(np.abs(grad_M0))/np.linalg.norm(np.abs(grad_ADC_xz)))
#    print('Grad Scaling', np.linalg.norm(np.abs(grad_M0))/np.linalg.norm(np.abs(grad_ADC_yz)))
#
#    print('Grad Scaling', np.linalg.norm(np.abs(grad_M0))/np.linalg.norm(np.abs(grad_kurt)))

        grad = np.array([grad_M0,
                         grad_ADC_x,
                         grad_ADC_xy,
                         grad_ADC_y,
                         grad_ADC_xz,
                         grad_ADC_z,
                         grad_ADC_yz,
                         grad_kurt],
                        dtype=DTYPE)
        grad[~np.isfinite(grad)] = 1e-20
        return grad

    def plot_unknowns(self, x, dim_2D=False):
        M0 = np.abs(x[0, ...]) * self.uk_scale[0]
        ADC_x = (np.real(x[1, ...]) * self.uk_scale[1])
        ADC_xy = (np.real(x[2, ...]) * self.uk_scale[2])
        M0_min = M0.min()
        M0_max = M0.max()
        ADC_x_min = ADC_x.min()
        ADC_x_max = ADC_x.max()
        ADC_xy_min = ADC_xy.min()
        ADC_xy_max = ADC_xy.max()

        ADC_y = (np.real(x[3, ...]) * self.uk_scale[3])
        ADC_xz = (np.real(x[4, ...]) * self.uk_scale[4])
        ADC_y_min = ADC_y.min()
        ADC_y_max = ADC_y.max()
        ADC_xz_min = ADC_xz.min()
        ADC_xz_max = ADC_xz.max()

        ADC_z = (np.real(x[5, ...]) * self.uk_scale[5])
        ADC_yz = (np.real(x[6, ...]) * self.uk_scale[6])
        ADC_z_min = ADC_z.min()
        ADC_z_max = ADC_z.max()
        ADC_yz_min = ADC_yz.min()
        ADC_yz_max = ADC_yz.max()

        kurt = np.real(x[7, ...] * self.uk_scale[7])
        kurt_min = kurt.min()
        kurt_max = kurt.max()

        DT = np.zeros((M0.shape[-3], M0.shape[-1],
                       M0.shape[-1], 3, 3), dtype=np.float32)
        DT[..., 0, 0] = ADC_x.real
        DT[..., 0, 1] = ADC_xy.real
        DT[..., 0, 2] = ADC_xz.real
        DT[..., 1, 0] = ADC_xy.real
        DT[..., 1, 1] = ADC_y.real
        DT[..., 1, 2] = ADC_yz.real
        DT[..., 2, 0] = ADC_xz.real
        DT[..., 2, 1] = ADC_yz.real
        DT[..., 2, 2] = ADC_z.real
        DT_eig = np.linalg.eigh(DT)[0]
        FA = np.sqrt(((DT_eig[...,
                              0] - DT_eig[...,
                                          1])**2 + (DT_eig[...,
                                                           1] - DT_eig[...,
                                                                       2])**2 + (DT_eig[...,
                                                                                        0] - DT_eig[...,
                                                                                                    2])**2) / 2 * (DT_eig[...,
                                                                                                                          0]**2 + DT_eig[...,
                                                                                                                                         1]**2 + DT_eig[...,
                                                                                                                                                        2]**2))
        FA_min = FA.min()
        FA_max = FA.max()

        if dim_2D:
            if not self.figure:
                plt.ion()
                self.figure, self.ax = plt.subplots(1, 2, figsize=(12, 5))
                self.M0_plot = self.ax[0].imshow((M0))
                self.ax[0].set_title('Proton Density in a.u.')
                self.ax[0].axis('off')
                self.figure.colorbar(self.M0_plot, ax=self.ax[0])
                self.ADC_x_plot = self.ax[1].imshow((ADC_x))
                self.ax[1].set_title('ADC_x in  ms')
                self.ax[1].axis('off')
                self.figure.colorbar(self.ADC_x_plot, ax=self.ax[1])
                self.figure.tight_layout()
                plt.draw()
                plt.pause(1e-10)
            else:
                self.M0_plot.set_data((M0))
                self.M0_plot.set_clim([M0_min, M0_max])
                self.ADC_x_plot.set_data((ADC_x))
                self.ADC_x_plot.set_clim([ADC_x_min, ADC_x_max])
                plt.draw()
                plt.pause(1e-10)
        else:
            [z, y, x] = M0.shape
            self.ax = []
            if not self.figure:
                plt.ion()
                self.figure = plt.figure(figsize=(12, 6))
                self.figure.subplots_adjust(hspace=0, wspace=0)
                self.gs = gridspec.GridSpec(8,
                                            10,
                                            width_ratios=[x / (20 * z),
                                                          x / z,
                                                          1,
                                                          x / z,
                                                          1,
                                                          x / (20 * z),
                                                          x / (2 * z),
                                                          x / z,
                                                          1,
                                                          x / (20 * z)],
                                            height_ratios=[x / z,
                                                           1,
                                                           x / z,
                                                           1,
                                                           x / z,
                                                           1,
                                                           x / z,
                                                           1])
                self.figure.tight_layout()
                self.figure.patch.set_facecolor(plt.cm.viridis.colors[0])
                for grid in self.gs:
                    self.ax.append(plt.subplot(grid))
                    self.ax[-1].axis('off')

                self.M0_plot = self.ax[1].imshow(
                    (M0[int(self.NSlice / 2), ...]))
                self.M0_plot_cor = self.ax[11].imshow(
                    (M0[:, int(M0.shape[1] / 2), ...]))
                self.M0_plot_sag = self.ax[2].imshow(
                    np.flip((M0[:, :, int(M0.shape[-1] / 2)]).T, 1))
                self.ax[1].set_title('Proton Density in a.u.', color='white')
                self.ax[1].set_anchor('SE')
                self.ax[2].set_anchor('SW')
                self.ax[11].set_anchor('NE')
                cax = plt.subplot(self.gs[:2, 0])
                cbar = self.figure.colorbar(self.M0_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                cax.yaxis.set_ticks_position('left')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.ADC_x_plot = self.ax[3].imshow(
                    (ADC_x[int(self.NSlice / 2), ...]))
                self.ADC_x_plot_cor = self.ax[13].imshow(
                    (ADC_x[:, int(ADC_x.shape[1] / 2), ...]))
                self.ADC_x_plot_sag = self.ax[4].imshow(
                    np.flip((ADC_x[:, :, int(ADC_x.shape[-1] / 2)]).T, 1))
                self.ax[3].set_title('ADC_x', color='white')
                self.ax[3].set_anchor('SE')
                self.ax[4].set_anchor('SW')
                self.ax[13].set_anchor('NE')
                cax = plt.subplot(self.gs[:2, 5])
                cbar = self.figure.colorbar(self.ADC_x_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.ADC_xy_plot = self.ax[7].imshow(
                    (ADC_xy[int(self.NSlice / 2), ...]))
                self.ADC_xy_plot_cor = self.ax[17].imshow(
                    (ADC_xy[:, int(ADC_x.shape[1] / 2), ...]))
                self.ADC_xy_plot_sag = self.ax[8].imshow(
                    np.flip((ADC_xy[:, :, int(ADC_x.shape[-1] / 2)]).T, 1))
                self.ax[7].set_title('ADC_xy', color='white')
                self.ax[7].set_anchor('SE')
                self.ax[8].set_anchor('SW')
                self.ax[17].set_anchor('NE')
                cax = plt.subplot(self.gs[:2, 9])
                cbar = self.figure.colorbar(self.ADC_xy_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.ADC_y_plot = self.ax[23].imshow(
                    (ADC_y[int(self.NSlice / 2), ...]))
                self.ADC_y_plot_cor = self.ax[33].imshow(
                    (ADC_y[:, int(ADC_y.shape[1] / 2), ...]))
                self.ADC_y_plot_sag = self.ax[24].imshow(
                    np.flip((ADC_y[:, :, int(ADC_y.shape[-1] / 2)]).T, 1))
                self.ax[23].set_title('ADC_y', color='white')
                self.ax[23].set_anchor('SE')
                self.ax[24].set_anchor('SW')
                self.ax[33].set_anchor('NE')
                cax = plt.subplot(self.gs[2:4, 5])
                cbar = self.figure.colorbar(self.ADC_y_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.ADC_xz_plot = self.ax[27].imshow(
                    (ADC_xz[int(self.NSlice / 2), ...]))
                self.ADC_xz_plot_cor = self.ax[37].imshow(
                    (ADC_xz[:, int(ADC_y.shape[1] / 2), ...]))
                self.ADC_xz_plot_sag = self.ax[28].imshow(
                    np.flip((ADC_xz[:, :, int(ADC_y.shape[-1] / 2)]).T, 1))
                self.ax[27].set_title('ADC_xz', color='white')
                self.ax[27].set_anchor('SE')
                self.ax[28].set_anchor('SW')
                self.ax[37].set_anchor('NE')
                cax = plt.subplot(self.gs[2:4, 9])
                cbar = self.figure.colorbar(self.ADC_xz_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.ADC_z_plot = self.ax[43].imshow(
                    (ADC_z[int(self.NSlice / 2), ...]))
                self.ADC_z_plot_cor = self.ax[53].imshow(
                    (ADC_z[:, int(ADC_z.shape[1] / 2), ...]))
                self.ADC_z_plot_sag = self.ax[44].imshow(
                    np.flip((ADC_z[:, :, int(ADC_z.shape[-1] / 2)]).T, 1))
                self.ax[43].set_title('ADC_z', color='white')
                self.ax[43].set_anchor('SE')
                self.ax[44].set_anchor('SW')
                self.ax[53].set_anchor('NE')
                cax = plt.subplot(self.gs[4:6, 5])
                cbar = self.figure.colorbar(self.ADC_z_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.ADC_yz_plot = self.ax[47].imshow(
                    (ADC_yz[int(self.NSlice / 2), ...]))
                self.ADC_yz_plot_cor = self.ax[57].imshow(
                    (ADC_yz[:, int(ADC_z.shape[1] / 2), ...]))
                self.ADC_yz_plot_sag = self.ax[48].imshow(
                    np.flip((ADC_yz[:, :, int(ADC_z.shape[-1] / 2)]).T, 1))
                self.ax[47].set_title('ADC_yz', color='white')
                self.ax[47].set_anchor('SE')
                self.ax[48].set_anchor('SW')
                self.ax[57].set_anchor('NE')
                cax = plt.subplot(self.gs[4:6, 9])
                cbar = self.figure.colorbar(self.ADC_yz_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.kurt_plot = self.ax[61].imshow(
                    (kurt[int(self.NSlice / 2), ...]))
                self.kurt_plot_cor = self.ax[71].imshow(
                    (kurt[:, int(kurt.shape[1] / 2), ...]))
                self.kurt_plot_sag = self.ax[62].imshow(
                    np.flip((kurt[:, :, int(kurt.shape[-1] / 2)]).T, 1))
                self.ax[61].set_title('kurtosis_x in a.u.', color='white')
                self.ax[61].set_anchor('SE')
                self.ax[62].set_anchor('SW')
                self.ax[71].set_anchor('NE')
                cax = plt.subplot(self.gs[6:8, 0])
                cbar = self.figure.colorbar(self.kurt_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                cax.yaxis.set_ticks_position('left')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                self.FA_plot = self.ax[41].imshow(
                    (FA[int(self.NSlice / 2), ...]))
                self.FA_plot_cor = self.ax[51].imshow(
                    (FA[:, int(FA.shape[1] / 2), ...]))
                self.FA_plot_sag = self.ax[42].imshow(
                    np.flip((FA[:, :, int(FA.shape[-1] / 2)]).T, 1))
                self.ax[41].set_title('FA', color='white')
                self.ax[41].set_anchor('SE')
                self.ax[42].set_anchor('SW')
                self.ax[51].set_anchor('NE')
                cax = plt.subplot(self.gs[4:6, 0])
                cbar = self.figure.colorbar(self.FA_plot, cax=cax)
                cbar.ax.tick_params(labelsize=12, colors='white')
                for spine in cbar.ax.spines:
                    cbar.ax.spines[spine].set_color('white')

                plt.draw()
                plt.pause(1e-10)

            else:
                self.M0_plot.set_data((M0[int(self.NSlice / 2), ...]))
                self.M0_plot_cor.set_data((M0[:, int(M0.shape[1] / 2), ...]))
                self.M0_plot_sag.set_data(
                    np.flip((M0[:, :, int(M0.shape[-1] / 2)]).T, 1))
                self.M0_plot.set_clim([M0_min, M0_max])
                self.M0_plot_cor.set_clim([M0_min, M0_max])
                self.M0_plot_sag.set_clim([M0_min, M0_max])

                self.ADC_x_plot.set_data((ADC_x[int(self.NSlice / 2), ...]))
                self.ADC_x_plot_cor.set_data(
                    (ADC_x[:, int(ADC_x.shape[1] / 2), ...]))
                self.ADC_x_plot_sag.set_data(
                    np.flip((ADC_x[:, :, int(ADC_x.shape[-1] / 2)]).T, 1))
                self.ADC_x_plot.set_clim([ADC_x_min, ADC_x_max])
                self.ADC_x_plot_sag.set_clim([ADC_x_min, ADC_x_max])
                self.ADC_x_plot_cor.set_clim([ADC_x_min, ADC_x_max])

                self.ADC_xy_plot.set_data((ADC_xy[int(self.NSlice / 2), ...]))
                self.ADC_xy_plot_cor.set_data(
                    (ADC_xy[:, int(ADC_xy.shape[1] / 2), ...]))
                self.ADC_xy_plot_sag.set_data(
                    np.flip((ADC_xy[:, :, int(ADC_xy.shape[-1] / 2)]).T, 1))
                self.ADC_xy_plot.set_clim([ADC_xy_min, ADC_xy_max])
                self.ADC_xy_plot_sag.set_clim([ADC_xy_min, ADC_xy_max])
                self.ADC_xy_plot_cor.set_clim([ADC_xy_min, ADC_xy_max])

                self.ADC_y_plot.set_data((ADC_y[int(self.NSlice / 2), ...]))
                self.ADC_y_plot_cor.set_data(
                    (ADC_y[:, int(ADC_y.shape[1] / 2), ...]))
                self.ADC_y_plot_sag.set_data(
                    np.flip((ADC_y[:, :, int(ADC_y.shape[-1] / 2)]).T, 1))
                self.ADC_y_plot.set_clim([ADC_y_min, ADC_y_max])
                self.ADC_y_plot_sag.set_clim([ADC_y_min, ADC_y_max])
                self.ADC_y_plot_cor.set_clim([ADC_y_min, ADC_y_max])

                self.ADC_xz_plot.set_data((ADC_xz[int(self.NSlice / 2), ...]))
                self.ADC_xz_plot_cor.set_data(
                    (ADC_xz[:, int(ADC_xz.shape[1] / 2), ...]))
                self.ADC_xz_plot_sag.set_data(
                    np.flip((ADC_xz[:, :, int(ADC_xz.shape[-1] / 2)]).T, 1))
                self.ADC_xz_plot.set_clim([ADC_xz_min, ADC_xz_max])
                self.ADC_xz_plot_sag.set_clim([ADC_xz_min, ADC_xz_max])
                self.ADC_xz_plot_cor.set_clim([ADC_xz_min, ADC_xz_max])

                self.ADC_z_plot.set_data((ADC_z[int(self.NSlice / 2), ...]))
                self.ADC_z_plot_cor.set_data(
                    (ADC_z[:, int(ADC_z.shape[1] / 2), ...]))
                self.ADC_z_plot_sag.set_data(
                    np.flip((ADC_z[:, :, int(ADC_z.shape[-1] / 2)]).T, 1))
                self.ADC_z_plot.set_clim([ADC_z_min, ADC_z_max])
                self.ADC_z_plot_sag.set_clim([ADC_z_min, ADC_z_max])
                self.ADC_z_plot_cor.set_clim([ADC_z_min, ADC_z_max])

                self.ADC_yz_plot.set_data((ADC_yz[int(self.NSlice / 2), ...]))
                self.ADC_yz_plot_cor.set_data(
                    (ADC_yz[:, int(ADC_yz.shape[1] / 2), ...]))
                self.ADC_yz_plot_sag.set_data(
                    np.flip((ADC_yz[:, :, int(ADC_yz.shape[-1] / 2)]).T, 1))
                self.ADC_yz_plot.set_clim([ADC_yz_min, ADC_yz_max])
                self.ADC_yz_plot_sag.set_clim([ADC_yz_min, ADC_yz_max])
                self.ADC_yz_plot_cor.set_clim([ADC_yz_min, ADC_yz_max])

                self.kurt_plot.set_data((kurt[int(self.NSlice / 2), ...]))
                self.kurt_plot_cor.set_data(
                    (kurt[:, int(kurt.shape[1] / 2), ...]))
                self.kurt_plot_sag.set_data(
                    np.flip((kurt[:, :, int(kurt.shape[-1] / 2)]).T, 1))
                self.kurt_plot.set_clim([kurt_min, kurt_max])
                self.kurt_plot_cor.set_clim([kurt_min, kurt_max])
                self.kurt_plot_sag.set_clim([kurt_min, kurt_max])

                self.FA_plot.set_data((FA[int(self.NSlice / 2), ...]))
                self.FA_plot_cor.set_data((FA[:, int(FA.shape[1] / 2), ...]))
                self.FA_plot_sag.set_data(
                    np.flip((FA[:, :, int(FA.shape[-1] / 2)]).T, 1))
                self.FA_plot.set_clim([FA_min, FA_max])
                self.FA_plot_sag.set_clim([FA_min, FA_max])
                self.FA_plot_cor.set_clim([FA_min, FA_max])

                plt.draw()
                plt.pause(1e-10)
