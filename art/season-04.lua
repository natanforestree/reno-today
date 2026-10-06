-- season-04.png: April decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- Cherry-blossom branches reach into the top corners and sway in the breeze, petals drift
-- down, a little bunny at the foot of the left pillar twitches its ears and nose, and two
-- painted eggs sit in the grass by the right pillar.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-04.lua
-- Writes art/season-04.aseprite and docs/art/season-04.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  bark = "#a8705a", barkLight = "#d49c7a", barkDark = "#74463c",
  petal = "#ff9cc8", petalLight = "#ffd0e4", petalWhite = "#fff4f8", petalDark = "#e0679f",
  heart = "#d9437f", pollen = P.gold, bud = "#f0609c",
  fur = P.ink, furShade = "#d8c6cf", earPink = "#ffb0c8", nose = "#f0709a", blush = "#ffa3be",
  grass = "#5aae4c", grassLight = "#86d264", grassDark = "#33773c",
  eggBlue = "#8fc8f0", eggBlueDark = "#5f98c8", eggYellow = "#ffe07a", eggYellowDark = "#d8a843",
  eggTrim = P.ink, eggDot = "#ff7fb0",
}

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- Blossoms, lit from the upper left: L white, l light, p petal, d shade, r the deep pink
-- heart, c pollen. The gaps between petals fill with outline when stamped.
local BLOSSOM = { "..LLl..", "L.llp.p", "Llprppp", "lprcrpd", ".pprpd.", ".pd.dd.", ".d...d." }
local FLORET = { "..L..", "LLlpp", ".lcp.", ".p.d." }
local KEY = { L = C.petalWhite, l = C.petalLight, p = C.petal, d = C.petalDark, r = C.heart, c = C.pollen }
local function blossom() return L.map(BLOSSOM, KEY) end
local function floret() return L.map(FLORET, KEY) end

