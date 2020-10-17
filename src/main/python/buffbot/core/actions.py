import attr

from . import events
from .types import Spell
from .utils import write_command


class Action:
    def __init_subclass__(cls, *, commands, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._commands = commands

    def do(self):
        for command in self._commands:
            write_command(command.format(**attr.asdict(self)))

    def check(self, event):
        raise NotImplementedError

    def failed(self, event, pending_events):
        raise NotImplementedError


@attr.s(frozen=True, auto_attribs=True)
class Target(Action, commands=["/tar {target}", "/say Hail, %t"]):

    target: str

    def check(self, event):
        if isinstance(event, events.Hail):
            if event.source.lower() == "you":
                return event.target.lower() == self.target.lower()

    def failed(self, event, pending_events):
        # If we've failed to target the person we're trying to buff
        # then there's nothing more we can do to that person, so we
        # will just drop all of the pending events.
        return []


@attr.s(frozen=True, auto_attribs=True)
class CastSpell(Action, commands=["/cast {spell[gem]}"]):

    target: str
    spell: Spell

    def check(self, event):
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

    def failed(self, event, pending_events):
        # If the person has run out of range, then we consider that a
        # hard fail, and remove all the pending events.
        #
        # If we don't have a target, then presumably the person has
        # zoned, and this is a hard failure.
        if isinstance(event, (events.OutOfRange, events.NoTarget)):
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
