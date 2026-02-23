import solitaire
import solitairesolver

GAME = solitaire.Solitaire()
SOLVER = solitairesolver.SolitaireSolver(GAME)

# SOLVER.gather_training()

SOLVER.train_net(20000)

# SOLVER.play_game()