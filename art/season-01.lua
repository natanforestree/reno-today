-- season-01.png: January decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- Snow lies piled on the arch: along the top of the steel band and round the crown's base, on the
-- pillar capitals and on both ends of the banner's top edge. Gentle snow falls behind the arch, a
-- snowman in a red scarf waves a stick arm from a drift at the foot of the left pillar, and a
-- cardinal hops on a drift at the foot of the right one.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-01.lua
-- Writes art/season-01.aseprite and docs/art/season-01.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  snowTop = "#ffffff", snow = "#eaf1fa", snowShade = "#c3d2ea",
  flake = "#ffffff", flakeDim = "#dfe8f5",
  coal = P.outline, carrot = "#f2802e", carrotDark = "#c75a1c", stick = "#4f3420", blush = "#ff9ab5",
  scarf = P.red, scarfLight = P.redLight, scarfDark = P.redDark,
  hat = "#4a86d0", hatLight = "#7cb0ec", hatDark = "#2f5a96", pom = P.ink,
  cardinal = "#e0303e", cardinalLight = "#ff6a6a", cardinalDark = "#9a1f2c", beak = "#ffb03a",
}

-- The arch's geometry (art/arch.lua): the band is the top half of the ring between ellipses
-- centred on (87.5, 58), outer radii 80x40 and inner 72x32; pillars at x 6..17 and 158..169
-- from y 50, capitals y 50..52; banner x 18..157, y 53..61; RENO (with glow) x 51..124, y 30..52.
local ACX, ACY = 87.5, 58
local function inE(x, y, rx, ry)
  local dx, dy = (x + 0.5 - ACX) / rx, (y + 0.5 - ACY) / ry
  return dx * dx + dy * dy <= 1
end
local function bandTop(x)
  for y = 0, ACY do if inE(x, y, 80, 40) then return y end end
end

-- Pixels that belong to the arch (with its outline): falling snow is hidden there, so it falls
-- behind the arch and never covers the lettering.
local function onArch(x, y)
  if y <= 59 and inE(x, y, 81.5, 41.5) and not inE(x, y, 70.5, 30.5) then return true end
  if x >= 74 and x <= 101 and y <= 24 then return true end                 -- the crown
  if y >= 48 and ((x >= 4 and x <= 19) or (x >= 156 and x <= 171)) then return true end
  if x >= 49 and x <= 126 and y >= 28 and y <= 54 then return true end
  return x >= 17 and x <= 158 and y >= 52 and y <= 62
end

-- The steel itself (band, pillars, banner): the piled snow's outline never goes on these. The
-- crown is left out, so where the crown stands in the snow it gets an outline of its own.
local function steel(x, y)
  if y <= ACY and inE(x, y, 80, 40) and not inE(x, y, 72, 32) then return true end
  if y >= 50 and ((x >= 6 and x <= 17) or (x >= 158 and x <= 169)) then return true end
  return x >= 18 and x <= 157 and y >= 53 and y <= 61
end

