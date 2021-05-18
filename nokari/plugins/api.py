import datetime
import time
import types
import typing
from contextlib import suppress
from io import BytesIO

import hikari
import lightbulb
from lightbulb import Bot, Context, plugins
from lightbulb.errors import ConverterFailure

from nokari import core, utils
from nokari.utils import converters, formatter
from nokari.utils.spotify import (
    NoSpotifyPresenceError,
    SpotifyCardGenerator,
    Track,
)


class API(plugins.Plugin):
    """A plugin that utilizes external APIs"""

    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot = bot
        self.spotify_card_generator = SpotifyCardGenerator(bot)
        self._spotify_argument_parser = utils.ArgumentParser(
            {
                "s": utils.ArgumentOptions(name="style", argmax=1),
                "h": utils.ArgumentOptions(name="hidden", argmax=0),
                "c": utils.ArgumentOptions(name="card", argmax=0),
                "t": utils.ArgumentOptions(name="time", argmax=0),
                "cl": utils.ArgumentOptions(name="colour", aliases=["color"], argmax=1),
                "m": utils.ArgumentOptions(name="member", argmax=0),
            }
        )

    async def send_spotify_card(
        self,
        ctx: Context,
        args: types.SimpleNamespace,
        *,
        data: typing.Union[hikari.Member, Track],
    ) -> None:
        if args.time:
            t0 = time.perf_counter()

        style_map = {
            "dynamic": "1",
            "fixed": "2",
            **{s: s for n in range(1, 3) if (s := str(n))},
        }
        style = style_map.get(args.style, "2")

        async with self.bot.rest.trigger_typing(ctx.channel_id):
            with BytesIO() as fp:
                await self.spotify_card_generator(
                    fp,
                    data,
                    args.hidden
                    or not (args.member or (not args.member and not args.remainder)),
                    args.colour,
                    style,
                )

                kwargs: typing.Dict[str, typing.Any] = {
                    "attachment": hikari.Bytes(fp, f"{data}-card.png")
                }
                if args.time:
                    kwargs[
                        "content"
                    ] = f"That took {(time.perf_counter() - t0) * 1000}ms!"

                # if random.randint(0, 101) < 25:
                #     kwargs["content"] = (
                #         kwargs.get("content") or ""
                #     ) + "\n\nHave you tried the slash version of this command?"

                await ctx.respond(**kwargs)

    @core.commands.group()
    @core.cooldown(1, 2, lightbulb.cooldowns.UserBucket)
    async def spotify(self, ctx: Context) -> None:
        """Contains subcommands that utilizes Spotify API"""
        await ctx.send_help(ctx.command)

    @spotify.command(name="track", aliases=["song"])
    @core.cooldown(1, 2, lightbulb.cooldowns.UserBucket)
    async def spotify_track(
        self, ctx: Context, *, arguments: typing.Optional[str] = None
    ) -> None:
        """
        Shows the information of a Spotify track. If -c/--card flag was present,
        it'll make a Spotify card
        """
        args = await self._spotify_argument_parser.parse(arguments or "")

        if args.member or (not args.member and not args.remainder):
            data: typing.Union[hikari.Member, Track] = ctx.member
            with suppress(ConverterFailure):
                data = await converters.member_converter(
                    converters.WrappedArg(args.remainder, ctx)
                )

                if data.is_bot:
                    return await ctx.respond("I won't make a card for bots >:(")
        else:
            maybe_track = await self.spotify_card_generator.search_and_pick_track(
                ctx, args.remainder
            )

            if not maybe_track:
                return

            data = maybe_track

        try:
            if args.card:
                await self.send_spotify_card(ctx, args, data=data)
                return

            if isinstance(data, hikari.Member):
                sync_id = self.spotify_card_generator.get_sync_id_from_member(data)
                data = await self.spotify_card_generator.get_track(sync_id)

        except NoSpotifyPresenceError as e:
            raise e.__class__(
                f"{'You' if data == ctx.author else 'They'} have no Spotify activity"
            )

        audio_features = await self.bot.loop.run_in_executor(
            self.bot.executor, data.get_audio_features
        )

        album = await self.spotify_card_generator._get_album(data.album_cover_url)
        colors = self.spotify_card_generator._get_colors(
            BytesIO(album), "top-bottom blur", data.album_cover_url
        )
        spotify_code_url = data.get_code_url(hikari.Color.from_rgb(*colors[0]))
        spotify_code = await self.spotify_card_generator._get_spotify_code(
            spotify_code_url
        )

        invoked_with = (
            ctx.content[len(ctx.prefix) + len(ctx.invoked_with) :]
            .strip()
            .split(maxsplit=1)[0]
        )
        embed = (
            hikari.Embed(
                title=f"{invoked_with.capitalize()} Info",
                description=f"**[{data}]({data.url}) by "
                f"{', '.join(f'[{artist}]({artist.url})' for artist in data.artists)} "
                f"on [{data.album}]({data.album.url})**\n",
            )
            .set_thumbnail(album)
            .set_image(spotify_code)
        )

        round_ = lambda n: int(round(n))

        for k, v in {
            "Key": audio_features.get_key(),
            "Tempo": f"{round_(audio_features.tempo)} BPM",
            "Duration": formatter.get_timestamp(
                datetime.timedelta(seconds=audio_features.duration_ms / 1000)
            ),
            "Album Type": data.album.album_type.capitalize(),
            "Popularity": str(data.popularity),
        }.items():
            embed.add_field(name=k, value=v, inline=True)

        for attr in (
            "danceability",
            "energy",
            "speechiness",
            "acousticness",
            "instrumentalness",
            "liveness",
            "valence",
        ):
            embed.add_field(
                name=attr.capitalize(),
                value=str(round_(getattr(audio_features, attr) * 100)),
                inline=True,
            )

        await ctx.respond(embed=embed)

    @spotify.command(name="artist", hidden=True)
    @core.cooldown(1, 2, lightbulb.cooldowns.UserBucket)
    async def spotify_artist(self, ctx: Context) -> None:
        raise NotImplementedError

    @spotify.command(name="album", hidden=True)
    @core.cooldown(1, 2, lightbulb.cooldowns.UserBucket)
    async def spotify_album(self, ctx: Context) -> None:
        raise NotImplementedError


def load(bot: Bot) -> None:
    bot.add_plugin(API(bot))


def unload(bot: Bot) -> None:
    bot.remove_plugin("API")
