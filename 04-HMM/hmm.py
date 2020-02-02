# Author: Kaituo Xu, Fan Yu
import numpy as np

def forward_algorithm(O, HMM_model):
    """HMM Forward Algorithm.
    Args:
        O: (o1, o2, ..., oT), observations
        HMM_model: (pi, A, B), (init state prob, transition prob, emitting prob)
    Return:
        prob: the probability of HMM_model generating O.
    """
    pi, A, B = HMM_model
    T = len(O)
    N = len(pi)
    prob = 0.0
    
    alpha = np.zeros([T, N])
    for t in range(T):
        for i in range(N):
            if t == 0:
                # initial
                alpha[t][i] = pi[i]
            else:
                # recursive
                for j in range(N):
                    alpha[t][i] += alpha[t - 1][j] * A[j][i]
            alpha[t][i] *= B[i][O[t]]
    # end
    for i in range(N):
        prob += alpha[T - 1][i]

    return prob

def backward_algorithm(O, HMM_model):
    """HMM Backward Algorithm.
    Args:
        O: (o1, o2, ..., oT), observations
        HMM_model: (pi, A, B), (init state prob, transition prob, emitting prob)
    Return:
        prob: the probability of HMM_model generating O.
    """
    pi, A, B = HMM_model
    T = len(O)
    N = len(pi)
    prob = 0.0

    beta = np.zeros([T, N])
    for t in reversed(range(T)):
        for i in range(N):
            if t == T - 1:
                # initial
                beta[t][i] = 1
            else:
                # recursive
                for j in range(N):
                    beta[t][i] += beta[t + 1][j] * A[i][j] * B[j][O[t + 1]]
    # end
    for i in range(N):
        prob += pi[i] * B[i][O[0]] * beta[0][i]

    return prob

def Viterbi_algorithm(O, HMM_model):
    """Viterbi decoding.
    Args:
        O: (o1, o2, ..., oT), observations
        HMM_model: (pi, A, B), (init state prob, transition prob, emitting prob)
    Returns:
        best_prob: the probability of the best state sequence
        best_path: the best state sequence
    """
    pi, A, B = HMM_model
    T = len(O)
    N = len(pi)
    best_prob = 0.0
    best_path = [0] * T
    
    delta = -np.inf * np.ones([T, N])
    phi = [[0] * T for row in range(N)]
    for t in range(T):
        for i in range(N):
            if t == 0:
                # initial
                delta[t][i] = pi[i]
                phi[t][i] = 0
            else:
                # recursive
                for j in range(N):
                    value = delta[t - 1][j] * A[j][i]
                    if value > delta[t][i]:
                        delta[t][i] = value
                        phi[t][i] = j + 1
            delta[t][i] *= B[i][O[t]]
        
    for i in range(N):
        # end
        if delta[T - 1][i] > best_prob:
            best_prob = delta[T - 1][i]
            best_path[T - 1] = i + 1
    
    for t in reversed(range(T - 1)):
        # backtracking, note that values in best_path range from 1 to N
        best_path[t] = phi[t + 1][best_path[t + 1] - 1]

    return best_prob, best_path


if __name__ == "__main__":
    color2id = { "RED": 0, "WHITE": 1 }
    # model parameters
    pi = [0.2, 0.4, 0.4]
    A = [[0.5, 0.2, 0.3],
         [0.3, 0.5, 0.2],
         [0.2, 0.3, 0.5]]
    B = [[0.5, 0.5],
         [0.4, 0.6],
         [0.7, 0.3]]
    # input
    observations = (0, 1, 0)
    HMM_model = (pi, A, B)
    # process
    observ_prob_forward = forward_algorithm(observations, HMM_model)
    print(observ_prob_forward)

    observ_prob_backward = backward_algorithm(observations, HMM_model)
    print(observ_prob_backward)

    best_prob, best_path = Viterbi_algorithm(observations, HMM_model) 
    print(best_prob, best_path)
