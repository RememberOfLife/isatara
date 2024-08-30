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

    def __init__(self, pics_base, pics, record_path, comp_features):
        self.pics_base = pics_base
        self.pics = pics

        root = tk.Tk()
        root.title("Pairwise Cross-Score")

        compairFrame = tk.Frame(root)

        compairFrame.grid_rowconfigure(0, weight=2)
        # compairFrame.grid_rowconfigure(1, weight=1)
        compairFrame.grid_columnconfigure(0, weight=1)
        compairFrame.grid_columnconfigure(1, weight=1)

        imgFrameL = tk.Frame(compairFrame, bg="lightyellow")
        imgFrameL.grid(row=0, column=0, sticky="nsew")

        imgDisplayL = tk.Canvas(imgFrameL, bg="lightblue")
        imgDisplayL.pack(expand=True, fill="both", padx=(10, 5), pady=(10, 10))
        imgDisplayL.bind("<Configure>", lambda event: self.resize_and_set_image(imgDisplayL, event))

        imgLabelContainerL = tk.Frame(imgDisplayL)
        imgLabelContainerL.place(anchor="ne", relx=1, rely=0)
        imgLabelL = tk.Label(imgLabelContainerL, bg="black", fg="aliceblue", text="-", padx=3, pady=1)
        imgLabelL.pack(anchor="e")

        imgFrameR = tk.Frame(compairFrame, bg="lightyellow")
        imgFrameR.grid(row=0, column=1, sticky="nsew")

        imgDisplayR = tk.Canvas(imgFrameR, bg="lightblue")
        imgDisplayR.pack(expand=True, fill="both", padx=(5, 10), pady=(10, 10))
        imgDisplayR.bind("<Configure>", lambda event: self.resize_and_set_image(imgDisplayR, event))

        imgLabelContainerR = tk.Frame(imgDisplayR)
        imgLabelContainerR.place(anchor="nw", relx=0, rely=0)
        imgLabelR = tk.Label(imgLabelContainerR, bg="black", fg="aliceblue", text="-", padx=3, pady=1)
        imgLabelR.pack(anchor="w")

        # frame = tk.Frame(compairFrame, bg="lightyellow")
        # frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        #TODO make this really compact and minimal sized, so the image boxes dont resize during normal operation!
        # label3 = tk.Label(frame, text="ABC", bg="cornsilk")
        # label3.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        #TODO make the buttons for manual comparison

        compairFrame.bind("<s>", lambda event: self.compair_skip())
        compairFrame.bind("<w>", lambda event: self.compair_both())
        compairFrame.bind("<a>", lambda event: self.compair_left())
        compairFrame.bind("<d>", lambda event: self.compair_right())

        metaevalFrame = tk.Frame(root)
        tk.Label(metaevalFrame, text="meta-eval").pack()
        #TODO

        root.bind("<m>", lambda event: self.switch_mode())
        root.bind("<q>", lambda event: exit())

        self.root = root
        self.compairFrame = compairFrame
        self.metaevalFrame = metaevalFrame
        imgDisplayL._image_ref_origin = None
        imgDisplayL._image_ref_tk = None
        imgDisplayR._image_ref_origin = None
        imgDisplayR._image_ref_tk = None
        self.imgDisplayL = imgDisplayL
        self.imgDisplayR = imgDisplayR
        self.imgLabelL = imgLabelL
        self.imgLabelR = imgLabelR
        self.idxL = None
        self.idxR = None
        self.switch_mode("compair")

    def switch_mode(self, target_mode=None):
        if not target_mode:
            self.mode = {
                    "compair": "meta-eval",
                    "meta-eval": "compair",
                }[self.mode]
        else:
            self.mode = target_mode
        if self.mode == "compair":
            self.metaevalFrame.forget()
            self.compairFrame.pack(expand=True, fill="both")
            self.compairFrame.focus()
        elif self.mode == "meta-eval":
            self.compairFrame.forget()
            self.metaevalFrame.pack(expand=True, fill="both")
            self.metaevalFrame.focus()
        else:
            print("ERROR: unknown mode")
            exit()

    def resize_and_set_image(self, imgDisplay, event):
        # get elem width and heigh
        if event:
            elem_width = event.width
            elem_height = event.height
        else:
            elem_width = imgDisplay.winfo_width()
            elem_height = imgDisplay.winfo_height()
        # skip resizing if no image set
        if imgDisplay._image_ref_origin == None:
            return
        # copy original for modification
        image = imgDisplay._image_ref_origin.copy()
        # calc the scaling we need to make it fit
        scale_width = elem_width / image.width
        scale_height = elem_height / image.height
        scale = min(scale_width, scale_height)
        # calc new with from scaling and resize
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        image = image.resize((new_width, new_height), Image.LANCZOS)
        # set image to canvas
        tk_image = ImageTk.PhotoImage(image)
        imgDisplay._image_ref_tk = tk_image
        imgDisplay.delete("IMG")
        imgDisplay.create_image(elem_width / 2, elem_height / 2, image=tk_image, anchor="center", tags="IMG")

    def new_compair(self):
        # pick new idcs for compair
        avoidL = -1
        avoidR = -1
        if self.idxL and self.idxR:
            avoidL = self.idxL[0]
            avoidR = self.idxR[0]
        self.idxL = random.choice(self.pics)
        self.idxR = random.choice(self.pics)
        while self.idxL[0] == self.idxR[0] or sorted([avoidL, avoidR]) == sorted([self.idxL[0], self.idxR[0]]):
            self.idxR = random.choice(self.pics)
        # set label for img stats
        self.imgLabelL.config(text=f"{self.idxL[0]}")
        self.imgLabelR.config(text=f"{self.idxR[0]}")
        # load and set images
        self.imgDisplayL._image_ref_origin = Image.open(f"{self.pics_base}/{self.idxL[1]}")
        self.imgDisplayR._image_ref_origin = Image.open(f"{self.pics_base}/{self.idxR[1]}")
        self.resize_and_set_image(self.imgDisplayL, None)
        self.resize_and_set_image(self.imgDisplayR, None)

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
    parser.add_argument("--record", required=True, metavar="RECORD", help="record file for comparison log")
    parser.add_argument("--features", required=False, metavar="FEATURES", help="comma-separated list of comparison features")
    args = parser.parse_args()
    
    pics_base = os.path.abspath(args.pictures)
    pics = get_number_files_list(pics_base)

    record_path = os.path.abspath(args.record)

    comp_features = args.features.split(",") if args.features else []

    app = App(pics_base, pics, record_path, comp_features)
    app.root.mainloop()


if __name__ == "__main__":
    main()
