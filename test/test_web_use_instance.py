
from test.fixtures import make_test_env, make_fake_space

from wsgi_intercept import httplib2_intercept
import wsgi_intercept
import httplib2
import simplejson

from tiddlyweb.store import Store
from tiddlyweb.model.tiddler import Tiddler


def setup_module(module):
    make_test_env()
    from tiddlyweb.config import config
    from tiddlyweb.web import serve
    # we have to have a function that returns the callable,
    # Selector just _is_ the callable
    def app_fn():
        return serve.load_app()
    #wsgi_intercept.debuglevel = 1
    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('0.0.0.0', 8080, app_fn)
    wsgi_intercept.add_wsgi_intercept('thing.0.0.0.0', 8080, app_fn)
    wsgi_intercept.add_wsgi_intercept('other.0.0.0.0', 8080, app_fn)

    module.store = Store(config['server_store'][0],
            config['server_store'][1], {'tiddlyweb.config': config})

def teardown_module(module):
    import os
    os.chdir('..')


def test_home_page_exist():
    http = httplib2.Http()
    response, content = http.request('http://0.0.0.0:8080/', method='GET')

    assert response['status'] == '200'
    assert 'discoursive' in content


def test_space_not_exist():
    http = httplib2.Http()
    response, content = http.request('http://thing.0.0.0.0:8080/', method='GET')

    assert response['status'] == '404'


def test_space_does_exist():
    make_fake_space(store, 'thing')
    http = httplib2.Http()
    response, content = http.request('http://thing.0.0.0.0:8080/', method='GET')

    assert response['status'] == '200'


def test_space_has_limited_view():
    make_fake_space(store, 'other')
    http = httplib2.Http()
    response, content = http.request('http://thing.0.0.0.0:8080/recipes',
            method='GET')

    assert response['status'] == '200'
    assert 'other_' not in content, content
    assert 'thing_' in content, content

    response, content = http.request('http://thing.0.0.0.0:8080/bags',
            method='GET')

    assert response['status'] == '200'
    assert 'other_' not in content, content
    assert 'thing_' in content, content

    response, content = http.request(
            'http://thing.0.0.0.0:8080/bags/thing_public/tiddlers',
            method='GET')
    assert response['status'] == '200'

    response, content = http.request(
            'http://thing.0.0.0.0:8080/bags/other_public/tiddlers',
            method='GET')
    assert response['status'] == '404', content

    response, content = http.request(
            'http://other.0.0.0.0:8080/bags',
            method='GET')
    assert response['status'] == '200', content
    assert 'other_' in content, content
    assert 'thing_' not in content, content

    response, content = http.request(
            'http://0.0.0.0:8080/bags',
            method='GET')
    assert response['status'] == '200', content
    assert 'other_' in content, content
    assert 'thing_' in content, content

    response, content = http.request(
            'http://thing.0.0.0.0:8080/bags/thing_public/tiddlers',
            method='GET')
    assert response['status'] == '200', content

    response, content = http.request(
            'http://thing.0.0.0.0:8080/bags/other_public/tiddlers',
            method='GET')
    assert response['status'] == '404', content

    tiddler1 = Tiddler('tiddler1', 'thing_public')
    tiddler2 = Tiddler('tiddler2', 'other_public')
    tiddler1.text = tiddler2.text = 'ohhai'
    store.put(tiddler1)
    store.put(tiddler2)

    response, content = http.request(
            'http://thing.0.0.0.0:8080/search?q=ohhai',
            headers={'Accept': 'application/json'},
            method='GET')
    assert response['status'] == '200', content

    info = simplejson.loads(content)
    assert len(info) == 1
    assert info[0]['title'] == tiddler1.title

    response, content = http.request(
            'http://other.0.0.0.0:8080/search?q=ohhai',
            headers={'Accept': 'application/json'},
            method='GET')
    assert response['status'] == '200', content

    info = simplejson.loads(content)
    assert len(info) == 1
    assert info[0]['title'] == tiddler2.title

    response, content = http.request(
            'http://0.0.0.0:8080/search?q=ohhai',
            headers={'Accept': 'application/json'},
            method='GET')
    assert response['status'] == '200', content

    info = simplejson.loads(content)
    assert len(info) == 2
