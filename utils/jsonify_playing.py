from functools import reduce

from pyatv import interface


def jsonify_playing(playing: interface.Playing):
    def reducer(memo, prop):
        val = getattr(playing, prop) or ""
        memo[prop] = str(val)
        return memo

    return reduce(reducer, playing._PROPERTIES, {})
