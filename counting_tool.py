import collections
from collections import deque
import colorsys
import csv
import cv2
from datetime import datetime
from datetime import timedelta
from imutils.video import FPS
from threading import Thread
import time
import math
#import matplotlib
#matplotlib.use("TkAgg")
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#from matplotlib.figure import Figure
from openpyxl import load_workbook
import os.path as path
import pandas as pd
import sys
from tkinter import BOTH
from tkinter import Button
from tkinter import Checkbutton
from tkinter import END
from tkinter import Entry
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askopenfilenames
from tkinter.filedialog import asksaveasfilename
from tkinter import IntVar
from tkinter import Label
from tkinter import LEFT
from tkinter import messagebox
from tkinter import RIGHT
from tkinter import Scrollbar
from tkinter import Text
from tkinter import Tk
from tkinter import Toplevel
from tkinter import ttk
from tkinter import Y
from tkinter import W

class App(object):

    Parameters = collections.namedtuple('p', ['a', 'b', 'c'])

    object_classes = {1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle', 5: 'airplane', 6: 'bus', 7: 'train', 8: 'truck', 9: 'boat', 10: 'traffic light',
                      11: 'fire hydrant', 12: 'stop sign', 13: 'parking meter', 14: 'bench', 15: 'bird', 16: 'cat', 17: 'dog', 18: 'horse', 19: 'sheep', 20: 'cow',
                      21: 'elephant', 22: 'bear', 23: 'zebra', 24: 'giraffe', 25: 'backpack', 26: 'umbrella', 27: 'handbag', 28: 'tie', 29: 'suitcase', 30: 'frisbee',
                      31: 'skis', 32: 'snowboard', 33: 'sports ball', 34: 'kite', 35: 'baseball bat', 36: 'baseball glove', 37: 'skateboard', 38: 'surfboard', 39: 'tennis racket', 40: 'bottle',
                      41: 'wine glass', 42: 'cup', 43: 'fork', 44: 'knife', 45: 'spoon', 46: 'bowl', 47: 'banana', 48: 'apple', 49: 'sandwich', 50: 'orange',
                      51: 'broccoli', 52: 'carrot', 53: 'hot dog', 54: 'pizza', 55: 'donut', 56: 'cake', 57: 'chair', 58: 'couch', 59: 'potted plant', 60: 'bed',
                      61: 'dining table', 62: 'toilet', 63: 'tv', 64: 'laptop', 65: 'mouse', 66: 'remote', 67: 'keyboard', 68: 'cell phone', 69: 'microwave', 70: 'oven',
                      71: 'toaster', 72: 'sink', 73: 'refrigerator', 74: 'book', 75: 'clock', 76: 'vase', 77: 'scissors', 78: 'teddy bear', 79: 'hair drier', 80: 'toothbrush'}

    def __init__(self):

        self.refPt = []
        self.image = None
        self.clone = None
        self.inter_line_counter = 0
        self.path_to_tracking_res = []
        self.result_lines = []
        self.scale_factor = 0.7
        self.fps = 25
        self.frames_per_part = 26520
        self.creation_time_first_frame = None
        self.cam = None
        self.slicee = None
        self.day = None        
        self.object_classes_to_detect = {'person': 1, 'bicycle': 1, 'car': 1, 'motorcycle': 1, 'bus': 1, 'truck': 1, 'dog': 1}
        self.root = Tk()
        self.export_granularity = 1
        self.export_granularity2 = 5
        self.export_granularity3 = 15
        self.export_raw = False
        self.opencv_thread = None
        self.source_changed = False

        
    def run(self):

        self.root.wm_title("Select actions:")
        self.root.resizable(width=False, height=False)
        self.root.geometry('{}x{}'.format(250, 525))
#        self.root.config(bg='lightgreen')
        self.root.attributes("-topmost", True)
        
        labelTop = Label(self.root,
                         text="Choose image scale factor\n and press '1. Select an image' ")
        labelTop.pack(side="top", padx="10", pady="5")
