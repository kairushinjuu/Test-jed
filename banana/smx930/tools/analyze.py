#!/usr/bin/env python3
"""SM-X930 / Mali-G925 log benchmark. Stdlib-only, strict about unavailable data.

No GPU simulation: these summaries describe *observed device logs* only.
"""
import argparse
import json
import re
import statistics
from pathlib import Path

TARGET = 50.0
FPS = re.compile(r'\[vk\] fps: (\d+(?:\.\d+)?) game frames a second.*?([\d.]+) presented')
SWAP = re.compile(r'\[vk\] swapchain \d+x\d+, (\d+) images')
OOMMEM = re.compile(r'\[vk\] memory: placed pools (\d+) MiB, images (\d+) MiB.*?scratch (\d+) MiB.*?: (\d+) MiB')
AVAIL = re.compile(r'MemAvailable (\d+) MiB')
IMG = re.compile(r'\[vk\] large image[^\n]*?(\d+x\d+)[^\n]*?(\d+(?:\.\d+)?) MiB')
COMPILE = re.compile(r'(?:pipeline|shader|fragment shader)[^\n]*?took (\d+(?:\.\d+)?) (ms|s)')
FRAME = re.compile(r'on-screen up to frame \d+: (\d+) frames, dropped (\d+).*?p99 ([\d.]+) ms; footprint (\d+) MiB')
PACING = re.compile(r'frame step: game time ([\d.]+) s in ([\d.]+) s')
MAPS = re.compile(r'(?:memory maps:?\s*|memory maps )([\d]+) of ([\d]+)')
DRIVER = re.compile(r'\[vk\] driver: ([^\n]+)')
DEVICE = re.compile(r'\[vk\] device (Mali-[^,]+)')
TARGET_ID = '0400486024DEC000'
# Device-only intro/audio diagnostics. The regexes intentionally require explicit log events;
# absent counters stay unknown, not zero. Each callback report covers a distinct 2000-call window.
AUDIO_WINDOW = re.compile(r'audio #\d+ device callbacks (\d+):.*?in these 2000, (\d+) underruns, ([\d.]+) ms zero-padded')
PACE_COST = re.compile(r'pace cost up to frame (\d+).*?queue submit ([\d.]+)')
PACE_GPU = re.compile(r'pace up to frame (\d+).*?GPU busy p50/p90 ([\d.]+)/([\d.]+) ms')
LONGFRAME = re.compile(r'\[longframe\] frame (\d+) \(([\d.]+) s\) whole frame ([\d.]+) ms')
FENCE_WAIT = re.compile(r'waits: GPU fences ([\d.]+)')
AAUDIO_OPEN = re.compile(r'AAudio stream: (\d+) Hz,.*?burst (\d+) frames, buffer (\d+) frames \(asked (\d+)\)')

