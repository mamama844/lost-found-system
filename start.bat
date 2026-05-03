@echo off
chcp 65001 >nul
echo ========================================
echo   城市失物招领智能匹配系统
echo ========================================
echo.

if not exist "venv" (
    echo [错误] 虚拟环境不存在
    echo 请先打开命令行，执行以下命令：
    echo.
    echo   cd d:\qqxiazai\lost-found-system
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    pause
    exit /b 1
)

echo [启动服务器]
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.

call venv\Scripts\activate.bat
python run.py
pause
