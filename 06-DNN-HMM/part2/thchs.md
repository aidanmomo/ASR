## thchs30

https://github.com/kaldi-asr/kaldi/blob/master/egs/thchs30/s5/run.sh

1. 配置命令相关参数和数据路径。

``` bash
#!/usr/bin/env bash

. ./cmd.sh ## You'll want to change cmd.sh to something that will work on your system.
           ## This relates to the queue.
. ./path.sh

H=pwd  #exp home
n=8    #parallel jobs

#corpus and trans directory
thchs=/nfs/public/materials/data/thchs30-openslr

#you can obtain the database by uncommting the following lines
#[ -d $thchs ] || mkdir -p $thchs  || exit 1
#echo "downloading THCHS30 at $thchs ..."
#local/download_and_untar.sh $thchs  http://www.openslr.org/resources/18 data_thchs30  || exit 1
#local/download_and_untar.sh $thchs  http://www.openslr.org/resources/18 resource      || exit 1
#local/download_and_untar.sh $thchs  http://www.openslr.org/resources/18 test-noise    || exit 1
```

2. 数据准备，生成 Kaldi 格式数据到 data 目录下：word.txt (phone.txt), text, wav.scp, utt2spk, spk2utt。
   * test_phone 主要用于音素解码，即 text 文件为 phone。

``` bash
#data preparation
#generate text, wav.scp, utt2pk, spk2utt
local/thchs-30_data_prep.sh $H $thchs/data_thchs30 || exit 1;
```

3. 创建或清空 data/mfcc 目录，将数据复制到 data/mfcc 目录下。

``` bash
#produce MFCC features
rm -rf data/mfcc && mkdir -p data/mfcc &&  cp -R data/{train,dev,test,test_phone} data/mfcc || exit 1;
```

4. 提取 MFCC 特征和倒谱均值归一化到 mfcc 目录下，同时在 data/mfcc 目录下生成 scp 和 conf 等相关文件，在 exp (experiment) 目录下生成相关日志。
   * `make_mfcc.sh`：`Usage: $0 [options] <data-dir> [<log-dir> [<mfcc-dir>] ]`
   * `compute_cmvn_stats.sh`：`Usage: $0 [options] <data-dir> [<log-dir> [<cmvn-dir>] ]`

``` bash
for x in train dev test; do
   #make  mfcc
   steps/make_mfcc.sh --nj $n --cmd "$train_cmd" data/mfcc/$x exp/make_mfcc/$x mfcc/$x || exit 1;
   #compute cmvn
   steps/compute_cmvn_stats.sh data/mfcc/$x exp/mfcc_cmvn/$x mfcc/$x || exit 1;
done
```

5. 将 data/mfcc/test 目录下的 scp 文件复制到 test_phone 目录下，指向同样的特征数据。

``` bash
#copy feats and cmvn to test.ph, avoid duplicated mfcc & cmvn
cp data/mfcc/test/feats.scp data/mfcc/test_phone && cp data/mfcc/test/cmvn.scp data/mfcc/test_phone || exit 1;
```

6. 准备 word 级别语言模型图的相关数据。

   1. 复制 resource/dict 目录下的相关文件到 data/dict 目录下。
   2. 将语言模型的词典文件与 resource/dict/lexicon 合并到 data/dict 目录下。
   3. 将 data/dict 目录下的词典相关数据转化成 L.fst (Lexicon) 文件到 data/lang 目录下。
      * `prepare_lang.sh`：`Usage: utils/prepare_lang.sh <dict-src-dir> <oov-dict-entry> <tmp-dir> <lang-dir>`

   4. 将 data/lang 目录下的 L.fst 相关文件复制到 data/graph/lang 目录下，将 arpa 类型的 3gram 语言模型和对应的 lexicon 文件转换成 G.fst (Grammer)。
      * `format_lm.sh`：`Usage: $0 <lang_dir> <arpa-LM> <lexicon> <out_dir>`

``` bash
#prepare language stuff
#build a large lexicon that invovles words in both the training and decoding.
(
  echo "make word graph ..."
  cd $H; mkdir -p data/{dict,lang,graph} && \
  cp $thchs/resource/dict/{extra_questions.txt,nonsilence_phones.txt,optional_silence.txt,silence_phones.txt} data/dict && \
  cat $thchs/resource/dict/lexicon.txt $thchs/data_thchs30/lm_word/lexicon.txt | \
  grep -v '<s>' | grep -v '</s>' | sort -u > data/dict/lexicon.txt || exit 1;
  utils/prepare_lang.sh --position_dependent_phones false data/dict "<SPOKEN_NOISE>" data/local/lang data/lang || exit 1;
  gzip -c $thchs/data_thchs30/lm_word/word.3gram.lm > data/graph/word.3gram.lm.gz || exit 1;
  utils/format_lm.sh data/lang data/graph/word.3gram.lm.gz $thchs/data_thchs30/lm_word/lexicon.txt data/graph/lang || exit 1;
)
```

7. 音素级别，对应 data/{dict_phone,graph_phone,lang_phone}。

