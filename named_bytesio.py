from io import BytesIO


class NamedBytesIO(BytesIO):
    def __init__(self, name: str, initial_bytes=None):
        super().__init__(initial_bytes)
        self.name = name
