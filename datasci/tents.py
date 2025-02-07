from typing import List, Set, Optional
from pathlib import Path
from itertools import starmap, repeat
import gzip


class UnsetFieldsException(Exception):
    pass


class UnsupportedFieldsException(Exception):
    pass


class Tent:
    _UNSET = "NA"

    def __init__(self, h: list, r_h: list, immutable: bool, unset=None):
        self._header = h
        self._header_set = set(h)
        self._required_header = r_h
        self._required_header_set = set(r_h)
        self._set_header = set()
        self._immutable = immutable
        if unset is not None:
            self._UNSET = unset
        for key in self._header:
            setattr(self, key, self._UNSET)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setattr__(self, key, value):
        if not key.startswith("_"):
            self._check_fields_are_supported({key})
            if key in self._set_header and self._immutable:
                raise ValueError(f"{key} is already set")
            self._set_header.add(key)
        super().__setattr__(key, value)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __eq__(self, other: "Tent"):
        return all(map(lambda key: self[key] == other[key], self._header))

    def __repr__(self):
        missing_fields = self._required_header_set.difference(self._set_header)
        if len(missing_fields) > 0:
            raise UnsetFieldsException(
                f"Missing unset fields: {missing_fields}. Entry can only be serialised with all of the following fields set: {self._required_header}"
            )
        values = starmap(getattr, zip(repeat(self), self._header))
        return "\t".join(map(str, values))

    def _check_fields_are_supported(self, field_names):
        if not self._header_set.issuperset(field_names):
            raise UnsupportedFieldsException(f"Supported fields: {self._header}")

    def update(self, **fields):
        self._check_fields_are_supported(fields.keys())
        for key, val in fields.items():
            self[key] = val

    def copy_values(self, other: "Tent"):
        for key in other._header:
            setattr(self, key, getattr(other, key))


def _get_fstream(fname: str):
    if fname.endswith(".gz"):
        fstream = gzip.open(fname, "rt")
    else:
        fstream = open(fname, "r")
    return fstream


def _read_header(fstream):
    while True:
        header = next(fstream).strip()
        if not header.startswith("#"):
            header = header.split("\t")
            break
    return header


class Tents:
    """
    [TODO] Description
    [TODO] Usage
    """

    @classmethod
    def from_tsv(self, fname: str, header: List[str] = None) -> "Tents":
        fin = _get_fstream(fname)
        if header is None:
            header = _read_header(fin)
        result = Tents(header=header)
        for line in fin:
            elements = line.strip().split("\t")
            new_tent = result.new()
            new_tent.update(**dict(zip(header, elements)))
            result.add(new_tent)
        fin.close()
        return result

    @classmethod
    def from_tsv_streamed(
        self, fname: str, chunksize: int, header: List[str] = None
    ) -> "Tents":
        """
        `chunksize`: number of lines to read, batch by batch

        Returns an iterator through the batches.
        """
        fin = _get_fstream(fname)
        if header is None:
            header = read_header(fin)
        result = Tents(header=header)
        for i, line in enumerate(fin):
            if i != 0 and i % chunksize == 0:
                yield result
                result = Tents(header=header)
            elements = line.strip().split("\t")
            new_tent = result.new()
            new_tent.update(**dict(zip(header, elements)))
            result.add(new_tent)
        fin.close()
        if len(result) > 0:
            yield result

    def __init__(
        self,
        header: list,
        required_header: list = [],
        immutable: bool = False,
        unset_value=None,
    ):
        self._header = header
        self._required_header = required_header
        self._entries = list()
        self._immutable = immutable
        self._unset = unset_value

    def _entries_to_tsv(self) -> str:
        return "\n".join(map(repr, self._entries))

    def __repr__(self):
        return self.get_header() + self._entries_to_tsv()

    def __iter__(self):
        return iter(self._entries)

    def __len__(self):
        return len(self._entries)

    def __getitem__(self, idx):
        return self._entries[idx]

    def to_tsv(self, with_header: bool = True):
        result = ""
        if with_header:
            result += self.get_header()
        return result + self._entries_to_tsv()

    def add(self, entry: Tent):
        repr(entry)
        assert entry._header == self._header
        self._entries.append(entry)

    def new(self) -> Tent:
        return Tent(self._header, self._required_header, self._immutable, self._unset)

    def get_header(self):
        return "\t".join(self._header) + "\n"

    def drop_elements(self, element_indices: Set[int]) -> None:
        """
        Drops the Tent entries whose indices are listed in `element_indices`
        """
        filtered_entries = list()
        for entry_idx in range(len(self)):
            if entry_idx not in element_indices:
                filtered_entries.append(self[entry_idx])
        self._entries = filtered_entries

    def extend(self, other: "Tents"):
        for element in other:
            self.add(element)
