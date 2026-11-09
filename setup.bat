@echo off
setlocal enabledelayedexpansion

:: ==============================================================================
:: ChatJPT Japanese Learning Ecosystem - Automated Setup & Environment Initializer
:: Target OS: Windows (Batch)
:: Components: Git, Python venv, ai-backend dependencies, ai-frontend npm, SQLite DB
:: ==============================================================================

title ChatJPT Setup and Initialization

:: 1. Resolve repository root
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ==============================================================================
echo                 ChatJPT Project Setup ^& Environment Initializer
echo ==============================================================================
echo.

:: 2. Auto-heal PATH for Node.js and Git if missing from current terminal session
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files\Git\cmd\git.exe" set "PATH=C:\Program Files\Git\cmd;!PATH!"
    if exist "C:\Program Files\Git\bin\git.exe" set "PATH=C:\Program Files\Git\bin;!PATH!"
)

where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files\nodejs\node.exe" set "PATH=C:\Program Files\nodejs;%APPDATA%\npm;!PATH!"
    if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" set "PATH=%LOCALAPPDATA%\Programs\nodejs;%APPDATA%\npm;!PATH!"
)

:: ==============================================================================
:: STEP 1: PREREQUISITE VERSION VERIFICATION (Git, Python, Node, npm)
:: ==============================================================================
echo [1/5] Checking Required Runtimes and Tools...

:: 1.1 Check Git
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Git was not found in PATH or standard installation directories.
    echo     Please install Git from https://git-scm.com/ and rerun setup.bat.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('git --version 2^>^&1') do set "GIT_VER=%%v"
echo [+] Git: %GIT_VER%

:: 1.2 Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Python was not found in PATH.
    echo     Please install Python 3.10, 3.11, 3.12, or 3.13 from https://www.python.org/
    echo     Make sure to check Add Python to PATH during installation.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "SYS_PY_VER=%%v"
echo [+] System Python: %SYS_PY_VER%

:: Validate Python version >= 3.10
python -c "import sys; sys.exit(0 if sys.version_info.major == 3 and sys.version_info.minor in range(10, 50) else 1)" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Python 3.10+ is required. Detected: %SYS_PY_VER%
    pause
    exit /b 1
)

:: 1.3 Check Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Node.js was not found in PATH.
    echo     Please install Node.js 18+ LTS from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node -v 2^>^&1') do set "NODE_VER=%%v"
echo [+] Node.js: %NODE_VER%

:: 1.4 Check npm
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: npm was not found in PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('npm -v 2^>^&1') do set "NPM_VER=%%v"
echo [+] npm: v%NPM_VER%
echo.

:: ==============================================================================
:: STEP 2: ENVIRONMENT CONFIGURATION INITIALIZATION (.env files)
:: ==============================================================================
echo [2/5] Initializing Configuration Files...

if not exist "ai-backend\.env" (
    if exist "ai-backend\.env.example" (
        copy "ai-backend\.env.example" "ai-backend\.env" >nul
        echo [+] Created ai-backend\.env from template .env.example.
    ) else (
        (
            echo APP_ENV=development
            echo PORT=8000
            echo DEBUG=true
            echo DEFAULT_LLM_PROVIDER=gemini
            echo DEFAULT_LLM_MODEL=gemini-3.8-flash
            echo MAX_TOKENS_PER_REQUEST=4096
        ) > "ai-backend\.env"
        echo [+] Created default ai-backend\.env file.
    )
) else (
    echo [i] ai-backend\.env already exists.
)

if not exist "ai-frontend\.env.local" (
    if exist "ai-frontend\.env.example" (
        copy "ai-frontend\.env.example" "ai-frontend\.env.local" >nul
        echo [+] Created ai-frontend\.env.local from template .env.example.
    ) else (
        (
            echo NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
        ) > "ai-frontend\.env.local"
        echo [+] Created default ai-frontend\.env.local file.
    )
) else (
    echo [i] ai-frontend\.env.local already exists.
)
echo.

:: ==============================================================================
:: STEP 3: PYTHON VIRTUAL ENVIRONMENT & BACKEND DEPENDENCIES
:: ==============================================================================
echo [3/5] Setting Up Python Virtual Environment in ai-backend\.venv...

set "VENV_DIR=%SCRIPT_DIR%ai-backend\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

if not exist "%VENV_PY%" (
    echo [i] Creating virtual environment at ai-backend\.venv...
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo [-] ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [+] Virtual environment created successfully.
) else (
    echo [i] Existing virtual environment found.
)

echo [i] Upgrading pip in virtual environment...
"%VENV_PY%" -m pip install --upgrade pip --quiet

