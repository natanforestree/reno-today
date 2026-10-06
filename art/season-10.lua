-- season-10.png: October decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- A ghost bobs in the top-left corner, two bats circle a full moon top-right, a spider
-- dangles from the banner, and jack-o'-lanterns flicker at the foot of each pillar.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-10.lua
-- Writes art/season-10.aseprite and docs/art/season-10.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  ghost = P.ink, ghostShade = "#c9bfe0", blush = "#ff9ab5",
  moon = P.goldLight, moonShade = "#ecd598", crater = "#e2c886", halo = "#fff1c22e",
  bat = "#5b4378", batDark = "#3b2b50",
  pumpkin = "#e2681c", pumpkinLight = "#f79a45", pumpkinDark = "#a8461a",
  stem = "#6b8f3a", stemDark = "#4a6328", thread = "#bba99b",
}
-- candle light inside the jack-o'-lanterns, one colour per frame
local FLAME = { P.goldLight, P.goldLight, P.bulb, P.goldLight, P.gold, P.bulb, P.goldLight, P.goldLight,
  P.bulb, P.goldLight, P.gold, P.goldLight, P.bulb, P.goldLight, P.goldLight, P.gold }

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- Ghost: a round head on a body whose hem ripples a little further along each frame.
local function ghost(f)
  local b = L.buffer(13, 16)
  local cx, top = 6, 0
  for y = 0, 15 do
    for x = 0, 12 do
      local dx = x + 0.5 - (cx + 0.5)
      local hem = 12 + math.floor(1.3 * math.sin(TAU * (x / 4 - f / 8)) + 0.5)
      local inHead = y < 6 and dx * dx + (y + 0.5 - 6) ^ 2 <= 36
      local inBody = y >= 6 and y <= hem and x >= 1 and x <= 11
      if inHead or inBody then b[y][x] = (x >= 10) and C.ghostShade or C.ghost end
    end
  end
  for _, e in ipairs({ { 4, 5 }, { 4, 6 }, { 8, 5 }, { 8, 6 } }) do L.set(b, e[1], e[2], P.outline) end
  L.set(b, 6, 8, P.outline); L.set(b, 6, 9, P.outline)
  L.set(b, 3, 8, C.blush); L.set(b, 9, 8, C.blush)
  return b
end

local BAT_UP = { "k.......k", "kk.k.k.kk", ".kkkkkkk.", "....k...." }
local BAT_DOWN = { "...k.k...", "..kkkkk..", ".kkkkkkk.", "kk.....kk" }
local function bat(f, phase)
  local up = (f + phase) % 4 < 2
  local b = L.map(up and BAT_UP or BAT_DOWN, { k = C.bat })
  L.paint(b, 3, up and 2 or 1, P.gold); L.paint(b, 5, up and 2 or 1, P.gold)   -- eyes
  return b
end

local function moon()
  local b = L.buffer(22, 22)
  local cx, cy = 11, 11
  L.eachDisc(cx, cy, 10, function(x, y) L.set(b, x, y, C.halo) end)
  L.eachDisc(cx, cy, 9, function(x, y, dx) L.set(b, x, y, dx < -5.5 and C.moonShade or C.moon) end)
  for _, c in ipairs({ { 8, 7, 1.6 }, { 14, 13, 1.2 }, { 9, 14, 0.9 }, { 14, 7, 0.8 } }) do
    L.eachDisc(c[1], c[2], c[3], function(x, y) L.paint(b, x, y, C.crater) end)
  end
  return b
end

-- Pumpkin: an ellipse with two darker ribs, lit from the left; face is a list of {dx, dy}
-- offsets from the centre, carved out and lit by the candle.
local function pumpkin(rx, ry, face, flame)
  local w, h = math.ceil(2 * rx), math.ceil(2 * ry) + 2
  local b = L.buffer(w, h)
  local cx, cy = w / 2, 2 + ry
  for y = 2, h - 1 do
    for x = 0, w - 1 do
      local u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
      if u * u + v * v <= 1 then
        local c = C.pumpkin
        if math.abs(math.abs(u) - 0.45) < 0.13 or u > 0.72 or v > 0.75 then c = C.pumpkinDark
        elseif u < -0.55 and v < 0.2 then c = C.pumpkinLight end
        b[y][x] = c
      end
    end
  end
  local mx, my = math.floor(cx), math.floor(cy)
  L.set(b, mx, 0, C.stemDark); L.set(b, mx, 1, C.stem); L.set(b, mx - 1, 0, C.stem)
  for _, p in ipairs(face or {}) do L.set(b, mx + p[1], my + p[2], flame) end
  return b
end

local HAPPY = { { -3, -2 }, { -4, -1 }, { -3, -1 }, { -2, -1 }, { 3, -2 }, { 2, -1 }, { 3, -1 }, { 4, -1 },
  { 0, 0 }, { -5, 1 }, { -4, 1 }, { -3, 1 }, { -1, 1 }, { 0, 1 }, { 1, 1 }, { 3, 1 }, { 4, 1 }, { 5, 1 },
  { -3, 2 }, { -2, 2 }, { -1, 2 }, { 1, 2 }, { 2, 2 }, { 3, 2 } }
local SPOOKY = { { -4, -2 }, { -3, -2 }, { -3, -1 }, { -2, -1 }, { 4, -2 }, { 3, -2 }, { 3, -1 }, { 2, -1 },
  { -3, 1 }, { -1, 1 }, { 1, 1 }, { 3, 1 }, { -4, 2 }, { -3, 2 }, { -2, 2 }, { -1, 2 }, { 0, 2 }, { 1, 2 },
  { 2, 2 }, { 3, 2 }, { 4, 2 }, { -2, 3 }, { 0, 3 }, { 2, 3 } }
local LITTLE = { { -2, -1 }, { 2, -1 }, { -2, 1 }, { -1, 1 }, { 0, 1 }, { 1, 1 }, { 2, 1 } }

local function spider()
  return L.map({ "k.k.k", ".kkk.", "kkrkk", ".kkk.", "k...k" }, { k = P.outline, r = P.red })
end

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- top right: the moon with two bats
  L.blit(b, moon(), 144, 3)
  L.stamp(b, bat(f, 0), 141 + wave(f, 4), 14 + wave(f, 2, math.pi / 2))
  L.stamp(b, bat(f, 2), 161 + wave(f, 3, math.pi), 6 + wave(f, 2, -math.pi / 2))
  -- top left: the ghost
  L.stamp(b, ghost(f), 16, 5 + wave(f, 2))
  -- under the banner: a spider on a thread that stretches and shrinks
  local drop = 7 + wave(f, 2, 1)
  L.line(b, 104, 62, 104, 62 + drop - 1, C.thread)
  L.blit(b, spider(), 102, 62 + drop)
  -- the foot of each pillar: jack-o'-lanterns and their little ones
  local flame = FLAME[f + 1]
  L.stamp(b, pumpkin(7.5, 5.5, HAPPY, flame), 21, 83)
  L.stamp(b, pumpkin(4.5, 3.5, nil, flame), 37, 87)
  L.stamp(b, pumpkin(7.5, 5.5, SPOOKY, FLAME[(f + 5) % FRAMES + 1]), 140, 83)
  L.stamp(b, pumpkin(5, 3.5, LITTLE, FLAME[(f + 9) % FRAMES + 1]), 128, 87)
  frames[f + 1] = b
end
L.saveStrip(frames, "season-10", MS)
