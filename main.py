import solitaire
import solitairesolver

GAME = solitaire.Solitaire()
SOLVER = solitairesolver.SolitaireSolver(GAME)

# Comment as needed

# SOLVER.gather_training()

# SOLVER.train_net(10000)

# SOLVER.test_net()

SOLVER.play_game()