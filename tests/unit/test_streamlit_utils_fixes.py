import pytest

from src.streamlit_utils import apply_fixes_to_code
from src.models.code_fix_models import CodeFix, CodeFixResult, FixConfidence, FixStatus


def test_apply_fixes_no_fixes_returns_original():
    code = "def foo():\n    return 1\n"
    result = CodeFixResult()

    out = apply_fixes_to_code(code, result, min_confidence="high")
    assert out == code


def test_apply_fixes_line_number_replacement_updates_code_and_status():
    code = "def foo():\n    return 1\n# end\n"
    fix = CodeFix(
        issue_description="Return should be 2",
        original_code="    return 1",
        fixed_code="    return 2",
        line_start=2,
        line_end=2,
        confidence=FixConfidence.HIGH,
    )

    result = CodeFixResult()
    result.add_fix(fix)

    out = apply_fixes_to_code(code, result, min_confidence="high")

    assert "return 2" in out
    # status should be marked applied
    assert result.fixes[0].status == FixStatus.APPLIED
    # stats updated
    assert result.applied_count == 1


def test_apply_fixes_string_fallback_when_line_out_of_range():
    code = "a = 1\nb = 2\nprint(a+b)\n"
    fix = CodeFix(
        issue_description="Use sum",
        original_code="print(a+b)",
        fixed_code="print(sum([a, b]))",
        line_start=999,
        line_end=999,
        confidence=FixConfidence.HIGH,
    )

    result = CodeFixResult()
    result.add_fix(fix)

    out = apply_fixes_to_code(code, result, min_confidence="high")

    assert "sum([a, b])" in out
    assert result.fixes[0].status == FixStatus.APPLIED


def test_apply_fixes_respects_confidence_threshold():
    code = "def foo():\n    return 1\nprint(foo())\n"

    high_fix = CodeFix(
        issue_description="Return should be 2",
        original_code="    return 1",
        fixed_code="    return 2",
        line_start=2,
        line_end=2,
        confidence=FixConfidence.HIGH,
    )

    medium_fix = CodeFix(
        issue_description="Change print",
        original_code="print(foo())",
        fixed_code="print(foo(), 'done')",
        line_start=3,
        line_end=3,
        confidence=FixConfidence.MEDIUM,
    )

    result = CodeFixResult()
    result.add_fix(high_fix)
    result.add_fix(medium_fix)

    out = apply_fixes_to_code(code, result, min_confidence="high")

    assert "return 2" in out
    # medium confidence fix should not be applied
    assert "done" not in out
    # only one applied
    assert result.applied_count == 1


def test_apply_fixes_all_threshold_applies_everything():
    code = "x=1\ny=2\nprint(x+y)\n"

    low_fix = CodeFix(
        issue_description="space",
        original_code="x=1",
        fixed_code="x = 1",
        line_start=1,
        line_end=1,
        confidence=FixConfidence.LOW,
    )

    med_fix = CodeFix(
        issue_description="space",
        original_code="y=2",
        fixed_code="y = 2",
        line_start=2,
        line_end=2,
        confidence=FixConfidence.MEDIUM,
    )

    res = CodeFixResult()
    res.add_fix(low_fix)
    res.add_fix(med_fix)

    out = apply_fixes_to_code(code, res, min_confidence="all")

    assert "x = 1" in out
    assert "y = 2" in out
    assert res.applied_count == 2


def test_apply_fixes_unknown_threshold_defaults_to_high():
    code = "a=1\nb=2\nprint(a+b)\n"
    # medium confidence fix should be filtered out when unknown threshold defaults to HIGH
    med_fix = CodeFix(
        issue_description="space",
        original_code="a=1",
        fixed_code="a = 1",
        line_start=1,
        line_end=1,
        confidence=FixConfidence.MEDIUM,
    )

    res = CodeFixResult()
    res.add_fix(med_fix)

    out = apply_fixes_to_code(code, res, min_confidence="not-a-real-level")

    # medium fix should not be applied because threshold defaulted to HIGH
    assert "a = 1" not in out


def test_apply_fixes_handles_bad_line_numbers_and_defaults():
    code = "one\ntwo\nthree\n"
    class BadLineFix:
        def __init__(self):
            self.issue_description = "change one"
            self.original_code = "one"
            self.fixed_code = "ONE"
            self.line_start = "bad"
            self.line_end = "bad"
            self.confidence = FixConfidence.HIGH

    res = CodeFixResult()
    # append a fake fix that will cause int() to raise when parsing line numbers
    res.fixes.append(BadLineFix())

    out = apply_fixes_to_code(code, res, min_confidence="high")

    # bad line numbers cause fallback to line 1 (defaults) and apply
    assert out.splitlines()[0] == "ONE"


def test_apply_fixes_ignores_status_setter_exceptions_line_based():
    code = "a\nb\n"

    class BadStatusFix:
        def __init__(self):
            self.issue_description = "bad"
            self.original_code = "a"
            self.fixed_code = "A"
            self.line_start = 1
            self.line_end = 1
            self.confidence = FixConfidence.HIGH

        @property
        def status(self):
            return "s"

        @status.setter
        def status(self, _):
            raise RuntimeError("cannot set status")

    res = CodeFixResult()
    res.fixes.append(BadStatusFix())

    out = apply_fixes_to_code(code, res, min_confidence="high")
    assert out.splitlines()[0] == "A"


def test_apply_fixes_ignores_status_setter_exceptions_fallback():
    code = "x=1\nprint(x)\n"

    class BadStatusFix2:
        def __init__(self):
            self.issue_description = "bad"
            self.original_code = "print(x)"
            self.fixed_code = "print(x, 'ok')"
            self.line_start = 999
            self.line_end = 999
            self.confidence = FixConfidence.HIGH

        @property
        def status(self):
            return "s"

        @status.setter
        def status(self, _):
            raise RuntimeError("cannot set status")

    res = CodeFixResult()
    res.fixes.append(BadStatusFix2())

    out = apply_fixes_to_code(code, res, min_confidence="high")
    assert "ok" in out


def test_apply_fixes_handles_update_statistics_exception():
    code = "def f():\n    return 1\n"
    fix = CodeFix(
        issue_description="ret",
        original_code="    return 1",
        fixed_code="    return 2",
        line_start=2,
        line_end=2,
        confidence=FixConfidence.HIGH,
    )
    res = CodeFixResult()
    res.add_fix(fix)

    # Replace update_statistics with one that raises
    def bad_update():
        raise RuntimeError("boom")

    # Bypass pydantic attribute checks by setting directly on the instance
    object.__setattr__(res, 'update_statistics', bad_update)

    out = apply_fixes_to_code(code, res, min_confidence="high")
    assert "return 2" in out
