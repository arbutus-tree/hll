"""Extract and grade a model's answer. No inspect_ai dependency."""
import re
from typing import NamedTuple

from . import pll
from .moves import DEFAULT_MOVESET, MoveError, parse_moves

SOLUTION_RE = re.compile(r"<solution>(.*?)</solution>", re.DOTALL)


class Grade(NamedTuple):
    solved: bool
    reason: str          # ok | no_solution_tag | empty | invalid_move | not_solved
    n_moves: int         # number of moves parsed (0 if the answer could not be parsed)
    detail: str = ""


def extract_solution(response):
    """Contents of the last <solution>...</solution> tag in a response, or None."""
    found = SOLUTION_RE.findall(response)
    return found[-1] if found else None


def grade(pid, response, moveset=DEFAULT_MOVESET):
    """Binary grade of a raw model response for problem `pid`.

    Solved means every face is a single colour after the moves, in any whole-cube orientation.
    No length cap, no optimality requirement, no partial credit; n_moves is reported for analysis.
    """
    sol = extract_solution(response)
    if sol is None:
        return Grade(False, "no_solution_tag", 0)
    try:
        moves = parse_moves(sol, moveset)
    except MoveError as e:
        reason = "empty" if "empty" in str(e) else "invalid_move"
        return Grade(False, reason, 0, str(e))
    if not pll.check_solved(pid, moves):
        return Grade(False, "not_solved", len(moves))
    return Grade(True, "ok", len(moves))
