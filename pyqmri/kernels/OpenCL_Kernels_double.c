
__kernel void update_v(__global double8 *v,__global double8 *v_, __global double8 *Kyk2, const double tau) {
  size_t i = get_global_id(0);
  v[i] = v_[i]-tau*Kyk2[i];
}

__kernel void update_r(__global double2 *r, __global double2 *r_, __global double2 *A, __global double2 *A_, __global double2 *res,
                          const double sigma, const double theta, const double lambdainv) {
  size_t i = get_global_id(0);

  r[i] = (r_[i]+sigma*((1+theta)*A[i]-theta*A_[i] - res[i]))*lambdainv;
}
__kernel void update_z2(__global double16 *z_new, __global double16 *z, __global double16 *gx,__global double16 *gx_,
                          const double sigma, const double theta, const double alphainv,
                          const int NUk) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;

  double fac = 0.0f;

  for (int uk=0; uk<NUk; uk++)
  {
     z_new[i] = z[i] + sigma*((1+theta)*gx[i]-theta*gx_[i]);

     // reproject
     fac = hypot(fac,hypot(
     hypot(hypot(hypot(z_new[i].s0,z_new[i].s1), hypot(z_new[i].s2,z_new[i].s3)),hypot(z_new[i].s4,z_new[i].s5)),
     hypot(hypot(2.0f*hypot(z_new[i].s6,z_new[i].s7),2.0f*hypot(z_new[i].s8,z_new[i].s9)),2.0f*hypot(z_new[i].sa,z_new[i].sb))));
     i += NSl*Nx*Ny;
   }
  fac *= alphainv;
  i = k*Nx*Ny+Nx*y + x;
  for (int uk=0; uk<NUk; uk++)
  {
    if (fac > 1.0f) z_new[i] /=fac;
    i += NSl*Nx*Ny;
  }
}
__kernel void update_z1(__global double8 *z_new, __global double8 *z, __global double8 *gx,__global double8 *gx_,
                          __global double8 *vx,__global double8 *vx_, const double sigma, const double theta, const double alphainv,
                          const int NUk_tgv, const int NUk_H1, const double h1inv) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;

  double fac = 0.0f;

  for (int uk=0; uk<NUk_tgv; uk++)
  {
     z_new[i] = z[i] + sigma*((1+theta)*gx[i]-theta*gx_[i]-(1+theta)*vx[i]+theta*vx_[i]);

     // reproject
     fac = hypot(fac,hypot(hypot(z_new[i].s0,z_new[i].s1), hypot(hypot(z_new[i].s2,z_new[i].s3),hypot(z_new[i].s4,z_new[i].s5))));
     i += NSl*Nx*Ny;
  }
  fac *= alphainv;
  i = k*Nx*Ny+Nx*y + x;
  for (int uk=0; uk<NUk_tgv; uk++)
  {
    if (fac > 1.0f) z_new[i] /=fac;
    i += NSl*Nx*Ny;
  }
  i = NSl*Nx*Ny*NUk_tgv+k*Nx*Ny+Nx*y + x;
  for (int uk=NUk_tgv; uk<(NUk_tgv+NUk_H1); uk++)
  {
    z_new[i] = (z[i] + sigma*((1+theta)*gx[i]-theta*gx_[i]))*h1inv;
    i += NSl*Nx*Ny;
  }
}
  __kernel void update_z1_tv(__global double8 *z_new, __global double8 *z, __global double8 *gx,__global double8 *gx_,
                          const double sigma, const double theta, const double alphainv,
                          const int NUk_tgv, const int NUk_H1, const double h1inv) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;

  double fac = 0.0f;

  for (int uk=0; uk<NUk_tgv; uk++)
  {
     z_new[i] = z[i] + sigma*((1+theta)*gx[i]-theta*gx_[i]);

     // reproject
     fac = hypot(fac,hypot(hypot(z_new[i].s0,z_new[i].s1), hypot(hypot(z_new[i].s2,z_new[i].s3),hypot(z_new[i].s4,z_new[i].s5))));
     i += NSl*Nx*Ny;
  }
  fac *= alphainv;
  i = k*Nx*Ny+Nx*y + x;
  for (int uk=0; uk<NUk_tgv; uk++)
  {
    if (fac > 1.0f) z_new[i] /=fac;
    i += NSl*Nx*Ny;
  }
  i = NSl*Nx*Ny*NUk_tgv+k*Nx*Ny+Nx*y + x;
  for (int uk=NUk_tgv; uk<(NUk_tgv+NUk_H1); uk++)
  {
    z_new[i] = (z[i] + sigma*((1+theta)*gx[i]-theta*gx_[i]))*h1inv;
    i += NSl*Nx*Ny;
  }
}
__kernel void update_primal(__global double2 *u_new, __global double2 *u, __global double2 *Kyk,__global double2 *u_k,
                            const double tau, const double tauinv, double div, __global double* min, __global double* max,
                            __global int* real, const int NUk) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;
  double norm = 0;
  int idx, idx2, idx3, idx4, idx5;
  double2 tmp;



  for (int uk=0; uk<NUk; uk++)
  {
     u_new[i] = (u[i]-tau*Kyk[i]+tauinv*u_k[i])*div;

     if(real[uk]>=1)
     {
         u_new[i].s1 = 0.0f;
         if (u_new[i].s0<min[uk])
         {
             u_new[i].s0 = min[uk];
         }
         if(u_new[i].s0>max[uk])
         {
             u_new[i].s0 = max[uk];
         }
     }
     else
     {
         norm =  sqrt(pow((double)(u_new[i].s0),(double)(2.0))+pow((double)(u_new[i].s1),(double)(2.0)));
         if (norm<min[uk])
         {
             u_new[i].s0 *= 1/norm*min[uk];
             u_new[i].s1 *= 1/norm*min[uk];
         }
         if(norm>max[uk])
         {
            u_new[i].s0 *= 1/norm*max[uk];
            u_new[i].s1 *= 1/norm*max[uk];
         }
     }

     i += NSl*Nx*Ny;
  }
}

