# License

This project uses KanjiVG data, which is © Ulrich Apel and released under the 
Creative Commons Attribution-ShareAlike 3.0 License.

You can find the full license here:  
http://creativecommons.org/licenses/by-sa/3.0/

Please respect the original license terms when using this data.

---

# KanjiVG to Lottie Converter

This Python project converts KanjiVG SVG files into Lottie JSON animations.g

## Features

- Parses KanjiVG SVG files to extract stroke path data.
- Converts SVG path commands into point data suitable for Lottie.
- Generates Lottie JSON animation files using customizable templates.
- Supports batch processing of all SVG files in a directory.
- Utilizes multithreading for faster generation.
- Automatically creates the output directory if it doesn’t exist.

## Installation & Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/MrAntoine77/kanjivg-to-lottie.git
   cd kanjivg-to-lottie
   ```
2. Make sure you have Python 3 installed.
3. Place your KanjiVG SVG files in the kanji/ directory.
4. Ensure the template files line.json and mask.json are present in the root directory.

## Usage

Run the main script to generate Lottie JSON files:
   ```bash
   python generate_lottie.py
   ```
This will process all .svg files in the kanji/ folder and output Lottie JSON files to the lottie/ folder.

## Complete Kanji Data

For the sake of keeping this repository lightweight, the full SVG files are not included.
This repository contains only 10 example SVG files.
You can download the complete set here:
https://github.com/KanjiVG/kanjivg


