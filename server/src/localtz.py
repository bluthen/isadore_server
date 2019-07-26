'''
A class capturing the platform's idea of local time.
From: http://docs.python.org/library/datetime.html
'''

import time as _time
from datetime import timedelta
from datetime import tzinfo

ZERO=timedelta(0)
STDOFFSET = timedelta(seconds= -_time.timezone)
if _time.daylight:
	DSTOFFSET = timedelta(seconds= -_time.altzone)
else:
	DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):

	def utcoffset(self, dt):
		if self._isdst(dt):
			return DSTOFFSET
		else:
			return STDOFFSET

	def dst(self, dt):
		if self._isdst(dt):
			return DSTDIFF
		else:
			return ZERO

	def tzname(self, dt):
		return _time.tzname[self._isdst(dt)]

	def _isdst(self, dt):
		tt = (dt.year, dt.month, dt.day,
			dt.hour, dt.minute, dt.second, dt.weekday(), 0, 0)
		stamp = _time.mktime(tt)
		tt = _time.localtime(stamp)
		return tt.tm_isdst > 0


# Local Variables:
# indent-tabs-mode: t
# python-indent: 4
# tab-width: 4
# End:
