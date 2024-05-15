# Trivil Compiler Tests

### Running tests

To run tests, you must have a trivil compiler. For the testing of the test suite, language author's compiler was used: [tric](https://gitflic.ru/project/alekseinedoria/trivil-0)

At times of writing the test, the behavior of the compiler was not specified, and the only work around was that, test cases must be run in the same directory as the compiler.

```bash
./test.py <directory of the test_suite>
```

`test.py` assumes that the compiler is named `tric` and is located in the PATH.
The tester will copy each test_case into the WORKDIR, and will run `tric` for this directory.
`tric` outputs the executable file in the format of `<module_name>.exe`. Tester will run this file and in the end, will delete this executable file and the source file that was copied. In the case of an error, a source file or an executable file can be still remain in the WORKDIR. 

NOTE: If there are any .tri files in the WORKDIR, `tric` might not work as expected.