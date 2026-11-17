#!/usr/bin/env python3
"""Pinned SM-X930 v0.8 -> v0.12.1 experimental performance patch.
Refuse source mismatches, preserve safe failure; run on the *already Mali-v0.8-patched* tree.
"""
import argparse
from pathlib import Path

def replace(root, rel, old, new, check):
    p = root / rel
    content = p.read_text(encoding='utf8')
    # The replacement may deliberately include the old prefix, so check that
    # the exact new span exists before checking the original anchor.
    if content.count(new) == 1:
        print('already patched',rel)
        return
    if content.count(old) != 1:
        raise ValueError(f'{rel}: expected one source anchor, found {content.count(old)}')
    if not check:
        p.write_text(content.replace(old,new,1),encoding='utf8')
    print('checked' if check else 'patched', rel)

def main(root,check=False):
    j='android/app/src/main/java/dev/nxnative/android/MaliSmx930.java'
    replace(root,j,'''        "DM_VK_PREWARM=0",              // no speculative shader work over game allocations''','''        "DM_VK_PREWARM=1",              // Mali: compile known first-scene pipelines during intro (single nice+10 thread)
        "DM_VK_PREWARM_MAX=256",        // only the first 256 seed records, not the full shader library
        "DM_VK_PREWARM_MALI_MIN_MB=3072", // stop starting prewarm builds when free RAM is scarce
        "DM_VK_PCACHE_SAVE_SLOW_S=1",   // save expensive first-use results promptly''',check)
    replace(root,j,'''        "DM_VK_IMG_DIAG=10"             // periodic diagnostic samples, not every frame''','''        "DM_VK_IMG_DIAG=10",            // periodic diagnostic samples, not every frame
        "DM_VK_SLOT_POOL=1"             // Mali per-slot pool reset avoids repetitive individual buffer resets''',check)
    p='dm/gfx/vk_android/vka_pso.c'
    old='''        pause_point();
        if (me > 0 && mem_mb) {'''
    new='''        pause_point();
        // Mali safeguard: only begin speculative compiles while enough memory remains.
        // Unlike the generic policy, this applies to worker zero as well; the game
        // continues normally when prewarm stops. Never wait here holding a pipeline gate.
        if (V.props.vendorID == 0x13B5u) {
            int floor_mb = VKA_ENV("DM_VK_PREWARM_MALI_MIN_MB", 0);
            uint64_t avail_mb = floor_mb > 0 ? mem_avail_mb() : 0;
            if (floor_mb > 0 && avail_mb && avail_mb < (uint64_t)floor_mb) {
                VLOG("Mali prewarm: stopped at %llu MiB MemAvailable (floor %d MiB); game work takes priority",
                     (unsigned long long)avail_mb, floor_mb);
                break;
            }
        }
        if (me > 0 && mem_mb) {'''
    replace(root,p,old,new,check)
    # Force the memory check to happen before each compile, not only before taking the queue slot.
    p='dm/gfx/vk_android/vka.h'
    old='''    X(vkCreateCommandPool) X(vkAllocateCommandBuffers) X(vkResetCommandBuffer) X(vkBeginCommandBuffer) X(vkEndCommandBuffer) \\\n'''
    new='''    X(vkCreateCommandPool) X(vkAllocateCommandBuffers) X(vkResetCommandBuffer) X(vkResetCommandPool) X(vkBeginCommandBuffer) X(vkEndCommandBuffer) \\\n'''
    replace(root,p,old,new,check)
    p='dm/gfx/vk_android/vka_exec.c'
    replace(root,p,'''static struct { VkCommandBuffer cb; uint64_t fence; VkCommandBuffer x[NCHUNK]; VkFence vf; int vf_on; } g_slot[NSLOT];''','''static struct { VkCommandBuffer cb; uint64_t fence; VkCommandBuffer x[NCHUNK]; VkFence vf; int vf_on; VkCommandPool pool; } g_slot[NSLOT];''',check)
    replace(root,p,'''static VkCommandPool g_pool;''','''static VkCommandPool g_pool;
static int g_slot_pool_mode; // Mali: own command pool for each reusable completed slot''',check)
    old='''    if (!g_pool) {
        VkCommandPoolCreateInfo pi = {VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT, .queueFamilyIndex = V.qf};
        VkCommandBuffer cbs[NSLOT];
        VkCommandBufferAllocateInfo ai = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = NSLOT};
        if (vk.vkCreateCommandPool(V.dev, &pi, NULL, &g_pool) || ((ai.commandPool = g_pool), vk.vkAllocateCommandBuffers(V.dev, &ai, cbs))) { VRED("submission command buffers not made"); g_pool = VK_NULL_HANDLE; return; }
        for (int i = 0; i < NSLOT; i++) g_slot[i].cb = cbs[i];
    }'''
    new='''    if (!g_pool) {
        // Arm GPUs benefit from whole-pool resets rather than resetting each
        // buffer.  A pool belongs to exactly one slot and is reset only after
        // that slot's GPU fence completes (below).  We avoid RESET_COMMAND_BUFFER_BIT.
        if (V.props.vendorID == 0x13B5u && VKA_ENV("DM_VK_SLOT_POOL", 0)) {
            int ok = vk.vkResetCommandPool != NULL;
            for (int i = 0; ok && i < NSLOT; i++) {
                VkCommandPoolCreateInfo pi = {VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, .queueFamilyIndex = V.qf};
                VkCommandBufferAllocateInfo ai = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                    .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1};
                if (vk.vkCreateCommandPool(V.dev, &pi, NULL, &g_slot[i].pool)) { ok = 0; break; }
                ai.commandPool = g_slot[i].pool;
                if (vk.vkAllocateCommandBuffers(V.dev, &ai, &g_slot[i].cb)) { ok = 0; break; }
            }
            if (ok) {
                g_pool = g_slot[0].pool; g_slot_pool_mode = 1;
                VLOG("Mali command pools: one pool per completed replay slot; pool resets, no individual buffer resets");
            } else {
                for (int i = 0; i < NSLOT; i++) {
                    if (g_slot[i].pool) vk.vkDestroyCommandPool(V.dev, g_slot[i].pool, NULL);
                    g_slot[i].pool = VK_NULL_HANDLE; g_slot[i].cb = VK_NULL_HANDLE;
                }
                VRED_ONCE("Mali per-slot command pools unavailable: using original replay pool");
            }
        }
        if (!g_pool) {
            VkCommandPoolCreateInfo pi = {VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT, .queueFamilyIndex = V.qf};
            VkCommandBuffer cbs[NSLOT];
            VkCommandBufferAllocateInfo ai = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = NSLOT};
            if (vk.vkCreateCommandPool(V.dev, &pi, NULL, &g_pool) ||
                ((ai.commandPool = g_pool), vk.vkAllocateCommandBuffers(V.dev, &ai, cbs))) {
                VRED("submission command buffers not made"); g_pool = VK_NULL_HANDLE; return;
            }
            for (int i = 0; i < NSLOT; i++) g_slot[i].cb = cbs[i];
        }
    }'''
    replace(root,p,old,new,check)
    old='''    g_cb = g_slot[k].cb;
    vk.vkResetCommandBuffer(g_cb, 0);
    VkCommandBufferBeginInfo bi = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};'''
    new='''    g_cb = g_slot[k].cb;
    if (g_slot_pool_mode) {
        // All command buffers of this slot (including split chunks) are retired
        // by the completion fence above. Synchronize the host encoder before reset.
        vka_enc_sync();
        VkResult rr = vk.vkResetCommandPool(V.dev, g_slot[k].pool, 0);
        if (rr) { VRED("Mali slot %u command pool reset failed: %d", k, rr); g_cb = VK_NULL_HANDLE; return; }
    } else vk.vkResetCommandBuffer(g_cb, 0);
    VkCommandBufferBeginInfo bi = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};'''
    replace(root,p,old,new,check)
    replace(root,p,'''    vk.vkResetCommandBuffer(cb, 0);
    VkCommandBufferBeginInfo bi = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};''','''    if (!g_slot_pool_mode) vk.vkResetCommandBuffer(cb, 0); // slot-pool reset already returned every chunk to initial state
    VkCommandBufferBeginInfo bi = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT};''',check)
    replace(root,p,'''VkCommandBufferAllocateInfo ai = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, .commandPool = g_pool, .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1};''','''VkCommandBufferAllocateInfo ai = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
            .commandPool = g_slot_pool_mode ? g_slot[k].pool : g_pool,
            .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1};''',check)
    # Never reset a Mali slot pool if a GPU fence timed out. On the Tab S11
    # Ultra we have observed >6-second GPU fence stalls; the original fallback
    # reuses the command buffer anyway, which is unsafe for whole-pool resets.
    replace(root,p,'''    if (g_slot[k].vf_on) {
        if (vk.vkWaitForFences(V.dev, 1, &g_slot[k].vf, VK_TRUE, vka_hang_ns())) VRED_ONCE("a command buffer slot's fence was not reached in the hang time: reused anyway");
        vk.vkResetFences(V.dev, 1, &g_slot[k].vf); g_slot[k].vf_on = 0;
        if (g_slot_ts[k]) gpu_slot_done(k);   // its GPU times are there (its timeline fence may come later)
    } else if (g_slot[k].fence) vka_wait_done(g_slot[k].fence, UINT64_MAX);''', '''    if (g_slot[k].vf_on) {
        VkResult fr = vk.vkWaitForFences(V.dev, 1, &g_slot[k].vf, VK_TRUE, vka_hang_ns());
        if (fr) {
            VRED_ONCE("a command buffer slot's fence was not reached in the hang time: reused anyway");
            if (g_slot_pool_mode) { // No reuse or pool reset while commands may be in flight.
                VRED("Mali command pool slot %u: fence wait failed %d; preserve in-flight buffers", k, fr);
                g_cb = VK_NULL_HANDLE; return;
            }
        }
        vk.vkResetFences(V.dev, 1, &g_slot[k].vf); g_slot[k].vf_on = 0;
        if (g_slot_ts[k]) gpu_slot_done(k);   // its GPU times are there (its timeline fence may come later)
    } else if (g_slot[k].fence) {
        int completed = vka_wait_done(g_slot[k].fence, UINT64_MAX);
        if (!completed && g_slot_pool_mode) {
            VRED("Mali command pool slot %u: timeline slot not retired, preserving command buffers", k);
            g_cb = VK_NULL_HANDLE; return;
        }
    }''',check)
    # Controlled submit diagnostics are bounded and off by default. No potentially unsafe barriers removed.
    p='dm/gfx/vk_android/vka_dev.c'
    replace(root,p,'''static _Atomic uint64_t g_qs_lock_ns, g_qs_call_ns, g_qs_n;''','''static _Atomic uint64_t g_qs_lock_ns, g_qs_call_ns, g_qs_n;
static _Atomic int g_mali_trace_left = -1; // bounded DM_VK_SUBMIT_TRACE count (off by default)''',check)
    old='''    g_qs_lock_ns += t1 - t0; g_qs_call_ns += now_ns() - t1; g_qs_n++;
    if (!r && signal > V.tl_queued) __atomic_store_n(&V.tl_queued, signal, __ATOMIC_RELEASE);
    pthread_mutex_unlock(&V.qmu);
    if (r == VK_ERROR_DEVICE_LOST) vka_device_lost("a submission");'''
    new='''    uint64_t t2 = now_ns();
    g_qs_lock_ns += t1 - t0; g_qs_call_ns += t2 - t1; g_qs_n++;
    if (!r && signal > V.tl_queued) __atomic_store_n(&V.tl_queued, signal, __ATOMIC_RELEASE);
    pthread_mutex_unlock(&V.qmu);
    if (V.props.vendorID == 0x13B5u) {
        int left = atomic_load_explicit(&g_mali_trace_left, memory_order_relaxed);
        if (left < 0) {
            int budget = VKA_ENV("DM_VK_SUBMIT_TRACE", 0);
            if (budget < 0) budget = 0;
            if (budget > 2048) budget = 2048;
            int initial = -1;
            atomic_compare_exchange_strong(&g_mali_trace_left, &initial, budget);
            left = atomic_load_explicit(&g_mali_trace_left, memory_order_relaxed);
        }
        while (left > 0 && !atomic_compare_exchange_weak_explicit(&g_mali_trace_left, &left, left-1,
                memory_order_relaxed, memory_order_relaxed)) {}
        if (left > 0) VLOG("Mali submit trace: %s cb=%d signal=%llu waits=%u binary=%d fence=%d host_signal=%d lock=%.3f ms driver=%.3f ms result=%d",
            signal ? "timeline" : fence ? "fenced" : "part-or-auxiliary", cb != VK_NULL_HANDLE,
            (unsigned long long)signal, nwait, bin_signal != VK_NULL_HANDLE, fence != VK_NULL_HANDLE,
            hf != VK_NULL_HANDLE, (t1-t0)/1e6, (t2-t1)/1e6, r);
    }
    if (r == VK_ERROR_DEVICE_LOST) vka_device_lost("a submission");'''
    replace(root,p,old,new,check)
    # No unbounded GPU queue batching: guest events and command ordering must be proven first.

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--check',action='store_true');ns=ap.parse_args();main(ns.root,ns.check)
