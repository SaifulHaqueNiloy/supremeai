@echo off
echo.
echo Building SupremeAI VSCode Extension...
echo.

REM Change to the extension directory
cd /d "c:\Users\n\supremeai\supremeai_2.0\tools\vscode-extension"

echo Compiling TypeScript...
pnpm compile

if %ERRORLEVEL% NEQ 0 (
    echo Error occurred during compilation!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Packaging extension...
pnpm package-ext

if %ERRORLEVEL% NEQ 0 (
    echo Error occurred during packaging!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo SupremeAI VSCode Extension built successfully!
echo VSIX file location: c:\Users\n\supremeai\supremeai_2.0\tools\vscode-extension\supremeai-vscode-6.0.0.vsix
echo.

pause
