-- season-03.png: March decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- A rainbow arcs between two little clouds in the top-left corner, three shamrocks float
-- top-right, clover tufts grow at the foot of each pillar, and a pot of gold glints by the right one.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-03.lua
-- Writes art/season-03.aseprite and docs/art/season-03.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  bands = { "#ec4651", "#ff9a3d", "#ffdb5c", "#5cc45a", "#4f9de6" },   -- outside to inside
  cloud = P.ink, cloudShade = "#c9bfe0", cloudLight = "#fffaf0",
  leaf = "#4cb24e", leafLight = "#8ee070", leafShine = "#c8f5a0", leafDark = "#2c7a3c", stem = "#3f8f3f",
  grass = "#52a948", grassLight = "#7fcf5c", grassDark = "#2f7438",
  pot = "#3e3856", potLight = "#5d567f", potShine = "#8a84ad", potDark = "#2a2440",
  rim = "#5f5a7c", rimLight = "#9a95b8",
  gold = P.gold, goldLight = P.goldLight, goldDark = P.goldDark, glint = "#fffdf2",
}

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- Rainbow: five 2 px bands round (cx, cy), cut off at the buffer's height h so the feet
-- stay hidden behind the clouds.
local function rainbow(w, h, cx, cy, rOut)
  local b = L.buffer(w, h)
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      local dx, dy = x + 0.5 - cx, y + 0.5 - cy
      local d = math.sqrt(dx * dx + dy * dy)
      local band = math.floor((rOut - d) / 2) + 1
      if dy < 0 and d <= rOut and band <= #C.bands then b[y][x] = C.bands[band] end
    end
  end
  return b
end

-- Cloud: a few overlapping puffs on a flat base, lit from the upper left.
local function cloud(puffs, w, h)
  local b = L.buffer(w, h)
  for _, p in ipairs(puffs) do
    L.eachDisc(p[1], p[2], p[3], function(x, y) L.set(b, x, y, C.cloud) end)
  end
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      if b[y][x] and (y >= h - 2 or not L.get(b, x + 1, y)) then b[y][x] = C.cloudShade end
    end
  end
  for _, p in ipairs(puffs) do
    L.paint(b, math.floor(p[1] - p[3] * 0.4), math.floor(p[2] - p[3] * 0.5), C.cloudLight)
  end
  return b
end

-- Shamrocks, drawn by hand: three heart-shaped leaves (up, left, right) meeting at the
-- centre, and a curling stem. h shine, l light, b leaf, d shade, s stem; the gaps between
-- leaves fill with outline when stamped.
local SHAMROCK = {
  "....ll.bb....",
  "...lhlbbbd...",
  "...llbbbbd...",
  ".ll.bbbbd.lb.",
  "lhlb.bbd.llbd",
  "llbbb.b.lbbbd",
  ".bbbbbbbbbbd.",
  "bbbbd.s.bbbbd",
  "bbdd..s..bbdd",
  ".dd...s...dd.",
  ".......s.....",
  ".......s.....",
  "........s....",
}
local SHAMROCK_SMALL = {
  "..ll.bb..",
  "..llbbd..",
  "ll.bbd.lb",
  "lbb.b.lbd",
  ".bbbbbbd.",
  "bbd.s.bbd",
  "dd..s..dd",
  ".....s...",
  ".....s...",
}
local function shamrock(rows)
  return L.map(rows, { h = C.leafShine, l = C.leafLight, b = C.leaf, d = C.leafDark, s = C.stem })
end

-- A little shamrock for the tufts, drawn by hand; the gaps between its leaves fill with outline.
local SPRIG = { "..l.b..", "..lbd..", "ll.b.bb", ".bbbbd.", "bd...bd" }
local function sprig() return L.map(SPRIG, { l = C.leafLight, b = C.leaf, d = C.leafDark }) end

-- Clover tuft standing on the ground at (x, y + 5): grass blades, and sprigs on stems at
-- {dx, height}. sway leans the sprig heads a pixel side to side.
local function tuft(dst, x, y, w, blades, heads, sway)
  for _, hd in ipairs(heads) do
    local hx, top = x + hd[1] + sway, y + 5 - hd[2]
    L.line(dst, x + hd[1], y + 5, hx, top + 4, C.stem)
    L.stamp(dst, sprig(), hx - 3, top)
  end
  local g = L.buffer(w, 6)
  for _, bl in ipairs(blades) do
    local bx, bh, lean = bl[1], bl[2], bl[3]
    L.line(g, bx, 5, bx + lean, 6 - bh, C.grass)
    L.set(g, bx + lean, 6 - bh, C.grassLight)
    L.set(g, bx, 5, C.grassDark)
  end
  L.stamp(dst, g, x, y)
end

