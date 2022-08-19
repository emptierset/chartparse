class LogChecker(object):
    def __init__(self, caplog):
        self.caplog = caplog

    def assert_contains_string_in_n_lines(self, s, n):
        lines = self.caplog.text.splitlines()
        matches = 0
        for line in lines:
            if s in line:
                matches += 1
        assert matches == n

    def assert_contains_string_in_one_line(self, s):
        self.assert_contains_string_in_n_lines(s, 1)
