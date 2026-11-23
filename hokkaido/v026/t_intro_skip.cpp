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
    std::atomic<unsigned> seen{0};
    std::atomic<bool> claimed{false};
    Session one, two, three;
    assert(!one.Configure(42,"video/av1","1",seen,claimed));
    assert(!one.Configure(OcarinaProgramId,"video/avc","1",seen,claimed));
    assert(!one.Configure(OcarinaProgramId,"video/av1","0",seen,claimed));
    assert(!claimed.load());
    assert(!one.Configure(OcarinaProgramId,"video/av01.0.08M.08","1",seen,claimed));
    assert(!claimed.load());
    assert(two.Configure(OcarinaProgramId,"video/av1","1",seen,claimed));
    assert(claimed.load());
    assert(!three.Configure(OcarinaProgramId,"video/av1","1",seen,claimed));
    bool eos=false;
    for(int i=0;i<3000;i++) {
        assert(two.AcceptPacket(eos));
        assert(eos == (i==0));
    }
    assert(two.PacketsIgnored()==3000);
    two.Stop(); assert(!two.Active());
    assert(!two.AcceptPacket(eos));assert(!eos);
    assert(!three.Configure(OcarinaProgramId,"video/av1","1",seen,claimed));
    unsigned eligible=0, rejected=0, eos_emitted=0;
    for(unsigned i=0;i<250000;++i) {
        const auto r=next();
        const bool matching=(r&7)==0;
        const bool enabled=(r&16)!=0;
        std::atomic<unsigned> seen_streams{0};
        std::atomic<bool> global{false};
        Session s1, s2, s3;
        const auto program=matching?OcarinaProgramId:42;
        const auto codec=((r&32)?"video/vp9":"video/av1");
        const auto opt=enabled?"1":"0";
        assert(!s1.Configure(program,codec,opt,seen_streams,global));
        const bool should=matching && enabled && !(r&32);
        assert(s2.Configure(program,codec,opt,seen_streams,global)==should);
        assert(!s3.Configure(program,codec,opt,seen_streams,global));
        for(unsigned j=0;j<7;j++) {
            bool first=false; const bool intercepted=s2.AcceptPacket(first);
            assert(intercepted==should);
            assert(first==(should && j==0));
            eos_emitted+=first;
        }
        if(should) {eligible++; assert(global.load());}
        else {rejected++; assert(!global.load());}
        s2.Stop(); assert(!s2.Active());
    }
    assert(eligible>1000&&rejected>1000&&eos_emitted==eligible);
    std::cout << "PASS intro skip: 250000 sessions, " << eligible
       << " selected, " << rejected << " rejected; exactly one EOS per selected session\n";
}
