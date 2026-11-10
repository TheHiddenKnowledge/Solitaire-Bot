import torch
import torch.nn as nn
import torch.optim as optim
from dataclasses import dataclass
from collections import deque
import random
import pickle
import math
import time
import gc

## @brief Input size of the neural net
# @hideinitializer
INPUT_SIZE = (2 * 7 * 20) + (2 * 5)
## @brief Move list size of the neural net output
# @hideinitializer
MOVES_SIZE = 6
## @brief Suit list size of the neural net output
# @hideinitializer
SUITS_SIZE = 5
## @brief Rank list size of the neural net output
# @hideinitializer
RANKS_SIZE = 14

## @class SolitaireNet
# @brief Neural net module for playing solitaire.
class SolitaireNet(nn.Module):
    # @return None
    def __init__(self, input_size, output_size):
        super(SolitaireNet, self).__init__()
        avg_size = math.ceil((input_size + output_size) / 2)
        self.fc1 = nn.Linear(input_size, avg_size)
        self.fc2 = nn.Linear(avg_size, avg_size)
        self.fc3 = nn.Linear(avg_size, output_size)

    ## @brief Performs a forward pass.
    # @param layer Input layer values
    # @return None
    def forward(self, layer):
        layer = torch.relu(self.fc1(layer))
        layer = torch.relu(self.fc2(layer))
        layer = self.fc3(layer)
        return layer

## @class SolverParams
# @brief Structure used for defining solver parameters.
@dataclass
class SolverParams:
    batch_size: int = 50
    memory_size: int = 1000
    gamma: float = .99
    epsilon: int = 1
    epsilon_min: float = .01
    epsilon_decay: float = .995
    learning_rate: float = .001
    guess_limit: int = 1000

