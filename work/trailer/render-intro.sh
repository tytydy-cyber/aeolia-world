#!/bin/zsh
set -euo pipefail
here=${0:a:h}
generated="$here/generated"
clips="$generated/clips"
exports="$here/../../exports"
mkdir -p "$clips" "$exports"

wide="split[bg][fg];[bg]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,gblur=sigma=28[blur];[fg]scale=-2:720[front];[blur][front]overlay=(W-w)/2:0,format=yuv420p"

for name in islands facility suburb playroom making; do
  ffmpeg -y -hide_banner -loglevel error -framerate 6.4 -i "$generated/clip-$name/%04d.jpg" -vf "$wide,minterpolate=fps=30:mi_mode=blend" -c:v libx264 -crf 19 -preset medium -an "$clips/$name.mp4"
done

for spec in 'opening 3.2' 'islands 1.0' 'facility 1.0' 'suburb 1.0' 'playroom 1.0' 'making 2.4' 'ending 5.5'; do
  set -- ${(z)spec}
  ffmpeg -y -hide_banner -loglevel error -loop 1 -i "$generated/card-$1.jpg" -t "$2" -r 30 -vf "$wide" -c:v libx264 -crf 18 -preset medium -an "$clips/card-$1.mp4"
done

cat > "$clips/concat.txt" <<'EOF'
file 'card-opening.mp4'
file 'card-islands.mp4'
file 'islands.mp4'
file 'card-facility.mp4'
file 'facility.mp4'
file 'card-suburb.mp4'
file 'suburb.mp4'
file 'card-playroom.mp4'
file 'playroom.mp4'
file 'card-making.mp4'
file 'making.mp4'
file 'card-ending.mp4'
EOF
ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$clips/concat.txt" -c copy "$clips/picture.mp4"

say -v Kyoko -r 240 -f "$here/narration.txt" -o "$generated/narration.aiff"
[[ $(stat -f%z "$generated/narration.aiff") -gt 4096 ]] || { print -u2 'ナレーションの生成に失敗しました'; exit 1; }
duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$clips/picture.mp4")
ffmpeg -y -hide_banner -loglevel error -f lavfi -i "aevalsrc=0.018*(sin(2*PI*110*t)+0.55*sin(2*PI*164.81*t)+0.35*sin(2*PI*220*t))+0.006*sin(2*PI*2*t)*sin(2*PI*329.63*t):s=48000:d=$duration" -af "lowpass=f=1800,aecho=0.7:0.75:700:0.18,afade=t=in:d=2,afade=t=out:st=$(awk -v d="$duration" 'BEGIN{print d-3}'):d=3" "$generated/music.wav"
ffmpeg -y -hide_banner -loglevel error -i "$generated/music.wav" -i "$generated/narration.aiff" -filter_complex "[0:a]volume=0.8[bg];[1:a]volume=1.35[voice];[bg][voice]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.92[a]" -map "[a]" -c:a aac -b:a 192k "$generated/mix.m4a"
ffmpeg -y -hide_banner -loglevel error -i "$clips/picture.mp4" -i "$generated/mix.m4a" -map 0:v -map 1:a -c:v copy -c:a copy -shortest -movflags +faststart "$exports/aeolia-workshop-intro.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$exports/aeolia-workshop-intro.mp4"
