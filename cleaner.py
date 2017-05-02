import json
import os
import pickle
from evotools.serialization import RESULTS_DIR


def walk(results_dir, fun):
    rootDir = results_dir
    for dirName, subdirList, fileList in os.walk(rootDir):
        print('Found directory: %s' % dirName)
        for fname in fileList:
            fun(dirName, fname)

def json2pickle(dirName, fname):
    if fname.endswith('.json'):
        to_convert = os.path.join(dirName, fname)
        with open(to_convert, 'r') as fh:
            loaded = json.load(fh)

            to_save = os.path.join(dirName, fname[:-4] + 'pickle')
            with open(to_save, 'wb') as fw:
                pickle.dump(loaded, fw)
                print('\tsaved pickle: %s' % to_save)
        os.remove(to_convert)


def clear_budget(dirName, fname):
    splitted = fname.split('.')
    budget = int(splitted[0])
    print('\t %s' % fname)
    if budget > 4500:
        to_remove = os.path.join(dirName, fname)
        print('\tRemoving: %s' % to_remove)
        os.remove(to_remove)

if __name__ == '__main__':
    walk(RESULTS_DIR, json2pickle)

