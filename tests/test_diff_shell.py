import pytest

from tests.utils import DiffTestCase, DiffTestRunner

SHELL_BASICS_CASES = [
    DiffTestCase(
        name="shell_001_function_definition",
        initial_files={
            "utils.sh": """#!/bin/bash

process_file() {
    local file=$1
    echo "Processing $file"
    cat "$file" | wc -l
}

log_message() {
    local level=$1
    local message=$2
    echo "[$level] $(date): $message"
}
""",
            "main.sh": """#!/bin/bash
echo "Main script"
""",
            "garbage.sh": """#!/bin/bash
shelltest_garbage_xyz001() { echo "unused"; }
shelltest_unused_abc002="never_used"
""",
        },
        changed_files={
            "main.sh": """#!/bin/bash
source ./utils.sh

for file in *.txt; do
    process_file "$file"
    log_message "INFO" "Processed $file"
done
""",
        },
        must_include=["main.sh", "process_file"],
        must_not_include=["shelltest_garbage_xyz001", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_002_source_script",
        initial_files={
            "config.sh": """#!/bin/bash

export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="myapp"
export LOG_LEVEL="info"

get_connection_string() {
    echo "postgres://${DB_HOST}:${DB_PORT}/${DB_NAME}"
}
""",
            "deploy.sh": """#!/bin/bash
echo "Deploying..."
""",
            "garbage.sh": """#!/bin/bash
shelltest_gunused_003() { echo "never called"; }
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "deploy.sh": """#!/bin/bash
source ./config.sh

echo "Connecting to database..."
CONNECTION=$(get_connection_string)
echo "Using connection: $CONNECTION"
echo "Log level: $LOG_LEVEL"
""",
        },
        must_include=["deploy.sh", "get_connection_string"],
        must_not_include=["shelltest_gunused_003", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_003_variable_expansion",
        initial_files={
            "env.sh": """#!/bin/bash
export CONFIG_PATH="/etc/myapp"
export DATA_DIR="/var/lib/myapp"
export APP_NAME="myapp"
""",
            "setup.sh": """#!/bin/bash
echo "Setup"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_GVAR_004="unused_value"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "setup.sh": """#!/bin/bash
source ./env.sh

mkdir -p "${CONFIG_PATH}/conf.d"
mkdir -p "${DATA_DIR}/logs"
echo "Created directories for ${APP_NAME}"
cp template.conf "${CONFIG_PATH}/${APP_NAME}.conf"
""",
        },
        must_include=["setup.sh", "CONFIG_PATH"],
        must_not_include=["SHELLTEST_GVAR_004", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_004_command_substitution",
        initial_files={
            "backup.sh": """#!/bin/bash
echo "Backup script"
""",
            "garbage.sh": """#!/bin/bash
shelltest_backup_005="never_used_value"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "backup.sh": """#!/bin/bash
current_date=$(date +%Y-%m-%d)
current_time=$(date +%H-%M-%S)
hostname=$(hostname)
git_hash=$(git rev-parse --short HEAD)

backup_name="backup_${hostname}_${current_date}_${current_time}"
echo "Creating backup: $backup_name"
echo "Git version: $git_hash"

file_count=$(find . -type f | wc -l)
echo "Total files: $file_count"
""",
        },
        must_include=["backup.sh", "backup_name"],
        must_not_include=["shelltest_backup_005", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_005_array",
        initial_files={
            "process.sh": """#!/bin/bash
echo "Process"
""",
            "garbage.sh": """#!/bin/bash
shelltest_array_006=("never" "used")
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "process.sh": """#!/bin/bash
files=("${@}")
declare -a results

for i in "${!files[@]}"; do
    file="${files[$i]}"
    if [[ -f "$file" ]]; then
        results+=("$file: OK")
    else
        results+=("$file: NOT FOUND")
    fi
done

echo "Results:"
for result in "${results[@]}"; do
    echo "  $result"
done

echo "Total files: ${#files[@]}"
""",
        },
        must_include=["process.sh", "results"],
        must_not_include=["shelltest_array_006", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_006_conditional",
        initial_files={
            "config.sh": """#!/bin/bash
export CONFIG_FILE="/etc/app/config.yaml"
""",
            "check.sh": """#!/bin/bash
echo "Check"
""",
            "garbage.sh": """#!/bin/bash
shelltest_config_007="not_used"
shelltest_unused_abc002="never_used"
""",
        },
        changed_files={
            "check.sh": """#!/bin/bash
source ./config.sh

if [[ -f "$CONFIG_FILE" ]]; then
    echo "Config file exists"
    if [[ -r "$CONFIG_FILE" ]]; then
        echo "Config file is readable"
    else
        echo "Config file is not readable"
        exit 1
    fi
elif [[ -d "$(dirname "$CONFIG_FILE")" ]]; then
    echo "Config directory exists, but file is missing"
    exit 1
else
    echo "Config directory does not exist"
    mkdir -p "$(dirname "$CONFIG_FILE")"
fi
""",
        },
        must_include=["check.sh", "CONFIG_FILE"],
        must_not_include=["shelltest_config_007", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_007_case_statement",
        initial_files={
            "service.sh": """#!/bin/bash
echo "Service"
""",
            "garbage.sh": """#!/bin/bash
shelltest_service_008="never_referenced"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "service.sh": """#!/bin/bash

case "$1" in
    start)
        echo "Starting service..."
        ./bin/app start
        ;;
    stop)
        echo "Stopping service..."
        ./bin/app stop
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        ./bin/app status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
""",
        },
        must_include=["service.sh"],
        must_not_include=["shelltest_service_008", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_008_loop",
        initial_files={
            "utils.sh": """#!/bin/bash
process() {
    local file=$1
    echo "Processing: $file"
}
""",
            "batch.sh": """#!/bin/bash
echo "Batch"
""",
            "garbage.sh": """#!/bin/bash
shelltest_loop_009() { echo "never called"; }
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "batch.sh": """#!/bin/bash
source ./utils.sh

for file in *.log; do
    process "$file"
done

while read -r line; do
    echo "Line: $line"
done < input.txt

counter=0
until [[ $counter -ge 10 ]]; do
    echo "Counter: $counter"
    ((counter++))
done
""",
        },
        must_include=["batch.sh", "process"],
        must_not_include=["shelltest_loop_009", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_009_here_document",
        initial_files={
            "generate.sh": """#!/bin/bash
echo "Generate"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_HEREDOC_010="unused_value_12345"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "generate.sh": """#!/bin/bash

cat <<EOF > config.json
{
    "name": "$APP_NAME",
    "version": "$VERSION",
    "environment": "$ENV",
    "database": {
        "host": "$DB_HOST",
        "port": $DB_PORT
    }
}
EOF

cat <<'SCRIPT' > setup.sh
#!/bin/bash
echo "This is a literal script"
echo '$HOME will not be expanded'
SCRIPT
""",
        },
        must_include=["generate.sh"],
        must_not_include=["SHELLTEST_HEREDOC_010", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_010_trap",
        initial_files={
            "cleanup.sh": """#!/bin/bash
cleanup() {
    echo "Cleaning up..."
    rm -f /tmp/lockfile
    rm -rf /tmp/workdir
}
""",
            "worker.sh": """#!/bin/bash
echo "Worker"
""",
            "garbage.sh": """#!/bin/bash
shelltest_cleanup_011() { echo "never invoked"; }
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "worker.sh": """#!/bin/bash
source ./cleanup.sh

trap cleanup EXIT
trap 'echo "Interrupted"; cleanup; exit 1' INT TERM

mkdir -p /tmp/workdir
touch /tmp/lockfile

echo "Working..."
sleep 60
echo "Done"
""",
        },
        must_include=["worker.sh", "cleanup"],
        must_not_include=["shelltest_cleanup_011", "unused_marker_12345"],
    ),
]

SHELL_ADVANCED_CASES = [
    DiffTestCase(
        name="shell_011_getopts",
        initial_files={
            "cli.sh": """#!/bin/bash
echo "CLI"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_CLI_012="never_used_option"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "cli.sh": """#!/bin/bash

usage() {
    echo "Usage: $0 [-f file] [-v] [-h]"
    exit 1
}

verbose=false
file=""

while getopts "f:vh" opt; do
    case "$opt" in
        f)
            file="$OPTARG"
            ;;
        v)
            verbose=true
            ;;
        h)
            usage
            ;;
        *)
            usage
            ;;
    esac
done

shift $((OPTIND - 1))

if [[ "$verbose" == true ]]; then
    echo "Verbose mode enabled"
fi

if [[ -n "$file" ]]; then
    echo "Processing file: $file"
fi
""",
        },
        must_include=["cli.sh", "getopts"],
        must_not_include=["SHELLTEST_CLI_012", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_012_exit_codes",
        initial_files={
            "caller.sh": """#!/bin/bash
handle_error() {
    local code=$1
    case $code in
        0) echo "Success" ;;
        1) echo "General error" ;;
        2) echo "Invalid argument" ;;
        *) echo "Unknown error: $code" ;;
    esac
}
""",
            "validate.sh": """#!/bin/bash
