"""Bounded local game metadata and lossless edits of Valve's text KeyValues."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import tempfile

MAX_METADATA = 8 * 1024 * 1024
_TOKENS = re.compile(r'\s+|//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[{}]|[^\s{}"]+')


def read_text(path, maximum=MAX_METADATA):
    with Path(path).open('rb') as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError('Game metadata exceeds its size limit')
    return raw.decode('utf-8-sig')


def read_json(path):
    return json.loads(read_text(path))


def atomic_write(path, data, expected=None):
    """Replace only an unchanged destination; private metadata stays user-owned."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if expected is not None and path.read_bytes() != expected:
        raise ValueError('The launcher configuration changed; read it again')
    fd, temporary = tempfile.mkstemp(prefix='.vitalux-', dir=path.parent)
    try:
        if path.exists():
            os.fchmod(fd, path.stat().st_mode & 0o777)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if expected is not None and path.read_bytes() != expected:
            raise ValueError('The launcher configuration changed; read it again')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_json(path, value):
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def _unquote(value):
    if value.startswith('"'):
        value = value[1:-1]
        value = re.sub(r'\\([\\"nt])', lambda m: {'n': '\n', 't': '\t'}.get(m[1], m[1]), value)
    return value


def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t') + '"'


@dataclass
class Node:
    key: str
    value: object
    start: int
    end: int


def parse(text):
    if len(text.encode()) > MAX_METADATA:
        raise ValueError('Valve metadata exceeds its size limit')
    tokens = [m for m in _TOKENS.finditer(text)
              if not m[0].isspace() and not m[0].startswith(('//', '/*'))]
    if len(tokens) > 400000:
        raise ValueError('Too many Valve metadata entries')
    position = 0

    def object_nodes(depth=0, closing=False):
        nonlocal position
        if depth > 48:
            raise ValueError('Valve metadata nesting is too deep')
        nodes = []
        while position < len(tokens):
            token = tokens[position]
            if token[0] == '}':
                if not closing:
                    raise ValueError('Unexpected closing brace')
                position += 1
                return nodes, token.start(), token.end()
            if token[0] == '{':
                raise ValueError('Missing Valve metadata key')
            key = _unquote(token[0])
            position += 1
            if position >= len(tokens):
                raise ValueError('Missing Valve metadata value')
            value_token = tokens[position]
            position += 1
            if value_token[0] == '{':
                value, close_start, close_end = object_nodes(depth+1, True)
                nodes.append(Node(key, value, value_token.start(), close_end))
            elif value_token[0] == '}':
                raise ValueError('Missing Valve metadata value')
            else:
                nodes.append(Node(key, _unquote(value_token[0]), value_token.start(), value_token.end()))
        if closing:
            raise ValueError('Unclosed Valve metadata object')
        return nodes, len(text), len(text)

    return object_nodes()[0]


def loads(text):
    def mapping(nodes):
        return {node.key: mapping(node.value) if isinstance(node.value, list) else node.value for node in nodes}
    return mapping(parse(text))


def get(mapping, key, default=None):
    return next((value for name, value in mapping.items() if name.casefold() == key.casefold()), default)


def set_string(text, path, value):
    """Keep other keys, comments, order and whitespace byte-for-byte intact."""
    path = tuple(path)
    if not path:
        raise ValueError('An edit requires a Valve key path')
    nodes = parse(text)
    owner = None
    for depth, name in enumerate(path):
        matches = [node for node in nodes if node.key.casefold() == str(name).casefold()]
        if len(matches) > 1:
            raise ValueError('Ambiguous duplicate Valve key')
        if not matches:
            def entry(index, indent):
                if index == len(path)-1:
                    return indent + quote(path[index]) + '\t\t' + quote(value) + '\n'
                return indent + quote(path[index]) + '\n' + indent + '{\n' + entry(index+1, indent+'\t') + indent + '}\n'
            insertion = owner.end-1 if owner else len(text)
            newline = '\r\n' if '\r\n' in text else '\n'
            extra = '\n' + entry(depth, '\t'*depth)
            extra = extra.replace('\n', newline)
            return text[:insertion] + extra + text[insertion:]
        node = matches[0]
        if depth == len(path)-1:
            if isinstance(node.value, list):
                raise ValueError('Expected a string launch option')
            return text[:node.start] + quote(value) + text[node.end:]
        if not isinstance(node.value, list):
            raise ValueError('Expected a Valve metadata object')
        owner, nodes = node, node.value
    raise ValueError('Invalid Valve key path')
