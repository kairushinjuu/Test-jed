#!/usr/bin/env python3
"""v0.22 G925 bounded staging memory and native format accounting.
Never changes guest pool limits, GPU-owned texture dimensions or Vulkan format.
"""
from pathlib import Path
import argparse
ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--check',action='store_true'); a=ap.parse_args()
changes={}
def patch(rel,old,new):
    p=a.root/rel; s=changes.get(p,p.read_text())
    if new in s: return
    if s.count(old)!=1: raise RuntimeError(f'{rel}: expected exactly one anchor ({s.count(old)} found): {old[:100]!r}')
    changes[p]=s.replace(old,new,1)

patch('dm/gfx/vk_android/vka_dev.c',
    'double mb = VKA_ENVF("DM_VK_UPLOAD_BATCH_MB", 64.0);',
    'double mb = VKA_ENVF("DM_VK_UPLOAD_BATCH_MB", V.props.vendorID == 0x13B5u ? 16.0 : 64.0);')
patch('dm/gfx/vk_android/vka_dev.c',
    'double cap = VKA_ENVF("DM_VK_UPLOAD_INFLIGHT_MB", 256.0) * 1048576.0;',
    'double cap = VKA_ENVF("DM_VK_UPLOAD_INFLIGHT_MB", V.props.vendorID == 0x13B5u ? 64.0 : 256.0) * 1048576.0;')
patch('dm/gfx/vk_android/vka_dev.c',
    '''static void sblk_trim(uint64_t done, uint64_t udone) {
    VkDeviceSize idle = 0;''',
    '''static void sblk_trim(uint64_t done, uint64_t udone) {
    VkDeviceSize idle = 0;
    // v0.22: cap the idle reservation, not live upload buffers.
    // DM_VK_SCRATCH_IDLE_MB restores an explicit per-device budget.
    VkDeviceSize idle_cap = (VkDeviceSize)(VKA_ENVF("DM_VK_SCRATCH_IDLE_MB", V.props.vendorID == 0x13B5u ? 16.0 : 64.0) * 1048576.0);''')
patch('dm/gfx/vk_android/vka_dev.c',
    'if (id && (b->size > (16u << 20) || idle + b->size > (64u << 20))) {',
    'if (id && (b->size > (16u << 20) || idle + b->size > idle_cap)) {')
patch('dm/gfx/vk_android/vka_tex.c',
    'static _Atomic uint32_t g_tgen, *g_tver, *g_sver;',
    '''// v0.22: categorize VkImage memory requirements. The caller holds g_tmu.
// These sizes are not deduplicated physical memory or internal Mali shadows.
static void v022_image_categories(char *dst, size_t n) {
    uint64_t astc=0, bcn=0, other=0, gpu=0;
    unsigned na=0, nb=0, no=0, ng=0;
    for (int i=0; i<g_nlive; ++i) {
        const vka_img *im=g_live[i];
        if (im->par || !im->bytes) continue;
        VkFormat f=im->f.vk;
        if (f >= VK_FORMAT_ASTC_4x4_UNORM_BLOCK && f <= VK_FORMAT_ASTC_12x12_SRGB_BLOCK) {astc+=im->bytes; na++;}
        else if (f >= VK_FORMAT_BC1_RGB_UNORM_BLOCK && f <= VK_FORMAT_BC7_SRGB_BLOCK) {bcn+=im->bytes; nb++;}
        else {other+=im->bytes; no++;}
        if (im->gpu_owned) {gpu+=im->bytes; ng++;}
    }
    snprintf(dst,n,"ASTC=%llu MiB/%u BCn=%llu MiB/%u other=%llu MiB/%u GPU-written=%llu MiB/%u; other includes depth and render targets",
        (unsigned long long)(astc>>20),na,(unsigned long long)(bcn>>20),nb,
        (unsigned long long)(other>>20),no,(unsigned long long)(gpu>>20),ng);
}
static _Atomic uint32_t g_tgen, *g_tver, *g_sver;''')
patch('dm/gfx/vk_android/vka_tex.c',
    '''        VLOG("v021 allocation breakdown: %s; image cache=%llu MiB (GPU allocation sizes, not RSS)",
             imstat, (unsigned long long)((g_img_bytes + vka_imem_zbytes()) >> 20));''',
    '''        VLOG("v021 allocation breakdown: %s; image cache=%llu MiB (GPU allocation sizes, not RSS)",
             imstat, (unsigned long long)((g_img_bytes + vka_imem_zbytes()) >> 20));
        char fc[256]; v022_image_categories(fc, sizeof fc);
        VLOG("v022 image formats: %s", fc);''')
if not a.check:
    for p,s in changes.items(): p.write_text(s)
print('v0.22 patch', 'anchors verified' if a.check else 'applied', len(changes),'files')
