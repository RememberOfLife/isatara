# isatara

Isatara is a visual pairwise comparison scoring tool. Its purpose is to score a large set of images, along user defined "feature" categories, by way of pairwise preferential decisions.

In practice that means:  
Isatara shows you two pictures from the designated source folder, and you have to decide if, the left, the right, both, or none of the two pictures perform favorably for the given feature category.

## usage

```
isatara.py --pictures=<path-to-your-pictures> --record=<path-to-the-log-file> [--features=<feature1,feature2,..>]
```

The directory with pictures should contain the pictures to score, enumerated with unpadded integers, starting at `1`. That is, e.g.: `1.png 2.jpg 3.png 4.png 5.webp ... 123.png`. Duplicate numbers and discontinuities cause a warning, the program may or may not work then.

The log file will be used to store the results of comparisons, if it already exists, its contents will be appended with any new comparisons, otherwise it gets created.

Features must be pure alphanumeric. If you do not specify any features, you will be comparing the built-in general comparison feature `*`. If you supply your own, we recommend full capital letters, because they display nicely in the visual overlay.

Shortcuts. Press:  
`<r>` to skip the current comparison, and load another set.  
`<a>` to mark the left image as favorable in the currently deciding feature.  
`<d>` to mark the right image as favorable..  
`<w>` to mark both images as equally favorable..  
`<s>` to mark both images as unqualified..  
`<space>` to toggle the overlay. (You will not be able to score while the overlay is disabled.)  
`<q>` to quit.  
