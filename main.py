import solitaire
import solitairesolver

GAME = solitaire.Solitaire()
# PARAMS = solitairesolver.SolverParams(batch_size=50, learning_rate=.01,
#                                       gamma=.9, guess_limit=100)
# SOLVER = solitairesolver.SolitaireSolver(GAME, PARAMS)

while not GAME.quit:
    GAME.run_game(False)
    GAME.draw_game()

# SOLVER.train_net(250, 5, 100)