class Epsilon:
    def __init__(self):
        self._dim = 0
        self._obj = []

    def epsilon(self, solution, pareto):
        eps_j = 0.0
        eps_k = 0.0

        self._dim = len(pareto[0])
        self.set_params()

        eps = float("-inf")

        for i in range(len(solution)):
            for j in range(len(pareto)):
                for k in range(self._dim):
                    if self._obj[k] == 0:
                        eps_temp = pareto[j][k] - solution[i][k]
                    else:
                        eps_temp = solution[i][k] - pareto[j][k]

                    if k == 0:
                        eps_k = eps_temp
                    elif eps_k < eps_temp:
                        eps_k = eps_temp
                if j == 0:
                    eps_j = eps_k
                elif eps_j > eps_k:
                    eps_j = eps_k
            if i == 0:
                eps = eps_j
            elif eps < eps_j:
                eps = eps_j

        return eps

    def set_params(self):
        self._obj = [0 for _ in range(self._dim)]


if __name__ == "__main__":
    opt = [[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]]
    mine = [[0.3, 1.5, 1.3]]
    eps = Epsilon()
    print(eps.epsilon(mine, opt))
