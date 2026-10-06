-- season-12.png: December decorations over the arch. 16 frames of 176x96, 120 ms each,
-- transparent except for the decorations (docs/style.css lays them over arch.png).
-- Light snow falls behind the arch, a swag of coloured string lights hangs under the banner with
-- its bulbs twinkling in turn, a little decorated tree with a twinkling star and presents stands
-- at the foot of the left pillar, and a stack of presents waits at the foot of the right one.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-12.lua
-- Writes art/season-12.aseprite and docs/art/season-12.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  snow = "#ffffff", snowDim = "#dfe8f5",
  tree = "#3f9a4c", treeLight = "#74c45e", treeDark = "#28663a", trunk = "#7c5a34", trunkDark = "#5a3e24",
  star = P.gold, starLight = P.goldLight,
  wire = "#27452f",
  -- string-light bulbs: lit and dim tones
  bulbs = {
    { "#ff5a66", "#9a2a36" }, { "#ffd36b", "#9a7a36" }, { "#6fe07a", "#2f7a3e" },
    { "#7cc4ff", "#36628f" }, { "#ff8ad0", "#9a3f72" },
  },
  halo = 72,                                   -- alpha of the glow round a bright bulb
  ornaments = { P.redLight, P.gold, "#7cc4ff", P.pink },
  -- presents: box, lit side, shade, ribbon
  presRed = { "#d42a3a", "#ec5562", "#8f1b2b", P.gold },
  presBlue = { "#4a86d0", "#7cb0ec", "#2f5a96", P.ink },
  presGold = { "#f2b632", "#ffe08a", "#c7902e", "#d42a3a" },
  presGreen = { "#3f9a4c", "#74c45e", "#28663a", "#ff8ad0" },
}

-- Where the arch is (art/arch.lua): the band between ellipses centred on (87.5, 58) with radii
-- 80x40 and 72x32, the crown, the pillars, RENO and the banner. Snow is hidden there, so it falls
-- behind the arch and never covers the lettering.
local function onArch(x, y)
  local function inE(rx, ry)
    local dx, dy = (x + 0.5 - 87.5) / rx, (y + 0.5 - 58) / ry
    return dx * dx + dy * dy <= 1
  end
  if y <= 59 and inE(81.5, 41.5) and not inE(70.5, 30.5) then return true end
  if x >= 74 and x <= 101 and y <= 24 then return true end                 -- the crown
  if y >= 48 and ((x >= 4 and x <= 19) or (x >= 156 and x <= 171)) then return true end
  if x >= 49 and x <= 126 and y >= 28 and y <= 54 then return true end
  return x >= 17 and x <= 158 and y >= 52 and y <= 62
end

-- Snow: columns of flakes that repeat every 16 px at 1 px a frame (small flakes) or every 32 px
-- at 2 px a frame (bigger, nearer flakes), so frame 16 flows back into frame 1. Each column sways
-- on its own wavelength, which keeps the flakes from lining up.
local SNOW = {
  { 3, 5, 1, 1.0, 6 }, { 24, 11, 1, 1.5, 7 }, { 33, 2, 2, 1.0, 9 }, { 46, 9, 1, 1.2, 5 },
  { 60, 14, 2, 1.5, 8 }, { 71, 4, 1, 1.0, 6 }, { 104, 7, 1, 1.4, 7 }, { 115, 12, 2, 1.2, 9 },
  { 129, 1, 1, 1.0, 5 }, { 141, 10, 1, 1.5, 8 }, { 152, 20, 2, 1.0, 6 }, { 166, 6, 1, 1.3, 7 },
  { 174, 13, 1, 1.0, 9 }, { 90, 3, 1, 1.0, 6 },
}
local function snow(b, f)
  for i, s in ipairs(SNOW) do
    local x0, y0, speed, amp, len = s[1], s[2], s[3], s[4], s[5]
    local period = 16 * speed
    for k = -1, math.ceil(H / period) do
      local y = y0 + speed * f + period * k
      local x = x0 + math.floor(amp * math.sin(y / len + i) + 0.5)
      local pts = speed == 2 and { { 0, 0 }, { 1, 0 }, { 0, 1 }, { 1, 1 } } or { { 0, 0 } }
      for _, p in ipairs(pts) do
        local px, py = x + p[1], y + p[2]
        if not onArch(px, py) then
          L.set(b, px, py, (speed == 2 and p[1] + p[2] == 2) and C.snowDim or C.snow)
        end
      end
    end
  end
end

-- The swag of lights: a dark wire sagging in four loops between hooks under the banner, with a
-- bulb every 6 px. A brightness wave runs along the string twice a loop, so the bulbs twinkle in
-- turn; the brightest get a soft glow.
local HOOKS = { 20, 54, 88, 122, 156 }
local function wireY(x)
  for i = 1, #HOOKS - 1 do
    local a, z = HOOKS[i], HOOKS[i + 1]
    if x >= a and x <= z then
      local t = (x - a) / (z - a) * 2 - 1
      return 62 + math.floor(5 * (1 - t * t) + 0.5)
    end
  end
end

