from fastai import *
from fastai.vision import *

def analyze(image, learn):
    img = open_image(image)
    prediction = learn.predict(img)[0]
    return prediction
from fastai import *
from fastai.vision import *
import sys
import json
if __name__ == "__main__":
    learn = load_learner('./')
    pred = analyze(sys.argv[1], learn)
    print(json.dumps({'result': str(pred)}))