def parse(text: str, digest: str = '') -> dict:
    lines = text.splitlines()
    intro_end = next((i for i, s in enumerate(lines) if '[codec] AV1 decoder 1: end of stream' in s), None)
    fps_samples = []
    env_values = {}
    for line in lines:
        mm = re.search(r'\[nxlaunch\] env (DM_[A-Z0-9_]+)=([^\n]+)', line)
        if mm: env_values[mm[1]] = mm[2]
    build = next((line[len('[nxlaunch] build '):] for line in lines if line.startswith('[nxlaunch] build ')), None)
    onscreen = []
    mem = []
    available = []
    compiles = []
    huge = []
    maps = []
    time_ratios = []
    swapchain_ok = 0
    swapchain_fail = 0
    audio_samples = []
    pace_submit_ms = []
    pace_gpu_ms = []
    longframes = []
    aaudio_open = []
    codec_ahead = 0
    for i, s in enumerate(lines):
        m = FPS.search(s)
        if m: fps_samples.append({'line': i+1, 'fps': float(m[1]), 'phase': 'intro' if intro_end is not None and i < intro_end else 'post_intro' if intro_end is not None else 'unclassified'})
        m = FRAME.search(s)
        if m: onscreen.append({'line': i+1, 'frames': int(m[1]), 'dropped': int(m[2]), 'p99_ms': float(m[3]), 'footprint_mib': int(m[4]), 'phase': 'intro' if intro_end is not None and i < intro_end else 'post_intro' if intro_end is not None else 'unclassified'})
        m = OOMMEM.search(s)
        if m: mem.append({'line': i+1, 'placed_mib': int(m[1]), 'images_mib': int(m[2]), 'scratch_mib': int(m[3]), 'total_mib': int(m[4])})
        m = AVAIL.search(s)
        if m: available.append(int(m[1]))
        m = COMPILE.search(s)
        if m: compiles.append(float(m[1]) * (1000 if m[2] == 's' else 1))
        m = IMG.search(s)
        if m: huge.append({'line': i+1, 'dimensions': m[1], 'mib': float(m[2])})
        m = MAPS.search(s)
        if m: maps.append([int(m[1]), int(m[2])])
        m = PACING.search(s)
        if m and float(m[2]): time_ratios.append(float(m[1])/float(m[2]))
        if SWAP.search(s): swapchain_ok += 1
        if 'vkCreateSwapchainKHR' in s and '-1000072003' in s: swapchain_fail += 1
        if m := AUDIO_WINDOW.search(s): audio_samples.append({'line':i+1,'callback':int(m[1]),'underruns':int(m[2]),'silence_ms':float(m[3])})
        if m := PACE_COST.search(s): pace_submit_ms.append(float(m[2]))
        if m := PACE_GPU.search(s): pace_gpu_ms.append(float(m[2]))
        if m := LONGFRAME.search(s):
            mw = FENCE_WAIT.search(s)
            longframes.append({'line':i+1,'frame':int(m[1]),'seconds':float(m[2]),'whole_ms':float(m[3]),'gpu_fence_wait_ms':float(mw[1]) if mw else None})
        if m := AAUDIO_OPEN.search(s): aaudio_open.append({'rate_hz':int(m[1]),'burst_frames':int(m[2]),'buffer_frames':int(m[3]),'requested_frames':int(m[4])})
        if '[codec] AV1 decoder' in s and 'packet refused (busy)' in s: codec_ahead += 1
    driver = next((m[1] for s in lines if (m:=DRIVER.search(s))), None)
    gpu = next((m[1] for s in lines if (m:=DEVICE.search(s))), None)
    phase_fps = lambda name: [x['fps'] for x in fps_samples if x['phase'] == name]
    play = phase_fps('post_intro')
    n_drop = sum(x['dropped'] for x in onscreen)
    n_seen = sum(x['frames'] for x in onscreen)
    post_stats = [x for x in onscreen if x['phase'] == 'post_intro']
    post_drop = sum(x['dropped'] for x in post_stats)
    post_seen = sum(x['frames'] for x in post_stats)
    post_ratio = post_drop/(post_seen+post_drop) if post_seen+post_drop else None
    post_p99 = max((x['p99_ms'] for x in post_stats),default=None)
    digest_oom = 'out of memory' in digest.lower() or 'ran out of memory' in digest.lower()
    flags = []
    if swapchain_fail: flags.append('SWAPCHAIN_FAILED')
    if not swapchain_ok: flags.append('NO_SUCCESSFUL_SWAPCHAIN_OBSERVED')
    if digest_oom: flags.append('APP_DIGEST_REPORTS_OOM_NOT_PROVEN_BY_LOG')
    if intro_end is None: flags.append('INTRO_END_NOT_OBSERVED')
    if len(play) < 10: flags.append('INSUFFICIENT_GAMEPLAY_FPS_SAMPLES')
    if mem and max(x['total_mib'] for x in mem) >= 2400: flags.append('GRAPHICS_ALLOCATIONS_OVER_2400_MIB')
    if compiles and max(compiles) >= 250: flags.append('LONG_SHADER_COMPILATION')
    if sum(a['underruns'] for a in audio_samples) > 0: flags.append('AUDIO_BUFFER_UNDERRUNS_OBSERVED')
    if longframes and max(x['whole_ms'] for x in longframes) >= 100: flags.append('LONG_FRAME_STALL_OVER_100MS')
    if pace_submit_ms and statistics.median(pace_submit_ms) >= 5: flags.append('CPU_DRIVER_SUBMIT_TIME_OVER_5MS_PER_FRAME')
    def rnd(x): return round(x, 2) if x is not None else None
    # We never claim a pass with fewer than 10 observations after the intro.
    play_median = statistics.median(play) if play else None
    play_p10 = sorted(play)[max(0, int(len(play)*0.10)-1)] if play else None
    passed = bool(len(play) >= 10 and play_median >= TARGET and play_p10 >= 45
                  and (post_ratio is None or post_ratio <= 0.03)
                  and (post_p99 is None or post_p99 <= 40)
                  and not swapchain_fail and not digest_oom)
    return {
        'target_hardware':'Samsung SM-X930 / Immortalis Mali-G925 MC12',
        'target_fps': TARGET,
        'game_title_id': TARGET_ID,
        'gpu':gpu, 'driver':driver, 'build':build, 'environment': {k: env_values.get(k) for k in ('DM_GRAPHICS_SCALE','DM_ROMFS_OVERLAY','DM_VK_NDSR','DM_VK_PSO_SLOTS','DM_VK_PREWARM','DM_VK_IMG_RESERVE_MB','DM_MEM_FILEBACK','DM_VK_TL_HOST','DM_DBG_AU_FRAMES','DM_CODEC_STATS')}, 'log_lines':len(lines),
        'swapchain_successes':swapchain_ok,'invalid_external_handle_errors':swapchain_fail,
        'intro_complete':intro_end is not None, 'intro_fps_median':rnd(statistics.median(phase_fps('intro'))) if phase_fps('intro') else None,
        'post_intro_fps_samples':len(play), 'post_intro_median_fps':rnd(play_median), 'post_intro_p10_fps':rnd(play_p10),
        'peak_graphics_allocation_mib':max([x['total_mib'] for x in mem],default=None),
        'peak_image_allocation_mib':max([x['images_mib'] for x in mem],default=None),
        'minimum_mem_available_mib':min(available,default=None),
        'peak_memory_maps':max([x[0] for x in maps],default=None),
        'largest_image':max(huge,key=lambda x:x['mib'],default=None),
        'longest_pipeline_compile_ms':rnd(max(compiles)) if compiles else None,
        'audio_callback_windows': len(audio_samples),
        'audio_underflow_events': sum(x['underruns'] for x in audio_samples) if audio_samples else None,
        'audio_zero_padded_ms': rnd(sum(x['silence_ms'] for x in audio_samples)) if audio_samples else None,
        'aaudio_stream': aaudio_open[-1] if aaudio_open else None,
        'median_vk_queue_submit_cpu_ms_per_frame': rnd(statistics.median(pace_submit_ms)) if pace_submit_ms else None,
        'median_gpu_busy_p50_ms': rnd(statistics.median(pace_gpu_ms)) if pace_gpu_ms else None,
        'worst_longframe': max(longframes,key=lambda x:x['whole_ms'],default=None),
        'logged_busy_av1_input_notices': codec_ahead,
        'max_onscreen_footprint_mib': max((x['footprint_mib'] for x in onscreen),default=None),
        'presented_frames_from_window_stats':n_seen,
        'dropped_frames_from_window_stats':n_drop,
        'observed_drop_ratio':rnd(n_drop/(n_seen+n_drop)) if n_seen+n_drop else None,
        'highest_window_p99_ms':max([x['p99_ms'] for x in onscreen],default=None),
        'post_intro_window_p99_ms':post_p99,'post_intro_dropped_ratio':rnd(post_ratio),
        'median_simulation_time_ratio':rnd(statistics.median(time_ratios)) if time_ratios else None,
        'digest_oom_classification':digest_oom,
        'flags':flags,'target_met_on_observed_gameplay':passed,
        'caveat':'A log cannot prove absence of visual corruption, audio sync, or Android LMKD without device traces. No extrapolation from intro to gameplay.'
    }

