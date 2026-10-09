-- icons.png: the page's little pixel icons, one row of 17 cells of 12x12 (204x12), shown at 2x.
-- The order is fixed: ICONS in docs/lib.js and the .ico-* rules in docs/style.css depend on it.
--   0 baby  1 car  2 house  3 book  4 music  5 leaf  6 warn  7 clear  8 mostly-clear
--   9 partly-cloudy  10 cloudy  11 fog  12 showers  13 rain  14 snow  15 thunder  16 calendar
-- The weather icons share one sun and one cloud. Light comes from the upper left.
-- Run from the repo root:
--   /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/icons.lua
-- Writes art/icons.aseprite and docs/art/icons.png.
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local CELL = 12

local C = {
  skin = "#ffd2ad", skinLight = "#ffeadb", skinShade = "#e9a47e", cheek = "#ff8fa8", mouth = "#d9536b",
  hair = "#c9773a",
  glass = "#9fd8ff", glassLight = "#e2f5ff", tyre = "#4b4159",
  roof = "#e2681c", roofLight = "#f79a45", roofDark = "#a8461a", wallShade = "#d8c3a8",
  door = "#8a5a3c", doorDark = "#5e3b28",
  pinkDark = "#c2448a", pageShade = "#e3cdb4", text = "#f29cc6",
  leafLight = "#c3f08f", leaf = "#86d663", leafMid = "#55ad4c", leafDark = "#3a7f3f",
  vein = "#e3f9b8", stem = "#5d8f3c",
  sun = "#ffd23f", sunShade = "#ffa53a", ray = "#ffbf3f",
  cloud = "#d9d2f0", cloudLight = "#fbf8ff", cloudShade = "#a59cc9",
  storm = "#a99fcb", stormLight = "#cfc7ea", stormShade = "#776ea0",
  drop = "#68c1ff", dropLight = "#c4e9ff", snow = "#ffffff",
}

local BABY = L.map({
  ".......hh...",
  "......h..h..",
  "...lllhss...",
  ".llssssssss.",
  ".lssssssssd.",
  "lssssssssssd",
  "lssesssssesd",
  "sccssssssccd",
  "sssssssssssd",
  ".ssssmmsssd.",
  "..dssssssd..",
  "....dddd....",
}, { s = C.skin, l = C.skinLight, d = C.skinShade, h = C.hair, e = P.outline, c = C.cheek, m = C.mouth })

local CAR = L.map({
  "............",
  "............",
  "...llllll...",
  "..lGgrGggr..",
  ".lGggrGgggr.",
  "llllllllllll",
  "lrrrrrrrrrry",
  "rrrrrrrrrrrr",
  "ddttddddttdd",
  ".thht..thht.",
  ".thht..thht.",
  "..tt....tt..",
}, { r = P.red, l = P.redLight, d = P.redDark, g = C.glass, G = C.glassLight, t = C.tyre,
  h = P.silver, y = P.goldLight })

local HOUSE = L.map({
  ".....RR.Cc..",
  "....RrrDCc..",
  "...RrrrrDD..",
  "..RrrrrrrD..",
  ".RrrrrrrrrD.",
  "RrrrrrrrrrrD",
  ".WWWWWWWWWW.",
  ".wffffwoowW.",
  ".wfYyfwoowW.",
  ".wfyyfwookW.",
  ".wffffwoowW.",
  ".wwwwwwoowW.",
}, { r = C.roof, R = C.roofLight, D = C.roofDark, c = P.red, C = P.redLight, w = P.ink, W = C.wallShade,
  f = C.doorDark, y = P.gold, Y = P.goldLight, o = C.door, k = P.gold })

local BOOK = L.map({
  "............",
  ".www....www.",
  "pwwwwsswwwwp",
  "pwtttsstttwp",
  "pwwwwsswwwwp",
  "pwtttsstttwp",
  "pwwwwsswwwwp",
  "pwtttsstttwp",
  "pwwwwsswwwwp",
  "pwwwwsswwwwp",
  "pppwwsswwppp",
  "...dddddd...",
}, { p = P.pink, d = C.pinkDark, w = P.ink, s = C.pageShade, t = C.text })

