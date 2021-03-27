import os
from tqdm import tqdm
import cv2
import csv
import ast
import numpy as np

from keras import layers
from keras import models
from keras import optimizers

from tkinter import *
from PIL import ImageTk, Image
from tkinter import filedialog
from tkinter.ttk import *


train_path = './trainingset'
x_genuine_path = './genuine'
x_forgery_path = './forgery'
x_random_path = './random'
x_random_csv_path = './randomcsv'
x_test_path = './test'
save_path = './modelsave'


def segmentImage(image):
    hHist = np.zeros(shape=image.shape[0], dtype=int)
    vHist = np.zeros(shape=image.shape[1], dtype=int)

    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            if (image[i][j] == 0):
                hHist[i] += 1
                vHist[j] += 1

    locLeft = 0
    locRight = image.shape[0]
    locTop = 0
    locBottom = image.shape[1]

    count = 0
    for i in range(hHist.shape[0]):
        if (count <= 0):
            count = 0
            if (hHist[i] != 0):
                locTop = i
                count += 1
        else:
            if (hHist[i] != 0):
                count += 1
            else:
                count -= hHist.shape[0] / 100

            if (count > hHist.shape[0] / 30):
                break

    count = 0
    for i in reversed(range(hHist.shape[0])):
        if (count <= 0):
            count = 0
            if (hHist[i] != 0):
                locBottom = i
                count += 1
        else:
            if (hHist[i] != 0):
                count += 1
            else:
                count -= hHist.shape[0] / 100

            if (count > hHist.shape[0] / 30):
                break

    count = 0
    for i in range(vHist.shape[0]):
        if (count <= 0):
            count = 0
            if (vHist[i] != 0):
                locLeft = i
                count += 1
        else:
            if (vHist[i] != 0):
                count += 1
            else:
                count -= vHist.shape[0] / 100

            if (count > vHist.shape[0] / 30):
                break

    count = 0
    for i in reversed(range(vHist.shape[0])):
        if (count <= 0):
            count = 0
            if (vHist[i] != 0):
                locRight = i
                count += 1
        else:
            if (vHist[i] != 0):
                count += 1
            else:
                count -= vHist.shape[0] / 100

            if (count > vHist.shape[0] / 30):
                break

    return locLeft, locRight, locTop, locBottom


def preProcessImage(train_path, final_img_size=(300, 300), power_law=False, segment=True, log_transform=False):
    train_batch = os.listdir(train_path)
    x_train = []
    train_data = [x for x in train_batch if
                  x.endswith('png') or x.endswith('PNG') or x.endswith('jpg') or x.endswith('JPG')]

    for sample in tqdm(train_data):
        img_path = os.path.join(train_path, sample)
        # importing images from drive
        # x = image.load_img(img_path)
        # img = image.img_to_array(x)
        img = cv2.imread(img_path)

        # Perfom Median blur on image
        mbvalue = int(np.max(img.shape) / 200)
        mbvalue = mbvalue if mbvalue % 2 == 1 else mbvalue + 1
        img = cv2.medianBlur(img, mbvalue)

        # changing RGB to grayscale
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # resize image to 600xH
        img = cv2.resize(img, (600, int(600 * float(img.shape[0]) / img.shape[1])))

        # if power_law enabled
        if (power_law):
            img = img ** 0.9
            img[img > 255] = 255
            img[img < 0] = 0
            img = img.astype('uint8')

        # denoising the grayscale image
        img = cv2.fastNlMeansDenoising(img, None, 10, 21)

        if (log_transform):
            img = (np.log(img + 1) / (np.log(10 + np.max(img)))) * 255
            img = img.astype('uint8')

        # Threshold binary image
        avg = np.average(img)
        _, image = cv2.threshold(img, int(avg) - 30, 255, cv2.THRESH_BINARY)

        # segment or edge detection the signature section only
        if (segment):
            seg = segmentImage(image)
            image = image[seg[2]:seg[3], seg[0]:seg[1]]

        # padding to make image into square
        lp, rp, tp, bp = (0, 0, 0, 0)
        if (image.shape[0] > image.shape[1]):
            lp = int((image.shape[0] - image.shape[1]) / 2)
            rp = lp
        elif (image.shape[1] > image.shape[0]):
            tp = int((image.shape[1] - image.shape[0]) / 2)
            bp = tp
        image_padded = cv2.copyMakeBorder(image, tp, bp, lp, rp, cv2.BORDER_CONSTANT, value=255)

        # resizing the image
        img = cv2.resize(image_padded, final_img_size)

        # producing image negative
        img = 255 - img

        # skeletonizing image
        # img = thin(img/255)

        img = img.astype('bool')

        # appending it in list
        x_train.append(img)

    # converting it into np-array
    x_train = np.array(x_train)
    return x_train


def convertToInt(arr):
    t1 = []
    for x in arr:
        t2 = []
        for y in x:
            t3 = []
            for z in y:
                if (z == True):
                    t3.append(1)
                else:
                    t3.append(0)
            t2.append(np.array(t3))
        t1.append(np.array(t2))
    return np.array(t1).astype('uint8')


def convertToBool(arr):
    t1 = []
    for x in arr:
        t2 = []
        for y in x:
            t3 = []
            for z in y:
                if (z == 1):
                    t3.append(True)
                else:
                    t3.append(False)
            t2.append(np.array(t3))
        t1.append(np.array(t2))
    return np.array(t1)


