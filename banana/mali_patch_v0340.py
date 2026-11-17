#!/usr/bin/env python3
"""Deterministic v0.3.40 Mali-G925 source patch. Pinned upstream e6b6f0d07a."""
from pathlib import Path
def replace(rel, old, new):
    path=Path(rel)
    s=path.read_text()
    if s.count(old)!=1:
        raise RuntimeError(f"{rel}: expected exactly one anchor, found {s.count(old)}")
    path.write_text(s.replace(old,new,1))
    print("PATCH",rel,len(s),len(s.replace(old,new,1)))
dev='dm/gfx/vk_android/vka_dev.c'
replace(dev,
'''    if (!V.placed && vk.vkMapMemory2KHR && vk.vkUnmapMemory2KHR) {
        const char *e = getenv("DM_VK_PLACED_PROBE");
        if (!e || strcmp(e, "0")) V.placed = vka_placed_probe();
    }''',
'''    // On Mali, do not probe unadvertised placed memory support implicitly.
    if (!V.placed && vk.vkMapMemory2KHR && vk.vkUnmapMemory2KHR) {
        const char *e = getenv("DM_VK_PLACED_PROBE");
        if (e ? strcmp(e, "0") != 0 : V.props.vendorID != 0x13B5u)
            V.placed = vka_placed_probe();
    }''')
replace(dev,
'''    if (!V.placed && !V.fd_alias) VRED("no placed maps or exported guest memory alias: guest memory stays anonymous and the GPU sees no memory pool");''',
'''    if (V.props.vendorID == 0x13B5u) {
        VLOG("Mali readiness: driver %s; placed=%d fd_alias=%d BC=%d mesh=%d compute_mesh=%d GPL=%d sparse=%d",
             pdr.driverName, V.placed, V.fd_alias, f2.features.textureCompressionBC,
             V.mesh, V.memu, V.gpl, V.sparse_res);
        if (!V.placed && !V.fd_alias)
            VRED("Mali: no valid guest-memory mapping path; a compatible placed-memory or exported FD-alias driver is required");
        if (!f2.features.textureCompressionBC)
            VRED("Mali: BC textures unsupported by active driver; texture conversion or a compatible driver is required");
        if (!V.mesh && !V.memu)
            VRED("Mali: mesh shader and compute-mesh fallback both unavailable");
    }
    if (!V.placed && !V.fd_alias) VRED("no placed maps or exported guest memory alias: guest memory stays anonymous and the GPU sees no memory pool");''')
replace('dm/gfx/vk_android/vka_pso.c',
'''    int nt = VKA_ENV("DM_VK_PREWARM", V.qcom_old ? 0 : 4);''',
'''    int nt = VKA_ENV("DM_VK_PREWARM", V.qcom_old ? 0 : V.props.vendorID == 0x13B5u ? 2 : 4);''')
present='dm/gfx/vk_android/vka_present.c'
replace(present,'enum { NFRAME = 3, MAXIMG = 8, PQ = 8, PRING = 512 };',
        'enum { NFRAME = 3, MAXIMG = 32, PQ = 8, PRING = 512 };')
replace(present,
'''    uint32_t n = caps.minImageCount < 3 ? 3 : caps.minImageCount; if (caps.maxImageCount && n > caps.maxImageCount) n = caps.maxImageCount; if (n > MAXIMG) n = MAXIMG;''',
'''    if (caps.minImageCount > MAXIMG) { VRED("swapchain: min %u images exceeds MAXIMG=%u", caps.minImageCount, (unsigned)MAXIMG); return 0; }
    uint32_t n = caps.minImageCount < 3 ? 3 : caps.minImageCount; if (caps.maxImageCount && n > caps.maxImageCount) n = caps.maxImageCount; if (n > MAXIMG) n = MAXIMG;''')
replace(present,
'''    g_nimg = MAXIMG; vk.vkGetSwapchainImagesKHR(V.dev, sw, &g_nimg, g_simg);''',
'''    uint32_t actual_images = 0;
    r = vk.vkGetSwapchainImagesKHR(V.dev, sw, &actual_images, NULL);
    if (r != VK_SUCCESS || !actual_images || actual_images > MAXIMG) {
        VRED("swapchain: driver returned %u images (%d), maximum %u", actual_images, r, (unsigned)MAXIMG);
        vk.vkDestroySwapchainKHR(V.dev, sw, NULL); g_swap = VK_NULL_HANDLE; g_nimg = 0; return 0;
    }
    g_nimg = actual_images;
    r = vk.vkGetSwapchainImagesKHR(V.dev, sw, &g_nimg, g_simg);
    if (r != VK_SUCCESS || g_nimg != actual_images) {
        VRED("swapchain: enumeration failed or changed (%d; %u of %u)", r, g_nimg, actual_images);
        vk.vkDestroySwapchainKHR(V.dev, sw, NULL); g_swap = VK_NULL_HANDLE; g_nimg = 0; return 0;
    }''')
replace('android/app/src/main/java/dev/nxnative/android/MainActivity.java',
'''if (addFab != null) addFab.setVisibility(games.isEmpty() && !Ondevice.showing() ? View.GONE : View.VISIBLE);''',
'''if (addFab != null) addFab.setVisibility(View.VISIBLE);''')
print("Mali source patch complete")
