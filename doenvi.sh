export PYTHONPATH=${DSKENV}/python${PYTHONPATH:+:${PYTHONPATH}}

envi() {
    source $DSKENV/bin/linux/envi_bsh $*
}
export -f envi

#alias envi='source ${DSKENV}/bin/linux/envi_bsh'
