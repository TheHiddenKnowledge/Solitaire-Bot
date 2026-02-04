import solitaire
import solitairesolver

GAME = solitaire.Solitaire()
SOLVER = solitairesolver.SolitaireSolver(GAME)

while not GAME.quit:
    SOLVER.get_input()
    prev_moves = GAME.moves
    GAME.run_game()
    if GAME.moves > prev_moves:
        SOLVER.get_output()
