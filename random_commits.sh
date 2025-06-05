#!/usr/bin/env bash

# Создаём файл логов, если он ещё не создан
touch log.txt

# Функция генерации случайного сообщения для коммита
generate_commit_message() {
  verbs=("Fix" "Add" "Improve" "Update" "Refactor" "Remove" "Optimize")
  objects=("RPC handler" "CLI argument" "ENS lookup" "token logic" "address parser" "logging" "balance fetch" "validator check" "output format" "retry logic")
  contexts=("flow" "code" "support" "case" "handler" "logic")

  verb=${verbs[$RANDOM % ${#verbs[@]}]}
  object=${objects[$RANDOM % ${#objects[@]}]}
  context=${contexts[$RANDOM % ${#contexts[@]}]}

  echo "$verb $object $context"
}

# Запускаем цикл для 10 коммитов
for i in {1..10}; do
  echo "entry $i" >> log.txt                       # Запись в лог
  git add .                                       
  export GIT_AUTHOR_DATE="$(date -d "$((RANDOM % 100 + 1)) days ago" '+%Y-%m-%dT12:00:00')"  # Дата автора
  export GIT_COMMITTER_DATE="$GIT_AUTHOR_DATE"    # Дата коммитера
  git commit -m "$(generate_commit_message)"      # Создаём коммит с рандомным сообщением
  git push origin main                            # Пушим коммит на GitHub
  sleep $((RANDOM % 16 + 15))                     # Задержка, чтобы не казалось спамом
done