__kernel void gradient(__global double8 *grad, __global double2 *u, const int NUk, __global double* ratio, const double dz) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;


  for (int uk=0; uk<NUk; uk++)
  {
     // gradient
     grad[i] = (double8)(-u[i],-u[i],-u[i]/dz,0.0f,0.0f);
     if (x < Nx-1)
     { grad[i].s01 += u[i+1].s01;}
     else
     { grad[i].s01 = 0.0f;}

     if (y < Ny-1)
     { grad[i].s23 += u[i+Nx].s01;}
     else
     { grad[i].s23 = 0.0f;}
     if (k < NSl-1)
     { grad[i].s45 += u[i+Nx*Ny].s01/dz;}
     else
     { grad[i].s45 = 0.0f;}
     // scale gradients
     {grad[i]*=ratio[uk];}
     i += NSl*Nx*Ny;
  }
}

__kernel void sym_grad(__global double16 *sym, __global double8 *w, const int NUk, const double dz) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;


  for (int uk=0; uk<NUk; uk++)
  {
     // symmetrized gradient
     double16 val_real = (double16)(w[i].s024, w[i].s024, w[i].s024,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f);
     double16 val_imag = (double16)(w[i].s135, w[i].s135, w[i].s135,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f);
     if (x > 0)
     { val_real.s012 -= w[i-1].s024;  val_imag.s012 -= w[i-1].s135;}
     else
     { val_real.s012 = (double3) 0.0f; val_imag.s012 = (double3) 0.0f; }

     if (y > 0)
     {val_real.s345 -= w[i-Nx].s024;  val_imag.s345 -= w[i-Nx].s135;}
     else
     {val_real.s345 = (double3)  0.0f; val_imag.s345 = (double3) 0.0f;  }

     if (k > 0)
     {val_real.s678 -= w[i-Nx*Ny].s024;  val_imag.s678 -= w[i-Nx*Ny].s135;}
     else
     {val_real.s678 = (double3) 0.0f; val_imag.s678 = (double3) 0.0f;  }

     sym[i] = (double16)(val_real.s0, val_imag.s0, val_real.s4,val_imag.s4,val_real.s8/dz,val_imag.s8/dz,
                        0.5f*(val_real.s1 + val_real.s3), 0.5f*(val_imag.s1 + val_imag.s3),
                        0.5f*(val_real.s2 + val_real.s6/dz), 0.5f*(val_imag.s2 + val_imag.s6/dz),
                        0.5f*(val_real.s5 + val_real.s7/dz), 0.5f*(val_imag.s5 + val_imag.s7/dz),
                        0.0f,0.0f,0.0f,0.0f);
     i += NSl*Nx*Ny;
   }
}
__kernel void divergence(__global double2 *div, __global double8 *p, const int NUk,
                         __global double* ratio, const double dz) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;

  for (int ukn=0; ukn<NUk; ukn++)
  {
     // divergence
     double8 val = p[i];
     if (x == Nx-1)
     {
         //real
         val.s0 = 0.0f;
         //imag
         val.s1 = 0.0f;
     }
     if (x > 0)
     {
         //real
         val.s0 -= p[i-1].s0;
         //imag
         val.s1 -= p[i-1].s1;
     }
     if (y == Ny-1)
     {
         //real
         val.s2 = 0.0f;
         //imag
         val.s3 = 0.0f;
     }
     if (y > 0)
     {
         //real
         val.s2 -= p[i-Nx].s2;
         //imag
         val.s3 -= p[i-Nx].s3;
     }
     if (k == NSl-1)
     {
         //real
         val.s4 = 0.0f;
         //imag
         val.s5 = 0.0f;
     }
     if (k > 0)
     {
         //real
         val.s4 -= p[i-Nx*Ny].s4;
         //imag
         val.s5 -= p[i-Nx*Ny].s5;
     }
     div[i] = val.s01+val.s23+val.s45/dz;
     // scale gradients
     {div[i]*=ratio[ukn];}
     i += NSl*Nx*Ny;
  }

}
__kernel void sym_divergence(__global double8 *w, __global double16 *q,
                             const int NUk, const double dz) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;

  for (int uk=0; uk<NUk; uk++)
  {
     // divergence
     double16 val0 = -q[i];
     double16 val_real = (double16)(val0.s0, val0.s6, val0.s8,
                                  val0.s6, val0.s2, val0.sa,
                                  val0.s8, val0.sa, val0.s4,
                                  0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f);
     double16 val_imag = (double16)(val0.s1, val0.s7, val0.s9,
                                  val0.s7, val0.s3, val0.sb,
                                  val0.s9, val0.sb, val0.s5,
                                  0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f);
     if (x == 0)
     {
         //real
         val_real.s012 = 0.0f;
         //imag
         val_imag.s012 = 0.0f;
     }
     if (x < Nx-1)
     {
         //real
         val_real.s012 += (double3)(q[i+1].s0, q[i+1].s68);
         //imag
         val_imag.s012 += (double3)(q[i+1].s1, q[i+1].s79);
     }
     if (y == 0)
     {
         //real
         val_real.s345 = 0.0f;
         //imag
         val_imag.s345 = 0.0f;
     }
     if (y < Ny-1)
     {
         //real
         val_real.s345 += (double3)(q[i+Nx].s6, q[i+Nx].s2, q[i+Nx].sa);
         //imag
         val_imag.s345 += (double3)(q[i+Nx].s7, q[i+Nx].s3, q[i+Nx].sb);
     }
     if (k == 0)
     {
         //real
         val_real.s678 = 0.0f;
         //imag
         val_imag.s678 = 0.0f;
     }
     if (k < NSl-1)
     {
         //real
         val_real.s678 += (double3)(q[i+Nx*Ny].s8a, q[i+Nx*Ny].s4);
         //imag
         val_imag.s678 += (double3)(q[i+Nx*Ny].s9b, q[i+Nx*Ny].s5);
     }
     // linear step
     //real
     w[i].s024 = val_real.s012 + val_real.s345 + val_real.s678/dz;
     //imag
     w[i].s135 = val_imag.s012 + val_imag.s345 + val_imag.s678/dz;

     i += NSl*Nx*Ny;
  }
}
__kernel void update_Kyk2(__global double8 *w, __global double16 *q, __global double8 *z,
                          const int NUk, const double dz) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;

  for (int uk=0; uk<NUk; uk++)
  {
     // divergence
     double16 val0 = -q[i];
     double16 val_real = (double16)(val0.s0, val0.s6, val0.s8,
                                  val0.s6, val0.s2, val0.sa,
                                  val0.s8, val0.sa, val0.s4,
                                  0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f);
     double16 val_imag = (double16)(val0.s1, val0.s7, val0.s9,
                                  val0.s7, val0.s3, val0.sb,
                                  val0.s9, val0.sb, val0.s5,
                                  0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,0.0f);
     if (x == 0)
     {
         //real
         val_real.s012 = 0.0f;
         //imag
         val_imag.s012 = 0.0f;
     }
     if (x < Nx-1)
     {
         //real
         val_real.s012 += (double3)(q[i+1].s0, q[i+1].s68);
         //imag
         val_imag.s012 += (double3)(q[i+1].s1, q[i+1].s79);
     }
     if (y == 0)
     {
         //real
         val_real.s345 = 0.0f;
         //imag
         val_imag.s345 = 0.0f;
     }
     if (y < Ny-1)
     {
         //real
         val_real.s345 += (double3)(q[i+Nx].s6, q[i+Nx].s2, q[i+Nx].sa);
         //imag
         val_imag.s345 += (double3)(q[i+Nx].s7, q[i+Nx].s3, q[i+Nx].sb);
     }
     if (k == 0)
     {
         //real
         val_real.s678 = 0.0f;
         //imag
         val_imag.s678 = 0.0f;
     }
     if (k < NSl-1)
     {
         //real
         val_real.s678 += (double3)(q[i+Nx*Ny].s8a, q[i+Nx*Ny].s4);
         //imag
         val_imag.s678 += (double3)(q[i+Nx*Ny].s9b, q[i+Nx*Ny].s5);
     }
     // linear step
     //real
     w[i].s024 = -val_real.s012 - val_real.s345 - val_real.s678/dz -z[i].s024;
     //imag
     w[i].s135 = -val_imag.s012 - val_imag.s345 - val_imag.s678/dz -z[i].s135;
     i += NSl*Nx*Ny;
  }
}

