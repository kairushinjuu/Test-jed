#include <cassert>
#include <cstdint>
#include "video_core/vulkan_common/android_pressure_policy.h"

using VideoCommon::AndroidMemoryPolicy::ShouldCollectInFrame;

int main() {
    assert(!ShouldCollectInFrame(false, false, 1024, 512));
    assert(!ShouldCollectInFrame(true, true, 1024, 512));
    assert(!ShouldCollectInFrame(true, false, 511, 512));
    assert(ShouldCollectInFrame(true, false, 512, 512));
    assert(ShouldCollectInFrame(true, false, 513, 512));
    assert(!ShouldCollectInFrame(true, false, 513, 0));
}
