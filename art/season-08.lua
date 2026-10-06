-- season-08.png: August decorations over the arch, for Hot August Nights, Reno's classic-car week.
-- 16 frames of 176x96, 120 ms each, transparent except for the decorations (docs/style.css lays
-- them over arch.png). A turquoise 1950s convertible with tail fins and whitewalls parks under the
-- banner: a glint runs along its chrome, it hops on its suspension once a loop, and little exhaust
-- puffs drift from its tailpipe. A string of checkered pennants hangs between the pillars.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/season-08.lua
-- Writes art/season-08.aseprite and docs/art/season-08.png (a 2816x96 strip).
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local W, H, FRAMES, MS = 176, 96, 16, 120
local TAU = 2 * math.pi

local C = {
  bodyLight = "#8fe3d6", body = "#3bbcb4", bodyShade = "#26928f", bodyDeep = "#1a6b6e",
  cream = P.ink, chrome = P.silver, chromeShade = P.steel, shine = "#ffffff",
  seatLight = P.redLight, seat = P.red, seatShade = P.redDark,
  glass = "#bfe6ef", headlight = P.goldLight, taillight = "#ff5b5b",
  tyre = "#2b2333", whitewall = P.ink,
  puff = "#efe3f2", puffShade = "#c4b2cf",
  string = P.muted, check = P.ink, checkDark = "#2b2333", flagGold = P.gold, flagTeal = "#3bbcb4",
}

local function wave(f, amp, phase) return math.floor(amp * math.sin(TAU * f / FRAMES + (phase or 0)) + 0.5) end

-- The car body, facing right, without its wheels: tail fins with tall taillights at the back, red
-- seats and a wraparound windshield above the belt line, a cream cove and a chrome spear down the
-- side, two doors, and chrome bumpers at each end. The wheel arches are cut out of it below.
local BODY = {
  "...................................CCC..................",
  ".oT................................gWgC.................",
  ".otTT............RRRr......RRRr.....ggWC................",
  ".otttTTTT.......Rrrrrq....Rrrrrq.k...gggC...............",
  ".otttttttTTTTT..Rrrrrq....Rrrrrq..k...gggC..............",
  ".ottttttttttttTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.........",
  ".TtttttttttttttttttttttdttttttttttttdttttttttttTTTTTTCC.",
  ".TttcccccccccccccttttttdtCttttttttttdttttttttttttttttCy.",
  ".TttcccccccccccccccctttdttttttttttttdttttttttttttttttCy.",
  ".TttCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCsttts.",
  "WCCddddddddddddddddddddDddddddddddddDddddddddddddddddWCC",
  "CCCddddddddddddddddddddDddddddddddddDddddddddddddddddCCC",
  "sssddddddddddddddddddddDddddddddddddDddddddddddddddddsss",
  ".DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD..",
  "...DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD....",
}
local WHEELS, AXLE = { 13, 43 }, 15   -- wheel centres in car pixels
local function body()
  local b = L.map(BODY, {
    T = C.bodyLight, t = C.body, d = C.bodyShade, D = C.bodyDeep, c = C.cream,
    C = C.chrome, s = C.chromeShade, W = C.shine, g = C.glass, k = P.outline,
    R = C.seatLight, r = C.seat, q = C.seatShade, o = C.taillight, y = C.headlight,
  })
  for _, wx in ipairs(WHEELS) do
    L.eachDisc(wx, AXLE, 6.2, function(x, y) if y >= 10 then L.set(b, x, y, nil) end end)
  end
  return b
end

-- Whitewall tyre: a rim of dark rubber, a wide cream ring, and a chrome hubcap lit from the upper left.
local function wheel()
  local b = L.buffer(10, 10)
  L.eachDisc(5, 5, 5, function(x, y, dx, dy)
    local r = math.sqrt(dx * dx + dy * dy)
    local c = C.tyre
    if r < 1.9 then c = (dx + dy < -0.4) and C.shine or C.chrome
    elseif r < 2.6 then c = C.chromeShade
    elseif r < 3.9 then c = C.whitewall end
    L.set(b, x, y, c)
  end)
  return b
end

-- A four-point sparkle; size 2 is the big star, 1 a small cross, 0 a single pixel.
local function sparkle(b, x, y, size)
  L.set(b, x, y, C.shine)
  for i = 1, size do
    local c = (i == size and size > 1) and P.goldLight or C.shine
    L.set(b, x - i, y, c); L.set(b, x + i, y, c); L.set(b, x, y - i, c); L.set(b, x, y + i, c)
  end
