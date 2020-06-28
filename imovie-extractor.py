import logging
import os
import shutil
import datetime
from pytz import timezone

imovie_root = "/Volumes/Mobile/iMovie Library Mobile.imovielibrary"
extraction_root = "/Volumes/Mobile/Home Movies 3"
# imovie_root = "/Users/brett/Develop/Working/iMovieTest/In"
# extraction_root = "/Users/brett/Develop/Working/iMovieTest/Out"
skip_titles = []
start_directory = None
single_mode = False
pacific_timezone = timezone("America/Los_Angeles")
utc_timezone = timezone("UTC")
handbrake_preset = "Fast 1080p30"
video_extension = ".m4v"

logger = logging.getLogger(__name__)


def main():
    start_time = datetime.datetime.now()
    logging.basicConfig(format='%(asctime)s  %(levelname)s:  %(message)s', level=logging.INFO)

    extract(imovie_root, extraction_root)

    duration = datetime.datetime.now() - start_time
    logging.info(f"Completed in {duration}")


def extract(root_directory, extraction_root):
    directories = os.walk(root_directory)
    start_processing = start_directory is None
    for directory in directories:
        directory_name = os.path.basename(os.path.normpath(directory[0]))

        if "Original Media" in directory[1]:
            if not start_processing:
                if directory_name == start_directory:
                    start_processing = True
                    logging.info(f"Start processing at {directory_name}")
                else:
                    logging.info(f"Skipping {directory_name}")
                    continue

            current_title = directory_name
            if current_title.startswith("20") and current_title[0:4].isnumeric():
                current_title = current_title[8:]
            logging.info(f"Current title: {current_title}")

        if directory_name == "Original Media" and start_processing and current_title not in skip_titles:
            for file in directory[2]:
                if file.startswith("."):
                    continue

                file_name, file_extension = os.path.splitext(file)
                file_path = os.path.join(directory[0], file)
                if file_name.startswith("clip-"):
                    year = int(file_name[5:9])
                    month = int(file_name[10:12])
                    day = int(file_name[13:15])
                    hour = int(file_name[16:18])
                    minute = int(file_name[19:21])
                    second = int(file_name[22:24])
                    create_datetime = pacific_timezone.localize(datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second))
                else:
                    stat = os.stat(file_path)
                    birth_time = stat.st_birthtime
                    create_datetime = datetime.datetime.utcfromtimestamp(birth_time).replace(tzinfo=timezone("UTC")).astimezone(pacific_timezone)

                if file_extension == ".dv" or file_name.startswith("clip-") or file_name.startswith("MVI_"):
                    requires_transcode = True
                    new_file_extension = video_extension
                elif file_name.startswith("P") and file_extension == ".mov":
                    requires_transcode = True
                    new_file_extension = video_extension
                elif file_name.startswith("IMG_"):
                    requires_transcode = False
                    new_file_extension = file_extension
                else:
                    logging.warning(f"File name doesn't follow established patter: {file_name}")
                    requires_transcode = False
                    new_file_extension = file_extension

                date_string = create_datetime.strftime("%Y-%m-%d")
                new_directory_name = f"{date_string} {current_title}"
                logging.info(f"New directory name: {new_directory_name}")
                new_directory_path = os.path.join(extraction_root, new_directory_name)
                if not os.path.exists(new_directory_path):
                    os.makedirs(new_directory_path)

                file_name_timestamp = create_datetime.strftime("%Y-%m-%d %H;%M;%S")
                new_file_name = f"{file_name_timestamp} {current_title}{new_file_extension}"
                logging.info(f"New file name: {new_file_name}")
                new_file_path = os.path.join(new_directory_path, new_file_name)
                if os.path.exists(new_file_path):
                    raise Exception(f"Path already exists at {new_file_path}")
                else:
                    if requires_transcode:
                        transcode(file_path, new_file_path)
                        transfer_exif(file_path, new_file_path)
                    else:
                        shutil.copyfile(file_path, new_file_path)

                set_exif_title(new_file_path, current_title)
                if requires_transcode:
                    set_exif_createtime(new_file_path, create_datetime)

            if single_mode and start_processing:
                break


def transcode(original_file, new_file):
    convert_command = f"HandbrakeCLI --input \"{original_file}\" --output \"{new_file}\" --preset \"{handbrake_preset}\""
    execute_command(convert_command)


def transfer_exif(original_file, new_file):
    transfer_exif_command = f"exiftool -TagsFromFile \"{original_file}\" \"{new_file}\""
    execute_command(transfer_exif_command)


def set_exif_title(file, title):
    set_title_command = f"exiftool -title=\"{title}\" \"{file}\""
    execute_command(set_title_command)


def set_exif_createtime(file, create_datetime):
    utc_datetime = datetime.datetime.utcfromtimestamp(create_datetime.timestamp())
    utc_string = utc_datetime.strftime("%Y:%m:%d %H:%M:%S")
    set_original_command = f"exiftool -xmp:dateTimeOriginal=\"{utc_string}\" \"{file}\""
    execute_command(set_original_command)

    original_to_createtime_command = f"exiftool \"-DateTimeOriginal>CreateDate\" \"{file}\""
    execute_command(original_to_createtime_command)

    local_string_raw = create_datetime.strftime("%Y:%m:%d %H:%M:%S%z")
    local_string = local_string_raw[:22] + ":" + local_string_raw[22:]
    set_createtime_command = f"exiftool -xmp:CreateDate=\"{local_string}\" \"{file}\""
    execute_command(set_createtime_command)

    set_original_command2 = f"exiftool -xmp:dateTimeOriginal=\"{local_string}\" \"{file}\""
    execute_command(set_original_command2)


def execute_command(command):
    logging.info(f"Executing: {command}")
    os.system(command)


main()