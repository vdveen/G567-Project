#Importing needed modules & packages
import arcpy
import datetime
import numpy as np
import matplotlib.pyplot as plt
import sys

#1. Get folder location
#2. Get name of output
#3. Get day to analyse

#Get the location of the original data and retrieve the folder string
inputfile = arcpy.GetParameterAsText(0)
folder = inputfile[:-33]

#Create cursor to go trough data
fields = ['starttime', 'start station latitude', 'start station longitude',\
 'end station latitude', 'end station longitude', 'stoptime', 'tripduration',\
 'gender']
cursor = arcpy.da.SearchCursor(inputfile, fields)

arcpy.AddMessage(folder)
#Create dataset to put fc in
try:
    arcpy.CreateFileGDB_management(folder, 'Output.gdb')
except:
    arcpy.AddMessage('GDB already in place')

#Set the dataset as workspace
geodb = folder +'Output.gdb'
arcpy.env.workspace = geodb

#Define unique path name for the line map
arcpy.env.overwriteOutput = True
filename = 'Citibike'
output = geodb + '\\' + filename
arcpy.AddMessage('Unique name: ' + output)

#Create Feature Class to populate
arcpy.CreateFeatureclass_management(geodb, filename, \
'POLYLINE', None, 'DISABLED', 'DISABLED', 4326)

#Add fields to FC with the start and endtime and the date
arcpy.AddField_management(output, 'StartTime', 'DATE')
arcpy.AddField_management(output, 'EndTime', 'DATE')

#Create insertcursor for populating the FC
fields2 = ['SHAPE@', 'StartTime', 'EndTime']
inscursor = arcpy.da.InsertCursor(output, fields2)

#Set (default) values of variables before starting loop
startday = arcpy.GetParameter(1)
endday = startday + 1
count = 0
tripduration = []
totallength = []
gender = []

for row in cursor:
    #Get the start time from the source data
    values = row[0], #without the comma this line throws a getitem error, wtf
    starttime = values[0]

    if starttime.day == startday:
        #Get the coordinates of the start and end
        startLat = row[1]
        startLon = row[2]
        endLat = row[3]
        endLon = row[4]

        #Make two points in Arcpy
        start = arcpy.Point(startLon,startLat,None,None,0)
        end = arcpy.Point(endLon,endLat,None,None,1)

        #Put them in an array
        triplineArray = arcpy.Array([start,end])
        sr = arcpy.SpatialReference(4326)

        #Create line between the two
        tripline = arcpy.Polyline(triplineArray, sr)

        #Store length in a list
        length = tripline.getLength('GEODESIC')
        totallength.append(length)

        #Get the end time from the source data
        endvalues = row[0],
        endtime = values[0]

        #Put point and hour in the FC with the InsertCursor
        newRow = [tripline, starttime, endtime]
        inscursor.insertRow(newRow)

        #Statistics
        trip = row[6]
        tripduration.append(trip)
        gendervalue = row[7]
        gender.append(gendervalue)

        #Keep track of amount of features done
        count += 1
        if count % 1000 == 0:
            arcpy.AddMessage('Trips Processed: ' + str(count))
            arcpy.AddMessage('Currently at: ' + str(starttime))

    #End at given day
    elif starttime.day == endday:
        break

#Statistical analysis function
def statanalysis(self, num = 0):
    mean = np.mean(self)
    std = np.std(self)
    minmax = (0, 5000)
    bins = 50

    #Generate plot based on what needs to be analysed
    #First, make plot with plt.hist, then add title and labels
    #and make sure the path is set correctly for the file
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

    #Give the image an unique name
    name = folder + 'Statistics' + path + '.png'

    #Save the image
    plt.savefig(name, bbox_inches='tight')
    plt.close()

statanalysis(tripduration, 1)
statanalysis(totallength, 2)
statanalysis(gender, 3)

#Put the results of the insert cursor in a layer file
arcpy.MakeFeatureLayer_management('/Citibike','temp')
outputname = folder + 'Citibike.lyr'
arcpy.AddMessage(outputname)
arcpy.SaveToLayerFile_management('temp', outputname, 'ABSOLUTE')

#Print messages
print arcpy.GetMessages()

#Clean up the mess
del cursor, inscursor, row, outputname

print arcpy.GetMessages()

print 'Done now'
