# Shared launcher logging. copy/truncate retains native crash-handler handles.
vitalux_log_line() {
  local path="$1" version="$2" message="$3" record size temporary lockfd
  local LC_ALL=C
  printf -v record '[%s] [Vitalux v%s] %s' "$(date -Is)" "${version:-unknown}" "$message"
  [[ -L "$path" || -L "$path.1" || -L "$path.lock" ]] && return 0
  exec {lockfd}>>"$path.lock" || return 0
  if command -v flock >/dev/null 2>&1; then flock -x "$lockfd" || { exec {lockfd}>&-; return 0; }; fi
  size=$(stat -c %s -- "$path" 2>/dev/null) || size=0
  if (( size > 0 && size + ${#record} + 1 > 5242880 )); then
    temporary=$(mktemp "$path.rotate-XXXXXXXX") || temporary=''
    if [[ -n "$temporary" ]]; then
      if cp -- "$path" "$temporary" && mv -f -- "$temporary" "$path.1"; then : >"$path"; fi
      rm -f -- "$temporary"
    fi
  fi
  printf '%s\n' "$record" >>"$path"
  exec {lockfd}>&-
  return 0
}
