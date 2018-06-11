##--------------------------------------------------------------------------------
## Evacuation GraphData.py
## Create visualizations of the evacuation route line data for the Northern Gulf
## analyzed using the 
##
## Created: February 2018
## Author: Amber Halstead <amber.halstead@duke.edu>
##--------------------------------------------------------------------------------
# Import necessary modulesimport arcpy
import pandas as pd

#Set the workspace to the ModelOutputs subfolder
arcpy.env.workspace = '../Data/ModelOutputs'

#Retrieve all files ending in "RoadDepth.shp"
files = arcpy.ListFeatureClasses("*RoadDepth.shp")

#Initialize the list of dataframes
dfs = []

#Loop through RoadDepth tables, convert to dataframes, and add to df list
for file in files:
    
    #Extract the scenario name
    name = file.split('_')[2]
    
    #Add shape_area if absent
    if arcpy.ListFields(file,"Shape_area") == []:
        arcpy.AddField_management(file, "Shape_area", "DOUBLE")
        arcpy.CalculateField_management(file, "Shape_area", "!shape.area@squarefeet!","PYTHON_9.3")

    #Convert to a numpy array and then a pandas dataframe
    arr = arcpy.da.TableToNumPyArray(file, ('ROAD_CLASS', 'STATE', 'Depth', 'Shape_area'))
    df = pd.DataFrame(arr)

    #Add the scenario name to the records
    df['Name'] = name

    #Add the dataframe to the list of dataframes
    dfs.append(df)

#Concatenate all dataframes into a single one
dfAll = pd.concat(dfs)

#Remove "No Inundation" records
dfAll = dfAll[dfAll.Depth != 'No Inundation']
dfAll = dfAll[dfAll.Depth != 'UNDEFINED']
dfAll = dfAll[dfAll.Depth != '']

#Compute sum of Shape_area across road classes
df = dfAll.groupby(['Name','STATE','ROAD_CLASS','Depth'])['Shape_area'].sum()

#Pivot the table on the STATE values
df2 = df.unstack(["STATE"])

#Create a list of Depth values (in order) for plotting
depthList = ['< 1ft','1 - 2ft', '2 - 3ft', '3 - 4ft', '4 - 5ft', '5 - 6ft', 
             '6 - 7ft', '7 - 8ft', '8 - 9ft', '9 - 10ft',  '> 10ft']
roadList =  ['FEDERAL HIGHWAY', 'INTERSTATE HIGHWAY', 'STATE HIGHWAY', 'STREET']

#Create a list of scenarios and road types
scenarios = df2.index.levels[0]
roads = df2.index.levels[1]

#Loop through each scenario, generate a plot, and save it to a png file
for scenario in scenarios:     
        #Transpose the table - subset by the specified scenario
        dfPlot = df2.xs((scenario)).T
        
        #Order the columns to match the depthList above
        dfPlot = dfPlot[depthList]

        #Create the bar chart
        fig = dfPlot.plot(kind='bar',       
                          subplots=True, 
                          figsize=(15,5),
                          legend=False,
                          title = "SLR: " + str(scenario),
                          colormap='viridis')#https://matplotlib.org/gallery/color/colormap_reference.html

        #legend centered towards top - w/3 columns
        #fig.legend(loc = 'upper right', bbox_to_anchor=(0.8,1.05),
        #           ncol = 3, fancybox = True, shadow = True)
        
        #legend is outside plot in single column
        #fig.legend(loc = 'center left', bbox_to_anchor=(1, 0.5), fancybox = True, shadow = True)

        #Save the figure to a file
        fig.get_figure().savefig("{0}_{1}.png".format(scenario,road))
