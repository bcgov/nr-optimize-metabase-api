# =======================================
# To build into an exe:
# 1. Navigate to this directory
# 2. Run: pip install pyinstaller
# 3. Run: pyinstaller --onefile h-drive-tree-size.py
# The module will create quite a few files, hopefully printing "Building EXE from ____ completed successfully" in terminal
# 4. Copy h-drive-tree-size.exe from dist folder to this directory before checking in code.
# =======================================
# Shorthand used:
# fp = folder path
import os


# Return a dictionary of folder name > size in mb
def tree_fetch(root):
    dir_dict = {}
    for root, dirs, files in os.walk(root):
        if root not in dir_dict.keys():
            dir_dict[root] = 0
        # for d in dirs:
            # print(os.path.join(root, d))
        for f in files:
            size_mb = os.path.getsize(os.path.join(root, f))/1024/1024
            dir_dict[root] += size_mb
    return dir_dict


# Writes a list to a file
def write_list(file_name, list=[]):
    with open(file_name, "w") as f:
        for line in list:
            f.write(line)
            f.write("\n")


def main():
    idir = os.getlogin()
    idir_fp = '\\\\Sfp.idir.bcgov\\u140\\' + idir + '$'
    print(f"Checking H: Drive for {idir} at {idir_fp}")
    if (os.path.isdir(idir_fp)):
        print("H: Drive found!")
        print("Counting folder sizes. Please wait...")
        dir_tree = tree_fetch(idir_fp)
        dir_list = []
        dir_list.append("Directory,Size (MB)")
        for folder_path in dir_tree:
            folder_size = dir_tree[folder_path]
            if folder_size > 1:
                name = folder_path.split(idir_fp)[1]
                dir_list.append(f"{name},{folder_size:0.2f}")
        write_list(os.path.join(idir_fp, "h_drive_directory_sizes.csv"), dir_list)
    input("Script Complete. A file named large_h_drive_directories.csv has been created in your H: Drive.")


if __name__ == "__main__":
    main()
