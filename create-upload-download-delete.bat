setlocal EnableExtensions
call setenv.bat

gin info %username%
echo %password%| gin login %username%

set "testroot=%tmp%\gintest"
md "%testroot%"
cd /D "%testroot%"

rem get a unique directory name for the repo
:uniqdirloop
set reponame=gin-test-win-%RANDOM%
if exist "%reponame%" goto :uniqdirloop

set repopath=%username%/%reponame%

gin create %reponame%
pushd %reponame%

rem create random files
set fname1=file-%RANDOM%.rnd
call %loc%\winutil\mkfile %fname1% 50
set fname2=file-%RANDOM%.rnd
call %loc%\winutil\mkfile %fname2% 50
set fname3=file-%RANDOM%.rnd
call %loc%\winutil\mkfile %fname3% 50
set fname4=file-%RANDOM%.rnd
call %loc%\winutil\mkfile %fname4% 50
set fname5=file-%RANDOM%.rnd
call %loc%\winutil\mkfile %fname5% 50

gin ls

rem should be 5
gin ls -s | grep "^??" | wc -l

gin upload %fname1% %fname5%
gin ls

rem should be 2
gin ls -s | grep "^OK" | wc -l
rem should be 3
gin ls -s | grep "^??" | wc -l

gin rmc %fname1%
gin ls
rem
rem should be 1
gin ls -s | grep "^NC" | wc -l
rem should be 1
gin ls -s | grep "^OK" | wc -l
gin upload
gin rmc
gin ls
rem should be 5
gin ls -s | grep "^NC" | wc -l

gin annex uninit
popd
rd /s /q %reponame%
echo %repopath%| gin delete %repopath%
