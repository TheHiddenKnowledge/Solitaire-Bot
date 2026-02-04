import numpy as np

# Neural net input structure:
# Column vector
# Filled with card indices mostly
# Columns of the tableau stacked on top of eachother, with empties being zeroed
# Top most revealed stock card index, zero if empty
# Card count in the stock
# Foundation cards are recorded as the top most card index, with empties
# being zeroed

# Neural net output structure:
# From card origin
# From card
# To card origin
# To card

class SolitaireSolver:
    def __init__(self, game):
        self.__game = game
        input_size = len(game.tableau) * len(game.tableau[0]) + 6
        self.__input = np.zeros((input_size, 1))
        self.__output = np.zeros((4, 1))

    def get_input(self):
        input_idx = 0
        for a in range(len(self.__game.tableau)):
            for b in range(len(self.__game.tableau[a])):
                card_idx = self.__game.tableau[a][b]
                if card_idx >= 0:
                    if self.__game.cards[card_idx].flipped:
                        self.__input[input_idx, 0] = 0
                    else:
                        self.__input[input_idx, 0] = card_idx + 1
                else:
                    self.__input[input_idx, 0] = 0
                input_idx += 1
        if self.__game.stock_idx >= 0:
            self.__input[input_idx, 0] = (self.__game.stock[
                self.__game.stock_idx] + 1)
        else:
            self.__input[input_idx, 0] = 0
        input_idx += 1
        stock_count = 0
        for a in range(len(self.__game.stock)):
            if self.__game.stock[a] >= 0:
                stock_count += 1
        self.__input[input_idx, 0] = stock_count
        input_idx += 1
        for a in range(len(self.__game.found_idxs)):
            found_idx = 0
            for b in range(len(self.__game.found_idxs[a])):
                if self.__game.found_idxs[a][b] >= 0:
                    found_idx = self.__game.found_idxs[a][b]
                else:
                    break
            self.__input[input_idx, 0] = found_idx
            input_idx += 1

    def get_output(self):
        entity_names = ['none', 'stock_reveal', 'stock_hidden',
                        'foundation', 'tableau_card', 'tableau_pile']
        card_structs = [self.__game.from_entity, self.__game.to_entity]
        for a in range(2):
            self.__output[2 * a, 0] = entity_names.index(card_structs[a][0])
            self.__output[2 * a + 1, 0] = card_structs[a][1]
        print(self.__output)