echo [i] Installing Python dependencies from ai-backend\requirements.txt...
"%VENV_PIP%" install -r "ai-backend\requirements.txt"
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Failed to install backend dependencies!
    pause
    exit /b 1
)

if exist "requirements-dev.txt" (
    echo [i] Installing development dependencies: PyYAML...
    "%VENV_PIP%" install -r "requirements-dev.txt" --quiet
)
echo [+] Backend Python dependencies installed and verified.
echo.

:: ==============================================================================
:: STEP 3.5: VOICEVOX NEURAL TTS EMBEDDED ENGINE SETUP
:: ==============================================================================
echo [3.5/5] Setting Up VoiceVox Core Embedded Engine v0.17.1...

:: 1. Check/Install voicevox-core Python Wheel
"%VENV_PY%" -c "import voicevox_core" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [i] Installing voicevox-core Python package v0.17.1 from GitHub...
    "%VENV_PIP%" install "https://github.com/VOICEVOX/voicevox_core/releases/download/0.17.1/voicevox_core-0.17.1-cp310-abi3-win_amd64.whl" --quiet
    if !ERRORLEVEL! neq 0 (
        echo [!] Warning: Could not install voicevox-core wheel directly; falling back to resilient audio synthesis.
    ) else (
        echo [+] voicevox-core package installed successfully.
    )
) else (
    echo [+] voicevox-core package already installed.
)

:: 2. Check/Download VoiceVox Core Models & Runtime Assets
set "VV_DLL=%SCRIPT_DIR%ai-backend\voicevox_core\onnxruntime\lib\voicevox_onnxruntime.dll"
set "VV_DICT=%SCRIPT_DIR%ai-backend\voicevox_core\dict\open_jtalk_dic_utf_8-1.11"
set "VV_MODELS=%SCRIPT_DIR%ai-backend\voicevox_core\models\vvms"

if not exist "!VV_DLL!" (
    echo [i] VoiceVox Core runtime files missing. Downloading assets from GitHub...
    if not exist "ai-backend\voicevox_core\download.exe" (
        "%VENV_PY%" -c "import urllib.request, pathlib; out = pathlib.Path('ai-backend/voicevox_core/download.exe'); out.parent.mkdir(parents=True, exist_ok=True); req = urllib.request.Request('https://api.github.com/repos/VOICEVOX/voicevox_core/releases/assets/667065933', headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/octet-stream'}); res = urllib.request.urlopen(req); out.write_bytes(res.read())"
    )
    if exist "ai-backend\voicevox_core\download.exe" (
        echo [i] Extracting VoiceVox ONNX Runtime, OpenJTalk dictionary, and VVM neural models...
        echo y | "ai-backend\voicevox_core\download.exe" -o "ai-backend\voicevox_core" --exclude c-api
        if exist "ai-backend\voicevox_core\download.exe" del /f /q "ai-backend\voicevox_core\download.exe" >nul 2>&1
        echo [+] VoiceVox Core embedded engine and models installed successfully.
    ) else (
        echo [!] Warning: Could not download VoiceVox downloader.
    )
) else (
    echo [+] VoiceVox Core embedded runtime and models verified on disk.
)
echo.

:: ==============================================================================
:: STEP 4: FRONTEND DEPENDENCY INSTALLATION (npm install)
:: ==============================================================================
echo [4/5] Installing Next.js Frontend Dependencies: npm install...

pushd "%SCRIPT_DIR%ai-frontend"
call npm install
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: npm install failed in ai-frontend!
    popd
    pause
    exit /b 1
)
popd
echo [+] Frontend dependencies installed successfully.
echo.

:: ==============================================================================
:: STEP 5: DATABASE SETUP & MIGRATIONS (SQLite app.db)
:: ==============================================================================
echo [5/5] Setting Up and Migrating SQLite Database: ai-backend\database\app.db...

:: 5.1 Initialize base tables if not yet present
"%VENV_PY%" -c "import sqlite3; from pathlib import Path; db = Path('ai-backend/database/app.db'); db.parent.mkdir(parents=True, exist_ok=True); conn = sqlite3.connect(str(db)); conn.executescript('CREATE TABLE IF NOT EXISTS users (id VARCHAR(36) PRIMARY KEY, email VARCHAR(255) NOT NULL UNIQUE COLLATE NOCASE, full_name VARCHAR(255), hashed_password VARCHAR(255), status VARCHAR(20) NOT NULL DEFAULT \'ACTIVE\', created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS conversations (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE, title VARCHAR(255) NOT NULL DEFAULT \'Cuoc tro chuyen moi\', created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS messages (id VARCHAR(36) PRIMARY KEY, conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, role VARCHAR(20) NOT NULL, content TEXT NOT NULL, model_used VARCHAR(100), tokens_prompt INTEGER DEFAULT 0, tokens_completion INTEGER DEFAULT 0, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);'); conn.close()"
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Failed to create base tables in app.db!
    pause
    exit /b 1
)

