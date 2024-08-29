#!/usr/bin/env python3

import argparse
import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import os
import re
from collections import Counter
import random


class App:

    def __init__(self, pic_path, pics):
        self.pic_path = pic_path
        self.pics = pics

        root = tk.Tk()
        root.title("Pairwise Cross-Score")

        root.grid_rowconfigure(0, weight=2)
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        #TODO above every image label should be meta info
        labelL = tk.Label(root, text="<empty>", bg="lightblue")
        labelL.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        labelL.bind("<Configure>", lambda event: self.set_and_resize_image(labelL, event))

        labelR = tk.Label(root, text="<empty>", bg="lightblue")
        labelR.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        labelR.bind("<Configure>", lambda event: self.set_and_resize_image(labelR, event))

        frame = tk.Frame(root, bg="lightyellow")
        frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        #TODO make this really compact and minimal sized, so the image boxes dont resize during normal operation!
        label3 = tk.Label(frame, text="ABC", bg="cornsilk")
        label3.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        #TODO make the buttons for manual comparison

        root.bind("<s>", lambda event: self.compair_skip())
        root.bind("<w>", lambda event: self.compair_both())
        root.bind("<a>", lambda event: self.compair_left())
        root.bind("<d>", lambda event: self.compair_right())

        self.root = root
        labelL._image_ref_origin = None
        labelL._image_ref_tk = None
        labelR._image_ref_origin = None
        labelR._image_ref_tk = None
        self.imgLabelL = labelL
        self.imgLabelR = labelR
        self.idxL = None
        self.idxR = None

        self.rsc = 0 #REMOVE

    def set_and_resize_image(self, label, event):
        #REMOVE
        print(f"=== {self.rsc}")
        self.rsc += 1

        if hasattr(label, "_skip_resize") and label._skip_resize:
            label._skip_resize = False
            print("resize skipped")
            return

        if event:
            label_width = event.width
            label_height = event.height
            print("event resize")
            # if label_width == label.winfo_width() and label_height == label.winfo_height():
                # print("resize no change skip")
                # return
        else:
            label_width = label.winfo_width()
            label_height = label.winfo_height()

        print(f"now size: {label_width}x{label_height}") #REMOVE

        if label._image_ref_origin == None:
            print("resize no origin skip")
            return
        
        image = label._image_ref_origin.copy()

        scale_width = label_width / image.width
        scale_height = label_height / image.height
        scale = min(scale_width, scale_height)

        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        image = image.resize((new_width, new_height), Image.LANCZOS)

        tk_image = ImageTk.PhotoImage(image)
        label._image_ref_tk = tk_image
        label.config(image=tk_image, width=label_width, height=label_height)
        label._skip_resize = True
        print("resize skipper primed!")

    def new_compair(self):
        avoidL = -1
        avoidR = -1
        if self.idxL and self.idxR:
            avoidL = self.idxL[0]
            avoidR = self.idxR[0]
        self.idxL = random.choice(self.pics)
        self.idxR = random.choice(self.pics)
        while self.idxL[0] == self.idxR[0] or sorted([avoidL, avoidR]) == sorted([self.idxL[0], self.idxR[0]]):
            self.idxR = random.choice(self.pics)
        print(f"new compair: {self.idxL[0]} . {self.idxR[0]}")
        self.imgLabelL._image_ref_origin = Image.open(f"{self.pic_path}/{self.idxL[1]}")
        self.imgLabelR._image_ref_origin = Image.open(f"{self.pic_path}/{self.idxR[1]}")
        print("new compair requests resizings")
        self.set_and_resize_image(self.imgLabelL, None)
        self.set_and_resize_image(self.imgLabelR, None)

    def compair_skip(self):
        self.new_compair()

    def compair_left(self):
        print(f"{self.idxL[0]}>{self.idxR[0]}")
        self.new_compair()

    def compair_right(self):
        print(f"{self.idxL[0]}<{self.idxR[0]}")
        self.new_compair()

    def compair_both(self):
        print(f"{self.idxL[0]}={self.idxR[0]}")
        self.new_compair()

    def output_compair_result(self):
        pass #TODO needs more complicated compare pattern


def get_number_files_list(target_dir):
    # match files named with a number, ignoring extension
    pattern = re.compile(r"^(\d+)")

    # scan directory and extract numbers from file names
    numbers_and_filenames = []
    for filename in os.listdir(target_dir):
        match = pattern.match(filename)
        if match:
            numbers_and_filenames.append((int(match.group(1)), filename))

    # sort numbers
    sorted_numbers_and_filenames = sorted(numbers_and_filenames, key=lambda x: x[0])

    # extract the sorted numbers to find duplicates and discontinuities
    sorted_numbers = [num for num, _ in sorted_numbers_and_filenames]

    # find duplicates
    duplicates = [item for item, count in Counter(sorted_numbers).items() if count > 1]
    if duplicates:
        print(f"WARN: duplicates: {duplicates}")

    # find missing numbers
    discontinuities = [x for x in range(min(sorted_numbers), max(sorted_numbers)) if x not in sorted_numbers]
    if discontinuities:
        print(f"WARN: missing numbers: {discontinuities}")
    
    return sorted_numbers_and_filenames


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pictures", required=True, metavar="PATH", help="path to picture directory")
    args = parser.parse_args()
    
    #TODO load the config what is to be compared..

    pic_path = os.path.abspath(args.pictures)
    pics = get_number_files_list(pic_path)

    app = App(pic_path, pics)
    app.root.mainloop()


if __name__ == "__main__":
    main()
