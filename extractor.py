
import os
import shutil
import pathlib
import send2trash
import patoolib
from patoolib.util import PatoolError

"""Extracts all archives in the current directory, placing files in destination,
    and deletes the archive."""
def extract_archives(origin, destination):
    
    origin_path = pathlib.Path(origin)

    for file_path_object in origin_path.iterdir():
        if patoolib.is_archive(file_path_object):
            try:
                archive_name_raw = os.path.splitext(file_path_object)[0]  # Name without extension
                sanitized_name = "".join([
                    c if c.isalnum() or c in ('_', '.') else "_" 
                    for c in archive_name_raw
                ])

                patoolib.extract_archive(str(file_path_object), outdir=destination)

                send2trash.send2trash(str(file_path_object))

            except PatoolError as e:
                print(f"Error extracting {file_path_object}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during extraction of {file_path_object}: {e}")




# -------------------------------------------------------

"""Potentially useful for compressing storage en masse"""

# def extract_archives():
#     """Extracts all archives in the current directory."""

#     for filename in os.listdir("."):
#         if patool.is_archive(filename):
#             try:
#                 print(f"Processing archive: {filename}")
#                 archive_name = os.path.splitext(filename)[0]  # Name without extension

#                 # Create a temporary directory for extraction
#                 temp_dir = f".temp_{archive_name}"
#                 os.makedirs(temp_dir, exist_ok=True)

#                 patool.extract_archive(filename, outdir=temp_dir)

#                 extracted_files = os.listdir(temp_dir)
#                 num_files = len(extracted_files)

#                 if num_files == 1:
#                     extracted_path = os.path.join(temp_dir, extracted_files[0])
#                     if os.path.isdir(extracted_path): # if the single file is a directory
#                         shutil.move(extracted_path, ".") # moves the directory to the current path
#                     else:
#                         shutil.move(extracted_path, archive_name) # moves the file to a folder named after the archive
#                         print(f"Extracted single file to: {archive_name}")
#                 elif num_files > 1:
#                     output_dir = archive_name
#                     os.makedirs(output_dir, exist_ok=True)
#                     for extracted_file in extracted_files:
#                         source_path = os.path.join(temp_dir, extracted_file)
#                         shutil.move(source_path, output_dir)
#                     print(f"Extracted multiple files to: {output_dir}")
#                 else: # if the archive is empty
#                     print(f"Archive {filename} is empty")

#                 shutil.rmtree(temp_dir) # clean up temporary directory

#             except patool.PatoolError as e:
#                 print(f"Error extracting {filename}: {e}")
#             except Exception as e:
#                 print(f"An unexpected error occurred during extraction of {filename}: {e}")


# extract_archives()