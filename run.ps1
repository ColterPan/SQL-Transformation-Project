param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "generate", "seed", "run", "test", "build", "docs", "all")]
    [string]$Command = "all"
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$Venv = Join-Path $RepoRoot ".venv"
$DbtDir = Join-Path $RepoRoot "dealership_analytics"

function Invoke-Setup {
    if (-not (Test-Path $Venv)) {
        python -m venv $Venv
    }
    & "$Venv\Scripts\python.exe" -m pip install --upgrade pip -q
    & "$Venv\Scripts\python.exe" -m pip install -r "$RepoRoot\scripts\requirements.txt" -q
    Push-Location $DbtDir
    try {
        $env:DBT_PROFILES_DIR = "."
        & "$Venv\Scripts\dbt.exe" deps
    } finally {
        Pop-Location
    }
}

function Invoke-Generate {
    & "$Venv\Scripts\python.exe" "$RepoRoot\scripts\generate_raw_data.py" --seed 42
}

function Invoke-Dbt {
    param([string[]]$DbtArgs)
    Push-Location $DbtDir
    try {
        $env:DBT_PROFILES_DIR = "."
        & "$Venv\Scripts\dbt.exe" @DbtArgs
    } finally {
        Pop-Location
    }
}

switch ($Command) {
    "setup"    { Invoke-Setup }
    "generate" { Invoke-Generate }
    "seed"     { Invoke-Dbt @("seed") }
    "run"      { Invoke-Dbt @("run") }
    "test"     { Invoke-Dbt @("test") }
    "build"    { Invoke-Dbt @("build") }
    "docs"     { Invoke-Dbt @("docs", "generate"); Invoke-Dbt @("docs", "serve") }
    "all" {
        Invoke-Setup
        Invoke-Generate
        Invoke-Dbt @("build")
    }
}