__kernel void operator_fwd(__global double2 *out, __global double2 *in,
                           __global double2 *coils, __global double2 *grad, const int NCo,
                           const int NScan, const int Nuk)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);

  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);

  double2 tmp_in = 0.0f;
  double2 tmp_grad = 0.0f;
  double2 tmp_coil = 0.0f;
  double2 tmp_mul = 0.0f;


    for (int scan=0; scan<NScan; scan++)
    {
      for (int coil=0; coil < NCo; coil++)
      {
        tmp_coil = coils[coil*NSl*X*Y + k*X*Y + y*X + x];
        double2 sum = 0.0f;
        for (int uk=0; uk<Nuk; uk++)
        {
          tmp_grad = grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x];
          tmp_in = in[uk*NSl*X*Y+k*X*Y+ y*X + x];

          tmp_mul = (double2)(tmp_in.x*tmp_grad.x-tmp_in.y*tmp_grad.y,tmp_in.x*tmp_grad.y+tmp_in.y*tmp_grad.x);
          sum += (double2)(tmp_mul.x*tmp_coil.x-tmp_mul.y*tmp_coil.y,
                                                    tmp_mul.x*tmp_coil.y+tmp_mul.y*tmp_coil.x);

        }
        out[scan*NCo*NSl*X*Y+coil*NSl*X*Y+k*X*Y + y*X + x] = sum;
      }
    }


}
__kernel void operator_ad(__global double2 *out, __global double2 *in,
                       __global double2 *coils, __global double2 *grad, const int NCo,
                       const int NScan, const int Nuk)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);

  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);


  double2 tmp_in = 0.0f;
  double2 tmp_mul = 0.0f;
  double2 conj_grad = 0.0f;
  double2 conj_coils = 0.0f;


  for (int uk=0; uk<Nuk; uk++)
  {
  double2 sum = (double2) 0.0f;
  for (int scan=0; scan<NScan; scan++)
  {
    conj_grad = (double2) (grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].x,
                          -grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].y);
  for (int coil=0; coil < NCo; coil++)
  {
    conj_coils = (double2) (coils[coil*NSl*X*Y + k*X*Y + y*X + x].x,
                                  -coils[coil*NSl*X*Y + k*X*Y + y*X + x].y);

    tmp_in = in[scan*NCo*NSl*X*Y+coil*NSl*X*Y + k*X*Y+ y*X + x];
    tmp_mul = (double2)(tmp_in.x*conj_grad.x-tmp_in.y*conj_grad.y,tmp_in.x*conj_grad.y+tmp_in.y*conj_grad.x);


    sum += (double2)(tmp_mul.x*conj_coils.x-tmp_mul.y*conj_coils.y,
                                     tmp_mul.x*conj_coils.y+tmp_mul.y*conj_coils.x);
  }
  }
  out[uk*NSl*X*Y+k*X*Y+y*X+x] = sum;
  }

}