-- Pot of gold: an iron pot with a rim and stubby legs, coins heaped over the top.
local POT = {
  ".................",
  ".................",
  ".................",
  ".................",
  ".................",
  "kkkkkkkkkkkkkkkkr",
  "rrrrrrrrrrrrrrrrr",
  ".Phhpppppppppppd.",
  ".Phppppppppppppd.",
  ".Ppppppppppppppd.",
  "..Ppppppppppppd..",
  "...pppppppppdd...",
  "....ddddddddd....",
  "...dd.......dd...",
}
local COINS = { { 2, 3 }, { 5, 1 }, { 8, 0 }, { 11, 1 }, { 13, 3 }, { 4, 3 }, { 7, 2 }, { 10, 3 } }
local function potOfGold()
  local b = L.map(POT, { k = C.rimLight, r = C.rim, p = C.pot, P = C.potLight, h = C.potShine,
    d = C.potDark })
  -- the heap: a half-ellipse of gold just above the rim
  for y = 0, 4 do
    for x = 0, 16 do
      local u, v = (x + 0.5 - 8.5) / 7.5, (y + 0.5 - 5.5) / 5
      if u * u + v * v <= 1 then b[y][x] = C.gold end
    end
  end
  -- coins on the heap: a dark rim and a bright face each
  for _, c in ipairs(COINS) do
    local x, y = c[1], c[2]
    L.paint(b, x, y, C.goldLight); L.paint(b, x + 1, y, C.goldLight)
    L.paint(b, x - 1, y + 1, C.goldDark); L.paint(b, x + 2, y + 1, C.goldDark)
    L.paint(b, x, y + 1, C.gold); L.paint(b, x + 1, y + 1, C.gold)
  end
  return b
end

-- A coin lying on the grass.
local function coin() return L.map({ ".yy.", "yYYo", ".oo." }, { y = C.gold, Y = C.goldLight, o = C.goldDark }) end

-- Glint: a four-point twinkle at size 2 (star), 1 (plus) or 0 (a dot).
local function glint(size)
  if size == 2 then
    return L.map({ "...w...", "...w...", "..wWw..", "wwWWWww", "..wWw..", "...w...", "...w..." },
      { w = C.goldLight, W = C.glint })
  elseif size == 1 then
    return L.map({ ".w.", "wWw", ".w." }, { w = C.goldLight, W = C.glint })
  end
  return L.map({ "W" }, { W = C.glint })
end
-- size of a pot glint k frames into its 16-frame cycle (off after the fourth frame)
local GLINT = { 2, 2, 1, 0 }

-- A twinkle beside the rainbow: its size each frame (nil is off).
local SPARK = { 1, 1, 0, nil, nil, nil, nil, nil, 0, 1, 2, 2, 1, 0, nil, nil }

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- top left: a rainbow between two clouds that bob out of step, and two twinkles
  L.stamp(b, rainbow(40, 18, 20, 22, 19), 2, 0)
  L.stamp(b, cloud({ { 4, 5, 3.2 }, { 9, 3.5, 4 }, { 14, 5, 3.2 } }, 18, 8), 0, 15 + wave(f, 1))
  L.stamp(b, cloud({ { 4, 5, 3.2 }, { 9, 3.5, 4 }, { 14, 5, 3.4 } }, 18, 8), 28, 13 + wave(f, 1, math.pi))
  for i, spot in ipairs({ { 48, 7 }, { 4, 4 } }) do
    local s = SPARK[(f + (i - 1) * 8) % FRAMES + 1]
    if s then local g = glint(s); L.blit(b, g, spot[1] - g.w // 2, spot[2] - g.h // 2) end
  end

  -- top right: three shamrocks floating, each bobbing and swaying on its own phase
  L.stamp(b, shamrock(SHAMROCK), 143 + wave(f, 1, 1), 4 + wave(f, 2))
  L.stamp(b, shamrock(SHAMROCK_SMALL), 127 + wave(f, 1, 3), 2 + wave(f, 1, 2))
  L.stamp(b, shamrock(SHAMROCK_SMALL), 161 + wave(f, 1, 5), 20 + wave(f, 1, 4))

  -- the foot of the left pillar: clover tufts
  tuft(b, 20, 90, 17, { { 1, 3, -1 }, { 3, 4, 0 }, { 6, 3, 1 }, { 9, 4, 0 }, { 12, 3, -1 }, { 15, 4, 1 } },
    { { 5, 11 }, { 11, 8 } }, wave(f, 1))
  tuft(b, 38, 90, 9, { { 1, 3, 0 }, { 4, 4, 1 }, { 7, 3, 0 } }, { { 4, 7 } }, wave(f, 1, 2))
  -- the foot of the right pillar: the pot of gold beside a tuft, a stray coin, glints
  tuft(b, 125, 90, 9, { { 1, 3, -1 }, { 4, 4, 0 }, { 7, 3, 1 } }, { { 4, 9 } }, wave(f, 1, 3))
  L.stamp(b, potOfGold(), 138, 82)
  L.stamp(b, coin(), 134, 92)
  for i, spot in ipairs({ { 147, 83 }, { 141, 85 }, { 151, 86 } }) do
    local s = GLINT[(f - (i - 1) * 6) % FRAMES + 1]
    if s then local g = glint(s); L.blit(b, g, spot[1] - g.w // 2, spot[2] - g.h // 2) end
  end
  frames[f + 1] = b
end
L.saveStrip(frames, "season-03", MS)
