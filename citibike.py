#-------------------------------------------------------------------------------
# Name:        citibike.py
# Purpose:     To create a layer file and a statistical analysis of  a day
#              of Citibke open data.
#
# Author:      A. van der Veen
#
# Created:     10/11/2014
# Copyright:   (c) vdveen 2014
#-------------------------------------------------------------------------------

#Importing necessary modules & packages
import arcpy
import datetime
import numpy as np
import matplotlib.pyplot as plt
from sys import exit

#Get the location of the Citibike data
inputfile = arcpy.GetParameterAsText(0)

#Remove the last part of the input file string to retrieve the folder it's in
folder = inputfile[:-33]

#Check if the inputs are acceptable
if not inputfile.endswith('Bike trip data.csv'):
    arcpy.AddError('This data is not original Citibike trip data.')
    exit()

startday = arcpy.GetParameter(1)
if startday > 30 or startday < 1:
    arcpy.AddError('The day of the month is not between 1 and 30')
    exit()

#Create cursor to go trough data
try:
    fields = ['starttime', 'start station latitude', 'start station longitude',\
 'end station latitude', 'end station longitude', 'stoptime', 'tripduration',\
 'gender']
    cursor = arcpy.da.SearchCursor(inputfile, fields)
except:
    msg = "Couldn't search data fields in " + folder
    arcpy.AddError(msg)
    exit()

#Create dataset to put fc in, don't create one if there is already one there
try:
    arcpy.CreateFileGDB_management(folder, 'Output.gdb')
except:
    arcpy.AddWarning('No new geodatabase created.')

#Set the (newly created) GDB as workspace
geodb = folder +'Output.gdb'
arcpy.env.workspace = geodb

#Define path name for the feature class
filename = 'Citibike'
output = geodb + '\\' + filename
arcpy.AddMessage('Feature Class: ' + output)

#Create Feature Class to populate
arcpy.env.overwriteOutput = True
arcpy.CreateFeatureclass_management(geodb, filename, \
'POLYLINE', None, 'DISABLED', 'DISABLED', 4326)

#Add fields to FC with the start and endtime and the date
arcpy.AddField_management(output, 'StartTime', 'DATE')
arcpy.AddField_management(output, 'EndTime', 'DATE')

#Create insertcursor for populating the FC
fields2 = ['SHAPE@', 'StartTime', 'EndTime']
inscursor = arcpy.da.InsertCursor(output, fields2)

#Set (default) values of variables before starting loop
endday = startday + 1
count = 0
tripduration = []
totallength = []
gender = []


for row in cursor:
    #Get the start time from the source data
    values = row[0], #without the comma this line throws a getitem error, wtf
    starttime = values[0]

    #Start reading the rows when the row day equals the given start day
    if starttime.day == startday:
        #Get the coordinates of the start and end
        startLat = row[1]
        startLon = row[2]
        endLat = row[3]
        endLon = row[4]

        #Make two points out of them in Arcpy
        start = arcpy.Point(startLon,startLat,None,None,0)
        end = arcpy.Point(endLon,endLat,None,None,1)

        #Put these two points in an array
        triplineArray = arcpy.Array([start,end])
        sr = arcpy.SpatialReference(4326)

        #Create a line between the two
        tripline = arcpy.Polyline(triplineArray, sr)

        #Store the line's length in a list
        length = tripline.getLength('GEODESIC')
        totallength.append(length)

        #Get the end time from the source data
        endvalues = row[0],
        endtime = values[0]

        #Put point and hour in the FC with the InsertCursor
        newRow = [tripline, starttime, endtime]
        inscursor.insertRow(newRow)

        #Append the duration and gender statistics
        trip = row[6]
        tripduration.append(trip)
        gendervalue = row[7]
        gender.append(gendervalue)

        #Keep track of amount of features done
        count += 1
        if count % 1000 == 0:
            #Every 1000 rows, display progress
            arcpy.AddMessage('Trips Processed: ' + str(count))
            arcpy.AddMessage('Currently at: ' + str(starttime))

    #End a day later than the given start day
    elif starttime.day == endday:
        break

#Put the results of the insert cursor in a new layer file
arcpy.MakeFeatureLayer_management('/Citibike','temp')
outputname = folder + 'Citibike.lyr'
arcpy.AddMessage(outputname)
arcpy.SaveToLayerFile_management('temp', outputname, 'ABSOLUTE')

#Function to analyse the duration, length and gender lists
def statanalysis(self, num = 0):
    #Calculate some standard statistics
    mean = np.mean(self)
    std = np.std(self)
    minmax = (0, 5000)
    bins = 50

    #This part generates the plots based on what needs to be analysed
    #First, it makes plot with plt.hist, then adds a title and labels
    #and makes sure the path is set correctly for the file
    if num == 1:
        plot = plt.hist(self, bins, minmax, color = 'grey')
        plt.title('Trip Duration Histogram')
        plt.xlabel('Seconds')
        path = 'Trip'
    elif num == 2:
        plot = plt.hist(self, bins, minmax, color = 'grey')
        plt.title('Total Length Histogram')
        plt.xlabel('Length')
        path = 'Length'
    elif num == 3:
        bins = [0, 1, 2, 3]
        plot = plt.hist(self, bins, color = 'grey')
        plt.title('Gender Histogram')
        plt.xlabel('1 = Male, 2 = Female')
        path = 'Gender'

    #Add mean and median to image
    text = 'Mean: ' + str(int(mean)) + ' Std: ' + str(int(std))
    plt.text(0.05, 0.95, text)

    #Give Y label
    plt.ylabel('Frequency')

    #Make sure ylabel isn't clipping
    plt.subplots_adjust(left=0.15)

    #Give the image an unique name based on the path variable from the if statement
    name = folder + 'Statistics' + path + '.png'

    #Save and close the image
    plt.savefig(name, bbox_inches='tight')
    plt.close()

#Go through the analysis three times, for the trip duration, the length
#and the gender of the biker
statanalysis(tripduration, 1)
statanalysis(totallength, 2)
statanalysis(gender, 3)

#Print messages
msg = 'Created layer file, geodatabase and statistical results are stored \
at ' + folder
print arcpy.AddWarning(msg)
print arcpy.GetMessages()

#Clean up the mess
del cursor, inscursor, row, outputname

