-- season-07.png: July decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- Fireworks go off in both top corners, four of them taking turns so one is always blooming:
-- a rocket climbs on a sparkly trail, bursts, and its stars droop and twinkle out. At the foot
-- of each pillar a little flag ripples beside a pail of crackling sparklers.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-07.lua
-- Writes art/season-07.aseprite and docs/art/season-07.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  -- firework colours as {light, main, dark}
  rose = { "#ffd6e2", "#ff5a7e", "#b8385a" },
  gold = { P.goldLight, P.gold, P.goldDark },
  aqua = { "#d8fdff", "#5fe3ea", "#2f97a6" },
  sky = { "#f4f8ff", "#9fd2ff", "#5a86d6" },
  flash = "#ffffff",
  red = "#e8404a", redDark = "#b02a3a", white = P.ink, whiteShade = "#d9cbe6",
  blue = "#3f5fc9", blueDark = "#2f4596", pole = P.goldDark, knob = P.gold,
  pail = "#4f7fe0", pailDark = "#3550a8", rim = P.steelLight, stripe = P.ink,
  wire = P.silver, wireShade = P.steelDark,
}

local function px(v) return math.floor(v + 0.5) end

-- A small deterministic hash so the crackle is random-looking but the same every run.
local function rnd(a, b, c) return (math.sin(a * 12.9898 + b * 78.233 + c * 37.719) * 43758.5453) % 1 end

-- Fireworks. Each has a centre, a radius, colours, a spoke count, the frame its rocket leaves
-- at and how far below the centre the rocket starts. Over its 16 frames the rocket climbs
-- (ages 0-2), the burst opens fast, slows, droops and twinkles out (ages 3-12), then the sky
-- rests (ages 13-15). In each corner the small one opens as the big one fades, and frame 1
-- catches both big ones in bloom.
local SHOWS = {
  { x = 17, y = 13, r = 11, col = C.rose, inner = C.gold, n = 12, start = 9, rot = 0, lift = 14 },
  { x = 40, y = 8, r = 7.5, col = C.aqua, n = 10, start = 1, rot = 0.3, lift = 10 },
  { x = 157, y = 12, r = 11, col = C.gold, inner = C.aqua, n = 12, start = 11, rot = 0.26, lift = 14 },
  { x = 135, y = 8, r = 7.5, col = C.sky, n = 10, start = 3, rot = 0, lift = 10 },
}

-- the rocket: a bright spark with a wobbly trail of embers below it, climbing to just under
-- the centre (kept short for the small ones so the trail stays off the arch)
local function rocket(b, s, age)
  local y = s.y + s.lift - age * (s.lift - 4) // 2
  L.set(b, s.x, y, C.flash)
  L.set(b, s.x, y + 1, s.col[1]); L.set(b, s.x, y + 2, s.col[2])
  L.set(b, s.x + ((age % 2 == 0) and 1 or -1), y + 4, s.col[3])
  L.set(b, s.x, y + 6, s.col[3])
end

-- One ring of stars along n spokes. Heads are bright and trail darker pixels back towards the
-- centre; as the burst ages the trails shorten, the stars droop and leave falling glitter, the
-- colours cool and the stars blink out one by one.
local function ring(b, s, n, rad, t, col, rot, big)
  local droop = 0.09 * math.max(0, t - 2) ^ 2
  for k = 0, n - 1 do
    local a = rot + TAU * k / n
    local ca, sa = math.cos(a), math.sin(a)
    local on = t < 6 or (k + t) % 2 == 0
    if t >= 8 then on = (k + t) % 3 == 0 end
    if on then
      local hx, hy = px(s.x + rad * ca), px(s.y + rad * sa + droop)
      local trail = (t <= 2) and 3 or (t <= 5) and 2 or 1
      for i = trail, 1, -1 do
        local r = rad - i * 1.2
        if r > 1 then
          L.set(b, px(s.x + r * ca), px(s.y + r * sa + droop * r / rad), (i == 1 and t <= 5) and col[2] or col[3])
        end
      end
      if t >= 6 then L.set(b, hx, hy - 2, col[3]) end            -- glitter falling behind
      local head = (t <= 5) and col[1] or (t <= 7) and col[2] or col[3]
      if big and t >= 2 and t <= 4 then
        for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }) do L.set(b, hx + d[1], hy + d[2], col[2]) end
      end
      L.set(b, hx, hy, head)
    end
  end
end

