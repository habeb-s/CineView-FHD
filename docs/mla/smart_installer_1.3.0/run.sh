#!/bin/bash
# Static compatibility of the three approved builds against every image release line in the requested ranges.
# Reference = the enigma2 commit each package was device-verified on. Targets = first and last release of each line.
set -u
cd ~/cineview-mla
OUT=rangecheck/out; mkdir -p $OUT rangecheck/wt
wt() {  # wt <repo> <commit> -> worktree path
	local R=$1 C=$2 P=$HOME/cineview-mla/rangecheck/wt/$(basename $1)_$2
	[ -d $P ] || git -C $R worktree add --detach -f $P $C >/dev/null 2>&1
	echo $P
}
run() {  # run <label> <build> <repo> <ref> <target>
	local REF=$(wt $3 $4) TGT=$(wt $3 $5)
	python3 mi/tools/mla/compat_image.py $2 $REF $TGT > $OUT/$1.txt 2>&1; echo "$1 rc=$? $(tail -1 $OUT/$1.txt)"
}
git -C e2git fetch -q origin 7.5 7.6 master 2>/dev/null
A75=$(git -C e2git rev-parse --short origin/7.5); A76=$(git -C e2git rev-parse --short origin/7.6); AM=$(git -C e2git rev-parse --short origin/master)
run atv_7.5_last  build_fatv e2git 57b7a51 $A75
run atv_7.6_last  build_fatv e2git 57b7a51 $A76
run atv_master    build_fatv e2git 57b7a51 $AM
run vix_6.7.000   build_fopenvix vixgit d3f089af4e 88659abfa
run vix_6.7.020   build_fopenvix vixgit d3f089af4e c342c745b
run vix_6.8.001   build_fopenvix vixgit d3f089af4e 689303c4b
run vix_6.8.009   build_fopenvix vixgit d3f089af4e c3a8d07ea
run vix_6.9.003   build_fopenvix vixgit d3f089af4e 38d3988a8
git -C bhgit fetch -q origin 2>/dev/null
run bh_6.0.004    build_fopenbh bhgit 52dedddc31 d7fa81a68b
run bh_py314_head build_fopenbh bhgit 52dedddc31 $(git -C bhgit rev-parse --short origin/Python3.14)
echo ALLDONE
