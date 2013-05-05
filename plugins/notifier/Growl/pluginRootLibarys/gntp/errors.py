class BaseError(Exception):
	pass


class ParseError(BaseError):
	errorcode = 500
	errordesc = 'Error parsing the message'


class AuthError(BaseError):
	errorcode = 400
	errordesc = 'Error with authorization'


class UnsupportedError(BaseError):
	errorcode = 500
	errordesc = 'Currently unsupported by gntp.py'


class NetworkError(BaseError):
	errorcode = 500
	errordesc = "Error connecting to growl server"
