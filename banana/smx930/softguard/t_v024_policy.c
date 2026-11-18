// v0.24: 250,000 deterministic source-level eligibility and mip-remap cases.
// Host x86_64 + ASan/UBSan; exercises the production vka_soft.h, not a mock.
// No game content, files or GPU needed.
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "vka_soft.h"
static uint64_t rng = UINT64_C(0x9E3779B97F4A7C15);
static uint32_t next(void) {
    rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17;
    return (uint32_t)(rng >> 12);
}
int main(void) {
    uint64_t candidates=0,rejected=0;
    for(unsigned i=0;i<250000;i++) {
        vksoft_tex v = {
            .w=1u<<(5+next()%8),.h=1u<<(5+next()%8),
            .levels=1+next()%13,.samples=1,
            .block_w=next()%3?4:1,.has_layout=(next()&7)!=0,
            .has_mem=1,.is_2d=1,.sparse_pool=0,.linear=0
        };
        int want = v.has_layout && v.has_mem && v.is_2d && !v.sparse_pool && !v.linear &&
            v.samples<=1 && v.levels>=3 && (v.w>=v.h?v.w:v.h)>=512 &&
            (v.w<v.h?v.w:v.h)>=256 && v.block_w>=2;
        assert(vksoft_candidate(&v)==want);
        if(!want){rejected++;continue;}
        candidates++;
        for(uint32_t level=0;level<v.levels;level++) {
            uint32_t lv=level;
            int ok=vksoft_lv(1,v.levels-1,&lv);
            assert(ok==(level>0));
            if(ok)assert(lv==level-1);
            uint32_t start=level,count=v.levels-level;
            vksoft_view(1,&start,&count);
            assert(count>0 && start<v.levels-1 && start+count<=v.levels-1);
        }
    }
    assert(candidates>10000 && rejected>10000);
    const uint64_t bytes_level0=2048ull*1024/16*16;
    uint64_t total=0;
    for(unsigned w=2048,h=1024;w&&h;w=(w+1)/2,h=(h+1)/2) {
        total+=((w+3)/4)*((h+3)/4)*16;
        if(w==1&&h==1)break;
    }
    double ratio=(double)bytes_level0/(double)total;
    assert(ratio>0.74&&ratio<0.76);
    printf("PASS soft mip test: %llu candidates, %llu rejected, BC7 level0 %.2f%% of chain\n",
        (unsigned long long)candidates,(unsigned long long)rejected,100*ratio);
    return 0;
}
