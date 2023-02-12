import typing as typ
from collections.abc import Mapping, Sequence

import _pytest
import pytest

from chartparse.exceptions import UnreachableError

Testcase = typ.NewType("Testcase", tuple[str, dict[str, typ.Any]])
AnonymousTestcase = typ.NewType("AnonymousTestcase", tuple[dict[str, typ.Any]])


def new(testname: str, **kwargs: typ.Any) -> Testcase:
    return Testcase((testname, kwargs))


def new_anonymous(**kwargs: typ.Any) -> AnonymousTestcase:
    return AnonymousTestcase((kwargs,))


def parametrize(
    ordered_param_names: Sequence[str],
    testcases: Sequence[Testcase | AnonymousTestcase],
    default_values: Mapping[str, typ.Any] | None = None,
) -> _pytest.mark.structures.MarkDecorator:
    unique_param_names = set(ordered_param_names)
    if len(ordered_param_names) != len(unique_param_names):
        raise ValueError(f"input params '{ordered_param_names}' must contain only unique params")

    _default_values = dict() if default_values is None else default_values
    param_names_with_default_values = set(_default_values.keys())
    if not param_names_with_default_values.issubset(unique_param_names):
        raise ValueError("default_values keys must be a subset of param names")

    def _testcase_to_pytest_param(
        tc: Testcase | AnonymousTestcase,
    ) -> _pytest.mark.structures.ParameterSet:
        if len(tc) == 2:
            testname, testcase_params = typ.cast(Testcase, tc)
            debugging_testname = testname
        elif len(tc) == 1:
            testname = None
            (testcase_params,) = typ.cast(AnonymousTestcase, tc)
            debugging_testname = "-".join(map(str, testcase_params.values()))
        else:
            raise UnreachableError(f"testcase {tc} has unhandled length")

        present_input_param_names = testcase_params.keys() | _default_values.keys()
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
                param_value = _default_values[param_name]
            param_values_in_order.append(param_value)

        if testname is None:
            return pytest.param(*param_values_in_order)
        else:
            return pytest.param(*param_values_in_order, id=testname)

    return pytest.mark.parametrize(
        ",".join(ordered_param_names),
        [_testcase_to_pytest_param(tc) for tc in testcases],
    )
