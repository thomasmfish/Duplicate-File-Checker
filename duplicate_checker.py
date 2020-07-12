import os
import sys
import hashlib
from pathlib import Path


def hash_file(path, bits=16):
    block_size = 2**bits
    with path.open('rb') as f:
        hasher = hashlib.md5()
        buf = f.read(block_size)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(block_size)
    return hasher.hexdigest()


def find_duplicates(base_directory, duplicate_dict={}):
    file_list = [path for path in Path(base_directory).rglob("*") if path.is_file()]
    for filename in file_list:
        file_hash = hash_file(filename)
        if file_hash in duplicate_dict:
            duplicate_dict[file_hash].append(str(filename))
        else:
            duplicate_dict[file_hash] = [str(filename)]
    return duplicate_dict

def print_results(duplicate_dict):
    duplicate_file_list = [x for x in duplicate_dict.values() if len(x) > 1]
    if len(duplicate_file_list) > 0:
        print('The following files have identical contents:\n')
        for duplicates_files in duplicate_file_list:
            for duplicate in duplicates_files:
                print('\t\t%s' % duplicate)
            print('----------')
    else:
        print('No duplicate files found')
    return duplicate_file_list

def delete_copies(duplicate_file_list):
    keep_new = str(input("When deleting duplicates, should new or old files be kept? (new/OLD)")).lower() == "new"
    delete_all = str(input("Would you like to delete all newer copies found? BE VERY CAREFUL! (y/N)")).lower() == "y"
    for duplicates_files in duplicate_file_list:
        duplicates_files = duplicates_files.sort(key=os.path.getmtime, reverse=keep_new)
        # Only delete if file suffix is the same for both duplicates
        if len({Path(path).suffix() for path in duplicates_files}) == 1:
            print('----------')
            for duplicate in duplicates_files[1:]:
                if delete_all:
                    _delete(duplicate)
                elif str(input("Would you like to delete file '%s'? (Y/n)" % duplicate)).lower() != "n":
                    _delete(duplicate)
                else:
                    print("Skipping file '%s'" % duplicate)

def _delete(filepath):
    # time = os.path.getmtime(filepath)
    # print("File: %s, time %i, formatted time %s", % (filepath, time, datetime.fromtimestamp(time).strftime("%d-%m-%Y %H:%M:%S")))
    print("Deleting copy: %s" % filepath)
    os.remove(filepath)

def _open_duplicates_file(filepath):
    with filepath.open('r') as f:
        return json.loads(f.read())

def _save_duplicates(duplicates_dict):
    with open("duplicates.json", 'w') as fp:
        json.dump(duplicates_dict, fp)


if __name__ == "__main__":
    import sys
    import json
    for arg in sys.argv[1:]:
        dup_dict = {}
        try:
            argpath = Path(arg).resolve(strict=True)
            if argpath.is_file() and argpath.suffix == ".json":
                print("Opening file hashes from %s" % argpath)
                dup_dict = _open_duplicates_file(argpath)
                argpath = argpath.parent
            if not bool(dup_dict) or str(input("Would you like to search directory '%s' for new duplicates? (y/N)" % argpath)).lower() == "y":
                dup_dict = find_duplicates(argpath, duplicate_dict=dup_dict)
            if bool(dup_dict):
                duplicate_file_list = print_results(dup_dict)
                if str(input("Would you like to save as json? (Y/n)")).lower() != "n":
                    _save_duplicates(dup_dict)
        except FileNotFoundError:
            print("Invalid input '%s'" % arg)
            raise
        if str(input("Would you like to delete newer copies? (y/N)")).lower() == "y":
            delete_copies(duplicate_file_list)
