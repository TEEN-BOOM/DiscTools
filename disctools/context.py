"""Job focused Context classes for discord.py"""

# MIT License

# Copyright (c) 2020-present WizzyGeek

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Optional, Sequence, Tuple, Union, TypeVar, cast

import discord
from discord.ext.commands import Context as _Context

T = TypeVar('T', bound=discord.abc.User)

def _maybe_sequence(doubtful: Union[T, Sequence[T]]) -> Sequence[T]:
    if not isinstance(doubtful, Sequence):
        return [doubtful]
    else:
        return doubtful

Targets = Union[discord.abc.User, Sequence[discord.abc.User]]
MemberTargets = Union[discord.Member, Sequence[discord.Member]]

class TargetContext(_Context):
    """A Context class with utilities to determine Member hierarchy.

    Helps in checks for moderation Commands.

    Note
    ====
    The functions of this class can only be used when the message of the context belongs to a guild
    """
    _target: Sequence[discord.abc.User]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target = None
        self.targets = self.message.mentions

    @property
    def targets(self) -> Sequence[discord.abc.User]:
        """Sequence[:class:`discord.abc.User`] : A sequence of Users that were mentioned, this should be set on invoke.
        By default it is set to a list of mentioned users in the message"""
        return self._target

    @targets.setter
    def targets(self, user: Targets) -> None:
        self._target = _maybe_sequence(user)

    @property
    def is_author_target(self) -> bool:
        """:class:`bool`: This property is equivalent to ``ctx.is_user_target(ctx.author)``"""
        return self.author in self.targets

    def is_user_target(self, user: discord.abc.User) -> bool:
        """Check if a user is a target

        Parameters
        ----------
        user : :class:`discord.abc.User`
            The user to verify as target

        Returns
        -------
        :class:`bool`
            True if the user is the target, else False
        """
        return user in self.targets


    def _above_check(self, user: discord.Member,
                     users: Optional[MemberTargets] = None
                     ) -> Tuple[bool, Optional[discord.Member]]:
        if self.guild is None:
            raise ValueError(f"Expected discord.Guild instance at {self.__class__.__qualname__}.guild instead got None")

        targets = cast(Sequence[discord.Member], self.targets) # type: ignore[redundant-cast]

        if user == self.guild.owner:
            return True, None

        if users is None:
            users = targets
        else:
            users = _maybe_sequence(users)

        for member in users:
            try:
                if member == self.guild.owner:
                    return False, member
                if member.top_role > user.top_role:
                    return False, member
                else:
                    pass
            except AttributeError as exc:
                raise TypeError(f"Expected all users to be of type discord.Member instead encountered {type(member)}") from exc
        else:
            return True, None

    def is_author_above(self,
                        users: Optional[MemberTargets] = None
                        ) -> Tuple[bool, Optional[discord.Member]]:
        """Check if author is above all given users

        Parameters
        ----------
        users :  Optional[Union[:class:`discord.Member`, Sequence[:class:`discord.Member`]]]
            The member(s) to check against, if None, then command's targets are used, by default None.

        Raises
        ------
        :exc:`TypeError`
            users argument is not of specified type or the attribute :attr:`_Context.author` is not a :class:`discord.Member` instance.
        :exc:`ValueError`
            guild attribute is None.

        Returns
        -------
        Tuple[:class:`bool`, Optional[:class:`discord.Member`]]
            A tuple of length two. If author is above targets then first element will
            be True and second element will be None. If author is not above target then
            first element will be False and second element will be the first user who is above the author.
            Example output: ``(True, None)``, ``(False, <discord.Member Object>)``.
        """
        if isinstance(self.author, discord.Member):
            return self._above_check(self.author, users)
        raise TypeError(f"Message author is of type {type(self.author)}, expected discord.Member instance.")

    def is_bot_above(self,
                     users: Optional[MemberTargets] = None
                     ) -> Tuple[bool, Optional[discord.Member]]:
        """Check if bot is above all given users, similar to :meth:`TargetContext.is_author_above`

        Parameters
        ----------
        users :  Optional[Union[:class:`discord.Member`, Sequence[:class:`discord.Member`]]]
            The member(s) to check against, if None, then command's targets are used, by default None.

        Raises
        ------
        :exc:`TypeError`
            users argument is not of specified type or the attribute :attr:`_Context.me` is not a :class:`discord.Member` instance.
        :exc:`ValueError`
            guild attribute is None.

        Returns
        -------
        Tuple[:class:`bool`, Optional[:class:`discord.Member`]]
            Same as :meth:`TargetContext.is_author_above`. Only that the comparisn is with Bot.
        """
        if isinstance(self.me, discord.Member):
            return self._above_check(self.me, users)
        raise TypeError(f"{self.__class__.__qualname__}.me is of type {type(self.me)}, expected discord.Member instance.")

    async def whisper(self, users: Optional[Union[Sequence[discord.User], discord.User]] = None,
                      *args, **kwargs) -> None:
        """|coro|
        DM all targets of a command.

        Parameters
        ----------
        users : Optional(Union[:class:`discord.User`, List[:class:`discord.User`]])
            The user(s) to DM. Defaults to self.targets.
        args
            The positional arguments that should be used to message the targets.
        kwargs
            The Key-word arguments that should be used to message the targets.

        Returns
        -------
            NoneType
        """
        if users is None:
            # This could be a Member, but that doesn't matter
            # since Member virtually inherits User
            users = cast(Sequence[discord.User], self.targets) # type: ignore[redundant-cast]
        users = _maybe_sequence(users)
        for target in users:
            target.send(*args, **kwargs)


class EmbedingContext(_Context):
    """Introduces :meth:`send_embed` which helps reduce usage of :class:`discord.Embed`"""
    async def send_embed(self, *args, **kwargs) -> discord.Message:
        """|coro|
        Send an embed.

        This is a shorthand to creating an :class:`discord.Embed` and sending it.
        All arguments are passed to :class:`discord.Embed`.


        Returns
        -------
        :class:`discord.Message`
            The message that was sent.
        """
        return await self.send(embed=discord.Embed(*args, **kwargs))

