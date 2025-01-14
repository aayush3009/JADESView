#! /usr/bin/env python

import os
import ast
import sys
import math
import time 
import argparse
import requests
from requests.auth import HTTPBasicAuth
from io import BytesIO
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.io import ascii
from astropy.table import Table

from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from astropy.visualization import (MinMaxInterval, ZScaleInterval, LogStretch, ImageNormalize, AsinhStretch, SinhStretch, LinearStretch)

import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg

#from Tkinter import *
try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import PIL
from PIL import ImageTk, Image, ImageGrab

JADESView_input_file = 'JADESView_input_file.dat'

# The default stretch on the various images
defaultstretch = 'LinearStretch'

# The default size of the various images
ra_dec_size_value = 2.0

# The default is to not make the crosshair
make_crosshair = False

# Currently, for testing JADESView, we have z_spec
use_zspec = True

def getEAZYimage(ID):
	start_time = time.time()
	EAZY_file_name = EAZY_files+str(ID)+'_EAZY_SED.png'

	if (EAZY_file_name.startswith('http')):
		response = requests.get(EAZY_file_name, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		image = Image.open(BytesIO(response.content))
	else:
		image = Image.open(EAZY_file_name)
		
	end_time = time.time()
	if (timer_verbose):
		print("Fetching the EAZY image: " +str(end_time - start_time))

	return image

def getBEAGLEimage(ID):
	start_time = time.time()
	BEAGLE_file_name = BEAGLE_files+str(ID)+'_BEAGLE_SED.png'

	if (BEAGLE_file_name.startswith('http')):
		response = requests.get(BEAGLE_file_name, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		image = Image.open(BytesIO(response.content))
	else:
		image = Image.open(BEAGLE_file_name)

	end_time = time.time()
	if (timer_verbose):
		print("Fetching the BEAGLE image: " +str(end_time - start_time))

	return image

def getSEDzimage(ID):
	start_time = time.time()
	SEDz_file_name = SEDz_files+str(ID)+'_BEAGLE_SED.png'

	if (SEDz_file_name.startswith('http')):
		response = requests.get(SEDz_file_name, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		image = Image.open(BytesIO(response.content))
	else:
		image = Image.open(SEDz_file_name)
		
	end_time = time.time()
	if (timer_verbose):
		print("Fetching the SEDz image: " +str(end_time - start_time))

	return image

def getBAGPIPESimage(ID):
	start_time = time.time()
	bagpipes_file_name_individual = '{:05d}.png'.format(ID)
	bagpipes_file_name = BAGPIPES_files+bagpipes_file_name_individual

	if (bagpipes_file_name.startswith('http')):
		response = requests.get(bagpipes_file_name, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		image = Image.open(BytesIO(response.content))
	else:
		image = Image.open(bagpipes_file_name)
		
	end_time = time.time()
	if (timer_verbose):
		print("Fetching the BAGPIPES image: " +str(end_time - start_time))

	return image

def resizeimage(image):
	global baseplotwidth
	wpercent = (baseplotwidth / float(image.size[0]))
	hsize = int((float(image.size[1]) * float(wpercent)))
	image = image.resize((baseplotwidth, hsize), PIL.Image.ANTIALIAS)
	photo = ImageTk.PhotoImage(image)
	return photo

def resizeBAGPIPESimage(image):
	global BAGPIPESbaseplotwidth
	wpercent = (BAGPIPESbaseplotwidth / float(image.size[0]))
	hsize = int((float(image.size[1]) * float(wpercent)))
	image = image.resize((BAGPIPESbaseplotwidth, hsize), PIL.Image.ANTIALIAS)
	photo = ImageTk.PhotoImage(image)
	return photo

def highz():
	global current_index
	global ID_iterator
	global ID_list
	global highZflag_array
	
	highZflag_array[current_index] = 1
	current_id = ID_list[ID_iterator]
	print("Object "+str(current_id)+" is a high-redshift candidate.")

def badfit():
	global current_index
	global ID_iterator
	global ID_list
	global badfitflag_array
	
	badfitflag_array[current_index] = 1
	current_id = ID_list[ID_iterator]
	print("Object "+str(current_id)+" has a bad fit.")

def baddata():
	global current_index
	global ID_iterator
	global ID_list
	global baddataflag_array
	
	baddataflag_array[current_index] = 1
	current_id = ID_list[ID_iterator]
	print("Object "+str(current_id)+" object has bad data.")

def update_eazy_text(current_id, eazy_results_IDs, eazy_results_zpeak):
	eazy_z_peak = getfile_value(current_id, eazy_results_IDs, eazy_results_zpeak, 4)
	eazy_z_a = getfile_value(current_id, eazy_results_IDs, eazy_results_za, 4)
	eazy_l68 = getfile_value(current_id, eazy_results_IDs, eazy_results_zl68, 4)
	eazy_u68 = getfile_value(current_id, eazy_results_IDs, eazy_results_zu68, 4)

	eazy_label_zpeak.configure(text="z_EAZY, peak = "+str(eazy_z_peak)+" ("+str(eazy_l68)+" - "+str(eazy_u68)+")")  
	eazy_label_za.configure(text="z_EAZY, a = "+str(eazy_z_a))  


def update_beagle_text(current_id, beagle_results_IDs, beagle_results_zavg):
	beagle_z_avg = getfile_value(current_id, beagle_results_IDs, beagle_results_zavg, 4)
	beagle_z_l68 = getfile_value(current_id, beagle_results_IDs, beagle_results_zl68, 4)
	beagle_z_u68 = getfile_value(current_id, beagle_results_IDs, beagle_results_zu68, 4)
	
	beagle_label.configure(text="z_BEAGLE,avg = "+str(beagle_z_avg)+" ("+str(beagle_z_l68)+" - "+str(beagle_z_u68)+")")  
	beagle_z_1 = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_1, 4)
	beagle_z_1_err = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_err_1, 4)
	beagle_z1_label.configure(text="z_BEAGLE,1 = "+str(beagle_z_1)+" +/- "+str(beagle_z_1_err))  
	beagle_z_2 = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_2, 4)
	beagle_z_2_err = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_err_2, 4)
	beagle_z2_label.configure(text="z_BEAGLE,2 = "+str(beagle_z_2)+" +/- "+str(beagle_z_2_err))  

	beagle_Pzgt2p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt2p0, 2)
	beagle_Pzgt4p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt4p0, 2)
	beagle_Pzgt6p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt6p0, 2)
	beagle_prob_label.configure(text="P(z > 2) = "+str(beagle_Pzgt2p0)+", P(z > 4) = "+str(beagle_Pzgt4p0)+", P(z > 4) = "+str(beagle_Pzgt6p0))  

def update_NN_text(current_id, NN_results_IDs, NN_results_zpred):

	NN_zpred = getfile_value(current_id, NN_results_IDs, NN_results_zpred, 4)
	NN_use = getfile_true_or_false(current_id, NN_results_IDs, NN_results_use)
	
	if (NN_use == True):
		nn_label.configure(text="z_NN = "+str(NN_zpred), fg = 'black')  
	if (NN_use == False):
		nn_label.configure(text="z_NN = "+str(NN_zpred)+" (USE = F)", fg = 'grey')  

	if(use_zspec == True):
		NN_zspec = getfile_value(current_id, NN_results_IDs, NN_results_zspec, 4)
		nn_label_zspec.configure(text="z_spec = "+str(NN_zspec))  
	
def update_color_selection_text(current_id, color_selection_results_IDs, color_selection_F090W_dropouts, color_selection_F115W_dropouts, color_selection_F150W_dropouts):
	is_F090W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F090W_dropouts)
	is_F115W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F115W_dropouts)
	is_F150W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F150W_dropouts)

	if (is_F090W_dropout):
		color_selection_label.configure(text="F090W Dropout")  
	elif (is_F115W_dropout):
		color_selection_label.configure(text="F115W Dropout")  
	elif (is_F150W_dropout):
		color_selection_label.configure(text="F150W Dropout")  
	else:
		color_selection_label.configure(text=" ")  
	
def update_BAGPIPES_text(current_id, BAGPIPES_results_IDs, BAGPIPES_results_zphot):
	BAGPIPES_zpred = getfile_value(current_id-1, BAGPIPES_results_IDs, BAGPIPES_results_zphot, 4)
	bagpipes_label.configure(text="z_BAGPIPES = "+str(BAGPIPES_zpred))
		

def nextobject():
	global e2
	global ID_iterator
	global current_index
	global ID_list
	global ID_list_indices
	global photo
	global new_photo
	global item4
	global item5
	global canvas   
	global fig_photo_objects
	global defaultstretch

	global eazy_positionx, eazy_positiony
	global eazytext_positionx, eazytext_positiony
	global beagle_positionx, beagle_positiony
	global beagletext_positionx, beagletext_positiony

	#global eazy_results_IDs, eazy_results_zpeak
	#global beagle_results_IDs, eazy_results_zavg
	
	notes_values[current_index] = e2.get()
	e2.delete(0,END)

	if (ID_iterator < len(ID_list)-1):
		ID_iterator = ID_iterator+1
