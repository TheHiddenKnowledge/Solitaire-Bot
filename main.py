import solitaire
import solitairesolver

GAME = solitaire.Solitaire()
PARAMS = solitairesolver.SolverParams(batch_size=20, learning_rate=.001,
                                      gamma = .9)
SOLVER = solitairesolver.SolitaireSolver(GAME, PARAMS)

SOLVER.train_net(500, 1, 100)