import gtk

import unicap
import unicapgtk
import gobject
import cv2
import cv2.cv as cv
import numpy as np
import PIL
from PIL import Image
import time

class AppWindow( gtk.Window ):
    def __init__(self):
        self.valZoom = 0
        self.valAutoExpo = False
        self.valShoot = False
        gtk.Window.__init__(self)
        self.connect( 'delete-event', gtk.main_quit )

        self.do_save = False

        vbox = gtk.VBox()
        self.add( vbox )

        hbox = gtk.HBox()
        vbox.pack_start( hbox, False, True )

        capture_button = gtk.ToggleButton( label = "Capture" )
        hbox.pack_start( capture_button, False, False )
        capture_button.connect( 'toggled', self.__on_capture_toggled )

        button = gtk.Button( stock = gtk.STOCK_SAVE )
        hbox.pack_start( button, False, False )
        button.connect( 'clicked', self.__on_save_clicked )

        prop_button = gtk.Button( label = "Properties" )
        hbox.pack_start( prop_button, False, False )

        shoot_button = gtk.Button( label = "Shoot" )
        hbox.pack_start( shoot_button, False, False )

        auto_button = gtk.Button( label = "*AutoExpousure" )
        hbox.pack_start( auto_button, False, False )

        calib_button = gtk.Button( label = "*LensCalib" )
        hbox.pack_start( calib_button, False, False )

        zoom_button = gtk.Button( label = "*Zoom" )
        hbox.pack_start( zoom_button, False, False )

        self.fmt_sel = unicapgtk.VideoFormatSelection()
        hbox.pack_end( self.fmt_sel, False, False )

        self.dev_sel = unicapgtk.DeviceSelection()
        self.dev_sel.rescan()
        self.dev_sel.connect( 'unicapgtk_device_selection_changed', self.__on_device_changed )
        hbox.pack_end( self.dev_sel, False, False )

        self.display = unicapgtk.VideoDisplay()
        self.display.connect( 'unicapgtk_video_display_predisplay', self.__on_new_frame )
        self.display.set_property( "scale-to-fit", True )
        vbox.pack_start( self.display, True, True )

        self.property_dialog = unicapgtk.PropertyDialog()
        self.property_dialog.connect( 'delete-event', self.property_dialog.hide_on_delete )
        prop_button.connect( 'clicked', lambda(x): self.property_dialog.present() )
        auto_button.connect( 'clicked', self.AutoExpousure )
        shoot_button.connect( 'clicked', self.Shoot )
        self.property_dialog.hide()

        dev = unicap.enumerate_devices()[0]
        self.dev_sel.set_device( dev )
        self.fmt_sel.set_device( dev )

        vbox.show_all()

        self.set_default_size( 640, 480 )

        capture_button.set_active( True )

    def __on_device_changed(self, dev_sel, identifier ):
        self.device = self.display.set_device( identifier )
        self.property_dialog.set_device( identifier )
        self.fmt_sel.set_device( identifier )

    def __on_capture_toggled(self, button):
        if button.get_active():
            self.display.start()
        else:
            self.display.stop()

    def AutoExpousure(self, button=None):
        self.valAutoExpo = True

    def Shoot(self, button=None):
        self.valShoot = True

    def CalibExpousure(self, button=None):
        self.valCalib = True

    def __on_save_clicked(self, button):
        pixbuf = self.display.get_still_image()
        dlg = gtk.FileChooserDialog( action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                     buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_REJECT,
                                              gtk.STOCK_OK,gtk.RESPONSE_ACCEPT) )
        dlg.set_default_response( gtk.RESPONSE_ACCEPT )
        response = dlg.run()
        if response == gtk.RESPONSE_ACCEPT:
            filename = dlg.get_filename()
        if filename.endswith( '.jpg' ):
            filetype = 'jpeg'
        elif filename.endswith( '.png' ):
            filetype = 'png'
        else:
            filename += '.jpg'
            filetype = 'jpeg'
            pixbuf.save( filename, filetype )
            dlg.destroy()

    def __on_new_frame( self, display, pointer ):
        # Note: The imgbuf created with wrap_gpointer is only valid during this callback
        imgbuf = unicap.ImageBuffer.wrap_gpointer( pointer )
        width = imgbuf.format['size'][0]
        height = imgbuf.format['size'][1] 
        
        if self.valAutoExpo:
            self.valAutoExpo = False

            # Arrays to store object points and image points from all the images.
            objpoints = [] # 3d point in real world space
            imgpoints = [] # 2d points in image plane.

            image = np.fromstring(imgbuf.tostring(), np.uint8).reshape(height, width, 3)
            #img_np = cv2.imdecode(image, cv2.CV_LOAD_IMAGE_GRAYSCALE)
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            img_new =  cv2.cvtColor(gray_image, cv2.COLOR_BAYER_GR2RGB)
            cv2.imwrite("raw.jpg",image)
            cv2.imwrite("bayer.jpg",img_new)
            print "Auto Expo processed"

            
            # termination criteria
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

            # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
            objp = np.zeros((6*7,3), np.float32)
            objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)
            
            ret, corners = cv2.findChessboardCorners(gray_image, (7,6),None)

            # If found, add object points, image points (after refining them)
            print ret, corners
            if ret == True:
                objpoints.append(objp)

                corners2 = cv2.cornerSubPix(gray_image,corners,(11,11),(-1,-1),criteria)
                imgpoints.append(corners2)

                # Draw and display the corners
                img = cv2.drawChessboardCorners(img_new, (7,6), corners2,ret)
                cv2.imwrite('img.jpg',img)
                print "blaoeaoeoe"
                

            print "AutoExpousure done"
        if self.valShoot:
            self.valShoot = False
            image = np.fromstring(imgbuf.tostring(), np.uint8).reshape(height, width, 3)
            #img_np = cv2.imdecode(image, cv2.CV_LOAD_IMAGE_GRAYSCALE)
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            img_new =  cv2.cvtColor(gray_image, cv2.COLOR_BAYER_GR2RGB)
            cv2.imwrite("raw_"+time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())+".jpg",image)
            cv2.imwrite("bayer_"+time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())+".jpg",img_new)
            print "Auto Expo processed"

        # Draw a circle and a cross on the video image 
        imgbuf.draw_line( (width/2 - 50, height/2 - 50), (width/2 + 50, height/2 + 50), (255,10,10), 0 )
        imgbuf.draw_line( (width/2 + 50, height/2 - 50), (width/2 - 50, height/2 + 50), (255,10,10), 0 )
        imgbuf.draw_circle( (width/2, height/2), 50, (190,220,190) )
    

if __name__ == '__main__':
    window = AppWindow()
    window.show()

    gtk.main()