import torch
import torch.nn as nn
import torch.optim as optim
from dataclasses import dataclass
from collections import deque
import random
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
        self.fc2 = nn.Linear(INPUT_SIZE, INPUT_SIZE)
        self.fc3 = nn.Linear(INPUT_SIZE, 2 * MOVES_SIZE + 2 * CARDS_SIZE)

    ## @brief Performs a forward pass.
    # @param layer Input layer values
    # @return None
    def forward(self, layer):
        layer = torch.sigmoid(self.fc1(layer))
        layer = torch.relu(self.fc2(layer))
        layer = torch.relu(self.fc2(layer))
        layer = self.fc3(layer)
        moves_2_idx = MOVES_SIZE + CARDS_SIZE
        card_2_idx = moves_2_idx + MOVES_SIZE + CARDS_SIZE
        moves_1 = layer[:, 0:MOVES_SIZE]
        cards_1 = layer[:, MOVES_SIZE:moves_2_idx]
        moves_2 = layer[:, moves_2_idx:moves_2_idx + MOVES_SIZE]
        cards_2 = layer[:, moves_2_idx + MOVES_SIZE:card_2_idx]
        layer = [moves_1, cards_1, moves_2, cards_2]
        return layer

@dataclass
class SolverParams:
    def __init__(self, batch_size = 50, memory_size = 1000, gamma = .99,
                 epsilon = 1, epsilon_min = .01, epsilon_decay = .995,
                 learning_rate = .001):
        self.batch_size = batch_size
        self.memory_size = memory_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate

## @class SolitaireSolver
# @brief Contains functions for training and running the neural net.
class SolitaireSolver:
    ## @param game Game instance object
    # @return None
    def __init__(self, game, params):
        ## @brief Game instance object
        # @hideinitializer
        self.__game = game
        ## @brief Solver paramas object
        # @hideinitializer
        self.__params = params
        self.__memory = deque(maxlen = params.memory_size)
        self.__device = (
            torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        ## @brief Policy neural net
        # @hideinitializer
        self.__policy_net = SolitaireNet().to(self.__device)
        ## @brief Target neural net (used for Q-learning stability)
        # @hideinitializer
        self.__target_net = SolitaireNet().to(self.__device)
        self.__target_net.load_state_dict(self.__policy_net.state_dict())
        self.__target_net.eval()
        self.__optimizer = optim.Adam(self.__policy_net.parameters(),
                                lr = self.__params.learning_rate)
        self.__loss = nn.MSELoss()

        # if not self.__load_net():
        #     print('No saved neural net present.')

    ## @brief Gets the current game state.
    # @return Game state array
    def get_state(self):
        game_state = []
        for a in range(len(self.__game.tableau)):
            for b in range(len(self.__game.tableau[a])):
                card_idx = self.__game.tableau[a][b]
                if card_idx >= 0:
                    if self.__game.cards[card_idx].flipped:
                        game_state.append(0)
                    else:
                        game_state.append(card_idx + 1)
                else:
                    game_state.append(0)
        if self.__game.stock_idx >= 0:
            game_state.append((self.__game.stock[
                self.__game.stock_idx] + 1))
        else:
            game_state.append(0)
        stock_count = 0
        for a in range(len(self.__game.stock)):
            if self.__game.stock[a] >= 0:
                stock_count += 1
        game_state.append(stock_count)
        for a in range(len(self.__game.found_idxs)):
            found_idx = 0
            for b in range(len(self.__game.found_idxs[a])):
                if self.__game.found_idxs[a][b] >= 0:
                    found_idx = self.__game.found_idxs[a][b]
                else:
                    break
            game_state.append(found_idx)
        return game_state

    ## @brief Gets the action to be taken based on the game state.
    # @return Action array
    def __get_action(self, state, epsilon):
        if random.random() < epsilon:
            return [random.randint(0, MOVES_SIZE - 1),
                    random.randint(0, CARDS_SIZE - 1),
                    random.randint(0, MOVES_SIZE - 1),
                    random.randint(0, CARDS_SIZE - 1)]
        else:
            action = []
            with torch.no_grad():
                tensor_state = torch.Tensor(state).unsqueeze(0).to(
                    self.__device)
                q_values = self.__policy_net(tensor_state)
            for q_value in q_values:
                action.append(torch.argmax(q_value).item())
            return action

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
    def __q_learn(self):
        if len(self.__memory) < self.__params.batch_size:
            return
        minibatch = random.sample(self.__memory, self.__params.batch_size)
        states, actions, rewards, next_states, dones = zip(*minibatch)
        states = torch.FloatTensor(states).to(self.__device)
        actions = torch.LongTensor(actions).to(self.__device)
        rewards = torch.FloatTensor(rewards).to(self.__device).unsqueeze(1)
        next_states = torch.FloatTensor(next_states).to(self.__device)
        dones = torch.FloatTensor(dones).to(self.__device).unsqueeze(1)
        for a in range(4):
            indices = actions[:, a].unsqueeze(1)
            current_q = self.__policy_net(states)[a].gather(1, indices)
            next_q = self.__target_net(next_states)[a].max(1)[0].detach().unsqueeze(1)
            target_q = rewards + (self.__params.gamma * next_q * (1 - dones))
            loss = self.__loss(current_q, target_q)
            self.__optimizer.zero_grad()
            loss.backward()
        self.__optimizer.step()

    ## @brief Plays solitaire using the trained nural net.
    # @return None
    def __step_game(self, action):
        state = self.get_state()
        entity_names = ['none', 'stock_reveal', 'stock_hidden',
                        'foundation', 'tableau_card', 'tableau_pile']
        self.__game.src_entity[0] = entity_names[int(action[0])]
        self.__game.src_entity[1] = int(action[1]) - 1
        self.__game.dest_entity[0] = entity_names[int(action[2])]
        self.__game.dest_entity[1] = int(action[3]) - 1
        reward = 0
        if (self.__game.src_entity == ['stock_hidden', 0]
                and self.__game.dest_entity == ['none', 0]):
            self.__game.increment_stock()
            reward = -1
        elif self.__game.move_cards():
            reward = self.__game.get_move_score()
        else:
            reward = -100
        self.__game.run_game(True)
        next_state = self.get_state()
        dones = self.__game.win
        return state, action, reward, next_state, dones

    def train_net(self, episodes, update_freq, max_moves):
        for episode in range(episodes):
            self.__game.reset_game()
            state = self.get_state()
            total_reward = 0
            for move in range(max_moves):
                action = self.__get_action(state, self.__params.epsilon)
                step_result = self.__step_game(action)
                self.__memory.append(step_result)
                state = step_result[3]
                total_reward += step_result[2] if (step_result[2] > 0) else 0
                self.__q_learn()
                if step_result[4]:
                    break
            if self.__params.epsilon > self.__params.epsilon_min:
                self.__params.epsilon *= self.__params.epsilon_decay

            if episode % update_freq == 0:
                self.__target_net.load_state_dict(
                    self.__policy_net.state_dict())
            print(
                f"Episode {episode}, Total Reward: {total_reward}, Epsilon: "
                f"{self.__params.epsilon:.3f}")

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