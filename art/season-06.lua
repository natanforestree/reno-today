-- season-06.png: June decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- A happy sun beams in the top-left corner, its straight and diagonal rays taking turns to
-- stretch; a puffy cloud drifts in the top-right, and a kite bobs beside it with its tail
-- wiggling and its string trailing off to someone out of sight.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-06.lua
-- Writes art/season-06.aseprite and docs/art/season-06.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  sun = "#ffd34a", sunLight = "#fff3a6", sunShade = "#f5a33a",
  ray = "#ffae42", rayLight = "#ffd36b", rayShade = "#e8792e",
  halo = "#ffd36b55", haloOuter = "#ffd36b22", cheek = "#ff8a7a", face = P.outline,
  cloud = "#fbf1ff", cloudLight = "#ffffff", cloudShade = "#d6c2ea",
  kiteRed = "#ff5f6d", kiteRedDark = "#d63a52", kiteYellow = "#ffd34a", kiteYellowDark = "#e8a23a",
  spar = P.goldLight, string = "#cdbfb0",
  bowPink = "#ff8ccb", bowBlue = "#7cc8ff", bowGreen = "#8cd86a",
}

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- Lights a filled shape from the upper left: pixels with nothing up-left of them take the
-- light colour, pixels with nothing below-right take the shade.
local function shade(b, light, dark)
  local out = L.copy(b)
  for y = 0, b.h - 1 do
    for x = 0, b.w - 1 do
      if b[y][x] then
        if not L.get(b, x + 1, y + 1) or not L.get(b, x, y + 2) then out[y][x] = dark
        elseif not L.get(b, x - 1, y - 1) or not L.get(b, x, y - 1) then out[y][x] = light end
      end
    end
  end
  return out
end

-- Sun: a round smiling face in a warm glow, ringed by eight chunky rays. The straight rays
-- and the diagonal ones take turns to stretch, so the sun seems to pulse. Like October's moon
-- it glows, so it is drawn without an outline.
local SN, SC = 29, 14          -- buffer size, centre pixel
local function sun(f)
  local b = L.buffer(SN, SN)
  L.eachDisc(SC + 0.5, SC + 0.5, 10.5, function(x, y) L.set(b, x, y, C.haloOuter) end)
  L.eachDisc(SC + 0.5, SC + 0.5, 8.5, function(x, y) L.set(b, x, y, C.halo) end)
  L.eachDisc(SC + 0.5, SC + 0.5, 6.5, function(x, y, dx, dy)
    local s = dx + dy
    L.set(b, x, y, (s < -4.5) and C.sunLight or (dx * dx + dy * dy > 25 and s > 2) and C.sunShade or C.sun)
  end)
  -- a ray pixel is lit on the side facing the upper left and shaded on the other
  local function rayPixel(x, y, ax, ay)
    local side = (x - ax) + (y - ay)
    L.set(b, x, y, side < 0 and C.rayLight or side > 0 and C.rayShade or C.ray)
  end
  local pulse = wave(f, 1)
  for _, u in ipairs({ { 0, -1 }, { 1, 0 }, { 0, 1 }, { -1, 0 } }) do
    local len = 4 + pulse
    for d = 0, len - 1 do
      local x, y = SC + u[1] * (9 + d), SC + u[2] * (9 + d)
      rayPixel(x, y, x, y)
      if d < math.ceil(len / 2) then
        rayPixel(x - u[2], y + u[1], x, y); rayPixel(x + u[2], y - u[1], x, y)
      end
    end
  end
  for _, u in ipairs({ { -1, -1 }, { 1, -1 }, { 1, 1 }, { -1, 1 } }) do
    local len = 3 - pulse
    for d = 0, len - 1 do
      local x, y = SC + u[1] * (7 + d), SC + u[2] * (7 + d)
      rayPixel(x, y, x, y)
      if d < len - 1 then rayPixel(x - u[1], y, x, y); rayPixel(x, y - u[2], x, y) end
    end
  end
  -- happy closed eyes, a smile and rosy cheeks
  for _, p in ipairs({ { -4, 0 }, { -3, -1 }, { -2, 0 }, { 2, 0 }, { 3, -1 }, { 4, 0 },
    { -2, 3 }, { -1, 4 }, { 0, 4 }, { 1, 4 }, { 2, 3 } }) do L.set(b, SC + p[1], SC + p[2], C.face) end
  for _, x in ipairs({ -5, -4, 4, 5 }) do L.set(b, SC + x, SC + 2, C.cheek) end
  return b
end

-- Cloud: a few round puffs on a flat bottom.
local PUFFS = { { 5, 8, 3.6 }, { 10, 5.5, 4.8 }, { 16, 6, 4.2 }, { 21, 8.5, 3.2 } }
local function cloud()
  local b = L.buffer(25, 12)
  for _, p in ipairs(PUFFS) do L.disc(b, p[1], p[2], p[3], C.cloud) end
  L.fillRect(b, 4, 8, 21, 11, C.cloud)
  return shade(b, C.cloudLight, C.cloudShade)
end

-- Kite: a diamond in four panels with its cross spars.
local KITE = { "....s....", "...asb...", "..aasbb..", ".aaasbbb.", "sssssssss", ".cccsddd.",
  ".cccsddd.", "..ccsdd..", "..ccsdd..", "...csd...", "....s...." }
local function kite()
  local b = L.map(KITE, { a = C.kiteRed, b = C.kiteYellow, c = C.kiteYellow, d = C.kiteRed, s = C.spar })
  -- shade the right-hand edge of each panel
  for y = 0, b.h - 1 do
    for x = b.w - 1, 0, -1 do
      local v = b[y][x]
      if v and v ~= C.spar then
        b[y][x] = (v == C.kiteRed) and C.kiteRedDark or C.kiteYellowDark
        break
      end
    end
  end
  return b
end
local BOW = { "bb.bb", "bbkbb", "bb.bb" }

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- top left: the sun in its glow
  L.blit(b, sun(f), 4, -1)
  -- top right: the kite's string sags off the right edge; the cloud drifts in front of it
  local kx, ky = 133, 1 + wave(f, 1)
  local sx, sy, ex, ey = kx + 4, ky + 5, 176, 36
  local px, py = sx, sy
  for i = 1, 12 do
    local t = i / 12
    local x = math.floor(sx + (ex - sx) * t + 0.5)
    local y = math.floor(sy + (ey - sy) * t + 7 * t * (1 - t) + 0.5)
    L.line(b, px, py, x, y, C.string)
    px, py = x, y
  end
  -- the tail streams down and to the left, a wiggle running along it
  local tail = {}
  for i = 0, 14 do
    local x = kx + 4 - i * 0.9
    local y = ky + 11 + i * 0.3 + 1.2 * math.sin(TAU * (i / 9 - f / FRAMES)) * math.min(1, i / 3)
    tail[i] = { math.floor(x + 0.5), math.floor(y + 0.5) }
    if i > 0 then L.line(b, tail[i - 1][1], tail[i - 1][2], tail[i][1], tail[i][2], C.string) end
  end
  L.stamp(b, kite(), kx, ky)
  for i, bow in ipairs({ { 5, C.bowPink }, { 10, C.bowBlue }, { 14, C.bowGreen } }) do
    local p = tail[bow[1]]
    L.stamp(b, L.map(BOW, { b = bow[2], k = L.mix(bow[2], P.outline, 0.35) }), p[1] - 2, p[2] - 1)
  end
  L.stamp(b, cloud(), 148 + wave(f, 2), 3 + wave(f, 1, math.pi / 2))
  frames[f + 1] = b
end
L.saveStrip(frames, "season-06", MS)