__kernel void update_Kyk1(__global double2 *out, __global double2 *in,
                       __global double2 *coils, __global double2 *grad, __global double8 *p, const int NCo,
                       const int NScan, __global double* ratio, const int Nuk, const double dz)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);

  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);

  size_t i = k*X*Y+X*y + x;

  double2 tmp_in = 0.0f;
  double2 tmp_mul = 0.0f;
  double2 conj_grad = 0.0f;
  double2 conj_coils = 0.0f;


  for (int uk=0; uk<Nuk; uk++)
  {
  double2 sum = (double2) 0.0f;
  for (int scan=0; scan<NScan; scan++)
  {
    conj_grad = (double2) (grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].x,
                          -grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].y);
  for (int coil=0; coil < NCo; coil++)
  {
    conj_coils = (double2) (coils[coil*NSl*X*Y + k*X*Y + y*X + x].x,
                                  -coils[coil*NSl*X*Y + k*X*Y + y*X + x].y);

    tmp_in = in[scan*NCo*NSl*X*Y+coil*NSl*X*Y + k*X*Y+ y*X + x];
    tmp_mul = (double2)(tmp_in.x*conj_grad.x-tmp_in.y*conj_grad.y,tmp_in.x*conj_grad.y+tmp_in.y*conj_grad.x);


    sum += (double2)(tmp_mul.x*conj_coils.x-tmp_mul.y*conj_coils.y,
                                     tmp_mul.x*conj_coils.y+tmp_mul.y*conj_coils.x);
  }
  }

   // divergence
   double8 val = p[i];
   if (x == X-1)
   {
       //real
       val.s0 = 0.0f;
       //imag
       val.s1 = 0.0f;
   }
   if (x > 0)
   {
       //real
       val.s0 -= p[i-1].s0;
       //imag
       val.s1 -= p[i-1].s1;
   }
   if (y == Y-1)
   {
       //real
       val.s2 = 0.0f;
       //imag
       val.s3 = 0.0f;
   }
   if (y > 0)
   {
       //real
       val.s2 -= p[i-X].s2;
       //imag
       val.s3 -= p[i-X].s3;
   }
   if (k == NSl-1)
   {
       //real
       val.s4 = 0.0f;
       //imag
       val.s5 = 0.0f;
   }
   if (k > 0)
   {
       //real
       val.s4 -= p[i-X*Y].s4;
       //imag
       val.s5 -= p[i-X*Y].s5;
   }

   // scale gradients
   {val*=ratio[uk];}

  out[uk*NSl*X*Y+k*X*Y+y*X+x] = sum - (val.s01+val.s23+val.s45/dz);
  i += NSl*X*Y;
  }
}


