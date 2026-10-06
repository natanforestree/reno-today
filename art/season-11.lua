-- season-11.png: November decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- Fall leaves drift down through both top corners and slip behind the arch, a turkey with a
-- fanned tail bobs its head and gobbles at the foot of the left pillar, and a hay bale with a
-- pumpkin pie and a gourd on top sits at the foot of the right one.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-11.lua
-- Writes art/season-11.aseprite and docs/art/season-11.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  body = "#8b5a3c", bodyLight = "#b47a4f", bodyDark = "#5f3b2a",
  head = "#d9a77a", headShade = "#b98559", snood = P.red, blush = "#ff9ab5",
  tip = P.goldLight, tipShade = "#ecd598", orange = "#e2681c", orangeLight = "#f79a45",
  red = P.red, redLight = P.redLight, fanBrown = "#a8693f", fanBrownDark = "#7c4a2e",
  beak = P.gold, beakDark = P.goldDark, leg = "#f79a45",
  hay = "#e8b84a", hayLight = "#f7d982", hayDark = "#b9862e", twine = "#8b5a3c",
  crust = "#e8b05e", crustDark = "#b37a38", filling = "#d9772c", fillingDark = "#b35a22",
  gold = "#f2b632", goldLight = "#ffe08a",
  gourd = "#6b8f3a", gourdLight = "#a9c46a", gourdDark = "#4a6328", cream = "#f3e6b8",
  stem = "#7c5a34",
  leafOrange = { "#f79a45", "#e2681c", "#a8461a" },
  leafRed = { "#ec5562", "#d42a3a", "#8f1b2b" },
  leafGold = { "#ffe08a", "#f2b632", "#c7902e" },
}

-- The arch's outer edge (art/arch.lua): an ellipse centred on (87.5, 58), rx 80, ry 40, plus its
-- 1px outline. Leaves only show in the sky above it, so they look as if they fall behind the arch.
local function inSky(x, y)
  local dx, dy = (x + 0.5 - 87.5) / 81.5, (y + 0.5 - 58) / 41.5
  return y < 48 and dx * dx + dy * dy > 1
end

-- Turkey, seen from the front: a fan of seven rounded feathers (red, orange and gold, each with a
-- pale tip and a brown root), a round brown body and a small head. bob dips the head, sway leans
-- it, and gobble opens the beak and swings the snood.
local FEATHERS = {
  { C.red, C.redLight }, { C.orange, C.orangeLight }, { C.gold, C.goldLight }, { C.orange, C.orangeLight },
  { C.gold, C.goldLight }, { C.orange, C.orangeLight }, { C.red, C.redLight },
}
local function turkey(bob, sway, gobble)
  local w, h = 25, 22
  local b = L.buffer(w, h)
  local cx, cy = 12.5, 12.5
  local n, lo, hi = #FEATHERS, -0.25, math.pi + 0.25
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      local dx, dy = x + 0.5 - cx, cy - (y + 0.5)
      local a, r = math.atan(dy, dx), math.sqrt(dx * dx + dy * dy)
      if a < -math.pi / 2 then a = a + TAU end
      if a >= lo and a <= hi then
        local t = (hi - a) / (hi - lo) * n            -- feather 1 on the left
        local i, u = math.floor(t), t - math.floor(t)
        local rout = 12.4 - 3.2 * (2 * u - 1) ^ 2
        if r <= rout and i < n then
          local fc = FEATHERS[i + 1]
          local c = fc[1]
          if r > rout - 1.3 then c = (u < 0.6) and C.tip or C.tipShade
          elseif r < 6.5 then c = C.fanBrown
          elseif u < 0.35 then c = fc[2] end
          if r < 6.5 and u > 0.75 then c = C.fanBrownDark end
          b[y][x] = c
        end
      end
    end
  end
  -- body, with its own outline so it stands out from the fan
  local body = L.buffer(11, 10)
  L.eachDisc(5.5, 5.2, 5.2, function(x, y, dx, dy)
    local c = C.body
    if dx + dy < -4 then c = C.bodyLight elseif dx > 2.5 or dy > 3.5 then c = C.bodyDark end
    L.set(body, x, y, c)
  end)
  L.stamp(b, body, 7, 10)
  -- legs and feet
  for _, lx in ipairs({ 10, 14 }) do
    L.set(b, lx, 20, C.leg); L.set(b, lx, 21, C.leg); L.set(b, lx - 1, 21, C.leg); L.set(b, lx + 1, 21, C.leg)
  end
  -- head
  local head = L.buffer(7, 7)
  L.eachDisc(3.5, 3.5, 3.4, function(x, y, dx, dy)
    L.set(head, x, y, (dx > 1.8 or dy > 2) and C.headShade or C.head)
  end)
  L.set(head, 2, 3, P.outline); L.set(head, 5, 3, P.outline)          -- eyes
  L.set(head, 1, 4, C.blush); L.set(head, 6, 4, C.blush)
  L.set(head, 3, 4, C.beak); L.set(head, 4, 4, C.beak)                -- beak
  L.set(head, 3, 5, gobble and P.outline or C.beakDark); L.set(head, 4, 5, C.beakDark)
  local hx, hy = 9 + sway, 5 + bob
  L.stamp(b, head, hx, hy)
  -- snood: a red droop from the beak that swings when it gobbles
  local sx = hx + (gobble and 5 or 4)
  L.set(b, sx, hy + 5, C.snood); L.set(b, sx, hy + 6, C.snood)
  L.set(b, sx + (gobble and 1 or 0), hy + 7, C.snood)
  return b
