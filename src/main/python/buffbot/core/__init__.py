from __future__ import annotations

import enum
import os

import attr

from .utils import shared_open

# Agnarr (PoP-Locked Progression)	1. True Box = One login per computer
# Aradune	1. True Box = One login per computer.
# 2. Timelocked Progression.
# 3. Boxing up to 2 accounts per computer is allowed.
# Coirnav	1. True Box = One login per computer
# 2. Timelocked Progression
# Mangler	1. True Box = One login per computer.
# 2. Timelocked Progression.
# Miragul	1. Started in the House of Thule expansion.
# 2. True Box = One login per computer.
# Phinigel	1. True Box = One login per computer.
# 2. Timelocked Progression
# Ragefire	1. Voting Timelocked Progression
# 2. Boxing multiple accounts from one computer is allowed.
# Rizlona	1. True Box = One login per computer.
# 2. Timelocked Progression.
# Selo (Fast Timelocked Progression)	1. True Box = One login per computer.


class Server(enum.Enum):
    # Live Servers
    AntoniusBayle = "antonius"
    Bertoxxulous = "bertox"
    Bristlebane = "bristle"
    CazicThule = "cazic"
    Drinal = "drinal"
    ErollisiMarr = "erollisi"
    FirionaVie = "firiona"
    Luclin = "luclin"
    Povar = "povar"
    TheRathe = "rathe"
    Tunare = "tunare"
    Vox = "vox"
    Xegony = "xegony"
    Zek = "zek"

    # Test Servers
    Test = "test"
    Beta = "beta"

    # TLP Servers
    Agnarr = "agnarr"
    Aradune = "aradune"
    Coirnav = "coirnav"
    Mangler = "mangler"
    Miragul = "miragul"
    Phinigel = "phinigel"
    Ragefire = "ragefire"
    Rizlona = "rizlona"
    Selo = "selo"

    # Unknown
    Unknown = "unknown"


SERVER_NAMES = {
    # Live Servers
    Server.AntoniusBayle: "Antonius Bayle (Kane Bayle)",
    Server.Bertoxxulous: "Bertoxxulous - Sarym",
    Server.Bristlebane: "Bristlebane - The Tribunal",
    Server.CazicThule: "Cazic-Thule - Fennin Ro",
    Server.Drinal: "Drinal - Maelin Starpyre",
    Server.ErollisiMarr: "Erollisi Marr - The Nameless",
    Server.FirionaVie: "Firiona Vie",
    Server.Luclin: "Luclin - Stromm",
    Server.Povar: "Povar - Quellious",
    Server.TheRathe: "The Rathe - Prexus",
    Server.Tunare: "Tunare - The Seventh Hammer",
    Server.Vox: "Vox",
    Server.Xegony: "Xegony - Druzzil Ro",
    Server.Zek: "Zek",
    # Test Servers
    Server.Test: "Test",
    Server.Beta: "Beta",
    # TLP servers
    Server.Agnarr: "Agnarr",
    Server.Aradune: "Aradune",
    Server.Coirnav: "Coirnav",
    Server.Mangler: "Mangler",
    Server.Phinigel: "Phinigel",
    Server.Ragefire: "Ragefire",
    Server.Rizlona: "Rizlona",
    Server.Selo: "Selo",
}


@attr.s(slots=True, auto_attribs=True, frozen=True)
class Character:

    name: str
    server: Server
    server_display: str

    @classmethod
    def from_filename(cls, filename: os.PathLike) -> Character:
        filename, _ = os.path.splitext(os.path.basename(filename))
        parts = os.fspath(filename).split("_")
        name = parts[1] if len(parts) >= 1 else "Unknown"
        server = Server(parts[2] if len(parts) >= 2 else "unknown")

        return cls(
            name=name, server=server, server_display=SERVER_NAMES.get(server, "Unknown")
        )


@attr.s(slots=True, auto_attribs=True, frozen=True)
class Spell:

    name: str
    gem: int
    success_message: str


class BuffBot:
    def __init__(self, *, filename, spells, acls):
        self.filename = filename
        self.spells = spells
        self.acls = acls

        self.character = Character.from_filename(self.filename)

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
        while line := self._fp.readline():
            # TODO: Actually process the events
            print(line)
