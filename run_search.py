import sys
import os
import re
import json
from datetime import datetime

import OpenImageIO as OpenIO
from collections import defaultdict, OrderedDict

# Regex matches name, udim, extension.
TXT_REGEX = re.compile(r'^(?P<name>.*?)[^\d](?P<udim>\d{4})\.(?P<ext>\w+)$')
TARGET_FILETYPES = {"tif", "exr", "txt", "jpeg", "jpg"}
OUTDIR = "/path/to/temp/file/folder"


def log(msg): print(msg, flush=True)


def valid_file_num(path: str=None) -> bool:
    """Returns false for max files, no files."""
    MAX_FILES = 3200
    count = 0
    for _,_, files in os.walk(path):
        for file in files:
            count += 1
            if count >= MAX_FILES:
                log(f"[FileCount] {count}")
                log(f"[MaxFileError] '{count}' files found, aborting image search.")
                return False
    if count == 0:
        log(f"[ZeroFileError] '{count}' image files found in {path}")
        return False
    else:
        log(f"[FileCount] {count}")
        return True
    
    
def user_input_handling(input_path: str=None) -> bool:
    if not input_path:
        log("[InvalidPathError] Input is equating to None.")
        return False
    
    if valid_file_num(input_path):
        log(f"[ValidPath] Input path valid {input_path}")
        return True
    else:
        return False
    

def get_metadata(image_list: list) -> list:
    """Collects key image information appends to dict
    then returns list."""
    for image_dict in image_list:
        file_path = image_dict.get("path")
        if os.path.exists(file_path):
            image_obj = OpenIO.ImageInput.open(file_path)
            if not image_obj:
                log(f"[MetadataError] ImageIO failed to open image: {file_path}")
                continue
            try:
                spec = image_obj.spec()
                image_dict["res"] = f"{spec.width}x{spec.height}"
                if hasattr(spec, "extra_attribs") and spec.extra_attribs:
                    image_dict["bitdepth"] = spec.extra_attribs[0].value
                image_dict["channels"] = getattr(spec, "nchannels", None)
            except Exception as e:
                log(f"[MetadataError] Exception raised while reading image {e}")
            finally:
                if image_obj:
                    image_obj.close()
        else:
            log(f"[ImageFileNotFoundError] {file_path}")
    return image_list


def find_target_files(input_path: str) -> list:
    """Returns a list of image files, seperated into
    a dictionary for each file."""
    log("[DEBUG] find target files func started.")
    image_file_list = []
    for dirpath, _, files in os.walk(input_path):
        for file in files:
            match = TXT_REGEX.match(file)
            if match and match.group("ext") in TARGET_FILETYPES:
                image_info = {
                    "name": match.group("name"),
                    "udim": match.group("udim"),
                    "file_type": match.group("ext"),
                    "path": os.path.join(dirpath, file)
                            }
                image_file_list.append(image_info)
    return image_file_list 


def collect_image_data(path: str):
    target_files = find_target_files(path)
    target_files_and_image_data = get_metadata(target_files)
    return target_files_and_image_data


def organise_image_data(image_dict: dict) -> dict:
    """Organise a nested dictionary with following structure
    name; ext; [{udims / images}]."""
    organized = defaultdict(lambda: defaultdict(list))

    for d in image_dict:
        name = d["name"]
        ext = d["file_type"]
        image = {"udim": d["udim"], 
                 "path": d["path"], 
                "res": d["res"], 
                "bitdepth": d["bitdepth"], 
                "channels": d["channels"]}
        organized[name][ext].append(image)

    # Sort keys / file names alphabetically.
    organised_keys = OrderedDict(sorted(organized.items()))

    # Sort images / udims numerically 1001-1050 etc.
    for name in organised_keys:
        for ext in organised_keys[name]:
            organised_keys[name][ext].sort(key=lambda x: x["udim"])
    
    # Convert back to normal dict.
    organized = {k: dict(v) for k, v in organised_keys.items()}
    return organized


def time_stamp():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return timestamp


def write_data_to_file(out_dir: str, data: dict):
    """Write dict data to json file."""
    time = time_stamp()
    try:
        if not data:
            raise Exception("Data None when passed to function")
        
        out_path = f"{out_dir}/img_search_{time}.json"
        with open(out_path, "w") as f:
            json.dump(data, f, indent=4)
        
        log(f"[INFO] File wrote to: {out_path}")
        log(f"[DataPath] {out_path}")

    except Exception as e:
        log(f"[WriteDataError] Error called while writing data: {e}")


def main(arg: str=None):
    log("[DEBUG] Main module in run search started.")
    path = arg
    if user_input_handling(path):
        image_search_data = collect_image_data(path)
        
        if image_search_data:
            searh_data_organised = organise_image_data(image_search_data)
            write_data_to_file(OUTDIR, searh_data_organised)
        else:
            log("[NoTargetFiles] No target files found in path.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        log("[SubprocessError] no arg passed to run_search")
        sys.exit(1)
    
    arg = str(sys.argv[1])

    log(f"[DEBUG] Arg passed {arg}")

    main(arg)