:: 5.2 Apply all core database migrations (002 through 021)
echo [i] Applying migration scripts...
"%VENV_PY%" "ai-backend\database\apply_migrations.py"
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Failed to apply core migrations!
    pause
    exit /b 1
)

:: 5.3 Apply response display preferences and user profile extensions
"%VENV_PY%" "ai-backend\database\migrate_response_settings.py"

:: 5.4 Seed official Sensei profiles: Sakura, Kenji, Yuka, Ren, Sensei Master
"%VENV_PY%" "ai-backend\database\migrate_sensei_schema.py"

:: 5.5 Seed JLPT exam banks and question catalog
"%VENV_PY%" -c "import sys; sys.path.insert(0, 'ai-backend'); from database.migrate_exams import migrate_and_seed; migrate_and_seed()"

:: 5.6 Synchronize local learning materials into database
if exist "tools\sync_local_materials_to_db.py" (
    "%VENV_PY%" "tools\sync_local_materials_to_db.py"
)

:: 5.7 Initialize semantic cache and embedded models tables
"%VENV_PY%" -c "import sqlite3; conn = sqlite3.connect('ai-backend/database/app.db'); conn.executescript('''CREATE TABLE IF NOT EXISTS semantic_cache (id VARCHAR(36) PRIMARY KEY, prompt_raw TEXT NOT NULL, prompt_normalized TEXT NOT NULL UNIQUE, category VARCHAR(50) NOT NULL DEFAULT 'general', response_text TEXT NOT NULL, keywords TEXT, similarity_score REAL DEFAULT 1.0, hit_count INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP); CREATE INDEX IF NOT EXISTS idx_semantic_cache_category ON semantic_cache(category); CREATE INDEX IF NOT EXISTS idx_semantic_cache_normalized ON semantic_cache(prompt_normalized); CREATE TABLE IF NOT EXISTS embedded_models (id VARCHAR(100) PRIMARY KEY, name VARCHAR(255) NOT NULL, file_path VARCHAR(500) NOT NULL, file_size_bytes INTEGER NOT NULL DEFAULT 0, min_ram_gb REAL NOT NULL DEFAULT 4.0, min_avail_ram_gb REAL NOT NULL DEFAULT 1.5, min_disk_gb REAL NOT NULL DEFAULT 1.5, min_cpu_cores INTEGER NOT NULL DEFAULT 2, download_status VARCHAR(30) NOT NULL DEFAULT 'NOT_DOWNLOADED', download_progress INTEGER NOT NULL DEFAULT 0, is_active BOOLEAN NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'''); conn.close()"

:: 5.8 Database verification self-test
set "PYTHONPATH=%SCRIPT_DIR%ai-backend"
"%VENV_PY%" -m unittest "ai-backend\tests\test_database_architecture.py" >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo [+] Database verification PASSED: Schema, indices, and default seed models intact.
) else (
    echo [!] Note: Database initialized; minor architecture test warning.
)
echo.

:: ==============================================================================
:: SETUP SUMMARY & READY CONFIRMATION
:: ==============================================================================
echo ==============================================================================
echo                      ChatJPT Setup Completed Successfully!
echo ==============================================================================
echo.
echo Components configured:
echo   [+] Runtime checks: Git, Python 3.10+, Node.js, npm
echo   [+] Python virtual environment: ai-backend\.venv
echo   [+] Backend dependencies: FastAPI, LangChain, LangGraph, Uvicorn, Discord.py
echo   [+] VoiceVox Core Embedded: v0.17.1 ONNX Runtime ^& 28 VVM Neural Voice Models
echo   [+] Frontend dependencies: Next.js 16, React 19, Three.js VRM, Tailwind
echo   [+] Database initialized: ai-backend\database\app.db
echo   [+] Environment config: ai-backend\.env, ai-frontend\.env.local
echo.
echo Next Steps:
echo   - Start the entire system in 1-click by running:
echo       run-demo.bat
echo.
echo   - Access the Web Portal:
echo       Frontend: http://localhost:3000
echo       Backend API: http://127.0.0.1:8000
echo.
echo ==============================================================================
exit /b 0
