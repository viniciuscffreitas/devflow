# HTML5 Video Autoplay Debug & Fix

## Trigger

Use when:
- `<video autoPlay muted playsInline>` renders as all-black or doesn't play in production
- Video loads (`readyState: 4`, `networkState: 1`) but stays `paused: true`
- Works locally but breaks on server/deploy

## Diagnose First

Run in browser console:

```js
const v = document.querySelector('video');
console.log({
  readyState: v.readyState,   // 4 = loaded, 0 = not loaded
  paused: v.paused,           // true = not playing despite autoplay
  muted: v.muted,
  autoplay: v.autoplay,
  error: v.error,
  src: v.currentSrc,
});
```

If `readyState: 4` + `paused: true` → the video IS loaded but autoplay was blocked. Three likely causes below.

## Root Causes & Fixes

### 1. Wrong pixel format (`yuvj420p`)

Screen capture tools (ffmpeg, Playwright CDP) output `yuvj420p` (full-range YUV). Browsers require `yuv420p` (limited-range). Full-range causes silent autoplay failure on some browsers.

**Fix:**
```bash
ffmpeg -i input.mp4 -pix_fmt yuv420p -movflags +faststart output.mp4
```

Check current format:
```bash
ffprobe -v quiet -show_streams input.mp4 | grep pix_fmt
# bad:  pix_fmt=yuvj420p
# good: pix_fmt=yuv420p
```

### 2. Missing `faststart` (moov atom at end)

Without `-movflags +faststart`, the MP4 moov atom is at the end of the file. The browser must download the full file before it can start playing — this blocks autoplay on slow connections or large files.

**Fix:** Always add `-movflags +faststart` when encoding MP4 for web:
```bash
ffmpeg -i input.mp4 -pix_fmt yuv420p -movflags +faststart -crf 23 output.mp4
```

### 3. `autoPlay` React prop isn't enough

React's `autoPlay` attribute alone doesn't guarantee playback. Safari iOS and some Chromium versions require an explicit `.play()` call.

**Fix in React:**
```tsx
"use client";
import { useRef, useEffect } from "react";

function VideoComponent({ src }: { src: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    videoRef.current?.play().catch(() => {});
    // .catch() silences "NotAllowedError" if autoplay is blocked by browser policy
  }, []);

  return (
    <video
      ref={videoRef}
      autoPlay
      loop
      muted
      playsInline
      style={{ width: "100%", height: "100%" }}
    >
      <source src={src.replace(/\.[^.]+$/, ".webm")} type="video/webm" />
      <source src={src.replace(/\.[^.]+$/, ".mp4")} type="video/mp4" />
    </video>
  );
}
```

**Note:** `muted` is REQUIRED for autoplay to work in all browsers. Without `muted`, browsers block autoplay unless the user has interacted with the page.

## Complete Re-encode Recipe

When a screen-captured video doesn't autoplay:

```bash
# Fix everything at once: trim fade-in, fix pix_fmt, add faststart
ffmpeg -y -ss 0.4 -i input.mp4 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -c:v libx264 -crf 23 -preset medium \
  output.mp4

# Re-encode WebM as well (VP9, better compression)
ffmpeg -y -i output.mp4 \
  -c:v libvpx-vp9 -crf 35 -b:v 0 -row-mt 1 \
  output.webm
```

**Always provide both WebM and MP4** — WebM first in `<source>` order (smaller, better quality).

## Black First Frame

If the video was captured with a fade-in from black, the paused poster frame will appear all-black. Fix:
- Trim the fade-in: `-ss 0.4` (skip first 0.4s)
- Or add `poster="/path/to/first-frame.jpg"` attribute

## Checklist

- [ ] `pix_fmt=yuv420p` (not `yuvj420p`)
- [ ] `-movflags +faststart` applied
- [ ] `muted` attribute on `<video>`
- [ ] `playsInline` attribute (required for iOS)
- [ ] `loop` attribute if looping
- [ ] Explicit `.play()` via `useEffect` in React
- [ ] Both WebM + MP4 sources provided
- [ ] First frame is not black (or `poster` attribute set)
