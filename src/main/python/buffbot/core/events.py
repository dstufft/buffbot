import datetime
import re
import typing

import attr


@attr.s(frozen=True, auto_attribs=True)
class Event:

    date: datetime.datetime

    def __init_subclass__(cls, *, search_text, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._search_re = re.compile(search_text)

    @classmethod
    def search(cls, date, line):
        if m := cls._search_re.search(line):
            return cls(date=date, **m.groupdict())


@attr.s(frozen=True, auto_attribs=True)
class Hail(Event, search_text=r"^(?P<source>\w+) says?, 'Hail, (?P<target>\w+)'$"):

    source: str
    target: str


@attr.s(frozen=True, auto_attribs=True)
class SpellBlocked(
    Event,
    search_text=r"^Your (?P<spell>.+) spell did not take hold(?: on (?P<target>\w+))?\. \(Blocked by (?P<blocked_by>.+)\.\)$",
):

    spell: str
    blocked_by: str
    target: typing.Optional[str] = attr.ib(default=None)


@attr.s(frozen=True, auto_attribs=True)
class OutOfRange(Event, search_text=r"^Your target is out of range, get closer!$"):
    pass


@attr.s(frozen=True, auto_attribs=True)
class SpellInterrupted(
    Event, search_text=r"^Your (?P<spell>.+) spell is interrupted\.$"
):
    spell: str


@attr.s(frozen=True, auto_attribs=True)
class InsufficientMana(Event, search_text=r"^Insufficient Mana to cast this spell!$"):
    pass


@attr.s(frozen=True, auto_attribs=True)
class NoTarget(Event, search_text=r"^You must first select a target for this spell!$"):
    pass


@attr.s(frozen=True, auto_attribs=True)
class SpellFizzle(Event, search_text=r"^Your (?P<spell>.+) spell fizzles!$"):

    spell: str


@attr.s(frozen=True, auto_attribs=True)
class SpellNotTakeHold(
    Event,
    search_text=r"^Your (?P<spell>.+) spell did not take hold on (?P<target>\w+)\.$",
):
    spell: str
    target: str


@attr.s(frozen=True, auto_attribs=True)
class Line(Event, search_text=r"^(?P<line>.+)$"):

    line: str
