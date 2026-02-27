import torch
import torch.nn as nn
import torch.optim as optim
import pickle
import time

## @brief Input size of the neural net
# @hideinitializer
INPUT_SIZE = 7 * 20 + 6
## @brief Move list size of the neural net output
# @hideinitializer
MOVES_SIZE = 6
## @brief Card list size of the neural net output
# @hideinitializer
CARDS_SIZE = 53

## @class SolitaireNet
# @brief Neural net module for playing solitaire.
class SolitaireNet(nn.Module):
    # @return None
    def __init__(self):
        super(SolitaireNet, self).__init__()
        self.fc1 = nn.Linear(INPUT_SIZE, INPUT_SIZE)
        self.fc2 = nn.Linear(2 * INPUT_SIZE, 2 * INPUT_SIZE)
        self.fc3 = nn.Linear(INPUT_SIZE, 2 * MOVES_SIZE + 2 * CARDS_SIZE)

    ## @brief Performs a forward pass.
    # @param layer Input layer values
    # @return None
    def forward(self, layer):
        layer = torch.sigmoid(self.fc1(layer))
        # layer = torch.relu(self.fc2(layer))
        layer = self.fc3(layer)
        moves_2_idx = MOVES_SIZE + CARDS_SIZE
        card_2_idx = moves_2_idx + MOVES_SIZE + CARDS_SIZE
        moves_1 = layer[:, 0:MOVES_SIZE]
        cards_1 = layer[:, MOVES_SIZE:moves_2_idx]
        moves_2 = layer[:, moves_2_idx:moves_2_idx + MOVES_SIZE]
        cards_2 = layer[:, moves_2_idx + MOVES_SIZE:card_2_idx]
        layer = [moves_1, cards_1, moves_2, cards_2]
        return layer

