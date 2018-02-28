import dicom,os, glob, scipy.io, numpy, vtk, sys, datetime, argparse
from clint.textui import colored
from vtk.util import numpy_support
from scipy.ndimage.filters import uniform_filter
from rolling_window import rolling_window



import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def eddyCurrentCorrection(UOrg, VOrg, WOrg, randNoiseThreshold=1, eddyCurrentThreshold=12, eddyOrder=1, plotBool=0, verbous=0, plotEddyPlane=1):


    USTD = numpy.zeros((UOrg.shape[0],UOrg.shape[1],UOrg.shape[2]))
    VSTD = numpy.zeros(USTD.shape)
    WSTD = numpy.zeros(USTD.shape)
    

    for kIter in range(UOrg.shape[2]):

        USTD[1:(UOrg.shape[0]-1),1:(UOrg.shape[1]-1), kIter] = numpy.std(rolling_window(UOrg[:,:,kIter,:], (3,3,0), toend=False), axis=(4,3,1))
        VSTD[1:(VOrg.shape[0]-1),1:(VOrg.shape[1]-1), kIter] = numpy.std(rolling_window(VOrg[:,:,kIter,:], (3,3,0), toend=False), axis=(4,3,1))
        WSTD[1:(WOrg.shape[0]-1),1:(WOrg.shape[1]-1), kIter] = numpy.std(rolling_window(WOrg[:,:,kIter,:], (3,3,0), toend=False), axis=(4,3,1))

    
    if verbous:    
        print("Ustd Max: ")
        print(USTD.max())
        print("Vstd Max: ")
        print(VSTD.max())
        print("Wstd Max: ")
        print(WSTD.max())

        print("Ustd Min: ")
        print(USTD.min())
        print("Vstd Min: ")
        print(VSTD.min())
        print("Wstd Min: ")
        print(WSTD.min())

        print("USTD size: ")
        print(USTD.shape)


    

    staticTissueU = UOrg[:,:,:,-1].copy()
    staticTissueV = VOrg[:,:,:,-1].copy()
    staticTissueW = WOrg[:,:,:,-1].copy()

    staticTissueU[(USTD < (eddyCurrentThreshold*USTD.max()/100)) & (VSTD < (eddyCurrentThreshold*VSTD.max()/100) ) & (WSTD < (eddyCurrentThreshold*WSTD.max()/100))] = 0
    staticTissueV[(USTD < (eddyCurrentThreshold*USTD.max()/100)) & (VSTD < (eddyCurrentThreshold*VSTD.max()/100) ) & (WSTD < (eddyCurrentThreshold*WSTD.max()/100))] = 0
    staticTissueW[(USTD < (eddyCurrentThreshold*USTD.max()/100)) & (VSTD < (eddyCurrentThreshold*VSTD.max()/100) ) & (WSTD < (eddyCurrentThreshold*WSTD.max()/100))] = 0

    print(staticTissueU.shape)
    
    if plotBool:    

        vmax = numpy.max([UOrg[:,:,20,1].max(), staticTissueU[:,:,20].max()])
        vmin = numpy.min([UOrg[:,:,20,1].min(), staticTissueU[:,:,20].min()])
        vmax = numpy.max([vmax, -vmin])
        vmin = -vmax
    
        for i in range(1,72):
        # plot with various axes scales
            plt.figure(i)

       
            plt.subplot(121)
            plt.imshow(UOrg[:,:,i,1], vmin=vmin, vmax=vmax, cmap='seismic')
            plt.title('Org data')


           
            plt.subplot(122)
            plt.imshow(UOrgtest[:,:,i], vmin=vmin, vmax=vmax, cmap='seismic')
            plt.title('static tissue')

            plt.show()
            

    del USTD, VSTD, WSTD  
    
    flowCorrected = numpy.zeros([UOrg.shape[0], UOrg.shape[1], UOrg.shape[2], 3, UOrg.shape[3]])
   
       
    xInit = numpy.linspace(0, UOrg.shape[0], UOrg.shape[0])
    yInit = numpy.linspace(0, UOrg.shape[1], UOrg.shape[1])
    
    X, Y = numpy.meshgrid(xInit, yInit, sparse=False, indexing='ij')
    
    X2=X*X
    Y2=Y*Y
    XY=X*Y
    
    
    plainU = numpy.zeros([UOrg.shape[0], UOrg.shape[1], UOrg.shape[2], UOrg.shape[3]])
    plainV = numpy.zeros([UOrg.shape[0], UOrg.shape[1], UOrg.shape[2], UOrg.shape[3]])
    plainW = numpy.zeros([UOrg.shape[0], UOrg.shape[1], UOrg.shape[2], UOrg.shape[3]])
    
    if eddyOrder == 1:
        # best-fit linear plane
        #for kIter in range(UOrg.shape[3]):
        for iIter in range(UOrg.shape[2]):
            
                BU = staticTissueU[:, :, iIter].ravel()
                BV = staticTissueV[:, :, iIter].ravel()
                BW = staticTissueW[:, :, iIter].ravel()
                    
                D = numpy.ones((staticTissueU.shape[0]*staticTissueU.shape[1], 3))
                print(D.shape)
                D[:, 0] = X.ravel()[BU>0]
                D[:, 1] = Y.ravel()[BU>0]
            
       
                CU,_,_,_ = scipy.linalg.lstsq(D, BU)    # coefficients
                CV,_,_,_ = scipy.linalg.lstsq(D, BV)    # coefficients
                CW,_,_,_ = scipy.linalg.lstsq(D, BW)
        
                # evaluate it on grid
                plainU[:,:,iIter] = CU[0]*X + CU[1]*Y + CU[2]
                plainV[:,:,iIter] = CV[0]*X + CV[1]*Y + CV[2]
                plainW[:,:,iIter] = CW[0]*X + CW[1]*Y + CW[2]
            
            
        
    
    elif eddyOrder == 2:
        # best-fit quadratic curve
        
        for iIter in range(plainU.shape[2]):
            
            eddyMaskTemp = eddyMask[:,:,iIter]
            indEddyMask = numpy.argwhere(eddyMaskTemp.ravel()).ravel()
            BU = UOrgMean[:, :, iIter].ravel()[indEddyMask]
            BV = VOrgMean[:, :, iIter].ravel()[indEddyMask]
            BW = WOrgMean[:, :, iIter].ravel()[indEddyMask]
                    
            D = numpy.ones((len(indEddyMask), 6))
            D[:, 0] = X.ravel()[indEddyMask]
            D[:, 1] = Y.ravel()[indEddyMask]
            D[:, 2] = XY.ravel()[indEddyMask]
            D[:, 3] = X2.ravel()[indEddyMask]
            D[:, 4] = Y2.ravel()[indEddyMask]
            
       
            CU,_,_,_ = scipy.linalg.lstsq(D, BU)    # coefficients
            CV,_,_,_ = scipy.linalg.lstsq(D, BV)    # coefficients
            CW,_,_,_ = scipy.linalg.lstsq(D, BW)
        
            # evaluate it on grid
            plainU[:,:,iIter] = CU[0]*X + CU[1]*Y + CU[2]*XY + CU[3]*X2 + CU[4]*Y2 + CU[5]
            plainV[:,:,iIter] = CV[0]*X + CV[1]*Y + CV[2]*XY + CV[3]*X2 + CV[4]*Y2 + CV[5]
            plainW[:,:,iIter] = CW[0]*X + CW[1]*Y + CW[2]*XY + CW[3]*X2 + CW[4]*Y2 + CW[5]
            
    
    
    if plotEddyPlane:
        plt.figure(2)
        #ax = fig.add_subplot(111, projection='3d')
            
        #for i in range(staticTissueU[20]):

        Axes3D.plot_surface(X, Y,  plainU[:,:,20])  

            

       