-- The "music" cell (live music) is a pair of beamed eighth notes in the arch's neon pink.
local NOTES = L.map({
  ".......lllll",
  "...lllllyyyy",
  "...yyyyyyyyd",
  "...lyddd..ly",
  "...ly.....ly",
  "...ly.....ly",
  "...ly.....ly",
  "...ly.....ly",
  "...ly...llyy",
  ".llyy..lyyyd",
  "lyyyd..yyyd.",
  "yyyd........",
}, { y = P.neon, l = P.neonCore, d = P.neonDim })

local LEAF = L.map({
  "..........lg",
  ".......lllvm",
  ".....llggvm.",
  "....lgggvmd.",
  "...lgggvmmd.",
  "...lggvmmd..",
  "..lggvmmmd..",
  "..lgvmmmd...",
  "..lvmmdd....",
  ".lvmdd......",
  ".s..........",
  "s...........",
}, { l = C.leafLight, g = C.leaf, m = C.leafMid, d = C.leafDark, v = C.vein, s = C.stem })

local WARN = L.map({
  ".....ly.....",
  "....lyyd....",
  "....lkkd....",
  "...lykkyd...",
  "...lykkyd...",
  "..lyykkyyd..",
  "..lyykkyyd..",
  ".lyyyyyyyyd.",
  ".lyyykkyyyd.",
  "lyyyykkyyyyd",
  "lyyyyyyyyyyd",
  "dddddddddddd",
}, { y = P.gold, l = P.goldLight, d = P.goldDark, k = P.outline })

-- The weather family: one sun and one cloud (plus a smaller cloud), drawn into each cell.
-- The sun is a 6x6 disc with rays; sun(b, x, y, rays) draws the disc with its top-left at
-- (x, y) and the rays named in the string (n ne e se s sw w nw, or "all").
local DISC = L.map({
  ".SSss.",
  "SSssss",
  "Sssssd",
  "sssssd",
  "ssssdd",
  ".sddd.",
}, { S = P.goldLight, s = C.sun, d = C.sunShade })
local RAYS = {
  n = { { 2, -3 }, { 3, -3 }, { 2, -2 }, { 3, -2 } }, s = { { 2, 7 }, { 3, 7 }, { 2, 8 }, { 3, 8 } },
  w = { { -3, 2 }, { -2, 2 }, { -3, 3 }, { -2, 3 } }, e = { { 7, 2 }, { 8, 2 }, { 7, 3 }, { 8, 3 } },
  nw = { { -2, -2 }, { -1, -1 } }, ne = { { 7, -2 }, { 6, -1 } },
  sw = { { -2, 7 }, { -1, 6 } }, se = { { 7, 7 }, { 6, 6 } },
}
local function sun(b, x, y, rays)
  if rays == "all" then rays = "n ne e se s sw w nw" end
  for r in rays:gmatch("%a+") do
    for _, p in ipairs(RAYS[r]) do L.set(b, x + p[1], y + p[2], C.ray) end
  end
  L.blit(b, DISC, x, y)
end

local CLOUD_ROWS = {
  "......wwc...",
  "..ww.wcccc..",
  ".wccccccccd.",
  "wccccccccccd",
  "cccccccccccd",
  "cccccccccccd",
  ".dddddddddd.",
}
local SMALL_CLOUD_ROWS = {
  "...wwc..",
  ".wwcccc.",
  "wccccccd",
  "cccccccd",
  ".dddddd.",
}
local function cloud(rows, storm)
  return L.map(rows, storm and { w = C.stormLight, c = C.storm, d = C.stormShade }
    or { w = C.cloudLight, c = C.cloud, d = C.cloudShade })
end

local BOLT = L.map({
  "...lly",
  "..lyy.",
  ".lyyyy",
  "...yy.",
  "..yy..",
  "..y...",
  ".y....",
}, { y = P.gold, l = P.goldLight })

local function cell() return L.buffer(CELL, CELL) end

-- Rain streaks: each {x, y} is the top of a two-pixel streak falling down and to the left.
local function drops(b, list)
  for _, d in ipairs(list) do
    L.set(b, d[1], d[2], C.dropLight)
    L.set(b, d[1] - 1, d[2] + 1, C.drop)
  end
