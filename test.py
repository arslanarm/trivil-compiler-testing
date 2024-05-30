#!/usr/bin/python
from dataclasses import dataclass
import enum
import json
import os
import shutil
import argparse
from typing import Optional

class TestResult:
    pass


@dataclass
class Success(TestResult):
    stdout: str

@dataclass
class CompileError(TestResult):
    stderr: str


@dataclass
class RuntimeError(TestResult):
    pass


@dataclass
class Manifest:
    type: str
    stdout: Optional[str]


def test(input_file) -> TestResult:
    shutil.copy(input_file, '.')

    process = os.popen(f"tric {os.path.basename(input_file)}")
    output = process.read()
    status = process.close()
    
    os.remove(os.path.basename(input_file))
    if (status is not None and status != 0) or "Без ошибок" not in output:
        return CompileError(stderr=output)
    generated_file_name = '_'.join(os.path.basename(input_file).split('_')[1:])[:-3] + "exe"
    process = os.popen(f"./{generated_file_name}")
    output = process.read()
    status = process.close()
    if status is not None and status != 0:
        os.remove(generated_file_name)
        return RuntimeError()
    os.remove(generated_file_name)
    return Success(stdout=output)


def load_manifest(manifest_path) -> Manifest:
    try:
        with open(manifest_path, "r") as f:
            obj = json.load(f)
            return Manifest(obj["type"], None if "stdout" not in obj else obj["stdout"])
    except:
        return None


def correct_output(manifest: Manifest, output):
    try:
        return manifest.stdout is None or manifest.stdout == output
    except:
        return True


def main():
    parser = argparse.ArgumentParser(description='CLI tool to test compiler "tric".')
    parser.add_argument('inputdir', help='The input directory to test with "tric".')
    args = parser.parse_args()

    test_count = 0
    fail_count = 0

    for root, dirs, files in os.walk(args.inputdir):
        for file in files:
            if not file.endswith(".tri"):
                continue
            test_count += 1
            file_path = os.path.join(root, file)
            result = test(file_path)

            manifest = load_manifest(os.path.join(root, file + ".json"))
            if manifest is None or manifest.type == "success":
                match result:
                    case CompileError(stderr=output):
                        fail_count += 1
                        print(f"Error in file {file_path}:\n{output}")
                    case RuntimeError():
                        fail_count += 1
                        print(f"Error in file {file_path}:\nRuntime error")
                    case Success(stdout=output):
                        if not correct_output(manifest, output):
                            fail_count += 1
                            print(f"Error in file {file_path}:\nStdout doesn't match:\nExpected:\n{manifest.stdout}\nActual:\n{output}")
                    case _:
                        assert False
            elif manifest.type == "compiler_error":
                match result:
                    case CompileError(stderr=output):
                        pass
                    case RuntimeError():
                        fail_count += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Runtime error)")
                    case Success(stdout=output):
                        fail_count += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Ran succesfully)")
                    case _:
                        assert False
            elif manifest.type == "runtime_error":
                match result:
                    case CompileError(stderr=output):
                        fail_count += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Compile error)")
                    case RuntimeError():
                        pass
                    case Success(stdout=output):
                        fail_count += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Ran succesfully)")
                    case _:
                        assert False
            else:
                print(f"ERROR: manifest type in {file_path}.json is incorrect")

            
                   
    print(f"Successful tests: {test_count - fail_count}")
    print(f"Overall test: {test_count}")


if __name__ == "__main__":
    main()

