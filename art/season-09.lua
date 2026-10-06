-- season-09.png: September decorations over the arch, for the Great Reno Balloon Race.
-- 16 frames of 176x96, 120 ms each, transparent except for the decorations (docs/style.css lays
-- them over arch.png). A big rainbow hot-air balloon floats in the top-left corner, its burner
-- flickering, a pink-and-cream one in the top-right, and a little far-off one drifts under the
-- banner. Each bobs gently on its own phase.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-09.lua
-- Writes art/season-09.aseprite and docs/art/season-09.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  red = "#e8434f", orange = "#ff9a3c", yellow = P.gold, green = "#7cc46a", blue = "#5aa7e6",
  pink = P.pink, cream = P.ink,
  light = "#ffffff", dark = "#6a2f5c",                     -- mixed in for highlights and shade
  skirt = "#8e5a2b", skirtLit = "#c7902e",
  rope = "#d8c3a5",
  wicker = "#b7793a", wickerLight = "#e0a868", wickerDark = "#7f4f25",
  flameTip = P.goldLight, flame = P.gold, flameBase = P.sunset,
}

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- Envelope: a round crown tapering to a narrow mouth, cut into curved vertical gores (one colour
-- each, left to right), lit from the upper left. The last two rows are the skirt; lit warms it.
local function envelope(R, gores, hb, lit)
  local w, cx, cy = 2 * R, R, R
  local mouth = math.max(1.5, R * 0.3)
  local b = L.buffer(w, hb)
  for y = 0, hb - 1 do
    local yc = y + 0.5
    local hw
    if yc <= cy then hw = math.sqrt(math.max(0, R * R - (yc - cy) ^ 2))
    else hw = mouth + (R - mouth) * math.cos((yc - cy) / (hb - cy) * math.pi / 2) end
    for x = 0, w - 1 do
      local u = (x + 0.5 - cx) / hw
      if math.abs(u) <= 1 then
        local c
        if y >= hb - 2 then
          c = lit and C.skirtLit or C.skirt
        else
          -- halfway between flat stripes and true gores, so the edge stripes don't shrink to slivers
          local a = 0.5 * math.asin(u) / (math.pi / 2) + 0.5 * u
          local k = math.min(#gores, math.floor((a + 1) / 2 * #gores) + 1)
          c = gores[k]
          local l = -0.7 * u - 0.5 * (yc - cy) / R
          if l > 0.7 then c = L.mix(c, C.light, 0.35)
          elseif l < -0.45 then c = L.mix(c, C.dark, 0.3) end
        end
        b[y][x] = c
      end
    end
  end
  return b
end

-- Wicker basket: a lit rim on top, a woven body, shaded on the right.
local function basket(w, h)
  local b = L.buffer(w, h)
  for y = 0, h - 1 do
    for x = 0, w - 1 do
      local c = C.wicker
      if y == 0 then c = C.wickerLight
      elseif x == w - 1 or (x + y) % 2 == 0 then c = C.wickerDark end
      b[y][x] = c
    end
  end
  return b
end

-- Burner flame, one per frame: its colours from the burner upward; a tall one warms the skirt.
local FLAMES = {
  { C.flameBase, C.flame, C.flameTip }, { C.flameBase, C.flame }, { C.flameBase, C.flame, C.flameTip },
  { C.flameBase, C.flame, C.flame, C.flameTip }, { C.flameBase, C.flame, C.flameTip }, { C.flameBase },
  { C.flameBase, C.flame }, { C.flameBase, C.flame, C.flameTip }, { C.flameBase, C.flame, C.flame, C.flameTip },
  { C.flameBase, C.flame, C.flameTip }, { C.flameBase, C.flame }, { C.flameBase, C.flame, C.flameTip },
  { C.flameBase, C.flame }, { C.flameBase, C.flame, C.flame, C.flameTip }, { C.flameBase, C.flame, C.flameTip },
  { C.flameBase, C.flame },
}

-- A whole balloon at (x, y): envelope, ropes, basket, and (if flame is given) the burner flame.
local function balloon(dst, x, y, R, gores, opt, flame)
  local hb, ropes, bw, bh = opt.hb, opt.ropes, opt.bw, opt.bh
  local tall = flame and #flame >= 3
  L.stamp(dst, envelope(R, gores, hb, tall), x, y)
  local mouth = math.max(1.5, R * 0.3)
  local ml, mr = math.floor(x + R - mouth + 0.5), math.floor(x + R + mouth - 0.5)
  local bx = x + R - bw // 2
  local by = y + hb + ropes
  L.line(dst, ml, y + hb, bx, by - 1, C.rope)
  L.line(dst, mr, y + hb, bx + bw - 1, by - 1, C.rope)
  if flame then
    for i, c in ipairs(flame) do   -- two pixels wide, the tip leaning left or right in turn
      if i < #flame or #flame % 2 == 1 then L.set(dst, x + R - 1, by - i, c) end
      if i < #flame or #flame % 2 == 0 then L.set(dst, x + R, by - i, c) end
    end
  end
  L.stamp(dst, basket(bw, bh), bx, by)
end

local BIG = { hb = 21, ropes = 4, bw = 6, bh = 4 }
local MID = { hb = 17, ropes = 3, bw = 4, bh = 3 }
local FAR = { hb = 10, ropes = 2, bw = 3, bh = 2 }
local RAINBOW = { C.red, C.orange, C.yellow, C.green, C.blue }
local CANDY = { C.pink, C.cream, C.pink, C.cream, C.pink }
local SKY = { C.blue, C.yellow, C.blue }

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- top left: the big rainbow balloon, burner flickering
  balloon(b, 8, 3 + wave(f, 2), 9, RAINBOW, BIG, FLAMES[f + 1])
  -- top right: the pink-and-cream one, bobbing a beat behind
  balloon(b, 150, 6 + wave(f, 2, 2.2), 7, CANDY, MID)
  -- under the banner: a little one far away
  balloon(b, 124, 69 + wave(f, 1, 4.2), 4, SKY, FAR)
  frames[f + 1] = b
end
L.saveStrip(frames, "season-09", MS)