-- Piled snow: a mask of snow pixels, shaded white on top and blue underneath, with a dark outline
-- only where it meets the sky, so it sits on the arch's own outline.
local function pile()
  local m = L.buffer(W, H)
  local function add(x, y) L.set(m, x, y, true) end
  -- along the band: deep and lumpy where it is nearly flat, thinner down the shoulders, bare where steep
  for x = 0, W - 1 do
    local top = bandTop(x)
    if top then
      local u = (x + 0.5 - ACX) / 80
      local slope = 0.5 * math.abs(u) / math.sqrt(math.max(1e-6, 1 - u * u))
      local t = slope < 0.45 and 3 or slope < 1.05 and 2 or 0
      if slope < 0.45 then                                                 -- lumpy on the flat top
        local lump = math.sin(x * 0.55) + math.sin(x * 0.23 + 1.7)
        if lump > 1.1 then t = t + 1 elseif lump < -1.3 then t = t - 1 end
      end
      if math.abs(x + 0.5 - ACX) < 8 then t = 2 end                          -- the crown's base
      for y = top - 1 - t, top - 2 do add(x, y) end
    end
  end
  -- on the pillar capitals: a little heap in the crook where the band meets the capital
  for _, row in ipairs({ { 46, 7, 9 }, { 47, 6, 9 }, { 48, 5, 9 } }) do
    for x = row[2], row[3] do add(x, row[1]); add(W - 1 - x, row[1]) end
  end
  -- on the banner's top edge: a heap at each end, stopping short of RENO (x 49..126)
  for x = 18, 47 do
    local t = (x > 44) and 1 or 2
    if math.sin(x * 0.8) > 0.6 and x < 43 then t = t + 1 end
    for y = 52 - t, 51 do add(x, y); add(W - 1 - x, y) end
  end
  -- shade it and outline it
  local b = L.buffer(W, H)
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      if m[y][x] then
        local above, below = L.get(m, x, y - 1), L.get(m, x, y + 1)
        local c = C.snow
        if not above then c = C.snowTop
        elseif not below then c = C.snowShade end
        b[y][x] = c
      end
    end
  end
  for y = 0, H - 1 do
    for x = 0, W - 1 do
      if not m[y][x] and not steel(x, y) then
        for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }) do
          if L.get(m, x + d[1], y + d[2]) then b[y][x] = P.outline; break end
        end
      end
    end
  end
  return b
end

-- Falling snow: columns of flakes 16 px apart falling 1 px a frame, so frame 16 flows back into
-- frame 1. Small flakes are single pixels; the big ones are little crosses. Each column sways on
-- its own wavelength so the flakes never line up.
local SNOW = {
  { 4, 3, false, 1.2, 6 }, { 15, 11, true, 1.0, 8 }, { 27, 6, false, 1.5, 7 }, { 38, 14, true, 1.2, 9 },
  { 49, 2, false, 1.0, 5 }, { 62, 9, false, 1.4, 8 }, { 73, 13, true, 1.0, 6 }, { 101, 5, true, 1.3, 7 },
  { 112, 12, false, 1.0, 9 }, { 124, 1, false, 1.5, 6 }, { 136, 8, true, 1.2, 8 }, { 147, 15, false, 1.0, 5 },
  { 158, 4, true, 1.4, 7 }, { 170, 10, false, 1.2, 9 }, { 88, 7, false, 1.0, 6 },
}
local function snowfall(b, f)
  for i, s in ipairs(SNOW) do
    local x0, y0, big, amp, len = s[1], s[2], s[3], s[4], s[5]
    for k = -1, 6 do
      local y = y0 + f + 16 * k
      local x = x0 + math.floor(amp * math.sin(y / len + i) + 0.5)
      local pts = big and { { 0, 0, C.flake }, { -1, 0, C.flakeDim }, { 1, 0, C.flakeDim }, { 0, -1, C.flakeDim }, { 0, 1, C.flakeDim } }
        or { { 0, 0, C.flake } }
      for _, p in ipairs(pts) do
        if not onArch(x + p[1], y + p[2]) then L.set(b, x + p[1], y + p[2], p[3]) end
      end
    end
  end
end

-- A snow drift: a low mound, white on top, blue at the base, highest at the pillar end.
local function drift(w, h, fromRight)
  local b = L.buffer(w, h)
  for x = 0, w - 1 do
    local t = (fromRight and (w - 1 - x) or x) / (w - 1)
    local top = math.floor(h * (0.15 + 0.85 * t * t) + 0.5 * math.sin(x * 0.9))
    top = math.max(0, math.min(h - 1, top))
    for y = top, h - 1 do
      b[y][x] = (y == top) and C.snowTop or (y >= h - 1) and C.snowShade or C.snow
    end
  end
  return b
end

-- Snowman: three snowballs lit from the upper left, coal eyes and buttons, a carrot nose,
-- rosy cheeks, a blue bobble hat, a red scarf whose tail flutters, and stick arms; the right one
-- waves.
local function snowball(w, h, cx, cy, r)
  local s = L.buffer(w, h)
  L.eachDisc(cx, cy, r, function(x, y, dx, dy)
    local c = C.snow
    if dx + dy < -r * 0.75 then c = C.snowTop elseif dx + dy > r * 0.5 then c = C.snowShade end
    L.set(s, x, y, c)
  end)
  return s
