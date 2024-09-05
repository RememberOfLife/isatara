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

    class StatisticsEntry:
        pref_win: int
        pref_loss: int
        share_win: int
        unfit_loss: int
        def __init__(self):
            self.pref_win = 0
            self.pref_loss = 0
            self.share_win = 0
            self.unfit_loss = 0

    class RecordEntry:
        feature: str
        idxL: int
        idxR: int
        result: str
        def __init__(self, feature, idxL, idxR, result):
            self.feature = str(feature)
            self.idxL = int(idxL)
            self.idxR = int(idxR)
            self.result = str(result)

    def __init__(self, pics, savepath, compair_mode):
        self.pic_ids = sorted([pic[0] for pic in pics])
        self.savepath = savepath
        self.compair_mode = compair_mode
        self.entries = []
        self.saved_idx = 0
        self.statistics = {}
        self.possible_combinations = {}
        for i, id1 in enumerate(self.pic_ids):
            for j, id2 in enumerate(self.pic_ids[i+1:]):
                self.possible_combinations[(id1, id2)] = set()
        self.load()

    def load(self):
        if os.path.exists(self.savepath):
            with open(self.savepath) as file:
                for line in file:
                    feature, idxL, idxR, result = line.strip().split(",")
                    self.entries += [self.RecordEntry(feature, idxL, idxR, result)]
            self.saved_idx = len(self.entries)
            for entry in self.entries:
                self.statistics_add_entry(entry)
                cpair = tuple(sorted((entry.idxL, entry.idxR)))
                if entry.feature not in self.possible_combinations[cpair]:
                    self.possible_combinations[cpair].add(entry.feature)
                else:
                    #TODO feature registered twice for the same compair
                    pass
                #TODO if we had the whole feature list up front, remove entries we're done with, here
                # if cpair in self.possible_combinations:
                #     del self.possible_combinations[cpair]

    def save(self):
        with open(self.savepath, "a") as file:
            for entry in self.entries[self.saved_idx:]:
                file.write(f"{entry.feature},{entry.idxL},{entry.idxR},{entry.result}\n")
        self.saved_idx = len(self.entries)

    def get_new_compair(self, features):
        features_sl = features
        features = set(features)
        available_combinations = dict([(cpair, features.difference(avfeatures)) for cpair, avfeatures in self.possible_combinations.items() if not features.issubset(avfeatures)])
        if len(available_combinations) == 0:
            return (None, None, [])
        #TODO for this we need to get elements from the toplist which are not already paired, this requires some more logic..
        if self.compair_mode == "smart":
            pass #TODO one favored and one uncertain
        elif self.compair_mode == "refine":
            pass #TODO top from toplist by favor
        elif self.compair_mode == "explore":
            pass #TODO top from toplist by uncertainty
        else:
            cpair = random.choice(list(available_combinations.keys()))
        return (*cpair, sorted(list(available_combinations[cpair]), key=lambda x: features_sl.index(x)))

    def add_compair_result(self, compair, feature, result):
        resultTypes = {
            "none": "x",
            "both": "=",
            "left": ">",
            "right": "<",
        }
        new_entry = self.RecordEntry(feature, *compair, resultTypes[result])
        self.entries += [new_entry]
        self.statistics_add_entry(new_entry)
        cpair = tuple(sorted((new_entry.idxL, new_entry.idxR)))
        self.possible_combinations[cpair].add(feature)

    def statistics_add_entry(self, recordentry):
        if recordentry.feature not in self.statistics:
            self.statistics[recordentry.feature] = {}
        for idx, dir in [(recordentry.idxL, ">"), (recordentry.idxR, "<")]:
            if idx not in self.statistics[recordentry.feature]:
                self.statistics[recordentry.feature][idx] = self.StatisticsEntry()
            if recordentry.result == "=":
                self.statistics[recordentry.feature][idx].share_win += 1
            elif recordentry.result == "x":
                self.statistics[recordentry.feature][idx].unfit_loss += 1
            elif recordentry.result == dir:
                self.statistics[recordentry.feature][idx].pref_win += 1
            else:
                self.statistics[recordentry.feature][idx].pref_loss += 1

    #TODO maybe weight for features
    def calculate_feature_toplist(self, features, sortby="favor"):
        if not type(features) is list:
            features = [features]
        #TODO do pagerank..
        toplist = []
        for feature in features:
            if feature not in self.statistics:
                return toplist #TODO can somehow do it with just partial statistics?
        for idx in self.pic_ids:
            favor_acc = 0
            certainty_acc = 0
            for feature in features:
                if idx in self.statistics[feature]:
                    sentry = self.statistics[feature][idx]
                else:
                    sentry = self.StatisticsEntry()
                wins = sentry.pref_win + sentry.share_win
                losses = sentry.pref_loss + sentry.unfit_loss
                totals = wins + losses
                local_certainty = totals / (len(self.pic_ids) - 1)
                probable_error = 1 - (local_certainty) #TODO could set to just one to be true review
                wins += probable_error
                losses += probable_error
                totals = wins + losses
                favor_acc += (wins / totals) * (1 / len(features))
                certainty_acc += local_certainty * (1 / len(features))
            toplist += [(idx, favor_acc, certainty_acc)]
        if sortby == "favor":
            toplist.sort(key=lambda x: x[1])
            toplist = reversed(toplist)
        elif sortby == "confidence":
            toplist.sort(key=lambda x: x[2])
            toplist = reversed(toplist)
        else:
            print("WARN: unknown sorting style")
        return toplist


