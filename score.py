#!/usr/bin/env python3

import argparse
import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import re
from collections import Counter
import random


def PILmeasureText(text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()
    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    return (text_width, text_height)


class Record:

    class RecordEntry:
        feature: str
        idxL: int
        idxR: int
        result: str
        def __init__(self, feature, idxL, idxR, result):
            self.feature = feature
            self.idxL = idxL
            self.idxR = idxR
            self.result = result

    def __init__(self, pics, savepath):
        self.pic_ids = [pic[0] for pic in pics]
        self.savepath = savepath
        self.entries = []
        self.saved_idx = 0
        self.load()

    def load(self):
        if os.path.exists(self.savepath):
            with open(self.savepath) as file:
                for line in file:
                    feature, idxL, idxR, result = line.split(",")
                    self.entries += [self.RecordEntry(feature, idxL, idxR, result)]
            self.saved_idx = len(self.entries)

    def save(self):
        with open(self.savepath, "a") as file:
            for entry in self.entries[self.saved_idx:]:
                file.write(f"{entry.feature},{entry.idxL},{entry.idxR},{entry.result}\n")
        self.saved_idx = len(self.entries)

    def get_new_compair(self, features):
        avoidPair = (-1, -1)
        if len(self.entries) > 0:
            avoidPair = sorted((self.entries[-1].idxL, self.entries[-1].idxR))
        newIdxL = random.choice(self.pic_ids)
        newIdxR = random.choice(self.pic_ids)
        while newIdxL == newIdxR or avoidPair == sorted([newIdxL, newIdxR]):
            newIdxR = random.choice(self.pic_ids)
        return (newIdxL, newIdxR)

    def add_compair_result(self, compair, feature, result):
        resultTypes = {
            "none": "x",
            "both": "=",
            "left": ">",
            "right": "<",
        }
        self.entries += [self.RecordEntry(feature, *compair, resultTypes[result])]


class App:

    def __init__(self, pics_base, pics, record_path, comp_features):
        self.pics_base = pics_base
        self.pics = dict(pics)
        self.record = Record(pics, record_path)

        root = tk.Tk()
        if len(comp_features) == 0:
            root.title(f"Pairwise Scoring: <general>")
            comp_features = ["*"]
        else:
            root.title(f"Pairwise Scoring: {", ".join(comp_features)}")

        self.features = comp_features
        
        compairFrame = tk.Frame(root)

        compairFrame.grid_rowconfigure(0, weight=2)
        compairFrame.grid_columnconfigure(0, weight=1)
        compairFrame.grid_columnconfigure(1, weight=1)

        imgFrameL = tk.Frame(compairFrame, bg="lightyellow")
        imgFrameL.grid(row=0, column=0, sticky="nsew")

        imgDisplayL = tk.Canvas(imgFrameL, bg="lightblue", highlightthickness=0)
        imgDisplayL.pack(expand=True, fill="both", padx=(10, 5), pady=(10, 10))
        imgDisplayL.bind("<Configure>", lambda event: self.resize_and_set_image(imgDisplayL, event))

        imgIdxLabelContainerL = tk.Frame(imgDisplayL)
        imgIdxLabelContainerL.place(anchor="ne", relx=1, rely=0)
        imgIdxLabelL = tk.Label(imgIdxLabelContainerL, bg="black", fg="aliceblue", text="-", padx=3, pady=1)
        imgIdxLabelL.pack(anchor="e")

        imgFeatureHighlightContainerL = tk.Frame(imgFrameL, bg="lightyellow", pady=10)
        imgFeatureHighlightContainerL.place(anchor="nw", relx=0, rely=0, relwidth=1, relheight=1)
        imgFeatureHighlightContainerL.lower()
        imgFeatureHighlightContainerL.highlights = []
        for i in range(len(comp_features)):
            imgFeatureHighlight = tk.Label(imgFeatureHighlightContainerL, bg="lightyellow", text="")
            imgFeatureHighlight.pack(anchor="n", expand=True, fill="both")
            imgFeatureHighlightContainerL.highlights += [imgFeatureHighlight]

        imgFrameR = tk.Frame(compairFrame, bg="lightyellow")
        imgFrameR.grid(row=0, column=1, sticky="nsew")

        imgDisplayR = tk.Canvas(imgFrameR, bg="lightblue", highlightthickness=0)
        imgDisplayR.pack(expand=True, fill="both", padx=(5, 10), pady=(10, 10))
        imgDisplayR.bind("<Configure>", lambda event: self.resize_and_set_image(imgDisplayR, event))

        imgIdxLabelContainerR = tk.Frame(imgDisplayR)
        imgIdxLabelContainerR.place(anchor="nw", relx=0, rely=0)
        imgIdxLabelR = tk.Label(imgIdxLabelContainerR, bg="black", fg="aliceblue", text="-", padx=3, pady=1)
        imgIdxLabelR.pack(anchor="w")

        imgFeatureHighlightContainerR = tk.Frame(imgFrameR, bg="lightyellow", pady=10)
        imgFeatureHighlightContainerR.place(anchor="nw", relx=0, rely=0, relwidth=1, relheight=1)
        imgFeatureHighlightContainerR.lower()
        imgFeatureHighlightContainerR.highlights = []
        for i in range(len(comp_features)):
            imgFeatureHighlight = tk.Label(imgFeatureHighlightContainerR, bg="lightyellow", text="")
            imgFeatureHighlight.pack(anchor="n", expand=True, fill="both")
            imgFeatureHighlightContainerR.highlights += [imgFeatureHighlight]

        compairFrame.bind("<r>", lambda event: self.compair_skip())
        compairFrame.bind("<s>", lambda event: self.compair_none())
        compairFrame.bind("<w>", lambda event: self.compair_both())
        compairFrame.bind("<a>", lambda event: self.compair_left())
        compairFrame.bind("<d>", lambda event: self.compair_right())
        if len(comp_features) > 1:
            compairFrame.bind("<space>", lambda event: self.toggle_overlay())

        metaevalFrame = tk.Frame(root)
        tk.Label(metaevalFrame, text="meta-eval").pack()
        #TODO

        root.bind("<m>", lambda event: self.switch_mode())
        root.bind("<Shift_L>", lambda event: self.record.save())
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
        self.imgIdxLabelL = imgIdxLabelL
        self.imgIdxLabelR = imgIdxLabelR
        self.imgFeatureHighlightContainerL = imgFeatureHighlightContainerL
        self.imgFeatureHighlightContainerR = imgFeatureHighlightContainerR
        self.idxL = None
        self.idxR = None
        self.featureIdx = 0
        self.compairResult = {}
        self.overlay = True
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

    def toggle_overlay(self):
        if self.idxL and self.idxR:
            self.overlay = not self.overlay
            self.update_compair_features()

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
        self.update_compair_features()

    def update_compair_features(self):
        for highlightFrame in [self.imgFeatureHighlightContainerL, self.imgFeatureHighlightContainerR]:
            if len(self.features) < 2:
                continue
            for i, highlight in enumerate(highlightFrame.highlights):
                if i == self.featureIdx and self.overlay:
                    highlight.config(bg="blueviolet")
                else:
                    highlight.config(bg="lightyellow")

        for imgDisplay, whichDisplay in [(self.imgDisplayL, "left"), (self.imgDisplayR, "right")]:
            imgDisplay.delete("FEATURE")
            imgDisplay._image_ref_tk_features = []
            if not self.overlay or len(self.features) < 2:
                continue
            elem_width = imgDisplay.winfo_width()
            elem_height = imgDisplay.winfo_height()
            perFeatureHeight = elem_height // len(self.features)
            for i in range(len(self.features)):
                if i > self.featureIdx:
                    continue
                decided = i < self.featureIdx and self.compairResult[self.features[i]] in ["both", whichDisplay]
                if not decided and i < self.featureIdx:
                    continue
                featureImg = Image.new("RGBA", (elem_width, perFeatureHeight + (1 if i == len(self.features) - 1 else 0)), (0, 0, 0, 50) if not decided else (0, 0, 0, 0))
                featureDraw = ImageDraw.Draw(featureImg)
                featureFontSize = perFeatureHeight * 0.8
                featureFont = ImageFont.load_default(featureFontSize)
                featureStr = f"{self.features[i]}"
                #TODO looks very good with all caps feature names, but we could also measure the str and center it manually (unreasonable effort though)
                text_width, text_height = PILmeasureText(featureStr, featureFont)
                horizontal_fill_ratio = 0.9
                if text_width > elem_width * horizontal_fill_ratio:
                    featureFontSize = featureFontSize * ((elem_width * horizontal_fill_ratio) / text_width)
                    featureFont = ImageFont.load_default(featureFontSize)
                featureDraw.text((elem_width/2, perFeatureHeight/2), featureStr, anchor="mm", fill=(255, 255, 255, 50), stroke_width=3, stroke_fill=(0, 0, 0, 100) if not decided else (0, 0, 0, 50), font=featureFont)
                featureImgTk = ImageTk.PhotoImage(featureImg)
                imgDisplay._image_ref_tk_features += [featureImgTk]
                imgDisplay.create_image(0, perFeatureHeight * i, image=featureImgTk, anchor="nw", tags="FEATURE")

    def new_compair(self):
        # pick new idcs for compair
        self.idxL, self.idxR = self.record.get_new_compair(self.features)
        # set label for img stats
        self.imgIdxLabelL.config(text=f"{self.idxL}")
        self.imgIdxLabelR.config(text=f"{self.idxR}")
        # load and set images
        self.imgDisplayL._image_ref_origin = Image.open(f"{self.pics_base}/{self.pics[self.idxL]}")
        self.imgDisplayR._image_ref_origin = Image.open(f"{self.pics_base}/{self.pics[self.idxR]}")
        self.resize_and_set_image(self.imgDisplayL, None)
        self.resize_and_set_image(self.imgDisplayR, None)

    def next_feature_or_compair(self, skip=False):
        self.featureIdx += 1
        if self.featureIdx >= len(self.features) or skip:
            self.compairResult = {}
            self.featureIdx = 0
            self.new_compair()
        else:
            self.update_compair_features()

    def compair_skip(self):
        self.next_feature_or_compair(skip=True)

    def compair_none(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.features[self.featureIdx]] = "none"
            self.record.add_compair_result((self.idxL, self.idxR), self.features[self.featureIdx], "none")
            self.next_feature_or_compair()

    def compair_left(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.features[self.featureIdx]] = "left"
            self.record.add_compair_result((self.idxL, self.idxR), self.features[self.featureIdx], "left")
            self.next_feature_or_compair()

    def compair_right(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.features[self.featureIdx]] = "right"
            self.record.add_compair_result((self.idxL, self.idxR), self.features[self.featureIdx], "right")
            self.next_feature_or_compair()

    def compair_both(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.features[self.featureIdx]] = "both"
            self.record.add_compair_result((self.idxL, self.idxR), self.features[self.featureIdx], "both")
            self.next_feature_or_compair()


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
    if not all(bool(re.match(r"^[a-zA-Z0-9]+$", feature)) for feature in comp_features):
        print("ERROR: non alpha-numeric features are not supported")
        exit()

    app = App(pics_base, pics, record_path, comp_features)
    app.root.mainloop()


if __name__ == "__main__":
    main()
