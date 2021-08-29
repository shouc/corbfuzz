nvm use --lts

rm -rf /tmp/rand.sock
node main.js > "$1" 2>"$1.err"

