"""A module that contains custom command class and decorator implementations."""
from __future__ import annotations

import typing

from lightbulb import commands
from lightbulb import context as context_
from lightbulb import errors

__all__: typing.Final[typing.List[str]] = ["Command", "command", "group"]
_CommandCallbackT = typing.TypeVar(
    "_CommandCallbackT", bound=typing.Callable[..., typing.Any]
)


class Command(commands.Command):
    """Custom class command with extra attributes."""

    disabled: bool

    def __init__(
        self,
        *args: typing.Any,
        usage: typing.Optional[str] = None,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.usage = usage
        """The custom command signature if specified."""

    async def is_runnable(self, context: context_.Context) -> bool:
        if getattr(self, "disabled", False):
            raise errors.CheckFailure("Command is disabled.")

        return await super().is_runnable(context)


class Group(Command, commands.Group):
    # pylint: disable=too-many-arguments,arguments-differ
    def command(
        self,
        name: typing.Optional[str] = None,
        cls: typing.Type[commands.Command] = Command,
        allow_extra_arguments: bool = True,
        aliases: typing.Optional[typing.Sequence[str]] = None,
        hidden: bool = False,
        **kwargs: typing.Any,
    ) -> typing.Callable[[_CommandCallbackT], Command]:
        def decorate(func: _CommandCallbackT) -> Command:
            nonlocal name
            name = name or func.__name__
            self._subcommands[name] = cls(
                func,
                name,
                allow_extra_arguments,
                aliases or [],
                hidden,
                parent=self,
                **kwargs,
            )
            if self.inherit_checks:
                self._subcommands[name]._checks.extend(self._checks)
            self.subcommands.add(self._subcommands[name])

            if aliases:
                for alias in aliases:
                    self._subcommands[alias] = self._subcommands[name]
            return self._subcommands[name]

        return decorate

    # pylint: disable=too-many-arguments,arguments-differ
    def group(
        self,
        name: typing.Optional[str] = None,
        allow_extra_arguments: bool = True,
        aliases: typing.Optional[typing.Sequence[str]] = None,
        hidden: bool = False,
        insensitive_commands: bool = False,
        inherit_checks: bool = True,
        **kwargs: typing.Any,
    ) -> typing.Callable[[_CommandCallbackT], Group]:
        def decorate(func: _CommandCallbackT) -> Group:
            nonlocal name
            name = name or func.__name__
            self._subcommands[name] = self.__class__(
                func,
                name,
                allow_extra_arguments,
                aliases or [],
                hidden,
                insensitive_commands=insensitive_commands,
                inherit_checks=inherit_checks,
                parent=self,
                **kwargs,
            )
            if self.inherit_checks:
                self._subcommands[name]._checks.extend(self._checks)
            self.subcommands.add(self._subcommands[name])
            if aliases:
                for alias in aliases:
                    self._subcommands[alias] = self._subcommands[name]
            return self._subcommands[name]

        return decorate


def command(
    name: typing.Optional[str] = None,
    cls: typing.Type[commands.Command] = Command,
    allow_extra_arguments: bool = True,
    aliases: typing.Optional[typing.Sequence[str]] = None,
    hidden: bool = False,
    **kwargs: typing.Any,
) -> typing.Callable[[_CommandCallbackT], commands.Command]:
    """
    A custom decorator that takes arbitrary kwargs and passes it
    when instantiating the Command object.
    """

    def decorate(func: _CommandCallbackT) -> commands.Command:
        return cls(
            func,
            name or func.__name__,
            allow_extra_arguments,
            aliases or [],
            hidden,
            **kwargs,
        )

    return decorate


# pylint: disable=too-many-arguments
def group(
    name: typing.Optional[str] = None,
    cls: typing.Type[commands.Group] = Group,
    allow_extra_arguments: bool = True,
    aliases: typing.Optional[typing.Sequence[str]] = None,
    hidden: bool = False,
    insensitive_commands: bool = False,
    inherit_checks: bool = True,
    **kwargs: typing.Any,
) -> typing.Callable[[_CommandCallbackT], Group]:
    """
    A custom decorator that takes arbitrary kwargs and passes it
    when instantiating the Group object.
    """

    def decorate(func: _CommandCallbackT) -> Group:
        return cls(
            func,
            name or func.__name__,
            allow_extra_arguments,
            aliases or [],
            hidden,
            insensitive_commands=insensitive_commands,
            inherit_checks=inherit_checks,
            **kwargs,
        )

    return decorate
