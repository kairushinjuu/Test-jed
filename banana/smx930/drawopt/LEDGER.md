# SM-X930 Mali G925 draw-path optimization ledger

2026-11-17 JST — User authorized source-level renderer optimization after v0.15 analysis. Focus: vka_draw images+pass+key overhead, memory lifetime with correctness-preserving guards. Target OOT Switch2 Edition 0400486024DEC000; no copyrighted game data here.

- Tool: container listing: prior v0.12.1 source ZIP available, GitHub branch `banana-mali-g925-20261117` and last passed v0.15 CI `44036153707`; source not initially extracted.
- Tool: checked ZIP layout, target files present, ~29 GB disk free, clang/cmake/ninja/javac available.
- Tool: extracted complete v0.12.1 source to isolated work dir.
- Re-extracted pinned v0.12.1 Vulkan renderer source from 138MB validated source ZIP; inspected `draw_body`→`walk_all`→`make_images`→`rp_begin`, `draw_writes` and submission reset. Confirmed guest binding walk and residency checks must not be cached across draws.
- Implemented conservative `DM_VK_DRAW_FAST_SCAN=1` default in `vka_draw.c` via idempotent pinned-source patcher: per-draw indexes of texture/image and tbuf bindings + shader write flags; make_images still queries live pending state, retains original per-stage image/tbuf order, never caches Vulkan views/handles or skips barriers; `DM_VK_DRAW_FAST_SCAN=0` old loop fallback. Native compilation and device FPS not yet verified.
- Added 4 local source/order regressions and ran them. Need CI Android compilation and deliverable, keep existing v0.12.1 separate.
