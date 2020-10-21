import functools
import os
import re
import typing

from datetime import datetime

from boltons.setutils import IndexedSet

from .actions import Action, CastSpell, Target
from .events import Event, Hail
from .types import Character, Spell
from .utils import shared_open, is_current_window


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
        self._current_target: typing.Optional[str] = None
        self._current_started: typing.Optional[datetime] = None
        self._current_action: typing.Optional[typing.Tuple[datetime, Action]] = None
        self._pending_actions: typing.List[Action] = []
        self._pause_until: typing.Optional[datetime] = None

        self._window_logged = False

    def __repr__(self):
        return (
            f"<BuffBot (filename={self.filename!r}, "
            f"spells={self.spells!r}, acls={self.acls!r})>"
        )

    def _check_and_log_window(self):
        if is_current_window("EverQuest"):
            self._window_logged = False
            return True
        else:
            if not self._window_logged:
                self.logger(
                    "Not processing buffs, as EverQuest isn't the active window."
                )
            self._window_logged = True
            return False

    def load(self):
        self._fp = shared_open(self.filename)
        self._fp.seek(0, 2)

    def reload(self):
        self._fp.close()
        self._fp = shared_open(self.filename)

    def close(self):
        self._fp.close()

    def read(self):
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
                    if event := event_type.search(date, line):
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
                            if not result.ok:
                                self._pending_actions = self._current_action[1].failed(
                                    event, self._pending_actions, logger=self.logger
                                )

                            # If we've been given a pause, then we'll set a pause until
                            # based off of that. This is going to use the datetime of
                            # the current event, this will help reduce any additonal
                            # waiting that might come around from lagging from when the
                            # file was written to when it was actually read and
                            # processed.
                            if result.pause is not None:
                                self._pause_until = event.date + result.pause

                            # Regardless of if the action was succesful or not, the
                            # current action is now complete, if the action was able
                            # to be retried, then the action should have readded a
                            # new event to our pending events.
                            self._current_action = None

                    # Finally, we'll handle this event on it's own as well, however
                    # we'll only do this if the current window is an EverQuest windowm
                    # otherwise we're going to just skip this event completely.
                    if self._check_and_log_window():
                        self._handle_event(event)

    def process(self):
        # Check to see if our current action has been waiting for a confirmation for
        # too long, if it has, then we will just assume it completed or failed, but
        # either way we'll just keep going. The most likely case for this is a buff
        # block, which prevents any message from happening.
        if (
            self._current_action is not None
            and (datetime.now() - self._current_action[0]).total_seconds() > 15
        ):
            # If we've reached the timeout, then we'll go ahead and ask the action
            # if we should retry, and if we should then we'll retry, and if we should
            # not, then we'll clear out our current action and move on.
            if self._current_action[1].retry(logger=self.logger):
                self._current_action = datetime.now(), self._current_action[1]
                self._current_action[1].do(logger=self.logger)
            else:
                self._current_action = None

        # If we've been marked to pause, then we're going to stop processing at this
        # point, unlesss we've gone past our pause until point.
        if self._pause_until is not None:
            if datetime.now() >= self._pause_until:
                # We've reached our pause until, so clear it out.
                self._pause_until = None
            else:
                # We have not reached our pause until, so skip the rest of this
                # iteration.
                return

        # Go through and start buffing people as needed.
        if not (self._current_action or self._pending_actions) and self._buff_queue:
            target = self._buff_queue.pop(0)
            self._pending_actions.extend(
                [Target(target=target)]
                + [CastSpell(target=target, spell=s) for s in self.spells]
            )
            self._current_started = datetime.now()

        if self._current_action is None and self._pending_actions:
            # Before starting a new action, we're going to check to make sure that
            # the EverQuest window is the active window, and if not we're going to
            # pause.
            if self._check_and_log_window():
                # Because the EverQuest window could have been in the background
                # for quite some time, it's possible that these pending actions
                # are very stale. In that case, we're going to just clear out
                # our pending actions, and move onto trying to buff other people.
                #
                # In this case, we'll use a 5 minute timeout.
                if (datetime.now() - self._current_started).total_seconds() >= 300:
                    self._current_started = None
                    self._pending_actions.clear()
                    self._buff_queue.clear()
                # Otherwise, our pending actions are fresh enough, and we can go ahead
                # and process the next one.
                else:
                    self._current_action = datetime.now(), self._pending_actions.pop(0)
                    self._current_action[1].do(logger=self.logger)

    @functools.singledispatchmethod
    def _handle_event(self, event):
        # By default, events that are not explicitly handled, do nothing, and
        # we just silently ignore them.
        pass

    @_handle_event.register
    def _(self, event: Hail):
        # If someone is hailing us, then we will add them to our buff queue
        if event.target.lower() == self.character.name.lower():
            # We're going to check to see if the person doing the hailing is
            # the person that our currently pending actions (if there are any)
            # is targeting. If they are, then this person is currently being
            # buffed, and shouldn't be added back to the buff queue to buff
            # again.
            if (
                self._current_action is not None
                and isinstance(self._current_action[1], (Target, CastSpell))
                and self._current_action[1].target.lower() == event.source.lower()
            ):
                return
            elif (
                self._pending_actions
                and isinstance(self._pending_actions[0], (Target, CastSpell))
                and self._pending_actions[0].target.lower() == event.source.lower()
            ):
                return

            # If wer're here, then there's no reason not to go ahead and add
            # this person to our buff queue.
            self._buff_queue.add(event.source)
