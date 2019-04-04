#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 10:28:16 2019

@author: omaier
"""
import numpy as np
import sys
from helper_fun import nlinvns_maier as nlinvns
from helper_fun import  goldcomp as goldcomp
import ipyparallel as ipp
import pyopencl.array as clarray
from helper_fun import utils
import os

path = os.environ["TOOLBOX_PATH"] + "/python/";
sys.path.append(path);
from bart import bart

#% Estimates sensitivities and complex image.
#%(see Martin Uecker: Image reconstruction by regularized nonlinear
#%inversion joint estimation of coil sensitivities and image content)
DTYPE = np.complex64
DTYPE_real = np.float32

def est_coils(data,par,file,args):
################################################################################
### Initiate parallel interface ################################################
################################################################################
  c = ipp.Client()
  nlinvNewtonSteps = 9
  nlinvRealConstr  = False
  try:
    if not file['Coils'][()].shape[1] >= par["NSlice"] and not args.sms:
      if args.trafo:

        traj_coil = np.reshape(par["traj"],(par["NScan"]*par["Nproj"],par["N"]))
        dcf_coil = (np.array(goldcomp.cmp(traj_coil),dtype=DTYPE))

        par["C"] = np.zeros((par["NC"],par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)
        par["phase_map"] = np.zeros((par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)

        par_coils = {}
        par_coils["traj"] = traj_coil
        par_coils["dcf"] = dcf_coil
        par_coils["N"] = par["N"]
        par_coils["NScan"] = 1
        par_coils["NC"] = 1
        par_coils["NSlice"] = 1
        par_coils["ctx"] = par["ctx"]
        par_coils["queue"] = par["queue"]

        FFT = utils.NUFFT(par_coils)

        result = []
        for i in range(0,(par["NSlice"])):
          sys.stdout.write("Computing coil sensitivity map of slice %i \r" \
                         %(i))
          sys.stdout.flush()

          ##### RADIAL PART
          combinedData = np.transpose(data[:,:,i,:,:],(1,0,2,3))
          combinedData = np.require(np.reshape(combinedData,(1,par["NC"],1,par["NScan"]*par["Nproj"],par["N"])),requirements='C')
          tmp_coilData = clarray.zeros(FFT.queue[0],(1,1,1,par["dimY"],par["dimX"]),dtype=DTYPE)
          coilData = np.zeros((par["NC"],par["dimY"],par["dimX"]),dtype=DTYPE)
          for j in range(par["NC"]):
              tmp_combinedData = clarray.to_device(FFT.queue[0],combinedData[None,:,j,...])
              FFT.adj_NUFFT(tmp_coilData,tmp_combinedData)
              coilData[j,...] = np.squeeze(tmp_coilData.get())

          combinedData = np.require(np.fft.fft2(coilData,norm=None)/np.sqrt(par["dimX"]*par["dimY"]),dtype=DTYPE,requirements='C')

          dview = c[int(np.floor(i*len(c)/par["NSlice"]))]
          result.append(dview.apply_async(nlinvns.nlinvns, combinedData,
                                          nlinvNewtonSteps, True, nlinvRealConstr))
#
        for i in range(par["NSlice"]):
          par["C"][:,i,:,:] = result[i].get()[2:,-1,:,:]
          sys.stdout.write("slice %i done \r" \
                         %(i))
          sys.stdout.flush()
          if not nlinvRealConstr:
            par["phase_map"][i,:,:] = np.exp(1j * np.angle( result[i].get()[0,-1,:,:]))
            # standardize coil sensitivity profiles
        sumSqrC = np.sqrt(np.sum((par["C"] * np.conj(par["C"])),0)) #4, 9, 128, 128
        if par["NC"] == 1:
          par["C"] = sumSqrC
        else:
          par["C"] = par["C"] / np.tile(sumSqrC, (par["NC"],1,1,1))
        del file['Coils']
        del FFT
      else:

        par["C"] = np.zeros((par["NC"],par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)
        par["phase_map"] = np.zeros((par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)

        result = []
        tmp =  np.sum(data,0)
        for i in range(0,(par["NSlice"])):
          sys.stdout.write("Computing coil sensitivity map of slice %i \r" \
                         %(i))
          sys.stdout.flush()

          ##### RADIAL PART
          combinedData = tmp[:,i,...]
          dview = c[int(np.floor(i*len(c)/par["NSlice"]))]
          result.append(dview.apply_async(nlinvns.nlinvns, combinedData,
                                          nlinvNewtonSteps, True, nlinvRealConstr))

        for i in range(par["NSlice"]):
          par["C"][:,i,:,:] = result[i].get()[2:,-1,:,:]
          sys.stdout.write("slice %i done \r" \
                         %(i))
          sys.stdout.flush()
          if not nlinvRealConstr:
            par["phase_map"][i,:,:] = np.exp(1j * np.angle( result[i].get()[0,-1,:,:]))

            # standardize coil sensitivity profiles
        sumSqrC = np.sqrt(np.sum((par["C"] * np.conj(par["C"])),0)) #4, 9, 128, 128
        if par["NC"] == 1:
          par["C"] = sumSqrC
        else:
          par["C"] = par["C"] / np.tile(sumSqrC, (par["NC"],1,1,1))
        del file['Coils']
#        par["C"] = np.transpose(par["C"],(0,2,3,1))
      file.create_dataset("Coils",par["C"].shape,dtype=par["C"].dtype,data=par["C"])
      file.flush()

    else:
      print("Using precomputed coil sensitivities")
      slices_coils = file['Coils'][()].shape[1]
      if args.sms:
        par["C"] = file['Coils'][...]+1j*file['Coils_imag'][...]
      else:
        par["C"] = file['Coils'][:,int(slices_coils/2)-int(np.floor((par["NSlice"])/2)):int(slices_coils/2)+int(np.ceil(par["NSlice"]/2)),...]

  except:
    if args.trafo:

      traj_coil = np.reshape(par["traj"],(par["NScan"]*par["Nproj"],par["N"]))
      dcf_coil = np.repeat(par["dcf"],par["NScan"],0)

      par["C"] = np.zeros((par["NC"],par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)
      par["phase_map"] = np.zeros((par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)

      par_coils = {}
      par_coils["traj"] = traj_coil
      par_coils["dcf"] = dcf_coil
      par_coils["N"] = par["N"]
      par_coils["NScan"] = 1
      par_coils["NC"] = 1
      par_coils["NSlice"] = 1
      par_coils["ctx"] = par["ctx"]
      par_coils["queue"] = par["queue"]

      FFT = utils.NUFFT(par_coils)

      result = []
      for i in range(0,(par["NSlice"])):
        sys.stdout.write("Computing coil sensitivity map of slice %i \r" \
                       %(i))
        sys.stdout.flush()

        combinedData = np.transpose(data[:,:,i,:,:],(1,0,2,3))
        combinedData = np.require(np.reshape(combinedData,(1,par["NC"],1,par["NScan"]*par["Nproj"],par["N"])),requirements='C')
        tmp_coilData = clarray.zeros(FFT.queue[0],(1,1,1,par["dimY"],par["dimX"]),dtype=DTYPE)
        coilData = np.zeros((par["NC"],par["dimY"],par["dimX"]),dtype=DTYPE)
        for j in range(par["NC"]):
            tmp_combinedData = clarray.to_device(FFT.queue[0],combinedData[None,:,j,...])
            FFT.adj_NUFFT(tmp_coilData,tmp_combinedData)
            coilData[j,...] = np.squeeze(tmp_coilData.get())
#
        combinedData = np.require(np.fft.fft2(coilData,norm=None)/np.sqrt(par["dimX"]*par["dimY"]),dtype=DTYPE,requirements='C')

        dview = c[int(np.floor(i*len(c)/par["NSlice"]))]
        result.append(dview.apply_async(nlinvns.nlinvns, combinedData,
                                          nlinvNewtonSteps, True, nlinvRealConstr))


      for i in range(par["NSlice"]):
        par["C"][:,i,:,:] = result[i].get()[2:,-1,:,:]
        sys.stdout.write("slice %i done \r" \
                       %(i))
        sys.stdout.flush()
        if not nlinvRealConstr:
          par["phase_map"][i,:,:] = np.exp(1j * np.angle( result[i].get()[0,-1,:,:]))

          # standardize coil sensitivity profiles
      sumSqrC = np.sqrt(np.sum((par["C"] * np.conj(par["C"])),0)) #4, 9, 128, 128
      if par["NC"] == 1:
        par["C"] = sumSqrC
      else:
        par["C"] = par["C"] / np.tile(sumSqrC, (par["NC"],1,1,1))
      del FFT
    else:

      par["C"] = np.zeros((par["NC"],par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)
      par["phase_map"] = np.zeros((par["NSlice"],par["dimY"],par["dimX"]), dtype=DTYPE)

      result = []
      tmp =  np.sum(data,0)
      for i in range(0,(par["NSlice"])):
        sys.stdout.write("Computing coil sensitivity map of slice %i \r" \
                       %(i))
        sys.stdout.flush()

        ##### RADIAL PART
        combinedData =  tmp[:,i,...]
        dview = c[int(np.floor(i*len(c)/par["NSlice"]))]
        result.append(dview.apply_async(nlinvns.nlinvns, combinedData,
                                        nlinvNewtonSteps, True, nlinvRealConstr))

      for i in range(par["NSlice"]):
        par["C"][:,i,:,:] = result[i].get()[2:,-1,:,:]
        sys.stdout.write("slice %i done \r" \
                       %(i))
        sys.stdout.flush()
        if not nlinvRealConstr:
          par["phase_map"][i,:,:] = np.exp(1j * np.angle( result[i].get()[0,-1,:,:]))

          # standardize coil sensitivity profiles
      sumSqrC = np.sqrt(np.sum((par["C"] * np.conj(par["C"])),0)) #4, 9, 128, 128
      if par["NC"] == 1:
        par["C"] = sumSqrC
      else:
        par["C"] = par["C"] / np.tile(sumSqrC, (par["NC"],1,1,1))
    file.create_dataset("Coils",par["C"].shape,dtype=par["C"].dtype,data=par["C"])
    file.flush()