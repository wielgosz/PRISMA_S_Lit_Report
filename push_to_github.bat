@echo off
cd /d "C:\Users\benwi\OneDrive\Documents\00-Work\Claude\PRISMA-S"
echo Working directory: %CD%
echo.

echo --- Initializing git repo ---
git init
echo.

echo --- Setting remote ---
git remote add origin https://github.com/wielgosz/PRISMA_S_Lit_Report.git
echo.

echo --- Staging all files ---
git add .
echo.

echo --- Committing ---
git commit -m "v1.2.0 — installable package with wizard, Drive support, PRISMA-S compliance sheet"
echo.

echo --- Setting branch to main ---
git branch -M main
echo.

echo --- Pushing to GitHub ---
git push -u origin main --force
echo.

echo === DONE ===
pause
