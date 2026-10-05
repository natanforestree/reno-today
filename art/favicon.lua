-- favicon.png: a neon pink R on a dark tile, 32x32.
-- Run: /Applications/Aseprite.app/Contents/MacOS/aseprite -b --script art/favicon.lua
local L = dofile(debug.getinfo(1, "S").source:sub(2):match("^(.-)[^/]+$") .. "lib.lua")
local P = L.P
local N, S, X0, Y0 = 32, 4, 6, 2
local R = { "####.", "#...#", "#...#", "####.", "#..#.", "#..#.", "#..##" }
local function lit(gx, gy)
  return gy >= 0 and gy < 7 and gx >= 0 and gx < 5 and R[gy + 1]:sub(gx + 1, gx + 1) == "#"
end

local b = L.buffer(N, N)
L.fillRect(b, 1, 0, N - 2, N - 1, P.night)           -- a tile with clipped corners
L.fillRect(b, 0, 1, N - 1, N - 2, P.night)
for gy = 0, 6 do
  for gx = 0, 4 do
    if lit(gx, gy) then L.fillRect(b, X0 + gx * S, Y0 + gy * S, X0 + gx * S + S - 1, Y0 + gy * S + S - 1, P.neon) end
  end
end
for gy = 0, 6 do
  for gx = 0, 4 do
    if lit(gx, gy) then
      local cx, cy = X0 + gx * S + 1, Y0 + gy * S + 1
      L.fillRect(b, cx, cy, cx + 1, cy + 1, P.neonCore)
      if lit(gx + 1, gy) then L.fillRect(b, cx + 2, cy, cx + S + 1, cy + 1, P.neonCore) end
      if lit(gx, gy + 1) then L.fillRect(b, cx, cy + 2, cx + 1, cy + S + 1, P.neonCore) end
    end
  end
end
L.saveStill(b, "favicon")
