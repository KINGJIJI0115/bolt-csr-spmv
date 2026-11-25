#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
void spmv(size_t,const uint64_t*,const uint32_t*,const double*,const double*,double*);
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char **argv){
 if(argc!=4&&argc!=5)return 2;int reps=atoi(argv[2]);uint64_t seed=strtoull(argv[3],0,10);if(reps<1)return 3;
 FILE *f=fopen(argv[1],"rb");if(!f)return 4;uint64_t head[4];if(fread(head,8,4,f)!=4||head[0]!=0x3152434454455354ULL)return 5;
 uint64_t rows=head[1],cols=head[2],nnz=head[3];if(!rows||!cols||cols>UINT32_MAX||rows>100000000||nnz>1000000000)return 6;
 uint64_t *rp=malloc((rows+1)*8);uint32_t *ci=malloc((nnz+1)*4);double *a=malloc((nnz+1)*8),*x=malloc(cols*8),*y=malloc(rows*8),*ref=malloc(rows*8);
 if(!rp||!ci||!a||!x||!y||!ref)return 7;
 if(fread(rp,8,rows+1,f)!=rows+1||fread(ci,4,nnz,f)!=nnz||fread(a,8,nnz,f)!=nnz||fgetc(f)!=EOF)return 8;fclose(f);
 if(rp[0]||rp[rows]!=nnz)return 9;for(uint64_t r=0;r<rows;r++)if(rp[r]>rp[r+1])return 10;for(uint64_t j=0;j<nnz;j++)if(ci[j]>=cols||!isfinite(a[j]))return 11;
 for(uint64_t i=0;i<cols;i++){seed^=seed<<13;seed^=seed>>7;seed^=seed<<17;x[i]=((int)(seed%2003)-1001)/1009.0;}
 for(uint64_t r=0;r<rows;r++){double s=0;for(uint64_t j=rp[r];j<rp[r+1];j++)s=fma(a[j],x[ci[j]],s);ref[r]=s;}
 spmv(rows,rp,ci,a,x,y);if(memcmp(y,ref,rows*8))return 12;
 double start=now();for(int k=0;k<reps;k++)spmv(rows,rp,ci,a,x,y);double elapsed=now()-start;
 if(memcmp(y,ref,rows*8))return 13;uint64_t hash=1469598103934665603ULL;double sum=0;
 for(uint64_t r=0;r<rows;r++){uint64_t bits;memcpy(&bits,y+r,8);hash=(hash^bits)*1099511628211ULL;sum+=y[r];}
 printf("{\"seconds\":%.9f,\"checksum\":%.17g,\"output_hash\":\"%016lx\",\"rows\":%lu,\"cols\":%lu,\"nnz\":%lu,\"reps\":%d}\n",elapsed,sum,hash,rows,cols,nnz,reps);
 if(argc==5){FILE *dump=fopen(argv[4],"wb");if(!dump||fwrite(y,8,rows,dump)!=rows||fclose(dump))return 14;}
 free(rp);free(ci);free(a);free(x);free(y);free(ref);return 0;
}