#	else:
#		len(ID_list)-1
#		save_destroy()
	
	if (item4 is not None):
		canvas.delete(item4)

	if (item5 is not None):
		canvas.delete(item5)

		
	current_index = ID_list_indices[ID_iterator]
	current_id = ID_list[ID_iterator]
	e2.insert(0, notes_values[current_index])

	#image = Image.open(EAZY_files+str(current_id)+"_EAZY_SED.png")
	if (EAZY_plots_exist == True):
		image = getEAZYimage(current_id)
		start_time = time.time()
		image = cropEAZY(image)
		end_time = time.time()
		if (timer_verbose):
			print("Cropping the EAZY image: " +str(end_time - start_time))
		start_time = time.time()
		photo = resizeimage(image)
		end_time = time.time()
		if (timer_verbose):
			print("Resizing the EAZY image: " +str(end_time - start_time))
		start_time = time.time()
		item4 = canvas.create_image(eazy_positionx, eazy_positiony, image=photo)
		end_time = time.time()
		if (timer_verbose):
			print("Creating the EAZY canvas: " +str(end_time - start_time))
	
	if (BEAGLE_plots_exist == True):
		#new_image = Image.open(BEAGLE_files+str(current_id)+"_BEAGLE_SED.png")
		new_image = getBEAGLEimage(current_id)
		start_time = time.time()
		new_photo = resizeimage(new_image)
		end_time = time.time()
		if (timer_verbose):
			print("Resizing the BEAGLE image: " +str(end_time - start_time))
		start_time = time.time()
		item5 = canvas.create_image(beagle_positionx, beagle_positiony, image=new_photo)
		end_time = time.time()
		if (timer_verbose):
			print("Creating the BEAGLE canvas: " +str(end_time - start_time))
	
	start_time = time.time()
	fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, current_id, current_index, defaultstretch)
	end_time = time.time()
	if (timer_verbose):
		print("Creating the thumbnails: " +str(end_time - start_time))
		
	object_label.configure(text="Object "+str(current_id))  

	canvas.delete("separator")
	redshift_separator = canvas.create_rectangle(1100*sf, (toprow_y-320.0)*sf, 1940*sf, (toprow_y-310.0)*sf, outline="#0abdc6", fill="#0abdc6", tags="separator")
	if (EAZY_results_file_exists):
		update_eazy_text(current_id, eazy_results_IDs, eazy_results_zpeak)
	if (BEAGLE_results_file_exists):
		update_beagle_text(current_id, beagle_results_IDs, beagle_results_zavg)
	if (NN_results_file_exists):
		update_NN_text(current_id, NN_results_IDs, NN_results_zpred)
	if (color_selection_results_file_exists):
		update_color_selection_text(current_id, color_selection_IDs, color_selection_F090W_dropouts, color_selection_F115W_dropouts, color_selection_F150W_dropouts)
	if (BAGPIPES_results_file_exists):
		update_BAGPIPES_text(current_id, BAGPIPES_results_IDs, BAGPIPES_results_zphot)


def previousobject():
	global ID_iterator
	global current_index
	global e2
	global ID_list
	global ID_list_indices
	global photo
	global new_photo
	global item4
	global item5
	global canvas   
	global fig_photo_objects
	global defaultstretch

	global eazy_positionx, eazy_positiony
	global eazytext_positionx, eazytext_positiony
	global beagle_positionx, beagle_positiony
	global beagletext_positionx, beagletext_positiony

	#global eazy_results_IDs, eazy_results_zpeak
	#global beagle_results_IDs, eazy_results_zavg

	notes_values[current_index] = e2.get()
	e2.delete(0,END)

	if (ID_iterator > 0):
		ID_iterator = ID_iterator-1
	else:
		ID_iterator = 0
	
	current_index = ID_list_indices[ID_iterator]
	current_id = ID_list[ID_iterator]
	e2.insert(0, notes_values[current_index])

	if (EAZY_plots_exist == True):
		canvas.delete(item4)
		#image = Image.open(EAZY_files+str(current_id)+"_EAZY_SED.png")
		image = getEAZYimage(current_id)
		image = cropEAZY(image)
		photo = resizeimage(image)
		item4 = canvas.create_image(eazy_positionx, eazy_positiony, image=photo)
		
	if (BEAGLE_plots_exist == True):
		canvas.delete(item5)
		#new_image = Image.open(BEAGLE_files+str(current_id)+"_BEAGLE_SED.png")
		new_image = getBEAGLEimage(current_id)
		new_photo = resizeimage(new_image)
		item5 = canvas.create_image(beagle_positionx, beagle_positiony, image=new_photo)

	fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, current_id, current_index, defaultstretch)

	object_label.configure(text="Object "+str(current_id))  

	canvas.delete("separator")
	redshift_separator = canvas.create_rectangle(1100*sf, (toprow_y-320.0)*sf, 1940*sf, (toprow_y-310.0)*sf, outline="#0abdc6", fill="#0abdc6", tags="separator")
	if (EAZY_results_file_exists):
		update_eazy_text(current_id, eazy_results_IDs, eazy_results_zpeak)
	if (BEAGLE_results_file_exists):
		update_beagle_text(current_id, beagle_results_IDs, beagle_results_zavg)
	if (NN_results_file_exists):
		update_NN_text(current_id, NN_results_IDs, NN_results_zpred)
	if (color_selection_results_file_exists):
		update_color_selection_text(current_id, color_selection_IDs, color_selection_F090W_dropouts, color_selection_F115W_dropouts, color_selection_F150W_dropouts)
	if (BAGPIPES_results_file_exists):
		update_BAGPIPES_text(current_id, BAGPIPES_results_IDs, BAGPIPES_results_zphot)


def gotoobject():

	global ID_iterator
	global current_index
	global e2
	global ID_list
	global ID_list_indices
	global photo
	global new_photo
	global item4
	global item5
	global canvas   
	global fig_photo_objects
	global defaultstretch

	global eazy_positionx, eazy_positiony
	global eazytext_positionx, eazytext_positiony
	global beagle_positionx, beagle_positiony
	global beagletext_positionx, beagletext_positiony

	#global eazy_results_IDs, eazy_results_zpeak
	#global beagle_results_IDs, eazy_results_zavg

	notes_values[current_index] = e2.get()
	e2.delete(0,END)

	if (e1.get().isdigit() == True):

		#current_id = int(e1.get())
		ID_iterator = np.where(ID_list == int(e1.get()))[0][0]

		current_index = ID_list_indices[ID_iterator]
		current_id = ID_list[ID_iterator]
		e2.insert(0, notes_values[current_index])
	
		#image = Image.open(EAZY_files+str(current_id)+"_EAZY_SED.png")
		if (EAZY_plots_exist == True):
			canvas.delete(item4)
			image = getEAZYimage(current_id)
			image = cropEAZY(image)
			photo = resizeimage(image)
			item4 = canvas.create_image(eazy_positionx, eazy_positiony, image=photo)
		
		if (BEAGLE_plots_exist == True):
			canvas.delete(item5)
			#new_image = Image.open(BEAGLE_files+str(current_id)+"_BEAGLE_SED.png")
			new_image = getBEAGLEimage(current_id)
			new_photo = resizeimage(new_image)
			item5 = canvas.create_image(beagle_positionx, beagle_positiony, image=new_photo)
	
		fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, current_id, current_index, defaultstretch)

		object_label.configure(text="Object "+str(current_id))  

		canvas.delete("separator")
		redshift_separator = canvas.create_rectangle(1100*sf, (toprow_y-320.0)*sf, 1940*sf, (toprow_y-310.0)*sf, outline="#0abdc6", fill="#0abdc6", tags="separator")
		if (EAZY_results_file_exists):
			update_eazy_text(current_id, eazy_results_IDs, eazy_results_zpeak)
		if (BEAGLE_results_file_exists):
			update_beagle_text(current_id, beagle_results_IDs, beagle_results_zavg)
		if (NN_results_file_exists):
			update_NN_text(current_id, NN_results_IDs, NN_results_zpred)
		if (color_selection_results_file_exists):
			update_color_selection_text(current_id, color_selection_IDs, color_selection_F090W_dropouts, color_selection_F115W_dropouts, color_selection_F150W_dropouts)
		if (BAGPIPES_results_file_exists):
			update_BAGPIPES_text(current_id, BAGPIPES_results_IDs, BAGPIPES_results_zphot)

	else:
		print("That's not a valid ID number.")

def togglecrosshair():
	global ID_iterator
	global ID_list
	global ID_list_indices
	global canvas   
	global fig_photo_objects
	global ra_dec_size_value
	global defaultstretch

	global make_crosshair
	
	if (make_crosshair == False):
		make_crosshair = True
		btn12.config(font=('helvetica bold', textsizevalue))

	else:
		make_crosshair = False
		btn12.config(font=('helvetica', textsizevalue))
		
	fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, ID_list[ID_iterator], ID_list_indices[ID_iterator], defaultstretch)

# This will remove the thumbnails, for future work
def cropEAZY(img):

	#output_image = img.crop((0, 0, 3300, 1600))
	output_image = img.crop((0, 0, 3300, 1480))

	return output_image

# This will remove the thumbnails, for future work
def cropBAGPIPES(img):

	#output_image = img.crop((0, 0, 3300, 1600))
	output_bagpipes_image = img.crop((0, 0, 3982, 2749))

	return output_bagpipes_image

def linearstretch():
	global sf
	global textsizevalue
	global ID_iterator
	global ID_list
	global ID_list_indices
	global canvas   
	global fig_photo_objects
	global defaultstretch
	global btn5
	global btn6
	global btn7

	btn5.config(height = int(2*sf), width = int(10*sf), fg='black', highlightbackground='white', font=('helvetica bold', textsizevalue))
	btn6.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))
	btn7.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))

	defaultstretch = 'LinearStretch'	
	fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, ID_list[ID_iterator], ID_list_indices[ID_iterator], defaultstretch)