def csvWriter(fil_name, nparray):
    example = nparray.tolist()
    with open(fil_name + '.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(example)


def csvReader(fil_name):
    with open(fil_name + '.csv', 'r') as f:
        reader = csv.reader(f)
        examples = list(reader)
        examples = np.array(examples)

    t1 = []
    for x in examples:
        t2 = []
        for y in x:
            z = ast.literal_eval(y)
            t2.append(np.array(z))
        t1.append(np.array(t2))
    ex = np.array(t1)
    return ex


mod = models.Sequential()
# Two “Conv2D” or 2-dimensional convolutional layers, each with a pooling layer following it.
#2d for width and height of pixels form
# The first layer uses 64 nodes, while the second uses 32, and ‘kernel’ or filter size for both is 3 squared pixels.
mod.add(layers.Conv2D(16, (5, 5), activation='relu', input_shape=(300, 300, 1)))
# A “dense” layer that takes that vector and generates probabilities for 10 target labels,
# using a relu activation function.
mod.add(layers.MaxPooling2D((2, 2)))
# Max pooling is a pooling operation that selects the maximum element
# from the region of the feature map covered by the filter.
# Thus, the output after max-pooling layer would be a feature map
# containing the most prominent features of the previous feature map
mod.add(layers.Conv2D(32, (3, 3), activation='relu'))
mod.add(layers.MaxPooling2D((2, 2)))
# A “flatten” layer  turns the inputs into a vector
mod.add(layers.Flatten())
# Dropout is a technique where randomly selected neurons are ignored during training
mod.add(layers.Dropout(0.5))
mod.add(layers.Dense(256, activation='relu'))
mod.add(layers.Dropout(0.5))
mod.add(layers.Dense(128, activation='relu'))
mod.add(layers.Dense(1, activation='sigmoid'))
# The main reason why we use sigmoid function is because it exists between (0 to 1).
# Therefore, it is especially used for models where we have to predict the probability as an output.

mod.compile(loss='binary_crossentropy', optimizer=optimizers.Adam(lr=1e-3), metrics=['acc'])

if 'mysign_weights.h5' not in os.listdir(save_path):
    x_genuine = preProcessImage(x_genuine_path)
    x_random = csvReader(os.path.join(x_random_csv_path, 'random2'))
    # another training
    mod.fit(np.concatenate((x_genuine, x_random)).reshape(x_genuine.shape[0] + x_random.shape[0], 300, 300, 1),
            np.concatenate((np.full(x_genuine.shape[0], 1), np.full(x_random.shape[0], 0))), epochs=5, verbose=1,
            shuffle=True)

    evaluated = mod.evaluate(x_genuine.reshape(x_genuine.shape[0], 300, 300, 1), np.full((x_genuine.shape[0]), 1))
    print('Accuracy: ', evaluated[1] * 100, '%')

    mod.save_weights(os.path.join(save_path, 'mysign_weights.h5'))

else:
    mod.load_weights(os.path.join(save_path, 'mysign_weights.h5'))




def wrt(st, fname):
    file = open(fname, "w+")
    file.write(st)
    file.close()


def red(fname):
    file = open(fname, "r")
    f = file.read()
    file.close()
    return f


def open_img():
    try:
        x = openfilename()
        wrt(x, "upload");
        print(x);
        img = Image.open(x)
    except:
        x = 'error.png'
        print(x);
        img = Image.open(x)
    img = img.resize((325, 200), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img)
    panel = Label(root, image=img)
    panel.image = img
    panel.place(x=455, y=100)


def openfilename():
    filename = filedialog.askopenfilename(title='UPLOAD IMAGE')
    return filename


def callback():
    #cell = "\n IMAGE FILE NOT upload"
    try:

        #model = load_model('mysign_weights.h5')
        # model.summary()
        #test_image = image.load_img(red("upload"), target_size=(50, 50, 3))
       # test_image = image.img_to_array(test_image)
        #test_image = expand_dims(test_image, axis=0)

        x_test = preProcessImage(os.path.join(x_test_path))
        x_test = x_test.reshape(300, 300)
        predicted_acc = mod.predict(np.array([x_test.reshape(300, 300, 1), ]))
        #print("\n\nAccuracy of Sign in Test Folder: ", predicted_acc * 100, "%")
        #print("*** If percent > 90% signature is genuine else forged***")


       # result = model.predict(test_image)
       # cell = "real " if result[0][1] == 1 else "forged"
        cell = "Real sign with accuracy\n" if predicted_acc >= 0.9 else "Forged sign with accuracy\n"
        cell =cell + str(predicted_acc*100);
        output.set(cell);
       # output.set("\n " + cell + predicted_acc*100 + "%");
        #" sign  !\n" +
        print(cell)
        os.remove('modelsave\\mysign_weights.h5')
    except:
        output.set(cell);
        print("EXCEPTION")


root = Tk()
root.title("SIGN VERIFY")
output = StringVar();
root.attributes('-fullscreen', True)

background = PhotoImage(file="cover.png")
Label(root, image=background).place(x=0, y=0)
img = Image.open("input.png")
img = img.resize((325, 200), Image.ANTIALIAS)
img = ImageTk.PhotoImage(img)
panel = Label(root, image=img)
panel.image = img
panel.place(x=455, y=100)

upload = PhotoImage(file=r"upload.png")
Button(root, text="upload", image=upload,
       command=open_img).place(x=150, y=150)

Label(root, text="\n                    \n",
      width=25,
      font=("Bauhaus 93", 20)).place(x=432, y=335)
Label(root, text="", textvariable=output,
      font=("Bauhaus 93", 20)).place(x=432, y=335)

detect = PhotoImage(file=r"verify.png")
Button(root, text="detect", image=detect,
       command=callback).place(x=150, y=340)

close = PhotoImage(file=r"close.png")
Button(root, text="close", image=close,
       command=root.destroy).place(x=0, y=0)

root.mainloop()


