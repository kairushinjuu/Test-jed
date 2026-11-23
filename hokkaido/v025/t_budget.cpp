#include <cassert>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include "video_core/texture_cache/eviction_age.h"
using VideoCommon::RetentionBudget;
using VideoCommon::RetentionBudgetRise;
using VideoCommon::EvictionAge;
static uint64_t state=0x0123456789abcdefULL;
static uint64_t rand64(){state^=state<<13;state^=state>>7;state^=state<<17;return state;}
int main(){
 const uint64_t MiB=1ULL<<20;
 uint64_t held=0, steps=0, slow=0, drops=0;
 for(int i=0;i<250000;i++){
   uint64_t sample=(2049+(rand64()%14336))*MiB;
   uint64_t before=held;
   held=RetentionBudget(held,sample);
   assert(held<=sample);
   if(before&&sample<before){assert(held==sample);drops++;}
   if(before&&sample>before){assert(held<=before+RetentionBudgetRise);if(held<sample)slow++;}
   steps++;
   uint64_t used=rand64()%20000*MiB;
   uint64_t critical=(4096+(rand64()%8192))*MiB;
   uint64_t override_age=rand64()%4000;
   uint64_t mode_age=(rand64()%3==0)?10:(rand64()%2==0?25:50);
   const bool oom=bool(rand64()&1);
   const auto age=EvictionAge(mode_age,override_age,used,critical,oom);
   assert(age>=mode_age);
   if(oom||used>=critical)assert(age==mode_age);
   else assert(age>=VideoCommon::MinEvictionAge);
 }
 assert(drops>10000&&slow>10000);
 // Reproduce the whole pressure trace, including a rapid 11 -> 8 GiB budget drop,
 // then a 10 GiB rebound that must be followed only gradually.
 held=RetentionBudget(0,11*1024*MiB);
 assert(held==11*1024*MiB);
 held=RetentionBudget(held,8*1024*MiB);
 assert(held==8*1024*MiB);
 for(int i=0;i<30;i++){held=RetentionBudget(held,10*1024*MiB);assert(held== (8*1024+i*16+16)*MiB);}
 assert(held== (8*1024+480)*MiB);
 std::cout<<"PASS 250000 retention/eviction cases: "<<steps<<" total, "<<drops<<" immediate drops, "<<slow<<" bounded rises\n";
}