def logstretch():
	global sf
	global textsizevalue
	global ID_iterator
	global ID_list
	global ID_list_indices
	global canvas   
	global fig_photo_objects
	global defaultstretch
	global btn5
	global btn6
	global btn7

	btn5.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))
	btn6.config(height = int(2*sf), width = int(10*sf), fg='black', highlightbackground='white', font=('helvetica bold', textsizevalue))
	btn7.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))

	defaultstretch = 'LogStretch'
	fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, ID_list[ID_iterator], ID_list_indices[ID_iterator], defaultstretch)

def asinhstretch():
	global sf
	global textsizevalue
	global ID_iterator
	global ID_list
	global ID_list_indices
	global canvas   
	global fig_photo_objects
	global defaultstretch
	global btn5
	global btn6
	global btn7

	btn5.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))
	btn6.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))
	btn7.config(height = int(2*sf), width = int(10*sf), fg='black', highlightbackground='white', font=('helvetica bold', textsizevalue))

	defaultstretch = 'AsinhStretch'
	fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, ID_list[ID_iterator], ID_list_indices[ID_iterator], defaultstretch)

# This is kind of a hack to make sure that the image thumbnail size is printed on
# the output files, since none of the labels or buttons are printed when you use
# canvas.postscript()
def save_canvas():
	global thumbnailsize
	global sf
	global canvas
	global ID_list
	global ID_iterator
	global e3

	current_id = ID_list[ID_iterator]

	ra_dec_size_value = float(e3.get())

	fig = plt.figure(figsize=(thumbnailsize*2.51,thumbnailsize/4.0))
	ax8 = fig.add_axes([0, 0, 1, 1])
	ax8.text(0.02, 0.5, "Image Size: "+str(ra_dec_size_value)+"\" x "+str(ra_dec_size_value)+"\"", transform=ax8.transAxes, fontsize=12, fontweight='bold', ha='left', va='center', color = 'black')
	fig_x = 20*sf
	if (number_images <= 6):
		fig_y = 760*sf
	if ((number_images > 6) & (number_images <= 12)):
		fig_y = 900*sf
	if (number_images > 12):
		fig_y = 1040*sf	

	fig_size_object = draw_figure(canvas, fig, loc=(fig_x, fig_y))

	#fig = plt.figure(figsize=(thumbnailsize*2.51,thumbnailsize/4.0))
	fig2 = plt.figure(figsize=(7, 2.5))
	ax9 = fig2.add_axes([0, 0, 1, 1])
	if (EAZY_results_file_exists):
		eazy_z_peak = getfile_value(current_id, eazy_results_IDs, eazy_results_zpeak, 4)
		eazy_z_a = getfile_value(current_id, eazy_results_IDs, eazy_results_za, 4)
		eazy_l68 = getfile_value(current_id, eazy_results_IDs, eazy_results_zl68, 4)
		eazy_u68 = getfile_value(current_id, eazy_results_IDs, eazy_results_zu68, 4)
		ax9.text(0.02, 0.9, "z_EAZY, peak = "+str(eazy_z_peak)+" ("+str(eazy_l68)+" - "+str(eazy_u68)+")", transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='left', va='center', color = '#133e7c')
		ax9.text(0.02, 0.8, "z_EAZY, peak = "+str(eazy_z_a), transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='left', va='center', color = '#133e7c')
	if (BEAGLE_results_file_exists):
		beagle_z_avg = getfile_value(current_id, beagle_results_IDs, beagle_results_zavg, 4)
		beagle_z_l68 = getfile_value(current_id, beagle_results_IDs, beagle_results_zl68, 4)
		beagle_z_u68 = getfile_value(current_id, beagle_results_IDs, beagle_results_zu68, 4)
		
		beagle_z_1 = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_1, 4)
		beagle_z_1_err = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_err_1, 4)
		beagle_z_2 = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_2, 4)
		beagle_z_2_err = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_err_2, 4)
	
		beagle_Pzgt2p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt2p0, 2)
		beagle_Pzgt4p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt4p0, 2)
		beagle_Pzgt6p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt6p0, 2)

		ax9.text(0.02, 0.7, "z_BEAGLE,avg = "+str(beagle_z_avg)+" ("+str(beagle_z_l68)+" - "+str(beagle_z_u68)+")", transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='left', va='center', color = '#711c91')
		ax9.text(0.02, 0.6, "z_BEAGLE,1 = "+str(beagle_z_1)+" +/- "+str(beagle_z_1_err), transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='left', va='center', color = '#711c91')
		ax9.text(0.02, 0.5, "z_BEAGLE,2 = "+str(beagle_z_2)+" +/- "+str(beagle_z_2_err), transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='left', va='center', color = '#711c91')
		ax9.text(0.02, 0.4, "P(z > 2) = "+str(beagle_Pzgt2p0)+", P(z > 4) = "+str(beagle_Pzgt4p0)+", P(z > 4) = "+str(beagle_Pzgt6p0), transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='left', va='center', color = '#711c91')
	if (NN_results_file_exists):
		NN_zpred = getfile_value(current_id, NN_results_IDs, NN_results_zpred, 4)
		ax9.text(0.98, 0.9, "z_NN = "+str(NN_zpred), transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='right', va='center', color = '#091833')		
		if (use_zspec == True):
			NN_zspec = getfile_value(current_id, NN_results_IDs, NN_results_zspec, 4)
			ax9.text(0.98, 0.8, "z_spec = "+str(NN_zspec), transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='right', va='center', color = 'red')		
	if (color_selection_results_file_exists):
		is_F090W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F090W_dropouts)
		is_F115W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F115W_dropouts)
		is_F150W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F150W_dropouts)

		if (is_F090W_dropout):
			ax9.text(0.98, 0.1, "F090W Dropout", transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='right', va='center', color = 'black')
		elif (is_F115W_dropout):
			ax9.text(0.98, 0.1, "F115W Dropout", transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='right', va='center', color = 'black')
		elif (is_F150W_dropout):
			ax9.text(0.98, 0.1, "F150W Dropout", transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='right', va='center', color = 'black')
	if (BAGPIPES_results_file_exists):
		BAGPIPES_zpred = getfile_value(current_id-1, BAGPIPES_results_IDs, BAGPIPES_results_zphot, 4)
		ax9.text(0.98, 0.3, "z_BAGPIPES = "+str(BAGPIPES_zpred), transform=ax9.transAxes, fontsize=14, fontweight='bold', ha='right', va='center', color = '#091833')		


	fig2_x = 950
	fig2_y = 650
	
	fig2_size_object = draw_figure(canvas, fig2, loc=(fig2_x, fig2_y))
	#fig.close()

	# The text needs to be at: 1100, 600
	#fig2 = plt.figure(figsize=(500,200))
	#ax9 = fig.add_axes([0, 0, 1, 1])
	#ax9.text(0.1, 0.1, "z_EAZY = "+str(eazy_z)+" ("+str(eazy_l68)+" - "+str(eazy_u68)+")", transform=ax9.transAxes, fontsize=12, fontweight='bold', ha='left', va='center', color = 'black')
	#fig_x = 1100
	#fig_y = 600
	#fig_redshift_object = draw_figure(canvas, fig2, loc=(fig_x, fig_y))
	#fig2.close()

	output_filename = str(current_id)+'_JADESView'
	canvas.postscript(file=output_filename+'.eps', colormode='color')
	
	# use PIL to convert to PNG 
	img = Image.open(output_filename+'.eps') 
	os.system('rm '+output_filename+'.eps')
	#print output_filename+'.png'
	img.save(output_filename+'.png', 'png') 

def changeradecsize():
	global ID_iterator
	global ID_list
	global ID_list_indices
	global canvas   
	global fig_photo_objects
	global ra_dec_size_value
	global defaultstretch
	global e3

	ra_dec_size_value = float(e3.get())
	fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, ID_list[ID_iterator], ID_list_indices[ID_iterator], defaultstretch)


def draw_figure(canvas, figure, loc=(0, 0)):
    """ Draw a matplotlib figure onto a Tk canvas

    loc: location of top-left corner of figure on canvas in pixels.
    Inspired by matplotlib source: lib/matplotlib/backends/backend_tkagg.py
    """
    figure_canvas_agg = FigureCanvasAgg(figure)
    figure_canvas_agg.draw()
    figure_x, figure_y, figure_w, figure_h = figure.bbox.bounds
    figure_w, figure_h = int(figure_w), int(figure_h)
    photo = PhotoImage(master=canvas, width=figure_w, height=figure_h)

    # Position: convert from top-left anchor to center anchor
    canvas.create_image(loc[0] + figure_w/2, loc[1] + figure_h/2, image=photo)

    # Unfortunately, there's no accessor for the pointer to the native renderer
    tkagg.blit(photo, figure_canvas_agg.get_renderer()._renderer, colormode=2)

    # Return a handle which contains a reference to the photo object
    # which must be kept live or else the picture disappears
    return photo

def create_thumbnails(canvas, fig_photo_objects, id_value, id_value_index, stretch):
	#global ID_values
	global thumbnailsize
	global RA_values
	global DEC_values
	global ra_dec_size_value
	global image_all
	global image_hdu_all
	global image_wcs_all
	global image_flux_value_err_cat
	global all_images_filter_name
	global number_images
	global SNR_values
	
	# Let's associate the selected object with it's RA and DEC		
	# Create the object thumbnails. 
	#idx_cat = np.where(ID_values == id_value)[0]
	idx_cat = id_value_index
	objRA = RA_values[idx_cat]
	objDEC = DEC_values[idx_cat]
			
	cosdec_center = math.cos(objDEC * 3.141593 / 180.0)
		
	# Set the position of the object
	position = SkyCoord(str(objRA)+'d '+str(objDEC)+'d', frame='fk5')
	size = u.Quantity((ra_dec_size_value, ra_dec_size_value), u.arcsec)
	
	fig_photo_objects = np.empty(0, dtype = 'object')
	for i in range(0, number_images):
		image = image_hdu_all[i].data
		image_hdu = image_hdu_all[i]
		image_wcs = image_wcs_all[i]
				
