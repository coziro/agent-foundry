#!/bin/bash
# tmuxペインにメッセージを送信し、Enterで確実に送信する
# 送信元ペインIDをメッセージに自動付与するため、受信側が返信先を把握できる
#
# Usage:
#   tmux-send.sh <target-pane> <message>
#   echo "<message>" | tmux-send.sh <target-pane>
#
#   target-pane: 送信先ペイン（例: 0:0.1）
#   message: 送信するメッセージ（シングルクォートを含む場合はstdinを使う）
#
# 送信されるメッセージの形式:
#   [FROM:<session>:<window>.<pane>] <message>
# 例:
#   [FROM:main:0.0] 今日の日付を教えてください

set -e

if [ $# -lt 1 ]; then
  echo "Usage: $0 <target-pane> [message]" >&2
  echo "       echo '<message>' | $0 <target-pane>" >&2
  exit 1
fi

TARGET="$1"

# メッセージを引数またはstdinから取得
if [ $# -ge 2 ]; then
  MESSAGE="$2"
else
  MESSAGE=$(cat)
fi

# 空メッセージのチェック
if [ -z "$MESSAGE" ]; then
  echo "Error: message is empty" >&2
  exit 1
fi

# 送信元ペインIDを取得（session_name:window_index.pane_index 形式）
# -t "$TMUX_PANE" で自ペインを明示指定する。指定しないとtmuxクライアントのフォーカス中ペインを返すため、
# 複数ペイン環境でフォーカスが移っているとFROMアドレスが間違ったペインになる。
SELF=$(tmux display-message -t "$TMUX_PANE" -p '#{session_name}:#{window_index}.#{pane_index}') || { echo "Error: failed to get own pane ID (is this running inside tmux?)" >&2; exit 1; }

# 改行を除去する。tmux send-keysは改行をEnterとして解釈するため、
# 改行が含まれると意図しない送信が発生しメッセージが壊れる
# printf '%s' を使い、echo による意図しない展開（-e, \n 等）を防ぐ
MESSAGE=$(printf '%s' "$MESSAGE" | tr '\n' ' ' | sed 's/[[:space:]]*$//')

FULL_MESSAGE="[FROM:${SELF}] ${MESSAGE}"

# -l（リテラルモード）でtmuxの特殊キー解釈を無効にし、文字をそのまま送信する
# Enterは -l では送れないため、別ステップで送信する
tmux send-keys -l -t "$TARGET" "$FULL_MESSAGE" || { echo "Error: failed to send message to pane '$TARGET'" >&2; exit 1; }
tmux send-keys -t "$TARGET" Enter || { echo "Error: failed to send Enter to pane '$TARGET'" >&2; exit 1; }
