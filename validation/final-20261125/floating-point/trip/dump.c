#include <stdio.h>
#include <stdlib.h>
__attribute__((destructor)) static void dump(void){const char*p=getenv("BOLT_TRIP_OUTPUT");if(!p)_Exit(90);FILE*f=fopen(p,"wb");if(!f)_Exit(91);if(fwrite((void*)0x801000,1,192,f)!=192)_Exit(92);if(fclose(f))_Exit(93);}