end

-- Hay bale: straw in short streaks along each row, a lit top face and two twine bands.
local function hayBale()
  local w, h = 18, 10
  local b = L.buffer(w, h)
  local seed = 7
  local function rnd(m) seed = (seed * 1103515245 + 12345) % 2147483648; return seed % m end
  for y = 0, h - 1 do
    local x = -rnd(4)
    while x < w do
      local len = 2 + rnd(3)
      local tone = rnd(5)
      for i = 0, len - 1 do
        local px = x + i
        if px >= 0 and px < w then
          local c = (tone == 0) and C.hayDark or (tone == 1) and C.hayLight or C.hay
          if y <= 1 then c = (tone == 0) and C.hay or C.hayLight end
          if px >= w - 3 and y > 1 then c = (tone == 1) and C.hay or C.hayDark end
          if y == h - 1 then c = C.hayDark end
          b[y][px] = c
        end
      end
      x = x + len
    end
  end
  for _, tx in ipairs({ 4, 12 }) do
    for y = 1, h - 1 do b[y][tx] = C.twine end
  end
  -- ragged straw along the top edge
  for _, x in ipairs({ 1, 7, 10, 16 }) do L.set(b, x, 0, nil) end
  return b
end

-- Pumpkin pie, seen a little from above: fluted crust round an orange filling, with a dollop of cream.
local function pie()
  return L.map({
    "....ww....",
    "..cwWwcc..",
    ".cfffffoc.",
    "cffffffooc",
    ".kckckckc.",
  }, { w = P.ink, W = "#e6dccb", c = C.crust, f = C.filling, o = C.fillingDark, k = C.crustDark })
end

-- Round striped gourd, green with cream stripes.
local function gourd()
  return L.map({
    "..s..",
    ".lcg.",
    "lgcgd",
    "ggcgd",
    ".dcd.",
  }, { s = C.stem, l = C.gourdLight, g = C.gourd, d = C.gourdDark, c = C.cream })
end

-- Two leaf shapes, each a pixel map of highlight, mid tone, shade and stem.
local MAPLE = { "...h...", ".h.hm.m", ".hhhmm.", "hhhmmmd", "..hmd..", "...s..." }
local OAK = { "..hhm", ".hhmm", "hhmmd", ".mmd.", "s...." }
local function leaf(shape, tones, flip)
  local b = L.map(shape, { h = tones[1], m = tones[2], d = tones[3], s = C.stem })
  return flip and L.flip(b) or b
end

-- Each path is a column of identical leaves 16 px apart falling 1 px a frame, so frame 16 runs
-- straight back into frame 1. They sway from side to side and turn over as they fall.
local PATHS = {
  { x = 13, y0 = 3, shape = MAPLE, tones = C.leafOrange, sway = 2.2, phase = 0.0 },
  { x = 27, y0 = 12, shape = OAK, tones = C.leafRed, sway = 1.6, phase = 2.1 },
  { x = 40, y0 = 6, shape = MAPLE, tones = C.leafGold, sway = 1.8, phase = 4.0 },
  { x = 134, y0 = 9, shape = OAK, tones = C.leafGold, sway = 1.8, phase = 1.0 },
  { x = 147, y0 = 1, shape = MAPLE, tones = C.leafRed, sway = 2.0, phase = 3.3 },
  { x = 160, y0 = 13, shape = MAPLE, tones = C.leafOrange, sway = 2.2, phase = 5.2 },
}

local function leaves(b, f)
  local layer = L.buffer(W, H)
  for _, p in ipairs(PATHS) do
    for k = -1, 4 do
      local y = p.y0 + f + 16 * k
      local x = p.x + math.floor(p.sway * math.sin(y / 5 + p.phase) + 0.5)
      local flip = math.floor((y + p.phase * 3) / 4) % 2 == 1
      L.stamp(layer, leaf(p.shape, p.tones, flip), x, y)
    end
  end
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      if layer[y][x] and inSky(x, y) then b[y][x] = layer[y][x] end
    end
  end
end

-- Head bob and gobble: two quick dips a loop, beak open at the bottom of each.
local BOB = { 0, 0, 0, 1, 2, 2, 1, 0, 0, 0, 0, 1, 2, 2, 1, 0 }

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- top corners: falling leaves
  leaves(b, f)
  -- foot of the left pillar: the turkey
  local bob = BOB[f + 1]
  L.stamp(b, turkey(math.min(bob, 1), (f >= 8 and bob > 0) and 1 or 0, bob == 2), 20, 74)
  -- foot of the right pillar: a hay bale with a pumpkin pie and a striped gourd on top
  L.stamp(b, hayBale(), 135, 86)
  L.stamp(b, pie(), 137, 81)
  L.stamp(b, gourd(), 148, 81)
  frames[f + 1] = b
end
L.saveStrip(frames, "season-11", MS)
