See: https://wyday.com/limelm/help/using-turboactivate-with-electron-nodejs/#extract-ta

File layout for a project might look something like this:


main.js
turboactivate.js
native
...Windows
......systa.exe
......TurboActivate.dll
......TurboActivate.dat
...Linux
......systa
......libTurboActivate.so
......TurboActivate.dat
...FreeBSD
......systa
......libTurboActivate.so
......TurboActivate.dat
...Mac
......systa
......libTurboActivate.dylib
......TurboActivate.dat