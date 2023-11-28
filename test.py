#!/usr/bin/python
import os
import shutil
import argparse

def test(input_file):
    shutil.copy(input_file, '.')

    output = os.popen(f"tric {os.path.basename(input_file)}").read()
    
    os.remove(os.path.basename(input_file))
    if "Без ошибок" not in output:
        return False, output
    generated_file_name = '_'.join(os.path.basename(input_file).split('_')[1:])[:-3] + "exe"
    status = os.system(f"./{generated_file_name}")
    if status != 0:
        return False, "Runtime error"
    os.remove(generated_file_name)
    return True, output

def main():
    parser = argparse.ArgumentParser(description='CLI tool to test compiler "tric".')
    parser.add_argument('inputdir', help='The input directory to test with "tric".')
    args = parser.parse_args()

    test_count = 0
    fail_count = 0

    for root, dirs, files in os.walk(args.inputdir + "/positive"):
        for file in files:
            test_count += 1
            result, output = test(os.path.join(root, file))
            if not result:
                fail_count += 1
                print(f"Error in file {file}:\n{output}")
    print(f"Successful tests: {test_count - fail_count}")
    print(f"Overall test: {test_count}")


if __name__ == "__main__":
    main()