end

local function snowman(f)
  local w, h = 26, 27
  local b = L.buffer(w, h)
  local cx = 13
  -- stick arms behind the body: the left one still, the right one waving
  L.line(b, 9, 13, 4, 10, C.stick); L.set(b, 3, 9, C.stick); L.set(b, 3, 11, C.stick)
  local lift = ({ 0, 1, 2, 1 })[(f // 2) % 4 + 1]
  local hy = 10 - lift * 2
  L.line(b, 17, 13, 21, hy, C.stick); L.set(b, 22, hy - 1, C.stick); L.set(b, 22, hy + 1, C.stick)
  L.stamp(b, snowball(w, h, cx, 21.5, 5.5), 0, 0)
  local mid = snowball(w, h, cx, 14, 4.2)
  L.set(mid, cx, 13, C.coal); L.set(mid, cx, 15, C.coal)                  -- buttons
  L.stamp(b, mid, 0, 0)
  -- head and hat together, so the brim sits right on the head
  local head = snowball(w, h, cx, 7, 3.7)
  local hat = L.map({ "...w...", "..lhd..", ".lhhhd.", "bbbbbbb" },
    { w = C.pom, h = C.hat, l = C.hatLight, d = C.hatDark, b = C.hatLight })
  L.blit(head, hat, cx - 3, 1)
  L.set(head, cx - 2, 6, C.coal); L.set(head, cx + 1, 6, C.coal)       -- eyes
  L.set(head, cx, 7, C.carrot); L.set(head, cx + 1, 7, C.carrot); L.set(head, cx + 2, 7, C.carrotDark)
  L.set(head, cx - 3, 8, C.blush); L.set(head, cx + 2, 8, C.blush)
  L.stamp(b, head, 0, 0)
  -- scarf round the neck, with a tail down the left side that flutters
  local scarf = L.buffer(9, 6)
  L.fillRect(scarf, 0, 0, 8, 1, C.scarf); L.fillRect(scarf, 0, 0, 3, 0, C.scarfLight)
  L.fillRect(scarf, 6, 1, 8, 1, C.scarfDark)
  local flap = ({ 0, 1, 1, 0, 0, -1, -1, 0 })[f % 8 + 1]
  L.fillRect(scarf, 1, 2, 2, 3, C.scarf); L.set(scarf, 2, 2, C.scarfDark)
  L.set(scarf, 1 + math.min(flap, 0), 4, C.scarfLight); L.set(scarf, 2 + math.max(flap, 0), 4, C.scarf)
  L.stamp(b, scarf, cx - 4, 10)
  return b
end

-- Cardinal: a round red bird facing left, with a tall crest, a black mask round a bright eye, an
-- orange beak, a darker wing and a tail cocked out behind.
local function cardinal()
  return L.map({
    "...r......",
    "..rr......",
    "..lrr.....",
    ".lrrrr....",
    "kkwkrr....",
    "ookkrrr...",
    ".kklrrdd..",
    "..llrdddtt",
    "..llrrddtt",
    "...lrrd..t",
    "....y.y...",
  }, { r = C.cardinal, l = C.cardinalLight, d = C.cardinalDark, t = C.cardinalDark, k = "#2a1a26",
    w = P.ink, o = C.beak, y = C.beak })
end

local HOP = { 0, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 0, 1, 2, 1, 0 }

local frames = {}
local snowPile = pile()
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  snowfall(b, f)
  L.blit(b, snowPile, 0, 0)
  -- foot of the left pillar: a drift with the snowman standing in it
  L.blit(b, snowman(f), 18, 69)
  L.stamp(b, drift(18, 4, false), 19, 92)
  -- foot of the right pillar: a drift with a cardinal hopping on it
  L.stamp(b, drift(24, 6, true), 133, 90)
  L.stamp(b, cardinal(), 140, 81 - HOP[f + 1])
  frames[f + 1] = b
end
L.saveStrip(frames, "season-01", MS)
