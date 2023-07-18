#!/usr/bin/env python
# coding: utf-8

# In[78]:


import os
import win32com.client
import numpy as np
import time
import h5py
import sidpy
import pyNSID
import progressbar
import matplotlib.pyplot as plt
from IPython.display import clear_output

class Acquisition():
    def __init__(self, exe_path = "G:\My Drive\AE\PyAE\BEPyAE 022823 01\BEPyAE.exe", client = "BEPyAE.Application", 
                 pyae_vi = "\BE_PyAE_01.vi", pyscanner_vi = "\FPGA PyScanner\FPGA_PyScanner_01.vi") -> None:
        """
        Initializes the Acquistion class and starts BEPyAE.exe.

        Args:
            exe_path (str): Path to the BEPyAE executable file.
            client (str): Name of the BEPyAE client.
            pyae_vi (str): Path to the BEPyAE VI.
            pyscanner_vi (str): Path to the Pyscanner VI.
        """ 

        # Start BEPyAE
        os.startfile(exe_path)

        # Wait until BEPyAE.exe starts, then set VI reference 'BEPyAE.vi'
        bepyae_not_start = True
        while bepyae_not_start:
            try:
                self.labview = win32com.client.Dispatch(client)
                self.VI = self.labview.getvireference(exe_path + pyae_vi)
                bepyae_not_start = False
            except:
                time.sleep(1)
        # Set Pyscanner vi as VIs
        if pyscanner_vi != None:
            self.VIs = self.labview.getvireference(exe_path + pyscanner_vi) 

    def init_BEPyAE(self, offline_development = False):
        """
        Initializes the connection between BEPyAE and Asylum Cypher AR.

        Args:
            offline_development (bool): Set to True for offline program development,
                                        False for microscope measurement.
        """
        # Set offline development mode
        self.VI.setcontrolvalue('offline_development_control_cluster', 
                           (offline_development,offline_development,offline_development,offline_development))
        
        # Initialize the connection between BEPyAE and Asylum Cypher AR 
        self.VI.setcontrolvalue('initialize_AR18_control_cluster', (True,))
        # Wait until initializing is done
        while self.VI.getcontrolvalue('initialize_AR18_control_cluster')[0]:
            time.sleep(0.2)

        # Note: The following lines are commented out as they are under development.
        # igor_para = self.VI.getcontrolvalue('main tab') 
        # self.AR_paras = self.VI.getcontrolvalue('initialize_AR18_indicator_cluster')
        
        return
    
    # Helf functions
    def progress_bar(self, max_value):
        """
        Creates a progress bar to track the progress of long experiments.

        Args:
            max_value (int): The maximum number of iterations.

        Returns:
            progressbar.ProgressBar: The progress bar object.
        """
        widgets = [' [',
                   progressbar.Timer(format= 'progress: %(elapsed)s'),
                   '] ', progressbar.Bar('*'),' (',progressbar.ETA(), ') ',]
        bar = progressbar.ProgressBar(max_value=max_value, widgets=widgets).start()
        return bar
 
    def convert_coordinates(self, original_coordinates=None, num_pix_x = 128, num_pix_y = 128, start_x = -1, finish_x = 1, start_y = -1, finish_y = 1):
        """
        Converts 2D space coordinates to the parameters of microscopy probe location.

        Args:
            original_coordinates (numpy.ndarray): Array representing the original coordinates in a 2D space.
            start_x (float or int): Start value of the X-axis in the target coordinate space. Default is -1.
            finish_x (float or int): Finish value of the X-axis in the target coordinate space. Default is 1.
            start_y (float or int): Start value of the Y-axis in the target coordinate space. Default is -1.
            finish_y (float or int): Finish value of the Y-axis in the target coordinate space. Default is 1.

        Returns:
            numpy.ndarray: Array representing the converted parameters of probe location.

        Notes:
            - The original_coordinates should be a numpy array of shape [2] with the first element representing Y-coordinate
              and the second element representing X-coordinate.
        """

        original_coordinates = np.asarray(original_coordinates, dtype = np.float64()) # convert to int to float first

        coor_x = original_coordinates [1]
        coor_y = original_coordinates [0]
        # rescale the data to be symmetric around 0
        convert_x = (coor_x - (num_pix_x/2)) / (num_pix_x)
        convert_y = (coor_y - (num_pix_y/2)) / (num_pix_y)
    
        # shift and scale it to the scan range
        convert_x = convert_x * (finish_x - start_x) + (finish_x + start_x) / 2
        convert_y = convert_y * (finish_y - start_y) + (finish_y + start_y) / 2
        
        # write converted locations
        converted_locations = np.copy(original_coordinates)
        converted_locations[1] = convert_x
        converted_locations[0] = convert_y
    
        return converted_locations

    def mk_dset(self, file_name, pfm_imgstack, channel_imgstack, complex_spectra,
                start_x, finish_x, start_y, finish_y, coordinates = None, beps = False):
        """
        Creates an H5 file to save band excitation data.

        Args:
            file_name (str): Customized H5 file name.
            pfm_imgstack (numpy.ndarray): Array containing all band excitation PFM image channels.
            channel_imgstack (numpy.ndarray): Array containing all images from customized channels.
            complex_spectra (numpy.ndarray): List containing the band excitation raw spectra.
            start_x (float or int): Start value of the X-axis for microscopy measurement locations.
            finish_x (float or int): Finish value of the X-axis for microscopy measurement locations.
            start_y (float or int): Start value of the Y-axis for microscopy measurement locations.
            finish_y (float or int): Finish value of the Y-axis for microscopy measurement locations.
            coordinates (numpy.ndarray, optional): Array representing where BEPS measurements were performed. Defaults to None.
            beps (bool, optional): Indicates whether the data to save is BEPS data. Defaults to False.

        Returns:
            sidpy datasets: If beps is False, returns sidpy datasets of BEPFM images, channel images, and BE complex spectra.
                            If beps is True, returns sidpy datasets of beps wavefrom, beps hyperimages, channel images, and BE complex spectra.
        """

        # Note: The following lines are commented out as they are under development.
        # scan_size_x = self.AR_paras[1][1]
        # scan_size_y = self.AR_paras[1][2]
        scan_size_x = 10e-6
        scan_size_y = 10e-6
        len_x = np.abs(finish_x - start_x)
        len_y = np.abs(finish_y - start_y)

        # Quick fitting PFM images
        dset_imgs = sidpy.Dataset.from_array(pfm_imgstack, title = 'be stack')
        dset_imgs.data_type = 'image_stack'
        dset_imgs.quantity = 'quick fit pfm'

        dset_imgs.set_dimension(0, sidpy.Dimension(np.linspace(0, 1, dset_imgs.shape[0])*(scan_size_y*len_y)/2,
                                name = "y axis", units = "m", quantity = "y axis", dimension_type = "spatial"))
        dset_imgs.set_dimension(1, sidpy.Dimension(np.linspace(0, 1, dset_imgs.shape[1])*(scan_size_x*len_x)/2,
                                name = "x axis", units = "m", quantity = "x axis", dimension_type = "spatial"))
        dset_imgs.set_dimension(2, sidpy.Dimension(np.arange(dset_imgs.shape[2]), 
                                name = "BE responses", quantity = "channels", dimension_type = "frame"))
        
        # Channel images
        dset_chns = sidpy.Dataset.from_array(channel_imgstack, title = 'channel stack')
        dset_chns.data_type = 'image_stack'
        dset_chns.quantity = 'channels'

        dset_chns.set_dimension(0, sidpy.Dimension(np.linspace(0, 1, dset_chns.shape[0])*(scan_size_y*len_y)/2,
                                name = "y axis", units = "m", quantity = "y axis", dimension_type = "spatial"))
        dset_chns.set_dimension(1, sidpy.Dimension(np.linspace(0, 1, dset_chns.shape[1])*(scan_size_x*len_x)/2,
                                name = "x axis", units = "m", quantity = "x axis", dimension_type = "spatial"))
        dset_chns.set_dimension(2, sidpy.Dimension(np.arange(dset_chns.shape[2]), 
                                name = "channels images", quantity = "channels", dimension_type = "frame"))

        # Complex spectra
        complex_spectra_arr = np.asarray(complex_spectra)
        # complex_spectra_arr = complex_spectra_arr.reshape((imgstack.shape[0], imgstack.shape[1], -1, 2))

        dset_complex_spectra = sidpy.Dataset.from_array(complex_spectra_arr[...,0] + 1j*complex_spectra_arr[...,1], title = 'complex_spectra')
        dset_complex_spectra.quantity = 'pfm complex spectra'
        dset_complex_spectra.units = 'V'

        dset_complex_spectra.set_dimension(0, sidpy.Dimension(np.arange(pfm_imgstack.shape[0])*(pfm_imgstack.shape[1]),
                                            name = 'location index y', quantity = 'index ', dimension_type = 'spatial'))

        dset_complex_spectra.set_dimension(1, sidpy.Dimension(np.arange(dset_complex_spectra.shape[1]),
                                            name = 'location index x', units = 'Hz',quantity = 'index',dimension_type = 'spatial'))

        # Create H5 file to write data
        suf = 0
        save_name = "{}_{}.hf5".format(file_name, suf)
        # Update suffex if a file with the same name already exists
        while os.path.exists(save_name):
            suf += 1
            save_name = "{}_{}.hf5".format(file_name, suf)

        hf = h5py.File(save_name, 'a')

        # Save BE pulse parameters
        beparms = self.VI.getcontrolvalue('BE_pulse_control_cluster')
        hf['BE Parameters/pulse parameters'] = np.asarray(beparms)

        # Frequency spectral
        fft_fres = np.asarray(self.VI.getcontrolvalue('BE_pulse_parm_indicator_cluster')[6])
        fft_bin_idx = np.asarray(self.VI.getcontrolvalue('BE_pulse_parm_indicator_cluster')[3])
        fre_arr = fft_fres[fft_bin_idx]
        hf['BE Parameters/frequency'] = np.asarray(fre_arr)

        # Image size
        img_size = np.asarray([(dset_imgs.shape[0])*(scan_size_y*len_y)/2, (dset_imgs.shape[1])*(scan_size_x*len_x)/2])
        hf['BE Parameters/scan size'] = img_size

        # For BEPS data, save DC waveform as well
        if beps == True:
            vec_dc = self.VI.getcontrolvalue("BEPS_VS_indicator_cluster")[0]
            vec_dc = np.asarray(vec_dc)
            hf['BEPS/vdc_waveform'] = vec_dc
            hf['BEPS/coordinates'] = coordinates

        # Save quick fitting images
        hf.create_group("BE Quick Fitting") 
        pyNSID.hdf_io.write_nsid_dataset(dset_imgs, hf['BE Quick Fitting'], main_data_name="Quick Fitting")

        # Save channel images
        hf.create_group("BE Channels") 
        pyNSID.hdf_io.write_nsid_dataset(dset_chns, hf['BE Channels'], main_data_name="Channels")
        
        # Save complex spectral
        hf.create_group("BE Complex Spectra") 
        pyNSID.hdf_io.write_nsid_dataset(dset_complex_spectra, hf['BE Complex Spectra'], main_data_name="Complex Spectra")

        hf.close()

        if beps == False:
            return dset_imgs, dset_chns, dset_complex_spectra
        elif beps == True:
            return vec_dc, dset_imgs, dset_chns, dset_complex_spectra

    def tip_control(self, tip_parms_dict=None, do_move_tip = True, do_set_setpoint = True, feedbackon = True):
        """
        Sets tip control parameters.

        Args:
            tip_parms_dict (dict, optional): Dictionary of tip control parameters. Default is None.
                                            Example: tip_parms_dict = {"set_point_V_00": 1, "next_x_pos_00": 0.5, "next_y_pos_01": 0.5, "transit_time_s_02": 1}
                                            Range of next_x_pos_00 and next_y_pos_00 is from -1 to 1.
            do_move_tip (bool, optional): Indicates whether to perform the tip movement. Default is True.
            do_set_setpoint (bool, optional): Indicates whether to set the setpoint. Default is True.
            feedbackon (bool, optional): Indicates whether to print feedback on setpoint and tip parameters. Default is True.

        Returns:
            None

        Notes:
            - The function sets tip control parameters based on the provided tip_parms_dict.
            - If tip_parms_dict is None, the function uses default values shown in the BEPyAE.exe.
            - The tip control parameters include set_point_V_00, next_x_pos_00, next_y_pos_01, and transit_time_s_02.
            - If do_move_tip is False, the tip movement is skipped.
            - If do_set_setpoint is False, the setpoint is not set.
            - If feedbackon is True, the function prints the setpoint and tip parameters.
        """

        # Read current parameters
        default_setpoint_cluster = self.VI.getcontrolvalue('set_setpoint_control_cluster')  # get setpoint value
        default_move_tip_cluster = self.VI.getcontrolvalue('move_tip_control_cluster')  # get tip control parameters

        # Set default values for tip control parameters
        tip_parms_list = [default_setpoint_cluster[0], default_move_tip_cluster[0], default_move_tip_cluster[1], default_move_tip_cluster[2]]
        
        tip_parms_name_list = ["set_point_V_00", "next_x_pos_00", "next_y_pos_01", "transit_time_s_02"]
        
        # if user customized some parameters, set the parameters as customized values
        if tip_parms_dict != None:
            for i in range (len (tip_parms_list)):
                if tip_parms_name_list[i] in tip_parms_dict:
                    tip_parms_list[i] = tip_parms_dict[tip_parms_name_list[i]]
        
        # Set tip parameters.  
        # if we set 'do_set_setpoint_01' and 'do_move_tip_03' to "False", 
        # # we will only input above parameters into PyAE but do not perform the actions
        self.VI.setcontrolvalue('set_setpoint_control_cluster', 
                                (tip_parms_list[0], do_set_setpoint))
        # wait until set setpoint is done
        while self.VI.getcontrolvalue("set_setpoint_control_cluster")[1]:
            time.sleep(0.1)

        self.VI.setcontrolvalue('move_tip_control_cluster', 
                                (tip_parms_list[1], 
                                 tip_parms_list[2], 
                                 tip_parms_list[3],
                                 do_move_tip))
        
        # wait until tip move is done
        while self.VI.getcontrolvalue('move_tip_control_cluster')[3]:
            time.sleep(0.1)  # Wait 0.1 s and check if action is done again

        # Print feedback on setpoint and tip parameters if feedbackon is True
        if feedbackon == True:
            # return setpoint
            setpoint_parms = self.VI.getcontrolvalue('set_setpoint_control_cluster')
            print("Setpoint is: ", setpoint_parms[0])
            # return move tip parameter
            move_tip_parms = self.VI.getcontrolvalue('move_tip_control_cluster')
            print("Tip parameters are: ", move_tip_parms[:-1])

        return

    def define_io_cluster (self, IO_cluster_parms_dict = None, do_set_IO = True, feedbackon = True):
        """
        Sets the IO Cluster parameters related to the hardware and software in the experiments.

        Args:
            IO_cluster_parms_dict (dict, optional): Dictionary of IO cluster parameters. Default is None.
                                                    Example: IO_cluster_parms_dict = {"AFM_platform_00": 0, "DAQ_card_01": 0,
                                                                                      "IO_rate_02": 0, "analog_input_range_03": 0,
                                                                                      "analog_output_range_04": 0, "analog_output_routing_05": 0,
                                                                                      "analog_output_amplifier_06": 0, "channel_01_type_07": 1,
                                                                                      "channel_02_type_08": 2, "channel_03_type_09": 3,
                                                                                      "IO_trigger_ring_10": 0}
                                                    Default parameters are the ones shown in the BEPyAE.exe IO_Control_cluster panel now.
           do_set_IO (bool, optional): Indicates whether to set the IO cluster. Default is True.
           feedbackon (bool, optional): Indicates whether to return the IO parameters. Default is True.

        Returns:
           If feedbackon is True, the function returns the IO parameters.
           If feedbackon is False, the function returns None.

        Notes:
           - The function sets the IO Cluster parameters based on the provided IO_cluster_parms_dict.
           - If IO_cluster_parms_dict is None, the function uses default values shown in the BEPyAE.exe.
           - If do_set_IO is False, the IO cluster is not set.
           - If feedbackon is True, the function returns the IO parameters obtained from the IO_indicator_cluster.
        """

        # Read current values in BEPyAE.exe
        default_io_cluster = self.VI.getcontrolvalue('IO_control_cluster')
        
        # Set default values for IO cluster parameters
        IO_cluster_parms_list = [default_io_cluster[0], default_io_cluster[1], default_io_cluster[2],
                                 default_io_cluster[3], default_io_cluster[4], default_io_cluster[5],
                                 default_io_cluster[6], default_io_cluster[7], default_io_cluster[8],
                                 default_io_cluster[9], default_io_cluster[10]]
        IO_cluster_parms_name_list = ["AFM_platform_00", "DAQ_card_01", "IO_rate_02", 
                                      "analog_input_range_03", "analog_output_range_04",
                                      "analog_output_routing_05", "analog_output_amplifier_06", 
                                      "channel_01_type_07", "channel_02_type_08", 
                                      "channel_03_type_09", "IO_trigger_ring_10"]
        
        # If user customized some parameters, update the parameters as customized values
        if IO_cluster_parms_dict != None:
            for i in range (len (IO_cluster_parms_list)):
                if IO_cluster_parms_name_list[i] in IO_cluster_parms_dict:
                    IO_cluster_parms_list[i] = IO_cluster_parms_dict[IO_cluster_parms_name_list[i]]

        # Set IO cluster 
        self.VI.setcontrolvalue('IO_control_cluster', 
                                (IO_cluster_parms_list[0], IO_cluster_parms_list[1], 
                                 IO_cluster_parms_list[2], IO_cluster_parms_list[3], 
                                 IO_cluster_parms_list[4], IO_cluster_parms_list[5], 
                                 IO_cluster_parms_list[6], IO_cluster_parms_list[7],
                                 IO_cluster_parms_list[8], IO_cluster_parms_list[9], 
                                 IO_cluster_parms_list[10], do_set_IO))
        
        # Return IO parameters or None based on feedbackon
        # Get IO parameters if feedbackon is True
        if feedbackon == True:
            IO_parms = self.VI.getcontrolvalue('IO_indicator_cluster')
            return IO_parms
        else:
            return
        
    
    def define_be_parms(self, be_parms_dict=None, do_create_be_waveform = True, feedbackon = True):
        """
        Define the parameters for the Band Excitation (BE) pulse.

        Args:
            be_parms_dict (dict, optional): Dictionary of BE parameters. Default is None.
                                            Example: be_parms_dict = {"center_frequency_Hz_00": 350, "band_width_Hz_01": 100,
                                                                      "amplitude_V_02": 1, "phase_variation_03": 1, "repeats_04": 4,
                                                                      "req_pulse_duration_s_05": 4, "auto_smooth_ring_06": 1}
                                            If be_parms_dict is None, the function uses default values shown in BE_pulse_control_cluster panel.
                                            Note that the unit for frequency is kHz and for time is ms.
            do_create_be_waveform (bool, optional): Indicates whether to create the BE waveform. Default is True. If do_create_be_waveform is False, only the parameters are inputted into BEPyAE without creating the waveform
            feedbackon (bool, optional): Indicates whether to return the BE parameters. Default is True.

        Returns:
            If feedbackon is True, the function returns the BE parameters obtained from the BE_pulse_control_cluster.
            If feedbackon is False, the function returns None.
        """ 
        # Read default values for BE parameters
        default_be_cluster = self.VI.getcontrolvalue('BE_pulse_control_cluster')
        
        # Set default values for BE parameters
        be_parms_list = [default_be_cluster[0]/1000, default_be_cluster[1]/1000, default_be_cluster[2],
                         default_be_cluster[3], default_be_cluster[4], default_be_cluster[5]*1000,
                         default_be_cluster[6], default_be_cluster[7]/1000, default_be_cluster[8]*1000]
        be_parms_name_list = ["center_frequency_Hz_00", "band_width_Hz_01", "amplitude_V_02", 
                              "phase_variation_03", "repeats_04", "req_pulse_duration_s_05",
                              "auto_smooth_ring_06", "edge_smoothing_Hz_07", "window_adjustment_08"]
        
        # If user customized some parameters, set the parameters as customized values
        if be_parms_dict != None:
            for i in range (len (be_parms_list)):
                if be_parms_name_list[i] in be_parms_dict:
                    be_parms_list[i] = be_parms_dict[be_parms_name_list[i]]
 
        # Set BE parameters. Here each variable was set above. "True" is 'do_create_BE_waveform', 
        # if we set 'do_create_BE_waveform' to "False", we will only input above parameters into PyAE
        self.VI.setcontrolvalue('BE_pulse_control_cluster', 
                                ((be_parms_list[0])*1000, 
                                 (be_parms_list[1])*1000, 
                                 be_parms_list[2],
                                 be_parms_list[3], be_parms_list[4], 
                                 (be_parms_list[5])/1000, 
                                 be_parms_list[6], 
                                 (be_parms_list[7])*1000, 
                                 (be_parms_list[8])/1000, do_create_be_waveform))
        
        # Get BE pulse cluster. We can get (and save) BE pulse parameters for post measurement analysis
        if feedbackon == True:
            time.sleep(0.5)
            be_parms = self.VI.getcontrolvalue('BE_pulse_control_cluster')
            print("BE parameters are: ", be_parms[:-1])
            return 
        else:
            return

    def define_apply_pulse(self, pulse_parms_dict = None, 
                           do_create_pulse = True, do_upload_pulse = True, do_apply_pulse = True):
        """
        Apply a DC pulse waveform with the specified parameters. The function performs the following steps:
            1. Sets the pulse parameters and create the pulse waveform.
            2. Upload the created pulse waveform to DAQ card.
            3. Applies the pulse waveform.

        Args:
            pulse_parms_dict (dict, optional): Dictionary of DC pulse parameters. Default is None.
                                               Example: pulse_parms_dict = {"pulse_init_amplitude_V_00": 0,
                                                                          "pulse_mid_amplitude_V_01": 3,
                                                                          "pulse_final_amplitude_V_02": 0,
                                                                          "pulse_on_duration_s_03": 30E-6,
                                                                          "pulse_final_duration_s_04": 10E-6,
                                                                          "rise_time_s_05": 1E-6,
                                                                          "pulse_repeats_06": 3}
                                               Default parameters are the values shown on the panel now. 
                                               If pulse_parms_dict is None, the function uses default values shown on the voltage_pulse_contro_cluster panel.
           do_create_pulse (bool, optional): Indicates whether to create the pulse waveform. Default is True.
           do_upload_pulse (bool, optional): Indicates whether to upload the pulse waveform to DAQ card. Default is True.
           do_apply_pulse (bool, optional): Indicates whether to apply the pulse waveform. Default is True.

        Returns:
           The function returns two numpy array containing the pulse waveform values and corresponding time array.

        """
        # Get default values
        default_pulse_parms = self.VI.getcontrolvalue("voltage_pulse_control_cluster")

        pulse_parms_list = [default_pulse_parms[0], default_pulse_parms[1],
                            default_pulse_parms[2], default_pulse_parms[3], 
                            default_pulse_parms[4], default_pulse_parms[5],
                            default_pulse_parms[6]]
        pulse_parms_name_list = ['pulse_init_amplitude_V_00', 'pulse_mid_amplitude_V_01',
                                 'pulse_final_amplitude_V_02', 'pulse_on_duration_s_03', 
                                 'pulse_final_duration_s_04', 'rise_time_s_05',
                                 'pulse_repeats_06']
        # if user customized some parameters, set the parameters as customized values
        if pulse_parms_dict != None:
            for i in range (len (pulse_parms_list)):
                if pulse_parms_name_list[i] in pulse_parms_dict:
                    pulse_parms_list[i] = pulse_parms_dict[pulse_parms_name_list[i]]
        
        ## Set pulse control value
        self.VI.setcontrolvalue('voltage_pulse_control_cluster', 
                                (pulse_parms_list[0], pulse_parms_list[1], pulse_parms_list[2],
                                 pulse_parms_list[3], pulse_parms_list[4], pulse_parms_list[5],
                                 pulse_parms_list[6], do_create_pulse, False, False))
        ## Wait until pulse is created
        while self.VI.getcontrolvalue('voltage_pulse_control_cluster')[7]:
            time.sleep(0.1) # wait 0.1 s and check status again

        ## Upload pulse
        self.VI.setcontrolvalue('voltage_pulse_control_cluster', 
                                (pulse_parms_list[0], pulse_parms_list[1], pulse_parms_list[2],
                                 pulse_parms_list[3], pulse_parms_list[4], pulse_parms_list[5],
                                 pulse_parms_list[6], False, do_upload_pulse, False))
        ## Wait until pulse is uploaded
        while self.VI.getcontrolvalue('voltage_pulse_control_cluster')[8]:
            time.sleep(0.1) # wait 0.1 s and check status again

        time.sleep(1)
        
        ## Upload pulse 2
        self.VI.setcontrolvalue('voltage_pulse_control_cluster', 
                                (pulse_parms_list[0], pulse_parms_list[1], pulse_parms_list[2],
                                 pulse_parms_list[3], pulse_parms_list[4], pulse_parms_list[5],
                                 pulse_parms_list[6], False, do_upload_pulse, False))
        ## Wait until pulse is uploaded
        while self.VI.getcontrolvalue('voltage_pulse_control_cluster')[8]:
            time.sleep(0.1) # wait 0.1 s and check status again

        ## Apply pulse
        self.VI.setcontrolvalue('voltage_pulse_control_cluster', 
                                (pulse_parms_list[0], pulse_parms_list[1], pulse_parms_list[2],
                                 pulse_parms_list[3], pulse_parms_list[4], pulse_parms_list[5],
                                 pulse_parms_list[6], False, False, do_apply_pulse))
        ## Wait until pulse is created
        while self.VI.getcontrolvalue('voltage_pulse_control_cluster')[9]:
            time.sleep(0.1) # wait 0.1 s and check status again
        
        # Get the pulse wave data
        pulse_wave = self.VI.getcontrolvalue("voltage_pulse_parm_indicator_cluster")
        pulse_value = np.asarray(pulse_wave[0])
        pulse_time = np.linspace(0, pulse_wave[2], int(pulse_wave[1]))
        return pulse_value, pulse_time
    
    def do_line_scan(self, line_scan_parms_dict = None, upload_to_daq = False, do_line_scan = False, feedbackon = True):
        """
        Perform a single band excitation (BE) line scan measurement.
        The function performs the following steps:
            1. Sets the BE pulse number (i.e., pixel) and offset voltage and upload it to DAQ card if upload_to_daq is True.
            3. Sets the BE line scan position parameters and perform line scan if do_BE_line_scan_04 is true.

        Args:
            line_scan_parms_dict (dict, optional): Dictionary of BE line scan parameters. Default is None.
                                                    Example: line_scan_parms_dict = {"voltage_offest_V_00": 0,
                                                                                     "num_BE_pulse_01": 128,
                                                                                     "start_x_pos_00": 0,
                                                                                     "start_y_pos_01": 0,
                                                                                     "stop_x_pos_02": 1,
                                                                                     "stop_y_pos_03": 0}
                                                    Default parameters are the values shown on BEPyAE.exe initialize_BE_line_scan_control_cluster and BE_line_scan_control_cluster panel now.
                                                    If line_scan_parms_dict is None, the function uses default values shown on the panel.
            upload_to_daq (bool, optional): Indicates whether to upload the line scan waveform to the DAQ card. Default is False.
            do_line_scan (bool, optional): Indicates whether to perform the line scan measurement. Default is False.
            feedbackon (bool, optional): Indicates whether to print line scan parameters. Default is True.

        Returns:
            The function returns three lists containing the complex spectrogram, SHO Quick Fitting, and channel data (channel1, channel2, channel3) obtained from the BE line scan measurement.

        """
        # Get default values
        default_line_scan_parms_1 = self.VI.getcontrolvalue("Initialize_BE_line_scan_control_cluster")
        default_line_scan_parms_2 = self.VI.getcontrolvalue("BE_line_scan_control_cluster")
        
        # Set default values
        linescan_parms_list = [default_line_scan_parms_1[0], default_line_scan_parms_1[1], default_line_scan_parms_2[0], 
                               default_line_scan_parms_2[1], default_line_scan_parms_2[2], default_line_scan_parms_2[3]]
        linescan_parms_name_list = ["voltage_offest_V_00", "num_BE_pulses_01", "start_x_pos_00",
                                    "start_y_pos_01", "stop_x_pos_02", "stop_y_pos_03"]
        
        # if user customized some parameters, set the parameters as customized values
        if line_scan_parms_dict != None:
            for i in range (len (linescan_parms_list)):
                if linescan_parms_name_list[i] in line_scan_parms_dict:
                    linescan_parms_list[i] = line_scan_parms_dict[linescan_parms_name_list[i]]
        
        if upload_to_daq == True:
            ## Set line scan control cluster
            self.VI.setcontrolvalue('Initialize_BE_line_scan_control_cluster', 
                                    (linescan_parms_list[0], linescan_parms_list[1], upload_to_daq))
            # Wait until linescan waveform is uploaded to daq card
            while self.VI.getcontrolvalue('Initialize_BE_line_scan_control_cluster')[2]:
                time.sleep(0.1) # wait 0.1 s and check the status again

            time.sleep(2)    
        
            ## Set line scan control cluster
            self.VI.setcontrolvalue('Initialize_BE_line_scan_control_cluster', 
                                    (linescan_parms_list[0], linescan_parms_list[1], upload_to_daq))
            # Wait until linescan waveform is uploaded to daq card
            while self.VI.getcontrolvalue('Initialize_BE_line_scan_control_cluster')[2]:
                time.sleep(0.1) # wait 0.1 s and check the status again
        

        ## Set BE line scan control cluster
        self.VI.setcontrolvalue('BE_line_scan_control_cluster', 
                                (linescan_parms_list[2], linescan_parms_list[3], 
                                 linescan_parms_list[4], linescan_parms_list[5],
                                 do_line_scan))
        # Wait until linescan is finished
        while self.VI.getcontrolvalue('BE_line_scan_control_cluster')[4]:
            time.sleep(0.1) # wait 0.1 s and check the status again
        
        # feedback about parameters
        if feedbackon == True:
            line_scan_parms_1 = self.VI.getcontrolvalue('Initialize_BE_line_scan_control_cluster')
            line_scan_parms_2 = self.VI.getcontrolvalue('BE_line_scan_control_cluster')
            print ("voltage offset and number of BE pulse are: ", line_scan_parms_1[:-1])
            print ("line scan start and end positions: ", line_scan_parms_2[:-1])

        ## Get BE line data
        be_line_result = self.VI.getcontrolvalue("BE_line_scan_indicator_cluster")
        complex_spectrogram = be_line_result[1]
        sho_guess_cluster = be_line_result[3]
        channel1 = be_line_result[4]
        channel2 = be_line_result[5]
        channel3 = be_line_result[6]

        return complex_spectrogram, sho_guess_cluster, channel1, channel2, channel3  #return raw data and quick fitting

    def raster_scan(self, file_name = "BEPFM", raster_parms_dict = None,
                    feedbackon = False, progress_on = True, ploton = True):
        """
        Perform a raster BE scan

        Args:
            file_name (str): Name of the H5 file to save the scan data.
            raster_parms_dict (dict): Dictionary of BE raster scan parameters.
                Default: None (default parameters shown in BEPyAE.exe Initialize_BE_line_scan_control_cluster and BE_line_scan_control_cluster panels are used).
                Example: {"tip_voltage": 0, "scan_pixel": 128, "scan_x_start": -1,
                          "scan_y_start": -1, "scan_x_stop": 1, "scan_y_stop": 1}
            feedbackon (bool): Flag to enable/disable feedback during the scan. Default is False (feedback is disabled).
            progress_on (bool): Flag to enable/disable progress bar display. Default is True (progress bar is displayed).
            ploton (bool): Flag to enable/disable real-time image plotting. Default is True (plots are displayed).

        Returns:
            Three sidpy datasets containing below data:
            - dset_imgs: PFM images.
            - dset_chns: channel images.
            - complex_spectra: complex spectra.

        """
        # Get default value
        line_scan_parms_1 = self.VI.getcontrolvalue("Initialize_BE_line_scan_control_cluster")
        line_scan_parms_2 = self.VI.getcontrolvalue("BE_line_scan_control_cluster")

        # Set default parameters
        raster_parms_name_list = ["tip_voltage", "scan_pixel", "scan_x_start", "scan_y_start", "scan_x_stop", "scan_y_stop"]
        raster_parms_list = [line_scan_parms_1[0], line_scan_parms_1[1], line_scan_parms_2[0], 
                             line_scan_parms_2[1], line_scan_parms_2[2], line_scan_parms_2[3]]

         # if user customized some parameters, set the parameters as customized values
        if raster_parms_dict !=None:
            for i in range (len (raster_parms_list)):
                if raster_parms_name_list[i] in raster_parms_dict:
                    raster_parms_list[i] = raster_parms_dict[raster_parms_name_list[i]]

        raster_quick_fit = []
        raster_channel1 = []
        raster_channel2 = []
        raster_channel3 = []
        raster_complex_spectra = []

        scan_line_array = np.linspace(raster_parms_list[3], raster_parms_list[5], raster_parms_list[1])
        # Move tip to start position
        self.tip_control(tip_parms_dict = {"next_x_pos_00": raster_parms_list[2], 
                                           "next_y_pos_01": scan_line_array[0]}, feedbackon = feedbackon)

        # Upload BE excitation waveform to DAQ
        self.do_line_scan(line_scan_parms_dict = {"voltage_offset_V_00": raster_parms_list[0], 
                                                  "num_BE_pulses_01": raster_parms_list[1]},
                                                  upload_to_daq = True, feedbackon = feedbackon)
        # Wait until waveform is uploaded to DAQ
        while self.VI.getcontrolvalue('Initialize_BE_line_scan_control_cluster')[2]:
            time.sleep(0.1) # wait 0.1 s and check the status again 
        
        # Create a progress bar
        if progress_on:
            bar_progress = self.progress_bar(int(raster_parms_list[1]))  
        for i in range(int(raster_parms_list[1])):
            # Move tip to strat pos
            self.tip_control(tip_parms_dict = {"next_x_pos_00": raster_parms_list[2], 
                                               "next_y_pos_01": scan_line_array[i], 
                                               "transit_time_s_02": 0.5}, do_set_setpoint = False, feedbackon = feedbackon)
            # Wait until tip move is done
            while self.VI.getcontrolvalue('move_tip_control_cluster')[3]:
                time.sleep(0.1)  # Wait 0.1 s and check if action is done again
            
            # Perform line scan at the current position
            line_cx_spectra, line_quick_fit, line_channel1, line_channel2, line_channel3= self.do_line_scan(
                line_scan_parms_dict = {"start_x_pos_00": raster_parms_list[2],
                                        "start_y_pos_01": scan_line_array[i], "stop_x_pos_02": raster_parms_list[4],
                                        "stop_y_pos_03": scan_line_array[i]}, do_line_scan = True, feedbackon = feedbackon)
            
            # Store the scan data
            raster_quick_fit.append(np.asarray(line_quick_fit))
            raster_channel1.append(line_channel1)
            raster_channel2.append(line_channel2)
            raster_channel3.append(line_channel3)
            raster_complex_spectra.append(np.asarray(line_cx_spectra))

            # plot real time images
            if ploton == True:
                if i%5 == 0:
                    clear_output(wait=True)
                    fig, axs = plt.subplots(1, 7, figsize=(28, 4))
                    fig.subplots_adjust(left=0.02, bottom=0.06, right=0.95, top=0.94, wspace=0.2)
                    cm = 'viridis'
                    shrink = 0.8
                    # channel 1
                    im0 = axs[0].imshow(np.asarray(raster_channel1), interpolation='nearest', cmap=cm)
                    fig.colorbar(im0, ax=axs[0], shrink = shrink, label = "Channel 1 (a.u.)")
                    axs[0].axis('off')
                    # channel 2
                    im1 = axs[1].imshow(np.asarray(raster_channel2), interpolation='nearest', cmap=cm)
                    fig.colorbar(im1, ax=axs[1], shrink = shrink, label = "Channel 2 (a.u.)")
                    axs[1].axis('off')
                    # channel 3
                    im2 = axs[2].imshow(np.asarray(raster_channel3), interpolation='nearest', cmap=cm)
                    fig.colorbar(im2, ax=axs[2], shrink = shrink, label = "Channel 3 (a.u.)")
                    axs[2].axis('off')
                    # amplitude
                    im3 = axs[3].imshow((np.asarray(raster_quick_fit))[:,:,0], interpolation='nearest', cmap=cm)
                    fig.colorbar(im3, ax=axs[3], shrink = shrink, label = "Amplitude (a.u.)")
                    axs[3].axis('off')
                    # frequency
                    im4 = axs[4].imshow(((np.asarray(raster_quick_fit))[:,:,1])/1000, interpolation='nearest', cmap=cm)
                    fig.colorbar(im4, ax=axs[4], shrink = shrink, label = "Frequency (kHz)")
                    axs[4].axis('off')
                    # q factor
                    im5 = axs[5].imshow((np.asarray(raster_quick_fit))[:,:,2], interpolation='nearest', cmap=cm)
                    fig.colorbar(im5, ax=axs[5], shrink = shrink, label = "Q factor (a.u.)")
                    axs[5].axis('off')
                    # phase
                    im6 = axs[6].imshow((np.asarray(raster_quick_fit))[:,:,3], interpolation='nearest', cmap=cm)
                    fig.colorbar(im6, ax=axs[6], shrink = shrink, label = "Phase (rad)")
                    axs[6].axis('off')
                    plt.show()

            # update progress
            if progress_on:
                bar_progress.update(i)
        # Create datasets and return scan data
        dset_imgs, dset_chns, complex_spectra = self.mk_dset(file_name = file_name, 
                                                             pfm_imgstack = np.asarray(raster_quick_fit),
                                                             channel_imgstack = np.asarray([raster_channel1, raster_channel2, raster_channel3]),
                                                             complex_spectra = np.asarray(raster_complex_spectra),
                                                             start_x = raster_parms_list[2], finish_x = raster_parms_list[4],
                                                             start_y = raster_parms_list[3], finish_y = raster_parms_list[5])

        return dset_imgs, dset_chns, complex_spectra
    

    def define_BEPS_parameters(self, beps_parms_dict = None, do_create_waveform = False, 
                               do_upload_waveform = False, do_VS_waveform = False, feedbackon = True):
        """
        Define band excitation piezoresponse spectroscopy measurement parameters. 
        beps_parms_dict: dictionary of BEPS measurement parameters
        e.g., beps_parms_dict = {"amplitude_V_00": 8, "offset_V_01": 0, "read_voltage_V_02": 0, "step_per_cycle_03": 64,
                                "num_cycles_04": 3, "cycle_fraction_05": 0, "cycle_phase_shift_06": 0, "measure_loops_07": 0,
                                "transition_time_s_08": 1E-6, "delay_after_step_s_09": 0, "set_pulse_amplitude_V_10": 0, 
                                "set_pulse_duration_s_11": 0, "FORC_num_cycles_12": 1, "FORC_A1_V_13: 7", "FORC_A2_V_14": 8,
                                "FORC_num_repeats_15": 0, "FORC_B1_V_16": -7, "FORC_B2_V_17": -8}
        Default parameters are the parameters shown in the BEPyAE.exe initialize_BEPS_VS_control_cluster panel.
        do_create_waveform: create a waveform; do_upload_waveform: upload waveform to DAQ; do_VS_waveform: output waveform  
        """
        # Get default parameters
        default_beps_parms = self.VI.getcontrolvalue("Initialize_BEPS_VS_control_cluster")
        
        # Set default parameters
        beps_parms_list = [default_beps_parms[0], default_beps_parms[1], default_beps_parms[2], default_beps_parms[3],
                           default_beps_parms[4], default_beps_parms[5], default_beps_parms[6], default_beps_parms[7],
                           default_beps_parms[8], default_beps_parms[9], default_beps_parms[10], default_beps_parms[11], 
                           default_beps_parms[12], default_beps_parms[13], default_beps_parms[14], default_beps_parms[15],
                           default_beps_parms[16], default_beps_parms[17]]
        beps_parms_name_list = ["amplitude_V_00", "offset_V_01", "read_voltage_V_02", "step_per_cycle_03",
                                "num_cycles_04", "cycle_fraction_05", "cycle_phase_shift_06", "measure_loops_07",
                                "transition_time_s_08", "delay_after_step_s_09", "set_pulse_amplitude_V_10", 
                                "set_pulse_duration_s_11", "FORC_num_cycles_12", "FORC_A1_V_13", "FORC_A2_V_14",
                                "FORC_num_repeats_15", "FORC_B1_V_16", "FORC_B2_V_17"] 
        # if user customized some parameters, set the parameters as customized values
        if beps_parms_dict != None:
            for i in range (len (beps_parms_list)):
                if beps_parms_name_list[i] in beps_parms_dict:
                    beps_parms_list[i] = beps_parms_dict[beps_parms_name_list[i]]

        ## Set BEPS control cluster
        self.VI.setcontrolvalue('Initialize_BEPS_VS_control_cluster', 
                                (beps_parms_list[0], beps_parms_list[1], beps_parms_list[2], beps_parms_list[3], 
                                 beps_parms_list[4], beps_parms_list[5], beps_parms_list[6], beps_parms_list[7], 
                                 beps_parms_list[8], beps_parms_list[9], beps_parms_list[10], beps_parms_list[11],
                                 beps_parms_list[12], beps_parms_list[13], beps_parms_list[14], beps_parms_list[15], 
                                 beps_parms_list[16], beps_parms_list[17], 
                                 do_create_waveform, False, False))
        # Wait until waveform is created
        while self.VI.getcontrolvalue('Initialize_BEPS_VS_control_cluster')[18]:
            time.sleep(0.1)

        self.VI.setcontrolvalue('Initialize_BEPS_VS_control_cluster', 
                                (beps_parms_list[0], beps_parms_list[1], beps_parms_list[2], beps_parms_list[3], 
                                 beps_parms_list[4], beps_parms_list[5], beps_parms_list[6], beps_parms_list[7], 
                                 beps_parms_list[8], beps_parms_list[9], beps_parms_list[10], beps_parms_list[11],
                                 beps_parms_list[12], beps_parms_list[13], beps_parms_list[14], beps_parms_list[15], 
                                 beps_parms_list[16], beps_parms_list[17], 
                                 False, do_upload_waveform, False))
        while self.VI.getcontrolvalue('Initialize_BEPS_VS_control_cluster')[19]:
            time.sleep(0.1)
    
        self.VI.setcontrolvalue('Initialize_BEPS_VS_control_cluster', 
                                (beps_parms_list[0], beps_parms_list[1], beps_parms_list[2], beps_parms_list[3], 
                                 beps_parms_list[4], beps_parms_list[5], beps_parms_list[6], beps_parms_list[7], 
                                 beps_parms_list[8], beps_parms_list[9], beps_parms_list[10], beps_parms_list[11],
                                 beps_parms_list[12], beps_parms_list[13], beps_parms_list[14], beps_parms_list[15], 
                                 beps_parms_list[16], beps_parms_list[17], 
                                 False, False, do_VS_waveform))
        while self.VI.getcontrolvalue('Initialize_BEPS_VS_control_cluster')[20]:
            time.sleep(0.1)

        # Show BEPS parameters
        if feedbackon == True:
            beps_parms = self.VI.getcontrolvalue("Initialize_BEPS_VS_control_cluster")
            print("BEPS parameters are: ", beps_parms)
        
        if do_VS_waveform == True:
            ## Get BEPS data
            beps_result = self.VI.getcontrolvalue("BEPS_VS_indicator_cluster")
            beps_vs_vec = beps_result[0]
            beps_cpx_spectrogram = beps_result[1]
            beps_amp_vec = beps_result[2]
            beps_res_vec = beps_result[3]
            beps_Q_vec = beps_result[4]
            beps_pha_vec = beps_result[5]
            beps_ch01 = beps_result[7]
            beps_ch02 = beps_result[8]
            beps_ch03 = beps_result[9]
        
            #return raw data and quick fitting
            return beps_vs_vec, beps_cpx_spectrogram, [beps_amp_vec,beps_res_vec, beps_Q_vec,
                                                       beps_pha_vec], [beps_ch01, beps_ch02, beps_ch03]  
        else:
            return 

    def do_beps_grid (self, beps_parms_dict = None, beps_grid_parms_dict = None, file_name = "BEPS_grid", 
                      feedbackon = False, progress_on = True):
        """
        Define band excitation piezoresponse spectroscopy measurement parameters.
    
        Args:
            beps_parms_dict (dict): Dictionary of BEPS measurement parameters.
                Example: beps_parms_dict = {"amplitude_V_00": 8, 
                                            "offset_V_01": 0, 
                                            "read_voltage_V_02": 0, 
                                            "step_per_cycle_03": 64,
                                            "num_cycles_04": 3, 
                                            "cycle_fraction_05": 0, 
                                            "cycle_phase_shift_06": 0, 
                                            "measure_loops_07": 0,
                                            "transition_time_s_08": 1E-6, 
                                            "delay_after_step_s_09": 0, 
                                            "set_pulse_amplitude_V_10": 0, 
                                            "set_pulse_duration_s_11": 0, 
                                            "FORC_num_cycles_12": 1, 
                                            "FORC_A1_V_13": 7, 
                                            "FORC_A2_V_14": 8,
                                            "FORC_num_repeats_15": 0, 
                                            "FORC_B1_V_16": -7, 
                                            "FORC_B2_V_17": -8 }
            Default parameters are the parameters shown in the BEPyAE.exe initialize_BEPS_VS_control_cluster panel.
            do_create_waveform (bool): Create the BEPS waveform.
            do_upload_waveform (bool): Upload the created waveform to DAQ card.
            do_VS_waveform (bool): Applied the uploaded waveform.
            feedbackon (bool): Flag to indicate whether to print BEPS parameters.
        
        beps_grid_parms_dict (dict): Dictionary of grid measurement parameters.
                Example: beps_grid_parms_dict = {"range_x": [-1, 1], 
                                                 "range_y": [-1, 1],
                                                 "pixel_num_x": 5, 
                                                 "pixel_num_y": 5}
                                           
        Returns:
            If `do_VS_waveform` is True, returns BEPS data including:
                - beps_vs_vec: BEPS DC waveform vector
                - beps quick fitting data
                - beps channel data
                - beps_cpx_spectrogram: BEPS complex spectrogram

         """
        
        # Set default value
        self.range_x = [-1, 1]
        self.range_y = [-1, 1]
        self.pixel_num_x = 5
        self.pixel_num_y = 5

        beps_grid_parms_list = [self.range_x, self.range_y, self.pixel_num_x, self.pixel_num_y]
        beps_grid_parms_name_list = ["range_x", "range_y", "pixel_num_x", "pixel_num_y"]
        # if user customized some parameters, set the parameters as customized values
        if beps_grid_parms_dict != None:
            for i in range (len (beps_grid_parms_list)):
                if beps_grid_parms_name_list[i] in beps_grid_parms_dict:
                    beps_grid_parms_list[i] = beps_grid_parms_dict[beps_grid_parms_name_list[i]]
        
        # Define grid locations
        pixel_x = np.linspace(beps_grid_parms_list[0][0], beps_grid_parms_list[0][1], beps_grid_parms_list[2])
        pixel_y = np.linspace(beps_grid_parms_list[1][0], beps_grid_parms_list[1][1], beps_grid_parms_list[3])
        pixels_xy = np.meshgrid(pixel_x, pixel_y)
        pixels_x = pixels_xy[0].reshape(-1)
        pixels_y = pixels_xy[1].reshape(-1)
        coordinates_final = np.asarray([pixels_x, pixels_y])

        # Upload BEPS waveform
        self.define_BEPS_parameters(beps_parms_dict = beps_parms_dict, do_create_waveform = True, 
                                    do_upload_waveform = True, do_VS_waveform = False, feedbackon = False)
        # creat an emapy list to save data
        grid_beps_quick_fit = []
        grid_beps_cpx_spectra = []
        grid_beps_chns = []

        # make a progress bar
        if progress_on:
            bar_progress = self.progress_bar(max_value = len(pixels_x))

        for i in range(len(pixels_x)):
            # move tip 
            self.tip_control(tip_parms_dict={"next_x_pos_00": pixels_x[i],
                                             "next_y_pos_01": pixels_y[i], 
                                             "transit_time_s_02": 0.2},
                                             do_move_tip = True, do_set_setpoint = False, 
                                             feedbackon=feedbackon)
            time.sleep(0.1)
            # do BEPS
            vs, cpx_spectra, beps_quick_fit, beps_chns = self.define_BEPS_parameters(beps_parms_dict = None,
                                                                                     do_create_waveform = False,
                                                                                     do_upload_waveform = False, 
                                                                                     do_VS_waveform = True, feedbackon=feedbackon)

            grid_beps_quick_fit.append(beps_quick_fit)
            grid_beps_cpx_spectra.append(cpx_spectra)
            grid_beps_chns.append(beps_chns)

            #update progress
            if progress_on:
                bar_progress.update(i)

        vdc, beps_qf, beps_chs, beps_cs = self.mk_dset(file_name = file_name,
                                                       pfm_imgstack = np.asarray(grid_beps_quick_fit),
                                                       channel_imgstack = np.asarray(grid_beps_chns),
                                                       complex_spectra = np.asarray(grid_beps_cpx_spectra),
                                                       start_x = beps_grid_parms_list[0][0],
                                                       finish_x = beps_grid_parms_list[0][1],
                                                       start_y = beps_grid_parms_list[1][0], 
                                                       finish_y = beps_grid_parms_list[1][1], 
                                                       coordinates = coordinates_final,
                                                       beps = True)

        return vdc, beps_qf, beps_chs, beps_cs   # return BEPS dc waveform and grid beps results

    def do_beps_random (self, beps_parms_dict = None, beps_grid_parms_dict = None, file_name = "BEPS_random",
                        random_counts = 10, feedbackon = False, progress_on = True):
        """
        Define band excitation piezoresponse spectroscopy measurement parameters.
    
        Args:
            beps_parms_dict (dict): Dictionary of BEPS measurement parameters.
                Example: beps_parms_dict = {"amplitude_V_00": 8, 
                                            "offset_V_01": 0, 
                                            "read_voltage_V_02": 0, 
                                            "step_per_cycle_03": 64,
                                            "num_cycles_04": 3, 
                                            "cycle_fraction_05": 0, 
                                            "cycle_phase_shift_06": 0, 
                                            "measure_loops_07": 0,
                                            "transition_time_s_08": 1E-6, 
                                            "delay_after_step_s_09": 0, 
                                            "set_pulse_amplitude_V_10": 0, 
                                            "set_pulse_duration_s_11": 0, 
                                            "FORC_num_cycles_12": 1, 
                                            "FORC_A1_V_13": 7, 
                                            "FORC_A2_V_14": 8,
                                            "FORC_num_repeats_15": 0, 
                                            "FORC_B1_V_16": -7, 
                                            "FORC_B2_V_17": -8 }
            Default parameters are the parameters shown in the BEPyAE.exe initialize_BEPS_VS_control_cluster panel.
            do_create_waveform (bool): Create the BEPS waveform.
            do_upload_waveform (bool): Upload the created waveform to DAQ card.
            do_VS_waveform (bool): Applied the uploaded waveform.
            feedbackon (bool): Flag to indicate whether to print BEPS parameters.

        Returns:
            If `do_VS_waveform` is True, returns BEPS data including:
                - beps_vs_vec: BEPS DC waveform vector
                - beps quick fitting data
                - beps channel data
                - beps_cpx_spectrogram: BEPS complex spectrogram

         """
        
        # Set default value
        self.range_x = [-1, 1]
        self.range_y = [-1, 1]
        self.pixel_num_x = 5
        self.pixel_num_y = 5

        beps_grid_parms_list = [self.range_x, self.range_y, self.pixel_num_x, self.pixel_num_y]
        beps_grid_parms_name_list = ["range_x", "range_y", "pixel_num_x", "pixel_num_y"]
        # if user customized some parameters, set the parameters as customized values
        if beps_grid_parms_dict != None:
            for i in range (len (beps_grid_parms_list)):
                if beps_grid_parms_name_list[i] in beps_grid_parms_dict:
                    beps_grid_parms_list[i] = beps_grid_parms_dict[beps_grid_parms_name_list[i]]
        
        # Define grid locations
        pixel_x = np.linspace(beps_grid_parms_list[0][0], beps_grid_parms_list[0][1], beps_grid_parms_list[2])
        pixel_y = np.linspace(beps_grid_parms_list[1][0], beps_grid_parms_list[1][1], beps_grid_parms_list[3])
        pixels_xy = np.meshgrid(pixel_x, pixel_y)
        pixels_x = pixels_xy[0].reshape(-1)
        pixels_y = pixels_xy[1].reshape(-1)
        
        # measure random locations
        coordinates_index = np.random.choice(len(pixels_x), random_counts, replace=False)
        pixels_x = pixels_x[coordinates_index]
        pixels_y = pixels_y[coordinates_index]
        coordinates_final = np.asarray([pixels_x, pixels_y])

        # Upload BEPS waveform
        self.define_BEPS_parameters(beps_parms_dict = beps_parms_dict, do_create_waveform = True, 
                                    do_upload_waveform = True, do_VS_waveform = False, feedbackon = False)
        # creat an emapy list to save data
        grid_beps_quick_fit = []
        grid_beps_cpx_spectra = []
        grid_beps_chns = []

        # make a progress bar
        if progress_on:
            bar_progress = self.progress_bar(max_value = len(pixels_x))

        for i in range(len(pixels_x)):
            # move tip 
            self.tip_control(tip_parms_dict={"next_x_pos_00": pixels_x[i],
                                             "next_y_pos_01": pixels_y[i], 
                                             "transit_time_s_02": 0.2},
                                             do_move_tip = True, do_set_setpoint = False, 
                                             feedbackon=feedbackon)
            time.sleep(0.1)
            # do BEPS
            vs, cpx_spectra, beps_quick_fit, beps_chns = self.define_BEPS_parameters(beps_parms_dict = None,
                                                                                     do_create_waveform = False,
                                                                                     do_upload_waveform = False, 
                                                                                     do_VS_waveform = True, feedbackon=feedbackon)

            grid_beps_quick_fit.append(beps_quick_fit)
            grid_beps_cpx_spectra.append(cpx_spectra)
            grid_beps_chns.append(beps_chns)

            #update progress
            if progress_on:
                bar_progress.update(i)

        vdc, beps_qf, beps_chs, beps_cs = self.mk_dset(file_name = file_name,
                                                       pfm_imgstack = np.asarray(grid_beps_quick_fit),
                                                       channel_imgstack = np.asarray(grid_beps_chns),
                                                       complex_spectra = np.asarray(grid_beps_cpx_spectra),
                                                       start_x = beps_grid_parms_list[0][0],
                                                       finish_x = beps_grid_parms_list[0][1],
                                                       start_y = beps_grid_parms_list[1][0], 
                                                       finish_y = beps_grid_parms_list[1][1], 
                                                       coordinates = coordinates_final,
                                                       beps = True)

        return vdc, beps_qf, beps_chs, beps_cs   # return BEPS dc waveform and grid beps results
    
    def do_beps_specific (self, beps_parms_dict = None, file_name = "BEPS_spec", 
                          coordinates = None, feedbackon = False, progress_on = True):
        """
        Define band excitation piezoresponse spectroscopy measurement parameters.
    
        Args:
            beps_parms_dict (dict): Dictionary of BEPS measurement parameters.
                Example: beps_parms_dict = {"amplitude_V_00": 8, 
                                            "offset_V_01": 0, 
                                            "read_voltage_V_02": 0, 
                                            "step_per_cycle_03": 64,
                                            "num_cycles_04": 3, 
                                            "cycle_fraction_05": 0, 
                                            "cycle_phase_shift_06": 0, 
                                            "measure_loops_07": 0,
                                            "transition_time_s_08": 1E-6, 
                                            "delay_after_step_s_09": 0, 
                                            "set_pulse_amplitude_V_10": 0, 
                                            "set_pulse_duration_s_11": 0, 
                                            "FORC_num_cycles_12": 1, 
                                            "FORC_A1_V_13": 7, 
                                            "FORC_A2_V_14": 8,
                                            "FORC_num_repeats_15": 0, 
                                            "FORC_B1_V_16": -7, 
                                            "FORC_B2_V_17": -8}
            Default parameters are the parameters shown in the BEPyAE.exe initialize_BEPS_VS_control_cluster panel.
            do_create_waveform (bool): Create the BEPS waveform.
            do_upload_waveform (bool): Upload the created waveform to DAQ card.
            do_VS_waveform (bool): Applied the uploaded waveform.
            feedbackon (bool): Flag to indicate whether to print BEPS parameters.

        Returns:
            If `do_VS_waveform` is True, returns BEPS data including:
                - beps_vs_vec: BEPS DC waveform vector
                - beps quick fitting data
                - beps channel data
                - beps_cpx_spectrogram: BEPS complex spectrogram

         """
        
        # BEPS locations
        pixels_x = coordinates[0].reshape(-1)
        pixels_y = coordinates[1].reshape(-1)
        coordinates_final = np.asarray([pixels_x[0], pixels_y[0]])

        # Upload BEPS waveform
        self.define_BEPS_parameters(beps_parms_dict = beps_parms_dict, do_create_waveform = True, 
                                    do_upload_waveform = True, do_VS_waveform = False, feedbackon = False)
        # creat an emapy list to save data
        grid_beps_quick_fit = []
        grid_beps_cpx_spectra = []
        grid_beps_chns = []

        # make a progress bar
        if progress_on:
            bar_progress = self.progress_bar(max_value = len(pixels_x))

        for i in range(len(pixels_x)):
            # move tip 
            self.tip_control(tip_parms_dict={"next_x_pos_00": pixels_x[i],
                                             "next_y_pos_01": pixels_y[i], 
                                             "transit_time_s_02": 0.2},
                                             do_move_tip = True, do_set_setpoint = False, 
                                             feedbackon=feedbackon)
            time.sleep(0.1)
            # do BEPS
            vs, cpx_spectra, beps_quick_fit, beps_chns = self.define_BEPS_parameters(beps_parms_dict = None,
                                                                                     do_create_waveform = False,
                                                                                     do_upload_waveform = False, 
                                                                                     do_VS_waveform = True, feedbackon=feedbackon)

            grid_beps_quick_fit.append(beps_quick_fit)
            grid_beps_cpx_spectra.append(cpx_spectra)
            grid_beps_chns.append(beps_chns)

            #update progress
            if progress_on:
                bar_progress.update(i)

        vdc, beps_qf, beps_chs, beps_cs = self.mk_dset(file_name = file_name,
                                                       pfm_imgstack = np.asarray(grid_beps_quick_fit),
                                                       channel_imgstack = np.asarray(grid_beps_chns),
                                                       complex_spectra = np.asarray(grid_beps_cpx_spectra),
                                                       start_x = -1,
                                                       finish_x = 1,
                                                       start_y = -1, 
                                                       finish_y = 1, 
                                                       coordinates = coordinates_final,
                                                       beps = True)

        return vdc, beps_qf, beps_chs, beps_cs   # return BEPS dc waveform and grid beps results
    
    def fpga_spiral_scan(self, spiral_parms_dict = None, scan_type = 1, data_rate = 0, do_scan_update = True, 
                    do_scan = False, feedbackon = True, file_name = "spiral_scan"):
        """
        Define and perform a spiral scan using FPGA.

        Args:
            spiral_parms_dict (dict): Dictionary of spiral scan parameters.
                Example: spiral_parms_dict = {"spiral_inner_radius_x_V_00": 0, "spiral_outer_radius_x_V_01": 1, 
                                              "spiral_inner_radius_y_V_02": 0, "spiral_outer_radius_y_V_03": 1,
                                              "sprial_N_cycles_04": 10, "spiral_duration_05": 100E-3,
                                              "spiral_direction_07": 0, "spiral_return_opt_08": 0}
                Default parameters are the values shown in the Pyscanner.exe spiral_scan_control_cluster panel now.
                If spiral_parms_dict = None, the function uses default values. 
                scan_type (int): set Scan type to 1 for spiral scan.
                data_rate (int): Data rate for the scan.
                do_scan_update (bool): Flag indicating whether to update the scan parameters.
                do_scan (bool): Flag indicating whether to perform the spiral scan.
                feedbackon (bool): Flag indicating whether to print feedback during the scan.
                file_name (str): Name of the HDF5 file to save the scan results.

            Returns:
                dict or None: 
                    If `do_scan` is True, returns a dictionary containing the scan results:
                        - "image_mask": Image mask data
                        - "image_counts": Image counts data
                        - "image_AI0": Image AI0 data
                        - "image_AI1": Image AI1 data
                        - "image_AI2": Image AI2 data
                        - "image_AI3": Image AI3 data
                        - "output_xy": Output XY data
                    If `do_scan` is False, returns None.
            """
        # Set scan type to spiral scan
        self.VIs.setcontrolvalue("scan_type", (scan_type))
        # Set data rate
        self.VIs.setcontrolvalue("data_rate", (data_rate))

        # Get default value
        spiral_parms = self.VIs.getcontrolvalue("spiral_scan_control_cluster")
        scan_offset_x = self.VIs.getcontrolvalue("scan_x_offset_V")
        scan_offset_y = self.VIs.getcontrolvalue("scan_y_offset_V")
        scan_rotation = self.VIs.getcontrolvalue("scan_rotation_deg")
        
        spiral_parms_list = [spiral_parms[0], spiral_parms[1], spiral_parms[2], spiral_parms[3], 
                             spiral_parms[4], spiral_parms[5], spiral_parms[6], spiral_parms[7], 
                             spiral_parms[8], spiral_parms[9], spiral_parms[10], scan_offset_x,
                             scan_offset_y, scan_rotation]
        spiral_parms_name_list = ["spiral_inner_radius_x_V_00", "spiral_outer_radius_x_V_01", "spiral_inner_radius_y_V_02",
                                  "spiral_outer_radius_y_V_03", "spiral_N_cycles_04", "spiral_duration_05", "spiral_dose_distrituion_06",
                                  "spiral_direction_07", "spiral_return_opt_08", "spiral_shape_opt_09", "low_pass_filter_Hz_10",
                                  "scan_x_offset_V", "scan_y_offset_V", "scan_rotation_deg"]
        
        # if user customized some parameters, set the parameters as customized values
        if spiral_parms_dict != None:
            for i in range (len (spiral_parms_list)):
                if spiral_parms_name_list[i] in spiral_parms_dict:
                    spiral_parms_list[i] = spiral_parms_dict[spiral_parms_name_list[i]]

        ## Set spiral scan control cluster
        self.VIs.setcontrolvalue('spiral_scan_control_cluster', 
                                (spiral_parms_list[0], spiral_parms_list[1], spiral_parms_list[2], spiral_parms_list[3],
                                 spiral_parms_list[4], spiral_parms_list[5], spiral_parms_list[6], spiral_parms_list[7],
                                 spiral_parms_list[8], spiral_parms_list[9], spiral_parms_list[10]))
        time.sleep(0.1)
        # Updata spiral scan parameters
        self.VIs.setcontrolvalue("do_scan_update", (do_scan_update))
        # Wait until spiral scan parameters are updated
        while self.VIs.getcontrolvalue("do_scan_update"):
            time.sleep(0.1) # wait 0.1 s and check the status again

        # Set scan offset and rotation angle
        self.VIs.setcontrolvalue("scan_x_offset_V", (spiral_parms_list[11]))
        self.VIs.setcontrolvalue("scan_y_offset_V", (spiral_parms_list[12]))
        self.VIs.setcontrolvalue("scan_rotation_deg", (spiral_parms_list[13]))
        
        # Do spiral scan
        self.VIs.setcontrolvalue("do_scan", (do_scan))
        # Wait until sprial scan is done
        while self.VIs.getcontrolvalue("do_scan"):
            time.sleep(0.1)

        time.sleep(0.5)
        if do_scan == True:
            # Get results
            image_mask = self.VIs.getcontrolvalue("image_mask")
            image_counts = self.VIs.getcontrolvalue("image_counts")
            image_AI0 = self.VIs.getcontrolvalue("image_AI0")
            image_AI1 = self.VIs.getcontrolvalue("image_AI1")
            image_AI2 = self.VIs.getcontrolvalue("image_AI2")
            image_AI3 = self.VIs.getcontrolvalue("image_AI3")
            output_xy = [self.VIs.getcontrolvalue('AO0_V'), self.VIs.getcontrolvalue('AO1_V')]
            num_image_pixels = self.VIs.getcontrolvalue('N_image_pixels')

            # Create hdf5 file to save data
            suf = 0
            save_name = "{}_{}.hf5".format(file_name, suf)
            # update suffex if file already exists
            while os.path.exists(save_name):
                suf += 1            
                save_name = "{}_{}.hf5".format(file_name, suf)

            hf = h5py.File(save_name, 'a')
            # image size
            # img_size = np.asarray([num_image_pixels*(scan_size_y*len_y)/2, num_image_pixels*(scan_size_x*len_x)/2])
            img_size = 10
            hf['Scan Parameters/scan size'] = img_size
            # path index
            hf['Scan Parameters/path index'] = output_xy
            # images
            hf["Scan Images/mask"] = image_mask
            hf["Scan Images/counts"] = image_counts
            hf["Scan Images/image_AI0"] = image_AI0
            hf["Scan Images/image_AI1"] = image_AI1
            hf["Scan Images/image_AI2"] = image_AI2
            hf["Scan Images/image_AI3"] = image_AI3
            # close hf file after writing all data
            hf.close()
        
            # pack results and return
            results = {"image_mask": image_mask, "image_counts": image_counts, 
                       "image_AI0": image_AI0, "image_AI1": image_AI1, 
                       "image_AI2": image_AI2, "image_AI3": image_AI3, "output_xy": output_xy}

            return results
        
        else:
            return
    
    # Help function for BE spiral reconstruction
    def SSTEM(yspar,mask,itern,levels,lambd):
        """
        INPUT: 
        -yspar: sparse image as an array, to reduce iteration numer, better rescaling the value to [0,1]
        -mask: binary array, 1 indicationg sampled pixel locations
        -itern: iteration number, usually 20 is enough
        -levels: wavelet level, common choice 2,3,4, larger value for larger feature size, if too blur, change to smaller one
        -lambd: threshold value, usually 0.8 is fine
        OUTPUT: 
        -Reconstructed image
        """
    
        fSpars = yspar
        W_thr = [0]*levels

        ProjC = lambda f, Omega: (1-Omega)*f + Omega*yspar
    
        for i in range(itern):
            fSpars = ProjC(fSpars, mask)
            W_pro = pywt.swt2(fSpars, 'db2',levels)
            for j in range(levels):
                sA = W_pro[j][0]
                sH = W_pro[j][1][0]
                sV = W_pro[j][1][1]
                sD = W_pro[j][1][2]
                W_thr[j] = (pywt.threshold(sA,0,'soft')),(pywt.threshold(sH,lambd,'soft'),
                            pywt.threshold(sV,lambd,'soft'),pywt.threshold(sD,lambd,'soft'))    
            fSpars = pywt.iswt2(W_thr,'db2')
        return fSpars

    # Spiral reconstruction function
    def spiral_be_reconstruction(sho_guess_cluster, output_xy, sample_factor=32, 
                                 num_image_pixels=200, itern=1, levels=3, lambd=3, cut_thresh=0.95):
        # BE line data
        sho_guess = np.asarray(sho_guess_cluster)
            
        # Sample
        output_x = np.asarray(output_xy[0])
        output_y = np.asarray(output_xy[1])
        outx_downsampled = output_x[::output_x.shape[0]//sho_guess.shape[0]//sample_factor]
        outy_downsampled = output_y[::output_y.shape[0]//sho_guess.shape[0]//sample_factor]
        outx_max = np.max(np.abs(outx_downsampled))
        outy_max = np.max(np.abs(outy_downsampled))
        xy_max = np.max([outx_max, outy_max])

        #The x and y positions are to convert to in pixels
        x_downsampled = 0.5*(outx_downsampled * num_image_pixels/outx_max + num_image_pixels)
        y_downsampled = 0.5*(outy_downsmapled * num_image_pixels/outy_max + num_image_pixels)

        sho_amp = sho_guess[:,0]
        sho_pha = sho_guess[:,3]
        new_us = np.linspace(0, sho_amp.shape[0], sho_amp.shape[0]*sample_factor)
        sho_amp_interp = np.interp(new_us, np.arange(0, sho_amp.shape[0]), sho_amp)
        sho_pha_interp = np.interp(new_us, np.arange(0, sho_pha.shape[0]), sho_pha)

        z_img = np.zeros((image_mask.shape[0], image_mask.shape[1], 2))

        for j in range(int(sho_amp_interp.shape[0]*cut_thresh)):
            pos = [int(x_downsampled[j]), int(y_downsampled[j])]
            pos[0] = np.clip(pos[0],0, image_mask.shape[0]-1)
            pos[1] = np.clip(pos[1],0,image_mask.shape[1]-1)
            z_img[pos[0], pos[1],0] = sho_amp_interp[j]*1E3
            z_img[pos[0], pos[1],1] = sho_pha_interp[j]

        mask_ = np.zeros(z_img[:,:,0].shape)
        for i1 in range(z_img[:,:,0].shape[0]):
            for i2 in range(z_img[:,:,0].shape[1]):
                if abs(z_img[i1,i2,0]) > 0:
                    mask_[i1,i2] = 1

        #Now do CS reconstructions
        reconstructions = []
        for k in range(5):
            try:
                reconstruction=self.SSTEM(np.abs(z_img[:,:,k]), mask_, itern, levels, lambd)
            except:
                pass
            reconstructions.append(reconstruction)
        
        return reconstructions

    def fpga_spiral_scan_BE(self, be_parms_dict = None, do_create_be_waveform = True,
                            spiral_parms_dict = None, num_BE_pulse = 128, tip_voltage = 0, 
                            scan_type = 1, data_rate = 0, do_scan_update = True,
                            do_BE_arb_line_update_00 = True, do_BE_arb_line_scan_01 = False, 
                            spiral_reconstruction = True, file_name = "spiral_BE"):
        """
        Perform spiral BE scan

        Args:
            be_parms_dict (dict): Dictionary for BE pulse parameters (default: None)
            spiral_parms_dict (dict): Dictionary for spiral scan parameters (default: None)
            num_BE_pulse (int): Number of BE pulses (default: 128)
            tip_voltage (float or int): Tip voltage (default: 0)
            scan_type (int): set scan_type = 1 for spiral scan
            data_rate (int): Data rate (default: 0)
            do_scan_update (bool): Flag to update scan parameters (default: True)
            do_BE_arb_line_update_00 (bool): Flag to update BE line parameters (default: True)
            do_BE_arb_line_scan_01 (bool): Flag to perform BE spiral scan (default: False)
            spiral_reconstruction (bool): Flag to perform spiral BE reconstruction (default: True)
            Parameters for spiral BE reconstruction: 
                - sample_factor (int): default: 32
                - lambd (int): default: 3
                - levels (int): default: 3
                - itern (int): default: 1
                - cut_thresh (float): default: 0.95

        Returns:
            FPGA results and BE results
        """
        #################################################################################################
        #####################################Do Spiral BE Measurements###################################
        #################################################################################################                    
        # define be parameters first
        self.define_be_parms(be_parms_dict = be_parms_dict, do_create_be_waveform = do_create_be_waveform)
        
        # define spiral parameters
        self.fpga_spiral_scan(spiral_parms_dict = spiral_parms_dict, scan_type = scan_type, 
                              data_rate = data_rate, do_scan_update = do_scan_update,  # do scan update can be False 
                            do_scan = False)  # do scan need to be False here, scan will be triggered from PyAe side
        # upload be scan pulse to DAQ
        self.VI.setcontrolvalue("Initialize_BE_line_scan_control_cluster", (tip_voltage, num_BE_pulse, True))
        # Wait when uploading pulse
        while self.VI.getcontrolvalue("Initialize_BE_line_scan_control_cluster")[2] == True:
            time.sleep(0.1)
        time.sleep(1)

        # upload be scan pulse to DAQ
        self.VI.setcontrolvalue("Initialize_BE_line_scan_control_cluster", (tip_voltage, num_BE_pulse, True))
        # Wait when uploading pulse
        while self.VI.getcontrolvalue("Initialize_BE_line_scan_control_cluster")[2] == True:
            time.sleep(0.1)
        time.sleep(1)

        # update BE arb scan
        self.VI.setcontrolvalue("BE_arb_scan_control_cluster", (False, do_BE_arb_line_update_00))
        # wait until update finish
        time.sleep(0.5)
        while self.VIs.getcontrolvalue("do_scan_update"):
            time.sleep(0.1)
        
        time.sleep(0.5)
        # do BE arb scan
        self.VI.setcontrolvalue("BE_arb_scan_control_cluster", (do_BE_arb_line_scan_01, False))
        # wait until scan finish
        while self.VI.getcontrolvalue("BE_arb_scan_control_cluster")[0]:
            time.sleep(0.1)
        
        # Wait until scan is done
        while self.VIs.getcontrolvalue("do_scan"):
            time.sleep(0.1)
        
        #################################################################################################
        ##########################################Get Results############################################
        #################################################################################################
        if do_BE_arb_line_scan_01 == True:
            # Get fpga results
            image_mask = self.VIs.getcontrolvalue("image_mask")
            image_counts = self.VIs.getcontrolvalue("image_counts")
            image_AI0 = self.VIs.getcontrolvalue("image_AI0")
            image_AI1 = self.VIs.getcontrolvalue("image_AI1")
            image_AI2 = self.VIs.getcontrolvalue("image_AI2")
            image_AI3 = self.VIs.getcontrolvalue("image_AI3")
            output_xy = [self.VIs.getcontrolvalue('AO0_V'), self.VIs.getcontrolvalue('AO1_V')]
            num_image_pixels = self.VIs.getcontrolvalue('N_image_pixels')
            
            # Pack results and return
            fpga_results = {"image_mask": image_mask, "image_counts": image_counts, 
                            "image_AI0": image_AI0, "image_AI1": image_AI1,
                            "image_AI2": image_AI2, "image_AI3": image_AI3, "output_xy": output_xy}

            # get BE results
            be_line_result = self.VI.getcontrolvalue("BE_line_scan_indicator_cluster")
            daq_wave, complex_spectrogram, sho_guess_cluster = be_line_result[0], be_line_result[1], be_line_result[3]
            channel1, channel2, channel3 = be_line_result[4], be_line_result[5], be_line_result[6]

        #################################################################################################
        ####################################Save Result as H5 File#######################################
        #################################################################################################
            # Define hf5 file name
            suf = 0
            save_name = "{}_{}.hf5".format(file_name, suf)
            # Update suffex if file already exists
            while os.path.exists(save_name):
                suf += 1
                save_name = "{}_{}.hf5".format(file_name, suf)
        
            # Create hf5 file
            hf = h5py.File(save_name, 'a')

            # Save BE pulse parameters
            beparms = self.VI.getcontrolvalue('BE_pulse_control_cluster')
            hf['BE Parameters/pulse parameters'] = np.asarray(beparms)

            # Frequency spectral
            fft_fres = np.asarray(self.VI.getcontrolvalue('BE_pulse_parm_indicator_cluster')[6])
            fft_bin_idx = np.asarray(self.VI.getcontrolvalue('BE_pulse_parm_indicator_cluster')[3])
            fre_arr = fft_fres[fft_bin_idx]
            hf['BE Parameters/frequency'] = np.asarray(fre_arr)

            # image size
            # img_size = np.asarray([(dset_imgs.shape[0])*(scan_size_y*len_y)/2, (dset_imgs.shape[1])*(scan_size_x*len_x)/2])
            img_size = 10  # this needs to be corrected later
            hf['Scan Parameters/scan size'] = img_size
            # Path index
            hf['Scan Parameters/path index'] = output_xy
            # images
            hf["Scan Images/mask"] = image_mask
            hf["Scan Images/counts"] = image_counts
            hf["Scan Images/image_AI0"] = image_AI0
            hf["Scan Images/image_AI1"] = image_AI1
            hf["Scan Images/image_AI2"] = image_AI2
            hf["Scan Images/image_AI3"] = image_AI3
            # BE line
            hf["BE Line/daq_wave"] = daq_wave
            hf["BE Line/complex_spectrogram"] = complex_spectrogram
            hf["BE Line/sho_guess_cluster"] = sho_guess_cluster
            hf["BE Line/channel1"] = channel1
            hf["BE Line/channel2"] = channel2
            hf["BE Line/channel3"] = channel3
                    
        #################################################################################################
        ####################################Do Spiral Rescontruction#####################################
        #################################################################################################
            if spiral_reconstruction == True:
                rescontructions = self.spiral_be_reconstruction(sho_guess_cluster, output_xy)
                # BE reconstruction
                hf["BE Line/recontructions"] = recontructions
                
                be_results = {"daq_wave": daq_wave, "complex_spectrogram": complex_spectrogram, 
                              "sho_guess_cluster": sho_guess_cluster, "channel1": channel1, 
                              "channel2": channel2, "channel3": channel3,
                              "reconstructions": reconstructions}

            else:
                be_results = {"daq_wave": daq_wave, "complex_spectrogram": complex_spectrogram, 
                              "sho_guess_cluster": sho_guess_cluster, "channel1": channel1, 
                              "channel2": channel2, "channel3": channel3}
            
            hf.close() # Close hf file after writing all data
            
            return fpga_results, be_results
        else:
            return
    
    def fpga_raster_scan(self, fpga_raster_parms_dict = None, scan_type = 3, data_rate = 0, do_scan_update = True, 
                    scan_x_offset = 0, scan_y_offset = 0, scan_rotation_deg = 0, do_scan = False):
        # Set scan type to raster scan
        self.VIs.setcontrolvalue("scan_type", (scan_type))
        # Set data rate
        self.VIs.setcontrolvalue("data_rate", (data_rate))

        # Set default value
        raster_scan_size_x_V_00 = 1,
        raster_scan_size_y_V_01 = 1,
        raster_N_scan_lines_02 = 64 
        raster_scan_duration_s_03 = 100E-3
        raster_type_04 = 0
        
        fpga_raster_parms_list = [raster_scan_size_x_V_00, raster_scan_size_y_V_01, raster_N_scan_lines_02, 
                                  raster_scan_duration_s_03, raster_type_04]
        fpga_raster_parms_name_list = ["raster_scan_size_x_V_00", "raster_scan_size_y_V_01", "raster_N_scan_lines_02",
                                       "raster_scan_duration_s_03", "raster_type_04"]
        
        # if user customized some parameters, set the parameters as customized values
        if fpga_raster_parms_dict != None:
            for i in range (len (fpga_raster_parms_list)):
                if fpga_raster_parms_name_list[i] in fpga_raster_parms_dict:
                    fpga_raster_parms_list[i] = fpga_raster_parms_dict[fpga_raster_parms_name_list[i]]

        ## Set raster scan control cluster
        self.VIs.setcontrolvalue('fast_raster_scan_control_cluster', 
                                (fpga_raster_parms_list[0], fpga_raster_parms_list[1], fpga_raster_parms_list[2], 
                                 fpga_raster_parms_list[3], fpga_raster_parms_list[4]))
        
        # Updata raster scan parameters
        self.VIs.setcontrolvalue("do_scan_update", (do_scan_update))
        # Wait until scan parameters are updated
        while self.VIs.getcontrolvalue("do_scan_update"):
            time.sleep(0.1) # wait 0.1 s and check the status again

        # Set scan offset and rotation angle
        self.VIs.setcontrolvalue("scan_x_offset_V", (scan_x_offset))
        self.VIs.setcontrolvalue("scan_y_offset_V", (scan_y_offset))
        self.VIs.setcontrolvalue("scan_rotation_deg", (scan_rotation_deg))
        
        # Do raster scan
        self.VIs.setcontrolvalue("do_scan", (do_scan))
        # Wait until raster scan is done
        while self.VIs.getcontrolvalue("do_scan"):
            time.sleep(0.1)

        return results

    def fpga_raster_scan_BE(self, be_parms_dict = None, do_create_be_waveform = True,
                            fpga_raster_parms_dict = None, num_BE_pulse = 128, tip_voltage = 0, 
                            scan_type = 3, data_rate = 0, 
                            do_scan_update = True, scan_x_offset = 0, scan_y_offset = 0, scan_rotation_deg = 0,
                            do_BE_arb_line_update_00 = True, do_BE_arb_line_scan_01 = True):
        # define be parameters
        self.define_be_parms(be_parms_dict = be_parms_dict, do_create_be_waveform = do_create_be_waveform)
        
        # define spiral parameters
        self.fpga_raster_scan(fpga_raster_parms_dict = fpga_raster_parms_dict, scan_type = scan_type,
                              data_rate = data_rate, do_scan_update = do_scan_update,  # do scan update can be False
                              scan_x_offset = scan_x_offset, scan_y_offset = scan_y_offset,
                              scan_rotation_deg = scan_rotation_deg, do_scan = False)  # do scan need to be False here, scan will be triggered from PyAe side
        
        # upload be scan pulse to DAQ
        self.VI.setcontrolvalue("initialize_BE_line_scan_control_cluster", (tip_voltage, num_BE_pulse, True))
        # Wait when uploading pulse
        while self.VI.setcontrolvalue("initialize_BE_line_scan_control_cluster")[2] == True:
            time.sleep(0.1)
        time.sleep(1)

        # upload be scan pulse to DAQ
        self.VI.setcontrolvalue("initialize_BE_line_scan_control_cluster", (tip_voltage, num_BE_pulse, True))
        # Wait when uploading pulse
        while self.VI.setcontrolvalue("initialize_BE_line_scan_control_cluster")[2] == True:
            time.sleep(0.1)
        time.sleep(1)

        # update BE arb scan
        self.VI.setcontrolvalue("BE_arb_scan_control_cluster", (False, do_BE_arb_line_update_00))
        # wait until update finish
        while self.VI.getcontrolvalue("BE_arb_scan_control_cluster")[0]:
            time.sleep(0.1)
        
        # do BE arb scan
        self.VI.setcontrolvalue("BE_arb_scan_control_cluster", (do_BE_arb_line_scan_01, False))
        # wait until scan finish
        while self.VI.getcontrolvalue("BE_arb_scan_control_cluster")[1]:
            time.sleep(0.1)
            
        # Wait until raster scan is done
        while self.VIs.getcontrolvalue("do_scan"):
            time.sleep(0.1)
            
        # get BE results
        be_result = self.VI.getcontrolvalue("BE_line_scan_indicator_cluster")
        complex_spectrogram, sho_guess_cluster = be_result[1], be_result[3]

        # Get fpga results
        mask = self.VIs.getcontrolvalue("image_mask")
        counts = self.VIs.getcontrolvalue("image_counts")
        image_AI0 = self.VIs.getcontrolvalue("image_AI0")
        image_AI1 = self.VIs.getcontrolvalue("image_AI1")
        image_AI2 = self.VIs.getcontrolvalue("image_AI2")
        image_AI3 = self.VIs.getcontrolvalue("image_AI3")

        fpga_results = {"mask": mask, "counts": counts, "image_AI0": image_AI0, 
                   "image_AI1": image_AI1, "image_AI2": image_AI2, "image_AI3": image_AI3}
        
        return complex_spectrogram, sho_guess_cluster, fpga_results

    def fpga_tip_control(self, fpga_tip_parms_dict=None, make_cur_pos_start_pos=True, 
                         do_probe_move_update=True, do_probe_move=True):
        """
        Control the tip using FPGA.

        Args:
            fpga_tip_parms_dict (dict): Dictionary of tip move parameters. 
            Example:
                fpga_tip_parms_dict = {"start_x_position_V_00": 0, "start_y_position_V_01": 0,
                                       "final_x_position_V_02": 0.5, "final_y_position_V_03": 0.5,
                                       "transit_time_s_04": 1}
            Default values are shown in the Pyscanner. If fpga_tip_parms_dict is None, default values will be used.
            make_cur_pos_start_pos (bool): Flag indicating whether to move from the current position.
                Set it to True when moving from the current position. (default: True)
            do_probe_move_update (bool): Flag indicating whether to update the tip move parameters.
                Set it to True to load the input parameters. (default: True)
            do_probe_move (bool): Flag indicating whether to move the probe.
                Set it to True to move the probe. (default: True)
        """
        # Read current parameters
        default_control_cluster = self.VIs.getcontrolvalue("line_scan_control_cluster")

        # Set default value for tip move parameters
        tipmove_parms_list = [default_control_cluster[0], default_control_cluster[1], default_control_cluster[2],
                              default_control_cluster[3], default_control_cluster[4]]
        tipmove_parms_name_list = ["start_x_position_V_00", "start_y_position_V_01", "final_x_position_V_02", 
                                   "final_y_position_V_03", "transit_time_s_04"]
        
        # if user customized some parameters, update them accordingly
        if fpga_tip_parms_dict!=None:
            for i in range (len (tipmove_parms_list)):
                if tipmove_parms_name_list[i] in fpga_tip_parms_dict:
                    tipmove_parms_list[i] = fpga_tip_parms_dict[tipmove_parms_name_list[i]]

        # if we move from current position, set make_cur_pos_start_pos
        self.VIs.setcontrolvalue("make_cur_pos_start_pos", (make_cur_pos_start_pos))
        time.sleep(0.1) #wait a moment for update

        # update tip move parameters
        self.VIs.setcontrolvalue("do_probe_move_update", (do_probe_move_update))
        # wait until update is done
        while self.VIs.getcontrolvalue("do_probe_move_update"):
            time.sleep(0.1) 

        # move tip
        self.VIs.setcontrolvalue("do_probe_move", (do_probe_move))
        # wait until tipmove is done
        while self.VIs.getcontrolvalue("do_probe_move"):
            time.sleep(0.1) 
        time.sleep(0.1)

        return
    
    def fpga_linebyline_raster_scan(self, line_by_line_raster_dict=None, initialize_line_by_line_raster=True,
                                    do_full_raster_scan=True, wait_to_advance_to_next_line=False,
                                    do_next_raster_line_only=False, stop_full_raster_scan=False):
        """
        Perform a slow raster scan, either by performing a full raster scan or advancing line by line.

        Args:
            line_by_line_raster_dict (dict): Dictionary of line-by-line raster scan parameters. 
                Example:
                    line_by_line_raster_dict = {"raster_scan_size_x_V_00": 1,
                                                "raster_scan_size_y_V_01": 1,
                                                "raster_N_scan_lines_02": 64,
                                                "raster_line_duration_s_03": 1,
                                                "scan_x_offset_V_04": 0,
                                                "scan_y_offset_V_05": 0,
                                                "scan_rotation_deg_06": 0}

            If line_by_line_raster_dict is None, default values shown in Pyscanner will be used.
            initialize_line_by_line_raster (bool): Flag indicating whether to initialize the line-by-line raster scan.
                Set it to True to initialize the scan. (default: True)
            do_full_raster_scan (bool): Flag indicating whether to perform a full raster scan.
                Set it to True to perform the full scan. (default: True)
            wait_to_advance_to_next_line (bool): Flag indicating whether to advance line by line.
                Set it to True to perform scan line by line. (default: False)
            do_next_raster_line_only (bool): Flag indicating whether to perform the next raster line only.
                Set it to True to perform the next line only. (default: False)
            stop_full_raster_scan (bool): Flag indicating whether to stop the full raster scan.
                Set it to True to stop the scan. (default: False)
        """

        # Read current parameters
        default_raster_cluster = self.VIs.getcontrolvalue("line_by_line_raster_scan_control_cluster")

        # Set default values
        lbl_raster_parms_list = [default_raster_cluster[0], default_raster_cluster[1], default_raster_cluster[2],
                                 default_raster_cluster[3], default_raster_cluster[4], default_raster_cluster[5],
                                 default_raster_cluster[6]]
        lbl_raster_parms_name_list = ["raster_scan_size_x_V_00", "raster_scan_size_y_V_01", "raster_N_scan_lines_02", 
                                      "raster_line_duration_s_03", "scan_x_offset_V_04", "scan_y_offset_V_05",
                                      "scan_rotation_deg_06"]

        # if user customized some parameters, update them accordingly
        if line_by_line_raster_dict!=None:
            for i in range (len (lbl_raster_parms_list)):
                if lbl_raster_parms_name_list[i] in line_by_line_raster_dict:
                    lbl_raster_parms_list[i] = line_by_line_raster_dict[lbl_raster_parms_name_list[i]]
        
        # initialize line by line raster
        self.VIs.setcontrolvalue("initialize_line_by_line_raster", (initialize_line_by_line_raster))
        # wait until initialization is done
        while self.VIs.getcontrolvalue("initialize_line_by_line_raster"):
            time.sleep(0.1) 
        
        # if not advance line by line, do full scan
        if wait_to_advance_to_next_line==False:
            # do full scan
            self.VIs.setcontrolvalue("do_full_raster_scan", (do_full_raster_scan))
            # wait until full scan is done
            while self.VIs.getcontrolvalue("do_full_raster_scan"):
                time.sleep(1) 
        
        # if not advance line by line, do full scan
        if wait_to_advance_to_next_line==True:
            self.VIs.setcontrolvalue("do_next_raster_line_only", (do_next_raster_line_only))
            while self.VIs.getcontrolvalue("do_next_raster_line_only"):
                time.sleep(0.1)

        ##################Read results#####################
        ###################################################

        return