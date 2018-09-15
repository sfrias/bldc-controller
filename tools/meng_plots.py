import numpy as np
import matplotlib.pyplot as plt
import csv

DATA_PATH = "dino_0"
DATA_PATH = "dino_raw"
DATA_PATH = "dino_raw1"
DATA_PATH = "dino_raw3"
DATA_PATH = "dino_raw_higher_load1"
DATA_PATH = "dino_raw_higher_load"
data1 = "t0_1.0"
data2 = "t1_1.0"
data3 = "t2_1.0"
data4 = "t3_1.0"
data5 = "t4_1.0"


data_list = [data1, data2, data3, data4, data5]

#########################################
l  = 0.008
dm = 0.008
pi = np.pi
mu = 0.20
g = 9.81

alpha = 28 * pi / 180
angle_grasp = 2 * pi / 180
r1_finger = 18.125
r2_finger = 60.0

def calc_F(tau):
    par = (l + pi * mu * dm) / (pi * dm - mu *  l)
    return tau * 2 / ( dm * par )

def calc_F_acme(tau):
    par = (l + pi * mu * dm / np.cos(alpha)) / (pi * dm - mu *  l / np.cos(alpha))
    return tau * 2 / ( dm * par )

def cmd_to_exp(cmd):
    f = calc_F_acme(cmd)
    return r1_finger / r2_finger * f * np.cos(angle_grasp)

####################################

def load_from_csv(path):
    raw = np.genfromtxt(str(path) + ".csv", delimiter=',',dtype=str)
    labels = raw[:1]
    data = raw[1:].astype(np.float)
    return labels, data

def plot_d(data, ti):
    fig, ax1 = plt.subplots()
    print(max(data[:,2]))
    print(max(data[:,3]))
    expected_force = cmd_to_exp(data[:,1])
    ax1.plot(data[:,0], expected_force, label="expected")
    ax1.plot(data[:,0], g*data[:,2], label="mes1")
    ax1.plot(data[:,0], g*data[:,3], label="mes2")
    ax1.legend()

    ax2 = ax1.twinx()

    eff = []
    for a, ex in zip(g*data[:,2], expected_force):
        if ex == 0:
            eff.append(0)
        else:
            eff.append(a / ex)

    ax2.plot(data[:,0], eff, label="efficency", color='r')
    ax2.set_ylim([0.0, 1.0])
    plt.title("pinch force")
    plt.xlabel('time')
    plt.ylabel('')
    # ax2.legend()
    fig.savefig("plots/time_" + ti + ".eps", format='eps', dpi=1000)

def plot_hist(data, ti):
    fig = plt.figure()
    plt.plot(data[:,1], data[:,2], "*")
    plt.title("pinch force")
    plt.xlabel('time')
    plt.ylabel('')
    fig.savefig("plots/hist_" + ti +".eps", format='eps', dpi=1000)


for d in data_list:
    _, loaded_data= load_from_csv(d)
    plot_d(loaded_data, d)
    plot_hist(loaded_data, d)
