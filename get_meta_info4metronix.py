import glob
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
def find_files(fullpath, file_extension):
    """
    find all files with the given file extension in the directory linked to the given path
    :file_extension: a string in the form of  "*.xml", "*.json" "*.ats"
    :return: a list of filenames or paths of xml files
    """
    list_of_files = []
    # make sure the given path ends with /
    if fullpath[-1] != '/':
        fullpath = fullpath + '/'
    # retrieve all json files in the given directory
    for filename in glob.glob(fullpath + file_extension):
        list_of_files.append(filename)
    # sort the list according the filenames.
    list_of_files.sort()
    return list_of_files

def find_xml_files(fullpath):
    """
    find all xml files in the directory linked to the given path
    :return: a list of filenames or paths of xml files
    """
    list_of_files = []
    # make sure the given path ends with /
    if fullpath[-1] != '/':
        fullpath = fullpath + '/'
    # retrieve all json files in the given directory
    for json_filename in glob.glob(fullpath + "*.xml"):
        list_of_files.append(json_filename)
    # sort the list according the filenames.
    list_of_files.sort()
    return list_of_files


def find_all_folders(fullpath):
    """fina all folders inside the given path."""
    subdirs = []
    pathlib_obj = Path(fullpath)
    for subdir in pathlib_obj.iterdir():
        # first it has to be a folder
        # second it is a not hidden folder
        if subdir.is_dir() and (subdir.name[0] != "."):
            subdirs.append(subdir)
    return subdirs

def flatten(t):
    """Convert nested lists into a flat list"""
    return [item for sublist in t for item in sublist]

def unique_coilset(pd_series):
    num = len(pd_series)
    # ignore empty elements in the given list
    list_no_empty_coilset = [element for element in pd_series if len(element) != 0]
    unique_coilset = []
    if len(list_no_empty_coilset) != 0:
        # keep the elements not in the unique_coilset
        for element in list_no_empty_coilset:
            # print(ref, element, element == ref)
            if element not in unique_coilset:
                unique_coilset.append(element)
    # remove the extra square brackets if there is only one set of coil
    if len(unique_coilset) == 1:
        unique_coilset = unique_coilset[0]
    return unique_coilset

def get_run_numbers_from_atsfiles(path):
    """Find the run number in a given folder"""
    # find a list of files with a given file extension
    filepaths = find_files(path, "*.ats")
    # convert filepath into pathlib_obj
    filepaths_pathlibObj = [Path(filepath) for filepath in filepaths]
    filenames_split = [item.stem.split("_") for item in filepaths_pathlibObj]
    # find the unique run number from all found ats files.
    run_numbers = []
    for filename in filenames_split:
        if filename[3] not in run_numbers:
            run_numbers.append(filename[3])

    return run_numbers

def is_run_number_in_filename(run_number, filepath):
    """Check if the given run number is in the given filename"""
    # convert filepath into a pathlib object
    if type(filepath).__name__ != "pathlib.PosixPath":
        filepath_pathlibObj = Path(filepath)
    else:
        filepath_pathlibObj = filepath
    filename_split = filepath_pathlibObj.stem.split("_")
    if run_number in filename_split:
        return True
    else:
        return False

