@echo off
cd /d "D:\SEMESTER 5\APLIKASI WEB\TILIEK"

echo ========================================
echo       TILIEK AUTOMATIC PROCESS
echo ========================================

echo.
echo [1/4] Crawling berita...
"D:\SEMESTER 5\APLIKASI WEB\TILIEK\venv\Scripts\python.exe" crawler.py
if errorlevel 1 goto error

echo.
echo [2/4] Preprocessing berita...
"D:\SEMESTER 5\APLIKASI WEB\TILIEK\venv\Scripts\python.exe" -m processing.preprocessing
if errorlevel 1 goto error

echo.
echo [3/4] Analisis sentimen IndoBERT...
"D:\SEMESTER 5\APLIKASI WEB\TILIEK\venv\Scripts\python.exe" -m processing.sentiment_analysis
if errorlevel 1 goto error

echo.
echo [4/4] Clustering berita...
"D:\SEMESTER 5\APLIKASI WEB\TILIEK\venv\Scripts\python.exe" -m processing.clustering
if errorlevel 1 goto error

echo.
echo ========================================
echo       SEMUA PROSES BERHASIL
echo ========================================

exit /b 0

:error
echo.
echo PROSES GAGAL. Periksa pesan error di atas.
exit /b 1
