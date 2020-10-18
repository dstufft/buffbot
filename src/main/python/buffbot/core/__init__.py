import functools
import os
import re
import typing

from datetime import datetime

from boltons.setutils import IndexedSet

from .actions import Action, CastSpell, Target
from .events import Event, Hail
from .types import Character, Spell
from .utils import shared_open


class BuffBot:

    _line_re = re.compile(r"^\[(?P<date>[^\]]+)\]\s+(?P<line>.+)$")

    def __init__(
        self,
        *,
        filename: os.PathLike,
        spells: typing.List[Spell],
        acls: typing.List[str],
        logger=None,
    ):
        self.filename = filename
        self.spells = spells
        self.acls = acls
        self.logger = logger

        self.character = Character.from_filename(self.filename)

        self._buff_queue = IndexedSet()
        self._current_action: typing.Optional[typing.Tuple[datetime, Action]] = None
        self._pending_actions: typing.List[Action] = []

    def __repr__(self):
        return (
            f"<BuffBot (filename={self.filename!r}, "
            f"spells={self.spells!r}, acls={self.acls!r})>"
        )

    def load(self):
        self._fp = shared_open(self.filename)
        self._fp.seek(0, 2)

    def reload(self):
        self._fp.close()
        self._fp = shared_open(self.filename)

    def close(self):
        self._fp.close()

    def process(self):
        # First we go through, and process all of the lines that are currently,
        # in the log file.
        while line := self._fp.readline():
            line = line.strip()
            if m := self._line_re.search(line):
                date = datetime.strptime(m.group("date"), "%a %b %d %H:%M:%S %Y")
                line = m.group("line")

                # Parse the line into an event.
                event = None
                for event_type in Event.__subclasses__():
                    if event := event_type.search(line):
                        break

                if event is not None:
                    # If we have an action we're currently doing, then we will pass thid
                    # event into the action, to let it see if it completes the action or
                    # not.
                    #
                    # This can have three outcomes:
                    # 1. True, the action should be deemed successful, and it's now
                    #          finished.
                    # 2. False, the action was a failure, and we should ask the action
                    #           what to do.
                    # 3. None, the event has no bearing on the success/failure of this
                    #          action.
                    if self._current_action is not None:
                        if (result := self._current_action[1].check(event)) is not None:
                            # Our action was unsucessful, so we'll have the action
                            # itself decide what to do, since some actions might be
                            # recoverable, while some may not be.
                            if not result:
                                self._pending_actions = self._current_action[1].failed(
                                    event, self._pending_actions
                                )

                            # Regardless of if the action was succesful or not, the
                            # current action is now complete, if the action was able
                            # to be retried, then the action should have readded a
                            # new event to our pending events.
                            self._current_action = None

                    # Finally, we'll handle this event on it's own as well
                    self._handle_event(event)

        # We've read all the log lines, we're going to check to see if our current
        # action has been waiting for a confirmation for too long, if it has, then
        # we will just assume it completed or failed, but either way we'll just keep
        # going. The most likely case for this is a buff block, which prevents any
        # message from happening.
        if (
            self._current_action is not None
            and (datetime.now() - self._current_action[0]).total_seconds() > 15
        ):
            self._current_action = None

        # Now that we've exhausted the log file, we'll go through and start
        # buffing people as needed.
        if not (self._current_action or self._pending_actions) and self._buff_queue:
            target = self._buff_queue.pop(0)
            self._pending_actions.extend(
                [Target(target=target)]
                + [CastSpell(target=target, spell=s) for s in self.spells]
            )

        if self._current_action is None and self._pending_actions:
            self._current_action = datetime.now(), self._pending_actions.pop(0)
            # TODO: Bring EQ Window to forefront
            self._current_action[1].do()

        # self.logger(date, line)

    @functools.singledispatchmethod
    def _handle_event(self, event):
        # By default, events that are not explicitly handled, do nothing, and
        # we just silently ignore them.
        pass

    @_handle_event.register
    def _(self, event: Hail):
        # If someone is hailing us, then we will add them to our buff queue
        if event.target.lower() == self.character.name.lower():
            self._buff_queue.add(event.source)
