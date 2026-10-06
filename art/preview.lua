-- Preview the seasonal decorations over the arch and the header's sunset sky.
-- Not part of the page; it only writes the paths you give it.
--   aseprite -b --script-param month=10 --script-param out=/tmp/oct.png --script art/preview.lua
--     one month: frames 1, 5, 9 and 13 side by side at 2x (frames=1,3,5 and scale=3 change that)
--   aseprite -b --script-param month=10 --script-param out=/tmp/oct.gif --script art/preview.lua
--     one month, animated at 3x
--   aseprite -b --script-param month=all --script-param out=/tmp/year.gif --script art/preview.lua
--     every month in a 3x4 grid, January to December, animated at 2x
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local W, H = 176, 96
local SEASON_FRAMES, ARCH_FRAMES, MS = 16, 8, 120

-- docs/style.css .sky: hard colour bands down the header. The arch sits near the top of a header
-- about 136 art pixels tall (padding, the arch, the title and the tagline).
local BANDS = { { 0.22, "#21183a" }, { 0.42, "#352049" }, { 0.60, "#5a2a55" },
  { 0.74, "#8c3b58" }, { 0.86, "#c95a4e" }, { 1.00, "#f0974f" } }
local function sky(y)
  local t = (y + 6) / 136
  for _, b in ipairs(BANDS) do if t < b[1] then return b[2] end end
  return BANDS[#BANDS][2]
end

local function load(rel)
  local img = Image { fromFile = L.path(rel) }
  assert(img, "can't read " .. rel)
  return img
end

local function pixel(img, x, y)
  local v = img:getPixel(x, y)
  local pc = app.pixelColor
  local a = pc.rgbaA(v)
  if a == 0 then return nil end
  return L.hex(pc.rgbaR(v), pc.rgbaG(v), pc.rgbaB(v), a)
end

local arch = load("docs/art/arch.png")

-- Frame f (1-based) of a month, composited: sky, arch frame, decorations.
local function scene(season, f)
  local b = L.buffer(W, H)
  for y = 0, H - 1 do for x = 0, W - 1 do b[y][x] = sky(y) end end
  local af = (f - 1) % ARCH_FRAMES
  local top = L.buffer(W, H)
  for y = 0, H - 1 do for x = 0, W - 1 do top[y][x] = pixel(arch, af * W + x, y) end end
  L.blit(b, top, 0, 0)
  if season then
    local s = L.buffer(W, H)
    for y = 0, H - 1 do for x = 0, W - 1 do s[y][x] = pixel(season, (f - 1) * W + x, y) end end
    L.blit(b, s, 0, 0)
  end
  return b
end

local function paste(dst, src, ox, oy, scale)
  for y = 0, src.h - 1 do
    for x = 0, src.w - 1 do
      L.fillRect(dst, ox + x * scale, oy + y * scale, ox + x * scale + scale - 1, oy + y * scale + scale - 1, src[y][x])
    end
  end
end

local function toImage(b)
  local img = Image(b.w, b.h, ColorMode.RGB)
  for y = 0, b.h - 1 do for x = 0, b.w - 1 do img:drawPixel(x, y, L.rgba(b[y][x] or "#000000")) end end
  return img
end

local month, out = app.params.month, app.params.out
assert(month and out, "pass --script-param month=NN|all and --script-param out=<path>")

if month == "all" then
  local seasons = {}
  for m = 1, 12 do seasons[m] = load(string.format("docs/art/season-%02d.png", m)) end
  local scale = tonumber(app.params.scale or "2")
  local spr = Sprite(3 * W * scale, 4 * H * scale, ColorMode.RGB)
  for f = 2, SEASON_FRAMES do spr:newEmptyFrame() end
  for f = 1, SEASON_FRAMES do
    local sheet = L.buffer(3 * W * scale, 4 * H * scale)
    for m = 1, 12 do
      paste(sheet, scene(seasons[m], f), ((m - 1) % 3) * W * scale, ((m - 1) // 3) * H * scale, scale)
    end
    spr:newCel(spr.layers[1], spr.frames[f], toImage(sheet), Point(0, 0))
    spr.frames[f].duration = MS / 1000
  end
  spr:saveCopyAs(out)
  spr:close()
elseif out:match("%.gif$") then
  local season = load(string.format("docs/art/season-%02d.png", tonumber(month)))
  local scale = tonumber(app.params.scale or "3")
  local spr = Sprite(W * scale, H * scale, ColorMode.RGB)
  for f = 2, SEASON_FRAMES do spr:newEmptyFrame() end
  for f = 1, SEASON_FRAMES do
    local big = L.buffer(W * scale, H * scale)
    paste(big, scene(season, f), 0, 0, scale)
    spr:newCel(spr.layers[1], spr.frames[f], toImage(big), Point(0, 0))
    spr.frames[f].duration = MS / 1000
  end
  spr:saveCopyAs(out)
  spr:close()
else
  local season = load(string.format("docs/art/season-%02d.png", tonumber(month)))
  local scale = tonumber(app.params.scale or "2")
  local list = {}
  for f in (app.params.frames or "1,5,9,13"):gmatch("%d+") do list[#list + 1] = tonumber(f) end
  local gap = 4
  local sheet = L.buffer(#list * (W * scale + gap) - gap, H * scale)
  for i, f in ipairs(list) do paste(sheet, scene(season, f), (i - 1) * (W * scale + gap), 0, scale) end
  local spr = Sprite(sheet.w, sheet.h, ColorMode.RGB)
  spr.cels[1].image = toImage(sheet)
  spr:saveCopyAs(out)
  spr:close()
end
print("wrote " .. out)