local function lights(b, f)
  for x = HOOKS[1], HOOKS[#HOOKS] do L.set(b, x, wireY(x), C.wire) end
  for _, hx in ipairs(HOOKS) do L.set(b, hx, 62, P.outline); L.set(b, hx, 63, C.wire) end
  local n = 0
  for i = 1, #HOOKS - 1 do
    for x = HOOKS[i] + 4, HOOKS[i + 1] - 4, 6 do
      n = n + 1
      local tones = C.bulbs[(n - 1) % #C.bulbs + 1]
      local glow = math.sin(TAU * (2 * f / FRAMES - n / 7))
      local y = wireY(x) + 1
      L.set(b, x, y, C.wire)                                        -- socket
      local col = glow > -0.35 and tones[1] or tones[2]
      if glow > 0.55 then
        L.eachDisc(x + 0.5, y + 3, 3, function(px, py)
          if py > y and not L.get(b, px, py) then L.set(b, px, py, L.alpha(tones[1], C.halo)) end
        end)
      end
      L.fillRect(b, x, y + 1, x, y + 4, col)
      L.fillRect(b, x - 1, y + 2, x - 1, y + 3, col); L.fillRect(b, x + 1, y + 2, x + 1, y + 3, col)
      if glow > 0.55 then L.set(b, x - 1, y + 2, P.ink) end          -- glint
    end
  end
end

-- The tree: three tiers, each lit on the left and shaded on the right and under the tier above,
-- with baubles that wink on their own phases.
local function tree(f)
  local w, h = 19, 18
  local b = L.buffer(w, h)
  local cx = 9
  local tiers = { { 0, 5, 0.5, 4.6 }, { 4, 10, 2.0, 6.6 }, { 9, 15, 3.0, 9.0 } }
  for ti, t in ipairs(tiers) do
    for y = t[1], t[2] do
      local hw = t[3] + (t[4] - t[3]) * (y - t[1]) / (t[2] - t[1])
      for x = 0, w - 1 do
        local dx = x - cx
        if math.abs(dx) <= hw then
          local c = C.tree
          if dx < -hw * 0.5 and y > t[1] then c = C.treeLight end
          if dx > hw * 0.45 then c = C.treeDark end
          if ti > 1 and y <= t[1] + 1 then c = C.treeDark end
          b[y][x] = c
        end
      end
    end
    -- scalloped hem: notch every other pixel along the tier's bottom edge
    local hw = t[4]
    for x = math.ceil(cx - hw), math.floor(cx + hw) do
      if (x + ti) % 3 == 0 then L.set(b, x, t[2], nil) end
    end
  end
  L.fillRect(b, cx - 1, 16, cx + 1, 17, C.trunk)
  L.set(b, cx + 1, 16, C.trunkDark); L.set(b, cx + 1, 17, C.trunkDark)
  local balls = { { 9, 3 }, { 7, 5 }, { 11, 7 }, { 6, 9 }, { 9, 9 }, { 13, 10 }, { 4, 13 }, { 8, 12 }, { 11, 14 }, { 14, 14 }, { 6, 14 } }
  for i, o in ipairs(balls) do
    local c = C.ornaments[(i - 1) % #C.ornaments + 1]
    local on = math.sin(TAU * f / FRAMES * 2 + i * 1.9) > -0.6
    L.paint(b, o[1], o[2], on and c or L.mix(c, C.treeDark, 0.5))
  end
  return b
end

-- The star on top: five points with a pale heart that brightens, and glints that flash round it,
-- straight out and then diagonally.
local function star(f)
  local b = L.buffer(13, 13)
  local pulse = math.sin(TAU * f / FRAMES * 2 + 1.2)   -- already sparkling in frame 1
  local s = L.map({ "..g..", ".gGg.", "ggGgg", ".gGg.", "g...g" },
    { g = C.star, G = pulse > 0 and P.ink or C.starLight })
  local body = L.buffer(7, 7)
  L.blit(body, s, 1, 1)
  L.outline(body, P.outline)
  L.blit(b, body, 3, 3)
  if pulse > 0.3 then
    for _, d in ipairs({ { 0, -1 }, { 0, 1 }, { -1, 0 }, { 1, 0 } }) do
      L.set(b, 6 + d[1] * 5, 6 + d[2] * 5, C.starLight)
    end
  elseif pulse < -0.3 then
    for _, d in ipairs({ { -1, -1 }, { 1, -1 }, { -1, 1 }, { 1, 1 } }) do
      L.set(b, 6 + d[1] * 4, 6 + d[2] * 4, C.starLight)
    end
  end
  return b
end

-- A wrapped present with a ribbon both ways and a bow on top.
local function present(w, h, tones)
  local b = L.buffer(w, h + 2)
  for y = 2, h + 1 do
    for x = 0, w - 1 do
      local c = tones[1]
      if x == 0 or y == 2 then c = tones[2] elseif x == w - 1 or y == h + 1 then c = tones[3] end
      b[y][x] = c
    end
  end
  local rx = w // 2
  for y = 2, h + 1 do b[y][rx] = tones[4] end
  local ry = 2 + h // 2
  for x = 0, w - 1 do b[ry][x] = tones[4] end
  for _, d in ipairs({ { -2, 0 }, { -1, 0 }, { 1, 0 }, { 2, 0 }, { -1, 1 }, { 0, 1 }, { 1, 1 } }) do
    L.set(b, rx + d[1], d[2], tones[4])
  end
  return b
end

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  snow(b, f)
  -- under the banner: the string of lights
  lights(b, f)
  -- foot of the left pillar: the tree, its star, and two presents
  L.stamp(b, tree(f), 24, 78)
  L.blit(b, star(f), 27, 69)
  L.stamp(b, present(8, 5, C.presRed), 38, 89)
  L.stamp(b, present(5, 4, C.presBlue), 47, 90)
  -- foot of the right pillar: a stack of presents
  L.stamp(b, present(11, 7, C.presGold), 139, 87)
  L.stamp(b, present(7, 5, C.presGreen), 141, 80)
  L.stamp(b, present(6, 5, C.presBlue), 151, 89)
  frames[f + 1] = b
end
L.saveStrip(frames, "season-12", MS)