class App:

    def __init__(self, pics_base, pics, record_path, comp_features, compair_mode):
        self.pics_base = pics_base
        self.pics = dict(pics)
        self.record = Record(pics, record_path, compair_mode)

        root = tk.Tk()
        if len(comp_features) == 0:
            root.title(f"Pairwise Scoring: <general>")
            comp_features = ["*"]
        else:
            root.title(f"Pairwise Scoring: {", ".join(comp_features)}")

        self.features = comp_features
        self.current_features = []
        
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
        root.bind("<q>", lambda event: self.quit())

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

    def quit(self):
        #TODO move this into proper panel
        for feature in self.record.statistics:
            print(f"feature toplist: {feature}")
            for tlentry in self.record.calculate_feature_toplist(feature):
                print(f"\t[{tlentry[0]}] ({tlentry[1]*100 :.2f}% ~ {tlentry[2]*100 :.2f}%)")
        print(f"general toplist:")
        for tlentry in self.record.calculate_feature_toplist(list(self.record.statistics.keys())):
            print(f"\t[{tlentry[0]}] ({tlentry[1]*100 :.2f}% ~ {tlentry[2]*100 :.2f}%)")
        exit()

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
        # drop ref and img
        imgDisplay._image_ref_tk = None
        imgDisplay.delete("IMG")
        # resizing only if image set
        if imgDisplay._image_ref_origin:
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
            imgDisplay.create_image(elem_width / 2, elem_height / 2, image=tk_image, anchor="center", tags="IMG")
        self.update_compair_features()

    def update_compair_features(self):
        for highlightFrame in [self.imgFeatureHighlightContainerL, self.imgFeatureHighlightContainerR]:
            for i, highlight in enumerate(highlightFrame.highlights):
                if i < len(self.current_features):
                    highlight.pack(anchor="n", expand=True, fill="both")
                else:
                    highlight.forget()
                if i == self.featureIdx and self.overlay:
                    highlight.config(bg="blueviolet")
                else:
                    highlight.config(bg="lightyellow")

        for imgDisplay, whichDisplay in [(self.imgDisplayL, "left"), (self.imgDisplayR, "right")]:
            imgDisplay.delete("FEATURE")
            imgDisplay._image_ref_tk_features = []
            if not self.overlay or len(self.features) < 2 or len(self.current_features) == 0:
                continue
            elem_width = imgDisplay.winfo_width()
            elem_height = imgDisplay.winfo_height()
            if elem_width < 10 or elem_height < 10:
                continue
            perFeatureHeight = elem_height // len(self.current_features)
            for i in range(len(self.current_features)):
                if i > self.featureIdx:
                    continue
                decided = i < self.featureIdx and self.compairResult[self.current_features[i]] in ["both", whichDisplay]
                if not decided and i < self.featureIdx:
                    continue
                featureImg = Image.new("RGBA", (elem_width, perFeatureHeight + (1 if i == len(self.current_features) - 1 else 0)), (0, 0, 0, 50) if not decided else (0, 0, 0, 0))
                featureDraw = ImageDraw.Draw(featureImg)
                featureFontSize = perFeatureHeight * 0.8
                featureFont = ImageFont.load_default(featureFontSize)
                featureStr = f"{self.current_features[i]}"
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
        self.idxL, self.idxR, self.current_features = self.record.get_new_compair(self.features)
        if self.idxL and self.idxR:
            # set label for img stats
            self.imgIdxLabelL.config(text=f"{self.idxL}")
            self.imgIdxLabelR.config(text=f"{self.idxR}")
            # load and set images
            self.imgDisplayL._image_ref_origin = Image.open(f"{self.pics_base}/{self.pics[self.idxL]}")
            self.imgDisplayR._image_ref_origin = Image.open(f"{self.pics_base}/{self.pics[self.idxR]}")
        else:
            # reset label
            self.imgIdxLabelL.config(text="-")
            self.imgIdxLabelR.config(text="-")
            # drop images1
            self.imgDisplayL._image_ref_origin = None
            self.imgDisplayR._image_ref_origin = None
        # force redraw
        self.resize_and_set_image(self.imgDisplayL, None)
        self.resize_and_set_image(self.imgDisplayR, None)

    def next_feature_or_compair(self, skip=False):
        self.featureIdx += 1
        if self.featureIdx >= len(self.current_features) or skip:
            self.compairResult = {}
            self.featureIdx = 0
            self.new_compair()
            self.record.save()
        else:
            self.update_compair_features()

    def compair_skip(self):
        self.next_feature_or_compair(skip=True)

    def compair_none(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.current_features[self.featureIdx]] = "none"
            self.record.add_compair_result((self.idxL, self.idxR), self.current_features[self.featureIdx], "none")
            self.next_feature_or_compair()

    def compair_left(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.current_features[self.featureIdx]] = "left"
            self.record.add_compair_result((self.idxL, self.idxR), self.current_features[self.featureIdx], "left")
            self.next_feature_or_compair()

    def compair_right(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.current_features[self.featureIdx]] = "right"
            self.record.add_compair_result((self.idxL, self.idxR), self.current_features[self.featureIdx], "right")
            self.next_feature_or_compair()

    def compair_both(self):
        if self.idxL and self.idxR and self.overlay:
            self.compairResult[self.current_features[self.featureIdx]] = "both"
            self.record.add_compair_result((self.idxL, self.idxR), self.current_features[self.featureIdx], "both")
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
    parser.add_argument("--compair-mode", required=False, choices=["random", "refine", "explore", "smart"], default="random", metavar="COMPAIR_MODE", help="strategy for offering compairs, can be one of: random, refine, explore, smart")
    args = parser.parse_args()
    
    pics_base = os.path.abspath(args.pictures)
    pics = get_number_files_list(pics_base)

    record_path = os.path.abspath(args.record)

    comp_features = args.features.split(",") if args.features else []
    if not all(bool(re.match(r"^[a-zA-Z0-9]+$", feature)) or feature == "*" for feature in comp_features):
        print("ERROR: non alpha-numeric features are not supported")
        exit()

    app = App(pics_base, pics, record_path, comp_features, args.compair_mode)
    app.root.mainloop()


if __name__ == "__main__":
    main()
