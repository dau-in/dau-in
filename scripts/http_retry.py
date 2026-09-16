# -*- coding: utf-8 -*-
"""
One retry helper, shared by every card builder.

Why it exists: on 2026-09-16 the Spotify card build died on
`URLError: [Errno 104] Connection reset by peer` -- a single dropped
connection, nothing wrong with the token or the account. Every build step in
update-widgets.yml is continue-on-error, so the run still committed the other
three cards, and the "Report card failures" step then failed the run and sent
the failure mail. That is the alert doing exactly what it was built to do,
but a one-off network blip is not worth an email: cry wolf often enough and
the mail stops meaning anything.

So transient failures get a few quick attempts before they count. What does
NOT get retried is anything the server answered deliberately -- a 401 on a
dead token, a 403 on a revoked key, a 404 -- because those will give the same
answer no matter how many times they're asked, and they are precisely the
failures the alert exists to surface. Rate limiting (429) and the 5xx range
are the exception: the server is saying "not now", not "no".
"""
import time
import urllib.error
import urllib.request

ATTEMPTS = 3
BACKOFF_SECONDS = 1.5

# 429 is "slow down", 5xx is the server having a bad moment. Everything else
# in the 4xx range is a real answer about the request itself.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def urlopen_retry(request, timeout=15, attempts=ATTEMPTS):
    """urlopen, but a dropped connection or a busy server gets another go."""
    last_error = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code not in RETRYABLE_STATUS:
                raise
            last_error = err
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as err:
            last_error = err
        if attempt < attempts - 1:
            # Linear, not exponential: the whole point is to ride out a blip
            # inside a job that runs every 30 minutes anyway, not to wait out
            # a real outage. Three tries top out at 4.5 seconds.
            time.sleep(BACKOFF_SECONDS * (attempt + 1))
    raise last_error
