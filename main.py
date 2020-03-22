'''
__author__: Kevin(xhaoAI)

This demo is to accomplish map match task by arcpy API in Arcgis10.5.
The main work is to map the GPS point on the road by matching the coodinates series into fine-grid Shanghai-Road-WGS84 shapefile.
'''
# coding=utf-8
import arcpy
import numpy as np
import pandas as pd
import os
import time

## mkdir before start ##
raw_data_dir=u'./data'
new_data_dir=u'./simplified data'
index_data_dir=u'./raw index'
output_file_dir=u'./output file'
processed_rawdata_dir=u'./processed raw data'
def createxyfromtable(in_Table, x_coords, y_coords, out_Layer, point_shp):
    # Make the XY event layer...

    arcpy.MakeXYEventLayer_management(in_Table, x_coords, y_coords, out_Layer)
    # Process: Copy Features
    arcpy.CopyFeatures_management(out_Layer, point_shp, "", "0", "0", "0")
    # Print total rows
    print(arcpy.GetCount_management(out_Layer))

def SaveShpAsCSV(ShpFile,OutputName):
    fields = arcpy.gp.listFields(ShpFile)
    fieldList2 = []
    for field in fields:
        fieldList2.append(str(field.name))
    del fieldList2[1]
    try:
        arcpy.ExportXYv_stats(ShpFile,fieldList2,"COMMA",OutputName,"ADD_FIELD_NAMES")
    except:
        print arcpy.gp.GetMessages()

# pre-process csv
def preprocessing():
    rawfilelist=os.listdir(raw_data_dir)
    done_files=os.listdir(new_data_dir)
    for rawfile in rawfilelist:
        try:
            if rawfile in done_files:
                print('already done! Next')
                continue
            else:
                print(rawfile)
                file_dir = raw_data_dir + '/' + rawfile
                data = pd.read_csv(file_dir, engine='python')
                index_notnul = data[
                    ~(data['Head_Unit.Longitude'].isnull()) & ~(data['Head_Unit.Latitude'].isnull())].index.values
                fulldata = data[~(data['Head_Unit.Longitude'].isnull()) & ~(data['Head_Unit.Latitude'].isnull())]
                ID = fulldata['vtti.file_id'].values
                lat = fulldata['Head_Unit.Latitude'].values
                lon = fulldata['Head_Unit.Longitude'].values
                new_data = pd.DataFrame({'ID': ID, 'Head_Unit.Latitude': lat, 'Head_Unit.Longitude': lon})
                new_data.to_csv(new_data_dir + '/' + rawfile)
                new_data_lat_lon_index = pd.DataFrame({'INDEX': index_notnul})
                new_data_lat_lon_index.to_csv(index_data_dir + '/' + rawfile)
        except Exception as e:
            print('WARNING! error occur: ',e)
            continue
    print('preprocessing done!')

def del_file(path):
    ls = os.listdir(path)
    for i in ls:
        c_path = os.path.join(path, i)
        if os.path.isdir(c_path):
            del_file(c_path)
        else:
            try:
                os.remove(c_path)
            except:
                continue

# preprocessing()

filelist=os.listdir(new_data_dir)
os.chdir(u'./simplified data')
existingFiles=os.listdir(processed_rawdata_dir)
for filename in filelist:
    if filename in existingFiles:
        continue
    else:
        try:
            print(filename)
            path = u'./gis_results'
            name = filename.replace('.csv', '')
            shp_path = path + '/' + name
            os.makedirs(shp_path)
            arcpy.env.workspace = shp_path
            # CSV to shp
            gps_name = 'GPS_POINT' + '_' + name
            gps_shp_name = 'GPS_POINT' + '_' + name + '.shp'
            createxyfromtable(filename, "Head_Unit.Longitude", "Head_Unit.Latitude", gps_name, gps_shp_name)
            # use NEAR toolkit
            near_shp_name = r'E:\zyh_Folder\gis_test_new\together.shp'
            arcpy.Near_analysis(gps_shp_name, near_shp_name, "10 Meters", "LOCATION")
            # creat new GPS points
            new_gps_name = 'GPS_POINT_together' + '_' + name
            new_gps_shp_name = 'GPS_POINT_together' + '_' + name + '.shp'
            gps_shp_dbf_name = gps_name + '.dbf'
            createxyfromtable(gps_shp_dbf_name, "NEAR_X", "NEAR_Y", new_gps_name, new_gps_shp_name)
            outputname = output_file_dir + '/' + filename + '_' + 'results.csv'
            SaveShpAsCSV(new_gps_shp_name, outputname)
            ## del shapefile to save space
            del_file(shp_path)   # 删除了文件夹中的内容，只保留了文件夹

            # concat the info to raw data
            match_data = pd.read_csv(outputname, engine='python')
            index_file = index_data_dir + '/' + filename
            index_data = pd.read_csv(index_file, engine='python')
            raw_file = raw_data_dir + '/' + filename
            raw_data = pd.read_csv(raw_file, engine='python')
            ## gps file
            NEAR_FID = match_data['NEAR_FID'].values  # len(NEAR_FID)=857
            NEAR_LON = match_data['NEAR_X'].values
            NEAR_LAT = match_data['NEAR_Y'].values
            ## real index in raw data
            real_index = index_data['INDEX'].values  # len(real_index)=857
            label = [0 for i in range(len(raw_data))]
            near_lon = [0 for i in range(len(raw_data))]
            near_lat = [0 for i in range(len(raw_data))]
            for count, ind in enumerate(real_index):
                if NEAR_FID[count] == -1:
                    label[ind] = 0
                else:
                    label[ind] = 1
                    near_lon[ind] = NEAR_LON[count]
                    near_lat[ind] = NEAR_LAT[count]
            raw_data['Road type'] = label
            raw_data['NEAR_LON'] = near_lon
            raw_data['NEAR_LAT'] = near_lat
            savedir = processed_rawdata_dir + '/' + filename
            raw_data.to_csv(savedir)
            print('#############', filename, ' done #############')
        except Exception as e:
            print('WARNING! error occur: ',e)
            continue






