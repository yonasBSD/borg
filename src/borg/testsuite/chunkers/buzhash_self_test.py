# Note: these tests are part of the self test, do not use or import pytest functionality here.
#       See borg.selftest for details. If you add/remove test methods, update SELFTEST_COUNT

from io import BytesIO

from ...chunkers import get_chunker
from ...chunkers.buzhash import buzhash, buzhash_update, Chunker
from ...constants import *  # NOQA
from .. import BaseTestCase
from . import cf


class ChunkerTestCase(BaseTestCase):
    def test_chunkify(self):
        data = b"0" * int(1.5 * (1 << CHUNK_MAX_EXP)) + b"Y"
        parts = cf(Chunker(0, 1, CHUNK_MAX_EXP, 2, 2).chunkify(BytesIO(data)))
        self.assert_equal(len(parts), 2)
        self.assert_equal(b"".join(parts), data)
        self.assert_equal(cf(Chunker(0, 1, CHUNK_MAX_EXP, 2, 2).chunkify(BytesIO(b""))), [])
        self.assert_equal(
            cf(Chunker(0, 1, CHUNK_MAX_EXP, 2, 2).chunkify(BytesIO(b"foobarboobaz" * 3))),
            [b"fooba", b"rboobaz", b"fooba", b"rboobaz", b"fooba", b"rboobaz"],
        )
        self.assert_equal(
            cf(Chunker(1, 1, CHUNK_MAX_EXP, 2, 2).chunkify(BytesIO(b"foobarboobaz" * 3))),
            [b"fo", b"obarb", b"oob", b"azf", b"oobarb", b"oob", b"azf", b"oobarb", b"oobaz"],
        )
        self.assert_equal(
            cf(Chunker(2, 1, CHUNK_MAX_EXP, 2, 2).chunkify(BytesIO(b"foobarboobaz" * 3))),
            [b"foob", b"ar", b"boobazfoob", b"ar", b"boobazfoob", b"ar", b"boobaz"],
        )
        self.assert_equal(
            cf(Chunker(0, 2, CHUNK_MAX_EXP, 2, 3).chunkify(BytesIO(b"foobarboobaz" * 3))), [b"foobarboobaz" * 3]
        )
        self.assert_equal(
            cf(Chunker(1, 2, CHUNK_MAX_EXP, 2, 3).chunkify(BytesIO(b"foobarboobaz" * 3))),
            [b"foobar", b"boobazfo", b"obar", b"boobazfo", b"obar", b"boobaz"],
        )
        self.assert_equal(
            cf(Chunker(2, 2, CHUNK_MAX_EXP, 2, 3).chunkify(BytesIO(b"foobarboobaz" * 3))),
            [b"foob", b"arboobaz", b"foob", b"arboobaz", b"foob", b"arboobaz"],
        )
        self.assert_equal(
            cf(Chunker(0, 3, CHUNK_MAX_EXP, 2, 3).chunkify(BytesIO(b"foobarboobaz" * 3))), [b"foobarboobaz" * 3]
        )
        self.assert_equal(
            cf(Chunker(1, 3, CHUNK_MAX_EXP, 2, 3).chunkify(BytesIO(b"foobarboobaz" * 3))),
            [b"foobarbo", b"obazfoobar", b"boobazfo", b"obarboobaz"],
        )
        self.assert_equal(
            cf(Chunker(2, 3, CHUNK_MAX_EXP, 2, 3).chunkify(BytesIO(b"foobarboobaz" * 3))),
            [b"foobarboobaz", b"foobarboobaz", b"foobarboobaz"],
        )

    def test_buzhash(self):
        self.assert_equal(buzhash(b"abcdefghijklmnop", 0), 3795437769)
        self.assert_equal(buzhash(b"abcdefghijklmnop", 1), 3795400502)
        self.assert_equal(
            buzhash(b"abcdefghijklmnop", 1), buzhash_update(buzhash(b"Xabcdefghijklmno", 1), ord("X"), ord("p"), 16, 1)
        )
        # Test with more than 31 bytes to make sure our barrel_shift macro works correctly
        self.assert_equal(buzhash(b"abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz", 0), 566521248)

    def test_small_reads(self):
        class SmallReadFile:
            input = b"a" * (20 + 1)

            def read(self, nbytes):
                self.input = self.input[:-1]
                return self.input[:1]

        chunker = get_chunker(*CHUNKER_PARAMS, sparse=False)
        reconstructed = b"".join(cf(chunker.chunkify(SmallReadFile())))
        assert reconstructed == b"a" * 20