def markdown(m:dict) -> str:
    def v(k): return str(m.get(k)) if m.get(k) is not None else 'not measured'
    rows=[('Driver',v('driver')),('Successful swapchains',v('swapchain_successes')),('Invalid external handle errors',v('invalid_external_handle_errors')),('Intro complete',v('intro_complete')),('Intro median FPS',v('intro_fps_median')),('Gameplay FPS observations',v('post_intro_fps_samples')),('Gameplay median FPS',v('post_intro_median_fps')),('Gameplay p10 FPS',v('post_intro_p10_fps')),('Peak Vulkan tracked allocations MiB',v('peak_graphics_allocation_mib')),('Minimum MemAvailable MiB',v('minimum_mem_available_mib')),('Longest pipeline compile ms',v('longest_pipeline_compile_ms')),('Audio callback underruns',v('audio_underflow_events')),('Inserted silence, ms',v('audio_zero_padded_ms')),('Median vkQueueSubmit CPU ms / frame',v('median_vk_queue_submit_cpu_ms_per_frame')),('GPU median busy p50 ms',v('median_gpu_busy_p50_ms')),('Worst longframe',v('worst_longframe')),('Observed dropped-frame ratio',v('observed_drop_ratio')),('Target met',v('target_met_on_observed_gameplay'))]
    return '# SM-X930 / Mali-G925 benchmark\n\n| Metric | Value |\n|---|---|\n'+'\n'.join('| '+a.replace('|','/')+' | '+b.replace('|','/')+' |' for a,b in rows)+'\n\n**Flags:** '+', '.join(m['flags'])+'\n\n'+m['caveat']+'\n'

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('log',type=Path)
    ap.add_argument('--digest',type=Path)
    ap.add_argument('--json',type=Path)
    ap.add_argument('--md',type=Path)
    a=ap.parse_args()
    r=parse(a.log.read_text(encoding='utf-8',errors='replace'),a.digest.read_text(encoding='utf-8',errors='replace') if a.digest else '')
    if a.json: a.json.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    if a.md: a.md.write_text(markdown(r))
    print(json.dumps(r,indent=2,ensure_ascii=False))
