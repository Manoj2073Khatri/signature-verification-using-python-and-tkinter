from tkinter import *
from PIL import ImageTk, Image
from tkinter import filedialog
from tkinter.ttk import *


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
    cell = "\n IMAGE FILE NOT UPLOADED..."
    try:
        model = load_model('mysign_weights.h5')
        # model.summary()
        test_image = image.load_img(red("upload"), target_size=(50, 50, 3))
        test_image = image.img_to_array(test_image)
        test_image = expand_dims(test_image, axis=0)
        result = model.predict(test_image)
        cell = "REAL " if result[0][1] == 1 else "FORGED"
        output.set("\n " + cell + " sign verified !\n");
        print(cell)
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

Label(root, text="\n                    OUTPUT\n",
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