def extract_meta_info4metronix(fullpath):
    paths = find_all_folders(fullpath)
    # get a list of all sub_folders of each parent folder
    sub_folders = {}
    for path in paths:
        # a dictionary key the name of the parent folder
        # the corresponding value is a list of the paths of all subfolders
        sub_folders[path.name] = find_all_folders(path)

    # find all xml files in each subfolders
    xmls = {}
    for key in sub_folders.keys():
        xml = []
        for folder in sub_folders[key]:
            xml.append(find_xml_files(str(folder)))
        # xmls is dictionary as well
        # keys are the key of the parent folder as well
        # values are the full path of all xml files found in the range of the parent folder
        xmls[key] = flatten(xml)

    # meta info is a list which for the moment only stores some basic information
    meta_info = []
    file_invalid = []
    header = ['SiteID', 'Instrument', "nC", "Sampling Rate", "Start Date", "Stop Date", "Coil"]
    for key in xmls.keys():
        for xml in xmls[key]:
            # check the file is empty
            # if pathlib_obj.stat().st_size != 0:
            # convert string-formatted path into Pathlib
            pathlib_obj = Path(xml)
            # find run number from the same folder where the xml file is.
            run_numbers = get_run_numbers_from_atsfiles(str(pathlib_obj.parent))
            # split filename into several parts
            xml_filename_split = pathlib_obj.stem.split("_")
            for run_number in run_numbers:
                if run_number in xml_filename_split:
                    # adu serial number always comes at the beginning of the filename
                    adu = xml_filename_split[0]
                    # the actual sampling rate always comes at the end of the filename
                    sample_freq = xml_filename_split[6].replace("H", "")
                    try:
                        # get root of an xml file
                        root = ET.parse(xml).getroot()
                        # sample_freq = root[0][8][0][0][1].text
                        if int(sample_freq) != 131072:
                            print(key, pathlib_obj.stem)
                            # start date is written the xml file
                            start_date = root[0][2].text
                            # start date is written the xml file
                            stop_date = root[0][2].text
                            # the number channels are also written
                            meas_channels = root[0][8][0][0][0].text
                            # Search coil number with key word
                            coil_serial_numbers = []
                            # find the model name of adus
                            if str(root[0][8][0])[10:15] == "ADU07":
                                instrument = "ADU-07" + "-" + adu
                                for coil_number in root.iter('sensor_sernum'):
                                    coil_serial_numbers.append(coil_number.text)
                            else:
                                instrument = root[0][8][0].attrib["Name"] + "-" + adu
                                for coil_number in root.iter('ci_serial_number'):
                                    coil_serial_numbers.append(coil_number.text)
                            # if everything is ok, the meta info extracted is appended to the list
                            meta_info.append([key, instrument, meas_channels, sample_freq, start_date, stop_date, coil_serial_numbers])
                    except:
                        # if python has problem to parse the xml file
                        # it means there must something wrong with
                        file_invalid.append([key, pathlib_obj.stem])
                        print(key, pathlib_obj.stem, "-------------------------invalid file")
    # convert the list of meta info into a dataframe to print out
    df_invalid = pd.DataFrame(file_invalid, columns=["SiteID", "Filename"]).sort_values(by=['SiteID'])
    df_meta_info = pd.DataFrame(meta_info, columns=header).sort_values(by=['SiteID'])
    return df_meta_info, df_invalid

def unique_entry(dataframe_obj):
    """Create unique entry for each site, even when it's measured several times"""
    site_meta_list = []
    siteids = pd.unique(dataframe_obj["SiteID"])
    for id in siteids:
        # fina meta info for each site
        site_meta = dataframe_obj[dataframe_obj["SiteID"] == id]
        # manipulate inside each site regarding the meta information
        unique_instrument = pd.unique(site_meta["Instrument"])
        # unique the number of channels
        unique_nC = pd.unique(site_meta["nC"])
        # unique sampling rates
        unique_sample_freq = pd.unique(site_meta["Sampling Rate"])
        # unique set of coil numbers
        # unique_coil_numbers = pd.unique(site_meta["Coil"].apply(str))
        unique_coil_numbers = unique_coilset(site_meta["Coil"])
        # managing the start and stop date for each site
        # for the moment, only keep the very first day when the site set up
        # and the last day the site was collected
        unique_start_date = pd.unique(site_meta["Start Date"].sort_values(ascending=True))[0]
        # the last day
        unique_stop_date = pd.unique(site_meta["Stop Date"].sort_values(ascending=True))[-1]

        site_meta_list.append([id, unique_nC, unique_instrument, sorted(unique_sample_freq), unique_start_date,  unique_stop_date, unique_coil_numbers ])

    df = pd.DataFrame(site_meta_list, columns=["SiteID", "nC", "Instrument", 'Sampling Rate', "Start Date", "Stop Date", "Coil"])

    return df
