@echo off
cmd /c "set PYTHONPATH=%PYTHONPATH%;D:\Python\uglybetting\"
cmd /c "activate uglybetting & cd /d D:\Python\uglybetting\src\scripts\ & python update_nap_intraday.py"
