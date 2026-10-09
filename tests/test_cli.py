from pathlib import Path

import pytest

import cli


@pytest.mark.parametrize(
    "raw, expected",
    [
        (r"\\wsl.localhost\Ubuntu\home\akash\bill_photos\cr9_bill.jpg", "/home/akash/bill_photos/cr9_bill.jpg"),
        (r"\\wsl$\Ubuntu-22.04\home\akash\bill.jpg", "/home/akash/bill.jpg"),
        (r"C:\Users\akash\Downloads\bill.jpg", "/mnt/c/Users/akash/Downloads/bill.jpg"),
        (r'"D:\Bills\may bill.png"', "/mnt/d/Bills/may bill.png"),
        ("bill_photos/cr9_bill.jpg", "bill_photos/cr9_bill.jpg"),
        ("  /home/akash/bill.jpg  ", "/home/akash/bill.jpg"),
    ],
)
def test_to_wsl_path(raw, expected):
    assert cli.to_wsl_path(raw) == expected


def test_image_path_is_absolute():
    assert cli.image_path("bill_photos/x.jpg") == Path("bill_photos/x.jpg").resolve()


def test_print_answer_shows_time(capsys):
    cli.print_answer("All good.", 12.4)
    assert "All good." in capsys.readouterr().out.splitlines()[1]
    cli.print_answer("x", 12.4)
    assert "(answered in 12 s)" in capsys.readouterr().out
