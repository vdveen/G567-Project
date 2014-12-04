#Testing out cursors

import arcpy
import datetime
import numpy as np
import matplotlib.pyplot as plt
from sys import exit

#Retrieve file and create update cursor from it
InputFile = 'data/2014-07 - Citi Bike trip data.csv'
fields = ['starttime', 'start station latitude', 'start station longitude',\
 'end station latitude', 'end station longitude', 'stoptime', 'tripduration',\
 'gender']
cursor = arcpy.da.SearchCursor(InputFile, fields)

#Create dataset to put fc in
try:
    arcpy.CreateFileGDB_management("Data", "Output.gdb")
except:
    print 'GDB already in place'

#Set the dataset as workspace
arcpy.env.workspace = 'Data/Output.gdb'

#Define unique path name for the line map
linemap = arcpy.CreateUniqueName('linemap')
linemap = linemap[16:]
output = 'Data/Output.gdb/' + linemap
print 'Unique name: ' + output

#Create Feature Class to populate
arcpy.CreateFeatureclass_management('Data/Output.gdb', linemap, \
'POLYLINE', None, 'DISABLED', 'DISABLED', 4326)

#Add fields to FC with the start and endtime and the date
arcpy.AddField_management(output, 'StartTime', 'DATE')
arcpy.AddField_management(output, 'EndTime', 'DATE')

#Create insertcursor for populating the FC
fields2 = ['SHAPE@', 'StartTime', 'EndTime']
inscursor = arcpy.da.InsertCursor(output, fields2)

startday = 3
endday = 4

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
            print count

    #End at given day
    elif starttime.day == endday:
        break

#Statistical analysis
def statanalysis(self, num = 0):
    mean = np.mean(self)
    print mean
    std = np.std(self)
    print std
    minmax = (0, 5000)
    bins = 50

    #Generate plot based on what needs to be analysed
    #First, make plot with plt.hist, then add title and labels
    #and make sure the path is set correctly for the file
    if num == 1:
        plot = plt.hist(self, bins, minmax, color = 'blue')
        plt.title('Trip Duration Histogram')
        plt.xlabel('Seconds')
        path = 'Trip'
    elif num == 2:
        plot = plt.hist(self, bins, minmax, color = 'blue')
        plt.title('Total Length Histogram')
        plt.xlabel('Length')
        path = 'Length'
    elif num == 3:
        bins = [0, 1, 2, 3]
        plot = plt.hist(self, bins, color = 'blue')
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
    name = linemap + 'stat' + path + '.png'

    #Save the image
    plt.savefig(name, bbox_inches='tight')
    plt.close()

statanalysis(tripduration, 1)
statanalysis(totallength, 2)
statanalysis(gender, 3)


#Put the results of the insert cursor in a layer file
arcpy.MakeFeatureLayer_management(output,'temp')
outputname = 'Data/' + linemap + '.lyr'
print outputname
arcpy.SaveToLayerFile_management('temp', outputname)

#Get the layer file so it can be edited
layer = arcpy.mapping.Layer(outputname)
timelayer = arcpy.mapping.Layer('assets/Time.lyr')

#Clean up the mess
del cursor, inscursor, row, layer, outputname

exit('The above part works')




#Open empty map document
mxd = arcpy.mapping.MapDocument('assets/Empty.mxd')
df = arcpy.mapping.ListDataFrames(mxd)[0]
print df
#Copy time settings from time layer:
arcpy.mapping.UpdateLayerTime(df, layer, timelayer)

#Add layer to map document
arcpy.mapping.AddLayer(df, layer)
arcpy.RefreshActiveView

#Save to copy
arcpy.env.overwriteOutput = True
copyname =  linemap + '.mxd'
layer.saveACopy(copyname)
print arcpy.GetMessages()


del mxd, df

print 'Done now'
