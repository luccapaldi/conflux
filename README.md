[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# tondu

A companion package to the tif file format for scientific analysis.

![Tif et Tondu](tif-et-tondu.jpg?raw=true "Tif et Tondu")

This is a package containing self-contained, modular functions for analysis of
DNA polymer physics. These functions are all a result of work in the Reisner
group at McGill University and are not intended to fully encompass all systems.
That being said, feel free to contribute or use this project in part or whole
for your own work. 

## Contributor guidelines

Try to follow PEP8 guidelines as much as possible (except that black line length
defaults are used; 88 chars). I also require the following
to merge changes:

* Run pipreqs to generate an updated requirements.txt
* Run black to autoformat your code following PEP8 convention

Otherwise just try to comment your work clearly. In the future I hope implement
tests but I haven't had the time yet.

## TODO

* Implement functions to correct for photobleaching
* Fix comment import
* Cropping/slicing interface?
* Auto and cross-correlation functions
* Display stacks
* Output images/stacks for presentations
* Split two color stacks
* Track conformation of chain
* Find cell boundary and area
* Intensity profiles
* Autoscale images for optimum result
