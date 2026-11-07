#!/usr/bin/env bash
# Shared setup branding and the terminal scroll region for installation output.

draw_setup_banner() {
    # Original OpenSoft wordmark, with inset half-block shading inspired by
    # https://github.com/anomalyco/opencode/blob/dev/packages/tui/src/component/logo.tsx
    local width="$1"
    local silver='\033[38;5;252m' edge='\033[38;5;239m' reset='\033[0m'
    local -a logo=(
        '                                    ▄ '
        '█▀▀█ █▀▀█ █▀▀█ █▀▀▄ █▀▀▀ █▀▀█ █▀▀▀ ▀█▀▀'
        '█__█ █__█ █^^^ █__█ ▀▀▀█ █__█ █^^   █__'
        '▀▀▀▀ █▀▀▀ ▀▀▀▀ ▀~~▀ ▀▀▀▀ ▀▀▀▀ ▀     ▀▀▀'
    )
    local -a tones=(255 252 250 246)
    local line char tone index position
    printf '\n'
    if (( width < 42 )); then
        printf '  %bOpenSoft%b\n\n' "$silver" "$reset"
        return
    fi
    for index in "${!logo[@]}"; do
        line="${logo[$index]}"
        tone="\033[38;5;${tones[$index]}m"
        printf '  %b' "$tone"
        for ((position=0; position<${#line}; position++)); do
            char="${line:$position:1}"
            case "$char" in
                _) printf '\033[48;5;237m %b%b' "$reset" "$tone" ;;
                '^') printf '\033[48;5;237m▀%b%b' "$reset" "$tone" ;;
                '~') printf '%b▀%b' "$edge" "$tone" ;;
                *) printf '%s' "$char" ;;
            esac
        done
        printf '%b\n' "$reset"
    done
    printf '\n'
}

start_setup_install_screen() {
    [[ -t 0 && -t 1 && -n "${TERM:-}" && "$TERM" != dumb ]] || return 0

    local rows columns header breaks log_top region rule
    read -r rows columns < <(stty size) || return 0
    (( rows >= 8 && columns >= 32 )) || return 0
    header="$(
        # Switch to the compact wordmark when the terminal is short.
        if (( rows >= 14 )); then draw_setup_banner "$((columns - 1))"
        else draw_setup_banner 0
        fi
        printf '  openBenches v%s\n\033[1m  Installing\033[0m · Install log' "$1"
    )"
    breaks="${header//[!$'\n']/}"
    log_top=$((${#breaks} + 3))
    # Keep normal stdout, stderr and stdin attached so installers and prompts
    # retain terminal behavior. Only the rows between header and footer scroll.
    region="$(tput csr "$((log_top - 1))" "$((rows - 2))" 2>/dev/null)" || return 0
    printf -v rule '%*s' "$((columns - 1))" ''
    export WORKBENCHES_INSTALL_SCREEN=1
    setup_install_screen_active=true
    # Terminal dimensions can change while a build is writing. Drop the
    # fixed rows on resize so subsequent output can use the whole terminal.
    trap 'restore_setup_install_screen; printf "\n"' WINCH
    printf '\033[0m\033[2J\033[H%s\n\033[2m%s\033[0m' "$header" "${rule// /─}"
    printf '\033[%d;1H\033[2m  Ctrl+C to cancel\033[0m%s\033[%d;1H\033[?25h' \
        "$rows" "$region" "$log_top"
}

restore_setup_install_screen() {
    [[ "${setup_install_screen_active:-}" == true ]] || return 0
    setup_install_screen_active=false
    trap - WINCH
    printf '\033[r\033[999;1H\033[0m\033[2K\033[?25h'
}

finish_setup_install_screen() {
    [[ "${WORKBENCHES_INSTALL_SCREEN:-}" == 1 ]] || return 0

    local status="$1" message
    case "$status" in
        0) message='Setup complete' ;;
        130|143) message='Setup cancelled' ;;
        *) message="Setup stopped (exit $status)" ;;
    esac
    restore_setup_install_screen
    printf '  %s\n' "$message"
}
