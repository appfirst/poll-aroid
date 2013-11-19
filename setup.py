try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'AppFirst Polling Daemon',
    'author': 'Malcolm Smith',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'polled@appfirst.com',
    'version': '0.8',
    #'packages': ['AfPoller','AfPoller.plugins'],
    # 'scripts': ['AfPoller/AfPoller.py'],
    'name': 'AfPoller'
}

setup(requires=['nose','requests','afstatsd'],**config)
