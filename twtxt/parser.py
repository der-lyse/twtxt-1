"""
    twtxt.parser
    ~~~~~~~~~~~~

    This module implements the parser for twtxt files.

    :copyright: (c) 2016-2017 by buckket.
    :license: MIT, see LICENSE for more details.
"""

import logging
from datetime import datetime, timezone

import click
import dateutil.parser

from twtxt.models import Tweet

logger = logging.getLogger(__name__)


def make_aware(dt):
    """Appends tzinfo and assumes UTC, if datetime object has no tzinfo already."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_iso8601(string):
    """Parse string using dateutil.parser."""
    return make_aware(dateutil.parser.parse(string))


def parse_tweets(raw_tweets, source, now=None):
    """
        Parses a list of raw tweet lines from a twtxt file
        and returns a list of :class:`Tweet` objects.

        :param list raw_tweets: list of raw tweet lines
        :param Source source: the source of the given tweets
        :param Datetime now: the current datetime

        :returns: a list of parsed tweets :class:`Tweet` objects
        :rtype: list
    """
    if now is None:
        now = datetime.now(timezone.utc)

    errors = 0
    tweets = []
    for line in raw_tweets:
        try:
            tweet = parse_tweet(line, source, now)
        except (ValueError, OverflowError) as e:
            logger.error("{0} - {1}".format(source.url, e))
            errors += 1
        else:
            if tweet is not None:
                tweets.append(tweet)

    if errors > 0:
        logger.error("{0} - {1} tweets, {2} errors".format(source.url, len(tweets), errors))
    return tweets


def parse_tweet(raw_tweet, source, now=None):
    """
        Parses a single raw tweet line from a twtxt file
        and returns a :class:`Tweet` object.

        :param str raw_tweet: a single raw tweet line
        :param Source source: the source of the given tweet
        :param Datetime now: the current datetime

        :returns: the parsed tweet
        :rtype: Tweet
    """
    if not raw_tweet or raw_tweet.startswith("#"):
        return None

    if now is None:
        now = datetime.now(timezone.utc)

    raw_created_at, text = raw_tweet.split("\t", 1)
    created_at = parse_iso8601(raw_created_at)

    if created_at > now:
        import humanize
        from_now = "%s from now" % humanize.naturaldelta(now - created_at)
        logger.error("Tweet by %s@%s is from the future: %r %s" % (source.nick, source.url, raw_created_at, from_now))

    return Tweet(click.unstyle(text.strip()), created_at, source)
