package dev.nxnative.android;

import java.util.List;

/**
 * A tiny, fixed-cost SM-X930-only boot policy. No allocations in the frame loop.
 * User-provided Advanced / env.txt overrides are appended after these defaults.
 * Avoid image-size clamps or shader skipping: they can damage game correctness.
 */
final class MaliSmx930 {
    static final String MODEL = "SM-X930";
    static final String OOT = "0400486024DEC000";
    private static final String[] STABLE = {
        "DM_VK_PSO_SLOTS=1",            // bounded compiler concurrency, from observed 33,920 mmap pressure
        "DM_VK_PREWARM=0",              // no speculative shader work over game allocations
        "DM_MEM_FILEBACK=1",            // reserve physical RAM for actively used Vulkan images
        "DM_MEM_FILEBACK_KINDS=shader,texture",
        "DM_VK_IMG_RESERVE_MB=1536",    // protect system and guest heap from uncontrolled image-cache growth
        "DM_VK_IMG_DIAG=10"             // periodic diagnostic samples, not every frame
    };
    private MaliSmx930() {}

    static boolean matches(String model, String titleId) {
        return MODEL.equals(model) && OOT.equals(titleId);
    }

    static boolean apply(String model, String titleId, List<String> env) {
        if (!matches(model, titleId)) return false;
        for (String entry : STABLE) {
            final int eq = entry.indexOf('=');
            final String key = entry.substring(0, eq + 1);
            boolean exists = false;
            for (String current : env) {
                if (current.startsWith(key)) { exists = true; break; }
            }
            if (!exists) env.add(entry);
        }
        return true;
    }
}