__kernel void operator_fwd_imagespace(__global double2 *out, __global double2 *in, __global double2 *grad,
                                      const int NScan, const int Nuk)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);

  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);

  double2 tmp_in = 0.0f;
  double2 tmp_grad = 0.0f;

    for (int scan=0; scan<NScan; scan++)
    {
        double2 sum = 0.0f;
        for (int uk=0; uk<Nuk; uk++)
        {
          tmp_grad = grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x];
          tmp_in = in[uk*NSl*X*Y+k*X*Y+ y*X + x];

          sum += (double2)(tmp_in.x*tmp_grad.x-tmp_in.y*tmp_grad.y,tmp_in.x*tmp_grad.y+tmp_in.y*tmp_grad.x);

        }
        out[scan*NSl*X*Y+k*X*Y + y*X + x] = sum;
    }


}
__kernel void operator_ad_imagespace(__global double2 *out, __global double2 *in,
                      __global double2 *grad,
                       const int NScan, const int Nuk)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);

  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);


  double2 tmp_in = 0.0f;
  double2 conj_grad = 0.0f;



  for (int uk=0; uk<Nuk; uk++)
  {
  double2 sum = (double2) 0.0f;
  for (int scan=0; scan<NScan; scan++)
  {
    conj_grad = (double2) (grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].x,
                          -grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].y);
    tmp_in = in[scan*NSl*X*Y+ k*X*Y+ y*X + x];
    sum += (double2)(tmp_in.x*conj_grad.x-tmp_in.y*conj_grad.y,tmp_in.x*conj_grad.y+tmp_in.y*conj_grad.x);

  }
  out[uk*NSl*X*Y+k*X*Y+y*X+x] = sum;
  }

}



