#!/usr/bin/env bash
# ♡ saludito al abrir la terminal: kaomoji + frase random
k=("(˘ω˘)" "(｡•ᴗ•｡)" "(◕‿◕✿)" "(≧◡≦) ♡" "ʕ•ᴥ•ʔ" "ฅ^•ﻌ•^ฅ" "(•̀ᴗ•́)و" "(っ˘ڡ˘ς)" "٩(◕‿◕｡)۶" "(´｡• ω •｡\`) ♡" "/ᐠ｡ꞈ｡ᐟ\\" "( ˘▽˘)っ♨")
f=("Hola de nuevo, __NAME__" "¿Qué vamos a programar hoy?" "Un commit a la vez" "Toma agüita antes de empezar"
   "Hoy también lo vas a hacer increíble" "Si compila, es arte" "Pequeños pasos, grandes sueños"
   "Respira hondo y a darle" "Recuerda guardar tu progreso" "El bug no es tuyo, es del universo"
   "Tu yo del futuro te lo va a agradecer" "Lo cute no quita lo programador")
h=$(date +%H)
if   (( 10#$h < 6 ));  then g="Ya es tarde, descansa pronto"
elif (( 10#$h < 12 )); then g="Buenos días"
elif (( 10#$h < 19 )); then g="Buenas tardes"
else g="Buenas noches"; fi
P=$'\e[38;2;255;143;200m'; D=$'\e[38;2;226;93;164m'; L=$'\e[38;2;169;139;187m'; R=$'\e[0m'
printf ' %s%s%s  %s%s ✧%s  %s%s ♡%s\n\n' "$P" "${k[RANDOM % ${#k[@]}]}" "$R" "$D" "$g" "$R" "$L" "${f[RANDOM % ${#f[@]}]}" "$R"
