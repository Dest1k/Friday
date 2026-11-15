/* Own non-Office LP64/SysV ABI fixture; its values have no metric meaning. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
struct UData { int32_t refs, length; uint16_t buf[2]; };
struct UString { struct UData *data; };
struct Device { int64_t value; };
struct Font { struct Device *device; };
int fixture_mode, fixture_repeat;
extern int32_t fixture_outer(struct Font *, struct UString *);
static void phase(const char *state, int index) {
 const char *path=getenv("FRW_FIXTURE_PHASE"), *nonce=getenv("FRW_FIXTURE_NONCE");
 char tmp[4096]; snprintf(tmp,sizeof(tmp),"%s.pending",path);
 FILE *f=fopen(tmp,"w"); if(!f) _exit(9);
 if(index<0) fprintf(f,"{\"nonce\":\"%s\",\"phase\":\"%s\",\"index\":null,\"digit\":null}\n",nonce,state);
 else fprintf(f,"{\"nonce\":\"%s\",\"phase\":\"%s\",\"index\":%d,\"digit\":\"%d\"}\n",nonce,state,index,index);
 if(fclose(f)||rename(tmp,path)) _exit(10);
}
int fixture_main(int argc,char **argv) {
 const char *mode=argc>1?argv[1]:"ok";
 fixture_mode=!strcmp(mode,"missing")?1:!strcmp(mode,"duplicate")?2:!strcmp(mode,"caller")?3:0;
 struct Device d={ !strcmp(mode,"overflow")?INT64_C(4294967422):126 };
 struct Font f={&d}; struct UData data={1,1,{48,0}}; struct UString s={&data};
 volatile int32_t sink=0;
 int count=!strcmp(mode,"short")?9:!strcmp(mode,"extra")?11:10;
 for(int i=0;i<count;i++) {
  int ix=i<10?i:9; phase("METRIC",ix);
  data.buf[0]=48+((!strcmp(mode,"misaligned")&&i==4)?5:ix);
  fixture_repeat=0; sink=fixture_outer(&f,&s);
 }
 phase("CLOSED",-1);
 return sink==126?0:4;
}
