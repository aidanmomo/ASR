import librosa
import numpy as np
from scipy.fftpack import dct

# If you want to see the spectrogram picture
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def plot_spectrogram(spec, note, file_name):
    """ Draw the spectrogram picture
        :param spec: a feature_dim by num_frames array(real)
        :param note: title of the picture
        :param file_name: name of the file
    """ 
    fig = plt.figure(figsize=(20, 5))
    heatmap = plt.pcolor(spec)
    fig.colorbar(mappable=heatmap)
    plt.xlabel('Time(s)')
    plt.ylabel(note)
    plt.tight_layout()
    plt.savefig(file_name)

#preemphasis config 
alpha = 0.97

# Enframe config
frame_len = 400      # 25ms, fs=16kHz
frame_shift = 160    # 10ms, fs=16kHz
fft_len = 512

# Mel filter config
num_filter = 23
num_mfcc = 12

# Enframe with Hamming window function
def preemphasis(signal, coeff=alpha):
    """ Perform preemphasis on the input signal
        :param signal: the signal to filter
        :param coeff: the preemphasis coefficient. 0 is no filter, default is 0.97
        :returns: the filtered signal
    """
    return np.append(signal[0], signal[1:] - coeff * signal[:-1])

def enframe(signal, frame_len=frame_len, frame_shift=frame_shift, win=np.hamming(frame_len)):
    """ Enframe with Hamming widow function
        :param signal: the signal be enframed
        :param frame_len: the length of each frame
        :param frame_shift: the step between each frame
        :param win: window function, default Hamming
        :returns: the enframed signal, num_frames by frame_len array
    """
    num_samples = signal.size
    num_frames = np.floor((num_samples - frame_len) / frame_shift) + 1
    frames = np.zeros((int(num_frames), frame_len))
    for i in range(int(num_frames)):
        frames[i, :] = signal[i * frame_shift:i * frame_shift + frame_len] 
        frames[i, :] = frames[i, :] * win

    return frames

def get_spectrum(frames, fft_len=fft_len):
    """ Get spectrum using fft
        :param frames: the enframed signal, num_frames by frame_len array
        :param fft_len: FFT length, default 512
        :returns: spectrum, a num_frames by fft_len/2+1 array (real)
    """
    cFFT = np.fft.fft(frames, n=fft_len)
    valid_len = int(fft_len / 2) + 1
    spectrum = np.abs(cFFT[:, 0:valid_len])
    return spectrum

def fbank(spectrum, sampling_rate, num_filter=num_filter):
    """ Get mel filter bank feature from spectrum
        :param spectrum: a num_frames by fft_len/2+1 array(real)
        :param sampling_rate: the sampling rate of the signal
        :param num_filter: mel filters number, default 23
        :returns: fbank feature, a num_frames by num_filter array
        DON'T FORGET LOG OPRETION AFTER MEL FILTER!
    """
    def powspec(magspec, fft_len=fft_len):
        """ Compute the power spectrum
            :param magspec: the magnitude spectrum of each frame in frames
            :param fft_len: FFT length, default 512
            :returns: the power spectrum of the corresponding frame
        """
        powspec =  1.0 / fft_len * np.square(spectrum)
        return powspec

    def get_filterbanks(sampling_rate, num_filter=num_filter, fft_len=fft_len, low_freq=0, high_freq=None):
        """ Compute a Mel-filterbank. The filters are stored in the columns, the rows correspond to fft bins
            :param sampling_rate: the sampling rate of the signal
            :param num_filter: mel filters number, default 23
            :param fft_len: FFT length, default 512
            :param low_freq: lowest band edge of mel filters, default 0
            :param high_freq: highest band edge of mel filters, default sampling_rate / 2
            :returns: filterbank, each column holds 1 filter
        """
        def hz2mel(hz):
            """ Convert a value in Hertz to Mels
                :param hz: a value in Hertz
                :returns: a value in Mels
            """
            return 2595 * np.log10(1 + hz / 700.)
    
        def mel2hz(mel):
            """ Convert a value in Mels to Hertz
                :param hz: a value in Mels
                :returns: a value in Hertz
            """
            return 700 * (10 ** (mel / 2595.) - 1)

        high_freq = high_freq or sampling_rate / 2
        low_mel = hz2mel(low_freq)
        high_mel = hz2mel(high_freq)
        mel_points = np.linspace(low_mel, high_mel, num_filter + 2)
        hz_points = mel2hz(mel_points)
        bin = np.floor(hz_points / high_freq * (fft_len / 2))

        fbank = np.zeros((int(fft_len / 2 + 1), num_filter))
        for i in range(0, num_filter):
            begin = int(bin[i])
            center = int(bin[i + 1])
            end = int(bin[i + 2])
            for j in range(begin, center):
                fbank[j, i] = (j - bin[i]) / (bin[i + 1] - bin[i])
            for j in range(center, end):
                fbank[j, i] = (bin[i + 2] - j) / (bin[i + 2] - bin[i + 1])
        return fbank
    
    pspec = powspec(spectrum)
    feats = get_filterbanks(sampling_rate)
    feats = np.dot(pspec, feats)
    feats = np.log(np.where(feats == 0, np.finfo(float).eps, feats))
    return feats

def mfcc(fbank, num_mfcc=num_mfcc):
    """ Get mfcc feature from fbank feature
        :param fbank: a num_frames by num_filter array (real)
        :param num_mfcc: mfcc number, default 12
        :returns: mfcc feature, a num_frames by num_mfcc array
    """
    def lifter(cepstra, L=22):
        """ Apply a cepstral lifter to the matrix of cepstra. 
            This has the effect of increasing the magnitude of the high frequency DCT coeffs
            :param cepstra: the matrix of mel-cepstra, will be num_frames * num_mfcc in size
            :param L: the liftering coefficient to use. Default is 22. L <= 0 disables lifter
            :returns: cepstra after liftering
        """
        if L > 0:
            num_mfcc = cepstra.shape[1]
            n = np.arange(num_mfcc)
            lift = 1 + (L / 2.) * np.sin(np.pi * n / L)
            return lift * cepstra
        return cepstra

    feats = np.zeros((fbank.shape[0], num_mfcc))
    feats = dct(fbank, type=2, axis=1, norm='ortho')[:, 1:(num_mfcc + 1)]
    feats = lifter(feats)
    return feats

def write_file(feats, file_name):
    """ Write the feature to file
        :param feats: a num_frames by feature_dim array (real)
        :param file_name: name of the file
    """
    f = open(file_name, 'w')
    (row, col) = feats.shape
    for i in range(row):
        f.write('[')
        for j in range(col):
            f.write(str(feats[i, j]) + ' ')
        f.write(']\n')
    f.close()

def main():
    # Read wav file
    wav, sr = librosa.load('./test.wav', sr=None)
    signal = preemphasis(wav)
    frames = enframe(signal)
    spectrum = get_spectrum(frames)

    fbank_feats = fbank(spectrum, sr)
    plot_spectrogram(fbank_feats.T, 'Filter Bank', 'fbank.png')
    write_file(fbank_feats, './test.fbank')

    mfcc_feats = mfcc(fbank_feats)
    plot_spectrogram(mfcc_feats.T, 'MFCC', 'mfcc.png')
    write_file(mfcc_feats, './test.mfcc')

if __name__ == '__main__':
    main()