#		if (all_images_filter_name[i] == 'HST_F814W'):
#			image_wcs.sip = None
		
		if (image_flux_value_err_cat[idx_cat, i] > -9999):
			# Make the cutout
			#print(all_images_filter_name[i])
			start_time = time.time()
			image_cutout = Cutout2D(image, position, size, wcs=image_wcs)
			#end_time = time.time()
			#print("       Running Cutout2D: " +str(end_time - start_time))
			
			SNR_fontsize_large = int(15.0*sf)
			SNR_fontsize_small = int(12.0*sf)
			
			# Create the wcs axes
			plt.clf()
			fig = plt.figure(figsize=(thumbnailsize,thumbnailsize))
			ax3 = fig.add_axes([0, 0, 1, 1], projection=image_cutout.wcs)
			if (all_images_filter_name[i] == 'SEGMAP'):
				ax3.text(0.51, 0.96, all_images_filter_name[i], transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', ha='center', va='top', color = 'black')
				ax3.text(0.5, 0.95, all_images_filter_name[i], transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', ha='center', va='top', color = 'white')
			
			else:
				ax3.text(0.51, 0.96, all_images_filter_name[i].split('_')[1], transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', ha='center', va='top', color = 'black')
				ax3.text(0.5, 0.95, all_images_filter_name[i].split('_')[1], transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', ha='center', va='top', color = 'white')
			if (number_images <= 18):
				if (SNR_values[idx_cat, i] > -100):
					#if (all_images_filter_name[i] != 'SEGMAP'):
					if (SNR_values[idx_cat, i] != -9999):
						ax3.text(0.96, 0.06, 'SNR = '+str(round(SNR_values[idx_cat, i],2)), transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', horizontalalignment='right', color = 'black')
						ax3.text(0.95, 0.05, 'SNR = '+str(round(SNR_values[idx_cat, i],2)), transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', horizontalalignment='right', color = 'white')
				else:
					#if (all_images_filter_name[i] != 'SEGMAP'):
					if (SNR_values[idx_cat, i] != -9999):					
						ax3.text(0.96, 0.06, 'SNR < -100', transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', horizontalalignment='right', color = 'black')
						ax3.text(0.95, 0.05, 'SNR < -100', transform=ax3.transAxes, fontsize=SNR_fontsize_large, fontweight='bold', horizontalalignment='right', color = 'white')
			else:
				if (SNR_values[idx_cat, i] > -100):
					if (all_images_filter_name[i] != 'SEGMAP'):
						ax3.text(0.96, 0.06, 'SNR = '+str(round(SNR_values[idx_cat, i],2)), transform=ax3.transAxes, fontsize=SNR_fontsize_small, fontweight='bold', horizontalalignment='right', color = 'black')
						ax3.text(0.95, 0.05, 'SNR = '+str(round(SNR_values[idx_cat, i],2)), transform=ax3.transAxes, fontsize=SNR_fontsize_small, fontweight='bold', horizontalalignment='right', color = 'white')
				else:
					if (all_images_filter_name[i] != 'SEGMAP'):
						ax3.text(0.96, 0.06, 'SNR < -100', transform=ax3.transAxes, fontsize=SNR_fontsize_small, fontweight='bold', horizontalalignment='right', color = 'black')
						ax3.text(0.95, 0.05, 'SNR < -100', transform=ax3.transAxes, fontsize=SNR_fontsize_small, fontweight='bold', horizontalalignment='right', color = 'white')
			
			if (make_crosshair == True):
				ax3.plot([0.5, 0.5], [0.65, 0.8], linewidth=2.0, transform=ax3.transAxes, color = 'white')
				ax3.plot([0.5, 0.5], [0.2, 0.35], linewidth=2.0, transform=ax3.transAxes, color = 'white')
				ax3.plot([0.2, 0.35], [0.5, 0.5], linewidth=2.0, transform=ax3.transAxes, color = 'white')
				ax3.plot([0.65, 0.8], [0.5, 0.5], linewidth=2.0, transform=ax3.transAxes, color = 'white')
						
			# Set the color map
			plt.set_cmap('gray')
			
			indexerror = 0		
			# Normalize the image using the min-max interval and a square root stretch
			thumbnail = image_cutout.data
			#start_time = time.time()
			if (stretch == 'AsinhStretch'):
				try:
					norm = ImageNormalize(thumbnail, interval=ZScaleInterval(), stretch=AsinhStretch())
				except IndexError:
					indexerror = 1
				except UnboundLocalError:
					indexerror = 1
			if (stretch == 'LogStretch'):
				try:
					norm = ImageNormalize(thumbnail, interval=ZScaleInterval(), stretch=LogStretch(100))
				except IndexError:
					indexerror = 1
				except UnboundLocalError:
					indexerror = 1
			if (stretch == 'LinearStretch'):
				try:
					norm = ImageNormalize(thumbnail, interval=ZScaleInterval(), stretch=LinearStretch())
				except IndexError:
					indexerror = 1
				except UnboundLocalError:
					indexerror = 1
			#end_time = time.time()
			#print("       Stretching Image: " +str(end_time - start_time))
			
			#start_time = time.time()
			if (all_images_filter_name[i] == 'SEGMAP'):
				ax3.imshow(thumbnail, origin = 'lower', aspect='equal')
			elif (indexerror == 0):
				ax3.imshow(thumbnail, origin = 'lower', aspect='equal', norm = norm)
			else:
				ax3.imshow(thumbnail, origin = 'lower', aspect='equal')
			#end_time = time.time()
			#print("       Plotting Thumbnail: " +str(end_time - start_time))
			
			if (number_images <= 18):
				if (i <= 5):
					fig_x, fig_y = (20*sf)+(175*i*sf), 500*sf
				if ((i > 5) & (i <= 11)):
					fig_x, fig_y = (20*sf)+(175*(i-6)*sf), 675*sf
				if ((i > 11) & (i <= 17)):
					fig_x, fig_y = (20*sf)+(175*(i-12)*sf), 850*sf
			if ((number_images > 18) & (number_images <= 24)):
				if (i <= 7):
					fig_x, fig_y = (20*sf)+(130*i*sf), 500*sf
				if ((i > 7) & (i <= 15)):
					fig_x, fig_y = (20*sf)+(130*(i-8)*sf), 675*sf
				if ((i > 15) & (i <= 23)):
					fig_x, fig_y = (20*sf)+(130*(i-16)*sf), 850*sf
			if ((number_images > 24) & (number_images <= 32)):
				if (i <= 7):
					fig_x, fig_y = (20*sf)+(130*i*sf), 500*sf
				if ((i > 7) & (i <= 15)):
					fig_x, fig_y = (20*sf)+(130*(i-8)*sf), 625*sf
				if ((i > 15) & (i <= 23)):
					fig_x, fig_y = (20*sf)+(130*(i-16)*sf), 750*sf
				if ((i > 23) & (i <= 31)):
					fig_x, fig_y = (20*sf)+(130*(i-24)*sf), 875*sf
							
			# Keep this handle alive, or else figure will disappear
			fig_photo_objects = np.append(fig_photo_objects, draw_figure(canvas, fig, loc=(fig_x, fig_y)))
			plt.close('all')
			end_time = time.time()
			if (timer_verbose):
				print("       Plotting Thumbnail: " +str(end_time - start_time))

	return fig_photo_objects



def save_destroy():
	global ID_values
	global current_index
	global ID_iterator
	global highZflag_array
	global output_flags_file
	global output_notes_file
	global e2 
	
	if (os.path.exists(output_flags_file)):
		os.system('rm '+output_flags_file)
	if (os.path.exists(output_notes_file)):
		os.system('rm '+output_notes_file)

	# First, let's make the dtype and colnames arrays
	colnames = np.zeros(4, dtype ='S20')
	dtype = np.zeros(4, dtype ='str')
	colnames[0] = 'ID'
	colnames[1] = 'HighZFlag'
	colnames[2] = 'BadFitFlag'
	colnames[3] = 'BadDataFlag'
	dtype[0] = 'I'
	dtype[1] = 'I'
	dtype[2] = 'I'
	dtype[3] = 'I'
	
	# And now let's assemble the data array
	output_data = np.zeros([number_objects, 4])
	output_data[:,0] = ID_values
	output_data[:,1] = highZflag_array
	output_data[:,2] = badfitflag_array
	output_data[:,3] = baddataflag_array
	
	# And finally, let's write out the output file.
	outtab = Table(output_data, names=colnames, dtype=dtype)
	outtab.write(output_flags_file)

	#notes_values[ID_iterator] = e2.get()
	current_id = ID_list[ID_iterator]
	notes_values[current_index] = e2.get()

	w = open(output_notes_file, 'a')
	w.write('#ID    Notes \n')
	for z in range(0, len(ID_values)):
		if (notes_values[z] != ''):
			w.write(str(ID_values[z])+'    '+str(notes_values[z])+'\n')
	w.close()

	quit()
	#root.destroy()

def plotbeagle():
	global e2
	global ID_iterator
	global current_index
	global ID_list
	global ID_list_indices
	global photo
	global new_photo
	global item4
	global item5
	global canvas   
	global fig_photo_objects
	global defaultstretch

	global eazy_positionx, eazy_positiony
	global eazytext_positionx, eazytext_positiony
	global beagle_positionx, beagle_positiony
	global beagletext_positionx, beagletext_positiony

	notes_values[current_index] = e2.get()
	e2.delete(0,END)

	canvas.delete(item5)
		
	current_index = ID_list_indices[ID_iterator]
	current_id = ID_list[ID_iterator]
	e2.insert(0, notes_values[current_index])

	new_image = getBEAGLEimage(current_id)
	start_time = time.time()
	new_photo = resizeimage(new_image)
	end_time = time.time()
	if (timer_verbose):
		print("Resizing the BEAGLE image: " +str(end_time - start_time))
	start_time = time.time()
	item5 = canvas.create_image(beagle_positionx, beagle_positiony, image=new_photo)
	end_time = time.time()
	if (timer_verbose):
		print("Creating the BEAGLE canvas: " +str(end_time - start_time))
	
	btn13.config(font=('helvetica bold', textsizevalue))
	btn10.config(font=('helvetica', textsizevalue))

	otherfit_label.configure(text="BEAGLE FIT")  
	
def plotbagpipes():
	global e2
	global ID_iterator
	global current_index
	global ID_list
	global ID_list_indices
	global photo
	global new_photo
	global item4
	global item5
	global canvas   
	global fig_photo_objects
	global defaultstretch

	global bagpipes_positionx, bagpipes_positiony

	notes_values[current_index] = e2.get()
	e2.delete(0,END)

	if (item5 is not None):
		canvas.delete(item5)
		
	current_index = ID_list_indices[ID_iterator]
	current_id = ID_list[ID_iterator]
	e2.insert(0, notes_values[current_index])

	new_image = getBAGPIPESimage(current_id)
	new_image = cropBAGPIPES(new_image)
	start_time = time.time()
	new_photo = resizeBAGPIPESimage(new_image)
	end_time = time.time()
	if (timer_verbose):
		print("Resizing the BAGPIPES image: " +str(end_time - start_time))
	start_time = time.time()
	item5 = canvas.create_image(bagpipes_positionx, bagpipes_positiony, image=new_photo)
	end_time = time.time()
	if (timer_verbose):
		print("Creating the BAGPIPES canvas: " +str(end_time - start_time))

	btn10.config(font=('helvetica bold', textsizevalue))
	btn13.config(font=('helvetica', textsizevalue))

	otherfit_label.configure(text="BAGPIPES FIT")  

def plotsedz():
	global e2
	global ID_iterator
	global current_index
	global ID_list
	global ID_list_indices
	global photo
	global new_photo
	global item4
	global item5
	global canvas   
	global fig_photo_objects
	global defaultstretch

	global eazy_positionx, eazy_positiony
	global eazytext_positionx, eazytext_positiony
	global beagle_positionx, beagle_positiony
	global beagletext_positionx, beagletext_positiony

	notes_values[current_index] = e2.get()
	e2.delete(0,END)

	canvas.delete(item5)
		
	current_index = ID_list_indices[ID_iterator]
	current_id = ID_list[ID_iterator]
	e2.insert(0, notes_values[current_index])

	new_image = getSEDzimage(current_id)
	start_time = time.time()
	new_photo = resizeimage(new_image)
	end_time = time.time()
	if (timer_verbose):
		print("Resizing the SEDz image: " +str(end_time - start_time))
	start_time = time.time()
	item5 = canvas.create_image(beagle_positionx, beagle_positiony, image=new_photo)
	end_time = time.time()
	if (timer_verbose):
		print("Creating the SEDz canvas: " +str(end_time - start_time))

	#btn9.config(font=('helvetica', textsizevalue))
	#btn11.config(font=('helvetica bold', textsizevalue))


def getfile_value(current_id, results_IDs, results_values, round_value):
	find_value_index = np.where(results_IDs == current_id)[0]
	if (len(find_value_index) > 0):
		return round(results_values[find_value_index[0]],round_value)
	else:
		return -9999

def getfile_true_or_false(current_id, results_IDs, results_values):
	find_value_index = np.where(results_IDs == current_id)[0]
	if (len(find_value_index) > 0):
		return results_values[find_value_index[0]] 
	else:
		return False


parser = argparse.ArgumentParser()

######################
# Optional Arguments #
######################

# JADESView Input File
parser.add_argument(
  '-input',
  help="JADESView Input File?",
  action="store",
  type=str,
  dest="input",
  required=False
)


# ID number
parser.add_argument(
  '-id',
  help="ID Number?",
  action="store",
  type=int,
  dest="id_number",
  required=False
)

# ID list
parser.add_argument(
  '-idlist',
  help="List of ID Numbers?",
  action="store",
  type=str,
  dest="id_number_list",
  required=False
)

# command line argument list of objects
parser.add_argument(
  '-idarglist',
  help="Command line argument list of objects",
  action="store",
  type=str,
  dest="idarglist",
  required=False
)

# Timer Verbose
parser.add_argument(
  '-tverb',
  help="Print timer values?",
  action="store",
  type=str,
  dest="tverb",
  required=False
)


args=parser.parse_args()

if (args.input):
	JADESView_input_file = args.input

timer_verbose = False
if (args.tverb):
	timer_verbose = True


# Right now, the default canvaswidth is 2000. 
canvaswidth = 2000

# I have to set these as false unless the file is specified in the input file
EAZY_plots_exist = False
EAZY_results_file_exists = False
BEAGLE_plots_exist = False
BEAGLE_results_file_exists = False
BAGPIPES_plots_exist = False
BAGPIPES_results_file_exists = False
NN_results_file_exists = False
color_selection_results_file_exists = False

# Read in the various input values from the input file. 
input_lines = np.loadtxt(JADESView_input_file, dtype='str')
number_input_lines = len(input_lines[:,0])
for i in range(0, number_input_lines):
	if (input_lines[i,0] == 'input_photometry'):
		input_photometry = input_lines[i,1]
	if (input_lines[i,0] == 'image_list'):
		all_images_file_name = input_lines[i,1]
	if (input_lines[i,0] == 'EAZY_files'):
		EAZY_files = input_lines[i,1]
		EAZY_plots_exist = True
	if (input_lines[i,0] == 'EAZY_results'):
		EAZY_results_file = input_lines[i,1]
		EAZY_results_file_exists = True
		EAZY_results_file_exists = os.path.exists(EAZY_results_file)
	if (input_lines[i,0] == 'BEAGLE_files'):
		BEAGLE_files = input_lines[i,1]
		BEAGLE_plots_exist = True
	if (input_lines[i,0] == 'BEAGLE_results'):
		BEAGLE_results_file = input_lines[i,1]
		BEAGLE_results_file_exists = True
		BEAGLE_results_file_exists = os.path.exists(BEAGLE_results_file)
	if (input_lines[i,0] == 'BAGPIPES_files'):
		BAGPIPES_files = input_lines[i,1]
		BAGPIPES_plots_exist = True
	if (input_lines[i,0] == 'BAGPIPES_results'):
		BAGPIPES_results_file = input_lines[i,1]
		BAGPIPES_results_file_exists = True
		BAGPIPES_results_file_exists = os.path.exists(BAGPIPES_results_file)
	if (input_lines[i,0] == 'SEDz_files'):
		SEDz_files = input_lines[i,1]
	if (input_lines[i,0] == 'NN_results'):
		NN_results_file = input_lines[i,1]
		NN_results_file_exists = True
		NN_results_file_exists = os.path.exists(NN_results_file)
	if (input_lines[i,0] == 'color_selection_results'):
		color_selection_results_file = input_lines[i,1]
		color_selection_results_file_exists = True
		color_selection_results_file_exists = os.path.exists(color_selection_results_file)
	if (input_lines[i,0] == 'output_flags_file'):
		output_flags_file = input_lines[i,1]
	if (input_lines[i,0] == 'output_notes_file'):
		output_notes_file = input_lines[i,1]
	if (input_lines[i,0] == 'canvaswidth'):
		canvaswidth = float(input_lines[i,1])
	if (input_lines[i,0] == 'defaultstretch'):
		defaultstretch = input_lines[i,1]
	if (input_lines[i,0] == 'ra_dec_size_value'):
		ra_dec_size_value = float(input_lines[i,1])
	if (input_lines[i,0] == 'fenrir_username'):
		fenrir_username = input_lines[i,1]
	if (input_lines[i,0] == 'fenrir_password'):
		fenrir_password = input_lines[i,1]

#base64string = base64.b64encode('%s:%s' % (fenrir_username, fenrir_password))

# # # # # # # # # # # # # # # # # # 
# Let's open up all the input files

# Open up the image list file
images_all_txt = np.loadtxt(all_images_file_name, dtype='str')
if (len(images_all_txt[0]) > 2):
	# First, if the user specifies where the science data extension is, they'll put 
	# them in the second column.
	all_images_filter_name = images_all_txt[:,0]
	all_image_extension_number = images_all_txt[:,1].astype('int')
	all_image_paths = images_all_txt[:,2]
else:
	# Here, we assume that the science extension is 1 
	all_images_filter_name = images_all_txt[:,0]
	all_image_extension_number = np.zeros(len(all_images_filter_name))+1
	all_image_paths = images_all_txt[:,1]

number_image_filters = len(all_images_filter_name)
number_images = len(all_image_paths)

# astropy.io.fits.open(...,memmap='True',lazy_load_hdus='True')

image_all = np.empty(0)
image_hdu_all = np.empty(0)
image_wcs_all = np.empty(0)
for i in range(0, number_images):
	print("Opening up image: "+all_image_paths[i])
	if (all_image_paths[i] == 'NoImage'):
		all_image_paths[i] = 'NoImage.fits'
	image_all = np.append(image_all, fits.open(all_image_paths[i]))
	try:
		#image_hdu_all = np.append(image_hdu_all, fits.open(all_image_paths[i])[1])
		image_hdu_all = np.append(image_hdu_all, fits.open(all_image_paths[i])[all_image_extension_number[i]])
	except IndexError:
		#print('IndexError')
		image_hdu_all = np.append(image_hdu_all, fits.open(all_image_paths[i]))
		#print('Running fits.open('+str(all_image_paths[i])+')')
	#print('Running WCS(image_hdu_all[i].header)')
	image_wcs_all = np.append(image_wcs_all, WCS(image_hdu_all[i].header))


sf = canvaswidth / 2000.0 # This is the "shrinkfactor" by which all of the canvas
                          # element positions and sizes are shrunk or expanded. I 
                          # RECOGNIZE THAT I SHOULD PUT THINGS ON A GRID, BUT THAT
                          # WILL COME IN A FUTURE UPDATE, OK

# The fontsize depends on this
fontsize = str(int(20*sf))

canvasheight = (canvaswidth*(1.0 / 1.8))  # For showing the various results on the figure, 
										   # I lock everything to a 1.8:1 aspect ratio

baseplotwidth = int(1000*sf)
BAGPIPESbaseplotwidth = int(800*sf)
textsizevalue = int(20*sf)
thumbnailsize = 1.5*sf

toprow_y = 1020
bottomrow_y = 1060

# However, if we get a lot of thumbnails, I might want to change things a bit
if ((number_images > 18) & (number_images <= 32)):
	toprow_y = 1020
	bottomrow_y = 1060
	thumbnailsize = 1.2*sf

# These do not change depending on the number of images we have.
eazy_positionx, eazy_positiony = 500*sf, 245*sf
eazytext_positionx, eazytext_positiony = 820*sf, 10*sf
beagle_positionx, beagle_positiony = 1500*sf, 350*sf
beagletext_positionx, beagletext_positiony = 1780*sf, 10*sf#1300*sf, 70*sf
bagpipes_positionx, bagpipes_positiony = 1490*sf, 330*sf#1490*sf, 275*sf
objectID_positionx, objectID_positiony = 20*sf, 10*sf#1300*sf, 70*sf

# Open up the photometric catalog
fitsinput = fits.open(input_photometry)
ID_values = fitsinput[1].data['ID'].astype('int')
RA_values = fitsinput[1].data['RA']
DEC_values = fitsinput[1].data['DEC']
number_objects = len(ID_values)

image_flux_value_cat = np.zeros([number_objects, number_image_filters])
image_flux_value_err_cat = np.zeros([number_objects, number_image_filters])
SNR_values = np.zeros([number_objects, number_image_filters])

for j in range(0, number_image_filters):
	try:
		image_flux_value_cat[:,j] = fitsinput[1].data[all_images_filter_name[j]]
		image_flux_value_err_cat[:,j] = fitsinput[1].data[all_images_filter_name[j]+'_err']
		SNR_values[:,j] = image_flux_value_cat[:,j] / image_flux_value_err_cat[:,j]

	except:		
		#if (all_images_filter_name[j] == 'SEGMAP'):
		SNR_values[:,j] = -9999
#		
#	else:
#		image_flux_value_cat[:,j] = fitsinput[1].data[all_images_filter_name[j]]
#		image_flux_value_err_cat[:,j] = fitsinput[1].data[all_images_filter_name[j]+'_err']
#		SNR_values[:,j] = image_flux_value_cat[:,j] / image_flux_value_err_cat[:,j]

number_input_objects = len(ID_values)
ID_iterator = 0

if (EAZY_results_file_exists):
	if (EAZY_results_file.startswith('http')):
		response = requests.get(EAZY_results_file, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		eazy_fits_file = BytesIO(response.content)
	else:
		eazy_fits_file = EAZY_results_file
	eazy_results_fits = fits.open(eazy_fits_file)
	eazy_results_IDs = eazy_results_fits[1].data['ID'].astype('int')
	eazy_results_zpeak = eazy_results_fits[1].data['z_peak']
	eazy_results_za = eazy_results_fits[1].data['z_a']
	eazy_results_zl68 = eazy_results_fits[1].data['l68']
	eazy_results_zu68 = eazy_results_fits[1].data['u68']
	#eazy_results_zl95 = eazy_results_fits[1].data['l95']
	#eazy_results_zu95 = eazy_results_fits[1].data['u95']


if (BEAGLE_results_file_exists):
	if (BEAGLE_results_file.startswith('http')):
		response = requests.get(BEAGLE_results_file, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		beagle_fits_file = BytesIO(response.content)
	else:
		beagle_fits_file = BEAGLE_results_file
		
	beagle_results_fits = fits.open(beagle_fits_file)
	beagle_ID_str = beagle_results_fits[1].data['ID']
	beagle_results_IDs = np.zeros(len(beagle_ID_str), dtype = 'int')
	for j in range(0, len(beagle_ID_str)):
		beagle_results_IDs[j] = int(beagle_ID_str[j])

	beagle_results_zavg = beagle_results_fits[1].data['redshift_beagle_mean']
	beagle_results_redshift_1 = beagle_results_fits[1].data['redshift_beagle_1']
	beagle_results_redshift_err_1 = beagle_results_fits[1].data['redshift_beagle_err_1']
	beagle_results_redshift_2 = beagle_results_fits[1].data['redshift_beagle_2']
	beagle_results_redshift_err_2 = beagle_results_fits[1].data['redshift_beagle_err_2']
	beagle_results_zl68 = beagle_results_fits[1].data['redshift_68.0_low']
	beagle_results_zu68 = beagle_results_fits[1].data['redshift_68.0_up']
	beagle_results_Pzgt2p0 = beagle_results_fits[1].data['redshift_p_gt_2.0']
	beagle_results_Pzgt4p0 = beagle_results_fits[1].data['redshift_p_gt_4.0']
	beagle_results_Pzgt6p0 = beagle_results_fits[1].data['redshift_p_gt_6.0']

if (NN_results_file_exists):
	if (NN_results_file.startswith('http')):
		response = requests.get(NN_results_file, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		NN_fits_file = BytesIO(response.content)
	else:
		NN_fits_file = NN_results_file

	NN_results_fits = fits.open(NN_fits_file)
	NN_results_IDs = NN_results_fits[1].data['ID_PHOTOMETRIC'].astype('int')
	NN_results_zpred = NN_results_fits[1].data['pred_z']
	NN_results_zspec = NN_results_fits[1].data['true_z']
	NN_results_use = NN_results_fits[1].data['USE']

if (color_selection_results_file_exists):
	if (color_selection_results_file.startswith('http')):
		response = requests.get(color_selection_results_file, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		color_selection_file = BytesIO(response.content)
	else:
		color_selection_file = color_selection_results_file

	color_selection_fits = fits.open(color_selection_file)
	color_selection_IDs = color_selection_fits[1].data['ID'].astype('int')
	color_selection_F090W_dropouts = color_selection_fits[1].data['NRC_F090W_Dropout_SNR3.0']
	color_selection_F115W_dropouts = color_selection_fits[1].data['NRC_F115W_Dropout_SNR3.0']
	color_selection_F150W_dropouts = color_selection_fits[1].data['NRC_F150W_Dropout_SNR3.0']

if (BAGPIPES_results_file_exists):
	if (BAGPIPES_results_file.startswith('http')):
		response = requests.get(BAGPIPES_results_file, auth=HTTPBasicAuth(fenrir_username, fenrir_password))
		BAGPIPES_fits_file = BytesIO(response.content)
	else:
		BAGPIPES_fits_file = BAGPIPES_results_file

	BAGPIPES_results_fits = fits.open(BAGPIPES_fits_file)
	BAGPIPES_results_IDs = BAGPIPES_results_fits[1].data['ID'].astype('int')
	BAGPIPES_results_zphot = BAGPIPES_results_fits[1].data['redshift_mean']

	
# Decide whether or not the user requested an ID number or an id number list
if (args.id_number):
	ID_list = ID_values
	ID_list_indices = np.arange(len(ID_values), dtype = int)
	current_id = int(args.id_number)
	current_index = np.where(ID_values == current_id)[0][0]
	ID_iterator = current_index
	if (args.id_number_list):
		print("You can't specify an individual ID and a list, ignoring the list.")
	if (args.idarglist):
		print("You can't specify an individual ID and a list, ignoring the list.")
	
if not (args.id_number):
	if not (args.id_number_list):
		ID_list = ID_values
		ID_list_indices = np.arange(len(ID_values), dtype = int)
		current_index = ID_list_indices[ID_iterator]
		current_id = ID_list[current_index]

	if (args.id_number_list):
		ID_input_file = np.loadtxt(args.id_number_list)
		if (len(ID_input_file.shape) > 1):
			ID_numbers_to_view = ID_input_file[:,0].astype(int)
		else:
			ID_numbers_to_view = ID_input_file.astype(int)
		number_id_list = len(ID_numbers_to_view)
	
		# Set up index array for 
		ID_list_indices = np.zeros(number_id_list, dtype = int)
		for x in range(0, number_id_list):
			ID_list_indices[x] = np.where(ID_values == ID_numbers_to_view[x])[0]
	
		ID_list = ID_numbers_to_view
		current_index = ID_list_indices[ID_iterator]
		current_id = ID_values[current_index]

	if (args.idarglist):
		ID_numbers_to_view = np.array(ast.literal_eval(args.idarglist))
	
		number_id_list = len(ID_numbers_to_view)
	
		# Set up index array for 
		ID_list_indices = np.zeros(number_id_list, dtype = int)
		for x in range(0, number_id_list):
			#print(np.where(ID_values == ID_numbers_to_view[x])[0])
			#print(len(np.where(ID_values == ID_numbers_to_view[x])[0]))
			if (len(np.where(ID_values == ID_numbers_to_view[x])[0]) > 0):
				ID_list_indices[x] = np.where(ID_values == ID_numbers_to_view[x])[0]
			else:
				sys.exit("Object "+str(ID_numbers_to_view[x])+" does not appear in this catalog. Exiting.")
					
		ID_list = ID_numbers_to_view
		current_index = ID_list_indices[ID_iterator]
		current_id = ID_values[current_index]


# Create the notes array
notes_values = np.array([''], dtype = 'object')
for x in range(0, number_input_objects-1):
	notes_values = np.append(notes_values, ['']) 

# Create the flag arrays
highZflag_array = np.zeros(number_input_objects, dtype = 'int')
badfitflag_array = np.zeros(number_input_objects, dtype = 'int')
baddataflag_array = np.zeros(number_input_objects, dtype = 'int')

# So, now, there are three arrays:
#   ID_list (which is the list of the ID values that will be viewed)
#   ID_list_indices (which is the indices for the ID values that will be viewed)

# There is also a:
#   current_id - the current ID number being displayed
#   current_index - the current index in the full photometric array 
#   ID_iterator - an iterator that keeps track of the index of the ID_list_indices array
#                 is currently being shown

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Now, everything is set up, so let's start creating the GUI

# Start by creating the GUI as root
root=Tk()
root.wm_title("JADESView")

# Create the canvas 
canvas=Canvas(root, height=canvasheight, width=canvaswidth, bg="#ffffff")

# Plot the EAZY SED
#image = Image.open(EAZY_files+str(current_id)+"_EAZY_SED.png")
image = getEAZYimage(current_id)

# Put the object label 
object_label = Label(root, text="Object "+str(current_id), font = "Helvetica "+str(int(textsizevalue*1.5)), fg="black", bg="white")
object_label.place(x=objectID_positionx, y = objectID_positiony)

# Crop out the thumbnails
if (EAZY_plots_exist == True):
	image = cropEAZY(image)
	photo = resizeimage(image)
	item4 = canvas.create_image(eazy_positionx, eazy_positiony, image=photo)
	Label(root, text="EAZY FIT", fg='black', bg='white', font=('helvetica', int(textsizevalue*1.5))).place(x=eazytext_positionx, y = eazytext_positiony)
else:
	item4 = None

# Plot the BEAGLE SED
#new_image = Image.open(BEAGLE_files+str(current_id)+"_BEAGLE_SED.png")
if (BEAGLE_plots_exist == True):
	new_image = getBEAGLEimage(current_id)
	new_photo = resizeimage(new_image)
	item5 = canvas.create_image(beagle_positionx, beagle_positiony, image=new_photo)
	otherfit_label = Label(root, text="BEAGLE FIT ", font = "Helvetica "+str(int(textsizevalue*1.5)), fg="black", bg="white")
	otherfit_label.place(x=beagletext_positionx, y = beagletext_positiony)

else:
	item5 = None

canvas.pack(side = TOP, expand=True, fill=BOTH)

# Plot the thumbnails
fig_photo_objects = np.empty(0, dtype = 'object')
fig_photo_objects = create_thumbnails(canvas, fig_photo_objects, current_id, current_index, defaultstretch)

# # # # # # # # # # # # # # 
# Place Labels with Redshift 

# #711c91, #ea00d9, #0abdc6, #133e7c, #091833

# A delineation line. 
redshift_separator = canvas.create_rectangle(1100*sf, (toprow_y-320.0)*sf, 1940*sf, (toprow_y-310.0)*sf, outline="#0abdc6", fill="#0abdc6", tags="separator")


# Make the EAZY redshift label
if (EAZY_results_file_exists == True):
	eazy_z_peak = getfile_value(current_id, eazy_results_IDs, eazy_results_zpeak, 4)
	eazy_z_a = getfile_value(current_id, eazy_results_IDs, eazy_results_za, 4)
	eazy_l68 = getfile_value(current_id, eazy_results_IDs, eazy_results_zl68, 4)
	eazy_u68 = getfile_value(current_id, eazy_results_IDs, eazy_results_zu68, 4)

	eazy_label_zpeak = Label(root, text="z_EAZY, peak = "+str(eazy_z_peak)+" ("+str(eazy_l68)+" - "+str(eazy_u68)+")", font = "Helvetica "+str(textsizevalue), fg="#133e7c", bg="#ffffff")
	eazy_label_zpeak.place(x=1100*sf, y = (toprow_y-290.0)*sf)
	eazy_label_za = Label(root, text="z_EAZY, a = "+str(eazy_z_a), font = "Helvetica "+str(textsizevalue), fg="#133e7c", bg="#ffffff")
	eazy_label_za.place(x=1100*sf, y = (toprow_y-250.0)*sf)


# Make the BEAGLE redshift labels
if (BEAGLE_results_file_exists == True):
	beagle_z_avg = getfile_value(current_id, beagle_results_IDs, beagle_results_zavg, 4)
	beagle_z_l68 = getfile_value(current_id, beagle_results_IDs, beagle_results_zl68, 4)
	beagle_z_u68 = getfile_value(current_id, beagle_results_IDs, beagle_results_zu68, 4)
	
	beagle_label = Label(root, text="z_BEAGLE,avg = "+str(beagle_z_avg)+" ("+str(beagle_z_l68)+" - "+str(beagle_z_u68)+")", font = "Helvetica "+str(textsizevalue), fg="#711c91", bg="#ffffff")
	beagle_label.place(x=1100*sf, y = (toprow_y-210.0)*sf)
	
	beagle_z_1 = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_1, 4)
	beagle_z_1_err = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_err_1, 4)
	beagle_z1_label = Label(root, text="z_BEAGLE,1 = "+str(beagle_z_1)+" +/- "+str(beagle_z_1_err), font = "Helvetica "+str(textsizevalue), fg="#711c91", bg="#ffffff")
	beagle_z1_label.place(x=1100*sf, y = (toprow_y-170.0)*sf)
	
	beagle_z_2 = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_2, 4)
	beagle_z_2_err = getfile_value(current_id, beagle_results_IDs, beagle_results_redshift_err_2, 4)
	beagle_z2_label = Label(root, text="z_BEAGLE,2 = "+str(beagle_z_2)+" +/- "+str(beagle_z_2_err), font = "Helvetica "+str(textsizevalue), fg="#711c91", bg="#ffffff")
	beagle_z2_label.place(x=1100*sf, y = (toprow_y-130.0)*sf)

	beagle_Pzgt2p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt2p0, 2)
	beagle_Pzgt4p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt4p0, 2)
	beagle_Pzgt6p0 = getfile_value(current_id, beagle_results_IDs, beagle_results_Pzgt6p0, 2)
	beagle_prob_label = Label(root, text="P(z > 2) = "+str(beagle_Pzgt2p0)+", P(z > 4) = "+str(beagle_Pzgt4p0)+", P(z > 4) = "+str(beagle_Pzgt6p0), font = "Helvetica "+str(textsizevalue), fg="#711c91", bg="#ffffff")
	beagle_prob_label.place(x=1100*sf, y = (toprow_y-90.0)*sf)

#NN_z = 5.000
if (NN_results_file_exists):
	NN_zpred = getfile_value(current_id, NN_results_IDs, NN_results_zpred, 4)
	NN_zspec = getfile_value(current_id, NN_results_IDs, NN_results_zspec, 4)
	NN_use = getfile_true_or_false(current_id, NN_results_IDs, NN_results_use)
	
	if (NN_use == True):
		nn_label = Label(root, text="z_NN = "+str(NN_zpred), font = "Helvetica "+str(textsizevalue), fg="#091833", bg="#ffffff")
	if (NN_use == False):
		nn_label = Label(root, text="z_NN = "+str(NN_zpred)+" (USE = F)", font = "Helvetica "+str(textsizevalue), fg="grey", bg="#ffffff")
	#nn_label.place(x=1800*sf, y = (toprow_y-210.0)*sf)
	nn_label.place(x=1740*sf, y = (toprow_y-290.0)*sf)
	if (use_zspec == True):
		nn_label_zspec = Label(root, text="z_spec = "+str(NN_zspec), font = "Helvetica "+str(textsizevalue)+" bold", fg="red", bg="#ffffff")
		nn_label_zspec.place(x=1740*sf, y = (toprow_y-250.0)*sf)

if (color_selection_results_file_exists):
	is_F090W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F090W_dropouts)
	is_F115W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F115W_dropouts)
	is_F150W_dropout = getfile_true_or_false(current_id, color_selection_IDs, color_selection_F150W_dropouts)
	
	if(is_F090W_dropout):
		color_selection_label = Label(root, text="F090W Dropout", font = "Helvetica "+str(textsizevalue), fg="#091833", bg="#ffffff")
		color_selection_label.place(x=1760*sf, y = (toprow_y-90.0)*sf)
	
	elif(is_F115W_dropout):
		color_selection_label = Label(root, text="F115W Dropout", font = "Helvetica "+str(textsizevalue), fg="#091833", bg="#ffffff")
		color_selection_label.place(x=1760*sf, y = (toprow_y-90.0)*sf)

	elif(is_F150W_dropout):
		color_selection_label = Label(root, text="F150W Dropout", font = "Helvetica "+str(textsizevalue), fg="#091833", bg="#ffffff")
		color_selection_label.place(x=1760*sf, y = (toprow_y-90.0)*sf)

	else:
		color_selection_label = Label(root, text=" ", font = "Helvetica "+str(textsizevalue), fg="#091833", bg="#ffffff")
		color_selection_label.place(x=1760*sf, y = (toprow_y-90.0)*sf)

if (BAGPIPES_results_file_exists):
	BAGPIPES_zpred = getfile_value(current_id-1, BAGPIPES_results_IDs, BAGPIPES_results_zphot, 4)

	bagpipes_label = Label(root, text="z_BAGPIPES = "+str(BAGPIPES_zpred), font = "Helvetica "+str(textsizevalue), fg="grey", bg="#ffffff")
	bagpipes_label.place(x=1740*sf, y = (toprow_y-150.0)*sf)


#SEDz_z = 5.000
#Label(root, text="z_SEDz = ", font = "Helvetica 20", fg="#000000", bg="#ffffff").place(x=1100*sf, y = (toprow_y-210.0)*sf)

#S3_z = 5.000
#Label(root, text="z_S3 = ", font = "Helvetica 20", fg="#000000", bg="#ffffff").place(x=1100*sf, y = (toprow_y-170.0)*sf)


# # # # # # # # # # # #
# Flag Object Buttons

# Create the Bad Fit Flag
btn1 = Button(root, text = 'Bad Fit', bd = '5', command = badfit)
btn1.config(height = int(2*sf), width = int(13*sf), fg='black', highlightbackground='white', font=('helvetica', textsizevalue), padx = 3, pady = 3)
btn1.place(x = 600*sf, y = (toprow_y-20)*sf)

# Create the High Redshift Flag Button
btn1 = Button(root, text = 'High Redshift', bd = '5', command = highz)
btn1.config(height = int(2*sf), width = int(11*sf), fg='red', highlightbackground='white', font=('helvetica', textsizevalue), padx = 20, pady = 3)
btn1.place(x = 793*sf, y = (toprow_y-20)*sf)

# Create the Bad Data Flag
btn1 = Button(root, text = 'Bad Data', bd = '5', command = baddata)
btn1.config(height = int(2*sf), width = int(13*sf), fg='black', highlightbackground='white', font=('helvetica', textsizevalue), padx = 3, pady = 3)
btn1.place(x = 1000*sf, y = (toprow_y-20)*sf)


# # # # # # # # # # # #
# Move to New Object Buttons


# Create the Previous Object Button
btn3 = Button(root, text = 'Previous Object', bd = '5', command = previousobject)  
btn3.config(height = int(2*sf), width = int(20*sf), fg='black', highlightbackground='white', font=('helvetica', textsizevalue), padx = 3, pady = 3)
btn3.place(x = 600*sf, y = bottomrow_y*sf)


# Create the Next Object Button
btn2 = Button(root, text = 'Next Object', bd = '5', command = nextobject)
btn2.config(height = int(2*sf), width = int(20*sf), fg='black', highlightbackground='white', font=('helvetica', textsizevalue), padx = 3, pady = 3)
btn2.place(x = 917*sf, y = bottomrow_y*sf)

if ((args.id_number_list is None) & (args.idarglist is None)):
	# Create the Object Entry Field and Button
	Label(root, text="Display Object: ", font=('helvetica', textsizevalue), fg="#000000", bg="#ffffff").place(x=1220*sf, y = (bottomrow_y+10.0)*sf)
	e1 = Entry(root, width = int(5*sf), font=('helvetica', textsizevalue), fg="#000000", bg="#ffffff")
	e1.place(x = 1370*sf, y = (bottomrow_y+6.0)*sf)

	btn9 = Button(root, text = 'Go', bd = '5', command = gotoobject)  
	btn9.config(height = int(1*sf), width = int(4*sf), fg='blue', highlightbackground='white', font=('helvetica', textsizevalue))
	#btn2.pack(side = 'bottom')
	btn9.place(x = 1470*sf, y = (bottomrow_y+9.0)*sf)


# # # # # # # # # # # #
# Quit Button

btn4 = Button(root, text = 'Quit', bd = '5', command = save_destroy)  
btn4.config(height = int(2*sf), width = int(10*sf), fg='red', highlightbackground='white', font=('helvetica', textsizevalue))
btn4.place(x = 1850*sf, y = (bottomrow_y+10.0)*sf)

# # # # # # # # # # # #
# Save Canvas Button

# save_canvas_imagegrab()
btn4 = Button(root, text = 'Save Canvas', bd = '5', command = save_canvas)  
btn4.config(height = int(2*sf), width = int(15*sf), fg='black', highlightbackground='white', font=('helvetica', textsizevalue))
btn4.place(x = 1645*sf, y = (bottomrow_y+10.0)*sf)

# # # # # # # # # # # #
# Image Stretch Buttons

Label(root, text="Stretch", font = ('helvetica', int(20*sf)), fg="#000000", bg='#ffffff').place(x=20*sf, y = (bottomrow_y+ 10.0)*sf)

# Create the LinearStretch Button
btn5 = Button(root, text = 'Linear', bd = '5', command = linearstretch)  
if (defaultstretch == 'LinearStretch'):
	btn5.config(height = int(2*sf), width = int(10*sf), fg='black', highlightbackground='white', font=('helvetica bold', textsizevalue))
else:
	btn5.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))
btn5.place(x = 100*sf, y = (bottomrow_y+10.0)*sf)


# Create the LogStretch Button
btn6 = Button(root, text = 'Log', bd = '5', command = logstretch)  
if (defaultstretch == 'LogStretch'):
	btn6.config(height = int(2*sf), width = int(10*sf), fg='black', highlightbackground='white', font=('helvetica bold', textsizevalue))
else:
	btn6.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))
