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

from __future__ import annotations

import enum
import os

import attr


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