echo "Validate"
""",
            "garbage.sh": """#!/bin/bash
shelltest_error_013() { echo "never invoked 12345"; }
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "validate.sh": """#!/bin/bash

if [[ -z "$1" ]]; then
    echo "Error: No input provided"
    exit 2
fi

if [[ ! -f "$1" ]]; then
    echo "Error: File not found"
    exit 1
fi

echo "Validation passed"
exit 0
""",
        },
        must_include=["validate.sh"],
        must_not_include=["shelltest_error_013", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_013_pipe",
        initial_files={
            "data.txt": """John,25,Engineer
Jane,30,Manager
Bob,22,Developer
""",
            "analyze.sh": """#!/bin/bash
echo "Analyze"
""",
            "garbage.sh": """#!/bin/bash
shelltest_data_014="0,Unused"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "analyze.sh": """#!/bin/bash

cat data.txt | grep "Engineer" | sort | head -10

find . -name "*.log" | xargs grep "ERROR" | wc -l

ps aux | grep "[n]ginx" | awk '{print $2}' | xargs kill 2>/dev/null

cat data.txt | cut -d',' -f2 | sort -n | tail -1
""",
        },
        must_include=["analyze.sh"],
        must_not_include=["shelltest_data_014", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_014_redirect",
        initial_files={
            "config.sh": """#!/bin/bash
export LOG_FILE="/var/log/app.log"
""",
            "runner.sh": """#!/bin/bash
echo "Runner"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_REDIRECT_015="unused_redirect_path"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "runner.sh": """#!/bin/bash
source ./config.sh

exec 2>&1 | tee -a "$LOG_FILE"

echo "Starting application..."
./app 2>&1 | tee -a "$LOG_FILE"

{
    echo "=== System Info ==="
    date
    hostname
    uptime
} >> "$LOG_FILE"

./script.sh > /dev/null 2>&1
""",
        },
        must_include=["runner.sh", "LOG_FILE"],
        must_not_include=["SHELLTEST_REDIRECT_015", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_015_subshell",
        initial_files={
            "config.sh": """#!/bin/bash
export BUILD_DIR="/tmp/build"
""",
            "build.sh": """#!/bin/bash
echo "Build"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_SUBSHELL_016="unused_build_path"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "build.sh": """#!/bin/bash
source ./config.sh

(cd "$BUILD_DIR" && make clean && make)

result=$(
    cd /tmp
    echo "Working in: $(pwd)"
    ls -la
)

(
    export CUSTOM_VAR="value"
    ./run-with-custom-env.sh
)

echo "Still in original directory: $(pwd)"
""",
        },
        must_include=["build.sh", "BUILD_DIR"],
        must_not_include=["SHELLTEST_SUBSHELL_016", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_016_background_job",
        initial_files={
            "jobs.sh": """#!/bin/bash
long_process() {
    sleep 30
    echo "Long process complete"
}
""",
            "parallel.sh": """#!/bin/bash
echo "Parallel"
""",
            "garbage.sh": """#!/bin/bash
shelltest_job_017() { echo "never started 67890"; }
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "parallel.sh": """#!/bin/bash
source ./jobs.sh

long_process &
pid1=$!

./another-task.sh &
pid2=$!

echo "Started background jobs: $pid1 $pid2"

wait $pid1
echo "Job 1 complete"

wait $pid2
echo "Job 2 complete"

wait
echo "All jobs complete"
""",
        },
        must_include=["parallel.sh", "long_process"],
        must_not_include=["shelltest_job_017", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_017_set_options",
        initial_files={
            "robust.sh": """#!/bin/bash
echo "Robust"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_SET_018="unused_option_12345"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "robust.sh": """#!/bin/bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CONFIG_FILE="${SCRIPT_DIR}/config.yaml"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Config file not found"
    exit 1
fi

process_data || {
    echo "Processing failed"
    exit 1
}
""",
        },
        must_include=["robust.sh", "pipefail"],
        must_not_include=["SHELLTEST_SET_018", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="shell_018_export",
        initial_files={
            "env.sh": """#!/bin/bash
echo "Env"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_EXPORT_019="unused_export_value"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "env.sh": """#!/bin/bash

export PATH="$PATH:$HOME/bin:/usr/local/app/bin"
export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"

export APP_HOME="/opt/myapp"
export APP_CONFIG="$APP_HOME/config"
export APP_LOG="$APP_HOME/logs"

export -f my_function

my_function() {
    echo "This function is exported"
}

./child-script.sh
""",
        },
        must_include=["env.sh", "APP_HOME"],
        must_not_include=["SHELLTEST_EXPORT_019", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_019_alias",
        initial_files={
            "aliases.sh": """#!/bin/bash

alias ll='ls -la'
alias la='ls -A'
alias grep='grep --color=auto'
alias df='df -h'

alias gs='git status'
alias gc='git commit'
alias gp='git push'
""",
            "interactive.sh": """#!/bin/bash
echo "Interactive"
""",
            "garbage.sh": """#!/bin/bash
alias shelltest_alias_020='echo never_used_67890'
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "interactive.sh": """#!/bin/bash
shopt -s expand_aliases
source ./aliases.sh

ll /tmp
gs
df
""",
        },
        must_include=["interactive.sh"],
        must_not_include=["shelltest_alias_020", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="shell_020_shebang",
        initial_files={
            "script.sh": """echo "No shebang"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_SHEBANG_021="unused_value_99999"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "script.sh": """#!/usr/bin/env bash

if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
    echo "Bash 4.0+ required"
    exit 1
fi

declare -A map
map[key]="value"

echo "Running with: $BASH_VERSION"
echo "Map value: ${map[key]}"
""",
        },
        must_include=["script.sh", "BASH_VERSION"],
        must_not_include=["SHELLTEST_SHEBANG_021", "unused_marker_12345"],
    ),
]

BASH_SPECIFIC_CASES = [
    DiffTestCase(
        name="bash_001_associative_array",
        initial_files={
            "lookup.sh": """#!/bin/bash
echo "Lookup"
""",
            "garbage.sh": """#!/bin/bash
shelltest_lookup_022="never_accessed_12345"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "lookup.sh": """#!/bin/bash

declare -A config
config[host]="localhost"
config[port]="8080"
config[debug]="true"

for key in "${!config[@]}"; do
    echo "$key = ${config[$key]}"
done

if [[ -v config[debug] ]]; then
    echo "Debug mode: ${config[debug]}"
fi
""",
        },
        must_include=["lookup.sh", "config"],
        must_not_include=["shelltest_lookup_022", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="bash_002_nameref",
        initial_files={
            "indirect.sh": """#!/bin/bash
echo "Indirect"
""",
            "garbage.sh": """#!/bin/bash
shelltest_nameref_023="never_referenced_67890"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "indirect.sh": """#!/bin/bash

modify_array() {
    local -n arr_ref=$1
    arr_ref+=("new_element")
}

my_array=("first" "second")
modify_array my_array

echo "Array: ${my_array[@]}"
""",
        },
        must_include=["indirect.sh", "arr_ref"],
        must_not_include=["shelltest_nameref_023", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="bash_003_process_substitution",
        initial_files={
            "compare.sh": """#!/bin/bash
echo "Compare"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_COMPARE_024="unused_compare_value"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "compare.sh": """#!/bin/bash

diff <(sort file1.txt) <(sort file2.txt)

while read -r line; do
    echo "Processing: $line"
done < <(find . -name "*.txt")

paste <(cut -d, -f1 data.csv) <(cut -d, -f3 data.csv)
""",
        },
        must_include=["compare.sh"],
        must_not_include=["SHELLTEST_COMPARE_024", "shelltest_unused_abc002"],
    ),
    DiffTestCase(
        name="bash_004_coprocess",
        initial_files={
            "coproc.sh": """#!/bin/bash
echo "Coprocess"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_COPROC_025="unused_coproc_99999"
unused_marker_12345="not_used"
""",
        },
        changed_files={
            "coproc.sh": """#!/bin/bash

coproc WORKER { while read -r line; do echo "Processed: $line"; done; }

echo "Hello" >&${WORKER[1]}
read -r result <&${WORKER[0]}
echo "Result: $result"

exec {WORKER[1]}>&-
wait $WORKER_PID
""",
        },
        must_include=["coproc.sh", "WORKER"],
        must_not_include=["SHELLTEST_COPROC_025", "unused_marker_12345"],
    ),
    DiffTestCase(
        name="bash_005_extglob",
        initial_files={
            "patterns.sh": """#!/bin/bash
echo "Patterns"
""",
            "garbage.sh": """#!/bin/bash
SHELLTEST_PATTERN_026="unused_pattern_12345"
shelltest_unused_abc002="not_used"
""",
        },
        changed_files={
            "patterns.sh": """#!/bin/bash
shopt -s extglob

rm -f !(*.txt|*.log)

for f in *.@(jpg|png|gif); do
    echo "Image: $f"
done

case "$file" in
    *.+(tar|gz|bz2))
        echo "Archive file"
        ;;
    !(*.*)
        echo "No extension"
        ;;
esac
""",
        },
        must_include=["patterns.sh", "extglob"],
        must_not_include=["SHELLTEST_PATTERN_026", "shelltest_unused_abc002"],
    ),
]

ALL_SHELL_CASES = SHELL_BASICS_CASES + SHELL_ADVANCED_CASES + BASH_SPECIFIC_CASES


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_SHELL_CASES, ids=lambda c: c.name)
def test_shell_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
