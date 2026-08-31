@echo off
setlocal
echo Building Supply Chain Data Review Protocol v2.2 Desktop Runner
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pyinstaller --onedir --windowed ^
  --name SupplyChainDataReviewRunner ^
  --add-data "protocol_v2_1;protocol_v2_1" ^
  --add-data "templates;templates" ^
  --add-data "protocol_engine;protocol_engine" ^
  app.py
echo.
echo Build complete. See dist\SupplyChainDataReviewRunner\
