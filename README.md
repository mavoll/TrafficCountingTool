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

1. Start tool, select an image representing the cams perspective and set parameters. Default values are taken from the image and its path using python´s os module.

<p align="center">
  <img src="/images/set_image_parameter.jpg" width="200" align="middle">
</p>

2. Select tracking result files and choose the object classes you want to count.

<p align="center">
  <img src="/images/select_tracking_files.jpg" width="200" align="middle">
  <img src="/images/select_classes.jpg" width="200" align="middle">
</p>

3. Draw all tracks (related to former chosen object classes).

<p align="center">
  <img src="/images/draw_all_tracks.jpg" width="200" align="middle">
</p>

4. Draw counting lines into image.

<p align="center">
  <img src="/images/draw_counting_lines.jpg" width="200" align="middle">
</p>

5. Start counting (can take a while depending off number of tracks and counting lines).

<p align="center">
  <img src="/images/start_counting.jpg" width="200" align="middle">
</p>

6. Choose export granularities and save results to excel. 

<p align="center">
  <img src="/images/save_results_to_excel.jpg" width="200" align="middle">
  <img src="/images/excel_results.jpg" width="200" align="middle">
</p>


## Authors

* **Marc-André Vollstedt** - marc.vollstedt@gmail.com

## Acknowledgments










