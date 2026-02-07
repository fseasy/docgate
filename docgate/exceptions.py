class LogicError(Exception): ...


class ApiBaseException(Exception): ...


class NotExistInDBException(ApiBaseException):
  """data not exists in db"""


class InvalidUserInputException(ApiBaseException):
  """User input is invalid"""
