setlocal EnableDelayedExpansion

echo off

set fname=%1
set count=%2

for /L %%i in (1,1,%count%) do echo !RANDOM! >> %fname%

echo on
exit /b 0