btn6.place(x = 250*sf, y = (bottomrow_y+10.0)*sf)


# Create the Asinh Button
btn7 = Button(root, text = 'Asinh', bd = '5', command = asinhstretch)  
if (defaultstretch == 'AsinhStretch'):
	btn7.config(height = int(2*sf), width = int(10*sf), fg='black', highlightbackground='white', font=('helvetica bold', textsizevalue))
else:
	btn7.config(height = int(2*sf), width = int(10*sf), fg='grey', highlightbackground='white', font=('helvetica', textsizevalue))
btn7.place(x = 400*sf, y = (bottomrow_y+10.0)*sf)

# # # # # # # # #  
# Notes / RA/DEC

# Create the Notes Field
Label(root, text="Notes", font = "Helvetica 20", fg="#000000", bg="#ffffff").place(x=1220*sf, y = (toprow_y+5.0)*sf)
e2 = Entry(root, width = int(50*sf), font=('helvetica', textsizevalue), fg="#000000", bg="#ffffff")
e2.place(x = 1300*sf, y = toprow_y*sf)
e2.insert(0, notes_values[current_index])

# Create the RA and DEC size field 
Label(root, text="RA/DEC size", font=('helvetica', textsizevalue), fg="#000000", bg="#ffffff").place(x=20*sf, y = (toprow_y+15.0)*sf)
e3 = Entry(root, width = int(10*sf), font=('helvetica', textsizevalue), fg="#000000", bg="#ffffff")
e3.place(x = 150*sf, y = (toprow_y+10.0)*sf)
e3.insert(0, str(ra_dec_size_value))
Label(root, text="arcseconds", font=('helvetica', textsizevalue), fg="#000000", bg="#ffffff").place(x=280*sf, y = (toprow_y+15.0)*sf)
btn8 = Button(root, text = 'Change', bd = '5', command = changeradecsize)  
btn8.config(height = 1, width = int(10*sf), fg='blue', highlightbackground = 'white', font=('helvetica', textsizevalue))
btn8.place(x = 400*sf, y = (toprow_y+13.0)*sf)

