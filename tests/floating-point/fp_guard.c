#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <fenv.h>
void spmv(size_t,const uint64_t*,const uint32_t*,const double*,const double*,double*);
int main(void) {
  uint32_t ci[1031];double a[1031],x[1031],y;uint64_t rp[2]={0,1031};
  int modes[]={FE_TONEAREST,FE_DOWNWARD,FE_UPWARD,FE_TOWARDZERO};unsigned tests=0;
  for(int r=0;r<4;r++) for(int c=0;c<8;c++) {
    if(fesetround(modes[r])) return 2;
    for(int j=0;j<1031;j++) {
      ci[j]=j;a[j]=(j%7-3)/7.;x[j]=(j%11-5)/11.;
      if(c==1) {a[j]=(j%2)?-0.:0.;x[j]=1.;}
      if(c==2) {a[j]=0x1p-1022;x[j]=0x1p-52;}
      if(c==3) {a[j]=0x1p1023;x[j]=2.;}
      if(c==4) {a[j]=1.;x[j]=INFINITY;}
      if(c==5) {a[j]=1.;x[j]=(j%2)?-INFINITY:INFINITY;}
      if(c==6 && j==512) {uint64_t b=UINT64_C(0x7ff8000000000321);memcpy(x+j,&b,8);}
      if(c==7 && j==512) {uint64_t b=UINT64_C(0x7ff0000000000456);memcpy(x+j,&b,8);}
    }
    feclearexcept(FE_ALL_EXCEPT);double ref=0;
    for(int j=0;j<1031;j++) ref=fma(a[j],x[ci[j]],ref);
    int expected=fetestexcept(FE_ALL_EXCEPT);
    feclearexcept(FE_ALL_EXCEPT);spmv(1,rp,ci,a,x,&y);int actual=fetestexcept(FE_ALL_EXCEPT);
    if(memcmp(&ref,&y,8)||expected!=actual) {fprintf(stderr,"FP mismatch mode=%d case=%d flags=%d/%d\n",r,c,expected,actual);return 3;}
    tests++;
  }
  fesetround(FE_TONEAREST);printf("{\"floating_cases\":%u,\"rounding_modes\":4,\"output_bits_and_exception_flags_equal\":true}\n",tests);return 0;
}
