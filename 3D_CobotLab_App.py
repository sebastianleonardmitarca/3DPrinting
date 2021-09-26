'''
    3D Printing Application
    Develop by Mitarca Sebastian-Leonard (CobotTeam)
    
    07 Sept 2021 - Second Version
    Fist version location: '...\\3D Printing\\3D Printing Python'
  
    ###    ###   ##  ######## 
    ####  ####   ##    ##
    ##  ##  ##   ##    ## 
    ##      ##   ##    ##               
            ##   ##    ##      
            ##   ##    ##

'''

#import libraries
import os, sys, re, datetime, time, csv, os.path
import shutil

#Global Location Variables
code_location = '~~~~~~~~'
processed_location = '...\\3D Printing\\3D Printing Python\\Processed'
logs_location = '...\\3D Printing\\3D Printing Python\\logs.txt'
csv_location = '...\\3D Printing\\3D Printing Python\\3DPrintingTable.csv'
history_location = '...\\3D Printing\\3D Printing Python\\History'
nok_location = '...\\3D Printing\\3D Printing Python\\NOK'

#write in logs file
def writeInLogs(message):
    try:
        date_time = datetime.datetime.now()
        logs_file = open(logs_location, 'a')
        print('%s %s \n' % (datetime.datetime.strftime(date_time, '%m/%d/%Y %H:%M:%S'), str(message)))
        logs_file.write('%s %s \n' % (datetime.datetime.strftime(date_time, '%m/%d/%Y %H:%M:%S'), str(message)))
        #logs_file.close()
    except:
        print("Nu s-a putut accesa/scrie in fisierul Logs")
        
#extract data from gcode
def getDataGcode(filename):
    printer_technology = ""
    filament_type = ""
    filament_used = 0
    printed_time = 0
    #filament_cost = 0

    try:
        with open(filename, 'r') as file:
            for line in file.readlines():
                try:
                    if '; printer_model =' in line:
                        printer_technology = line.split('=')[1].strip()
                        writeInLogs('  [INFO] printer technology: ' + str(printer_technology))
                    elif ';TARGET_MACHINE.NAME:' in line:
                        printer_technology = line.split(':')[1].strip()
                        writeInLogs('  [INFO] printer technology: ' + str(printer_technology))
                except:
                    writeInLogs(" [ERROR] Nu a fost gasit 'printer_technology'")
                
                try:
                    if 'filament_type =' in line:
                        filament_type = line.split("=",1)[1].strip()
                        writeInLogs('  [INFO] filament type: ' + str(filament_type))
                    
                    elif 'EXTRUDER_TRAIN.1.INITIAL_TEMPERATURE' in line:
                        info_temperature = line.split(':')[1].strip()
                        if int(info_temperature) >= 225 and int(info_temperature) <= 255:
                            filament_type = 'PETG'
                            writeInLogs('  [INFO] filament type: ' + str(filament_type))
                        elif int(info_temperature) >= 190 and int(info_temperature) <= 215:
                            filament_type = 'PLA'
                            writeInLogs('  [INFO] filament type: ' + str(filament_type))
                except:
                    writeInLogs(" [ERROR] Nu a fost gasit 'filament type'")

                try:
                    if '; filament used [g] =' in line:
                        weight = re.search(r'\d+(\.\d{1,2})?', line)     
                        filament_used = float(weight.group())
                        writeInLogs('  [INFO] total filament used: ' + str(filament_used))  
                    elif 'EXTRUDER_TRAIN.1.MATERIAL.VOLUME_USED' in line:
                        info_filament_used = line.split(':')[1].strip()
                        if filament_type == 'PLA':
                            filament_used = round(int(info_filament_used)/1000*1.24)
                            writeInLogs('  [INFO] total filament used: ' + str(filament_used)) 
                        elif filament_type == 'PETG':
                            filament_used = round(int(info_filament_used)/1000*1.38)
                            writeInLogs('  [INFO] total filament used: ' + str(filament_used)) 
                except:
                    writeInLogs(" [ERROR] Nu a fost gasit 'filament used [g]'")

                try:
                    if '; estimated printing time (normal mode)' in line:
                        my_index = 2
                        info_time_split_list = []
                        info_index_list = [1440, 60, 1]
                        info_time_concat = line.split()[7:]

                        for info_time_item in info_time_concat:
                            info_time_item = info_time_item[:len(info_time_item)-1]
                            info_time_split_list.append(info_time_item)
                        printed_time = int(info_time_split_list.pop(-1))//60

                        while len(info_time_split_list) > 0:
                            printed_time = printed_time + (int(info_time_split_list.pop(-1))*info_index_list[my_index])
                            my_index -= 1
                       
                        writeInLogs('  [INFO] estimated printing time (minutes): ' + str(printed_time))
                    elif 'PRINT.TIME' in line:
                        printed_time = int(line.split(':')[1])//60
                        writeInLogs('  [INFO] estimated printing time (minutes): ' + str(printed_time))
                except:
                    writeInLogs(" [ERROR] Nu s-a putut convertii timpul ori nu a fost gasit elementul 'estimaned printing time'")
        file.close()
    except:
        writeInLogs(" [ERROR] Nu s-a putut deschide fisierul .gcode!")

    return printer_technology, filament_type, filament_used, printed_time

#extract data from sl1
def getDataSl1(filename):
    printer_technology_sl1 = ""
    filament_type_sl1 = ""
    filament_used_sl1 = 0
    printed_time_sl1 = 0
    #filament_cost_sl1 = 0
    
    #binary encode
    printer_technology_sl1_binary = 'printerModel ='.encode('latin-1')
    filament_used_sl1_binary = 'usedMaterial ='.encode('latin-1')
    filament_type_sl1_binary = 'materialName ='.encode('latin-1')
    printed_time_sl1_binary = 'printTime ='.encode('latin-1')

    try:
        with open(filename, 'rb') as file:
            for line in file.readlines():
                try:
                    if printer_technology_sl1_binary in line:
                        printer_technology_sl1 = line.decode('latin-1').split('=')[1].strip()
                        writeInLogs('  [INFO] printer technology: ' + str(printer_technology_sl1))
                except:
                    writeInLogs(" [ERROR] Nu a fost gasit elementul 'print Model!")

                try:
                    if filament_type_sl1_binary in line:
                        filament_type_sl1 = line.decode('latin-1').split('=')[1].strip()
                        filament_type_sl1 = filament_type_sl1.split('@')[0].strip()
                        writeInLogs('  [INFO] filament type: ' + str(filament_type_sl1))
                except:
                    writeInLogs(" [ERROR] Nu a fost gasit elementul 'material Name!")

                try:
                    if filament_used_sl1_binary in line:
                        filament_used_sl1 = line.decode('latin-1').split('=')[1].strip()
                        writeInLogs('  [INFO] total filament used: ' + str(filament_used_sl1))
                except:
                    writeInLogs(" [ERROR] Nu a fost gasit elementul 'used Material!")

                try:
                    if printed_time_sl1_binary in line:
                        printed_time_sl1 = round(float(line.decode('latin-1').split('=')[1].strip())//60)
                        writeInLogs('  [INFO] estimated printing time (minutes): ' + str(printed_time_sl1))
                except:
                    writeInLogs(" [ERROR] Nu a fost gasit elementul 'print Time!")
        file.close()
    except:
        writeInLogs(" [ERROR] Nu s-a putut deschide fisierul .sl1!")
    
    return printer_technology_sl1, filament_type_sl1, filament_used_sl1, printed_time_sl1

#write in csv file
def writeInCSV(info_time, info_filename, info_technology, info_filament, info_used, info_printed_time):
    try:
        with open(csv_location, 'a', newline='') as output_csv:
            write = csv.writer(output_csv)
            write.writerow([info_time, info_filename, info_technology, info_filament, info_used, info_printed_time])
        output_csv.close()
    except:
        writeInLogs(" [ERROR] Nu s-a putut scrie in CSV!")

#move file to Processed
def moveToProcessed(filename, location):
    temp_processed_location = processed_location + "\\" + filename
    writeInLogs('  [INFO] se muta fisierul...')
    try:
        shutil.copy(location, temp_processed_location)
        writeInLogs('  [INFO] fisierul a fost mutat!')
        os.remove(location)
        writeInLogs('  [INFO] fisierul a fost sters!')
    except:
        writeInLogs(" [ERROR] Nu s-a putut muta fisierul!")

#main part
while 1:
    try:
        file_created_datetime = " "
        temp_location = os.listdir(code_location)

        for item in temp_location:
            file_created_datetime = time.strftime('%m/%d/%Y',time.gmtime(os.path.getmtime(code_location + '\\' + item)))

            if item.endswith('.gcode'):
                gcode_file = code_location + '\\' + item
                sample_file_name = item.split('.gcode')[0]
                writeInLogs('[STATUS] application status: start process; file type: gcode!')
                writeInLogs('  [INFO] created at: ' + str(file_created_datetime))
                writeInLogs('  [INFO] filename: ' + str(sample_file_name))
                printer_technology, filament_type, filament_used, printed_time = getDataGcode(gcode_file)
                writeInCSV(file_created_datetime, sample_file_name, printer_technology, filament_type, filament_used, printed_time)
                moveToProcessed(item,gcode_file)
            elif item.endswith('.sl1'):
                sl1_file = code_location + '\\' + item
                sample_file_name = item.split('.sl1')[0]
                writeInLogs('[STATUS] application status: start process; file type: sl1!')
                writeInLogs('  [INFO] created at: ' + str(file_created_datetime))
                writeInLogs('  [INFO] filename: ' + str(sample_file_name))
                printer_technology_sl1, filament_type_sl1, filament_used_sl1, printed_time_sl1 = getDataSl1(sl1_file)
                writeInCSV(file_created_datetime, sample_file_name, printer_technology_sl1, filament_type_sl1, filament_used_sl1, printed_time_sl1)
                moveToProcessed(item,sl1_file)

    except IOError:
        time.sleep(1)
