# -*- coding: utf-8 -*-

from app import create_app
from app.exts import db

# create app
app = create_app()

if __name__ == '__main__':
    app.run()
