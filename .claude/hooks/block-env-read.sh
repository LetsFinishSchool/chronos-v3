#!/usr/bin/env bash
# PreToolUse-Hook: verbietet Lesen/Ausgeben von .env und .envrc (enthalten Secrets).
# Erlaubt bleiben Vorlagen wie .envrc.example / .env.example.
# Exit 2 = Aufruf blockieren, stderr geht an Claude.
input=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$input")

# Dateiname ist .env, .envrc oder .env.<irgendwas> (außer .example/.sample/.template)
secret_name='(^|/)\.env(rc|\.[A-Za-z0-9_-]+)?$'
template='\.(example|sample|template)$'

deny() {
  echo "Blockiert: .env/.envrc enthalten Secrets und dürfen nicht gelesen oder ausgegeben werden. Nutze .envrc.example oder frage die Person." >&2
  exit 2
}

case "$tool" in
  Read|Edit|Write|NotebookEdit|Grep|Glob)
    for p in $(jq -r '[.tool_input.file_path, .tool_input.path, .tool_input.notebook_path] | map(select(. != null)) | .[]' <<<"$input"); do
      [[ $p =~ $secret_name && ! $p =~ $template ]] && deny
    done
    # Grep/Glob über Verzeichnisse mit explizitem Glob auf .env*
    g=$(jq -r '.tool_input.glob // .tool_input.pattern // empty' <<<"$input")
    [[ $tool != Grep && $g =~ (^|/)\.env && ! $g =~ $template ]] && deny
    [[ $tool == Grep ]] && g=$(jq -r '.tool_input.glob // empty' <<<"$input") && [[ $g =~ (^|/)\.env && ! $g =~ $template ]] && deny
    ;;
  Bash)
    cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
    # Nennt der Befehl .env/.envrc (nicht als Teil eines längeren Namens, nicht als Vorlage)?
    ref='(^|[[:space:]"'"'"'=/<>(])\.env(rc|\.[A-Za-z0-9_-]+)?([[:space:]"'"'"';|&<>)]|$)'
    if [[ $cmd =~ $ref ]]; then
      stripped=$(sed -E 's/\.env(rc)?\.(example|sample|template)//g' <<<"$cmd")
      if [[ $stripped =~ $ref ]]; then
        # Lese-/Ausgabebefehle, source und Umleitungen
        reader='(^|[[:space:];&|(`])(cat|tac|less|more|head|tail|bat|nl|od|xxd|hexdump|strings|grep|egrep|fgrep|rg|ag|awk|sed|cut|sort|uniq|tee|cp|mv|base64|jq|yq|python3?|node|perl|ruby|source|vi|vim|nano|view|code|xargs|diff|cmp|wc|paste|column|rev|dd|curl)([[:space:]]|$)|(^|[[:space:];&|(])\.[[:space:]]|<[[:space:]]*[^[:space:]]*\.env'
        [[ $stripped =~ $reader ]] && deny
      fi
    fi
    # Gesamte Umgebung ausgeben verrät geladene Secrets
    [[ $cmd =~ (^|[[:space:];&|])(printenv|env|export[[:space:]]+-p|declare[[:space:]]+-x)([[:space:]]*($|[;&|])) ]] && deny
    ;;
esac
exit 0
