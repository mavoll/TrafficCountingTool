# TrafficCountingTool
Tool to draw lines into images and count objects crossing those lines (using Python and Tkinter; depending on former generated tracking results)

To run the tool:

* Install prerequisites and run the python script (counting_tool.py), or
* just run the executable file (.exe file for windows; .app for mac will follow) 

### Please note:
* This tool depends on former generated tracking result files. Have a look at this [repository](https://github.com/mavoll/MotionPathsExtraction) describing an approach to extract vehicle and pedestrian motion tracks from recorded videos using open-source software.
* You can find example tracking result files [here](/test_data/cam_01/recording_day/time_slice/tracks_01.txt).
The format per line of those files is:
  * [image_is, object_id, rectangle_x, rectangle_y, widht, height, object_class, not relevant, not relevant, not relevant]
    * Object classes: {1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle', 6: 'bus', 8: 'truck', 17: 'dog'}
    * rectangle_x and rectangle_y are representing the lower left corner of each rectangle

## Prerequisites and used versions

* Python 3.6
* OpenCV 3.2
* Pandas 0.19.2
* Tkinter 8.6
* openpyxl 2.4.1

## Usage

* For just trying out, you can find an image and tracking result files [here](/test_data/cam_01/recording_day/time_slice/).

1. Start tool, select an image representing the cams perspective and set parameters. Default parameters are taken from the image (created at) and its path using python´s os module.

<p align="center">
  <img src="/images/set_image_parameter.jpg" width="600" align="middle">
</p>

2. Select tracking result files and choose the object classes you want to count for.

<p align="center">
  <img src="/images/select_tracking_files.jpg" width="450" align="middle">
  <img src="/images/select_classes.jpg" width="150" align="middle">
</p>

3. Draw all tracks (related to former chosen object classes). Drawing all relevant tracks helps to find best positions for the counting lines. 

<p align="center">
  <img src="/images/draw_all_tracks.jpg" width="600" align="middle">
</p>

4. Draw counting lines into image.

* point p1 is the point of the line where you have started to draw the line. Accordingly p2 is the point where you have released the left mouse button. 
* if you look from point p1 to point p2 you will always find B at the left hand side and A at the right hand side

<p align="center">
  <img src="/images/counting_line.jpg" width="600" align="middle">
  <img src="/images/draw_counting_lines.jpg" width="600" align="middle">
</p>

5. Start intersection counting (can take a while depending off number of tracks and counting lines).

<p align="center">
  <img src="/images/start_counting.jpg" width="600" align="middle">
</p>

6. Choose export granularities and save results to excel. 

<p align="center">
  <img src="/images/save_results_to_excel.jpg" width="300" align="middle">
  <img src="/images/excel_results.jpg" width="600" align="middle">
</p>

## Authors

* **Marc-André Vollstedt** - marc.vollstedt@gmail.com

## Acknowledgments