__kernel void update_Kyk1_imagespace(__global double2 *out, __global double2 *in,
                       __global double2 *grad, __global double8 *p,
                       const int NScan, __global double* ratio, const int Nuk, const double dz)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);

  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);

  size_t i = k*X*Y+X*y + x;

  double2 tmp_in = 0.0f;
  double2 conj_grad = 0.0f;


  for (int uk=0; uk<Nuk; uk++)
  {
  double2 sum = (double2) 0.0f;
  for (int scan=0; scan<NScan; scan++)
  {
    conj_grad = (double2) (grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].x,
                          -grad[uk*NScan*NSl*X*Y+scan*NSl*X*Y + k*X*Y + y*X + x].y);
    tmp_in = in[scan*NSl*X*Y+ k*X*Y+ y*X + x];
    sum += (double2)(tmp_in.x*conj_grad.x-tmp_in.y*conj_grad.y,tmp_in.x*conj_grad.y+tmp_in.y*conj_grad.x);
  }

   // divergence
   double8 val = p[i];
   if (x == X-1)
   {
       //real
       val.s0 = 0.0f;
       //imag
       val.s1 = 0.0f;
   }
   if (x > 0)
   {
       //real
       val.s0 -= p[i-1].s0;
       //imag
       val.s1 -= p[i-1].s1;
   }
   if (y == Y-1)
   {
       //real
       val.s2 = 0.0f;
       //imag
       val.s3 = 0.0f;
   }
   if (y > 0)
   {
       //real
       val.s2 -= p[i-X].s2;
       //imag
       val.s3 -= p[i-X].s3;
   }
   if (k == NSl-1)
   {
       //real
       val.s4 = 0.0f;
       //imag
       val.s5 = 0.0f;
   }
   if (k > 0)
   {
       //real
       val.s4 -= p[i-X*Y].s4;
       //imag
       val.s5 -= p[i-X*Y].s5;
   }
   // scale gradients
   {val*=ratio[uk];}

  out[uk*NSl*X*Y+k*X*Y+y*X+x] = sum - (val.s01+val.s23+val.s45/dz);
  i += NSl*X*Y;
  }
}