end

-- The glint's path along the chrome, in car pixels: the rear bumper, then down the spear.
local GLINT = { { 1, 11 } }
for x = 4, 44, 4 do GLINT[#GLINT + 1] = { x, 9 } end
-- Frames 4..15 sweep the glint along GLINT; frames 0..2 finish with a star on the headlight.
local function glint(b, f, ox, oy)
  if f <= 2 then
    sparkle(b, ox + 54, oy + 7, 2 - f)
  elseif f >= 4 then
    local p = GLINT[f - 3]
    local x, y = ox + p[1], oy + p[2]
    L.set(b, x - 1, y, C.shine); L.set(b, x + 1, y, C.shine)
    sparkle(b, x, y, 1)
  end
end

-- Body lift above the wheels each frame: a little hop and a rebound once a loop.
local HOP = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0, 1, 0, 0 }

-- Exhaust puffs: little clouds that swell from a dot to a two-bump puff and shrink away again.
local PUFFS = {
  { "pp", "ps" },
  { ".pp.", "ppps", ".ss." },
  { ".ppp.", "pppps", "pppss", ".sss." },
  { ".pp.pp.", "pppppps", "pppppss", ".sssss." },
}
local PUFF_AGE = { 1, 2, 3, 4, 4, 3, 2, 1 }   -- puff size by age; a puff lives 8 frames
local PUFF_BIRTH = { 13, 9, 5, 1 }
local function puff(size) return L.map(PUFFS[size], { p = C.puff, s = C.puffShade }) end

-- A pennant pointing down: checks, or plain gold or teal with a lit left edge. sway nudges the tip.
local PENNANT = { "#####", "#####", ".###.", ".###.", "..#.." }
local function pennant(style, sway)
  local b = L.buffer(7, 5)
  for y, row in ipairs(PENNANT) do
    for x = 1, #row do
      if row:sub(x, x) == "#" then
        local px, py = x - 1, y - 1
        local c
        if style == "check" then c = ((px + py) % 2 == 0) and C.check or C.checkDark
        else
          c = style == "gold" and C.flagGold or C.flagTeal
          if px == 0 then c = L.mix(c, "#ffffff", 0.35) end
        end
        L.set(b, 1 + px + ((py >= 3) and sway or 0), py, c)
      end
    end
  end
  return b
end

-- The pennant string droops from the inner edge of each pillar, just under the banner.
local X0, X1, Y0, SAG = 17, 158, 64, 3
local function sagY(x)
  local u = (x - (X0 + X1) / 2) / ((X1 - X0) / 2)
  return math.floor(Y0 + SAG * (1 - u * u) + 0.5)
end
local STYLES = { "check", "gold", "check", "teal" }

local frames = {}
for f = 0, FRAMES - 1 do
  local b = L.buffer(W, H)
  -- under the banner: a pennant string from pillar to pillar, the pennants swaying in turn
  for x = X0, X1 do L.set(b, x, sagY(x), C.string) end
  local i = 0
  for x = 24, X1 - 8, 11 do
    i = i + 1
    L.stamp(b, pennant(STYLES[(i - 1) % 4 + 1], wave(f, 1, i * 0.9)), x - 4, sagY(x) + 1)
  end
  -- the car, parked in the middle with its tyres on the ground (y = 95)
  local cx, cy = 60, 76
  for _, wx in ipairs(WHEELS) do L.stamp(b, wheel(), cx + wx - 5, cy + AXLE - 5) end
  local lift = HOP[f + 1]
  L.stamp(b, body(), cx, cy - lift)
  glint(b, f, cx, cy - lift)
  -- exhaust puffs drifting back and up from the tailpipe under the rear bumper
  for _, born in ipairs(PUFF_BIRTH) do
    local age = (f - born) % FRAMES
    local size = PUFF_AGE[age + 1]
    if size then
      local p = puff(size)
      local right, mid = cx - 2 - 1.4 * age, cy + 13 - lift - 0.6 * age
      L.stamp(b, p, math.floor(right - p.w + 1.5), math.floor(mid - p.h / 2 + 0.5))
    end
  end
  frames[f + 1] = b
end
L.saveStrip(frames, "season-08", MS)
