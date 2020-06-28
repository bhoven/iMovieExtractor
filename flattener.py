import logging
import os
import shutil
import datetime


hierarchy_root = "/Volumes/Mobile/Home Movies 3"
flat_root = "/Volumes/Mobile/Home Movies Flat"


def main():
    start_time = datetime.datetime.now()
    logging.basicConfig(format='%(asctime)s  %(levelname)s:  %(message)s', level=logging.INFO)

    directories = os.walk(hierarchy_root)
    for directory in directories:
        for file in directory[2]:
            if file.startswith(".") or file.endswith("_original"):
                continue

            file_path = os.path.join(directory[0], file)
            new_file_path = os.path.join(flat_root, file)
            if os.path.exists(new_file_path):
                raise Exception(f"Path already exists at {new_file_path}")
            shutil.copyfile(file_path, new_file_path)

    duration = datetime.datetime.now() - start_time
    logging.info(f"Completed in {duration}")


main()
