## 2. Feature Extraction

给定一段音频，请提取12维MFCC特征，阅读代码预加重、分帧、加窗部分，完善作业代码中 fbank和mfcc部分，并给出最终的Fbank和MFCC特征，用默认的配置参数，无需进行修改。 

## 3. EM & GMM

实现基于 GMM 的 0(o)-9 孤立词识别系统

提供的数据：

* 330句训练预料，每个英文单词 (0-9，o) 含有 30 个句子用于训练对应的 GMM
* 所有的训练数据和测试数据的原始音频路径
* 对应的抄本 text (标注，0-9，o)
* 特征 (feats.scp, feats.ark) 都在 train 和 test 文件夹下

原始音频的 39 维 MFCC 特征已经通过 kaldi 提取给出，代码中也给出了读取 kaldi 格式特征的代码。 feats.scp 里面存储的是某句话的特征数据的真实文件和位置，特征实际存储在二进制文件 feats.ark 中 (可以忽略读取 kaldi 特征部分代码)。

使用提供的特征，完善代码中 GMM 参数估计部分，并且用测试数据对其进行测试，统计错误率。每一个孤立词建立一个 GMM 模型，高斯成分个数 K 可以自定，特征维度是 39 维。

## 4. HMM

考虑盒子和球模型 $\lambda=(A,B,\pi)$，状态集合 $Q=\{1,2,3\}$，观测集合 $V=\{红，白\}$ ， 
$$
A=\left[\begin{matrix}
   0.5 & 0.2 & 0.3 \\
   0.3 & 0.5 & 0.2 \\
   0.2 & 0.3 & 0.5
  \end{matrix}\right],
B=\left[\begin{matrix}
   0.5 & 0.5 \\
   0.4 & 0.6 \\
   0.7 & 0.3
  \end{matrix}\right],
\pi=(0.2,0.4,0.4)^T
$$


设 $T=3$，$O=\{红，白，红\}$， 

• 实现前向算法和后向算法，分别计算 $P(O|\lambda)$
• 实现Viterbi算法，求最优状态序列，即最优路径 $I^*=(i_1^*,i_2^*,i_3^*)$

## 5. GMM & HMM

基于GMM-HMM的语音识别系统

