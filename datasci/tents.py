from typing import Optional
from itertools import starmap, repeat


class UnsetFieldsException(Exception):
    pass


class UnsupportedFieldsException(Exception):
    pass


class Tent:
    _UNSET = "NA"

    def __init__(self, h: list, r_h: list, immutable: bool, unset = None):
        self._headers = h
        self._headers_set = set(h)
        self._required_headers = r_h
        self._immutable = immutable
        if unset is not None:
            self._UNSET = unset
        for key in self._headers:
            setattr(self, key, self._UNSET)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setattr__(self, key, value):
        if not key.startswith("_"):
            self._check_fields_are_supported({key})
            existing_val = getattr(self, key, None) 
            if existing_val is not None and existing_val != self._UNSET and self._immutable:
                raise ValueError(f"{key} is already set")
        super().__setattr__(key, value)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        missing_fields = self._get_missing_fields()
        if len(missing_fields) > 0:
            raise UnsetFieldsException(
                f"Missing unset fields: {missing_fields}. Entry can only be serialised with all of the following fields set: {self._required_headers}"
            )
        values = starmap(getattr, zip(repeat(self), self._headers))
        return "\t".join(map(str, values))

    def _check_fields_are_supported(self, field_names):
        if not self._headers_set.issuperset(field_names):
            raise UnsupportedFieldsException(
                f"Supported fields: {self._headers}"
            )

    def _get_missing_fields(self):
        result = set()
        for required_field in self._required_headers:
            if getattr(self, required_field) == self._UNSET:
                result.add(required_field)
        return result

    def update(self, **fields):
        self._check_fields_are_supported(fields.keys())
        for key, val in fields.items():
            self[key] = val


class Tents:
    """
    [TODO] Description
    [TODO] Usage
    """

    def __init__(self, headers: list, required_headers: list = [], immutable: bool = False, unset_value = None):
        self._headers = headers
        self._required_headers = required_headers
        self._entries = list()
        self._immutable = immutable
        self._unset = unset_value

    def __repr__(self, with_header: bool = True):
        return self.get_header() + "\n".join(map(lambda l: "\t".join(map(str,l)), self._entries))

    def add(self, entry: Tent):
        repr(entry)
        assert entry._headers == self._headers
        self._entries.append(entry[key] for key in self._headers)

    def new(self) -> Tent:
        return Tent(self._headers, self._required_headers, self._immutable, self._unset)

    def get_header(self):
        return "\t".join(self._headers) + "\n"
