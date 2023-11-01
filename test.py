#!/usr/bin/python
import os
import shutil
import argparse

def test(input_file):
    shutil.copy(input_file, '.')

    output = os.popen(f"tric {os.path.basename(input_file)}").read()
    
    os.remove(os.path.basename(input_file))
    if "Без ошибок" in output:
        os.remove('_'.join(os.path.basename(input_file).split('_')[1:])[:-3] + "exe")
        return True, output
    return False, output

def main():
    parser = argparse.ArgumentParser(description='CLI tool to test compiler "tric".')
    parser.add_argument('inputdir', help='The input directory to test with "tric".')
    args = parser.parse_args()

    for root, dirs, files in os.walk(args.inputdir):
        for file in files:
            result, output = test(os.path.join(root, file))
            if not result:
                print(f"Error in file {file}:\n{output}")
 

if __name__ == "__main__":
    main()

