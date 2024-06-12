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


def level_of_nestedness(path):
    if path.strip():
        head, tail = os.path.split(path)
        if len(tail) == 0 or path == tail:
            return 1
        return 1 + level_of_nestedness(head)
    return 0


def unnest(path, how_much):
    assert how_much >= 0
    if how_much == 0:
        return path
    return unnest(os.path.dirname(path), how_much - 1)


def main():
    parser = argparse.ArgumentParser(description='CLI tool to test compiler "tric".')
    parser.add_argument('inputdir', help='The input directory to test with "tric".')
    parser.add_argument('-l', '--result_level', help='Nesting level of the folders that will be grouped by for showing a results', type=int, required=False, default=0)
    args = parser.parse_args()

    input_dir_abs_path = os.path.abspath(args.inputdir)
    base_level = level_of_nestedness(input_dir_abs_path)
    result_level = base_level + args.result_level

    counts = {"___other": {"total": 0, "fails": 0}}
    test_count = 0
    fail_count = 0

    for root, dirs, files in os.walk(args.inputdir):
        root_abs_path = os.path.abspath(root)
        nestedness = level_of_nestedness(root_abs_path)
  
        for file in files:
            base = unnest(root, nestedness - result_level)
            key = base.removesuffix('/')
            if key not in counts:
                counts[key] = {"total": 0, "fails": 0}
            count = counts[key]
            if not file.endswith(".tri"):
                continue
            count["total"] += 1
            file_path = os.path.join(root, file)
            result = test(file_path)

            manifest = load_manifest(os.path.join(root, file + ".json"))
            if manifest is None or manifest.type == "success":
                match result:
                    case CompileError(stderr=output):
                        count["fails"] += 1
                        print(f"Error in file {file_path}:\n{output}")
                    case RuntimeError():
                        count["fails"] += 1
                        print(f"Error in file {file_path}:\nRuntime error")
                    case Success(stdout=output):
                        if not correct_output(manifest, output):
                            count["fails"] += 1
                            print(f"Error in file {file_path}:\nStdout doesn't match:\nExpected:\n{manifest.stdout}\nActual:\n{output}")
                    case _:
                        assert False
            elif manifest.type == "compiler_error":
                match result:
                    case CompileError(stderr=output):
                        pass
                    case RuntimeError():
                        count["fails"] += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Runtime error)")
                    case Success(stdout=output):
                        count["fails"] += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Ran succesfully)")
                    case _:
                        assert False
            elif manifest.type == "runtime_error":
                match result:
                    case CompileError(stderr=output):
                        count["fails"] += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Compile error)")
                    case RuntimeError():
                        pass
                    case Success(stdout=output):
                        count["fails"] += 1
                        print(f"Error in file {file_path}:\nDidn't return compile error(Ran succesfully)")
                    case _:
                        assert False
            else:
                print(f"ERROR: manifest type in {file_path}.json is incorrect")

            
    for key in sorted(counts.keys()):
        value = counts[key]
        if key == "___other":
            if value["total"] > 0:
                print("Other:")
            else:
                continue
        else:
            print(key)
        print(f"  Successful tests: {value['total'] - value['fails']}")
        print(f"  Overall test: {value['total']}")


if __name__ == "__main__":
    main()

