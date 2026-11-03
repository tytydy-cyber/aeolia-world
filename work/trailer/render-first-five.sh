#!/bin/zsh
set -euo pipefail
here=${0:a:h}; generated="$here/generated-first-five"; exports="$here/../../exports"; mkdir -p "$generated/clips" "$exports"
for spec in 'drop 7.78' 'reveal 9' 'bridge 9.13'; do set -- ${(z)spec}; ffmpeg -y -hide_banner -loglevel error -framerate "$2" -i "$generated/$1/%04d.jpg" -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,minterpolate=fps=30:mi_mode=blend,format=yuv420p" -c:v libx264 -crf 18 -preset medium -an "$generated/clips/$1.mp4"; done
cat > "$generated/clips/concat.txt" <<'EOF'
file 'drop.mp4'
file 'reveal.mp4'
file 'bridge.mp4'
EOF
ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$generated/clips/concat.txt" -c copy "$generated/picture.mp4"
ffmpeg -y -hide_banner -loglevel error -f lavfi -i "anoisesrc=color=pink:amplitude=.025:sample_rate=48000:duration=5" -f lavfi -i "sine=frequency=92:sample_rate=48000:duration=5" -filter_complex "[0:a]lowpass=f=1200,afade=t=in:d=0.2,volume=.75[wind];[1:a]volume=.08,afade=t=in:st=0.8:d=1[tone];[wind][tone]amix=inputs=2,alimiter=limit=.8[a]" -map "[a]" -c:a aac -b:a 160k "$generated/sound.m4a"
ffmpeg -y -hide_banner -loglevel error -i "$generated/picture.mp4" -i "$generated/sound.m4a" -map 0:v -map 1:a -c copy -shortest -movflags +faststart "$exports/aeolia-first-five.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$exports/aeolia-first-five.mp4"
