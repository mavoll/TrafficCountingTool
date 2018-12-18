# TrafficCountingTool
Tool to draw lines into images and count objects crossing those lines (using Python and Tkinter; depending on former generated tracking results)

To run the tool:

* Install prerequisites and run the python script (counting_tool.py), or
* just run the executable file (.exe file for windows; .app for mac will follow) 

### Please note:
* This tool depends on former generated tracking results. See this [repository](https://github.com/mavoll/MotionPathsExtraction) describing an approach to extract vehicle and pedestrian motion tracks from recorded videos using open-source software.  

## Prerequisites and used versions

* Python 3.6
* OpenCV 3.2
* Pandas 0.19.2
* Tkinter 8.6
* openpyxl 2.4.1

## Usage

1. Start tool, select an image representing the cams perspective. Set parameters (default values are taken from the image and its path using python´s os module):

<img src="/images/set_image_parameter.jpg" width="100">

![Select tracking files](/images/select_tracking_files.jpg)

![Select object classes to track](/images/select_classes.jpg)

![Draw all tracks](/images/draw_all_tracks.jpg)

![Draw counting lines](/images/draw_counting_lines.jpg)

![Start counting](/images/start_counting.jpg)

![Save to Excel](/images/save_results_to_excel.jpg)

![Excel result](/images/excel_results.jpg)

## Authors

* **Marc-André Vollstedt** - marc.vollstedt@gmail.com

## Acknowledgments