#        labelTop.config(bg='lightgreen')
        
        comboExample = ttk.Combobox(self.root,
                                    values=[
                                        0.5,
                                        0.6,
                                        0.7,
                                        0.8,
                                        0.9,
                                        1.0])

        comboExample.current(2)
        comboExample.state(['readonly'])
        comboExample.bind("<<ComboboxSelected>>", self.set_scale_factor)
        comboExample.pack(side="top", padx="10", pady="5")
        
        btn0 = Button(self.root, text="Read Instructions", command=self.instructions)
        btn0.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn1 = Button(self.root, text="1. Select an image", command=self.open_image)
        btn1.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn2 = Button(self.root, text="2. Select an tracking file(s)", command=self.open_tracks)
        btn2.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn6 = Button(self.root, text="3. Draw all tracks on image", command=self.draw_all_tracks)
        btn6.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        labelDraw = Label(self.root, text="4. Press & release left mouse button \n to draw some counting lines into the image.")
        labelDraw.pack(side="top", padx="10", pady="5")
#        labelDraw.config(bg='lightgreen')
        
        btn7 = Button(self.root, text="5. Start Intersection counting", command=self.count_intersections)
        btn7.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn8 = Button(self.root, text="6. Save current image", command=self.save_image)
        btn8.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn9 = Button(self.root, text="7. Save raw results as csv", command=self.save_counting_results)
        btn9.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn11 = Button(self.root, text="8. Save results to Excel", command=self.save_to_excel)
        btn11.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn5 = Button(self.root, text="Reset all (except input image)", command=self.reset_all)
        btn5.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        btn10 = Button(self.root, text="Reset (keep counting lines)",
                       command=self.reset_keep_counting_lines)
        btn10.pack(side="top", fill="both", expand="yes", padx="10", pady="5")

        self.root.protocol("WM_DELETE_WINDOW", App.on_closing)
        self.root.mainloop()

        cv2.destroyAllWindows()
        sys.exit()
        
    def set_scale_factor(self, event=None):

        if event is not None:
            self.scale_factor = float(event.widget.get())

    def open_image(self):

        options = {}
        options['filetypes'] = [('Image file', '.jpg'), ('Image file', '.jpeg')]
        options['defaultextension'] = "jpg"
        options['title'] = "Choose image"

        filename = askopenfilename(**options)

        if filename:              
            self.refPt = []
            self.inter_line_counter = 0
            self.result_lines = []
            self.path_to_tracking_res = []

            self.image = cv2.imread(filename)
            h = int(self.image.shape[0] * self.scale_factor)
            w = int(self.image.shape[1] * self.scale_factor)
            self.image = cv2.resize(self.image, (w, h))
            self.clone = self.image.copy()

            if self.opencv_thread is None:
                self.source_changed = False
                self.opencv_thread = Thread(target=self.show_image)
                self.opencv_thread.daemon = True
                self.opencv_thread.start()

            self.creation_time_first_frame = datetime.fromtimestamp(
                path.getctime(filename)).strftime('%Y-%m-%d %H:%M:%S')
            tmp = path.split(filename)[0]
            tmp2 = path.split(tmp)[0]
            tmp3 = path.split(tmp2)[0]
            self.cam = path.basename(tmp3)
            self.slicee = path.basename(tmp)
            self.day = path.basename(tmp2)
            
            self.ask_for_attributes()
    
    def show_image(self):

        cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow('image', 0, 0)
        cv2.setMouseCallback('image', self.draw_intersecting_line_callback)
                    
        self.start_processing()

        cv2.destroyAllWindows()
        self.opencv_thread = None

    def start_processing(self):
        
        if self.image is not None:
            
            fps = None
            fps = FPS().start()
            
            while True:
                
                try:
                    
                    fps.update()
                    fps.stop()
                    fps_text = "FPS " + "{:.2f}".format(fps.fps())                    
                    offsetX = 20
                    offsetY = 20
                    text_width = 100
                    text_height = 10
                    #(text_width, text_height) = cv2.getTextSize(fps_text, fontScale=cv2.FONT_HERSHEY_SIMPLEX, thickness=1)
                    cv2.rectangle(self.image, 
                                  (offsetX - 2, offsetY - text_height - 2), 
                                  (offsetX + 2 + text_width, offsetY + 2), 
                                  (0, 0, 0), cv2.FILLED)
                    cv2.putText(self.image, fps_text, (offsetX, offsetY),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
                    cv2.imshow('image', self.image)
                    
                    time.sleep(0.01)

                    ch = 0xFF & cv2.waitKey(1)
                    if ch == 27:
                        break

                except Exception:
                    continue
            
    def ask_for_attributes(self):

        window = Toplevel(self.root)
        window.wm_title("Is creation time correct?")
        window.resizable(width=False, height=False)
#        instruct.geometry('{}x{}'.format(500, 100))
        window.geometry('{}x{}'.format(250, 510))
#        time.config(bg='lightgreen')
        window.attributes('-topmost', True)

        label1 = Label(window, text="Is creation time correct?\n\
        Choose another time otherwise.\n\
        Make sure it is the time of the \n\
        first frame of the part!")
        label1.pack(side="top", padx="10", pady="5")

        e1 = Entry(window)
        e1.config(width=30)
        e1.insert(END, self.creation_time_first_frame)
        e1.pack(side="top", padx="10", pady="5")

        label2 = Label(window, text="Is frame rate correct?\n\
        Choose another fps otherwise.\n\
        Make sure it is the frame rate the\n\
        tracker used!")
        label2.pack(side="top", padx="10", pady="5")

        e2 = Entry(window)
        e2.config(width=10)
        e2.insert(END, self.fps)
        e2.pack(side="top", padx="10", pady="5")

        label3 = Label(window, text="Is number frames per part correct?\n\
        Choose another number otherwise.")
        label3.pack(side="top", padx="10", pady="5")

        e3 = Entry(window)
        e3.config(width=10)
        e3.insert(END, self.frames_per_part)
        e3.pack(side="top", padx="10", pady="5")

        label4 = Label(window, text="Whats the name of camera perspective?")
        label4.pack(side="top", padx="10", pady="5")

        e4 = Entry(window)
        e4.config(width=30)
        e4.insert(END, self.cam)
        e4.pack(side="top", padx="10", pady="5")        
        
        label5 = Label(window, text="Whats the name of time slice?")
        label5.pack(side="top", padx="10", pady="5")

        e5 = Entry(window)
        e5.config(width=30)
        e5.insert(END, self.slicee)
        e5.pack(side="top", padx="10", pady="5")
        
        label6 = Label(window, text="Whats the name of recording day?")
        label6.pack(side="top", padx="10", pady="5")

        e6 = Entry(window)
        e6.config(width=30)
        e6.insert(END, self.day)
        e6.pack(side="top", padx="10", pady="5")

        btn1 = Button(window, text="Save", command=lambda *args: self.set_parameters(e1.get(),
                                                                                     e2.get(),
                                                                                     e3.get(),
                                                                                     e4.get(),
                                                                                     e5.get(),
                                                                                     e6.get(),
                                                                                     window))

        btn1.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        
        self.root.wait_window(window)   

    def set_parameters(self, time, fps, number_frames, cam, slicee, day, window):

        self.creation_time_first_frame = time
        self.fps = fps
        self.frames_per_part = number_frames
        self.cam = cam
        self.slicee = slicee
        self.day = day
        window.destroy()

    def open_tracks(self):

        if self.image is not None:

            options = {}
            options['filetypes'] = [('Text file', '.txt'),
                                    ('Comma separated', '.csv'), ('All files', '*')]
            options['defaultextension'] = "txt"
            options['title'] = "Choose tracking results file(s)"

            mes = "If you choose more than one tracking file, make sure that those\
                files are named in a manner that make them sortable! It is important\
                in order to associate all frames with its correct creation time!"
            messagebox.showinfo("Caution!", mes)

            filenames = askopenfilenames(**options)

            if filenames:

                lst = list(filenames)
                self.path_to_tracking_res = sorted(lst)
                self.result_lines = []
                
                self.ask_for_object_classes()

        else:
            messagebox.showinfo("No image selected", "Please select an image first!")
    
    def ask_for_object_classes(self):

        window = Toplevel(self.root)
        window.wm_title("Choose object classes to detect?")
        window.resizable(width=False, height=False)
#        instruct.geometry('{}x{}'.format(500, 100))
        window.geometry('{}x{}'.format(200, 320))
#        time.config(bg='lightgreen')
        window.attributes('-topmost', True)
        
        label1 = Label(window, text="Choose object classes to detect?")
        label1.pack(side="top", padx="10", pady="5")

        self.object_classes_to_detect = {key:IntVar(value=value) for key, value in self.object_classes_to_detect.items()}
        
        for key, value in self.object_classes_to_detect.items():
            c = Checkbutton(window, text = key, variable = value, onvalue = 1, offvalue = 0)
            c.select()
            c.pack(side="top", anchor=W, padx="10", pady="5")
        
        btn1 = Button(window, text="Save", command=lambda *args: self.set_classes(window))
        btn1.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        
        self.root.wait_window(window)
        
    def set_classes(self, window):
        
        for key, value in self.object_classes_to_detect.items():
            self.object_classes_to_detect[key] = value.get()
            
        window.destroy()
                       
    def save_image(self):

        if self.image is not None:

            options = {}
            options['filetypes'] = [('Image file', '.jpg'), ('Image file', '.jpeg')]
            options['defaultextension'] = "jpg"
            options['initialfile'] = "counting_result_image.jpg"
            options['title'] = "Where to save?"

            filename = asksaveasfilename(**options)

            if filename:

                outputjpgfile = filename

                try:

                    cv2.imwrite(outputjpgfile, self.image)

                except Exception:

                    e = sys.exc_info()[0]
                    messagebox.showinfo("Error saving file", e)
                    raise

        else:
            messagebox.showinfo("No image selected", "Please select an image first!")

    def save_counting_results(self):

        if self.image is not None and self.result_lines:

            options = {}
            options['filetypes'] = [('Text file', '.txt'), ('Comma separated', '.csv')]
            options['defaultextension'] = "txt"
            options['initialfile'] = "counting_results.txt"
            options['title'] = "Where to save?"

            filename = asksaveasfilename(**options)

            if filename:

                outputtxtfile = filename

                try:

                    with open(outputtxtfile, 'w') as the_file:

                        the_file.write('\n'.join('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' %
                                                 (timestamp, date, time, track_class, intersection_line_id, direction,
                                                  intersect_point_x, intersect_point_y, point1_x, point1_y, point2_x, point2_y)
                                                 for (
                                                     timestamp, date, time, track_class, intersection_line_id, direction,
                                                     intersect_point_x, intersect_point_y, point1_x, point1_y, point2_x, point2_y)
                                                 in self.result_lines))
                except Exception:

                    e = sys.exc_info()[0]
                    messagebox.showinfo("Error saving file", e)
                    raise

        else:
            messagebox.showinfo("No image selected and/or counting results generated",
                                "Please select an image and start counting first!")

    def save_to_excel(self):

        if self.image is not None and self.result_lines:

            options = {}
            options['filetypes'] = [('Excel', '.xlsx')]
            options['defaultextension'] = "xlsx"
            options['initialfile'] = "counting_results_" + self.day + ".xlsx"
            options['title'] = "Where to save?"
            options['confirmoverwrite'] = False

            filename = asksaveasfilename(**options)

            if filename:
                
                try:
                    self.ask_for_export_granularity()

                    df = pd.DataFrame(self.result_lines, columns=('Timestamp', 'Date', 'Time', 'Object class', 'Intersection line id', 'Direction',
                                                                  'Intersection point x', 'Intersection point y',
                                                                  'Intersection line p1 x', 'Intersection line p1 y',
                                                                  'Intersection line p2 x', 'Intersection line p2 y'))

                    sorted_by_timestamp = df.sort_values(['Timestamp'], ascending=True)
                    sorted_by_timestamp.Timestamp = pd.to_datetime(sorted_by_timestamp['Timestamp'])

                    freq = str(self.export_granularity) + 'min'
                    freq2 = str(self.export_granularity2) + 'min'
                    freq3 = str(self.export_granularity3) + 'min'
                    
                    pivot1 = sorted_by_timestamp.pivot_table(index=[pd.Grouper(key='Timestamp', freq=freq)], values='Intersection point x',
                                                             columns=['Object class', 'Intersection line id', 'Direction'], aggfunc='count', fill_value=0)

                    pivot2 = sorted_by_timestamp.pivot_table(index=[pd.Grouper(key='Timestamp', freq=freq2)], values='Intersection point x',
                                                             columns=['Object class', 'Intersection line id', 'Direction'], aggfunc='count', fill_value=0)

                    pivot3 = sorted_by_timestamp.pivot_table(index=[pd.Grouper(key='Timestamp', freq=freq3)], values='Intersection point x',
                                                             columns=['Object class', 'Intersection line id', 'Direction'], aggfunc='count', fill_value=0)

                    sheetname = str(self.cam) + '_' + datetime.strptime(self.creation_time_first_frame,
                                                                        '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d') + '_' + str(self.slicee) + '_' + freq
                    
                    sheetname2 = str(self.cam) + '_' + datetime.strptime(self.creation_time_first_frame,
                                                                        '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d') + '_' + str(self.slicee) + '_' + freq2
                    
                    sheetname3 = str(self.cam) + '_' + datetime.strptime(self.creation_time_first_frame,
                                                                        '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d') + '_' + str(self.slicee) + '_' + freq3
                    
                    sheetname4 = str(self.cam) + '_' + datetime.strptime(self.creation_time_first_frame,
                                                                         '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d') + '_' + str(self.slicee) + '_' + 'raw'

                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:

                        if path.exists(filename):

                            workbook = load_workbook(filename)
                            writer.book = workbook
                            writer.sheets = dict((ws.title, ws) for ws in workbook.worksheets)
                            pivot1.to_excel(writer, sheet_name=sheetname)
                            pivot2.to_excel(writer, sheet_name=sheetname2)
                            pivot3.to_excel(writer, sheet_name=sheetname3)
                            
                            if self.export_raw == True:
                                sorted_by_timestamp.to_excel(writer, sheet_name=sheetname4)

                        else:

                            pivot1.to_excel(writer, sheet_name=sheetname)
                            pivot2.to_excel(writer, sheet_name=sheetname2)
                            pivot3.to_excel(writer, sheet_name=sheetname3)
                            
                            if self.export_raw == True:
                                sorted_by_timestamp.to_excel(writer, sheet_name=sheetname4)

                    writer.save()

                except Exception:
                    e = sys.exc_info()[0]
                    messagebox.showinfo("Error saving file", e)
                    raise
        else:
            messagebox.showinfo("No image selected and/or counting results generated",
                                "Please select an image and start counting first!")

    def ask_for_export_granularity(self):

        window = Toplevel(self.root)
        window.wm_title("Choose export granularity?")
        window.resizable(width=False, height=False)
#        instruct.geometry('{}x{}'.format(500, 100))
        window.geometry('{}x{}'.format(225, 200))
#        time.config(bg='lightgreen')
        window.attributes('-topmost', True)
        
        label1 = Label(window, text="Choose export granularities in minutes")
        label1.pack(side="top", padx="10", pady="5")

        e2 = Entry(window)
        e2.config(width=10)
        e2.insert(END, self.export_granularity)
        e2.pack(side="top", padx="10", pady="5")
        
        e3 = Entry(window)
        e3.config(width=10)
        e3.insert(END, self.export_granularity2)
        e3.pack(side="top", padx="10", pady="5")
        
        e4 = Entry(window)
        e4.config(width=10)
        e4.insert(END, self.export_granularity3)
        e4.pack(side="top", padx="10", pady="5")

        var = IntVar(value=int(self.export_raw))
        c = Checkbutton(window, text = 'Export raw data too?', variable = var, onvalue = 1, offvalue = 0)
        c.pack(side="top", anchor=W, padx="10", pady="5")
        
        btn1 = Button(window, text="Save", command=lambda *args: self.set_export_granularity(e2.get(), e3.get(), e4.get(),var.get(), window))
        btn1.pack(side="top", fill="both", expand="yes", padx="10", pady="5")
        
        self.root.wait_window(window)

    def set_export_granularity(self, export_granularity, export_granularity2, export_granularity3, export_raw, window):
        
        self.export_granularity = export_granularity
        self.export_granularity2 = export_granularity2
        self.export_granularity3 = export_granularity3
        self.export_raw = export_raw
            
        window.destroy()
        
    def draw_all_tracks(self):

        if self.path_to_tracking_res:

            for i in range(0, len(self.path_to_tracking_res)):

                track_buffer_dict = {}

                with open(self.path_to_tracking_res[i], 'r') as csv_file:

                    csv_reader = csv.reader(csv_file, delimiter=',')

                    try:

                        for row in csv_reader:

                            track_id = int(row[1])                            
                            track_class = int(float(row[7]))
                                                        
                            if  self.object_classes_to_detect.get(App.object_classes[track_class]) == 1:
                       
                                track_color = App.create_unique_color_int(track_id)
                                cy = (float(row[3]) + float(row[5])) * self.scale_factor
                                cx = (float(row[2]) + (float(row[4]) / 2)) * self.scale_factor
                                center = (int(cx), int(cy))
    
                                if track_id not in track_buffer_dict:
                                    pts = deque([], maxlen=None)
                                else:
                                    pts = track_buffer_dict[track_id]
    
                                if pts:
                                    last_center = pts[-1]  # .pop()
                                else:
                                    pts.append(center)
                                    track_buffer_dict[track_id] = pts
                                    continue
    
                                cv2.line(self.image, last_center, center, track_color, 1)
    
                                pts.append(center)
                                track_buffer_dict[track_id] = pts

                    except Exception:

                        e = sys.exc_info()[0]
                        messagebox.showinfo("Error parsing tracking file", e)
                        raise

            #cv2.imshow('image', self.image)

        else:
            messagebox.showinfo("No tracking file chosen", "Please select an tracking file first!")

    def reset_all(self):

        if self.image is None:
            messagebox.showinfo("No image selected", "Please select an image first!")

        else:
            self.image = self.clone.copy()
            self.refPt = []
            self.inter_line_counter = 0
            self.result_lines = []
            self.path_to_tracking_res = []
            #cv2.imshow("image", self.image)

    def reset_keep_counting_lines(self):

        if self.image is None:
            messagebox.showinfo("No image selected", "Please select an image first!")

        else:
            self.image = self.clone.copy()
            self.result_lines = []
            self.path_to_tracking_res = []
            # draw counting lines
            for j in range(0, len(self.refPt), 2):

                point1 = (self.refPt[j][0], self.refPt[j][1])
                point2 = (self.refPt[j + 1][0], self.refPt[j + 1][1])
                self.put_intersection_line_on_image(point1, point2)

            #cv2.imshow("image", self.image)

    def instructions(self):

        instruct = Toplevel(self.root)
        instruct.wm_title("Instructions:")
        instruct.resizable(width=False, height=False)
#        instruct.geometry('{}x{}'.format(500, 100))

        text = Text(instruct)
        scroll = Scrollbar(instruct, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.tag_configure('big', font=('Arial', 14, 'bold'))
        text.tag_configure('bold', foreground='#476042', font=('Arial', 10, 'bold'))
        text.tag_configure('normal', foreground='#476042', font=('Arial', 10))

        text.insert(END, '\nInstructions\n', 'big')
        quote = """
        First choose image, tracking result file, result jpg file and result txt file.
        If the image showing up, then press:
        -'e' for exit
        -'r' for reset, and
        -draw counting lines by press and
        release left mouse button,

        than press 'c' to start counting.
        -skip drawing lines and press 'c' to
        get all tracks visualized first.
        """
        text.insert(END, quote, 'normal')
        text.configure(state="disabled")
        text.pack(side=LEFT)
        scroll.pack(side=RIGHT, fill=Y)
                
    def count_intersections(self):

        if self.path_to_tracking_res and self.refPt:

            for i in range(0, len(self.path_to_tracking_res)):

                track_buffer_dict = {}

                try:
                    with open(self.path_to_tracking_res[i], 'r') as csv_file:

                        csv_reader = csv.reader(csv_file, delimiter=',')

                        for row in csv_reader:

                            image_id = int(row[0]) + (int(self.frames_per_part) * i)
                            track_id = int(row[1])
                            track_class = int(float(row[7]))
                            track_color = App.create_unique_color_int(track_id)
                            cy = (float(row[3]) + float(row[5])) * self.scale_factor
                            cx = (float(row[2]) + (float(row[4]) / 2)) * self.scale_factor
                            center = (int(cx), int(cy))
                                                        
                            if  self.object_classes_to_detect.get(App.object_classes[track_class]) == 1:

                                if track_id not in track_buffer_dict:
                                    pts = deque([], maxlen=None)
                                else:
                                    pts = track_buffer_dict[track_id]
    
                                if pts:
                                    last_center = pts[-1]  # .pop()
                                else:
                                    pts.append(center)
                                    track_buffer_dict[track_id] = pts
                                    continue
    
                                intersection_line_id = 0
    
                                for j in range(0, len(self.refPt), 2):
    
                                    intersection_line_id += 1
                                    point1 = (self.refPt[j][0], self.refPt[j][1])
                                    point2 = (self.refPt[j + 1][0], self.refPt[j + 1][1])
    
                                    line_params = App.get_parameters(last_center, center)
                                    intersect_line_params = App.get_parameters(point1, point2)
                                    intersect_point = App.check_intersec(
                                        intersect_line_params, line_params, last_center, center, point1, point2)
    
                                    if intersect_point:
                                                                                
                                        direction = App.get_direction(point1, point2, last_center)
                                        
                                        if direction:
                                            
                                            t = image_id / int(self.fps) * 1000
                                            timestamp = datetime.strptime(
                                                self.creation_time_first_frame, '%Y-%m-%d %H:%M:%S') + timedelta(milliseconds=t)
                                                    
                                            self.result_lines.append(
                                                (timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                                 timestamp.strftime('%Y-%m-%d'),
                                                 timestamp.strftime('%H:%M:%S'),
                                                 App.object_classes[track_class],
                                                 intersection_line_id,
                                                 direction,
                                                 intersect_point[0],
                                                 intersect_point[1],
                                                 point1[0],
                                                 point1[1],
                                                 point2[0],
                                                 point2[1]))
        
                                            cv2.circle(self.image, (int(intersect_point[0]), int(intersect_point[1])), 4,
                                                       track_color, -1)
                                            cv2.putText(self.image,
                                                        str(intersection_line_id),
                                                        (point1[0], point1[1] - 5),
                                                        cv2.FONT_HERSHEY_SIMPLEX,
                                                        0.7,
                                                        (0, 0, 255),
                                                        3)
        
                                pts.append(center)
                                track_buffer_dict[track_id] = pts

                except Exception:
                    e = sys.exc_info()[0]
                    messagebox.showinfo("Error parsing tracking file", e)
                    raise

            #cv2.imshow('image', self.image)
            self.draw_counting_sums()

        else:

            messagebox.showinfo("No tracking file chosen and/or counting lines drawn",
                                "Please select an tracking file first and draw counting lines!")
   
    def draw_counting_sums(self):
                
        df = pd.DataFrame(self.result_lines, columns=('Timestamp', 'Date', 'Time', 'Object class', 'Intersection line id', 'Direction',
                                                                  'Intersection point x', 'Intersection point y',
                                                                  'Intersection line p1 x', 'Intersection line p1 y',
                                                                  'Intersection line p2 x', 'Intersection line p2 y'))        
                
        pivot1 = df.pivot_table(index=['Object class', 'Intersection line id', 'Direction'],
                                values='Intersection point x',
                                aggfunc='count',
                                fill_value=0,
                                margins=True)
        
#        pivot2 = df.pivot_table(index=['Object class'],
#                                values='Intersection point x',
#                                aggfunc='count',
#                                fill_value=0)
        
        instruct = Toplevel(self.root)
        instruct.wm_title("Counting Sums:")
        
#        f = Figure(figsize=(3,3), dpi=100)
#        a = f.add_subplot(111)
#        pivot2.plot(kind='bar', ax=a)         
#       
#        canvas = FigureCanvasTkAgg(f, instruct)
#        canvas.show()
#        canvas._tkcanvas.pack(side=LEFT, fill=BOTH, expand=1)

        text = Text(instruct)    
        text.insert(END, str(pivot1), 'normal')        
        text.configure(state="disabled")
        text.pack(side=LEFT, fill=BOTH)
            
    def create_unique_color_int(tag, hue_step=0.41):

        h, v, = (tag * hue_step) % 1, 1. - (int(tag * hue_step) % 4) / 5.
        r, g, b = colorsys.hsv_to_rgb(h, 1., v)

        return int(255 * r), int(255 * g), int(255 * b)

    def get_parameters(point1, point2):  # (a,b,c) <- aX + bY + c = 0

        if point2[1] - point1[1] == 0:
            a = 0
            b = -1.0
        elif point2[0] - point1[0] == 0:
            a = -1.0
            b = 0
        else:
            a = (point2[1] - point1[1]) / (point2[0] - point1[0])
            b = -1.0

        c = (-a * point1[0]) - (b * point1[1])

        return App.Parameters(a, b, c)

    def check_intersec(params1, params2, point1, point2, point3, point4):

        det = params1.a * params2.b - params2.a * params1.b

        if det == 0:
            return None  # lines are parallel
        else:
            x = (params2.b * -params1.c - params1.b * -params2.c) / det
            y = (params1.a * -params2.c - params2.a * -params1.c) / det
            if x <= max(point1[0], point2[0]) and x >= min(point1[0], point2[0]) and y <= max(point1[1], point2[1]) and y >= min(point1[1], point2[1]):
                if x <= max(point3[0], point4[0]) and x >= min(point3[0], point4[0]) and y <= max(point3[1], point4[1]) and y >= min(point3[1], point4[1]):
                    return (int(x), int(y))
                else:
                    return None
            else:
                return None

    def get_perp_coord(point1, point2, length):

        aX = point1[0]
        aY = point1[1]
        bX = point2[0]
        bY = point2[1]

        vX = bX - aX
        vY = bY - aY

        mag = math.sqrt(vX * vX + vY * vY)
        vX = vX / mag  # sin()
        vY = vY / mag  # cos()
        temp = vX
        vX = 0 - vY
        vY = temp
        cX = bX + vX * length
        cY = bY + vY * length
        dX = bX - vX * length
        dY = bY - vY * length

        return (int(cX), int(cY)), (int(dX), int(dY))

    def get_line_mid_point(point1, point2):

        return ((point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2)

    def is_point_in_rectangle(rec_point1, rec_point2, point3):

        x1 = rec_point1[0]
        y1 = rec_point1[1]
        x2 = rec_point2[0]
        y2 = rec_point2[1]
        x3 = point3[0]
        y3 = point3[1]

        if x1 <= x3 <= x2 and y1 <= y3 <= y2:
            return True
        else:
            return False

    def get_direction(point1, point2, point3):

        if App.is_point_on_clockwise_side_of_line(point1, point2, point3) is True:
            return "AB"
        elif App.is_point_on_clockwise_side_of_line(point1, point2, point3) is False:
            return "BA"
        else:
            return None    
                               
    def is_point_on_clockwise_side_of_line(point1, point2, point3):

        aX = point1[0]
        aY = point1[1]
        bX = point2[0]
        bY = point2[1]

        pX = point3[0]
        pY = point3[1]

        v1 = (bX - aX, bY - aY)
        v2 = (bX - pX, bY - pY)
        xp = v1[0] * v2[1] - v1[1] * v2[0]  # Cross product

        if xp > 0:
            return False
        elif xp < 0:
            return True
        else:
            return None

    def draw_intersecting_line_callback(self, event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDOWN:
            if self.refPt:
                self.refPt.append((x, y))
            else:
                self.refPt = [(x, y)]

        elif event == cv2.EVENT_LBUTTONUP:
            if self.refPt[-1] != (x, y):
                self.refPt.append((x, y))
                self.put_intersection_line_on_image(
                    self.refPt[self.inter_line_counter], self.refPt[self.inter_line_counter + 1])
                #cv2.imshow("image", self.image)
                self.inter_line_counter += 2
            else:  # point instead of line
                self.refPt.pop()

    def put_intersection_line_on_image(self, point1, point2):

        cv2.line(self.image, point1, point2, (0, 255, 0), 2)
        cv2.putText(self.image,
                    "p1" + str(point1),
                    (point1[0] - 60, point1[1]),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.3,
                    (0, 0, 255),
                    1)
        cv2.putText(self.image,
                    "p2" + str(point2),
                    (point2[0] - 60, point2[1]),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.3,
                    (0, 0, 255),
                    1)

        point7 = App.get_line_mid_point(point1, point2)
        point8, point9 = App.get_perp_coord(point1, point7, 20)

        cv2.putText(self.image,
                    "A",
                    point8,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.3,
                    (0, 0, 255),
                    1)
        cv2.putText(self.image,
                    "B",
                    point9,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.3,
                    (0, 0, 255),
                    1)

        
    def on_closing():

        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            sys.exit()

if __name__ == '__main__':
    #    import sys

    App().run()
