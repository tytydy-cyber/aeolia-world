#!/bin/zsh
set -euo pipefail
here=${0:a:h}; generated="$here/generated-cinematic"; clips="$generated/clips"; output="$here/../../outputs/assets/aeolia-introduction.mp4"; mkdir -p "$clips" "${output:h}"
for spec in 'islands-wide 13.85' 'facility 15' 'suburb-wide 12' 'playroom-rainbow 12.86'; do
  set -- ${(z)spec}; name=$1; fps=$2
  ffmpeg -y -hide_banner -loglevel error -framerate "$fps" -i "$generated/clip-$name/%04d.jpg" -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,minterpolate=fps=30:mi_mode=blend,format=yuv420p" -c:v libx264 -crf 18 -preset medium -an "$clips/$name.mp4"
done
for spec in 'opening 1.1' 'ending 1.5'; do set -- ${(z)spec}; ffmpeg -y -hide_banner -loglevel error -loop 1 -i "$generated/card-$1.jpg" -t "$2" -r 30 -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p" -c:v libx264 -crf 18 -preset medium -an "$clips/card-$1.mp4"; done
cat > "$clips/concat.txt" <<'EOF'
file 'card-opening.mp4'
file 'islands-wide.mp4'
file 'facility.mp4'
file 'suburb-wide.mp4'
file 'playroom-rainbow.mp4'
file 'card-ending.mp4'
EOF
ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$clips/concat.txt" -c copy "$clips/picture.mp4"
duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$clips/picture.mp4")
ffmpeg -y -hide_banner -loglevel error -f lavfi -i "aevalsrc=0.025*sin(2*PI*(92+8*sin(2*PI*.035*t))*t)+0.014*sin(2*PI*138.59*t)+0.009*sin(2*PI*184.99*t)+0.004*sin(2*PI*.22*t)*sin(2*PI*369.99*t):s=48000:d=$duration" -af "lowpass=f=2100,aecho=.75:.82:760:.28,afade=t=in:d=2,afade=t=out:st=$(awk -v d="$duration" 'BEGIN{print d-3}'):d=3,alimiter=limit=.8" -c:a aac -b:a 192k "$generated/music.m4a"
ffmpeg -y -hide_banner -loglevel error -i "$clips/picture.mp4" -i "$generated/music.m4a" -map 0:v -map 1:a -c copy -shortest -movflags +faststart "$output"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$output"
