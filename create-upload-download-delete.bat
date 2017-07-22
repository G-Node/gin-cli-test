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

gin ls
gin upload
gin ls
gin rmc %fname1%
gin ls
gin rmc

git annex uninit
popd
rd /s /q %reponame%
echo %repopath%| gin delete %repopath%