## @class SolitaireSolver
# @brief Contains functions for training and running the neural net.
class SolitaireSolver:
    ## @param game Game instance object
    # @return None
    def __init__(self, game):
        ## @brief Game instance object
        # @hideinitializer
        self.__game = game
        ## @brief Neural net module
        # @hideinitializer
        self.__net = SolitaireNet()

        ## @brief Input data array
        # @hideinitializer
        self.__input_data = []
        ## @brief Output data array
        # @hideinitializer
        self.__output_data = []

        if not self.__load_training():
            print('No training data present.')
        if not self.__load_net():
            print('No saved neural net present.')

    ## @brief Gets the neural net input from the current game state.
    # @return Input array
    def __get_input(self):
        game_input = []
        for a in range(len(self.__game.tableau)):
            for b in range(len(self.__game.tableau[a])):
                card_idx = self.__game.tableau[a][b]
                if card_idx >= 0:
                    if self.__game.cards[card_idx].flipped:
                        game_input.append(0)
                    else:
                        game_input.append(card_idx + 1)
                else:
                    game_input.append(0)
        if self.__game.stock_idx >= 0:
            game_input.append((self.__game.stock[
                self.__game.stock_idx] + 1))
        else:
            game_input.append(0)
        stock_count = 0
        for a in range(len(self.__game.stock)):
            if self.__game.stock[a] >= 0:
                stock_count += 1
        game_input.append(stock_count)
        for a in range(len(self.__game.found_idxs)):
            found_idx = 0
            for b in range(len(self.__game.found_idxs[a])):
                if self.__game.found_idxs[a][b] >= 0:
                    found_idx = self.__game.found_idxs[a][b]
                else:
                    break
            game_input.append(found_idx)
        return game_input

    ## @brief Gets the neural net output from the current game state.
    # @return Output array
    def __get_output(self):
        game_output = []
        entity_names = ['none', 'stock_reveal', 'stock_hidden',
                        'foundation', 'tableau_card', 'tableau_pile']
        card_structs = [self.__game.src_entity, self.__game.dest_entity]
        for a in range(2):
            moves_output = []
            for b in range(MOVES_SIZE):
                move_idx = entity_names.index(card_structs[a][0])
                if b == move_idx:
                    moves_output.append(1)
                else:
                    moves_output.append(0)
            cards_output = []
            for b in range(CARDS_SIZE):
                card_idx = card_structs[a][1]
                if (card_structs[a][0]
                    in ['foundation', 'tableau_card', 'tableau_pile']):
                    card_idx += 1
                if b == card_idx:
                    cards_output.append(1)
                else:
                    cards_output.append(0)
            game_output.append(moves_output)
            game_output.append(cards_output)
        return game_output

    ## @brief Loads the training data from file.
    # @return True if the file exists
    def __load_training(self):
        try:
            with open('data/data.pkl', 'rb') as file:
                self.__input_data, self.__output_data = pickle.load(file)
            return True
        except FileNotFoundError:
            return False

    ## @brief Saves the training data to file.
    # @return None
    def __save_training(self):
        with open('data/data.pkl', 'wb') as file:
            pickle.dump((self.__input_data, self.__output_data), file)

    ## @brief Runs a game loop used to gather training data.
    # @return None
    def gather_training(self):
        while not self.__game.quit:
            game_state = self.__get_input()
            self.__game.run_game()
            if self.__game.move_made:
                self.__input_data.append(game_state)
                self.__output_data.append(self.__get_output())
        if self.__game.quit:
            self.__save_training()

    ## @brief Loads the neural net from file.
    # @return True if the file exists
    def __load_net(self):
        try:
            self.__net.load_state_dict(torch.load('data/solver_net.pt'))
            return True
        except FileNotFoundError:
            return False

    ## @brief Saves the neural net to file.
    # @return None
    def __save_net(self):
        torch.save(self.__net.state_dict(), 'data/solver_net.pt')

    ## @brief Trains the neural net for a given amount of epochs.
    # @param max_epoch Maximum epoch count for training
    # @return None
    def train_net(self, max_epoch):
        # Normalizing training data
        trans_input = torch.Tensor(self.__input_data) / 52
        trans_output = []
        for a in range(len(self.__output_data[0])):
            temp_list = []
            for b in range(len(self.__output_data)):
                temp_list.append(self.__output_data[b][a])
            trans_output.append(torch.Tensor(temp_list))
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.__net.parameters(), lr = 0.01)
        # Used for displaying epoch results
        epoch_div = 0
        if max_epoch % 100 != max_epoch:
            epoch_div = round(max_epoch / 100)
        for epoch in range(max_epoch):
            self.__net.train()
            outputs = self.__net(trans_input)
            optimizer.zero_grad()
            total_loss = 0
            for a in range(len(trans_output)):
                loss = criterion(outputs[a], trans_output[a])
                loss.backward(retain_graph = True)
                total_loss += loss.item() / 4
            optimizer.step()
            if (epoch + 1) % epoch_div == 0 and epoch_div != 0:
                print(f'Epoch {epoch + 1}, Loss: {total_loss:.6f}')
            if epoch == max_epoch - 1:
                if epoch_div == 0 or (epoch + 1) % epoch_div != 0:
                    print(f'Epoch {epoch + 1}, Loss: {total_loss:.6f}')
        self.__save_net()

    def test_net(self):
        fail_count = 0
        trans_input = torch.Tensor(self.__input_data) / 52
        trans_output = self.__net(trans_input)
        for a in range(len(self.__output_data)):
            pass_test = 1
            actual_list = []
            expected_list = []
            for b in range(len(self.__output_data[0])):
                soft_max = trans_output[b][a].softmax(dim = 0).tolist()
                actual_value = soft_max.index(max(soft_max))
                actual_list.append(actual_value)
                expected_value = self.__output_data[a][b].index(
                    max(self.__output_data[a][b]))
                expected_list.append(expected_value)
                if actual_value != expected_value:
                    pass_test *= 0
            if not pass_test:
                print('TEST FAILED   Item: ' + str(a + 1) + ' Actual: ' + str(
                    actual_list),
                      ' Expected: ' + str(expected_list))
                fail_count += 1
        if fail_count > 0:
            print('TEST FAILED!')
            print('Set count: ' + str(len(self.__output_data)))
        else:
            print('TEST PASSED!')
            print('Set count: ' + str(len(self.__output_data)))


    ## @brief Plays solitaire using the trained nural net.
    # @return None
    def play_game(self):
        while not self.__game.quit:
            game_state = torch.Tensor([self.__get_input()]) / 52
            net_output = self.__net(game_state)
            move = []
            for a in range(len(net_output)):
                soft_max = net_output[a][0].softmax(dim = 0).tolist()
                move.append(soft_max.index(max(soft_max)))
            print(self.format_move(move))
            self.__game.run_game()

    ## @brief Formats the move array for display.
    # @return Formatted array
    def format_move(self, move):
        formatted_move = []
        entity_names = ['none', 'stock_reveal', 'stock_hidden',
                        'foundation', 'tableau_card', 'tableau_pile']
        card_suits = ['Club', 'Spade', 'Diamond', 'Heart']
        card_ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                      'Jack', 'Queen', 'King']
        for a in range(2):
            formatted_move.append(entity_names[move[2 * a]])
            if move[2 * a] == 4:
                card_suit = card_suits[int((move[2 * a + 1] - 1) / 13)]
                card_rank = card_ranks[int((move[2 * a + 1] - 1) % 13)]
                formatted_move.append(card_suit + ', ' + card_rank)
        return formatted_move