## @class SolitaireSolver
# @brief Contains functions for training and running the neural net.
class SolitaireSolver:
    ## @param game Game instance object
    # @param params Solver parameters object
    # @return None
    def __init__(self, game, params):
        ## @brief Game instance object
        # @hideinitializer
        self.__game = game
        ## @brief Solver parameters object
        # @hideinitializer
        self.__params = params
        ## @brief Memory for storing game data used during training
        # @hideinitializer
        self.__memory = deque(maxlen = params.memory_size)
        ## @brief Device used by torch
        # @hideinitializer
        self.__device = (
            torch.device("cuda" if torch.cuda.is_available() else "cpu"))

        input_sizes = [INPUT_SIZE, INPUT_SIZE, INPUT_SIZE,
                       INPUT_SIZE, INPUT_SIZE, INPUT_SIZE]
        output_sizes = [MOVES_SIZE, SUITS_SIZE, RANKS_SIZE,
                        MOVES_SIZE, SUITS_SIZE, RANKS_SIZE]
        ## @brief Policy neural nets
        # @hideinitializer
        self.__policy_nets = []
        ## @brief Target neural nets (used for Q-learning stability)
        # @hideinitializer
        self.__target_nets = []
        ## @brief Optimizers used to train neural nets
        # @hideinitializer
        self.__optimizers = []
        for a in range(len(input_sizes)):
            self.__policy_nets.append(
                SolitaireNet(input_sizes[a], output_sizes[a]).to(self.__device))
            self.__target_nets.append(
                SolitaireNet(input_sizes[a], output_sizes[a]).to(self.__device))
            self.__target_nets[a].load_state_dict(
                self.__policy_nets[a].state_dict())
            self.__target_nets[a].eval()
            self.__optimizers.append(
                optim.Adam(self.__policy_nets[a].parameters(),
                                lr = self.__params.learning_rate))
        ## @brief Object used to calculate loss for gradient descent
        # @hideinitializer
        self.__loss = nn.MSELoss()
        ## @brief Array of valid actions used for random action selection
        # @hideinitializer
        self.__valid_actions = self.__get_valid_actions()

        # if not self.__load_net():
        #     print('No saved neural net present.')

    def __del__(self):
        self.__memory.clear()
        gc.collect()

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
                        game_state.append(0)
                    else:
                        game_state.append(self.__game.cards[card_idx].suit + 1)
                        game_state.append(self.__game.cards[card_idx].rank + 1)
                else:
                    game_state.append(0)
                    game_state.append(0)
        if self.__game.stock_idx >= 0:
            card_idx = self.__game.stock[self.__game.stock_idx]
            game_state.append(self.__game.cards[card_idx].suit + 1)
            game_state.append(self.__game.cards[card_idx].rank + 1)
        else:
            game_state.append(0)
            game_state.append(0)
        for a in range(len(self.__game.found_idxs)):
            card_idx = -1
            for b in range(len(self.__game.found_idxs[a])):
                if self.__game.found_idxs[a][b] >= 0:
                    card_idx = self.__game.found_idxs[a][b] + 1
                else:
                    break
            if card_idx >= 0:
                game_state.append(self.__game.cards[card_idx].suit + 1)
                game_state.append(self.__game.cards[card_idx].rank + 1)
            else:
                game_state.append(0)
                game_state.append(0)
        return game_state

    ## @brief Reduces the action space to only the allowable actions.
    # @return Valid action space
    def __get_valid_actions(self):
        action_space = []
        for a in range(3):
            action_space.append([a, 0, 0])
        for a in range(4):
            action_space.append([3, a + 1, 0])
        for a in range(4):
            for b in range(13):
                action_space.append([4, a + 1, b + 1])
        for a in range(7):
            action_space.append([5, 0, a + 1])
        return action_space

    ## @brief Gets the action to be taken based on the game state.
    # @param state Current game state
    # @param epsilon Current epsilon value
    # @return Action array
    def __get_action(self, state, epsilon):
        if random.random() < epsilon:
            action = []
            for a in range(self.__params.guess_limit):
                src_action_idx = (
                    random.randint(0, len(self.__valid_actions) - 1))
                src_action = self.__valid_actions[int(src_action_idx)]
                dest_action_idx = (
                    random.randint(0,len(self.__valid_actions) - 1))
                dest_action = self.__valid_actions[int(dest_action_idx)]
                action = [src_action[0], src_action[1], src_action[2],
                          dest_action[0], dest_action[1], dest_action[2]]
                self.__format_action(action)
                if (self.__game.src_entity == ['stock_hidden', -1]
                        and self.__game.dest_entity == ['none', -1]):
                    break
                if self.__game.can_card_move():
                    break
            return action, 'guess'
        else:
            action = []
            with torch.no_grad():
                for policy_net in self.__policy_nets:
                    tensor_state = torch.Tensor(state).unsqueeze(0).to(
                        self.__device)
                    q_values = policy_net(tensor_state)
                    action.append(torch.argmax(q_values).item())
            return action, 'model'

    ## @brief Formats the neural net output to be used in the game engine.
    # @return None
    def __format_action(self, action):
        trans_action = action.copy()
        for a in range(len(trans_action)):
            trans_action[a] = int(trans_action[a])
        trans_action[1] -= 1
        trans_action[2] -= 1
        trans_action[4] -= 1
        trans_action[5] -= 1
        entity_names = ['none', 'stock_reveal', 'stock_hidden',
                        'foundation', 'tableau_card', 'tableau_pile']
        self.__game.src_entity[0] = entity_names[trans_action[0]]
        match self.__game.src_entity[0]:
            case 'foundation':
                self.__game.src_entity[1] = trans_action[1]
            case 'tableau_card':
                if trans_action[1] > 0 and trans_action[2] > 0:
                    card_idx = 13 * trans_action[1] + trans_action[2]
                    self.__game.src_entity[1] = card_idx
                else:
                    self.__game.src_entity[1] = -1
            case 'tableau_pile':
                self.__game.src_entity[1] = trans_action[1]
            case _:
                self.__game.src_entity[1] = trans_action[1]
        self.__game.dest_entity[0] = entity_names[trans_action[3]]
        match self.__game.dest_entity[0]:
            case 'foundation':
                self.__game.dest_entity[1] = trans_action[4]
            case 'tableau_card':
                if trans_action[4] > 0 and trans_action[5] > 0:
                    card_idx = 13 * trans_action[4] + trans_action[5]
                    self.__game.dest_entity[1] = card_idx
                else:
                    self.__game.dest_entity[1] = -1
            case 'tableau_pile':
                self.__game.dest_entity[1] = trans_action[4]
            case _:
                self.__game.dest_entity[1] = trans_action[4]

    ## @brief Advances the game using the selected action.
    # @param action Selected action to take
    # @return None
    def __step_game(self, action):
        state = self.get_state()
        self.__format_action(action)
        reward = 0
        if (self.__game.src_entity == ['stock_hidden', -1]
                and self.__game.dest_entity == ['none', -1]):
            self.__game.increment_stock()
            reward = -1
        elif self.__game.move_cards():
            reward = self.__game.get_move_score()
        else:
            reward = -5
        self.__game.run_game(False)
        next_state = self.get_state()
        dones = self.__game.win
        return state, action, reward, next_state, dones

    ## @brief Performs the Q learning algorithm.
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
        for a in range(len(self.__policy_nets)):
            indices = actions[:, a].unsqueeze(1)
            current_q = self.__policy_nets[a](states).gather(1, indices)
            next_q = self.__target_nets[a](next_states).max(1)[0].detach(
            ).unsqueeze(1)
            target_q = rewards + (self.__params.gamma * next_q * (1 - dones))
            loss = self.__loss(current_q, target_q)
            self.__optimizers[a].zero_grad()
            loss.backward()
            self.__optimizers[a].step()

    ## @brief Trains the neural net using reinforcement learning.
    # @param episodes Number of episodes to train neural net for
    # @param update_freq Frequency that the lagging neural net is updated
    # @param max_moves Max allowable moves before the episode is ended
    # @return None
    def train_dqn(self, episodes, update_freq, max_moves):
        for episode in range(episodes):
            self.__game.reset_game()
            state = self.get_state()
            total_reward = 0
            for move in range(max_moves):
                action, type = self.__get_action(state,
                                                self.__params.epsilon)
                step_result = self.__step_game(action)
                if step_result[2] >= -1:
                    print(type, step_result[2])
                self.__memory.append(step_result)
                state = step_result[3]
                total_reward += step_result[2]
                self.__q_learn()
                if step_result[4]:
                    break
            if self.__params.epsilon > self.__params.epsilon_min:
                self.__params.epsilon *= self.__params.epsilon_decay

            if episode % update_freq == 0:
                for a in range(len(self.__policy_nets)):
                    self.__target_nets[a].load_state_dict(
                        self.__policy_nets[a].state_dict())
            print(
                f"Episode {episode}, Total Reward: {total_reward}, Epsilon: "
                f"{self.__params.epsilon:.3f}")