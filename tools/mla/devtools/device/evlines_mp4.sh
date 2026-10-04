#!/bin/bash
# Side-by-side MP4 (left: Classic continuous swim, right: line jumps) from the fbrec recordings, real 10 fps.
cd ~/cineview-mla/shots/evlines
for c in en_now ar_now en_next live_next; do
  for v in classic lines; do
    python3 - $v_$c <<EOF
import struct
d=open("${v}_${c}.bin","rb").read(); w,h,n=struct.unpack("<III",d[6:18]); off=18+8*n
open("${v}_${c}.rgb","wb").write(d[off:]); open("${v}_${c}.size","w").write("%dx%d"%(w,h))
EOF
  done
  S=$(cat classic_$c.size)
  ffmpeg -loglevel error -y -f rawvideo -pix_fmt rgb24 -s $S -r 10 -i classic_$c.rgb -f rawvideo -pix_fmt rgb24 -s $S -r 10 -i lines_$c.rgb \
    -filter_complex "[0:v]pad=iw+16:ih:0:0:white[a];[a][1:v]hstack=inputs=2,pad=iw:ih+1:0:0:white,format=yuv420p" -c:v libx264 -crf 20 -movflags +faststart cmp_$c.mp4
  rm -f classic_$c.rgb lines_$c.rgb classic_$c.size lines_$c.size
  ls -la cmp_$c.mp4
done
