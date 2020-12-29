from tensorflow.keras.applications.resnet50 import ResNet50 as myModel
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions

from tensorflow.keras.preprocessing import image
import numpy as np

model = myModel(weights="imagenet")

def get_classes(file_path):


    img = image.load_img(file_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x= np.array([x])
    x = preprocess_input(x)

    preds = model.predict(x)
    predictions = decode_predictions(preds, top=3)[0]
    print(predictions)
    return predictions


if __name__ == "__main__":
    name = '/cxldata/projects/image-class/dog.png'
    get_classes(name)
