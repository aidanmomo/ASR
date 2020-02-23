## thchs DNN

https://github.com/kaldi-asr/kaldi/blob/master/egs/thchs30/s5/local/run_dnn.sh

Xent: Cross entropy

MPE: Minimum Phone Error

1. 提取 FBank 特征

``` bash
#generate fbanks
if [ $stage -le 0 ]; then
  echo "DNN training: stage 0: feature generation"
  rm -rf data/fbank && mkdir -p data/fbank &&  cp -R data/{train,dev,test,test_phone} data/fbank || exit 1;
  for x in train dev test; do
    echo "producing fbank for $x"
    #fbank generation
    steps/make_fbank.sh --nj $nj --cmd "$train_cmd" data/fbank/$x exp/make_fbank/$x fbank/$x || exit 1
    #ompute cmvn
    steps/compute_cmvn_stats.sh data/fbank/$x exp/fbank_cmvn/$x fbank/$x || exit 1
  done

  echo "producing test_fbank_phone"
  cp data/fbank/test/feats.scp data/fbank/test_phone && cp data/fbank/test/cmvn.scp data/fbank/test_phone || exit 1;
fi
```

2. xEnt 训练。用对齐的结果训练深度神经网络；使用 gmm 的解码图进行解码。
   * `train.sh`：`Usage: $0 <data-train> <data-dev> <lang-dir> <ali-train> <ali-dev> <exp-dir>`
   * `decosde.sh`：`Usage: $0 [options] <graph-dir> <data-dir> <decode-dir>`

``` bash
#xEnt training
if [ $stage -le 1 ]; then
  outdir=exp/tri4b_dnn
  #NN training
  (tail --pid=$$ -F $outdir/log/train_nnet.log 2>/dev/null)& # forward log
  $cuda_cmd $outdir/log/train_nnet.log \
    steps/nnet/train.sh --copy_feats false --cmvn-opts "--norm-means=true --norm-vars=false" --hid-layers 4 --hid-dim 1024 \
    --learn-rate 0.008 data/fbank/train data/fbank/dev data/lang $alidir $alidir_cv $outdir || exit 1;
  #Decode (reuse HCLG graph in gmmdir)
  (
    steps/nnet/decode.sh --nj $nj --cmd "$decode_cmd" --srcdir $outdir --config conf/decode_dnn.config --acwt 0.1 \
      $gmmdir/graph_word data/fbank/test $outdir/decode_test_word || exit 1;
  )&
  (
   steps/nnet/decode.sh --nj $nj --cmd "$decode_cmd" --srcdir $outdir --config conf/decode_dnn.config --acwt 0.1 \
     $gmmdir/graph_phone data/fbank/test_phone $outdir/decode_test_phone || exit 1;
  )&
fi
```

3. MPE 训练

``` bash
#MPE training
srcdir=exp/tri4b_dnn
acwt=0.1

if [ $stage -le 2 ]; then
  # generate lattices and alignments
  steps/nnet/align.sh --nj $nj --cmd "$train_cmd" \
    data/fbank/train data/lang $srcdir ${srcdir}_ali || exit 1;
  steps/nnet/make_denlats.sh --nj $nj --cmd "$decode_cmd" --config conf/decode_dnn.config --acwt $acwt \
    data/fbank/train data/lang $srcdir ${srcdir}_denlats || exit 1;
fi

if [ $stage -le 3 ]; then
  outdir=exp/tri4b_dnn_mpe
  #Re-train the DNN by 3 iteration of MPE
  steps/nnet/train_mpe.sh --cmd "$cuda_cmd" --num-iters 3 --acwt $acwt --do-smbr false \
    data/fbank/train data/lang $srcdir ${srcdir}_ali ${srcdir}_denlats $outdir || exit 1
  #Decode (reuse HCLG graph)
  for ITER in 3 2 1; do
   (
    steps/nnet/decode.sh --nj $nj --cmd "$decode_cmd" --nnet $outdir/${ITER}.nnet --config conf/decode_dnn.config --acwt $acwt \
      $gmmdir/graph_word data/fbank/test $outdir/decode_test_word_it${ITER} || exit 1;
   )&
   (
   steps/nnet/decode.sh --nj $nj --cmd "$decode_cmd" --nnet $outdir/${ITER}.nnet --config conf/decode_dnn.config --acwt $acwt \
     $gmmdir/graph_phone data/fbank/test_phone $outdir/decode_test_phone_it${ITER} || exit 1;
   )&
  done
fi
```

