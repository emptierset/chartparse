import pytest


def new(testname, **kwargs):
    return (testname, kwargs)


def new_anonymous(**kwargs):
    return (kwargs,)


def parametrize(ordered_param_names, testcases, default_values=None):
    unique_param_names = set(ordered_param_names)
    if len(ordered_param_names) != len(unique_param_names):
        raise ValueError(f"input params '{ordered_param_names}' must contain only unique params")

    default_values = dict() if default_values is None else default_values
    param_names_with_default_values = set(default_values.keys())
    if not param_names_with_default_values.issubset(unique_param_names):
        raise ValueError("default_values keys must be a subset of param names")

    def _testcase_to_pytest_param(testcase):
        if len(testcase) == 2:
            testname, testcase_params = testcase
            debugging_testname = testname
        elif len(testcase) == 1:
            testname = None
            (testcase_params,) = testcase
            debugging_testname = "-".join(map(str, testcase_params.values()))
        else:
            raise ValueError(f"testcase {testcase} has unhandled length")

        present_input_param_names = testcase_params.keys() | default_values.keys()
        if present_input_param_names != unique_param_names:
            missing_param_names = unique_param_names.difference(present_input_param_names)
            raise ValueError(
                "all params in input params must be present in either default_values or the "
                "testcase itself;\n"
                f"The testcase named '{debugging_testname}' is missing values for the following "
                "params:\n"
                f"{missing_param_names}"
            )

        param_values_in_order = []
        for param_name in ordered_param_names:
            try:
                param_value = testcase_params[param_name]
            except KeyError:
                param_value = default_values[param_name]
            param_values_in_order.append(param_value)

        if testname is None:
            return pytest.param(*param_values_in_order)
        else:
            return pytest.param(*param_values_in_order, id=testname)

    return pytest.mark.parametrize(
        ",".join(ordered_param_names),
        [_testcase_to_pytest_param(tc) for tc in testcases],
    )
