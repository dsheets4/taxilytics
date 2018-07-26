"""
This file was used to request a django URL with CSRF protection and then POST to the
form using the token extracted from the GET.
"""

import urllib.parse
import urllib.request
import http.cookiejar


url = 'http://localhost:8000/polls/2/vote/'

values = {'choice' : 16}
data = urllib.parse.urlencode(values)
data = data.encode('utf-8')


def csrf_example():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    with opener.open(url) as get_request:
        get_page = get_request.read()
        print(get_page)

        for cookie in cj:
            if cookie.name == 'csrftoken':
                csrftoken = cookie.value
                break

        values = {'choice' : 16}
        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8')
        opener.addheaders = [('X-CSRFToken', csrftoken)]

        with opener.open(url, data) as post_request:
            post_page = post_request.read()
            print(post_page)


def no_csrf_example():
    opener = urllib.request.build_opener()
    with opener.open(url, data) as post_request:
        post_page = post_request.read()
        print(post_page)


csrf_example()
