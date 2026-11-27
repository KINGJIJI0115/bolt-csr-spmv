#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
#include <unistd.h>
void spmv(size_t,const uint64_t*,const uint32_t*,const double*,const double*,double*);
int main(void){
 const size_t n=5000000;double *x=malloc(n*8);if(!x)return 2;
 for(size_t i=0;i<n;i++)x[i]=((int)(i%2003)-1001)/1009.0;
 size_t page=sysconf(_SC_PAGESIZE),capacity=4096*8,span=(capacity+page-1)/page*page;
 char *im=mmap(0,span+2*page,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0),*am=mmap(0,span+2*page,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
 if(im==MAP_FAILED||am==MAP_FAILED)return 3;
 if(mprotect(im+page,span,PROT_READ|PROT_WRITE)||mprotect(am+page,span,PROT_READ|PROT_WRITE))return 4;
 uint64_t rp[6]={0};double y[5],ref[5];uint64_t hash=0;
 for(size_t len=0;len<=4096;len++){
  uint32_t *ci=(void*)(im+page+span-len*4);double *a=(void*)(am+page+span-len*8);
  for(size_t j=0;j<len;j++){ci[j]=(uint32_t)((j*7919+17)%n);a[j]=((int)(j%37)-18)/31.0;}
  rp[0]=rp[1]=0;rp[2]=len>3?3:len;rp[3]=rp[2];rp[4]=rp[5]=len;
  for(size_t r=0;r<5;r++){double s=0;for(uint64_t j=rp[r];j<rp[r+1];j++)s=fma(a[j],x[ci[j]],s);ref[r]=s;}
  spmv(5,rp,ci,a,x,y);if(memcmp(y,ref,sizeof y)){fprintf(stderr,"mismatch length %zu\n",len);return 5;}
  uint64_t bits;memcpy(&bits,y+3,8);hash=hash*31+bits;
 }
 uint64_t zero[4]={0};spmv(3,zero,NULL,NULL,NULL,y);for(int i=0;i<3;i++)if(y[i]!=0)return 6;
 spmv(0,NULL,NULL,NULL,NULL,NULL);
 /* Nonfinite and signed-zero operands: retain the original FMA ordering. */
 double vals[]={INFINITY,-INFINITY,NAN,-0.0,0.0,0x1p-1022,0x1p-1074,0x1p100};
 uint32_t ids[16];double a[16];uint64_t rr[2]={0,16};
 for(int c=0;c<8;c++){for(int j=0;j<16;j++){ids[j]=(j+c)%8;a[j]=vals[(j*3+c)%8];}double s=0;for(int j=0;j<16;j++)s=fma(a[j],vals[ids[j]],s);spmv(1,rr,ids,a,vals,y);if(isnan(s)?!isnan(y[0]):memcmp(&s,y,8))return 7;}
 printf("{\"guard_lengths\":4097,\"null_empty_rows\":true,\"zero_rows\":true,\"special_fp\":8,\"hash\":\"%016lx\"}\n",hash);
 munmap(im,span+2*page);munmap(am,span+2*page);free(x);return 0;
}
