import torch
import torch.nn as nn
import torch.optim as optim
import pickle
import time

## @class SolitaireNet
# @brief Neural net module for playing solitaire.
class SolitaireNet(nn.Module):
    ## @param input_size Size of the input layer
    # @return None
    def __init__(self, input_size):
        super(SolitaireNet, self).__init__()
        self.fc1 = nn.Linear(input_size, 2 * input_size)
        self.fc2 = nn.Linear(2 * input_size, 2 * input_size)
        self.fc3 = nn.Linear(2 * input_size, 4)

    ## @brief Performs a forward pass.
    # @param layer Input layer values
    # @return None
    def forward(self, layer):
        layer = torch.relu(self.fc1(layer))
        layer = torch.relu(self.fc2(layer))
        layer = self.fc3(layer)
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
        input_size = len(game.tableau) * len(game.tableau[0]) + 6
        ## @brief Neural net module
        # @hideinitializer
        self.__net = SolitaireNet(input_size)

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
            game_output.append(entity_names.index(card_structs[a][0]))
            game_output.append(card_structs[a][1])
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
        trans_output = torch.Tensor(self.__output_data) / 52
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.__net.parameters(), lr = 0.0005)
        # Used for displaying epoch results
        epoch_div = 0
        if max_epoch % 100 != max_epoch:
            epoch_div = round(max_epoch / 100)
        for epoch in range(max_epoch):
            self.__net.train()
            outputs = self.__net(trans_input)
            loss = criterion(outputs, trans_output)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if (epoch + 1) % epoch_div == 0 and epoch_div != 0:
                print(f'Epoch {epoch + 1}, Loss: {loss.item():.6f}')
            if epoch == max_epoch - 1:
                if epoch_div == 0 or (epoch + 1) % epoch_div != 0:
                    print(f'Epoch {epoch + 1}, Loss: {loss.item():.6f}')
        self.__save_net()

    ## @brief Plays solitaire using the trained nural net.
    # @return None
    def play_game(self):
        while not self.__game.quit:
            game_state = torch.Tensor(self.__get_input()) / 52
            move = (52 * self.__net(game_state)).round()
            self.__game.run_game()