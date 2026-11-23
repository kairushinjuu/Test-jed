#include <atomic>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <string>
#include "core/hle/service/nx2_intro_skip.h"
using namespace Service::Nx2IntroSkip;
static uint64_t state = UINT64_C(0x7bdbde9d472d1001);
static uint64_t next() {state^=state<<13;state^=state>>7;state^=state<<17;return state;}
int main() {
    assert(IsAv1("video/av1"));
    assert(IsAv1("video/av01"));
    assert(IsAv1("video/av01.0.08M.08"));
    for (auto s : {"", "video/avc", "video/vp9", "video/av123", "application/av01"})
        assert(!IsAv1(s));
    assert(Requested("1"));
    for (const char* s : std::initializer_list<const char*>{nullptr,"", "0", "2", "1garbage", "true"}) assert(!Requested(s));
    std::atomic<bool> claimed{false};
    Session one, two;
    assert(!one.Configure(42,"video/av1","1",claimed));
    assert(!one.Configure(OcarinaProgramId,"video/avc","1",claimed));
    assert(!one.Configure(OcarinaProgramId,"video/av1","0",claimed));
    assert(!claimed.load());
    assert(one.Configure(OcarinaProgramId,"video/av01.0.08M.08","1",claimed));
    assert(claimed.load());
    assert(!two.Configure(OcarinaProgramId,"video/av1","1",claimed));
    bool eos=false;
    for(int i=0;i<3000;i++) {
        assert(one.AcceptPacket(eos));
        assert(eos == (i==0));
    }
    assert(one.PacketsIgnored()==3000);
    one.Stop(); assert(!one.Active());
    assert(!one.AcceptPacket(eos));assert(!eos);
    assert(!one.Configure(OcarinaProgramId,"video/av1","1",claimed));
    unsigned eligible=0, rejected=0, eos_emitted=0;
    for(unsigned i=0;i<250000;++i) {
        const auto r=next();
        const bool matching=(r&7)==0;
        const bool enabled=(r&16)!=0;
        std::atomic<bool> global{false}; Session s;
        const bool configured=s.Configure(matching?OcarinaProgramId:42,
                   ((r&32)?"video/vp9":"video/av1"),enabled?"1":"0", global);
        const bool should=matching && enabled && !(r&32);
        assert(configured==should);
        for(unsigned j=0;j<7;j++) {
            bool first=false; const bool intercepted=s.AcceptPacket(first);
            assert(intercepted==should);
            assert(first==(should && j==0));
            eos_emitted+=first;
        }
        if(configured) {eligible++; assert(global.load());}
        else {rejected++; assert(!global.load());}
        s.Stop(); assert(!s.Active());
    }
    assert(eligible>1000&&rejected>1000&&eos_emitted==eligible);
    std::cout << "PASS intro skip: 250000 sessions, " << eligible
       << " selected, " << rejected << " rejected; exactly one EOS per selected session\n";
}