__kernel void update_primal_explicit(__global double2 *u_new, __global double2 *u, __global double2 *Kyk, __global double2 *u_k,
__global double2* ATd, const double tau, const double delta_inv, const double lambd, __global double* mmin, __global double* mmax, __global int* real, const int NUk) {
  size_t Nx = get_global_size(2), Ny = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2), y = get_global_id(1);
  size_t k = get_global_id(0);
  size_t i = k*Nx*Ny+Nx*y + x;


  for (int uk=0; uk<NUk; uk++)
  {
     u_new[i] = u[i]-tau*(lambd*u_new[i]-lambd*ATd[i]+delta_inv*u[i]-delta_inv*u_k[i]-Kyk[i]);

     if(real[uk]>0)
     {
         u_new[i].s1 = 0;
         if (u_new[i].s0<mmin[uk])
         {
             u_new[i].s0 = mmin[uk];
         }
         if(u_new[i].s0>mmax[uk])
         {
             u_new[i].s0 = mmax[uk];
         }
     }
     else
     {
         if (u_new[i].s0<mmin[uk])
         {
             u_new[i].s0 = mmin[uk];
         }
         if(u_new[i].s0>mmax[uk])
         {
             u_new[i].s0 = mmax[uk];
         }
         if (u_new[i].s1<mmin[uk])
         {
             u_new[i].s1 = mmin[uk];
         }
         if(u_new[i].s1>mmax[uk])
         {
             u_new[i].s1 = mmax[uk];
         }
     }
     i += NSl*Nx*Ny;
  }
}

__kernel void operator_fwd_cg(__global double2 *out, __global double2 *in,
                       __global double2 *coils, const int NCo,
                       const int NScan)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);

  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);

  double2 tmp_in = 0.0f;
  double2 tmp_grad = 0.0f;
  double2 tmp_coil = 0.0f;
  double2 tmp_mul = 0.0f;


    for (int scan=0; scan<NScan; scan++)
    {
      for (int coil=0; coil < NCo; coil++)
      {
        out[scan*NCo*NSl*X*Y+coil*NSl*X*Y+k*X*Y + y*X + x] = (double2)(in[scan*NSl*X*Y+k*X*Y+ y*X + x].x*coils[coil*NSl*X*Y + k*X*Y + y*X + x].x-
                                                                      in[scan*NSl*X*Y+k*X*Y+ y*X + x].y*coils[coil*NSl*X*Y + k*X*Y + y*X + x].y,
                                                                      in[scan*NSl*X*Y+k*X*Y+ y*X + x].x*coils[coil*NSl*X*Y + k*X*Y + y*X + x].y+
                                                                      in[scan*NSl*X*Y+k*X*Y+ y*X + x].y*coils[coil*NSl*X*Y + k*X*Y + y*X + x].x);
      }
    }


}
__kernel void operator_ad_cg(__global double2 *out, __global double2 *in,
                       __global double2 *coils, const int NCo,
                       const int NScan)
{
  size_t X = get_global_size(2);
  size_t Y = get_global_size(1);
  size_t NSl = get_global_size(0);
  size_t x = get_global_id(2);
  size_t y = get_global_id(1);
  size_t k = get_global_id(0);


  double2 tmp_in = 0.0f;
  double2 tmp_mul = 0.0f;
  double2 conj_grad = 0.0f;
  double2 conj_coils = 0.0f;


  for (int scan=0; scan<NScan; scan++)
  {
  double2 sum = (double2) 0.0f;
  for (int coil=0; coil < NCo; coil++)
  {
    conj_coils = (double2) (coils[coil*NSl*X*Y + k*X*Y + y*X + x].x,
                                  -coils[coil*NSl*X*Y + k*X*Y + y*X + x].y);
    tmp_in = in[scan*NCo*NSl*X*Y+coil*NSl*X*Y + k*X*Y+ y*X + x];

    sum += (double2)(tmp_in.x*conj_coils.x-tmp_in.y*conj_coils.y,
                                     tmp_in.x*conj_coils.y+tmp_in.y*conj_coils.x);
  }
  out[scan*NSl*X*Y+k*X*Y+y*X+x] = sum;
  }


}
