import netrunner
import numpy as np

input_layer = netrunner.NetLayer(2, 'input')
inner_layer_1 = netrunner.NetLayer(8, 'relu')
inner_layer_2 = netrunner.NetLayer(8, 'relu')
inner_layer_3 = netrunner.NetLayer(8, 'relu')
outer_layer = netrunner.NetLayer(4, 'relu')

net_layers = [input_layer, inner_layer_1, inner_layer_2,
              outer_layer]

net = netrunner.NetRunner(net_layers)
net.init_net()
net.init_runner(.1, .9)

input_1 = np.array([[1], [28]]) / 52
input_2 = np.array([[14], [28]]) / 52
input_3 = np.array([[28], [3]]) / 52
input_4 = np.array([[28], [16]]) / 52
input_5 = np.array([[2], [29]]) / 52
input_6 = np.array([[15], [29]]) / 52
input_7 = np.array([[29], [4]]) / 52
input_8 = np.array([[29], [17]]) / 52

output_1 = np.array([[4], [1], [4], [28]]) / 52
output_2 = np.array([[4], [14], [4], [28]]) / 52
output_3 = np.array([[4], [28], [4], [3]]) / 52
output_4 = np.array([[4], [28], [4], [16]]) / 52
output_5 = np.array([[4], [2], [4], [29]]) / 52
output_6 = np.array([[4], [15], [4], [29]]) / 52
output_7 = np.array([[4], [29], [4], [4]]) / 52
output_8 = np.array([[4], [29], [4], [17]]) / 52

training_set = [[input_1, output_1], [input_2, output_2],
                [input_3, output_3], [input_4, output_4],
                [input_5, output_5], [input_6, output_6],
                [input_7, output_7], [input_8, output_8]]

cost = 1
epoch = 0
while cost > .00005:
    net.init_mini_batch(training_set, 8, False)
    cost, epoch = net.step_epoch(training_set)
print(cost, epoch)
print()

print(52 * net.forward_pass(input_1))
print()
print(52 * net.forward_pass(input_2))
print()
print(52 * net.forward_pass(input_3))
print()
print(52 * net.forward_pass(input_4))
print()
print(52 * net.forward_pass(input_5))
print()
print(52 * net.forward_pass(input_6))
print()
print(52 * net.forward_pass(input_7))
print()
print(52 * net.forward_pass(input_8))