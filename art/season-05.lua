-- season-05.png: May decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- Beds of tulips, daisies and forget-me-nots sway at the foot of each pillar, and a pink
-- butterfly and a blue one flutter in the two top corners.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-05.lua
-- Writes art/season-05.aseprite and docs/art/season-05.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  grass = "#5f9e48", grassLight = "#8cc860", grassDark = "#3e7034",
  stem = "#6aa84f", leaf = "#4f8a3c", leafLight = "#8cc860",
  daisy = P.ink, daisyShade = "#d9cbe6", centre = P.gold, centreShade = P.goldDark,
  red = "#ee4a4a", redLight = "#ff8f80", redDark = "#b02a3a",
  yellow = "#ffd34a", yellowLight = "#fff3a6", yellowDark = "#d9952a",
  pink = "#ff8ccb", pinkLight = "#ffd2ea", pinkDark = "#d1559a",
  blue = "#7cc8ff", blueLight = "#d2efff", blueDark = "#3f86c9",
  lilac = "#b89cff", lilacLight = "#e2d6ff", lilacDark = "#7a5fcf",
  orange = "#ffad4a", orangeDark = "#d9752a", spot = P.ink, body = "#5b4378",
}

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- A round flower head of radius r with n petals (the gaps between them become notches once
-- outlined) round a centre of radius rc. Lit from the upper left. col = {main, light, dark}.
local function bloom(r, n, col, rc, eye)
  local size = math.ceil(2 * r)
  local b = L.buffer(size, size)
  local c = size / 2
  for y = 0, size - 1 do
    for x = 0, size - 1 do
      local dx, dy = x + 0.5 - c, y + 0.5 - c
      local d = math.sqrt(dx * dx + dy * dy)
      local edge = r * (0.64 + 0.36 * math.abs(math.cos(n / 2 * (math.atan(dy, dx) + math.pi / 2))))
      if d <= rc then
        b[y][x] = (dx + dy <= 0) and (eye or C.centre) or C.centreShade
      elseif d <= edge then
        local s = dx + dy
        b[y][x] = (s < -r * 0.6) and col[2] or (s > r * 0.55) and col[3] or col[1]
      end
    end
  end
  return b
end

local TULIP = { "a.bb.c", "aabbcc", "aabbbc", "abbbbc", "abbbcc", ".bbcc.", "..bc.." }
-- forget-me-nots: three tiny flowers on short stalks off the top of one stem
local SPRIG = { "....a....", "...aob...", "....c....", ".a..g..a.", "aob.g.aob", ".c..g..c.",
  "..g.g.g..", "...ggg..." }

local function head(fl)
  local c = fl.c
  if fl.kind == "tulip" then return L.map(TULIP, { a = c[2], b = c[1], c = c[3] }) end
  if fl.kind == "sprig" then return L.map(SPRIG, { a = c[2], b = c[1], c = c[3], o = C.centre, g = C.stem }) end
  if fl.kind == "daisy" then return bloom(3.6, 6, c, 1.2, fl.eye) end
  return bloom(2.6, 5, c, 0.8, fl.eye)            -- "small"
end