-- A branch (or twig) is a list of points {x, y, thickness}. bend() returns it swayed: the
-- base stays put and the far end moves by up to `sway` px. Blossoms are placed on the result.
local function bend(points, sway)
  local out = {}
  for i, p in ipairs(points) do
    local t = (i - 1) / (#points - 1)
    out[i] = { p[1], p[2] + math.floor(sway * t * t + 0.5), p[3] }
  end
  return out
end

local function branch(b, pts)
  local layer = L.buffer(W, H)
  for i = 1, #pts - 1 do
    local a, c = pts[i], pts[i + 1]
    L.line(layer, a[1], a[2], c[1], c[2], C.bark)
    if a[3] > 1 then L.line(layer, a[1], a[2] + 1, c[1], c[2] + 1, C.barkDark) end
  end
  -- light catches the top edge of the thick bark
  for y = 0, H - 2 do
    for x = 0, W - 1 do
      if layer[y][x] == C.bark and not L.get(layer, x, y - 1) and layer[y + 1][x] then
        layer[y][x] = C.barkLight
      end
    end
  end
  L.stamp(b, layer, 0, 0)
end

-- Bunny facing us, sitting. twitch tips the right ear's top out for a moment; wiggle lifts
-- the nose a pixel.
local BUNNY = {
  "...w.....w...",
  "..wpw...wpw..",
  "..wpw...wpw..",
  "..wpw...wps..",
  "..wpw...wps..",
  "..wws...wws..",
  "..wwwwwwwws..",
  ".wwwwwwwwwss.",
  ".wwwkwwwkwss.",
  ".wwbwwnwwbws.",
  ".wwwwwwwwwss.",
  "..wwwwwwwss..",
  ".wwwwwwwwwss.",
  "wwwwwwwwwwwss",
  "wwwwwwwwwwsss",
  ".wwws.swwsss.",
}
local function bunny(twitch, wiggle)
  local rows = {}
  for i, r in ipairs(BUNNY) do rows[i] = r end
  if twitch then
    -- the top three rows of the right ear lean one pixel outwards
    for i = 1, 3 do rows[i] = rows[i]:sub(1, 7) .. "." .. rows[i]:sub(8, 12) end
  end
  if wiggle then
    rows[9] = rows[9]:sub(1, 6) .. "n" .. rows[9]:sub(8)
    rows[10] = rows[10]:sub(1, 6) .. "w" .. rows[10]:sub(8)
  end
  return L.map(rows, { w = C.fur, s = C.furShade, p = C.earPink, k = P.outline, n = C.nose, b = C.blush })
end
-- ear twitches and nose wiggles, by frame
local TWITCH = { [6] = true, [7] = true, [12] = true }
local WIGGLE = { [2] = true, [4] = true, [10] = true, [14] = true }

-- Painted egg, 7x9: a base colour, a shade down its right side, and dots or a zigzag band.
local function egg(base, dark, trim, dots)
  local b = L.buffer(7, 9)
  L.ellipse(b, 3.5, 4.8, 3.5, 4.5, base)
  for y = 0, 8 do for x = 0, 6 do
    if b[y][x] and (x >= 5 and not L.get(b, x + 1, y) or y == 8) then b[y][x] = dark end
  end end
  if dots then
    for _, d in ipairs({ { 2, 3 }, { 4, 2 }, { 1, 6 }, { 3, 5 }, { 5, 5 }, { 4, 7 } }) do L.paint(b, d[1], d[2], trim) end
  else
    for x = 0, 6 do L.paint(b, x, 4 + (x % 2), trim) end
  end
  L.paint(b, 2, 1, C.petalWhite); L.paint(b, 1, 2, C.petalWhite)
  return b
end

local function grass(w, blades)
  local g = L.buffer(w, 5)
  for _, bl in ipairs(blades) do
    L.line(g, bl[1], 4, bl[1] + bl[3], 5 - bl[2], C.grass)
    L.set(g, bl[1] + bl[3], 5 - bl[2], C.grassLight)
    L.set(g, bl[1], 4, C.grassDark)
  end
  return g
end

-- Falling petal: drifts down 1 px a frame and right every other frame, tumbling between a
-- flat and an edge-on shape; it starts and ends its loop as a single pixel.
local function petal(b, f, x, y, phase)
  local k = (f + phase) % FRAMES
  local px, py = x + k // 2 + wave(k, 1, phase), y + k
  if k == 0 or k == 15 then L.set(b, px, py, C.petalLight); return end
  if (k // 3) % 2 == 0 then
    L.blit(b, L.map({ "lp", "pd" }, KEY), px, py)
  else
    L.blit(b, L.map({ "lpd" }, KEY), px, py)
  end
end

-- Blossom spots on a branch: {point index, dx, dy, kind}, relative to that (swaying) point.
local function bloomOn(b, pts, spots)
  for _, sp in ipairs(spots) do
    local p = pts[sp[1]]
    local x, y = p[1] + sp[2], p[2] + sp[3]
    if sp[4] == "B" then L.stamp(b, blossom(), x, y)
    elseif sp[4] == "f" then L.stamp(b, floret(), x, y)
    else L.set(b, x, y, C.bud); L.set(b, x, y - 1, C.petalLight) end
  end
end

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  local breeze = math.sin(TAU * f / FRAMES)
  -- top left: a branch in from the left edge with two twigs, covered in blossom
  local main = bend({ { -2, 14, 2 }, { 8, 11, 2 }, { 18, 8, 2 }, { 28, 5, 1 }, { 38, 3, 1 } }, breeze)
  local twigA = bend({ { 12, 10, 1 }, { 19, 14, 1 }, { 27, 17, 1 } }, breeze)
  local twigB = bend({ { 22, 7, 1 }, { 24, 1, 1 } }, breeze)
  branch(b, main); branch(b, twigA); branch(b, twigB)
  bloomOn(b, twigA, { { 2, -5, -3, "f" }, { 3, -5, -5, "B" }, { 3, 2, -1, "f" }, { 3, 2, 3, "o" } })
  bloomOn(b, twigB, { { 2, -3, -2, "f" }, { 2, 2, 0, "o" } })
  bloomOn(b, main, { { 2, -6, -4, "B" }, { 2, 1, 0, "f" }, { 3, -3, -6, "B" }, { 3, 2, -2, "f" },
    { 4, -1, -5, "f" }, { 4, 0, 0, "o" }, { 5, -5, -4, "B" }, { 5, 2, -1, "f" }, { 1, 3, -3, "o" } })
  -- top right: a branch in from the right edge, swaying the other way
  local mainR = bend({ { 178, 18, 2 }, { 167, 14, 2 }, { 157, 11, 2 }, { 147, 7, 1 }, { 137, 5, 1 } }, -breeze)
  local twigC = bend({ { 162, 12, 1 }, { 155, 17, 1 }, { 148, 20, 1 } }, -breeze)
  local twigD = bend({ { 151, 9, 1 }, { 149, 2, 1 } }, -breeze)
  branch(b, mainR); branch(b, twigC); branch(b, twigD)
  bloomOn(b, twigC, { { 2, 0, -3, "f" }, { 3, -2, -5, "B" }, { 3, -5, -1, "f" }, { 3, -1, 3, "o" } })
  bloomOn(b, twigD, { { 2, -1, -2, "f" }, { 2, -3, 0, "o" } })
  bloomOn(b, mainR, { { 2, -1, -4, "B" }, { 2, -6, 0, "f" }, { 3, -3, -6, "B" }, { 3, -6, -2, "f" },
    { 4, -3, -5, "f" }, { 4, 0, 0, "o" }, { 5, -3, -4, "B" }, { 5, -6, -1, "f" }, { 1, -2, -4, "o" } })

  -- petals drifting down from both branches, and a few under the banner
  for _, p in ipairs({ { 9, 15, 0 }, { 24, 12, 5 }, { 32, 6, 10 }, { 3, 24, 13 },
    { 137, 9, 3 }, { 152, 13, 8 }, { 163, 18, 12 }, { 166, 4, 6 },
    { 24, 63, 7 }, { 40, 66, 14 }, { 132, 64, 2 }, { 146, 67, 11 } }) do
    petal(b, f, p[1], p[2], p[3])
  end

  -- the foot of the left pillar: the bunny, with a tuft of grass
  L.stamp(b, bunny(TWITCH[f], WIGGLE[f]), 22, 80)
  L.stamp(b, grass(9, { { 1, 3, 0 }, { 3, 4, 1 }, { 6, 3, 0 }, { 8, 2, 1 } }), 34, 91)
  -- the foot of the right pillar: two eggs in the grass
  L.stamp(b, egg(C.eggYellow, C.eggYellowDark, C.eggDot, true), 141, 86)
  L.stamp(b, egg(C.eggBlue, C.eggBlueDark, C.eggTrim, false), 149, 87)
  L.stamp(b, grass(20, { { 1, 3, 0 }, { 3, 2, 1 }, { 6, 3, -1 }, { 9, 2, 0 }, { 12, 3, 1 }, { 15, 2, 0 }, { 17, 3, -1 } }), 138, 91)
  frames[f + 1] = b
end
L.saveStrip(frames, "season-04", MS)
