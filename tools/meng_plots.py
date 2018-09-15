import numpy as np
import matplotlib.pyplot as plt
import csv

DATA_PATH = "dino_0.csv"
DATA_PATH = "dino_raw.csv"
DATA_PATH = "dino_raw1.csv"
DATA_PATH = "dino_raw3.csv"
DATA_PATH = "dino_raw_higher_load1.csv"
def load_from_csv(path):
    raw = np.genfromtxt(str(path), delimiter=',',dtype=str)
    labels = raw[:1]
    data = raw[0:].astype(np.float)
    return labels, data

def plot_d():
    fig, ax1 = plt.subplots()
    _, data= load_from_csv(DATA_PATH)
    print(max(data[:,2]))
    print(max(data[:,3]))
    ax1.plot(data[:,0], data[:,1], label="input")
    ax2 = ax1.twinx()
    ax2.plot(data[:,0], data[:,2], label="mes1")
    ax2.plot(data[:,0], data[:,3], label="mes2")
    plt.title("pinch force")
    plt.xlabel('time')
    plt.ylabel('')
    plt.show()
    plot_hist(data)
    fig.savefig("gripper.eps", format='eps', dpi=1000)

def plot_hist(data):
    plt.plot(data[:,1], data[:,2], "*")
    plt.show()

plot_d()