local function firework(b, s, f)
  local age = (f - s.start) % FRAMES
  if age <= 2 then return rocket(b, s, age) end
  local t = age - 3                                     -- frames since the bang
  if t > 9 then return end
  if t == 0 then
    -- the bang: a bright little star
    L.set(b, s.x, s.y, C.flash)
    for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }) do L.set(b, s.x + d[1], s.y + d[2], s.col[1]) end
    for _, d in ipairs({ { 2, 0 }, { -2, 0 }, { 0, 2 }, { 0, -2 }, { 1, 1 }, { -1, 1 }, { 1, -1 }, { -1, -1 } }) do
      L.set(b, s.x + d[1], s.y + d[2], s.col[2])
    end
    return
  end
  local grow = 1 - (1 - math.min(t, 4) / 4) ^ 2
  local rad = s.r * (0.3 + 0.7 * grow) + 0.15 * math.max(0, t - 4)
  if s.inner and t <= 6 then ring(b, s, s.n // 2, rad * 0.5, t + 1, s.inner, s.rot + TAU / s.n, false) end
  ring(b, s, s.n, rad, t, s.col, s.rot, s.inner ~= nil)
  if t <= 2 then L.set(b, s.x, s.y, s.col[1]) end
end

-- Flag: stripes and a starry blue corner, rippling in a breeze that runs away from the pole.
local FLAG = { "bsbsbrrrrrr", "bbsbbwwwwww", "bsbsbrrrrrr", "bbbbbwwwwww", "rrrrrrrrrrr",
  "wwwwwwwwwww", "rrrrrrrrrrr" }
local SHADE = { [C.red] = C.redDark, [C.white] = C.whiteShade, [C.blue] = C.blueDark }
local function flag(f)
  local base = L.map(FLAG, { r = C.red, w = C.white, b = C.blue, s = C.white })
  local b = L.buffer(base.w + 2, base.h + 2)
  for x = 0, base.w - 1 do
    local ph = TAU * (x / 8 - f / FRAMES)
    local dy = px(0.9 * math.sin(ph) * math.min(1, x / 3)) + 1
    local dark = x >= 2 and math.cos(ph) > 0.45
    for y = 0, base.h - 1 do
      local c = base[y][x]
      if c and dark and not (c == C.white and FLAG[y + 1]:sub(x + 1, x + 1) == "s") then c = SHADE[c] or c end
      L.set(b, x, y + dy, c)
    end
  end
  return b
end

-- A flag on its pole at pole x px0, standing on the ground.
local function flagpole(dst, x0, f)
  local top = 72
  local b = L.buffer(15, 96 - top)
  L.line(b, 1, 2, 1, 95 - top, C.pole)
  L.set(b, 1, 0, C.knob); L.set(b, 0, 1, C.knob); L.set(b, 1, 1, C.knob); L.set(b, 2, 1, P.goldDark)
  L.set(b, 0, 0, P.goldLight)
  L.blit(b, flag(f), 2, 2)
  L.stamp(dst, b, x0 - 1, top)
end

-- Pail: a little blue bucket with a white star on it, holding two sparklers.
local PAIL = { "aaaaaaaaa", "bbbbwbbbd", "bbwwwwwbd", ".bbwwwbd.", ".bbwbwbd.", ".bbbbbbd.", "..bbbbd.." }
local function pail() return L.map(PAIL, { a = C.rim, b = C.pail, d = C.pailDark, w = C.stripe }) end

-- A sparkler's burning tip at (x, y): a white-hot core, eight rays of sparks whose lengths
-- change every frame, and a few loose sparks further out. Tiny particles, so no outline.
local function crackle(b, x, y, f, seed)
  local rot = rnd(f, seed, 3) * TAU / 8
  for k = 0, 7 do
    local a = rot + TAU * k / 8
    local len = 1 + math.floor(rnd(k, f, seed) * 3.99)
    for r = 1, len do
      L.set(b, px(x + r * math.cos(a)), px(y + r * math.sin(a)), (r == 1) and P.goldLight or P.gold)
    end
  end
  for k = 0, 3 do
    local a, r = rnd(f, k, seed + 2) * TAU, 4.5 + rnd(k, seed, f + 1) * 2
    L.set(b, px(x + r * math.cos(a)), px(y + r * math.sin(a)), (k % 2 == 0) and P.goldLight or P.bulb)
  end
  L.set(b, x, y, C.flash)
end

-- A pail at x0 standing on the ground, with two sparklers leaning out of it.
local function sparklers(dst, x0, f, seed)
  -- the wires are as thin as the spider's thread in October, so like it they go unoutlined
  local tips = { { 3, x0 + 2, 77 }, { 5, x0 + 7, 80 } }      -- {foot dx, tip x, tip y}
  for _, t in ipairs(tips) do
    L.line(dst, x0 + t[1], 90, t[2], t[3], C.wire)
    L.line(dst, x0 + t[1] + 1, 90, t[2] + 1, t[3] + 1, C.wireShade)
  end
  L.stamp(dst, pail(), x0, 89)
  for i, t in ipairs(tips) do crackle(dst, t[2], t[3], f, seed + i) end
end

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- the top corners: fireworks taking turns
  for _, s in ipairs(SHOWS) do firework(b, s, f) end
  -- the foot of each pillar: a flag and a pail of sparklers
  flagpole(b, 20, f)
  sparklers(b, 36, f, 1)
  sparklers(b, 129, f, 7)
  flagpole(b, 144, (f + 5) % FRAMES)
  frames[f + 1] = b
end
L.saveStrip(frames, "season-07", MS)
