-- arch.png: the page header, the Reno Arch at dusk. 8 frames of 176x96, 120 ms each.
-- Bulbs chase along the pillars and over the arch (every fourth bulb is dark and the
-- dark ones step forward a bulb each frame), RENO glows in pink neon with a flicker on
-- frame 6, and the red banner reads THE BIGGEST LITTLE CITY IN THE WORLD in a 5-px-tall font.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/arch.lua
-- Writes art/arch.aseprite and docs/art/arch.png (a 1408x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 8, 120

-- The arch band is the top half of the ring between two ellipses centred on (ACX, ACY).
local ACX, ACY = 87.5, 58
local OUT_RX, OUT_RY, IN_RX, IN_RY = 80, 40, 72, 32
local function inside(x, y, rx, ry)
  local dx, dy = (x + 0.5 - ACX) / rx, (y + 0.5 - ACY) / ry
  return dx * dx + dy * dy <= 1
end

-- 5x7 letters for RENO; a 3x5 font for the banner ("#" is lit).
local BIG = {
  R = { "####.", "#...#", "#...#", "####.", "#..#.", "#..#.", "#..##" },
  E = { "#####", "#....", "#....", "####.", "#....", "#....", "#####" },
  N = { "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#" },
  O = { ".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###." },
}
local SMALL = {
  T = { "###", ".#.", ".#.", ".#.", ".#." }, H = { "#.#", "#.#", "###", "#.#", "#.#" },
  E = { "###", "#..", "##.", "#..", "###" }, B = { "##.", "#.#", "##.", "#.#", "##." },
  I = { "###", ".#.", ".#.", ".#.", "###" }, G = { ".##", "#..", "#.#", "#.#", ".##" },
  S = { ".##", "#..", ".#.", "..#", "##." }, L = { "#..", "#..", "#..", "#..", "###" },
  C = { ".##", "#..", "#..", "#..", ".##" }, Y = { "#.#", "#.#", ".#.", ".#.", ".#." },
  N = { "#..#", "##.#", "#.##", "#..#", "#..#" }, W = { "#...#", "#...#", "#.#.#", "#.#.#", ".#.#." },
  O = { ".#.", "#.#", "#.#", "#.#", ".#." }, R = { "##.", "#.#", "##.", "#.#", "#.#" },
  D = { "##.", "#.#", "#.#", "#.#", "##." },
}
local BANNER = "THE BIGGEST LITTLE CITY IN THE WORLD"   -- 132 px wide in this font, x 22..153

-- Everything that stays the same between frames. The left half is drawn and then
-- mirrored, so the arch is exactly symmetric.
local function structure()
  local b = L.buffer(W, H)
  -- starburst crown: 16 rays round a gold hub (the band covers the lower rays)
  for k = 0, 15 do
    local a = math.rad(k * 22.5)
    local len = (k % 2 == 0) and 11 or 6
    for s = 0, len * 2 do
      local r = s / 2
      L.set(b, ACX + r * math.cos(a), 12 - r * math.sin(a),
        (k % 2 == 0 and r > len - 2) and P.gold or P.silver)
    end
  end
  L.disc(b, ACX, 12, 4, P.gold)
  L.set(b, 85, 10, P.goldLight); L.set(b, 86, 10, P.goldLight); L.set(b, 85, 11, P.goldLight)
  -- the band: lit along the outer edge, shaded along the inner edge
  for y = 0, ACY do
    for x = 0, W - 1 do
      if inside(x, y, OUT_RX, OUT_RY) and not inside(x, y, IN_RX, IN_RY) then
        local c = P.steel
        if not (inside(x, y - 1, OUT_RX, OUT_RY) and inside(x - 1, y, OUT_RX, OUT_RY)
            and inside(x + 1, y, OUT_RX, OUT_RY)) then
          c = P.steelLight
        elseif inside(x, y + 1, IN_RX, IN_RY) or inside(x - 1, y, IN_RX, IN_RY)
            or inside(x + 1, y, IN_RX, IN_RY) then
          c = P.steelDark
        end
        L.set(b, x, y, c)
      end
    end
  end
  -- pillars, with a wider capital and base
  for y = 50, H - 1 do
    local wide = y <= 52 or y >= H - 4
    for x = wide and 6 or 8, wide and 17 or 15 do
      L.set(b, x, y, (x <= 8) and P.steelLight or (x >= 15) and P.steelDark or P.steel)
    end
  end
  for y = 0, H - 1 do
    for x = 0, W / 2 - 1 do b[y][W - 1 - x] = b[y][x] end
  end
  -- the banner across the opening, with its lettering
  L.fillRect(b, 18, 53, 157, 61, P.red)
  L.fillRect(b, 18, 54, 157, 54, P.redLight)
  L.fillRect(b, 18, 53, 157, 53, P.redDark)
  L.fillRect(b, 18, 61, 157, 61, P.redDark)
  local x = 22
  for i = 1, #BANNER do
    local ch = BANNER:sub(i, i)
    if ch == " " then
      x = x + 2
    else
      local g = SMALL[ch]
      for gy = 1, 5 do
        for gx = 1, #g[1] do
          if g[gy]:sub(gx, gx) == "#" then L.set(b, x + gx - 1, 54 + gy, P.ink) end
        end
      end
      x = x + #g[1] + 1
    end
  end
  return b
end

-- The chase path: up the left pillar, over the arch, down the right pillar.
local PATH, half = {}, {}
for i = 0, 21 do
  local t = math.rad(170 - i * (78 / 21))           -- 170 degrees to 92
  half[#half + 1] = { math.floor(ACX + 76 * math.cos(t)), math.floor(ACY - 36 * math.sin(t)) }
end
for y = 92, 56, -6 do PATH[#PATH + 1] = { 11, y } end
for _, p in ipairs(half) do PATH[#PATH + 1] = p end
for i = #half, 1, -1 do PATH[#PATH + 1] = { W - 1 - half[i][1], half[i][2] } end
for y = 56, 92, 6 do PATH[#PATH + 1] = { W - 1 - 11, y } end

local function bulb(b, x, y, lit)
  if not lit then L.set(b, x, y, P.bulbOff); return end
  for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }) do
    local under = L.get(b, x + d[1], y + d[2])
    if under then L.set(b, x + d[1], y + d[2], L.mix(under, P.bulb, 0.45)) end
  end
  L.set(b, x, y, P.bulb)
end

-- RENO in neon tubes: 3x3 blocks per font pixel, with a pale core line along each stroke.
local function neon(f)
  local b = L.buffer(W, H)
  local x0, y0 = 52, 31                              -- 4 letters x 15 px + 3 gaps x 4 px = 72 px
  for li, ch in ipairs({ "R", "E", "N", "O" }) do
    local g = BIG[ch]
    local dim = (f == 6 and ch == "N")
    local tube, core = dim and P.neonDim or P.neon, dim and P.neonDimCore or P.neonCore
    local lx = x0 + (li - 1) * 19
    local function lit(gx, gy)
      return gy >= 0 and gy < 7 and gx >= 0 and gx < 5 and g[gy + 1]:sub(gx + 1, gx + 1) == "#"
    end
    for gy = 0, 6 do
      for gx = 0, 4 do
        if lit(gx, gy) then L.fillRect(b, lx + gx * 3, y0 + gy * 3, lx + gx * 3 + 2, y0 + gy * 3 + 2, tube) end
      end
    end
    for gy = 0, 6 do
      for gx = 0, 4 do
        if lit(gx, gy) then
          local cx, cy = lx + gx * 3 + 1, y0 + gy * 3 + 1
          L.set(b, cx, cy, core)
          if lit(gx + 1, gy) then L.set(b, cx + 1, cy, core); L.set(b, cx + 2, cy, core) end
          if lit(gx, gy + 1) then L.set(b, cx, cy + 1, core); L.set(b, cx, cy + 2, core) end
        end
      end
    end
  end
  L.outline(b, P.glow, true, { [P.neonDim] = true, [P.neonDimCore] = true })
  return b
end

local base = structure()
local frames = {}
for f = 1, FRAMES do
  local b = L.copy(base)
  for i, p in ipairs(PATH) do bulb(b, p[1], p[2], (i - f) % 4 ~= 0) end
  L.outline(b, P.outline)
  L.blit(b, neon(f), 0, 0)
  frames[f] = b
end
L.saveStrip(frames, "arch", MS)
