-- season-02.png: February decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- A red heart and a pink heart beat softly in the top corners while little hearts float up
-- around them, and heart balloons on strings sway at the foot of each pillar.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-02.lua
-- Writes art/season-02.aseprite and docs/art/season-02.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  red = "#e8364f", redLight = "#ff6f80", redDark = "#a3203e",
  pink = "#ff8cc0", pinkLight = "#ffc2dc", pinkDark = "#d4589a",
  rose = "#ff5f8f", roseLight = "#ff9bb5", roseDark = "#c23a6a",
  shine = "#fff4f6", string = "#ecd3de",
}
local TONE = {
  red = { b = C.red, l = C.redLight, d = C.redDark, w = C.shine },
  pink = { b = C.pink, l = C.pinkLight, d = C.pinkDark, w = C.shine },
  rose = { b = C.rose, l = C.roseLight, d = C.roseDark, w = C.shine },
}

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- Hearts at six sizes, lit from the upper left: l light, w shine, b body, d shade.
local HEART = {
  [3] = { "b.b", "bbd", ".d." },
  [5] = { "lb.bb", "bbbbd", ".bbd.", "..d.." },
  [7] = { ".lb.bb.", "lwbbbbd", "bbbbbbd", ".bbbbd.", "..bbd..", "...d..." },
  [9] = { ".ll..bb..", "lwwlbbbbd", "lwlbbbbbd", "bbbbbbbbd", ".bbbbbbd.", "..bbbbd..", "...bbd...", "....d...." },
  [11] = { ".lll...bbb.", "lwwll.bbbbd", "lwllbbbbbbd", "llbbbbbbbbd", "lbbbbbbbbbd", ".bbbbbbbbd.",
    "..bbbbbbd..", "...bbbbd...", "....bbd....", ".....d....." },
  [13] = { "..lll...bbb..", ".lwwll.bbbbb.", "lwwllbbbbbbbd", "lwllbbbbbbbbd", "llbbbbbbbbbbd",
    "lbbbbbbbbbbbd", ".bbbbbbbbbbd.", "..bbbbbbbbd..", "...bbbbbbd...", "....bbbbd....",
    ".....bbd.....", "......d......" },
}
local function heart(size, tone) return L.map(HEART[size], TONE[tone]) end

-- A heart balloon: a glossy heart with a little knot under its tip.
local function balloon(size, tone)
  local h = heart(size, tone)
  local b = L.buffer(h.w, h.h + 2)
  L.blit(b, h, 0, 0)
  local mx = (h.w - 1) // 2
  L.set(b, mx, h.h, TONE[tone].d)
  L.set(b, mx - 1, h.h + 1, TONE[tone].d); L.set(b, mx, h.h + 1, TONE[tone].d); L.set(b, mx + 1, h.h + 1, TONE[tone].d)
  return b
end

-- The big heart beats twice a loop: two frames full size, then six a size smaller.
-- (x, y) is the top-left of the full-size heart; the small one keeps the same centre.
local function beatingHeart(b, f, x, y, tone, lag)
  local big = (f + lag) % 8 < 2
  if big then L.stamp(b, heart(13, tone), x, y) else L.stamp(b, heart(11, tone), x + 1, y + 1) end
end

-- A little heart rising 1 px a frame from yBottom for one loop, swaying. It pops in small at
-- the bottom and shrinks away at the top, so the wrap back to the start is invisible.
local function riser(b, f, size, tone, x, yBottom, phase)
  local k = (f + phase) % FRAMES
  local s = size
  if k == 0 or k == 14 then s = 3 elseif k == 1 or k == 13 then s = math.min(size, 5) end
  if k == 15 then return end
  local off = (size - s) // 2
  local sway = math.floor(1.2 * math.sin(TAU * k / 10 + phase) + 0.5)
  L.stamp(b, heart(s, tone), x + sway + off, yBottom - k + off)
end

-- A string from a balloon's knot down to where it is tied, bowing a little to one side.
local function tether(b, x0, y0, x1, y1, bow)
  local px, py = x0, y0
  for i = 1, 8 do
    local t = i / 8
    local x = x0 + (x1 - x0) * t + bow * 4 * t * (1 - t)
    local y = y0 + (y1 - y0) * t
    L.line(b, px, py, x, y, C.string)
    px, py = x, y
  end
end

-- A small bow where the strings are tied: two loops and a knot.
local function bow(tone)
  return L.map({ "bb.bb", "blkbl", ".b.b." }, { b = TONE[tone].b, l = TONE[tone].l, k = TONE[tone].d })
end

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- top left: a red heart beating, little pink hearts floating up around it
  riser(b, f, 5, "pink", 3, 38, 6)
  riser(b, f, 7, "pink", 31, 21, 5)
  riser(b, f, 5, "rose", 41, 16, 11)
  beatingHeart(b, f, 13, 6 + wave(f, 1), "red", 0)
  -- top right: a pink heart beating half a beat later, little red hearts floating up
  riser(b, f, 7, "rose", 137, 20, 2)
  riser(b, f, 5, "red", 129, 14, 10)
  riser(b, f, 5, "red", 168, 38, 13)
  beatingHeart(b, f, 149, 7 + wave(f, 1, math.pi), "pink", 4)

  -- the foot of the left pillar: two balloons tied to a bow
  local tieL = { 22, 91 }
  local ax, ay = 22 + wave(f, 1, 0.5), 66 + wave(f, 1, 2)
  local bx, by = 33 + wave(f, 1, 2.5), 72 + wave(f, 1, 4)
  tether(b, ax + 5, ay + 12, tieL[1], tieL[2], -1)
  tether(b, bx + 4, by + 10, tieL[1] + 1, tieL[2], 1)
  L.stamp(b, balloon(11, "red"), ax, ay)
  L.stamp(b, balloon(9, "pink"), bx, by)
  L.stamp(b, bow("red"), tieL[1] - 2, tieL[2])
  -- the foot of the right pillar: one balloon
  local tieR = { 153, 91 }
  local cx, cy = 141 + wave(f, 1, 3.5), 69 + wave(f, 1, 5)
  tether(b, cx + 5, cy + 12, tieR[1], tieR[2], 1)
  L.stamp(b, balloon(11, "rose"), cx, cy)
  L.stamp(b, bow("pink"), tieR[1] - 2, tieR[2])
  frames[f + 1] = b
end
L.saveStrip(frames, "season-02", MS)
