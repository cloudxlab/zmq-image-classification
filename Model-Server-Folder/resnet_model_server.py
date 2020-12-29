from io import BytesIO
from PIL import Image
import threading
import zmq
from base64 import b64decode
import numpy as np

import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import ResNet50 as myModel
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.python.keras.backend import set_session

sess = tf.Session()
set_session(sess)
model = myModel(weights="imagenet")
graph = tf.get_default_graph()

class Server(threading.Thread):
    def __init__(self):
        self._stop = threading.Event()
        threading.Thread.__init__(self)

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        context = zmq.Context()
        frontend = context.socket(zmq.ROUTER)
        frontend.bind('tcp://*:5576')

        backend = context.socket(zmq.DEALER)
        backend.bind('inproc://backend_endpoint')

        poll = zmq.Poller()
        poll.register(frontend, zmq.POLLIN)
        poll.register(backend,  zmq.POLLIN)

        while not self.stopped():
            sockets = dict(poll.poll())
            if frontend in sockets:
                if sockets[frontend] == zmq.POLLIN:
                    _id = frontend.recv()
                    json_msg = frontend.recv_json()

                    handler = RequestHandler(context, _id, json_msg)
                    handler.start()

            if backend in sockets:
                if sockets[backend] == zmq.POLLIN:
                    _id = backend.recv()
                    msg = backend.recv()
                    frontend.send(_id, zmq.SNDMORE)
                    frontend.send(msg)

        frontend.close()
        backend.close()
        context.term()


class RequestHandler(threading.Thread):
    def __init__(self, context, id, msg):

        """
        RequestHandler
        :param context: ZeroMQ context
        :param id: Requires the identity frame to include in the reply so that it will be properly routed
        :param msg: Message payload for the worker to process
        """
        threading.Thread.__init__(self)
        print("--------------------Entered requesthandler--------------------")
        self.context = context
        self.msg = msg
        self._id = id


    def process(self, obj):

        imgstr = obj['payload']

        img = Image.open(BytesIO(b64decode(imgstr)))

        if img.mode != "RGB":
            img = img.convert("RGB")
        # resize the input image and preprocess it
        img = img.resize((224,224))
        img = image.img_to_array(img)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)

        with graph.as_default():
            set_session(sess)
            predictions = model.predict(img)

        predictions = decode_predictions(predictions, top=3)[0]
        print("Predictions from class_model_server.py:",predictions)

        pred_strings = []
        for _,pred_class,pred_prob in predictions:
            pred_strings.append(str(pred_class).strip()+" : "+str(round(pred_prob,5)).strip())
        preds = ", ".join(pred_strings)

        return_dict = {}
        return_dict["preds"] = preds
        return return_dict

    def run(self):
        # Worker will process the task and then send the reply back to the DEALER backend socket via inproc
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://backend_endpoint')
        print('Request handler started to process %s\n' % self.msg)

        # Simulate a long-running operation
        output = self.process(self.msg)

        worker.send(self._id, zmq.SNDMORE)
        worker.send_json(output)
        del self.msg

        print('Request handler quitting.\n')
        worker.close()

def main():
    # Start the server that will handle incoming requests
    server = Server()
    server.start()

if __name__ == '__main__':
    main()
