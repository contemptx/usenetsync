@echo off
REM Set NNTP environment variables for UsenetSync
REM Edit these values with your actual NNTP server details

set NNTP_SERVER=news.newshosting.com
set NNTP_USER=your_username_here
set NNTP_PASS=your_password_here

echo NNTP environment variables set:
echo NNTP_SERVER=%NNTP_SERVER%
echo NNTP_USER=%NNTP_USER%
echo NNTP_PASS=****

echo.
echo Now run: python run_test.py
