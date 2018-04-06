import arcpy
import csv

arcpy.Delete_management("in_memory")
arcpy.env.workspace = "in_memory"


GPS_POINTS = "filepath"
STUDENTS = "filepath"
SCHOOLS = "filepath"
OUTPUT_FILE = "filepath"
GPS_ROUTE_FIELD = "RteDisplayName"
STUDENT_ROUTE_FIELD = "RouteID"
SCHOOL_ROUTE_FIELD = "Route_Number"
STUDENT_BUFFER_DISTANCE = "175 feet"
SCHOOL_BUFFER_DISTANCE = "350 feet"
GPS_DRIVER_FIELD = "Driver"


#Create list of unique row values
def uniqueValues(table, field):
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor})

listOfRoutes = uniqueValues(GPS_POINTS,GPS_ROUTE_FIELD)
print len(listOfRoutes)
for route in listOfRoutes:
    if route[-2:] == 'PM' or route == 'NA':
        print route
        listOfRoutes.remove(route)
print len(listOfRoutes)

#Select schools or students on a specific route
def makeLayerOfPointsInRoute(route,inTable,pointType,clause):
    return arcpy.MakeFeatureLayer_management(inTable,route+pointType,clause,'','')

#Make a buffer around school or student points
def makeBuffer(inTable,pointType,distance,route):
    return arcpy.Buffer_analysis(inTable, pointType+"buffer"+route, distance)

#Count number of planned stops for route
def countPlannedStops(students,schools):
    numOfSchools = arcpy.GetCount_management(schools)
    numOfStudents = arcpy.GetCount_management(students)
    return numOfSchools+numOfStudents

#Check if planned stop is near arrival event, isolate each buffer and check for point within
def countPointInBuffers(buffers,pointType,arrivalEvents,route):
    print "COUNTING"
    countDict = {}
    with arcpy.da.SearchCursor(buffers,'OBJECTID')as cursor:
        for row in cursor:
            objectID = row[0]
            clause = "OBJECTID"+" = "+str(objectID)
            singleBuffer = arcpy.MakeFeatureLayer_management(buffers,pointType+"BUFF"+str(objectID)+route,clause,'','')
            arrivalPointsWithin = arcpy.SelectLayerByLocation_management(arrivalEvents,"WITHIN",
                                                                         singleBuffer,'',"NEW_SELECTION","NOT_INVERT")
            numOfEventsInBuffer = int(arcpy.GetCount_management(arrivalPointsWithin)[0])
            countDict.update({objectID:numOfEventsInBuffer})
            arcpy.SelectLayerByAttribute_management(arrivalEvents, "CLEAR_SELECTION")
    return countDict

def countNonZeroValues(dictionary):
    count = 0
    for x in dictionary.itervalues():
        if x > 0:
            count+=1
    return count
            
def main():
    with open(OUTPUT_FILE, 'ab') as reportfile: 
        fieldnames = ['Route','Driver','School Stops','School Stops Logged','Student Stops','Student Stops Logged','Stops Logged PCT']
        writer = csv.DictWriter(reportfile, fieldnames)
        writer.writeheader()
        for route in listOfRoutes:
            ResultDict = {}
        
            print "ROUTE:",route

            gpsClause = GPS_ROUTE_FIELD + " = " + "'"+route+"'"
            gpsPoints = makeLayerOfPointsInRoute(route,GPS_POINTS,"gps",gpsClause)

            driver = uniqueValues(gpsPoints,GPS_DRIVER_FIELD)[0]
            print "DRIVER:",driver
            
            studentClause = STUDENT_ROUTE_FIELD + " = " +"'" +route[:4]+"'"
            students = makeLayerOfPointsInRoute(route,STUDENTS,"students",studentClause)
            
            schoolClause = SCHOOL_ROUTE_FIELD + " = " + "'"+route[:4]+"'"
            schools = makeLayerOfPointsInRoute(route,SCHOOLS,"schools",schoolClause)

            studentBuffers = makeBuffer(students,"students",STUDENT_BUFFER_DISTANCE,route[:4])
            schoolBuffers = makeBuffer(schools,"schools",SCHOOL_BUFFER_DISTANCE,route[:4])

            print "SCHOOLS"
            arrivalPointsAtSchoolDict = countPointInBuffers(schoolBuffers,"school",gpsPoints,route[:4])

            print "STUDENTS"
            arrivalPointsAtStudentDict = countPointInBuffers(studentBuffers,"student",gpsPoints,route[:4])

            
            numOfSchools = len(arrivalPointsAtSchoolDict)
            numOfStudents = len(arrivalPointsAtStudentDict)
            numOfStops = numOfSchools + numOfStudents

            numOfLoggedSchools = countNonZeroValues(arrivalPointsAtSchoolDict)
            numOfLoggedStudents = countNonZeroValues(arrivalPointsAtStudentDict)
            numOfLoggedStops = numOfLoggedSchools + numOfLoggedStudents

            ResultDict['Route'] = route
            ResultDict['Driver'] = driver
            ResultDict['School Stops'] = numOfSchools
            ResultDict['School Stops Logged'] = numOfLoggedSchools
            ResultDict['Student Stops'] = numOfStudents
            ResultDict['Student Stops Logged'] = numOfLoggedStudents

            try:
                ResultDict['Stops Logged PCT'] = float(numOfLoggedStops)/float(numOfStops)
            except ZeroDivisionError:
                ResultDict['Stops Logged PCT'] = "0 division err"
            writer.writerow(ResultDict)
            
main()

        

        

        
        
            

    





    
        
