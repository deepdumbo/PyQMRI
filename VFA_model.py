#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 30 11:42:42 2017

@author: omaier
"""

import numpy as np
import time
from scipy.ndimage.filters import gaussian_filter as gf
import matplotlib.pyplot as plt
plt.ion()

from createInitGuess_FLASH import createInitGuess_FLASH
#from compute_mask import compute_mask
DTYPE = np.complex64

class constraint:
  def __init__(self, min_val=-np.inf, max_val=np.inf, real_const=False):
    self.min = min_val
    self.max = max_val
    self.real = real_const


class VFA_Model:
  def __init__(self,fa,fa_corr,TR,images,phase_map,Nislice):
    self.constraints = []    
    self.TR = TR
    self.images = images
    self.fa = fa
    self.fa_corr = fa_corr
    self.Nislice = Nislice
    
    (NScan,Nislice,dimX,dimY) = images.shape
    
    phi_corr = np.zeros_like(images,dtype=DTYPE)
    for i in range(np.size(fa)):
      phi_corr[i,:,:,:] = fa[i]*fa_corr
    
    self.sin_phi = np.sin(phi_corr)
    self.cos_phi = np.cos(phi_corr)    

    
    th = time.clock()

    [M0_guess, T1_guess, mask_guess] = createInitGuess_FLASH(self.images,phi_corr,self.TR)

    T1_guess[np.isnan(T1_guess)] = np.spacing(1)
    T1_guess[np.isinf(T1_guess)] = np.spacing(1)
    T1_guess = np.abs(T1_guess)
    T1_guess[T1_guess<0] = 0 


#    T1_guess[T1_guess>5000] = 5000
#    T1_guess = np.abs(T1_guess)
    M0_guess = np.abs(M0_guess)
    M0_guess[M0_guess<0] = 0 
    M0_guess[np.isnan(M0_guess)] = np.spacing(1)
    M0_guess[np.isinf(M0_guess)] = np.spacing(1)   

    
#
    hist =  np.histogram((M0_guess),int(1e3),range=(0,10*(np.max((np.median(M0_guess),np.mean(M0_guess))))))
    aa = np.array(hist[0], dtype=np.float64)
    #bb = hist[1] #hist0[1][:-1] + np.diff(hist0[1])/2
    bb =(hist[1])
   
    max_val = aa[np.argmax(aa[1:-1])+1]
    FWHM = 2*np.abs(np.argwhere(aa[np.argmax(aa[1:-1])+1:]<max_val/2)[0][0])
    std = FWHM/(2*np.sqrt(2*np.log(2)))
#    
    

    M0_guess[M0_guess > bb[np.argmax(aa[1:-1])+ 1+ int(5*std)]] =  bb[np.argmax(aa[1:-1])+ 1+ int(5*std)] #passst
#    print(M0_guess)
    
    hist =  np.histogram((T1_guess),int(1e3),range=(0,10*(np.max((np.median(T1_guess),np.mean(T1_guess))))))
    aa = np.array(hist[0], dtype=np.float64)
#    bb = hist[1] #hist0[1][:-1] + np.diff(hist0[1])/2
    bb =(hist[1])
   
    max_val = aa[np.argmax(aa[1:-1])+1]
    FWHM = 2*np.abs(np.argwhere(aa[np.argmax(aa[1:-1])+1:]<max_val/2)[0][0])
    std = FWHM/(2*np.sqrt(2*np.log(2)))
#    
    

    T1_guess[T1_guess > bb[np.argmax(aa[1:-1])+ 1+ int(5*std)]] =  bb[np.argmax(aa[1:-1])+ 1+ int(5*std)] #passst

    self.M0_sc = np.max(np.abs(M0_guess))    
    self.T1_sc = np.max(np.abs(T1_guess))

    self.T1_guess = np.copy(T1_guess)
    self.M0_guess = np.copy(M0_guess)

    test_T1 = np.reshape(np.linspace(10,5000,dimX*dimY*Nislice),(Nislice,dimX,dimY))
    G_x = self.execute_forward_3D(np.array([0.01*np.ones((Nislice,dimY,dimX),dtype=DTYPE),np.exp(-self.TR/(test_T1*np.ones((Nislice,dimY,dimX),dtype=DTYPE)))],dtype=DTYPE))
    self.M0_sc = self.M0_sc*np.max(np.abs(images))/np.max(np.abs(G_x))

    
    #print(mask_guess)
    print('T1 scale: ',self.T1_sc,
                              '/ M0_scale: ',self.M0_sc)
    #print(M0_guess[39,11]) M0 guess is gleich

#    self.T1_sc = 5e3
#    self.M0_sc = 50

    M0_guess = M0_guess / self.M0_sc
    T1_guess = T1_guess / self.T1_sc

    T1_guess[np.isnan(T1_guess)] = 0;
    M0_guess[np.isnan(M0_guess)] = 0;
    

    print( 'done in', time.clock() - th)

    E1 = np.exp(-self.TR/(self.T1_guess[None,None,:,:]))
    E1[~np.isfinite(E1)] = 1e-20

#    result = np.array(np.concatenate((self.M0_guess[None,:,:,:],E1),axis=0),dtype=DTYPE)
    result = np.array([1e-5*np.ones((Nislice,dimY,dimX),dtype=DTYPE),np.exp(-self.TR/(1500*np.ones((Nislice,dimY,dimX),dtype=DTYPE)))],dtype=DTYPE)
#    result = np.concatenate((((M0_guess)*np.exp(1j*np.angle(phase_map)))[None,:,:,:],(T1_guess)[None,None,:,:]),axis=0)
#    result = np.array([(0.01+0*M0_guess*np.exp(1j*np.angle(phase_map))),0.3+0*(T1_guess)])
#    result = np.array([1e-3*np.ones((Nislice,dimY,dimX),dtype=DTYPE),1500/self.T1_sc*np.ones((Nislice,dimY,dimX),dtype=DTYPE)])
    self.guess = result                   
    self.constraints.append(constraint(-300,300,False)  )
#    self.constraints.append(constraint(10/self.T1_sc,5500/self.T1_sc,True))
    self.constraints.append(constraint(np.exp(-self.TR/(50)),np.exp(-self.TR/(5500)),True))
  def execute_forward_2D(self,x,islice):
#    E1 = np.exp(-self.TR/(x[1,:,:]*self.T1_sc))
    E1 = x[1,...]

    S = x[0,:,:]*self.M0_sc*(-E1 + 1)*self.sin_phi[:,islice,:,:]/(-E1*self.cos_phi[:,islice,:,:] + 1)
    S[~np.isfinite(S)] = 1e-20
    S = np.array(S,dtype=DTYPE)
    return S
  def execute_gradient_2D(self,x,islice):
#    E1 = np.exp(self.TR/(x[1,:,:]*self.T1_sc))  ####no minus!!!  
    E1 = x[1,:,:]

    E1[~np.isfinite(E1)] = 0
#    grad_M0 = (self.M0_sc*self.sin_phi[:,islice,:,:]*(E1-1))/(E1-self.cos_phi[:,islice,:,:])
#    grad_T1 = (-(x[0,:,:]*self.M0_sc*self.TR*E1*(2*self.sin_phi[:,islice,:,:]-2*self.sin_phi[:,islice,:,:]*self.cos_phi[:,islice,:,:]))/
#               (2*x[1,:,:]**2*self.T1_sc*(E1-self.cos_phi[:,islice,:,:])**2))
    grad_M0 = self.M0_sc*(-E1 + 1)*self.sin_phi[:,islice,:,:]/(-E1*self.cos_phi[:,islice,:,:] + 1)
    grad_T1 = x[0,...]*self.M0_sc*(-E1 + 1)*self.sin_phi[:,islice,:,:]*self.cos_phi[:,islice,:,:]/(-E1*self.cos_phi[:,islice,:,:] + 1)**2\
    - x[0,...]*self.M0_sc*self.sin_phi[:,islice,:,:]/(-E1*self.cos_phi[:,islice,:,:] + 1)
    grad = np.array([grad_M0,grad_T1],dtype=DTYPE)
    grad[~np.isfinite(grad)] = 1e-20
    return grad
  
  def execute_forward_3D(self,x):
#    E1 = np.exp(-self.TR/(x[1,:,:,:]*self.T1_sc))
    E1 = x[1,...]
    S = x[0,:,:]*self.M0_sc*(-E1 + 1)*self.sin_phi/(-E1*self.cos_phi + 1)
    S[~np.isfinite(S)] = 1e-20
    return S
  def execute_gradient_3D(self,x):
    E1 = x[1,:,:]
#    E1[~np.isfinite(E1)] = 0
#    grad_M0 = (self.M0_sc*self.sin_phi[:,islice,:,:]*(E1-1))/(E1-self.cos_phi[:,islice,:,:])
#    grad_T1 = (-(x[0,:,:]*self.M0_sc*self.TR*E1*(2*self.sin_phi[:,islice,:,:]-2*self.sin_phi[:,islice,:,:]*self.cos_phi[:,islice,:,:]))/
#               (2*x[1,:,:]**2*self.T1_sc*(E1-self.cos_phi[:,islice,:,:])**2))
    grad_M0 = self.M0_sc*(-E1 + 1)*self.sin_phi/(-E1*self.cos_phi + 1)
    grad_T1 = x[0,...]*self.M0_sc*(-E1 + 1)*self.sin_phi*self.cos_phi/(-E1*self.cos_phi + 1)**2\
    - x[0,...]*self.M0_sc*self.sin_phi/(-E1*self.cos_phi + 1)
    grad = np.array([grad_M0,grad_T1])
    grad[~np.isfinite(grad)] = 1e-20
    return grad
  

  def execute_forward_2D_ns(self,x,islice):
    E1 = np.exp(-self.TR/(x[1,:,:]))#
#    E1 = x[1,:,:]
    S = x[0,:,:]*self.sin_phi[:,islice,:,:]*(1-E1)/(1-E1*self.cos_phi[:,islice,:,:])
    S[~np.isfinite(S)] = 1e-20
    return S
  def execute_gradient_2D_ns(self,x,islice):
    E1 = np.exp(self.TR/(x[1,:,:]))  ####no minus!!!  
#    E1 = x[1,:,:]
#    E1[~np.isfinite(E1)] = 0
    grad_M0 = (self.sin_phi[:,islice,:,:]*(E1-1))/(E1-self.cos_phi[:,islice,:,:])
    grad_T1 = (-(x[0,:,:]*self.TR*E1*(2*self.sin_phi[:,islice,:,:]-2*self.sin_phi[:,islice,:,:]*self.cos_phi[:,islice,:,:]))/
               (2*x[1,:,:]**2*(E1-self.cos_phi[:,islice,:,:])**2))
#    grad_M0 = (self.M0_sc*self.sin_phi[:,islice,:,:]*(1 - E1))/(-self.cos_phi[:,islice,:,:]*E1 + 1)
#    grad_T1 = (x[0,:,:]*self.M0_sc*self.sin_phi[:,islice,:,:]*(self.cos_phi[:,islice,:,:] - 1))/(E1*self.cos_phi[:,islice,:,:] - 1)**2
    grad = np.array([grad_M0,grad_T1])
    grad[~np.isfinite(grad)] = 1e-20
    return grad   
  def plot_unknowns(self,x,dim_2D=False):
      
      if dim_2D:
          plt.figure(1)
          plt.imshow(np.transpose(np.abs(x[0,...]*self.M0_sc)))
          plt.pause(0.05)
          plt.figure(2)
          plt.imshow(np.transpose(np.abs(-self.TR/np.log(x[1,...]))))
#          plt.imshow(np.transpose(np.abs(x[1,...]*self.T1_sc)))
          plt.pause(0.05)          
      else:         
          plt.figure(1)
          plt.imshow(np.transpose(np.abs(x[0,int(self.Nislice/2),...]*self.M0_sc)))
          plt.pause(0.05)
          plt.figure(2)
          plt.imshow(np.transpose(np.abs(-self.TR/np.log(x[1,int(self.Nislice/2),...]))))
        #      plt.imshow(np.transpose(np.abs(x[1,0,:,:]*self.model.T1_sc)),vmin=0,vmax=3000)
          plt.pause(0.05)
           
           
             
