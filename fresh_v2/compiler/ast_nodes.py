from dataclasses import dataclass

@dataclass
class Program:
    statements: list

@dataclass
class Number:
    value: int | float

@dataclass
class String:
    value: str

@dataclass
class Boolean:
    value: bool

@dataclass
class Variable:
    name: str

@dataclass
class Binary:
    left: object
    operator: str
    right: object

@dataclass
class Unary:
    operator: str
    operand: object

@dataclass
class Call:
    name: str
    args: list

@dataclass
class Declare:
    name: str
    value: object

@dataclass
class Assign:
    name: str
    value: object

@dataclass
class Print:
    value: object

@dataclass
class If:
    condition: object
    body: list
    otherwise: list

@dataclass
class Repeat:
    count: object
    body: list

@dataclass
class While:
    condition: object
    body: list

@dataclass
class Function:
    name: str
    params: list
    body: list

@dataclass
class Return:
    value: object

@dataclass
class Global:
    name: str
