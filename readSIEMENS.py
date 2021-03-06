import dicom,os, glob, scipy.io, numpy, vtk, sys, datetime, argparse, timeit
from clint.textui import colored
from readSIEMENSFlow import readSIEMENSFlow

''' This function reads SIEMENS Flow data '''


        


def readPatientInfo(FolderPath, cmra, tof):

    MagPathStr = str(FolderPath)
    foldersList = [os.path.join(MagPathStr,o) for o in os.listdir(MagPathStr) if os.path.isdir(os.path.join(MagPathStr,o))]  
    if not foldersList:
        filesListTEMP = glob.glob(MagPathStr + "/*") 
            
        ds = dicom.read_file(filesListTEMP[0])
        if not "SIEMENS" in ds.Manufacturer: 
                print("This is not a SIEMENS sequence.")
                sys.exit()
    else:
            
                for dirName in foldersList:
                    filesListTEMP = glob.glob(dirName + "/*") 
                    
                    ds = dicom.read_file(filesListTEMP[0])
                    if "SIEMENS" in ds.Manufacturer:
                        proceed = True
                        
                        if "magnitude"  in ds.ImageComments:
                            PathMagData = dirName
                            #print(PathMagData)
                            
     
                        if "phase" in ds.ImageComments:
                            PathFlowData = dirName
                            #print(PathFlowData)
 #ConstDimsTemp = (int(ds.Rows), int(ds.Columns), int(ds.ImagesInAcquisition), int(ds.CardiacNumberOfImages))
                            #dXY = ds.PixelSpacing
                            #dZ = ds.SpacingBetweenSlices
                            #pixel_spc = (dXY[0],dXY[1],dZ)
                            #print(pixel_spc)
                        
          
   

    lstFilesDCM = glob.glob(PathMagData  + "/*") 
    RefDs = dicom.read_file(lstFilesDCM[0])
    print(colored.yellow("\t"+"**"*20))
    print(colored.yellow("\t\tSIEMENS 4D Flow DICOM reader. \n\t\tDeveloped by: Ali Bakhshinejad \n\t\tali.bakhshinejad@gmail.com"))
    print(colored.yellow("\t"+"**"*20))
    
    
    
    print(colored.green("Reading data for case:"))
    print(colored.blue("\t Patient ID: " + RefDs.PatientID ))
    print(colored.blue("\t Manufacturer Name: " + RefDs.Manufacturer ))
    #print("M: " + RefDs.SoftwareVersion )
    return RefDs
            
        

def printReport(outPath, RefDs):
    # file-output.py
    today = datetime.date.today()

    dXY = RefDs.PixelSpacing
    dZ = RefDs.SliceThickness
    pixel_spc = (dXY[0],dXY[1],dZ)
    f = open(outPath + "/readMe.txt",'w')
    f.write('This is the report for reading GE produced DICOM files. \n In case any problems contact: ali.bakhshinejad@gmail.com \n Produced at ' + str(today))
    f.write('\n' + '--'*20)
    f.write('\n Patient information')
 #   f.write('\n Patient Name: ' + RefDs.PatientName)
    f.write('\n Patient ID: ' + RefDs.PatientID)
    f.write('\n Patient Position: ' + RefDs.PatientPosition)
    f.write('\n'+'--'*5)
    f.write('\n Image information:')
   # f.write('\n Image Orientation Position: ' + RefDs.ImageOrientationPosition)
    f.write('\n Resolution: ' + str(pixel_spc))
    f.close() 
    
def main():

    start_time = timeit.default_timer()

    parser = argparse.ArgumentParser(description="SIEMENS 4D Flow DICOM reader developed by Ali Bakhshinejad. contact: ali.bakhshinejad@gmail.com")

    parser.add_argument("-i", "--input", help="Path to the main folder.")
    parser.add_argument("-v", "--velocityorder", help="The order of reading velocity files, default value is [1,0,2] which reresents [y,x,z]")
    parser.add_argument("-si", "--velocitysign", help="Sign for each velocity component, default value is [1,1,-1]")
    parser.add_argument("-e", "--eddycurrent", action="store_true", help="Activating Eddy current correction function")
    parser.add_argument("-p", "--eddyplane", type=int, help="The plane order to fit on the static tissue. Currently we support 1st and second order (value: 1 or 2). Default value is 2nd order polynominal.")
    parser.add_argument("-t", "--eddythreshold", type=int, help="The threshold value to generate static tissue mask (default value is standard deviation less than 20)")
    parser.add_argument("-n", "--randomnoise", help="Threshold for random noise correction. (In percentage)")
    parser.add_argument("-ol", "--output", help="Output location")
    parser.add_argument("--vtk", action="store_true", help="save in VTK format")
    parser.add_argument("--mat", action="store_true", help="save in MAT format")
    parser.add_argument("-se", "--segmentation",  action="store_true", help="Only save magnitude file to be used for segmentation purposes.")

    parser.add_argument("--cmra", action="store_true", help="Read cMRA dataset, (No Flow Data).")
    parser.add_argument("--tof", action="store_true", help="Read Time Of Flght (TOF) database.")

    args = parser.parse_args()
    

    if args.input is None:
        print(colored.red("FatalError: Input location is missing."))
        sys.exit()
    else:
        print(colored.green("We are looking to read data from: "))
        RefDs = readPatientInfo(args.input, args.cmra, args.tof)

    if args.velocityorder is None:
        args.velocityorder = numpy.array([0,1,2])
#    else:
#        args.velocityorder = numpy.array(args.velocityorder)

    if args.velocitysign is None:
        args.velocitysign = numpy.array([-1,1,-1])
#    else:
#        args.velocitysign = numpy.array(args.velocitysign)

    if args.output is None:
        print(colored.red("FatalError: output location is missing."))
        sys.exit()
    else:
        if not os.path.exists(args.output):
            os.makedirs(args.output)

    if args.eddythreshold is None:
        args.eddythreshold = 20

    if args.randomnoise is None:
        print(colored.yellow("Warning: No random noise correction will happen!"))


    if (args.eddycurrent and args.eddyplane is None):
        args.eddyplane = 2

    
    
   
    #print(args)
   # if args.cmra:
#        RefDs = readGEcMRA(args)

#    elif args.tof:
#        RefDs = readGETOF(args)
#    else:
    RefDs =  readSIEMENSFlow(args)

    printReport(args.output, RefDs)
    # code you want to evaluate
    elapsed = timeit.default_timer() - start_time
    print(colored.yellow("Execuation time: " + str(elapsed)+ " s \nDone!"))
    
    
main()
