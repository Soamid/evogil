import pickle
with open("test.pickle", mode='rb') as f:
    o = pickle.load(f)
    print(o)


