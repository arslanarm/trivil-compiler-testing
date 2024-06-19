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


def print_with_color(text: str, color: str, end='\n'):
    """
    Prints the given text with the specified ANSI color.
    Args:
    text (str): The text to print.
    color (str): The color name, which can be 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', or 'white'.
    """
    color_codes = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m'
    }
    reset_code = '\033[0m'
    colored_text = f"{color_codes.get(color, '')}{text}{reset_code}"
    print(colored_text, end=end)



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


class Tester:
    counts = {"___other": {"total": 0, "fails": 0}}


    def test_failed(self, key, file_path):
        if key not in self.counts:
            self.counts[key] = {"total": 0, "fails": 0}
        count = self.counts[key]
        count["total"] += 1
        count['fails'] += 1
        print_with_color(f"FAIL: {file_path}", color='red')

    def test_passed(self, key, file_path):
        if key not in self.counts:
            self.counts[key] = {"total": 0, "fails": 0}
        count = self.counts[key]
        count["total"] += 1
        print_with_color(f"OK: {file_path}", color='green')
    
    def print_report(self):
        for key in sorted(self.counts.keys()):
            value = self.counts[key]
            if key == "___other":
                if value["total"] > 0:
                    print("Other: ", end='')
                else:
                    continue
            else:
                print(key + ': ', end='')
            if value['fails'] > 0:
                print_with_color(f"Failed tests: {value['fails']}/{value['total']}", color='red')
            else:
                print_with_color(f"All tests passed: {value['total']}", color='green')


def main():
    parser = argparse.ArgumentParser(description='CLI tool to test compiler "tric".')
    parser.add_argument('inputdir', help='The input directory to test with "tric".')
    parser.add_argument('-l', '--result_level', help='Nesting level of the folders that will be grouped by for showing a results', type=int, required=False, default=0)
    args = parser.parse_args()

    input_dir_abs_path = os.path.abspath(args.inputdir)
    base_level = level_of_nestedness(input_dir_abs_path)
    result_level = base_level + args.result_level

    tester = Tester()

    for root, dirs, files in os.walk(args.inputdir):
        root_abs_path = os.path.abspath(root)
        nestedness = level_of_nestedness(root_abs_path)
  
        for file in files:
            if not file.endswith(".tri"):
                continue
            base = unnest(root, nestedness - result_level)
            key = base.removesuffix('/')
           
            file_path = os.path.join(root, file)
            result = test(file_path)

            manifest = load_manifest(os.path.join(root, file + ".json"))
            if manifest is None or manifest.type == "success":
                match result:
                    case CompileError(stderr=output):
                        tester.test_failed(key, file_path)
                        print("Compiler error: " + output)
                    case RuntimeError():
                        tester.test_failed(key, file_path)
                        print(f"Runtime error")
                    case Success(stdout=output):
                        if not correct_output(manifest, output):
                            tester.test_failed(key, file_path)
                            print(f"Stdout doesn't match:\nExpected:\n{manifest.stdout}\nActual:\n{output}")
                        else:
                            tester.test_passed(key, file_path)
                    case _:
                        assert False
            elif manifest.type == "compiler_error":
                match result:
                    case CompileError(stderr=output):
                        tester.test_passed(key, file_path)
                    case RuntimeError():
                        tester.test_failed(key, file_path)
                        print("Didn't return compile error(Runtime error)")
                    case Success(stdout=output):
                        tester.test_failed(key, file_path)
                        print("Didn't return compile error(Ran succesfully)")
                    case _:
                        assert False
            elif manifest.type == "runtime_error":
                match result:
                    case CompileError(stderr=output):
                        tester.test_failed(key, file_path)
                        print("Didn't return runtime error(Compile error)")
                    case RuntimeError():
                        tester.test_passed(key, file_path)
                    case Success(stdout=output):
                        tester.test_failed(key, file_path)
                        print("Didn't return runtime error(Ran succesfully)")
                    case _:
                        assert False
            else:
                print(f"ERROR: manifest type in {file_path}.json is incorrect")

    print("-------REPORT--------")
    tester.print_report()
    print("-------REPORT--------")


if __name__ == "__main__":
    main()