``` bash
#make_phone_graph
(
  echo "make phone graph ..."
  cd $H; mkdir -p data/{dict_phone,graph_phone,lang_phone} && \
  cp $thchs/resource/dict/{extra_questions.txt,nonsilence_phones.txt,optional_silence.txt,silence_phones.txt} data/dict_phone  && \
  cat $thchs/data_thchs30/lm_phone/lexicon.txt | grep -v '<eps>' | sort -u > data/dict_phone/lexicon.txt  && \
  echo "<SPOKEN_NOISE> sil " >> data/dict_phone/lexicon.txt  || exit 1;
  utils/prepare_lang.sh --position_dependent_phones false data/dict_phone "<SPOKEN_NOISE>" data/local/lang_phone data/lang_phone || exit 1;
  gzip -c $thchs/data_thchs30/lm_phone/phone.3gram.lm > data/graph_phone/phone.3gram.lm.gz  || exit 1;
  utils/format_lm.sh data/lang_phone data/graph_phone/phone.3gram.lm.gz $thchs/data_thchs30/lm_phone/lexicon.txt \
    data/graph_phone/lang  || exit 1;
)
```

8. 单音素的训练、测试和对齐。
   1. 训练：初始化 > 生成训练图 > 对标签进行初始化对齐 > 统计估计模型所需统计量 > 重新估计参数 > 重新对齐。
      * `train_mono.sh`：`Usage: steps/train_mono.sh [options] <data-dir> <lang-dir> <exp-dir>`
   2. 解码测试。
      * `thchs-30_decode.sh`：`mkgraph.sh` 和 `decode.sh`
   3. 对齐。
      * `align_si.sh`：`usage: steps/align_si.sh <data-dir> <lang-dir> <src-dir> <align-dir>`

``` bash
#monophone
steps/train_mono.sh --boost-silence 1.25 --nj $n --cmd "$train_cmd" data/mfcc/train data/lang exp/mono || exit 1;
#test monophone model
local/thchs-30_decode.sh --mono true --nj $n "steps/decode.sh" exp/mono data/mfcc &

#monophone_ali
steps/align_si.sh --boost-silence 1.25 --nj $n --cmd "$train_cmd" data/mfcc/train data/lang exp/mono exp/mono_ali || exit 1;
```

9. 三音素的训练、测试和对齐。
   * 训练：使用单音素模型的对齐结果对三音素参数统计，用于生成决策树 > 完成三音素聚类 > 将单音素对齐文件中的元素替换为决策树的叶子节点 >  生成训练图 > 迭代训练和对齐。
     * `train_deltas`：`Usage: steps/train_deltas.sh <num-leaves> <tot-gauss> <data-dir> <lang-dir> <alignment-dir> <exp-dir>`

``` bash
#triphone
steps/train_deltas.sh --boost-silence 1.25 --cmd "$train_cmd" 2000 10000 data/mfcc/train data/lang exp/mono_ali exp/tri1 || exit 1;
#test tri1 model
local/thchs-30_decode.sh --nj $n "steps/decode.sh" exp/tri1 data/mfcc &

#triphone_ali
steps/align_si.sh --nj $n --cmd "$train_cmd" data/mfcc/train data/lang exp/tri1 exp/tri1_ali || exit 1;
```

10. 线性判别分析与最大似然线性变换的训练、测试和对齐

``` bash
#lda_mllt
steps/train_lda_mllt.sh --cmd "$train_cmd" --splice-opts "--left-context=3 --right-context=3" 2500 15000 data/mfcc/train data/lang exp/tri1_ali exp/tri2b || exit 1;
#test tri2b model
local/thchs-30_decode.sh --nj $n "steps/decode.sh" exp/tri2b data/mfcc &

#lda_mllt_ali
steps/align_si.sh  --nj $n --cmd "$train_cmd" --use-graphs true data/mfcc/train data/lang exp/tri2b exp/tri2b_ali || exit 1;
```

11. 说话人自适应训练、测试和对齐

``` bash
#sat
steps/train_sat.sh --cmd "$train_cmd" 2500 15000 data/mfcc/train data/lang exp/tri2b_ali exp/tri3b || exit 1;
#test tri3b model
local/thchs-30_decode.sh --nj $n "steps/decode_fmllr.sh" exp/tri3b data/mfcc &

#sat_ali
steps/align_fmllr.sh --nj $n --cmd "$train_cmd" data/mfcc/train data/lang exp/tri3b exp/tri3b_ali || exit 1;
```

12. Quick 训练、测试和对齐

``` bash
#quick
steps/train_quick.sh --cmd "$train_cmd" 4200 40000 data/mfcc/train data/lang exp/tri3b_ali exp/tri4b || exit 1;
#test tri4b model
local/thchs-30_decode.sh --nj $n "steps/decode_fmllr.sh" exp/tri4b data/mfcc &

#quick_ali
steps/align_fmllr.sh --nj $n --cmd "$train_cmd" data/mfcc/train data/lang exp/tri4b exp/tri4b_ali || exit 1;

#quick_ali_cv
steps/align_fmllr.sh --nj $n --cmd "$train_cmd" data/mfcc/dev data/lang exp/tri4b exp/tri4b_ali_cv || exit 1;
```

13. DNN

``` bash
#train dnn model
local/nnet/run_dnn.sh --stage 0 --nj $n  exp/tri4b exp/tri4b_ali exp/tri4b_ali_cv || exit 1;
```

14. 训练去噪自编码器 (Denoising AutoEncoder, DAE) 模型

``` bash
#train dae model
#python2.6 or above is required for noisy data generation.
#To speed up the process, pyximport for python is recommeded.
local/dae/run_dae.sh $thchs || exit 1;
```

