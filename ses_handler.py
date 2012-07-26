#    Copyright 2012 Dexetra <contact@dexetra.com>

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from decimal import Decimal
from logging import Handler, NOTSET

import boto
from boto.ses.exceptions import SESMaxSendingRateExceededError


class SESHandler(Handler):
    """A logging.Handler subclass which emits logs via the Amazon SES.

    Requires the boto library.
    https://github.com/boto/boto

    Make sure that the `sender` email address has been verified.
    And if you haven't acquired production access yet,
    verify the email addresses for the `recipients` too.
    Also be aware of the maximum send quota you can send from your
    AWS account.

    Refer here for more information:
    http://boto.cloudhackers.com/en/latest/ses_tut.html
    http://aws.amazon.com/ses/
    """

    def __init__(self, sender='', recipients=[], subject='', level=NOTSET):
        super(SESHandler, self).__init__(level)
        self._ses_connection = boto.connect_ses()
        self._sender = sender
        self._recipients = recipients
        self._subject = subject
        self.limit_exceeded = False

    def close(self):
        self._ses_connection.close()
        super(SESHandler, self).close()

    def emit(self, record):
        if not self.limit_exceeded:
            try:
                message = self.format(record)
                self._ses_connection.send_email(
                        source=self._sender, subject=self._subject,
                        body=message, to_addresses=self._recipients)
            except SESMaxSendingRateExceededError:
                self.limit_exceeded = True
            except Exception:
                self.handleError(record)

    @property
    def limit_exceeded(self):
        if self._limit_exceeded:
            result = self._ses_connection.get_send_quota()[
                    'GetSendQuotaResponse']['GetSendQuotaResult']
            self._limit_exceeded = (Decimal(result['Max24HourSend']) <=
                                    Decimal(result['SentLast24Hours']))
        return self._limit_exceeded

    @limit_exceeded.setter
    def limit_exceeded(self, value):
        self._limit_exceeded = value
