# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import typing

import attr

from . import events
from .types import Spell
from .utils import write_command


@attr.s(slots=True, frozen=True, auto_attribs=True)
class Result:

    ok: bool
    pause: typing.Optional[datetime.timedelta] = attr.ib(default=None)


class Action:
    def __init_subclass__(cls, *, commands, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._commands = commands

    def do(self, *, logger):
        self.log(logger)

        for command in self._commands:
            write_command(command.format(**attr.asdict(self)))

    def check(self, event) -> typing.Optional[Result]:
        raise NotImplementedError

    def failed(self, event, pending_events, *, logger):
        raise NotImplementedError

    def retry(self, *, logger):
        pass

    def log(self, logger):
        pass


class Retryable:
    def __init_subclass__(cls, retries=3, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._retries = retries

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._has_started = False

    def started(self):
        self._has_started = True

    def retry(self, *, logger):
        if not self._has_started and self._retries:
            self._retries -= 1
            return True


@attr.s(frozen=True, auto_attribs=True)
class Target(Action, commands=["/tar {target}", "/say Hail, %t"]):

    target: str

    def check(self, event) -> typing.Optional[Result]:
        if isinstance(event, events.Hail):
            if event.source.lower() == "you":
                return Result(ok=event.target.lower() == self.target.lower())

        return None

    def failed(self, event, pending_events, *, logger):
        # If we've failed to target the person we're trying to buff
        # then there's nothing more we can do to that person, so we
        # will just drop all of the pending events.
        logger(f"Could not target {self.target}")
        return []


@attr.s(auto_attribs=True)
class CastSpell(Action, Retryable, commands=["/cast {spell[gem]}"]):

    target: str
    spell: Spell

    def log(self, logger):
        logger(f"Buffing {self.target} with {self.spell.name}.")

    def check(self, event) -> typing.Optional[Result]:
        if self._check_started(event):
            self.started()

        if ok := self._check(event):
            return Result(ok=ok, pause=datetime.timedelta(seconds=2))
        return None

    def _check_started(self, event):
        if isinstance(event, events.SpellCast):
            if event.source.lower() == "you" and event.spell == self.spell.name:
                return True

    def _check(self, event):
        # If we get a blocked spell message, and that spell is the spell
        # we're trying to cast, on the person we're trying to cast it on
        # then we'll consider the cast successful.
        if isinstance(event, events.SpellBlocked):
            if (
                event.spell == self.spell.name
                and event.target is not None
                and event.target.lower() == self.target.lower()
            ):
                return True
        # If we got a message that our spell would not take hold, that
        # probably means that the person is max buffs, and thus our
        # spell failed to cast.
        if isinstance(event, events.SpellNotTakeHold):
            if (
                event.spell == self.spell.name
                and event.target.lower() == self.target.lower()
            ):
                return False
        # If we get a generic line event, then we'll check to see if it
        # matches our success message for this spell, if it does then
        # we've good, otherwise this event doesn't mean anything for us.
        elif isinstance(event, events.Line):
            if self.spell.success_message.format(target=self.target) == event.line:
                return True
        # These failures don't require any additional logic, if we get
        # these events, then we know it's a failure.
        elif isinstance(
            event,
            (
                events.OutOfRange,
                events.SpellInterrupted,
                events.SpellFizzle,
                events.InsufficientMana,
                events.NoTarget,
            ),
        ):
            return False

    def failed(self, event, pending_events, *, logger):
        # If the person has run out of range, then we consider that a
        # hard fail, and remove all the pending events.
        #
        # If we don't have a target, then presumably the person has
        # zoned, and this is a hard failure.
        #
        # If the spell didn't take hold, we're going to assume that
        # their buff slots are totally full, and it's pointless to
        # try to do anything else to them.
        if isinstance(
            event, (events.OutOfRange, events.NoTarget, events.SpellNotTakeHold)
        ):
            logger(
                f"Could not buff {self.target} with {self.spell.name} "
                f"({event.__class__.__name__}"
            )
            return []
        # If our spell was interrupted for some reason, then we'll go
        # ahead and recast it.
        #
        # Insufficient mana is a recoverable failure, so we'll recast
        # and see if it works this time.
        elif isinstance(
            event,
            (events.SpellInterrupted, events.SpellFizzle, events.InsufficientMana),
        ):
            return [self] + pending_events
        # If we get here, then something is wrong, so we'll just hard
        # error.
        else:
            raise NotImplementedError("failed called for unhandled event")
