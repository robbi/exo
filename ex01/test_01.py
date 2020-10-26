import pytest
from solution import calc

test_cases = [
    ("12",),
    ("-123",),
    ("1,23",),
    ("-12,34",),
    ("1+2",),
    ("-1,2+3",),
    ("12,+3,4",),
    ("1-2",),
    ("-1,2-3",),
    ("12,-3,4",),
    ("13*24",),
    ("-1,2*34",),
    ("12,*-3,4",),
    ("13/24",),
    ("-1,2/-34",),
    ("12,/3,4",),
    ("1+2*-3-4/5",),
    ("1+2*(-3+4)/5",),
    ("((1+2)*(-3+4)-5)/6",),
]

def eval_testcase(tc):
    if len(tc) == 1:
        result = eval(tc[0].replace(',', '.'))
    else:
        result = tc[1]
    return (tc[0], result)

test_cases = [eval_testcase(tc) for tc in test_cases]

@pytest.mark.parametrize("test_input, expected_output", test_cases)
def test_calc(test_input, expected_output):
    assert(calc(test_input) == expected_output)