end
-- Snowflakes: {x, y, big}; a big one is a little plus.
local function flakes(b, list)
  for _, f in ipairs(list) do
    local x, y, big = f[1], f[2], f[3]
    L.set(b, x, y, C.snow)
    if big then
      for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }) do L.set(b, x + d[1], y + d[2], C.cloud) end
    end
  end
end

-- A band of mist along row y, lit at its left end.
local function mist(b, y, x0, x1)
  for x = x0, x1 do L.set(b, x, y, x == x0 and C.cloudLight or x == x1 and C.cloudShade or C.cloud) end
end

local ICONS = {}
local function add(b) ICONS[#ICONS + 1] = b end

add(BABY); add(CAR); add(HOUSE); add(BOOK); add(NOTES); add(LEAF); add(WARN)

-- 7 clear
do
  local b = cell()
  sun(b, 3, 3, "all")
  add(b)
end

-- 8 mostly clear: the sun with a small cloud over its lower right
do
  local b = cell()
  sun(b, 3, 3, "all")
  L.stamp(b, cloud(SMALL_CLOUD_ROWS), 4, 7)
  add(b)
end

-- 9 partly cloudy: the sun peeks out from behind the cloud
do
  local b = cell()
  sun(b, 6, 2, "n nw w")
  L.stamp(b, cloud(CLOUD_ROWS), 0, 5)
  add(b)
end

-- 10 cloudy: a shaded cloud behind the main one
do
  local b = cell()
  L.stamp(b, cloud(SMALL_CLOUD_ROWS, true), 4, 1)
  L.stamp(b, cloud(CLOUD_ROWS), 0, 5)
  add(b)
end

-- 11 fog: the top of the cloud, dissolving into bands of mist
do
  local b = cell()
  L.stamp(b, cloud({ table.unpack(CLOUD_ROWS, 1, 5) }), 0, 0)
  mist(b, 6, 0, 9); mist(b, 8, 2, 11); mist(b, 10, 0, 8)
  add(b)
end

-- 12 showers: sun behind the cloud and a few drops
do
  local b = cell()
  sun(b, 6, 0, "w")
  L.stamp(b, cloud(CLOUD_ROWS), 0, 3)
  drops(b, { { 2, 10 }, { 6, 10 }, { 10, 10 } })
  add(b)
end

-- 13 rain
do
  local b = cell()
  L.stamp(b, cloud(CLOUD_ROWS), 0, 0)
  drops(b, { { 2, 8 }, { 6, 8 }, { 10, 8 }, { 4, 10 }, { 8, 10 } })
  add(b)
end

-- 14 snow
do
  local b = cell()
  L.stamp(b, cloud(CLOUD_ROWS), 0, 0)
  flakes(b, { { 2, 9, true }, { 8, 9, true }, { 5, 11 }, { 11, 11 } })
  add(b)
end

-- 15 thunder: a darker cloud and a lightning bolt
do
  local b = cell()
  L.stamp(b, cloud(CLOUD_ROWS, true), 0, 0)
  L.stamp(b, BOLT, 3, 5)
  add(b)
end

-- 16 calendar ("More local calendars"): a page with ring tabs and one day picked out
add(L.map({
  "..s......s..",
  "RRsRRRRRRsRR",
  "rrrrrrrrrrrr",
  "dddddddddddd",
  "wwwwwwwwwwwW",
  "wgwgwgwgwgwW",
  "wwwwwwwwwwwW",
  "wgwgwyywgwgW",
  "wwwwwyywwwwW",
  "wgwgwgwgwgwW",
  "wwwwwwwwwwwW",
  "WWWWWWWWWWWW",
}, { s = P.silver, R = P.redLight, r = P.red, d = P.redDark, w = P.ink, W = C.wallShade, g = P.muted, y = P.gold }))

assert(#ICONS == 17, "expected 17 icons, got " .. #ICONS)
local strip = L.buffer(CELL * #ICONS, CELL)
for i, b in ipairs(ICONS) do
  assert(b.w == CELL and b.h == CELL, "icon " .. (i - 1) .. " is not 12x12")
  L.blit(strip, b, (i - 1) * CELL, 0)
end
L.saveStill(strip, "icons")