#            plt.subplot(121)
 #           plt.imshow(UOrg[:,:,i,1], vmin=vmin, vmax=vmax, cmap='seismic')
  #          plt.title('Org data')


           
   #         plt.subplot(122)
    #        plt.imshow(UOrgtest[:,:,i], vmin=vmin, vmax=vmax, cmap='seismic')
     #       plt.title('static tissue')

        plt.show()  
   


    for k in range(UOrg.shape[3]):
        
        flowCorrected[:, :, :,0, k] = UOrg[:,:,:,k] - plainU
        flowCorrected[:, :, :,1, k] = VOrg[:,:,:,k] - plainV
        flowCorrected[:, :, :,2, k] = WOrg[:,:,:,k] - plainW
    
    
    return flowCorrected

def randNoise(UOrg, VOrg, WOrg, randThre=25, plotBool=1):

    USTD = numpy.zeros((UOrg.shape[0],UOrg.shape[1],UOrg.shape[2]))
    VSTD = numpy.zeros(USTD.shape)
    WSTD = numpy.zeros(USTD.shape)
    

    for kIter in range(UOrg.shape[2]):

        USTD[1:(UOrg.shape[0]-1),1:(UOrg.shape[1]-1), kIter] = numpy.std(rolling_window(UOrg[:,:,kIter,:], (3,3,0), toend=False), axis=(4,3,1))
        VSTD[1:(VOrg.shape[0]-1),1:(VOrg.shape[1]-1), kIter] = numpy.std(rolling_window(VOrg[:,:,kIter,:], (3,3,0), toend=False), axis=(4,3,1))
        WSTD[1:(WOrg.shape[0]-1),1:(WOrg.shape[1]-1), kIter] = numpy.std(rolling_window(WOrg[:,:,kIter,:], (3,3,0), toend=False), axis=(4,3,1))

      
   # UOrgtest = UOrg[:,:,:,1].copy()

   # UOrgtest[(USTD > (randThre*USTD.max()/100)) & (VSTD > (randThre*VSTD.max()/100) ) & (WSTD > (randThre*WSTD.max()/100))] = 0
            

    
    flowCorrected = numpy.zeros([UOrg.shape[0], UOrg.shape[1], UOrg.shape[2],3,UOrg.shape[3]])


    UOrg[(USTD > (randThre*USTD.max()/100)) & (VSTD > (randThre*VSTD.max()/100) ) & (WSTD > (randThre*WSTD.max()/100))] = 0
    VOrg[(USTD > (randThre*USTD.max()/100)) & (VSTD > (randThre*VSTD.max()/100) ) & (WSTD > (randThre*WSTD.max()/100))] = 0
    WOrg[(USTD > (randThre*USTD.max()/100)) & (VSTD > (randThre*VSTD.max()/100) ) & (WSTD > (randThre*WSTD.max()/100))] = 0



    flowCorrected[:,:,:,0] = UOrg
    flowCorrected[:,:,:,1] = VOrg
    flowCorrected[:,:,:,2] = WOrg

    
    if plotBool:
        vmax = numpy.max([UOrg[:,:,20,1].max(), VOrg[:,:,20,1].max(), WOrg[:,:,20,1].max()])
        vmin = numpy.min([UOrg[:,:,20,1].min(), VOrg[:,:,20,1].min(), WOrg[:,:,20,1].min()])
        vmax = numpy.max([vmax, -vmin])
        vmin = -vmax

        # plot with various axes scales
        plt.figure(1)

       
        plt.subplot(131)
        plt.imshow(UOrg[:,:,20,1], vmin=vmin, vmax=vmax, cmap='seismic')
        plt.title('U Org')


       
        plt.subplot(132)
        plt.imshow(VOrg[:,:,20, 1], vmin=vmin, vmax=vmax, cmap='seismic')
        plt.title('V Org')

        plt.subplot(133)
        plt.imshow(WOrg[:,:,20, 1], vmin=vmin, vmax=vmax, cmap='seismic')
        plt.title('W Org')

        plt.show()
    

    return flowCorrected





