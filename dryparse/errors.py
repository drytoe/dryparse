# TODO write error messages for each exception


class DryParseError(Exception):
    pass


class OptionRequiresArgumentError(DryParseError):
    def __init__(self, option: str = None):
        self.option = option
        super().__init__()


class OptionDoesNotTakeArgumentsError(DryParseError):
    def __init__(self, option: str = None):
        self.option = option
        super().__init__()


class OptionArgumentTypeConversionError(DryParseError):
    def __init__(self, argument: str = None, type: type = None):
        self.argument = argument
        self.type = type
        super().__init__()
