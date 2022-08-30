#!/Users/jirigalatu/opt/miniconda3/envs/drex/bin/python3
import glob
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import argparse
import sys


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
    return [item for sublist in t for item in sublist]


try:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="a string that indicates the path ", type=str)
    parser.add_argument("html", help="a string as an output filename", type=str)
    args = parser.parse_args()

    print("-------Starting------")

    path = args.path

    paths = find_all_folders(path)

    sub_folders = {}
    for path in paths:
        sub_folders[path.name] = find_all_folders(path)

    xmls = {}
    for key in sub_folders.keys():
        xml = []
        for folder in sub_folders[key]:
            xml.append(find_xml_files(str(folder)))
        xmls[key] = flatten(xml)

    meta_info = []
    for key in xmls.keys():
        for xml in xmls[key]:
            print(key, xml)
            pathlib_obj = Path(xml)
            xml_filename_split = pathlib_obj.stem.split("_")
            adu = xml_filename_split[0]
            sample_freq = xml_filename_split[6].replace("H", "")
            if pathlib_obj.stat().st_size != 0:
                try:
                    root = ET.parse(xml).getroot()
                    # sample_freq = root[0][8][0][0][1].text
                    if int(sample_freq) != 131072:
                        start_date = root[0][2].text
                        stop_date = root[0][2].text
                        coil_serial_numbers = []
                        if str(root[0][8][0])[10:15] == "ADU07":
                            instrument_serial_number = "ADU07" + "-" + adu
                            meas_channels = root[0][8][0][0][0].text
                            for coil_number in root.iter('ci_serial_number'):
                                coil_serial_numbers.append(coil_number.text)
                        else:
                            instrument_serial_number = root[0][8][0].attrib["Name"] + "-" + adu
                            meas_channels = root[0][8][0][0][0].text
                            for coil_number in root.iter('ci_serial_number'):
                                coil_serial_numbers.append(coil_number.text)

                        meta_info.append(
                            [key, instrument_serial_number, meas_channels, sample_freq, start_date, stop_date,
                             coil_serial_numbers])
                except:
                    print(key, "invalid file", xml)

    header = ['SiteID', 'Instrument', "nC", "Sampling Rate", "Start Date", "Stop Date", "Coils"]
    df = pd.DataFrame(meta_info, columns=header).sort_values(by=['SiteID'])
    df.to_html(buf=args.html, index=False, na_rep=' ', justify="center", escape=False)
    print("Done!")
except:
    e = sys.exc_info()[0]
    print(e)