-- One flower: a stem from the ground at (x, 95) up to a head that sways sideways by dx, with
-- a leaf partway up. Returns a buffer and where it goes, so each flower gets its own outline.
local function flower(fl, dx)
  local hd = head(fl)
  local top = 95 - fl.h
  local hx = fl.x + dx - (hd.w // 2)
  local x0, y0 = math.min(fl.x, hx) - 4, top
  local b = L.buffer(hd.w + 9, 96 - top)
  local function put(px, py, c) L.set(b, px - x0, py - y0, c) end
  -- stem: rooted at the bottom, leaning further towards the head the higher it goes
  local bend = top + hd.h - 1
  for y = bend, 95 do
    local t = (y - bend) / math.max(1, 95 - bend)
    put(fl.x + math.floor(dx * (1 - t) * (1 - t) + 0.5), y, C.stem)
  end
  if fl.leaf then
    local s, ly = fl.leaf, 95 - math.floor(fl.h * 0.4)
    local lx = fl.x + math.floor(dx * 0.3 + 0.5)
    put(lx + s, ly, C.leaf); put(lx + 2 * s, ly, C.leaf); put(lx + 2 * s, ly - 1, C.leafLight)
    put(lx + 3 * s, ly - 1, C.leaf); put(lx + 3 * s, ly - 2, C.leafLight)
  end
  L.blit(b, hd, hx - x0, top - y0)
  return b, x0, y0
end

-- A low mound of leafy bumps along the ground, with a few blades poking up. Each bump is
-- {centre x, half width, height, {{blade dx, length, lean}, ...}}.
local function mound(x0, x1, bumps)
  local w = x1 - x0 + 1
  local b = L.buffer(w, 9)
  local top = {}
  for x = 0, w - 1 do
    local best, bump = 99, nil
    for _, m in ipairs(bumps) do
      local dx = x + 0.5 - (m[1] - x0)
      if math.abs(dx) <= m[2] then
        local y = 9 - m[3] * math.sqrt(1 - (dx / m[2]) ^ 2)
        if y < best then best, bump = y, { dx / m[2] } end
      end
    end
    if bump then
      top[x] = math.floor(best + 0.5)
      for y = top[x], 8 do
        local c = C.grass
        if bump[1] > 0.5 or y >= 8 then c = C.grassDark
        elseif y <= top[x] + 1 and bump[1] < 0 then c = C.grassLight end
        b[y][x] = c
      end
    end
  end
  for _, m in ipairs(bumps) do
    for _, bl in ipairs(m[4] or {}) do
      local x = m[1] - x0 + bl[1]
      if top[x] then
        for k = 1, bl[2] do L.set(b, x + ((k == bl[2]) and (bl[3] or 0) or 0), top[x] - k, C.grass) end
      end
    end
  end
  return b
end

local BEDS = {
  { x0 = 20, x1 = 50,
    bumps = { { 24, 4, 4, { { -1, 2, -1 } } }, { 29, 4, 3 }, { 34, 4, 5, { { 2, 3, 1 } } }, { 40, 3, 3 },
      { 45, 5, 4, { { 1, 2, 1 } } } },
    flowers = {
      { x = 23, h = 14, kind = "daisy", c = { C.daisy, C.daisy, C.daisyShade }, leaf = -1 },
      { x = 29, h = 19, kind = "tulip", c = { C.red, C.redLight, C.redDark }, leaf = 1 },
      { x = 35, h = 12, kind = "sprig", c = { C.blue, C.blueLight, C.blueDark } },
      { x = 41, h = 16, kind = "tulip", c = { C.yellow, C.yellowLight, C.yellowDark }, leaf = -1 },
      { x = 47, h = 10, kind = "small", c = { C.lilac, C.lilacLight, C.lilacDark } },
    } },
  { x0 = 125, x1 = 155,
    bumps = { { 130, 5, 4, { { -1, 2, -1 } } }, { 135, 3, 3 }, { 141, 4, 5, { { -2, 3, -1 } } },
      { 147, 4, 3 }, { 151, 4, 4, { { 1, 2, 1 } } } },
    flowers = {
      { x = 128, h = 10, kind = "small", c = { C.pink, C.pinkLight, C.pinkDark } },
      { x = 134, h = 16, kind = "tulip", c = { C.pink, C.pinkLight, C.pinkDark }, leaf = 1 },
      { x = 140, h = 12, kind = "sprig", c = { C.blue, C.blueLight, C.blueDark } },
      { x = 146, h = 19, kind = "daisy", c = { C.daisy, C.daisy, C.daisyShade }, leaf = -1 },
      { x = 152, h = 12, kind = "tulip", c = { C.red, C.redLight, C.redDark }, leaf = 1 },
    } },
}

-- Butterfly: wings open, half-open and closed. u/h/d are the upper wing and its highlight and
-- shade, l/m the lower wing and its shade, s the spots, k the body, a the antennae.
local WINGS = {
  { ".....a...a.....", "......a.a......", ".hhh...k...hhh.", "hhhuu..k..huuud", "hhuuuuukhuuuuud",
    "hussuuukuuussud", ".uuuuuukuuuuud.", "..uuuuukuuuud..", "...llllklllm...", "..lslllklllsm..",
    "..lll.....lmm.." },
  { ".....a...a.....", "......a.a......", "....hh.k.hh....", "....hhukhuud...", "....hsukusd....",
    "....uuukuud....", ".....uukud.....", ".....llklm.....", "....lllkllm....", "....ll...lm....",
    "..............." },
  { ".....a...a.....", "......a.a......", "......hkd......", "......hkd......", "......ukd......",
    "......ukd......", "......ukd......", "......lkm......", "......lkm......", "...............",
    "..............." },
}
-- the pink one flaps quickly; the blue one holds its wings open a little longer
local FLAP = { pink = { 1, 2, 3, 2 }, blue = { 1, 1, 2, 3, 3, 2, 1, 1 } }
local function wings(f, kind) local seq = FLAP[kind]; return seq[f % #seq + 1] end
local function butterfly(f, kind, col)
  return L.map(WINGS[wings(f, kind)], { u = col.u, h = col.h, d = col.d, l = col.l, m = col.m,
    s = C.spot, k = C.body, a = col.h })
end

local PINK_BF = { u = C.pink, h = C.pinkLight, d = C.pinkDark, l = C.orange, m = C.orangeDark }
local BLUE_BF = { u = C.blue, h = C.blueLight, d = C.blueDark, l = C.lilac, m = C.lilacDark }

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- top corners: a butterfly in each, looping a small figure of eight and lifting on the
  -- downstroke
  local a = TAU * f / FRAMES
  L.stamp(b, butterfly(f, "pink", PINK_BF), 15 + math.floor(4 * math.sin(a) + 0.5),
    6 + math.floor(2 * math.sin(2 * a) + 0.5) + (wings(f, "pink") == 1 and 0 or 1))
  L.stamp(b, butterfly(f, "blue", BLUE_BF), 145 + math.floor(3.5 * math.sin(a + math.pi) + 0.5),
    8 + math.floor(2 * math.sin(2 * a + 2) + 0.5) + (wings(f, "blue") == 1 and 0 or 1))
  -- the foot of each pillar: flowers sway on their own phases, then the leafy mound hides
  -- their roots
  for i, bed in ipairs(BEDS) do
    for j, fl in ipairs(bed.flowers) do
      local fb, fx, fy = flower(fl, wave(f, fl.h > 12 and 1.3 or 1, j * 1.9 + i * 0.7))
      L.stamp(b, fb, fx, fy)
    end
    L.stamp(b, mound(bed.x0, bed.x1, bed.bumps), bed.x0, 87)
  end
  frames[f + 1] = b
end
L.saveStrip(frames, "season-05", MS)
