#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
__attribute__((noinline)) void spmv(size_t rows,const uint64_t *rp,const uint32_t *ci,const double *a,const double *x,double *y){
 for(size_t r=0;r<rows;r++){
  double s=0;
  for(uint64_t j=rp[r];j<rp[r+1];j++) s+=a[j]*x[ci[j]];
  y[r]=s;
 }
}
