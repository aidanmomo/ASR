ref=$1
reco=$2

python convert_fmt.py $ref ${ref}.fmt
python convert_fmt.py $reco ${reco}.fmt

python2 compute-wer.pyc --v=1 ${ref}.fmt ${reco}.fmt