btn12 = Button(root, text = 'Crosshair', bd = '5', command = togglecrosshair)  
btn12.config(height = 1, width = int(10*sf), fg='blue', highlightbackground = 'white', font=('helvetica', textsizevalue))
btn12.place(x = 400*sf, y = (toprow_y-25.0)*sf)


# # # # # # # # #  
# Alternate Fits 

# The button to plot the BEAGLE results
btn13 = Button(root, text = 'BEAGLE', bd = '5', command = plotbeagle)  
btn13.config(height = 1, width = int(10*sf), fg='blue', highlightbackground = 'white', font=('helvetica bold', textsizevalue))
btn13.place(x = 1300*sf, y = (toprow_y-50.0)*sf)

# The button to plot the BAGPIPES results
if (BAGPIPES_plots_exist == True):
	btn10 = Button(root, text = 'BAGPIPES', bd = '5', command = plotbagpipes)  
	btn10.config(height = 1, width = int(10*sf), fg='blue', highlightbackground = 'white', font=('helvetica', textsizevalue))
	btn10.place(x = 1450*sf, y = (toprow_y-50.0)*sf)

# The button to plot the SEDz results
#btn11 = Button(root, text = 'SEDz', bd = '5', command = plotsedz)  
#btn11.config(height = 1, width = int(10*sf), fg='blue', highlightbackground = 'white', font=('helvetica', textsizevalue))
#btn11.place(x = 1450*sf, y = (toprow_y-50.0)*sf)

root.mainloop()