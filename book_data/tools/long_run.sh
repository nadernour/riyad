#!/bin/sh
# Keep the matn check going (content step 4, docs/matn.md): a fresh Claude Code session for each
# round of up to 12 hadith, waiting out usage-limit resets in between. Taken from the owner's azkar project.
#
# It runs on the owner's Debian machine only. Start it from book_data/ in the background, so it keeps
# going after the terminal closes:
#     nohup tools/long_run.sh >> .cache/long-run.log 2>&1 &
# Stop it (the loop and the round in progress):
#     pkill -f '[t]ools/long_run.sh'; pkill -f '[c]laude -p Do one round'
# The brackets keep pkill from matching the shell that runs the command, such as a Claude Code session's.
# Progress: .venv/bin/python tools/long_run.py checked (left, of all) · log: .cache/long-run.log
# (tail -F .cache/long-run.log). The rounds don't commit: commit content/ yourself now and then.
# A round's whole session can be opened afterwards, from book_data/, with: claude --resume <its session id in the log>
#
# Each session may only read files, write content/matn/inbox.json, and run the project's
# Python tools; anything else is refused without asking.
cd "$(dirname "$0")/.." || exit 1
LOG=.cache/long-run.log
OUT=.cache/long-run-round.jsonl
PROBE=.cache/long-run-limits.jsonl
BEFORE=.cache/long-run-checked.txt
PROMPT="Do one round of the matn check: follow docs/matn.md exactly."
TOOLS="Read,Glob,Grep,Write(content/matn/**),Edit(content/matn/**),Bash(.venv/bin/python tools/*)"
# The only built-in tools a round uses. Leaving out the others, the MCP servers and the skills
# cuts the session's base prompt by more than half.
BUILTIN="Read,Glob,Grep,Edit,Write,Bash"
# Pinned, so that changing the model or effort in another session (saved in ~/.claude/settings.json)
# doesn't change the run. In the azkar project, Opus at low effort read scans with fewer slips than
# at xhigh, at about a third of the cost. But here the first rounds at low effort skipped zooms that
# docs/matn.md asks for (h. 21's round zoomed 4 spots for 103 words it gave marks to), so the run
# uses medium; start it with EFFORT=low to go back. The log gives each round's fixes and zooms.
MODEL=claude-opus-5-5
EFFORT=${EFFORT:-medium}
# Start a round only while the 5-hour window is below this percent, because a round cut off by
# the limit loses the hadith it was working on.
START=${START:-85}
WAIT=1800          # seconds to wait after a round that made no progress
MAX_IDLE_ROUNDS=24 # stop after this many rounds in a row without progress (~12 hours)

# claude -p always uses an API key from the environment instead of the subscription login.
if [ -n "$ANTHROPIC_API_KEY$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN is set, so every round would be billed to it"
    echo "instead of using your Claude subscription. Unset it first (or remove this check to use the API)."
    exit 1
fi

# Read how much of the usage limits is used, with a one-word Haiku request.
read_limits() {
    CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p "Reply with the single word OK." --model haiku --tools "" --strict-mcp-config \
        --disable-slash-commands --no-session-persistence --output-format stream-json --verbose \
        > "$PROBE" 2>> "$LOG"
}

# The comparison takes minutes (the first time, Tesseract reads every page too), longer than a
# round's commands may run, so it is made here: when there is none, or when tools/matn.py or
# tools/numbering.py has changed since it was made, e.g. after a pull.
{ [ .cache/matn.json -nt tools/matn.py ] && [ .cache/matn.json -nt tools/numbering.py ]; } \
    || .venv/bin/python tools/matn.py compare >> "$LOG" 2>&1 || exit 1

idle=0
while true; do
    set -- $(.venv/bin/python tools/long_run.py checked)
    [ "$1" -eq 0 ] && break
    read_limits
    wait=$(.venv/bin/python tools/long_run.py wait "$PROBE" "$START")
    if [ "${wait%% *}" -gt 0 ] 2>/dev/null; then
        echo "=== $(date '+%F %T') $1 of $2 left · ${wait#* }" >> "$LOG"
        sleep "${wait%% *}"
        continue
    fi
    echo "$1 $2" > "$BEFORE"
    echo "=== $(date '+%F %T') round starts ($1 of $2 left, effort $EFFORT)" >> "$LOG"
    # A 5-minute prompt cache: on a subscription the default is 1 hour, whose cache writes cost
    # more, and calls in a round come at most a few minutes apart.
    # No auto-memory: a round works only from the repo's files, and can't save notes into the
    # memory the owner's own sessions load.
    # A 10-minute command timeout: `next` renders the round's crops, which a slow machine may take
    # longer than the 2-minute default for.
    BASH_DEFAULT_TIMEOUT_MS=600000 CLAUDE_CODE_PROMPT_CACHE_TTL=5m CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p "$PROMPT" \
        --model "$MODEL" --effort "$EFFORT" --permission-mode dontAsk --allowedTools "$TOOLS" --tools "$BUILTIN" --strict-mcp-config \
        --disable-slash-commands --output-format stream-json --verbose > "$OUT" 2>> "$LOG"
    # Log the round's session id, length, cost estimate, limits used, progress and closing message.
    .venv/bin/python tools/long_run.py report "$OUT" "$PROBE" "$BEFORE" >> "$LOG" 2>&1
    set -- $(.venv/bin/python tools/long_run.py checked)
    if [ "$1" -ge "$(cut -d' ' -f1 "$BEFORE")" ]; then
        idle=$((idle + 1))
        if [ "$idle" -ge "$MAX_IDLE_ROUNDS" ]; then
            echo "=== $(date '+%F %T') no progress in $idle rounds; stopping" >> "$LOG"
            echo "Stopped: no progress in $idle rounds. See $LOG."
            exit 1
        fi
        echo "=== $(date '+%F %T') no progress; waiting $((WAIT / 60)) minutes" >> "$LOG"
        sleep "$WAIT"
    else
        idle=0
    fi
done
echo "=== $(date '+%F %T') all hadith are checked" >> "$LOG"
echo "All hadith are checked. See docs/matn.md for what comes next."
